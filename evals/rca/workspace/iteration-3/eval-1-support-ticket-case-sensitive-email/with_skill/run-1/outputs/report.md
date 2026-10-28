# RCA: support search misses users when the email case differs

Support search returns "not found" when the typed email differs in case from the stored email.
The root cause is that no layer owns a canonical form of the email key.
Signup stores the raw input, and the store compares with exact `==`.
I recommend one `normalize_email()` function that the store applies on every write and every lookup, plus a uniqueness rule on the normalized key.

The same defect also breaks password reset, lets one person create duplicate accounts, and sends invites to existing members.

## Symptom and scope

Support agents look up customers by email and get "not found" for customers who exist.
Four agents reported it in 24 hours, first on 2026-05-12. Each lookup costs 5 to 10 minutes and a page to the data team.

The ticket log shows one customer and three casings:

```text
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

| | Value |
|---|---|
| Expected | Any casing of a registered address finds the user. |
| Actual | Only the exact stored casing finds the user. |
| Repro | `python3 -m unittest discover tests -v` fails `test_search_finds_user_signed_up_with_mixed_case` with `'not_found' != 'ok'`. |
| Log replay | Probe 1 signed up `Jane.smith@gmail.com` and replayed the three queries. The result matched the log exactly: `not_found`, `not_found`, `ok`. |

**Timeline.** The history has no known-good version to compare against.
The app code exists in one commit only (`a1c647a`, the fixture import). That commit already contains the exact `==` at `app/db.py:34`.

The defect is latent since the code was written, so the change is in the inputs.
Support searches with addresses copied from tickets and Stripe. Those can differ in case from the signup input.
I could not find what changed on 2026-05-12. See the open questions.

**Workspace.** I worked in a copy of the fixture at `outputs/fixture`.
All probes ran from stdin with `python3 -B` and monkeypatched the fix in memory. I edited no source file.
The test run created two `__pycache__` directories. I deleted them, and the tree hash matches the step-1 baseline (`48f1174a`).

## 5-whys chain

1. **Why did support get "not found" for a customer who exists?**
   - **Answer:** `search_by_email` returns `not_found` whenever `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. Probe 1 reproduced the three log lines.

2. **Why did `find_by_email` return `None` for an existing user?**
   - **Answer:** It compares the query to the stored value with exact string equality.
   - **Evidence:** `app/db.py:34` has `if u.email == email:`. Probe 1 hit only on `Jane.smith@gmail.com`, the stored casing.

3. **Why does the stored value differ in case from what support types?**
   - **Answer:** Signup stores the email exactly as the user typed it, with no transform.
   - **Evidence:** `app/signup.py:1` says "Stores email as the user typed it". `app/signup.py:15` passes `email` to `db.insert` unchanged.

4. **Why do the write path and the read path disagree on the form of the email?**
   - **Answer:** No layer owns a canonical form. Signup, the store, and all four callers pass the raw string through.
   - **Evidence:** `grep -rnE 'lower|casefold|normali|strip|=='` over `app/` finds one hit, `app/db.py:34`. The store docstring at `app/db.py:1` says "Case-sensitive lookups by email."

5. **Why does no layer own it?**
   - **Answer:** The model treats the email as a plain `str` that serves as an identity key. No type, invariant, or spec says that email identity ignores case.
   - **Evidence:** `app/db.py:10` declares `email: str`. The repo has no `docs/` or spec. The only test before this bug used a lowercase address (`tests/test_search.py:20-22`).

I stop at link 5 because a fix at that level repairs all four callers at once.

## Symptom, proximate, root

- **Symptom.** Support search says "not found" for a customer who exists.
- **Proximate cause.** `app/db.py:34` compares the raw query to the raw stored email with `==`.
- **Root cause.** The email identity key has no canonical form and no owner. Writes store raw input, and reads compare raw input.

**Falsification.** If case were not the cause, a case-insensitive comparison would not fix the repro.
I ran three checks:

- The three log queries are equal after `lower()` and differ before it. They have the same length, no whitespace, and only ASCII. Case is the only difference.
- With the monkeypatched case-insensitive store, the repro test passes and all three log queries return `ok`.
- A second mechanism, such as whitespace or a homoglyph, cannot explain this ticket, because the third query succeeded with only a case change.

One limitation remains. Other tickets may also involve whitespace. Probe 6 showed that a stored leading space also causes `not_found`.

## Siblings

All four callers of `db.find_by_email` inherit the exact `==`. Probes 2 to 5 show each failure.

| Severity | Site | Failure seen in the probe |
|---|---|---|
| High | `app/signup.py:13` | `Bob@Example.COM` then `bob@example.com` creates a second account (ids 1 and 2). |
| High | `app/password_reset.py:11` | A reset for `bob@example.com` raises `ResetError("no such user")`. The user cannot reset the password. |
| High | Existing data | Duplicate accounts from the signup sibling are probably already in production. With them, search returns whichever row matches the typed casing (probe 5). |
| Medium | `app/invite.py:7` | An invite to an existing member returns `invite_sent`. The invitee can then create a duplicate account. |
| Medium | `app/search.py:7` | The reported bug. `BOB@EXAMPLE.COM` also returns `not_found`. |
| Low | Same class, other axis | A stored `" carol@example.com"` is not found by `carol@example.com` (probe 6). |

## Assumptions

1. **Assumption:** `db.find_by_email` is the only email comparison in the app.
   - **How validated:** grep for `find_by_email`, `.email`, and `==` over `app/` and `tests/`.
   - **Result:** Confirmed. One comparison, four callers.

2. **Assumption:** Case is the only difference between the failing and the passing queries in the ticket.
   - **How validated:** Falsification check 1 above.
   - **Result:** Confirmed.

3. **Assumption:** Matching on a lowercased key is safe if the store keeps the address as typed for sending.
   - **How validated:** RFC 5321 § 2.4 says the domain ignores case and SMTP must preserve the case of the local part. The fix keeps the typed form for sending and uses the key only to match.
   - **Result:** Confirmed for the design. The residual risk is two real mailboxes that differ only by case. I did not measure it.

4. **Assumption:** Production has no case-duplicate accounts, so a unique index on the normalized key will apply cleanly.
   - **How validated:** none. The fixture has no production data.
   - **Result:** UNVERIFIED. The recommended fix gates the unique index on a duplicate query. Stage 1 does not rest on this assumption.

## Fix proposals

### Proposal A: symptom fix

- **Files:** `app/search.py`, `app/db.py`.
- **Approach:** Add a case-insensitive scan that only search uses. Lowercasing only the query does not work. Probe 7 showed it still returns `not_found` for `Bob@Example.COM`.
- **Tests:** The existing repro test.
- **Blast radius:** Search only. Signup, reset, and invite stay broken.
- **Rollback:** Revert the commit.

### Proposal B: root-cause fix (recommended)

- **Files:** `app/db.py`, `app/signup.py`, new tests, and a data migration in production.
- **Approach, stage 1:** Add `normalize_email(e) = e.strip().lower()` in the store. `find_by_email` compares normalized keys. `insert` rejects a key that already exists. The store keeps the typed address for display and sending.
- **Approach, stage 2:** In production, add an `email_normalized` column and backfill it. Run `SELECT lower(trim(email)), count(*) FROM users GROUP BY 1 HAVING count(*) > 1`. Merge any duplicates, then add a unique index on the column.
- **Tests:** The repro test plus the class test under Prevention.
- **Blast radius:** All four callers. Signup now rejects a case variant of a registered address, which is the intended change.
- **Rollback:** Revert stage 1. Stage 2 is additive until the duplicate merge, which needs its own backup.

**Recommendation:** Proposal B.
Stage 1 is about as small as Proposal A and also repairs password reset and signup.
Proposal A would end the support pages but hide the duplicate-account sibling, which keeps creating bad data.

### Counterfactual

**Result: confirmed with survivors.** I monkeypatched stage 1 into the store and ran the captured failures again:

| Case | Before | After |
|---|---|---|
| Repro test suite | 1 failure | OK, 2 tests |
| Jane log replay, three casings | `not_found`, `not_found`, `ok` | `ok`, `ok`, `ok` |
| Signup `bob@example.com` after `Bob@Example.COM` | second account | `email already registered` |
| Password reset with a different case | `ResetError` | `reset-token-for-1` |
| Invite to an existing member | `invite_sent` | `already_member` |
| Stored address after signup | `Bob@Example.COM` | `Bob@Example.COM` (kept as typed) |

The fix breaks the chain at link 4, because the store now owns one canonical form for reads and writes.
These survivors remain after stage 1:

- **Duplicate rows created before the fix.** Search returns the first match (id 1 of ids 1 and 2). Stage 2 closes this.
- **Lookups that skip the store.** Raw SQL with `WHERE email = ...`, such as the queries of the data team, keeps the old behaviour. The stage 2 column and index close this for new code.

## Prevention

- **Test.** Add a parametrized test that signs up one address, then calls search, reset, invite, and signup with case and whitespace variants. Every caller must resolve to the same user, and signup must reject the variant. This catches the class across callers, not only in search.
- **Guardrail.** Add a unique index on the normalized key so that a duplicate insert fails loudly. In code, make `find_by_email` the only email comparison and reject `.email ==` outside `app/db.py` in a lint or grep check in CI.
- **Doc.** Write the invariant down: "Email identity ignores case and outer whitespace. The store keeps the typed form for display and sending." Replace the docstrings at `app/db.py:1` and `app/signup.py:1`, which currently document the opposite.

## Open questions

- **Interim rule for support.** No reliable casing rule exists. The stored casing is whatever the customer typed at signup. Should support use the data-team query until stage 1 ships?
- **What changed on 2026-05-12?** The code has no change on record. A new support workflow or a new traffic source would explain the burst. I could not check either.
- **How many duplicate accounts exist now?** The stage 2 query answers this. The answer decides the effort of the merge and whether billing is split across accounts.
- **Whitespace and Unicode.** I recommend `strip().lower()`. `casefold()` would also merge `ß` with `ss`, which may join distinct addresses. Do you want internationalized addresses in scope?

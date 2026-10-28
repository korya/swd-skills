# RCA: user search misses customers when the email casing differs

## Headline

Support search returns "not found" for existing customers when the typed email casing differs from the stored casing.

The root cause is that the system has no canonical form for an email address. Signup stores the raw string, and `db.find_by_email` compares raw strings exactly.

The same gap breaks the duplicate check at signup, password reset, and team invites. I recommend one canonical email key at the store boundary, with a uniqueness rule on that key.

## Symptom and scope

Support agents search for a customer by email and get `not_found`, although the customer exists. The bug report (`BUG_REPORT.md`) gives these facts:

- **Who:** four support agents reported it within 24 hours. Each miss costs 5 to 10 minutes per ticket and a page to the data team.
- **Since when:** first reported 2026-05-12. That is the date of the first report, not of the first occurrence.
- **Severity:** P2.

The log in the report shows one customer and three attempts:

```
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

| | Value |
|---|---|
| Expected | Any casing of the address finds the customer. |
| Actual | Only the exact casing typed at signup finds the customer. |

**Repro.** The repro is deterministic. `python3 -m unittest discover tests -v` fails one of two tests:

```
FAIL: test_search_finds_user_signed_up_with_mixed_case
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
```

A replay of the logged Jane case reproduces all three log results (probe P6 below).

**Workspace.** I worked in a copy of the fixture at `outputs/fixture`. The copy has no git repository of its own. I recorded a SHA-1 of every file as the baseline and verified the copy against it at the end.

## Timeline

No responsible change is identifiable, because the fixture has no commit history. The defect is in the code as written, not in a regression.

- `app/db.py:1` documents the behaviour as intended: "Case-sensitive lookups by email."
- `app/signup.py:1` documents the write side: "Stores email as the user typed it."
- The only known date is the first report, 2026-05-12.

The bug predates every change I can see. The new element is probably in the inputs, such as more mixed-case signups or a change in how agents copy addresses. I have no evidence for either, so this stays an open question.

## 5-whys chain

1. **Why did support see "not found" for an existing customer?**
   - **Answer:** `search_by_email` returns `not_found` whenever `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. Log lines 1 and 2 above.

2. **Why did `find_by_email` return `None` for a stored user?**
   - **Answer:** It compares the stored string and the query with exact, case-sensitive equality.
   - **Evidence:** `app/db.py:34` reads `if u.email == email:`. Probe P6 reproduces all three log lines.

3. **Why does the stored string differ in case from the query?**
   - **Answer:** Signup stores the email exactly as the user typed it, with no normalization.
   - **Evidence:** `app/signup.py:15` passes the raw `email` to `db.insert`. Probe P5b shows a leading space is also stored.

4. **Why does neither the write path nor the read path normalize?**
   - **Answer:** No module defines a canonical form for an email address.
   - **Evidence:** `grep -rn "lower\|casefold\|strip" app/` returns no matches. `app/db.py:1` declares case-sensitive lookup as the design.

5. **Why did no layer take responsibility for it?**
   - **Answer:** Email identity is a plain `str` at every layer, with no type, invariant, or uniqueness rule on a normalized key. Each of the four callers depends on exact string match without stating it.
   - **Evidence:** `app/db.py:10` (`email: str`) and `app/db.py:32`. The four callers are `search.py:7`, `signup.py:13`, `password_reset.py:11`, and `invite.py:7`. Probe P1 creates two accounts for one mailbox. Before this bug, the only test used a lowercase address (`tests/test_search.py:20-22`).

I stop at link 5. A fix at that level repairs all four callers at once, so it prevents the siblings.

## Symptom, proximate cause, root cause

- **Symptom:** support search returns "not found" for customers who exist.
- **Proximate cause:** the exact string comparison at `app/db.py:34`.
- **Root cause:** the code base has no canonical email key. Nothing enforces one normalized form at write time, at read time, or as a uniqueness rule.

**Falsification.** I tried to disprove that case is the mechanism.

- **What we would see otherwise:** a case-insensitive comparison would still fail the repro.
- **Second mechanism:** whitespace or invisible characters in the query would give the same symptom. The logged queries differ only in case, so case explains this log.
- **Experiment:** I replaced only the comparison in `find_by_email` with `lower()` on both sides, in memory. The failing test passed (2 of 2). The root cause survives.

## Siblings

Every email lookup goes through `db.find_by_email`, so every caller has the same defect. Probes P1 to P5 show each one.

| # | Sibling | Evidence | Severity |
|---|---|---|---|
| S1 | Signup duplicate check lets `bob@example.com` register after `Bob@Example.COM`. | P1: two users, ids 1 and 2. `app/signup.py:13` | High |
| S2 | Password reset says "no such user" for a different casing. | P2: `ResetError no such user`. `app/password_reset.py:11` | High |
| S3 | Invite sends a new invite to an existing member. | P3: `invite_sent`. `app/invite.py:7` | Medium |
| S4 | A leading or trailing space breaks lookup and is stored as typed. | P5 and P5b: `not_found`, stored `' dave@example.com'` | Medium |
| S5 | Data is probably already corrupted with case-variant duplicate accounts and untrimmed addresses. | S1 allows it. No production data was available to count. | High until counted |

S1 matters most for the fix. If duplicates exist, a lookup that simply ignores case returns an arbitrary account. Password reset would then issue a token for the wrong user record.

S3 has a second effect that I could not verify. If the invitee accepts by signing up, S1 likely creates a duplicate account. The accept flow is not in the fixture.

## Fix proposals

### Proposal 1: symptom fix

Make only the search case-insensitive.

- **Files:** `app/search.py`.
- **Approach:** scan `db.all_users()` and compare `email.strip().lower()` on both sides. Return all matches, so that agents see duplicates.
- **Tests:** the existing failing test, plus a test with two case-variant accounts.
- **Blast radius:** the support search only.
- **Rollback:** revert one file.
- **Cost:** S1 to S5 stay open. Signup keeps creating duplicates, and reset keeps locking users out. The fix also hides the root cause, because support stops reporting it.

### Proposal 2: root-cause fix

Give the store one canonical email key and a uniqueness rule on it.

- **Files:** `app/db.py`, plus a data migration. The callers need no change.
- **Approach:** add `normalize_email(raw) = raw.strip().lower()`. Store the typed address for display and the key for matching. `insert` rejects a second user with the same key. `find_by_email` matches on the key and raises `AmbiguousEmail` when legacy data holds more than one match.
- **Lowercase, not casefold:** `casefold()` maps `ß` to `ss`, so it would merge two different mailboxes. Probe P8 confirms that `lower()` keeps them apart.
- **Migration:** backfill the key. List key collisions with `SELECT lower(trim(email)), count(*) FROM users GROUP BY 1 HAVING count(*) > 1`. Merge or retire duplicates. Then add a unique index on the key, or use a `citext` column.
- **Search behaviour on legacy duplicates:** `search_by_email` catches `AmbiguousEmail` and returns all matching ids. Support then sees the duplicates instead of an error.
- **Tests:** see Prevention.
- **Blast radius:** every email lookup. Two accounts whose addresses differ only in case can no longer both exist. That is the intended change, but it is a product decision (open question 1).
- **Rollback:** revert `app/db.py`. The key column is additive. Drop the unique index if it was added.

### Recommendation

I recommend Proposal 2. The code change is about 30 lines in one file and repairs all four callers. The migration and the duplicate cleanup take the most time.

If support needs relief today, ship Proposal 1 first as a stopgap. Track it as temporary and remove it when Proposal 2 lands.

### Counterfactual

**Result: confirmed with survivors.**

I applied Proposal 2 to a temporary copy of the fixture and replayed the repro and every probe. I then deleted the copy.

| Probe | Before | After |
|---|---|---|
| Failing test | 1 of 2 fail | 2 of 2 pass |
| P6: Jane, three casings | 1 of 3 found | 3 of 3 found |
| P1: case-variant signup | second account created | `email already registered` |
| P2: reset, other casing | `no such user` | token for user 1 |
| P3: invite existing member | `invite_sent` | `already_member` |
| P5: search with spaces | `not_found` | `ok` |
| P7: two legacy duplicates | returns one arbitrary user | `AmbiguousEmail` with ids 1 and 2 |
| P8: `Straße` then `strasse` | not tested | kept as two users |

The fix breaks link 4 of the chain, because one module now defines the canonical form. It also breaks link 5 for writes through `insert`.

The fix leaves two survivors:

- **Legacy duplicates.** They now fail loudly instead of silently. Each caller must handle `AmbiguousEmail` until the migration merges them. The fix is wide enough only with that migration.
- **Writes that bypass `insert`.** Any code that builds a `User` and appends it directly skips the uniqueness check. In production, only a database unique index closes this path.

## Assumptions

1. **Assumption:** `db.find_by_email` is the only email lookup path.
   - **How validated:** `grep -rn "find_by_email\|\.email\b\|==" app/` finds four callers and one comparison, at `db.py:34`.
   - **Result:** Confirmed.

2. **Assumption:** stored addresses keep the casing the user typed.
   - **How validated:** `app/signup.py:15` and probe P5b.
   - **Result:** Confirmed.

3. **Assumption:** case is the mechanism behind the logged misses.
   - **How validated:** the falsification experiment and probe P6.
   - **Result:** Confirmed.

4. **Assumption:** the product may treat the whole address, including the local part, as case-insensitive.
   - **How validated:** none. RFC 5321 allows a case-sensitive local part. Large mail providers ignore case, and the bug report treats the three casings as one customer. No product spec in the fixture decides it.
   - **Result:** UNVERIFIED. Proposal 2 rests on this assumption, so it is a hypothesis until the product owner confirms it. See open question 1.

5. **Assumption:** `lower()` is a safe normalization for non-ASCII addresses.
   - **How validated:** probe P8 and a `lower()` against `casefold()` comparison on `Straße`.
   - **Result:** Confirmed for `ß`. Other Unicode edge cases are not tested.

6. **Assumption:** production data contains case-variant duplicate accounts.
   - **How validated:** probe P1 shows the code permits them. No production data was available.
   - **Result:** UNVERIFIED. Run the collision query in Proposal 2 before adding the unique index.

## Prevention

- **Test for this bug:** keep `test_search_finds_user_signed_up_with_mixed_case`. Add the same casing and whitespace test for signup, password reset, and invite.
- **Test for the class:** add one parametrized test over every public function that takes an email. Each one must give the same result for the stored form, all-lowercase, all-uppercase, and the padded form.
- **Guardrail in the store:** a unique index on the normalized key, or a `citext` column. A second account for the same mailbox then becomes impossible, not merely unlikely.
- **Guardrail in the types:** replace `email: str` in lookup signatures with an `EmailKey` type that only `normalize_email` can build. A raw string comparison then fails the type check.
- **Doc update:** state the invariant "one account per normalized email" in the product spec or `AGENTS.md`. Name `normalize_email` as the only allowed way to compare addresses.

## Open questions

1. **Case policy.** May the product treat `Bob@Example.COM` and `bob@example.com` as the same account? Proposal 2 depends on a yes.
2. **Duplicate count.** How many case-variant duplicate accounts exist in production? Who decides how to merge them, given billing in Stripe?
3. **Trigger.** Did something change on or before 2026-05-12, such as a signup client, an import, or the support tool? The code alone does not explain why four reports arrived in one day.
4. **Answer to support now.** Until a fix ships, agents can try the casing the customer used at signup, or ask the data team. No casing rule is reliable, because the store keeps whatever each customer typed.

## Side effects of this investigation

- I copied the fixture to `outputs/fixture` and worked only in the copy.
- The first test run created `__pycache__` in the copy. I deleted it and ran later commands with `PYTHONDONTWRITEBYTECODE=1`.
- I tested Proposal 2 in a temporary copy at `run-3/cf-tree` and deleted that copy afterwards.
- The final SHA-1 check of `outputs/fixture` matches the baseline. Nothing was pushed, published, or sent.

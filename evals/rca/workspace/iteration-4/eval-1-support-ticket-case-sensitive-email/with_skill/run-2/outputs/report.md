# RCA: support search misses customers when the email casing differs

## Headline

Support search returns "not found" when the agent types an email in a different letter case than the stored one.
The root cause is that the user store has no email identity rule, so it compares raw strings byte for byte.
The recommended fix normalizes the email in `app/db.py` on every insert and lookup and allows one account per normalized email.

## Symptom and scope

Support agents search for a customer by email and get "not found" for a customer who exists. The data team then finds the same customer with SQL on the `users` table. Each ticket loses 5 to 10 minutes.

- **Who:** 4 support agents reported it within 24 hours.
- **Since when:** first report on 2026-05-12. The defect itself is older. See the timeline below.
- **Expected:** a search for `jane.smith@gmail.com` finds the customer stored as `Jane.smith@gmail.com`.
- **Actual:** only the exact stored casing finds the customer.

The logs from the ticket, verbatim:

```
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

Support asked for a casing rule they can follow. No such rule exists. A search succeeds only with the casing the customer typed at signup, and support cannot know that casing.

### Reproduction

The repro is deterministic. The test in the fixture fails on every run:

```sh
python3 -m unittest discover tests -v
# test_search_finds_user_signed_up_with_mixed_case ... FAIL
# AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
```

A probe against the same code reproduces the exact log pattern:

| Query | Stored email | Result |
|---|---|---|
| `Jane.Smith@gmail.com` (exact) | `Jane.Smith@gmail.com` | `ok` |
| `jane.smith@gmail.com` | `Jane.Smith@gmail.com` | `not_found` |
| `Jane.smith@gmail.com` | `Jane.Smith@gmail.com` | `not_found` |
| `JANE.SMITH@GMAIL.COM` | `Jane.Smith@gmail.com` | `not_found` |

### Workspace

All work ran in a copy of the fixture at `outputs/fixture`. The copy is not a git repository of its own. I recorded a SHA-1 baseline of every file before the investigation. No source file changed. The probes and the fix prototype ran in memory from stdin. The test runs created `__pycache__` directories, and I removed them at the end. The tree matches the baseline.

## Timeline

The defect is latent, not a regression. Nothing in the available history changed the lookup.

- The fixture carries no product history. Its only commit is `a1c647a`, which adds the whole directory at once.
- `app/db.py:1` documents the behaviour as intended: "Case-sensitive lookups by email."
- `app/signup.py:1` documents the other half: "Stores email as the user typed it."
- No deploy, flag, or dependency record is available for the period before 2026-05-12.

The trigger for the 2026-05-12 reports is not known. A change in the inputs is likely, such as support copying emails from Stripe or from tickets. I have no evidence for any specific input change. See the open questions.

## 5-whys chain

1. **Why did support search return "not found" for an existing customer?**
   - **Answer:** `search.search_by_email` got `None` from `db.find_by_email` and mapped it to `not_found`.
   - **Evidence:** `app/search.py:7-9`. The log line `search.search_by_email email="jane.smith@gmail.com" -> not_found`.

2. **Why did `db.find_by_email` return `None`?**
   - **Answer:** It compares the stored email and the query with exact string equality, which is case-sensitive.
   - **Evidence:** `app/db.py:34` is `if u.email == email:`. The probe table above shows that only the exact casing matches.

3. **Why did the stored email and the query differ in case?**
   - **Answer:** Signup stores the email exactly as the customer typed it. Support types the email from a different source, with a different casing.
   - **Evidence:** `app/signup.py:15` passes the raw `email` to `db.insert`. `app/db.py:26` stores it unchanged. The probe shows `stored: 'Jane.Smith@gmail.com'`. The three log queries show three casings for one customer.

4. **Why does neither the write nor the read normalize the email?**
   - **Answer:** No normalization function exists anywhere in the codebase.
   - **Evidence:** `grep -rn "lower\|casefold\|normaliz" app tests` returns no source hits.

5. **Why does no normalization function exist?**
   - **Answer:** The store treats email as an opaque string, but all four callers use it as the identity key for a person. No contract defines when two emails are the same address.
   - **Evidence:** `app/db.py:1` declares case-sensitive lookups as the design. `grep -rn find_by_email app` shows 4 callers: search, signup, password reset, and invite. The fixture has no docs, invariants, or `AGENTS.md`. The only other test uses an all-lowercase email (`tests/test_search.py:20-22`), so no test exercised mixed case.

The chain stops at link 5. A fix at this level repairs all four callers at once. A fix above it repairs only search.

## Symptom, proximate cause, root cause

| Label | Finding | Location |
|---|---|---|
| Symptom | Support search returns "not found" for an existing customer. | `app/search.py:9` |
| Proximate cause | The lookup compares emails with case-sensitive equality. | `app/db.py:34` |
| Root cause | The user store has no definition of email identity. It stores raw input and compares raw strings, while every caller uses email as the key for a person. | `app/db.py:1`, `app/db.py:24-36` |

### Falsification of the root cause

I tried to disprove the root cause with three questions.

- **What would we see if case-sensitive comparison were not the cause?** The exact casing would also fail, or a case variant would succeed. Neither happens. Log line 3 and the probe both show that only the exact casing succeeds.
- **Does a second mechanism produce the same symptom?** Yes. Leading or trailing whitespace also defeats the lookup: a search for `"bob@example.com "` returns `not_found`. The log queries show no whitespace, but I cannot inspect their raw bytes. Unicode lookalike characters are a third mechanism that I did not rule out.
- **Cheapest disconfirming experiment:** I replaced only the comparison in `db.find_by_email` with a case-insensitive one, in memory. The failing test passed: 2 tests, 0 failures. With the original comparison restored, the test failed again.

We believe the missing email identity rule is the root cause. We have not ruled out whitespace or lookalike characters in the production log queries.

## Siblings

The same gap breaks every flow that looks up a user by email. I ran each flow with a stored `Jane.Smith@gmail.com` and a query of `jane.smith@gmail.com`.

| # | Sibling | Observed behaviour | Severity |
|---|---|---|---|
| S1 | Password reset, `app/password_reset.py:11` | Raises `ResetError: no such user`. The customer cannot reset the password. | High |
| S2 | Signup duplicate check, `app/signup.py:13` | Accepts `jane.smith@gmail.com` as a new account. The store then holds two users for one mailbox. | High |
| S3 | Existing data in `users` | Case-only duplicate accounts may already exist because of S2. The count is unknown. | High |
| S4 | Team invite, `app/invite.py:7` | Returns `invite_sent` to an existing member. Acceptance can then create a duplicate through S2. | Medium |
| S5 | Whitespace in input, all four flows | A trailing space defeats the lookup in the same way as a case difference. | Medium |

S3 also changes the fix. When duplicates exist, a case-insensitive lookup has two matches and must choose one. The probe confirms this: after a duplicate signup, `Jane.Smith@gmail.com` finds user 1 and `jane.smith@gmail.com` finds user 2.

No other code reads `User.email` for comparison. `grep -rn "\.email" app` shows only `db.py:34` and the response field in `search.py:10`.

## Assumptions

1. **Assumption:** The lookup in production behaves like the fixture lookup.
   - **How validated:** The log lines name `search.search_by_email`, the fixture function. The logs show the fixture pattern: exact casing succeeds, variants fail.
   - **Result:** Confirmed for the fixture. The production store is not available to read.

2. **Assumption:** The failing log queries differ from the stored email only in letter case.
   - **How validated:** Log line 3 returns `ok` for `Jane.smith@gmail.com`. Lines 1 and 2 differ from it only in letter case as displayed.
   - **Result:** Confirmed as displayed. Raw bytes are not available.

3. **Assumption:** Every email lookup goes through `db.find_by_email`.
   - **How validated:** `grep -rn "find_by_email\|\.email" app tests`.
   - **Result:** Confirmed. A fix in `find_by_email` reaches all four callers.

4. **Assumption:** A case-insensitive email identity is correct for this product.
   - **How validated:** RFC 5321 section 2.4 makes domains case-insensitive. It permits a case-sensitive local part but discourages any reliance on it. The data team already finds these customers with SQL.
   - **Result:** Confirmed as a technical basis. A product sign-off is still open.

5. **Assumption:** The fix can keep the email that the customer typed for display.
   - **How validated:** The in-memory prototype stores the stripped input and compares a normalized key. `db.all_users()[0].email` returns `Jane.smith@gmail.com`.
   - **Result:** Confirmed.

6. **Assumption:** No case-only duplicates exist in production today.
   - **How validated:** none. No production data is available.
   - **Result:** UNVERIFIED. The recommended fix does not rest on it. The fix runs an audit first and stops if the audit finds duplicates.

## Fix proposals

### Proposal A: symptom fix in search

- **Approach:** Make `search_by_email` scan `db.all_users()` and compare `email.strip().lower()` on both sides.
- **Files:** `app/search.py`.
- **Tests:** the existing failing test passes.
- **Blast radius:** support search only.
- **Rollback:** revert one file.
- **Cost:** It leaves S1, S2, S4, and S5 broken. S2 keeps creating duplicates, and each duplicate makes search ambiguous. The fix also hides the cause, because the one visible flow stops failing.

### Proposal B: root-cause fix in the store

- **Approach:**
  1. Add `normalize_email(email)` in `app/db.py`. It strips whitespace and lowercases the address.
  2. `db.insert` stores the stripped email for display and the normalized email as the key.
  3. `db.find_by_email` compares normalized query against normalized key.
  4. `db.insert` raises `DuplicateEmail` when the normalized key already exists.
  5. In the SQL store, add a unique index on the normalized email, for example `lower(trim(email))`.
  6. Before the index, run an audit: `SELECT lower(trim(email)), count(*) FROM users GROUP BY 1 HAVING count(*) > 1`.
- **Files:** `app/db.py`, plus one migration for the SQL store. `signup`, `search`, `password_reset`, and `invite` need no change.
- **Tests:** the repro test, plus the class test under Prevention.
- **Blast radius:** all four email flows. Signup rejects case variants of existing accounts. Invite stops sending invites to existing members. Both changes are intended.
- **Rollback:** revert the code and drop the index. A merge of duplicate accounts is not reversible, so it needs a separate approval.

### Recommendation

I recommend Proposal B. Proposal A fixes one of five broken paths and lets S2 keep corrupting the data. Proposal B costs one function, two call-site changes in `db.py`, and one migration.

Ship Proposal A first only if the audit finds duplicates that block the index. In that case, mark it as temporary in the code and track Proposal B.

### Counterfactual

Result: **confirmed with survivors.**

- **Would the repro still fire?** No. I ran an in-memory prototype of Proposal B. The repro test passed with 0 failures. Search, password reset, and invite all found `Jane.smith@gmail.com` from three other casings. A case-variant signup and a direct `db.insert` both failed with a duplicate error.
- **Which link does the fix break?** Link 5. The store now defines email identity, which also breaks links 2 to 4 for every caller.
- **Does it address the captured failure?** Yes. The prototype reproduces the log scenario and returns `ok` for all three logged casings.

Survivors:

- **Existing duplicates (S3).** Code cannot repair rows that already exist. The audit and a merge decision are required.
- **Raw comparisons in future code.** Code that reads `db.all_users()` and compares `.email` directly bypasses the rule. No such code exists today. The guardrail below closes this path.
- **Lookalike characters.** Normalization by case and whitespace does not merge Unicode lookalikes. That is a separate decision.

## Prevention

- **Test:** add one parametrized test over every email entry point: search, password reset, invite, and signup. Each case stores one casing and queries with a different casing and with surrounding whitespace. This test catches a new flow that bypasses the rule, not only this bug.
- **Guardrail:** enforce identity in the store, not in callers. The unique index on the normalized email makes a duplicate fail loudly. A stronger option is an `Email` value type whose equality uses the normalized form, so a raw comparison is impossible to write.
- **Lint check:** add a CI check that fails on `.email ==` outside `app/db.py`.
- **Doc:** replace the docstring at `app/db.py:1` with the identity rule. Add an invariant to the repo docs: "Email identity is case-insensitive and ignores surrounding whitespace. Only `app/db.py` applies the rule."

## Open questions

1. **Product policy.** Do you accept a case-insensitive local part? RFC 5321 permits case-sensitive local parts, although almost no mail provider uses them.
2. **Normalization function.** Use `lower()` to match the SQL index, or `casefold()` for non-ASCII addresses? The two differ only for non-ASCII input. The function in code and in the index must be the same.
3. **Existing duplicates.** How many case-only duplicates exist in production, and who decides how to merge them? A merge is not reversible.
4. **Trigger.** What changed around 2026-05-12? No deploy, config, or support-process history was available to me.
5. **Provider rules.** Gmail ignores dots and `+tag` suffixes in the local part. I recommend no normalization for them, because the rules differ per provider.

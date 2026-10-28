# RCA: user search misses customers when the email casing differs

## Headline

Support cannot find a customer unless they type the email with the exact casing the customer used at signup. The root cause is that the codebase has no canonical form for an email address. Every lookup compares raw strings, and no rule says that `Bob@Example.COM` and `bob@example.com` are one user. The same defect also lets a person register twice, blocks their password reset, and sends team invites to existing members. I recommend one canonical email key in the user store, with a uniqueness rule on that key. This fix repairs all four flows in one place.

The answer to the question from support: there is no casing rule that they can follow. Search matches only the exact characters that the customer typed at signup, and support cannot see those characters.

## Symptom and scope

Support agents search for a customer by email and get `not_found`. The customer exists. The data team finds the same customer with SQL. The bug report quotes this log:

```text
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

- **Who.** Support agents who handle tickets. Four agents reported it within 24 hours.
- **Since when.** First reported on 2026-05-12. The code shows the defect has no start date (see Timeline).
- **Cost.** Support reports 5 to 10 minutes per ticket, plus pages to the data team.
- **Expected.** Any casing of a registered address finds the customer.
- **Actual.** Only the exact stored casing finds the customer.

The failing test reproduces it deterministically:

```text
$ python3 -m unittest discover tests -v
test_search_finds_user_signed_up_with_mixed_case ... FAIL
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
```

A probe script replays the bug-report log against the fixture and gets the same three results. The script is in `probes/probe_siblings.py` next to this report.

## Timeline

The defect is as old as the code that we have. The fixture has no Git history of its own. The parent repository added all fixture files in one commit (`a1c647a`, 2026-10-23). `git log -S lower -- evals/rca/fixture` finds no commit that removed case handling. No deploy, flag, or dependency record exists in the fixture.

The skill says to look at the inputs when the bug predates every change. The code has compared emails case-sensitively from the start. Something about the inputs probably changed near 2026-05-12, so that more searches used a different casing. I do not know what changed. It is an open question below.

## The 5-whys chain

1. **Why did search return `not_found` for `jane.smith@gmail.com`?**
   - **Answer:** `search_by_email` returns `not_found` when `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. The failing test output above.

2. **Why did `find_by_email` return `None` when the user exists?**
   - **Answer:** It compares the query to the stored address with `==`, which matches only identical characters.
   - **Evidence:** `app/db.py:34` has `if u.email == email:`. The probe finds `Jane.smith@gmail.com` and misses the two other casings.

3. **Why does the stored address differ in casing from the query?**
   - **Answer:** Signup stores the address exactly as the user typed it. Support types the address as they see it elsewhere.
   - **Evidence:** `app/signup.py:1` docstring says "Stores email as the user typed it". `app/signup.py:15` passes the raw value to `db.insert`, and `app/db.py:26` stores it. The log shows that the stored form is `Jane.smith@gmail.com`.

4. **Why does neither side convert the address to one form?**
   - **Answer:** The codebase has no canonical form for an email address. Each layer passes the raw string through.
   - **Evidence:** `grep -rn "lower()\|casefold\|strip()" app` returns no match. `app/db.py:1` documents "Case-sensitive lookups by email" as a property of the store.

5. **Why did nothing catch this before customers did?**
   - **Answer:** No spec, invariant, or constraint states that one address in any casing is one user. The only uniqueness check reuses the flawed lookup. The tests covered only the exact-casing round trip.
   - **Evidence:** The fixture has no docs or spec files. `app/db.py:24-29` (`insert`) has no uniqueness check. `app/signup.py:13` checks duplicates through `find_by_email`. `tests/test_search.py:20-22` was the only passing test, and it searches with the same casing it stored.

## Symptom, proximate cause, root cause

| Label | What | Where |
|---|---|---|
| Symptom | Search returns `not_found` for a registered customer | `app/search.py:9` |
| Proximate cause | Raw string equality on the email | `app/db.py:34` |
| Root cause | No canonical email identity, and no rule or constraint that enforces one | `app/db.py`, `app/signup.py`, no spec |

A fix at the proximate cause stops this ticket. A fix at the root cause stops the class, because all four callers go through the same lookup.

### Falsification

I tried to disprove the root cause with these three checks:

- **The data could be missing or the search path could be broken.** Then the exact casing would also fail. The third log line and the probe both find the user with the exact casing. This rules it out.
- **A second mechanism could produce the same symptom.** Leading or trailing whitespace, or invisible characters from copy and paste, also break `==`. The probe shows that whitespace also returns `not_found`. This is the same root cause, not a competing one, because a canonical key removes both. I cannot rule out invisible characters in the logged queries, because a log does not show them.
- **A disconfirming experiment.** I changed only the comparison key in a scratch copy of the code. The failing test passed, and all three sibling flows changed behavior. The comparison is the operative mechanism.

One falsifier stays unrun. The fixture uses an in-memory store. If the production store compares case-insensitively, the production bug has a different cause. Open question 1 covers this.

## Siblings

All four callers of `db.find_by_email` share the defect. The sweep used `grep -rn "find_by_email\|\.email" app tests`. The probe confirms each caller.

| Flow | Location | What happens with a different casing | Severity |
|---|---|---|---|
| Signup duplicate check | `app/signup.py:13` | A second account is created for the same person. The probe gets user id 2 for `bob@example.com` after `Bob@Example.COM`. | High. It corrupts data, and production may already hold duplicates. |
| Password reset | `app/password_reset.py:11` | `ResetError: no such user` for a registered user. | High. Customers cannot recover their account. |
| Team invite | `app/invite.py:7` | `invite_sent` to an existing member. | Medium. Combined with the signup sibling, the invitee can create a second account. |
| User search (reported) | `app/search.py:7` | `not_found`. | P2, as filed. |

Duplicate accounts also make a symptom-only fix unsafe. With two accounts for one person, a case-insensitive search returns the first one and hides the second. The probe shows ids `[1, 2]` for one address.

## Assumptions

1. **Assumption:** Every email lookup goes through `db.find_by_email`.
   - **How validated:** `grep -rn "find_by_email\|\.email ==" app` finds four callers and one comparison, at `app/db.py:34`. `db.all_users()` has no caller in `app/`.
   - **Result:** Confirmed for this codebase.

2. **Assumption:** The product treats addresses that differ only in casing as one customer.
   - **How validated:** `BUG_REPORT.md:9-12` and `:29-30` treat the three casings as one customer. Stripe and the data team also find one customer. Major mail providers ignore casing in the local part.
   - **Result:** Confirmed as product intent from the report. RFC 5321 allows a case-sensitive local part, so a product owner must still accept the policy (open question 2).

3. **Assumption:** Trimming surrounding whitespace never merges two real addresses.
   - **How validated:** The RFC 5321 mailbox grammar does not allow unquoted leading or trailing whitespace.
   - **Result:** Confirmed.

4. **Assumption:** Production holds no accounts that differ only in casing.
   - **How validated:** Not possible here. The fixture has no production data.
   - **Result:** UNVERIFIED. The recommended fix does not rest on it. Its migration counts collisions first and stops if it finds any (open question 3).

5. **Assumption:** The production store compares emails case-sensitively, like the fixture.
   - **How validated:** Not possible here.
   - **Result:** UNVERIFIED. The RCA explains the fixture. It explains production only if this holds (open question 1).

## Fix proposals

### A. Symptom fix: case-insensitive comparison in search only

- **Files.** `app/search.py`.
- **Approach.** Compare `strip().casefold()` of the query and of each stored address. The diff is in `probes/symptom-fix.diff`.
- **Tests.** The failing test passes. I ran it in a scratch copy, and both tests passed.
- **Blast radius.** Search only. In a SQL store, it needs a functional index on `lower(email)` or it scans the table.
- **Rollback.** Revert one file.
- **What it leaves.** Signup, password reset, and invite stay broken. With duplicates, search silently returns one of the accounts.

### B. Root-cause fix: one canonical email key in the store

- **Files.** `app/db.py`, and a new `tests/test_email_identity.py`. The diff is in `probes/root-cause-fix.diff`.
- **Approach.**
  - Add `email_key(email)`, which returns `email.strip().casefold()`. It is the only definition of email identity.
  - Store the key next to the typed address. Display still uses the typed address, as `app/signup.py:1` intends.
  - `find_by_email` compares keys. The four callers need no change.
  - `insert` rejects a second user with the same key (`DuplicateEmail`). In SQL, this is a unique index on the key column.
- **Migration for a real store.**
  1. Add and backfill the key column.
  2. Count keys with more than one user.
  3. Stop if the count is above zero, and resolve the duplicates (open question 3).
  4. Add the unique index.
- **Tests.** In a scratch copy, all 8 tests passed: the 2 existing tests and 6 new class tests. The new tests cover every flow with three casings.
- **Blast radius.** Every email lookup. Signup now rejects a different casing of a registered address. Invites now see existing members. Both are intended changes.
- **Rollback.** Revert the code. The key column can stay. Drop the unique index if a rollback needs to admit duplicates.

### Recommendation

I recommend B. Fix A hides the duplicate-account problem and leaves account recovery broken. Ship A as a stopgap only if duplicate resolution blocks the migration in B. Then track B as the real fix.

## Counterfactual

The recommended fix B is **confirmed, with survivors**. With B in place, the captured repro does not fire. The test passes in the scratch copy, and the probe finds all three logged casings.

- **Links it breaks.** Link 2, because the comparison uses the key. Link 4, because the key is the one canonical form. The uniqueness rule also breaks link 5 for duplicates.
- **Survivor 1.** Duplicate accounts created before the fix stay in the store until the migration resolves them.
- **Survivor 2.** New code can still bypass the key. An example is a loop over `db.all_users()` that compares `.email`. The guardrails below close this.

## Prevention

- **Test.** Add `tests/test_email_identity.py`, in `probes/` next to this report. It runs each of the four flows with three casings of one stored address. A stronger form is a property test over random casings of random addresses.
- **Guardrail: constraint.** Enforce uniqueness on the canonical key in the store. In SQL, use a unique index on the key column, or a `citext` column. The Python key function and the database must use the same folding. Python `casefold()` and SQL `lower()` differ for some non-ASCII characters.
- **Guardrail: type.** Make `find_by_email` accept an `EmailKey` value type that only `email_key()` can build. A raw string then fails the type check.
- **Guardrail: lint.** Add a CI check that fails on `.email ==` outside `app/db.py`.
- **Alert.** Monitor the `not_found` rate of the search endpoint. Support worked around this bug by paging the data team, and no system noticed.
- **Doc.** Write the invariant: "One user per canonical email. Canonical form is trimmed and case-folded. The typed form is kept for display." Put it in the product specs, and correct the `app/db.py:1` docstring, which documents the opposite rule.

## Open questions

1. **Does production compare emails case-sensitively?** The fixture is an in-memory store. A MySQL table with a case-insensitive collation would not show this bug. Check the column type and collation of `users.email`, and the query that the data team ran.
2. **Does the product owner accept case-insensitive email identity?** RFC 5321 allows a case-sensitive local part. Nearly no real provider uses it. This decision belongs to the product owner, not to this RCA.
3. **How many duplicate accounts exist now, and how do we merge them?** Run `SELECT lower(email), count(*) FROM users GROUP BY 1 HAVING count(*) > 1`. Merging accounts touches billing and login, so it needs an owner.
4. **What changed in the inputs near 2026-05-12?** Four reports in 24 hours suggest a change, for example a new support workflow or a new signup channel. The code alone does not explain the burst.
5. **`casefold()` or `lower()`?** `casefold()` maps `ß` to `ss` and can merge two addresses with non-ASCII local parts. `lower()` matches SQL `lower()`. I used `casefold()` in the scratch fix. Choose one and use it in both the code and the database.

## Side effects of this investigation

- I worked only in the copy at `outputs/fixture`. Its files match the SHA-1 baseline in `probes/baseline.sha` again.
- I applied both fixes in scratch copies under `probes/`, ran the tests, kept the diffs, and deleted the copies.
- Test runs created `__pycache__` folders in the fixture. I deleted them.
- I pushed, published, and sent nothing.

# RCA: support search misses users when the email casing differs

Support search finds a customer only when the agent types the exact email casing the customer used at signup.
The root cause is the data model, which uses the raw typed email as the account identity with no normalization or uniqueness rule.
We recommend one normalized email key in `app/db.py`, used by every lookup and enforced as unique on insert, plus a cleanup of duplicate accounts.

## Symptom and scope

Support agents search for a customer by email and get "not found" for customers who exist.
The same customer appears with one casing and disappears with another.
The bug report quotes these log lines verbatim:

```
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

- **Who:** support agents. Four agents reported it within 24 hours.
- **Since when:** first seen 2026-05-12. The defect itself is older (see the timeline).
- **Cost:** 5 to 10 minutes per ticket, plus a page to the data team.
- **Expected:** any casing of the address finds the customer.
- **Actual:** only the casing stored at signup finds the customer.

Support asks for "the rule for which casing to use". The rule is "the exact casing the customer typed at signup". Agents cannot know that casing, so no usable rule exists until the fix ships.

### Reproduction

The failing test reproduces the bug deterministically:

```
$ python3 -m unittest discover tests -v
test_search_finds_user_signed_up_with_lowercase ... ok
test_search_finds_user_signed_up_with_mixed_case ... FAIL
AssertionError: 'not_found' != 'ok'
 : expected to find Bob, got {'status': 'not_found'}
FAILED (failures=1)
```

Probe P1 replays the bug report against the fixture. It stores `Jane.smith@gmail.com` and searches with the three logged casings. The results match the production log line for line: `not_found`, `not_found`, `ok`.

### Workspace and baseline

All work ran in a copy of the fixture at `outputs/fixture`. The copy is identical to the tracked `evals/rca/fixture` (checked with `diff -r`). The fixture is not its own git repository. The enclosing repository was on branch `korya-rca-simplify` at `0694414`, with the run directory untracked. The fix was tested in a throwaway copy, `run-1/cf-tmp`, which was then deleted. The fixture copy is unchanged apart from the removal of the `__pycache__` folders that the first test run created.

## Timeline

The defect is latent since the first version of the code. It is not a regression.

- **`a1c647a` (2026-10-23):** the only commit that touches the fixture. It adds all of `app/`, the test, and the bug report in one change.
- **No later change** touches `app/`. `git log --all -- evals/rca/fixture/app` shows only that commit and its twin `d116c23`.

No code change explains why the reports started on 2026-05-12. Something new in the inputs is the likely trigger. Examples are a new support workflow that uses the search tool, or more signups with mixed-case addresses. We have no data to tell these apart. See the open questions.

## 5-whys chain

1. **Why did support search return "not found" for `jane.smith@gmail.com`?**
   - **Answer:** `search_by_email` returns `not_found` when `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. Probe P1 returns `{'status': 'not_found'}` for that query.

2. **Why did `find_by_email` return `None` for an existing user?**
   - **Answer:** It compares the stored string and the query with exact equality. `Jane.smith@gmail.com` is not equal to `jane.smith@gmail.com`.
   - **Evidence:** `app/db.py:34` has `if u.email == email:`. Probe P5 shows the exact stored string matches. Probe P6 shows a case-insensitive comparison finds the user for all casings.

3. **Why is the stored casing different from what the agent typed?**
   - **Answer:** Signup stores the email exactly as the customer typed it. No code normalizes the email on write or on read.
   - **Evidence:** `app/signup.py:1` says "Stores email as the user typed it". `app/signup.py:15` passes the raw value to `db.insert`. `grep -rnE "lower\(|casefold\(|strip\(|normaliz" app/ tests/` finds nothing.

4. **Why does no code normalize the email?**
   - **Answer:** The data model has no concept of an email identity key. One field, `User.email`, serves as both the display value and the identity, and the store declares case-sensitive lookup as its design.
   - **Evidence:** `app/db.py:1` docstring says "Case-sensitive lookups by email". `app/db.py:7-11` defines `User` with a single `email: str` field.

5. **Why did nothing catch the gap before customers hit it?**
   - **Answer:** No layer states or enforces "one account per address, in any casing". The store accepts any insert. Uniqueness lives only in a check-then-insert in signup, which uses the same case-sensitive lookup. The tests covered only exact-case lookups.
   - **Evidence:** `app/db.py:24-29` inserts with no uniqueness check. `app/signup.py:13` is the only duplicate check. Probe P2 creates two accounts for `Bob@Example.COM` and `bob@example.com`. `tests/test_search.py:20-22` is the only test that existed besides the repro. The fixture has no spec or invariant document.

The chain stops at link 5 because a fix at that level also repairs every sibling below.

## Symptom, proximate cause, root cause

| Label | What it is | Where |
|---|---|---|
| Symptom | Support search says "not found" for a customer who exists | `app/search.py:9` |
| Proximate cause | Exact string equality between the stored email and the query | `app/db.py:34` |
| Root cause | The raw typed email is the account identity. No normalized key exists and the store enforces no uniqueness on it. | `app/db.py:1-29`, `app/signup.py:13-15` |

### Falsification of the root cause

We tried to disprove the root cause with three checks.

- **What we would see if it were wrong.** The exact stored casing would also fail, or a case-insensitive comparison would not fix the lookup. Neither happens. P1 and P5 show exact casing works. P6 shows case-insensitive comparison works for every casing.
- **A second mechanism with the same symptom.** Surrounding whitespace also produces "not found" (P5). The logged queries differ only in case and contain no whitespace, so whitespace did not cause this report. It is the same class of defect and appears as a sibling. A missing record is ruled out because the third logged search returned `ok id=8412`.
- **The cheapest disconfirming experiment.** Probe P6 replaces `find_by_email` in memory with a case-insensitive comparison. The failing query then succeeds. We ran it.

One limitation remains. The bug report mentions a SQL `users` table, and the fixture models it with an in-memory list. We have not seen the production schema or its collation. We believe the in-memory model reflects production. We have not ruled out a production-only difference in collation or column type.

## Siblings

Every email lookup in the codebase goes through `db.find_by_email`, so every caller inherits the defect.

| Sibling | Effect | Evidence | Severity |
|---|---|---|---|
| `app/signup.py:13` duplicate check | A second signup with a different casing creates a second account | P2: accounts 1 `Bob@Example.COM` and 2 `bob@example.com` | High |
| `app/password_reset.py:11` | A customer who types a different casing gets "no such user" and cannot reset the password | P3: `ResetError: no such user` | High |
| `app/invite.py:7` | An existing member gets a new invite and can create a second account through it | P4: `{'status': 'invite_sent'}` for an existing member | Medium |
| Whitespace in the address | A leading or trailing space also misses the user | P5: `not_found` for `" Bob@Example.COM"` | Medium |
| Data already stored | Production can already hold several accounts for one address | P2 proves the path exists. The production count is unknown. | High |

The stored duplicates also block a naive fix. P7 shows that a case-insensitive lookup over duplicates matches two accounts. The current loop returns the first one. A password reset could then go to the wrong account.

## Fix proposals

### Proposal A: symptom fix

Make only the search compare case-insensitively.

- **Files:** `app/search.py`.
- **Approach:** scan `db.all_users()` and compare `u.email.lower()` with `email.lower()`.
- **Tests:** the existing repro passes.
- **Blast radius:** support search only.
- **Rollback:** revert one file.

This fix stops the support tickets and nothing else. Signup keeps creating duplicate accounts. Password reset and invite stay broken. Search also returns an arbitrary account when duplicates exist (P7). It hides the cause from the next person who sees the search work.

### Proposal B: root-cause fix (recommended)

Give the store one normalized identity key and enforce it in one place.

- **Files:** `app/db.py`. The callers do not change.
- **Approach:**
  - Add `normalize_email(email)`, which returns `email.strip().lower()`.
  - Add a `User.email_key` field. Keep `User.email` as the display value, stripped of surrounding spaces.
  - `insert` computes the key and raises `DuplicateEmail` when the key exists.
  - `find_by_email` normalizes the query and compares keys.
  - Replace the `app/db.py:1` docstring with the invariant from the prevention section.
  - Compute `email_key` in `__post_init__`, not as a default, so no `User` can exist without a key.
- **Production work:** add a normalized key column with a unique index, or a case-insensitive column type. First find and merge the existing duplicate accounts, or the unique index cannot be built.
- **Tests:** the existing repro, plus the contract test in the prevention section.
- **Blast radius:** every email lookup. All four callers want case-insensitive behavior. None depends on case being distinct.
- **Rollback:** the code change reverts cleanly. The unique index can be dropped. A merge of duplicate accounts cannot be undone, so it needs its own approval and a backup.

We recommend Proposal B. The four callers share one defect, and B repairs all of them with one change in the store. Proposal A is acceptable only as a same-day stopgap, shipped together with a ticket for B.

### Counterfactual

**Outcome: confirmed with survivors.**

We applied Proposal B in a throwaway copy of the fixture and ran the repro and the probes:

```
Ran 2 tests ... OK
CF search 'Jane.Smith@gmail.com' -> ok
CF search 'jane.smith@gmail.com' -> ok
CF search 'Jane.smith@gmail.com' -> ok
CF search ' JANE.SMITH@gmail.com ' -> ok
CF dup signup rejected: email already registered
CF reset -> reset-token-for-1
CF invite -> {'status': 'already_member'}
CF direct insert rejected: DuplicateEmail jane.smith@gmail.com
CF display email kept: Jane.smith@gmail.com
```

- **Would the repro still fire?** No. All three logged queries find the user.
- **Which link does the fix break?** Links 4 and 5. A normalized key now exists, and the store enforces uniqueness on it. Links 2 and 3 disappear as a consequence.
- **Does it address the captured failure?** Yes, the captured failure and all four siblings in code.

The survivors are outside the code change:

- **Existing duplicate accounts** in production remain until someone merges them.
- **Equivalence rules beyond case and whitespace**, such as Unicode case folding or provider-specific rules, are not covered. Gmail ignores dots, for example. These are product decisions (see the open questions).

## Prevention

- **Test.** Add a contract test that runs every email entry point against a set of variants. The entry points are search, password reset, invite, and the duplicate check in signup. The variants are upper case, lower case, mixed case, and surrounding spaces. The search test for this exact bug is the floor. This test catches the next lookup that skips the key.
- **Guardrail in the store.** Make `insert` reject a duplicate key. In production, back it with a unique index on the normalized key. Then a duplicate account is impossible, not merely unlikely.
- **Guardrail in review.** Fail CI on any `.email ==` comparison outside `app/db.py`. A stronger option is a distinct `EmailKey` type, so a type checker rejects a comparison of a raw string with a key.
- **Doc.** State the invariant where the next author reads it: "Email identity is case-insensitive and ignores surrounding spaces. `User.email` is for display only. Compare emails only through `db.normalize_email`." Put it in the `app/db.py` docstring and in the product spec or `AGENTS.md`, if the real repository has one.

## Assumptions

1. **Assumption:** every email lookup goes through `db.find_by_email`.
   - **How validated:** `grep -rn email app/` finds one comparison, at `app/db.py:34`, and four callers.
   - **Result:** Confirmed.

2. **Assumption:** the logged queries differ only in case.
   - **How validated:** compared the three logged strings. They are equal after `lower()` and contain no spaces.
   - **Result:** Confirmed.

3. **Assumption:** no caller depends on two casings being two different accounts.
   - **How validated:** read all four callers. Ran the existing tests and the probes against Proposal B.
   - **Result:** Confirmed.

4. **Assumption:** callers need the original casing for display.
   - **How validated:** `app/search.py:10` returns `user.email`. The counterfactual shows Proposal B keeps `Jane.smith@gmail.com`.
   - **Result:** Confirmed.

5. **Assumption:** the product treats the whole address, local part included, as case-insensitive.
   - **How validated:** none in the code. RFC 5321 makes the domain case-insensitive and lets a mail server treat the local part as case-sensitive. Most providers ignore case in the local part.
   - **Result:** UNVERIFIED. This is a product decision. Proposal B confines it to `normalize_email`, so a different answer changes one function.

6. **Assumption:** production holds no duplicate accounts that differ only in case.
   - **How validated:** none. We have no access to production data. P2 proves the code path that creates them.
   - **Result:** UNVERIFIED. The unique index depends on it. Run the duplicate query below before the migration.

7. **Assumption:** production lookups behave like the fixture, with case-sensitive comparison.
   - **How validated:** the production log matches the fixture result for all three casings (P1).
   - **Result:** Confirmed for behavior. The schema and collation are not seen.

## Open questions

- **Equivalence rule.** Is the whole address case-insensitive, or only the domain? Should Unicode addresses use `casefold()` instead of `lower()`? Proposal B assumes the whole address and `lower()`.
- **Existing duplicates.** How many accounts collide? A query such as `SELECT lower(trim(email)), count(*) FROM users GROUP BY 1 HAVING count(*) > 1` answers it. Who decides how to merge them, given billing records in Stripe?
- **Trigger on 2026-05-12.** What changed in the support workflow or the signup population around that date? The code did not change.
- **Production schema.** What column type and collation does `users.email` use? This decides between a key column, a functional unique index, and a case-insensitive column type.
- **Interim guidance for support.** Until the fix ships, should support ask the data team to use a case-insensitive SQL lookup instead of guessing the casing?

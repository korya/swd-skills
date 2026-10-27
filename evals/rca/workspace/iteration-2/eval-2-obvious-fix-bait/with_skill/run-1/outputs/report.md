# RCA: user search by email misses customers who signed up with mixed case

## Headline

Email has no canonical form anywhere in the service. The store compares the raw string the
user typed, so every lookup by email is case-sensitive, not only search. Normalize the email
once in `app/db.py`, on write and on lookup, instead of patching `app/search.py`.

The requested one-line patch in `app/search.py` would make the failing test pass. It would
leave signup, invite, and password reset broken in the same way. It also cannot be applied
as written, because `app/search.py` has no comparison line. The `u.email == email` line it
targets lives in `app/db.py:34`.

## Symptom and scope

Support agents search a customer by email and get "not found" for a customer who exists.
The agents retry with other casings until one matches. The ticket reports four agents in
24 hours, first seen 2026-05-12, and a cost of 5 to 10 minutes per ticket.

Logs from `BUG_REPORT.md`, quoted verbatim:

```
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

Expected: any casing of the same mailbox finds the same user. Actual: only the exact string
stored at signup matches.

### Repro

`tests/test_search.py:24` is a deterministic repro. It signs up `Bob@Example.COM` and
searches `bob@example.com`. Run in the working copy:

```
python3 -I -m unittest discover tests -v
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
FAILED (failures=1)
```

### Baseline

The fixture is a plain directory, not a git repository, so there is no branch or `HEAD`.
The baseline is the md5 of every source file, recorded before any edit. The aggregate
checksum of the working copy is `2772235721f8affeb56aaf10b7396f79`, identical to the
source fixture. The tree matched this checksum again at the end of the investigation.

## Timeline

No git history exists for the fixture, so `git log` and `git log -S` could not be run. The
module docstrings record the design intent instead and serve as the timeline evidence.

| File | Docstring | What it tells us |
|---|---|---|
| `app/db.py:1` | "In-memory user store. Case-sensitive lookups by email." | Case-sensitive matching was a stated choice, not an accident. |
| `app/signup.py:1` | "Stores email as the user typed it." | No normalization on write was also a stated choice. |

Nothing in the code is new. The input changed: customers sign up with the casing their mail
client displays, and support types the casing they see on the ticket.

## 5-whys chain

1. **Why did search return `not_found` for an existing user?**
   - **Answer:** `db.find_by_email` returned `None`.
   - **Evidence:** `app/search.py:7-9` returns `{"status": "not_found"}` whenever
     `db.find_by_email(email)` is `None`. The failing test output above.

2. **Why did `find_by_email` return `None`?**
   - **Answer:** It compares the stored email and the query with `==`, which is
     case-sensitive in Python. `"Bob@Example.COM" == "bob@example.com"` is `False`.
   - **Evidence:** `app/db.py:32-36`, line 34 is `if u.email == email:`.

3. **Why does the stored email differ in case from the query?**
   - **Answer:** Signup stores the email exactly as typed, and search passes the query
     exactly as typed. Neither side normalizes.
   - **Evidence:** `app/signup.py:15` calls `db.insert(email=email, ...)` with the raw
     argument. `app/db.py:26` stores it unchanged. `app/search.py:7` passes its argument
     unchanged. `grep -rn 'lower\|casefold' app` finds no match.

4. **Why does no layer normalize?**
   - **Answer:** The service has no canonical form for an email. The store treats the email
     as an opaque string and documents case-sensitive lookups as its contract.
   - **Evidence:** `app/db.py:1` docstring. `app/signup.py:1` docstring. `db.insert` and
     `db.find_by_email` have no normalization hook.

5. **Why is there no canonical form?**
   - **Answer:** The store's contract was written for exact string identity, and the four
     callers inherited it without a shared rule for what "same email" means. No test
     covered a mixed-case round trip until the one in the bug report.
   - **Evidence:** `tests/test_search.py:20` covers only the lowercase round trip. The four
     callers at `app/signup.py:13`, `app/invite.py:7`, `app/password_reset.py:11`, and
     `app/search.py:7` all call `db.find_by_email` with a raw string.

A fix at link 4 (one canonical form in `db`) prevents every sibling below. That is the stop.

## Symptom, proximate cause, root cause

- **Symptom.** Search by email returns "not found" unless the casing matches the signup
  string exactly.
- **Proximate cause.** `app/db.py:34` compares emails with case-sensitive `==`.
- **Root cause.** The service has no canonical form for an email. Writes store the raw
  string, lookups compare the raw string, and each of four callers relies on the exact
  match without knowing it.

### Falsification of the root cause

- **If the root cause were wrong, we would see** a mismatch with identical casing, for
  example from trailing whitespace or a Unicode variant. The ticket logs show three queries
  that differ only in case. The repro differs only in case.
- **A second mechanism** could be a stale read replica or a separate index. The fixture has
  one in-memory list, `app/db.py:14`, and no other read path.
- **Disconfirming experiment, run:** normalizing case in `db` alone made the repro pass and
  every sibling probe pass (see Counterfactual). If case were not the mechanism, the test
  would still fail.

## Siblings

Every lookup goes through the same comparison, so every lookup shares the bug. Probes ran
against the unmodified fixture with a user signed up as `Bob@Example.COM`.

| Sibling | Call site | Probe result | Severity |
|---|---|---|---|
| Duplicate accounts | `app/signup.py:13` | `signup("bob@example.com")` succeeded. Two accounts, ids 1 and 2, for one mailbox. | High. Data corruption, and it undermines the one-line fix (below). |
| Password reset fails | `app/password_reset.py:11` | `request_reset("bob@example.com")` raised `ResetError("no such user")`. | High. The customer is locked out. |
| Invite re-sent to a member | `app/invite.py:7` | `is_already_member("bob@example.com")` returned `False`. | Medium. Duplicate invite, possible second account. |
| Existing data | the `users` table | Not inspected, no access from the fixture. | Unknown. Mixed-case rows and case-variant duplicates may already exist. |

The one-line search patch interacts with the first sibling. On a store that already holds
`Bob@Example.COM` and `bob@example.com`, a case-insensitive search matches both. The probe
showed ids `[1, 2]`, and `find_by_email` returns whichever was inserted first.

## Assumptions

1. **Assumption:** `db.find_by_email` is the only email lookup in the service.
   - **How validated:** `grep -rn 'find_by_email\|\.email\|email ==' app tests`.
   - **Result:** Confirmed. Four callers, one comparison at `app/db.py:34`.

2. **Assumption:** `db.insert` is the only email write.
   - **How validated:** Same grep. `app/signup.py:15` is the only caller of `insert`.
   - **Result:** Confirmed.

3. **Assumption:** Lowercasing the whole address is the correct canonical form.
   - **How validated:** RFC 5321 allows a case-sensitive local part. Every major provider
     treats the local part as case-insensitive, and the ticket's own customer signed up
     and was found under different casings. Not validated against the product's policy.
   - **Result:** UNVERIFIED as policy. Open question 1. The fix below adopts lowercase,
     which is what the user's request also assumes.

4. **Assumption:** Production data holds no case-variant duplicates that a normalizing
   backfill would collide on.
   - **How validated:** Cannot be validated from the fixture.
   - **Result:** UNVERIFIED. Open question 2. The code fix does not depend on it, the
     backfill does.

5. **Assumption:** Callers do not depend on `User.email` keeping the user's typed casing.
   - **How validated:** `grep -rn '\.email' app` shows one read, `app/search.py:10`, which
     echoes it to the support tool.
   - **Result:** Confirmed for the fixture. Open question 3 covers display casing.

## Fix proposals

### Proposal A: symptom fix (the one requested)

- **Files:** `app/search.py`.
- **Approach:** Replace the `db.find_by_email` call with a loop over `db.all_users()` that
  compares `email.lower() == u.email.lower()`. The requested line cannot go into
  `app/search.py` as is, since that file has no `u`. Search would become a fourth
  implementation of lookup.
- **Tests:** `test_search_finds_user_signed_up_with_mixed_case` passes.
- **Blast radius:** Search only. Signup, invite, and password reset keep the bug. Duplicate
  accounts keep being created, and search then returns an arbitrary one of them.
- **Rollback:** Revert one file.

### Proposal B: root-cause fix (recommended)

- **Files:** `app/db.py`, `tests/test_search.py`, new `tests/test_email_identity.py`,
  a one-off backfill script.
- **Approach:** Add `db.normalize_email(email) -> str` that strips whitespace and
  lowercases. Call it in `db.insert` before storing and in `db.find_by_email` before
  comparing. Replace the `app/db.py:1` docstring with the new contract. Backfill existing
  rows to the canonical form after resolving duplicates (open question 2).
- **Tests:** The existing repro. One round-trip test per caller: signup rejects a
  case-variant duplicate, invite recognizes a member by any casing, reset finds the user
  by any casing. One test that `insert` stores the canonical form.
- **Blast radius:** Every email lookup becomes case-insensitive at once. `User.email`
  comes back lowercase, so the support tool shows `bob@example.com` for a user who typed
  `Bob@Example.COM`. The backfill touches every row in `users`.
- **Rollback:** Revert `app/db.py`. The backfill is one-way unless the original casing is
  saved first, so save it in a new column before running it.

### Recommendation

Proposal B. Proposal A would fix the ticket and hide the cause. Support would stop
reporting, while signup kept minting duplicate accounts and password reset kept locking
customers out. Those two siblings are worse than the reported symptom. The fix in B is
smaller than A in diff size and touches the one place every caller already goes through.

## Counterfactual

Proposal B was applied to the working copy, run, and reverted. The baseline checksum
matched afterwards.

| Check | Before | After B |
|---|---|---|
| `test_search_finds_user_signed_up_with_mixed_case` | FAIL | OK |
| signup of a case-variant duplicate | second account created, ids 1 and 2 | `SignupError("email already registered")` |
| `invite.is_already_member("bob@example.com")` | `False` | `True` |
| `password_reset.request_reset("BOB@example.com")` | `ResetError("no such user")` | `reset-token-for-1` |

**Confirmed.** The fix breaks link 3: stored and queried emails no longer differ in case,
because both pass through the same canonical form. The repro cannot fire. No survivors in
the code. Existing mixed-case rows survive until the backfill runs.

Proposal A is confirmed for the captured repro only. Survivors: signup, invite, password
reset, and the ambiguous match on duplicates.

## Prevention

- **Test.** A round-trip test per caller with a mixed-case signup and a lowercase query
  (listed under Proposal B). Those are the floor.
- **Guardrail.** Make the canonical form the only form the store accepts. Have `db.insert`
  raise if `email != normalize_email(email)`, so a future write path that skips
  normalization fails loudly in tests. Stronger: a `NormalizedEmail` type returned only by
  `normalize_email`, with `insert` and `find_by_email` typed to accept only it. Then the
  class of bug is a type error.
- **Doc.** Replace the `app/db.py:1` docstring, which currently documents the bug as the
  contract. State the rule once: "Emails are stored and compared in canonical form, see
  `normalize_email`."

## Open questions

1. Is lowercasing the whole address the product's rule, or only the domain part? RFC 5321
   permits a case-sensitive local part. Lowercasing the whole address is the common
   choice and what the ticket's customer expects.
2. How many case-variant duplicate accounts exist in production, and which one wins? The
   data team can answer with `SELECT lower(email), count(*) ... GROUP BY 1 HAVING count(*) > 1`.
   The backfill cannot run before this is answered.
3. Should the service keep the user's typed casing for display? If yes, store it in a
   separate column and keep `email` as the canonical lookup key.
4. Did the `search.search_by_email` logs start on 2026-05-12, or did the tool start logging
   then? The ticket gives a first-seen date, not an introduction date.

## Side effects disclosed

- Copied the fixture to the working copy. No other path was modified.
- Edited `app/db.py` in the working copy to run the counterfactual, then restored it from
  the source fixture. The aggregate md5 matched the baseline afterwards.
- Ran three probe scripts through `python3 -I` on stdin. No files written.
- Nothing pushed, published, or sent.

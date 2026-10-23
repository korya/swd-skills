# RCA: user search misses customers whose email was typed in a different case

## Headline

Search is not the bug; it is the first place the bug was noticed. Every email lookup in the service goes through `db.find_by_email`, which compares raw strings (`app/db.py:34`), and signup stores emails exactly as typed (`app/signup.py:1`, `app/db.py:26`). The system has no canonical form for an email address, so four flows disagree about who a user is. The requested one-liner in `app/search.py` cannot be written there (`u` is not in scope), and a lookup-only `.lower()` fixes the ticket while leaving whitespace misses and already-duplicated accounts in place. Recommended: define the canonical form once in `db.py`, apply it on write and on read, enforce uniqueness in the store, and plan a backfill for existing data.

## Symptom and scope

- **What support saw** (`BUG_REPORT.md`, verbatim):
  ```
  2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
  2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
  2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
  ```
- **Who:** 4 support agents in 24h, P2, first seen 2026-05-12; cost 5-10 min per ticket plus a data-team page.
- **Expected vs actual:** one person, one account, findable by any casing; actual: findable only by the exact bytes they signed up with.
- **Repro:** `python3 -m unittest discover tests -v` in the fixture copy. `test_search_finds_user_signed_up_with_mixed_case` fails with `'not_found' != 'ok'` (deterministic, 0.000s).
- **Baseline:** fixture copied to `OUTPUT_DIR/fixture`; not a git repo. SHA-1 of every non-`.pyc` file recorded before any experiment and re-verified at the end; unchanged. No edits were made to the fixture; both candidate fixes were trialled on scratch copies.

## Timeline

The fixture has no version history, so `git log` cannot name an introducing change. Per the skill's fallback ("if the bug predates every change, look for what is new in the inputs"): the compare has been bytewise since the store was written (`db.py:1` docstring states "Case-sensitive lookups by email" as a design, not an accident), and the first-seen date most plausibly tracks a change in inputs (customers signing up from mail clients that display capitalised addresses) rather than a code change. This is an inference from the docstring and the absence of history, not a verified fact; see Open questions.

## 5-whys chain

1. **Why did search return `not_found` for `bob@example.com`?**
   - **Answer:** `search_by_email` got `None` from `db.find_by_email` and mapped it to `not_found`.
   - **Evidence:** `app/search.py:7-9`; probe P2 returns `{'status': 'not_found'}`.

2. **Why did `find_by_email` return `None`?**
   - **Answer:** It compares the query string to the stored string with `==`, and `"Bob@Example.COM" != "bob@example.com"`.
   - **Evidence:** `app/db.py:33-34` (`if u.email == email`); probe P1 shows the exact-case query `"Bob@Example.COM"` returns `ok` for the same record, so nothing else in the search path is broken.

3. **Why was the stored value `Bob@Example.COM` rather than a lower-cased form?**
   - **Answer:** Signup passes the email through untouched and `insert` stores whatever it receives; nothing in the codebase normalises email.
   - **Evidence:** `app/signup.py:1` ("Stores email as the user typed it"), `app/signup.py:15`, `app/db.py:26`; `grep -rn lower|casefold|strip|normalize app/` returns nothing.

4. **Why does neither side normalise?**
   - **Answer:** The store's contract is literally "case-sensitive lookups by email", and the callers each take that as a given. There is no single definition of "the same email" anywhere, so each flow silently inherits bytewise identity.
   - **Evidence:** `app/db.py:1` docstring; four callers at `signup.py:13`, `invite.py:7`, `password_reset.py:11`, `search.py:7`, none of which transforms the input.

5. **Why was a bytewise identity for emails allowed to stand?**
   - **Answer:** No invariant, test, or constraint encodes "one person = one email, independent of case/whitespace". The only test (`tests/test_search.py:20`) exercised a lower-case round trip, so the gap was invisible; the store has no uniqueness enforcement at all (`db.insert` never checks), so the dedupe at `signup.py:13` is the only guard and it uses the same flawed compare.
   - **Evidence:** `tests/test_search.py:20-22`; `app/db.py:24-29` (no uniqueness check); probe P4 creates a second account for `bob@example.com`.

Every link above is backed by a file:line or a probe result; none is `UNVERIFIED`.

## Classification

- **Symptom:** support search returns `not_found` for an existing customer unless the casing matches exactly.
- **Proximate cause:** bytewise `u.email == email` at `app/db.py:34`.
- **Root cause:** the service has no canonical form for an email address. Identity is "the bytes the user typed", applied inconsistently to write (stored raw) and read (compared raw), and nothing (constraint, test, type) says otherwise.

### Falsification of the root

- **If this were wrong, we would see:** exact-case lookups failing too (a broken search path), or lower-case signups failing lookup (an encoding issue). Probe P1 (exact case: `ok`) and the passing lower-case test rule both out.
- **Second mechanism producing the same symptom:** trailing/leading whitespace in the query. Probe P6 shows `"Bob@Example.COM "` also returns `not_found`. This is not a competing explanation for the logged failures (the three log lines differ only in case), but it is the same class (no canonical form) and a lookup-only `.lower()` does not cover it.
- **Cheapest disconfirming experiment:** fix only the compare on a scratch copy and see whether the whole class disappears. Done (experiment A): the ticket closes, whitespace misses survive, and pre-existing duplicate rows become silently first-match-wins. So the compare is where the symptom lives; the missing canonical form is why it lives there.

## Siblings

All four callers share `db.find_by_email`, so all four misbehave on a case mismatch (probe P3, P4):

| Call site | What goes wrong on a case mismatch | Severity |
|---|---|---|
| `app/search.py:7` | support cannot find the customer (the ticket) | P2 |
| `app/password_reset.py:11` | `ResetError("no such user")`: a real customer typing their own email in the "wrong" case is locked out | **P1** in effect: customer-facing lockout |
| `app/invite.py:7` | existing member is re-invited as if new; `already_member` guard is bypassed | P3 |
| `app/signup.py:13` | dedupe passes and a **second account** is created for the same person (probe P4: store holds `['Bob@Example.COM', 'bob@example.com']`) | **P1**: data corruption; every day it stays open it manufactures more duplicates |

Data already affected: the signup sibling means production very likely already contains duplicate accounts differing only by case. The fixture is in-memory so it cannot be queried here, but in production this is a `SELECT lower(email), count(*) ... GROUP BY 1 HAVING count(*) > 1` before any fix ships (see Open questions).

Also in the class, not covered by case folding alone: whitespace (probe P6).

## Assumptions

1. **Assumption:** `db.find_by_email` is the only email lookup path.
   - **How validated:** `grep -rn --include='*.py' find_by_email|"email =="` over the fixture.
   - **Result:** Confirmed; one compare at `db.py:34`, four callers.
2. **Assumption:** Exact-case lookups work, so the search path itself is sound.
   - **How validated:** Probe P1.
   - **Result:** Confirmed.
3. **Assumption:** Normalising at write and read does not break the existing lower-case behaviour.
   - **How validated:** Experiment B runs both tests `OK`; lower-case signup/search round trip still passes.
   - **Result:** Confirmed.
4. **Assumption:** `strip().lower()` is an acceptable canonical form for this product (RFC 5321 technically allows a case-sensitive local part; in practice no major provider honours it).
   - **How validated:** Not validated against product/legal requirements.
   - **Result:** UNVERIFIED as a product decision. The fix does not rest on the exact choice (any single canonical form fixes the class); the choice itself is an open question.
5. **Assumption:** Production data already contains case-variant duplicates that need a merge/backfill.
   - **How validated:** Cannot be run against the in-memory fixture; probe P4 proves the mechanism exists.
   - **Result:** UNVERIFIED for the data; confirmed for the mechanism. The fix proposal below does not depend on the answer, but the rollout plan does.

## Fix proposals

### A. Symptom fix (smallest change that closes the ticket)

- **File:** `app/db.py:34` only. Not `app/search.py`: the requested line `email.lower() == u.email.lower()` references `u`, which exists only inside `find_by_email`. Putting a lower-case compare in `search.py` would require re-implementing the lookup there, which would fix search and leave reset/invite/signup broken.
- **Approach:** `if u.email.lower() == email.lower():`.
- **Tests:** existing suite passes (experiment A: `OK`).
- **Blast radius:** all four callers immediately become case-insensitive (good), including signup dedupe going forward.
- **What it leaves behind:** whitespace misses (P6 still `not_found`); stored data stays mixed-case; already-duplicated accounts resolve silently to whichever row was inserted first (id 2 becomes unreachable by email). O(n) `.lower()` per row per lookup, irrelevant in-memory, relevant if this mirrors a real DB where it defeats the index.
- **Rollback:** revert one line.

### B. Root-cause fix (recommended)

- **Files:** `app/db.py` (one canonical function, applied in `insert` and `find_by_email`, uniqueness enforced in the store); no change required in the four callers. Verified diff from experiment B:
  ```diff
  -"""In-memory user store. Case-sensitive lookups by email."""
  +"""In-memory user store. Emails are stored and looked up in canonical form."""
  +def canonical_email(email: str) -> str:
  +    """Single definition of email identity: trimmed, lower-cased."""
  +    return email.strip().lower()
   def insert(email: str, name: str) -> User:
       global _NEXT_ID
  +    email = canonical_email(email)
  +    if find_by_email(email) is not None:
  +        raise ValueError(f"duplicate email: {email}")
   def find_by_email(email: str) -> Optional[User]:
  +    email = canonical_email(email)
  ```
- **Approach:** identity is defined once, at the storage boundary, on both write and read; the store refuses duplicates instead of trusting every caller to pre-check. Callers keep their current code.
- **Tests:** existing suite `OK`; add the tests in Prevention.
- **Blast radius:** stored emails change shape (lower-cased) for new rows; any display that relies on the user's original capitalisation needs a separate `display_email` field if that matters (open question). `insert` can now raise, which `signup` already guards against via its own pre-check, so no caller sees a new exception in normal flow.
- **Rollback:** revert `db.py`; data written in canonical form remains valid under the old compare for lower-case queries.
- **Rollout (production analogue):** (1) ship B; (2) run the duplicate query; (3) backfill: lower-case existing rows, merge or flag the case-variant duplicates by policy; (4) add the DB-level unique constraint on the normalised column.

**Recommendation:** B. A closes the ticket but keeps manufacturing the class (whitespace now, any future identity rule later) and leaves the duplicate-account mechanism as "fixed by accident". A is acceptable as a same-day hotfix only if B cannot ship within the week, and only with the duplicate query run first so support knows which customers have two accounts.

## Counterfactual

- **Fix A** against the captured repro: **confirmed for this case, but siblings survive.** Breaks link 2 (the compare). Survivors: whitespace misses (P6), pre-existing duplicates resolved silently, mixed-case data at rest.
- **Fix B** against the captured repro: **confirmed.** Breaks link 4 (there is now one definition of email identity, used on both sides). The repro test passes, the three sibling probes pass, duplicate signup is blocked at the store (experiment B output: `OK`; `search(lower): ok`, `search(trailing sp): ok`, `invite(lower): already_member`, `reset(lower): reset-token-for-1`, `dup signup: blocked`).

## Prevention

- **Tests (floor):** in `tests/`: (1) signup mixed-case, lookup lower-case, for each of search, reset, invite; (2) signup twice with case/whitespace variants raises `SignupError`; (3) `db.insert` with a case variant of an existing row raises (store-level, independent of signup).
- **Guardrail (makes the class loud or impossible):**
  - A `CanonicalEmail` type (`NewType` or a small value class) that `db` accepts and that can only be constructed via `canonical_email()`; raw `str` into `insert`/`find_by_email` becomes a type-checker error.
  - In the real DB: unique index on `lower(email)` (or a generated `email_normalized` column). Duplicate creation then fails at the constraint, not at a Python pre-check that can be bypassed by any new caller.
- **Doc update:** `db.py` docstring already corrected in B. Add an invariant to the service docs: "Email identity is `canonical_email(x)`; no module compares or stores raw email strings." The current docstring asserted the opposite rule as if it were intended, and the bug followed from it.

## Open questions

1. **Canonical form policy.** Is `strip().lower()` acceptable, or does the product need to honour case-sensitive local parts for some domain? (Assumption 4.) Also: should the user's typed capitalisation be preserved for display in a separate field?
2. **Existing duplicates.** How many production rows collide under `lower(email)`, and what is the merge policy (oldest wins, most-active wins, manual review)? (Assumption 5.) This must be answered before fix A or B goes to a persistent store.
3. **Timeline.** Does the first-seen date correlate with any change in signup sources (new mail client, OAuth provider that returns display-case emails)? Not answerable from the fixture; would confirm the "inputs changed, code did not" reading.

## Side effects and restoration

- No edits to `OUTPUT_DIR/fixture`. Both experiments ran on scratch copies under the session scratchpad, since removed.
- Running the test suite in the fixture copy may have refreshed `__pycache__/*.pyc`; those were restored from the source fixture so the copy matches it byte-for-byte.
- Nothing pushed, published, or sent.

# RCA: user search misses customers when email casing differs

## Headline

Support cannot find users unless they type the email with the exact casing stored at signup, because the codebase has **no definition of email identity**: `db.find_by_email` compares raw strings (`app/db.py:34`) and `signup` stores whatever the user typed (`app/signup.py:15`). The same gap breaks password reset, lets invites go to existing members, and lets one person sign up twice. Recommended fix: canonicalize email once, inside `app/db.py`, on both write and read, and make the raw-string comparison impossible to express.

## Symptom and scope

- **What support saw:** `search.search_by_email` returns `not_found` for a customer who exists. From `BUG_REPORT.md`:
  ```
  2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
  2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
  2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
  ```
- **Who:** 4 support agents in 24h, P2, first seen 2026-05-12. Costs 5–10 min per ticket plus a page to the data team.
- **Expected vs actual:** an email address identifies one account regardless of casing (the local part is technically case-sensitive per RFC 5321, but no major provider treats it that way and users do not know their "canonical" casing). Actual: only a byte-exact match finds the user.
- **Repro:** `tests/test_search.py::test_search_finds_user_signed_up_with_mixed_case` fails deterministically:
  ```
  AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
  ```
- **Baseline:** working copy at `OUTPUT_DIR/fixture` (no git history; SHA-1 of all source files recorded before investigation and re-checked after — unchanged).

## Timeline

The fixture carries no git history and no deploy/config log, so the responsible change cannot be cited by SHA. What the code itself says: `app/db.py:1` documents the store as "Case-sensitive lookups by email" and `app/signup.py:1` as "Stores email as the user typed it". Both are stated as design, not as oversights, which means the behaviour has been there since these modules were written. The bug surfaced now because of a change in **inputs**, not code: the report's three log lines show the same agents trying several casings, which is what you expect once mixed-case signups (phone email clients capitalize the first letter) reached a volume where support hits them daily. Limitation: without history this is an inference from the code's own comments, not a cited commit.

## 5-whys chain

1. **Why did search return `not_found`?**
   - **Answer:** `search_by_email` returns `not_found` whenever `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`.

2. **Why did `find_by_email` return `None` for an existing user?**
   - **Answer:** It compares with `u.email == email`, a byte-exact string comparison; `"Bob@Example.COM" == "bob@example.com"` is `False`.
   - **Evidence:** `app/db.py:32-36`; probe: `search_by_email("Bob@Example.COM")` → `ok`, `search_by_email("bob@example.com")` → `not_found` on the same store.

3. **Why is the stored value mixed-case in the first place?**
   - **Answer:** `signup` passes the email straight through to `db.insert`, and `insert` stores it verbatim. Nothing in the write path normalizes.
   - **Evidence:** `app/signup.py:15` (`db.insert(email=email, ...)`), `app/db.py:24-29`; module docstring `app/signup.py:1` "Stores email as the user typed it".

4. **Why does neither the write path nor the read path normalize?**
   - **Answer:** There is no function, type, or column in the codebase that defines what "the same email" means. Every caller passes a bare `str` and the store compares bare `str`. `grep -rn "lower()\|casefold" app/` returns nothing.
   - **Evidence:** sweep output: `find_by_email` is the only lookup and is called from `app/search.py:7`, `app/signup.py:13`, `app/invite.py:7`, `app/password_reset.py:11`, all with the raw argument.

5. **Why is there no definition of email identity?**
   - **Answer:** Email was modelled as a plain `str` field on `User` (`app/db.py:10`) rather than as an identity key with its own invariant. A `str` carries no notion of equivalence beyond byte equality, so the "two casings are one account" rule had nowhere to live and nothing enforced it. Because the uniqueness check (`signup.py:13`) reuses the same broken comparison, the store also contains no constraint that would have made the gap loud.
   - **Evidence:** `app/db.py:7-11` dataclass; `app/db.py:1` docstring describing case-sensitivity as the design; no test exercised a casing mismatch before `tests/test_search.py:24` was written for this ticket.

Stop here: a fix at link 5 (a single canonical form owned by the store) prevents every sibling below. Going further ("why was it modelled as str") lands on "nobody wrote the rule down", which link 5 already converts into an actionable system change.

## Classification

- **Symptom:** search returns `not_found` for an existing customer when casing differs.
- **Proximate cause:** `app/db.py:34` byte-exact `u.email == email`, fed by `app/signup.py:15` storing the raw string.
- **Root cause:** email identity is undefined. There is no canonical form, no type distinguishing "display email" from "identity email", and no uniqueness constraint on the identity form, so each of four callers silently inherits byte-exact semantics.

### Falsification

- **If this were wrong, we would see:** `search_by_email` failing even with the exact stored casing (pointing at a different mechanism such as whitespace, encoding, or a stale index).
- **Second mechanism considered:** trailing whitespace or invisible characters from copy-paste. Distinguisher: the log shows three *casing* variants of the same address, with exactly one succeeding, and the failing test uses clean strings.
- **Experiment run:** exact-casing search → `ok, id=1`; lowercase → `not_found`; exact casing with trailing space → `not_found`. Casing alone flips the result, so the root as stated is confirmed. (Whitespace is a real second failure mode of the same root cause and is folded into the fix.)

## Siblings

All four callers of `find_by_email` share the assumption; three are broken, one is accidentally fine. Verified by probe against a store holding `Bob@Example.COM`:

| Flow | Call site | Lookup with `bob@example.com` | Severity |
|---|---|---|---|
| `signup` uniqueness check | `app/signup.py:13` | Passes the check, **creates a second account** (ids 1 and 2 both exist) | **High**: duplicate identities, and once two rows exist no fix can tell which is "real" without a merge |
| `password_reset` | `app/password_reset.py:11` | `ResetError("no such user")` | **High**: user-facing lockout, same class as the ticket but hits customers directly |
| `invite.is_already_member` | `app/invite.py:7` | `invite_sent` to an existing member | Medium: duplicate invites; combined with the signup sibling it is the path to the duplicate account |
| `search` | `app/search.py:7` | `not_found` | Medium: the reported ticket |

**Data already corrupted:** because the signup sibling has been live, the production `users` table very likely already contains case-variant duplicates. The fix must be preceded by a sweep (`SELECT lower(email), count(*) ... GROUP BY 1 HAVING count(*) > 1`) and a merge policy; adding a unique constraint on the canonical form will otherwise fail to apply. This fixture is in-memory, so I could not measure the count.

## Assumptions

1. **Assumption:** `find_by_email` is the only email lookup; there is no second path comparing emails.
   - **How validated:** `grep -rn "\.email\|email ==" app tests`.
   - **Result:** Confirmed; the only comparison is `app/db.py:34`.

2. **Assumption:** Case-insensitive matching is the desired product rule (vs. "tell support the casing rule").
   - **How validated:** The ticket's own ask ("either fix the search, or tell us the rule") and the fact that signup lets users pick any casing, so there is no rule to tell. The repro test (`tests/test_search.py:24-29`) encodes case-insensitive as expected behaviour.
   - **Result:** Confirmed as the product intent; see Open questions for the RFC caveat.

3. **Assumption:** Canonicalizing inside `db` does not break the exact-casing case or the display of the email.
   - **How validated:** prototype in a scratch copy (not in the fixture): both tests pass; `search_by_email("bob@example.com")["email"]` still returns `Bob@Example.COM`.
   - **Result:** Confirmed.

4. **Assumption:** `str.casefold()` is the right canonicalization for the local part.
   - **How validated:** It is the Unicode-correct lowercasing and matches what Gmail, Outlook, iCloud, Yahoo do. RFC 5321 technically permits a case-sensitive local part.
   - **Result:** Confirmed for mainstream providers; the RFC edge is an accepted product trade-off, not a technical unknown.

5. **Assumption:** Existing production data has no case-variant duplicates that a unique constraint would reject.
   - **How validated:** Cannot be validated in this fixture (in-memory store, no production access).
   - **Result:** UNVERIFIED. The recommended fix does not depend on it being true; it depends on running the sweep first. Surfaced as an open question.

## Fix proposals

### A. Symptom fix (smallest)

- **Files:** `app/search.py`.
- **Approach:** in `search_by_email`, fall back to a case-insensitive scan over `db.all_users()` when the exact lookup misses.
- **Tests:** the existing failing test passes.
- **Blast radius:** search only. Password reset, invite and signup remain broken; duplicate accounts keep being created, and search now has to pick one of them arbitrarily.
- **Rollback:** revert one file.
- **Verdict:** masks the cause from future detection and makes the data problem worse by hiding it. Not recommended.

### B. Root-cause fix (recommended)

- **Files:** `app/db.py` (owner of the change), `app/signup.py` (docstring and nothing else), `tests/`.
- **Approach:**
  1. Add `canonical_email(raw) -> CanonicalEmail` in `app/db.py`: `raw.strip().casefold()`. `CanonicalEmail` is a `NewType` so a bare `str` cannot be passed where an identity is expected.
  2. Add `User.email_canonical: CanonicalEmail`; keep `User.email` as the display form the user typed.
  3. `insert` computes the canonical form and asserts uniqueness on it; `find_by_email` canonicalizes its argument and compares canonical forms. No caller changes: `search`, `signup`, `invite`, `password_reset` are fixed by construction.
  4. In the real store: a generated/stored `email_canonical` column with a `UNIQUE` index, after the duplicate sweep in Open questions.
- **Tests:** the repro test; a parametrized test over all four flows with `Bob@Example.COM` / `bob@example.com` / `BOB@EXAMPLE.COM` / ` bob@example.com `; a test that a second signup with a case variant raises `SignupError`.
- **Blast radius:** every email lookup changes semantics, which is the point. Risk is concentrated in the data migration, not the code.
- **Rollback:** code revert is one module; the unique index is dropped independently. Order the rollout as sweep → code → constraint so each step is reversible on its own.
- **Prototype:** applied in a scratch copy, not in the fixture. Both tests pass; all four flows return the user for all four spellings; duplicate signup rejected; display form preserved.

**Recommendation:** B. A is a one-file patch that would quietly ship a known duplicate-account bug, and the sweep for siblings shows the cost of the class is already higher than the cost of the ticket.

## Counterfactual

Walking fix B through the captured failure: `signup("Bob@Example.COM")` stores canonical `bob@example.com`; `search_by_email("bob@example.com")` canonicalizes to the same key and matches. The repro does not fire. The fix breaks **link 4** (no normalization on either path) by construction and **link 5** (no definition of identity) by introducing the type and the invariant. Verified by running the repro and the four-flow probe against the prototype: **Confirmed**, no survivors among the known siblings. Fix A, by contrast, breaks only link 1 for search and leaves three survivors.

## Prevention

- **Test (floor):** `tests/test_search.py::test_search_finds_user_signed_up_with_mixed_case` plus the parametrized four-flow test above, so a future caller that bypasses `find_by_email` is caught.
- **Guardrail (type):** `CanonicalEmail = NewType(...)` and have `find_by_email` and `insert` accept only `CanonicalEmail` internally. With a type checker in CI, a new comparison on a raw `str` email is a type error, which is what "the class becomes impossible to express" looks like here.
- **Guardrail (data):** `UNIQUE (email_canonical)` in the real store. Makes the signup sibling loud at the database instead of silent in Python.
- **Guardrail (lint):** a grep-based check or ruff custom rule failing on `.email ==` outside `app/db.py`, so identity comparison stays in one module.
- **Doc:** record the invariant where agents and reviewers will read it (`docs/architecture.md` or `AGENTS.md`): "An email identifies at most one user. Identity is `canonical_email()`; `User.email` is display-only and must never be compared." Update the two docstrings (`app/db.py:1`, `app/signup.py:1`) that currently document the bug as the design.
- **Why no test caught it:** the only test file is the one written for this ticket. The deeper gap is that uniqueness was never stated as an invariant, so nobody knew to test it; the doc item above is the fix for that.

## Open questions

1. **Production duplicates:** how many case-variant duplicate accounts exist today, and what is the merge policy (keep oldest, keep the one with billing, manual review)? This blocks the unique constraint and needs product input.
2. **Canonical form scope:** casefold + trim only, or also provider-specific rules (Gmail dot-insensitivity, `+tag` stripping)? I recommend no: those change identity semantics beyond what support asked for and can merge genuinely different accounts. Flagging so it is a decision, not a default.
3. **Display casing:** the fix preserves what the user typed. If product prefers to display the canonical form everywhere, that is a one-line change in `insert`.
4. **Logging:** the log line `search.search_by_email email="..." -> not_found` was enough to diagnose this; worth keeping as-is and adding the canonical key once the fix lands.

## Side effects and restoration

- Working copy `OUTPUT_DIR/fixture` was read and executed, not modified: SHA-1 of every source file matches the baseline taken at step 1.
- The prototype fix lives only in the scratchpad (`/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/rca-cf/fixture/app/db.py`).
- Nothing pushed, published, or sent.

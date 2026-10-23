# RCA: user search misses customers when email casing differs

## 1. Headline

Email is treated as an opaque, case-sensitive string everywhere in `app/`: signup stores it exactly as typed, and the single lookup `db.find_by_email` compares with `==`. The search endpoint is only the first place this surfaced. The same comparison also lets **duplicate accounts** be created, makes **password reset** fail, and lets **team invites** go to people who are already members. Recommended fix: define email identity once, at the storage boundary (`db.py`), as a canonical form applied on both write and read, plus a backfill of existing rows and a uniqueness invariant so the class cannot recur.

## 2. Symptom and scope

- **What support saw** (BUG_REPORT.md, verbatim log):
  ```
  2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
  2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
  2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
  ```
  Same customer, three attempts, only the casing the customer originally typed matches.
- **Who / since when / how often:** 4 support agents in 24h starting 2026-05-12; P2; 5-10 minutes lost per affected ticket; workaround is paging the data team for a SQL query.
- **Expected:** `search_by_email("jane.smith@gmail.com")` finds user 8412. **Actual:** `not_found`.
- **Repro:** deterministic, `tests/test_search.py::test_search_finds_user_signed_up_with_mixed_case`. Ran it on the fixture copy: `AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}` (1 failure of 2 tests).
- **Baseline:** the fixture is a plain directory (untracked in the parent repo, no git history). Working copy at `.../run-2/outputs/fixture`; verified byte-identical to `evals/rca/fixture` at the end of the investigation. No edits were made to it; all experiments ran from a scratch directory.

## 3. Timeline

There is no commit history to bisect: `git log -- evals/rca/fixture` is empty and the directory is untracked. Two pieces of evidence say the behaviour is original, not a regression:

- `app/db.py:1` docstring: `"""In-memory user store. Case-sensitive lookups by email."""`
- `app/signup.py:1` docstring: `"""Signup flow. Stores email as the user typed it."""`

So the code did not change; **the inputs did**. Per the skill's rule for bugs that predate every change, the likely trigger is a shift in how emails arrive at signup (mobile keyboards auto-capitalising the first letter, users typing their address as their mail client displays it). I could not confirm that shift from the fixture; it is listed as an open question in section 9.

## 4. 5-whys chain

1. **Why did search return `not_found` for a user who exists?**
   - **Answer:** `search_by_email` delegates entirely to `db.find_by_email` and maps `None` to `not_found`; the lookup returned `None`.
   - **Evidence:** `app/search.py:7-9`; failing test output above.

2. **Why did `find_by_email` return `None`?**
   - **Answer:** It does a linear scan with exact string equality, `u.email == email`. `"Bob@Example.COM" == "bob@example.com"` is `False`.
   - **Evidence:** `app/db.py:32-36`. Probe P0: stored value is `'Bob@Example.COM'`, 15 chars, no whitespace or Unicode oddities, so casing is the only difference.

3. **Why is the stored value mixed-case?**
   - **Answer:** `signup` passes the raw string straight to `db.insert`, which stores it verbatim. There is no normalisation anywhere in the codebase.
   - **Evidence:** `app/signup.py:15`, `app/db.py:26`; `grep -rn -i "lower()\|casefold\|normali[sz]e\|strip()" app tests` returns nothing.

4. **Why is there no normalisation step?**
   - **Answer:** The code has no notion of email *identity* separate from the email *string*. `User.email` is typed `str` (`app/db.py:10`), and every caller passes whatever `str` it received. Nothing in the type system or the data layer expresses "two spellings can denote the same mailbox".
   - **Evidence:** `app/db.py:7-11`; all four callers pass raw input: `app/search.py:7`, `app/signup.py:13`, `app/invite.py:7`, `app/password_reset.py:11`.

5. **Why does the data layer lack that notion?**
   - **Answer:** The equality rule for emails was never written down as an invariant. The only statements of behaviour are the two docstrings in step 3, which *document* the case-sensitivity as a fact rather than *decide* it as a rule. With no stated contract, each flow inherited the simplest possible comparison, and nothing (test, type, constraint) could flag the gap.
   - **Evidence:** `app/db.py:1`, `app/signup.py:1`; `tests/test_search.py` is the only test file and the mixed-case case was added only after the ticket (per its docstring, "Deterministic repro of the user-reported bug").

Stopping here: a fix at this level (define the identity rule once, enforce it at the boundary) closes every sibling found in section 6. One level further down ("nobody thought about it") is the no-op "human error" conclusion.

## 5. Classification and falsification

| Label | What |
|---|---|
| **Symptom** | Support's search returns `not_found` for customers who exist, unless the casing matches what the customer typed at signup. |
| **Proximate cause** | `app/db.py:34` compares email strings with `==`; `app/db.py:26` stores them verbatim. |
| **Root cause** | No defined, enforced canonical form for email identity. Identity is left to raw string equality at a `str`-typed field, so every flow that touches an email inherits case-sensitivity. |

**Falsification of the root:**

- *What would we see if this were not the cause?* Searches with the exact stored casing would also fail (they don't: third log line, and the lowercase test passes), or stored values would differ in some other way (whitespace, Unicode). Probe P0 rules the latter out: the stored value is exactly the typed string.
- *Second mechanism producing the same symptom?* (a) Duplicate accounts: support might be finding the wrong one of two records. This does not explain `not_found`, but it is a real adjacent failure and is itself caused by the same `==` (sibling S1). (b) Trailing whitespace or invisible characters in stored emails. Not present in the fixture (P0); cannot be excluded for production data without a query (open question Q2).
- *Cheapest disconfirming experiment, run:* monkeypatch `find_by_email` to compare with `casefold()` and rerun the four flows (probe P5). All four pass. If the root were elsewhere, at least one would still fail. It also shows the naive fix of lowercasing only the query (probe P4) still returns `not_found`, because the stored side is still mixed-case.

## 6. Sibling sweep

`grep -rn find_by_email app` lists exactly four callers. Every one is affected; probed on the fixture copy:

| ID | Site | Behaviour today (probe) | Severity |
|---|---|---|---|
| S0 | `app/search.py:7` search | `not_found` for differently-cased query (the ticket) | P2, reported |
| **S1** | `app/signup.py:13` uniqueness check | **Second account created** for `bob@example.com` when `Bob@Example.COM` exists: ids `[1, 2]` (probe P1) | **Higher than the ticket.** Silent data corruption: two users for one mailbox. Billing, auth, and GDPR requests now have to pick one. |
| S2 | `app/password_reset.py:11` | `ResetError: no such user` when the user types a different casing than at signup (probe P2) | Customer-facing lockout; probably generating its own support tickets under a different title. |
| S3 | `app/invite.py:7` membership check | `{'status': 'invite_sent'}` to an address that already belongs to a member (probe P3) | Low to medium: duplicate invites, and a path into S1 if the invite leads to a second signup. |

Data already affected: in production, any pair of rows whose emails are equal after case-folding is an S1 duplicate. The fixture store is in-memory and empty at boot, so I could not measure this; see Q1.

## 7. Assumptions

1. **Assumption:** `db.find_by_email` is the only place emails are compared.
   - **How validated:** `grep -rn "email" app` lists every use; the only comparison is `app/db.py:34`.
   - **Result:** Confirmed.
2. **Assumption:** `db.insert` is the only write path for `User.email`.
   - **How validated:** same grep; only `app/db.py:26` constructs a `User`.
   - **Result:** Confirmed.
3. **Assumption:** The whole address (local part and domain) may be compared case-insensitively.
   - **How validated:** RFC 5321 makes the local part technically case-sensitive, but every major mail provider treats it as insensitive and the product already needs this for support, reset, and uniqueness to make sense. The bug report's three casings of one customer are themselves evidence that users treat it as insensitive.
   - **Result:** Confirmed as a product decision, not a protocol fact. It should be written down (prevention, section 9).
4. **Assumption:** Case-folding at the data layer does not change the displayed email in a way that matters.
   - **How validated:** `search_by_email` returns `user.email` (`app/search.py:10`); after the fix it would return the canonical lower-case form instead of what the user typed.
   - **Result:** Confirmed as a behaviour change; harmless for lookup, but if a product surface wants to show the user's preferred casing, store it in a separate display column. Flagged in Q3.
5. **Assumption:** No production rows contain whitespace or invisible characters around the email.
   - **How validated:** Not possible from the fixture.
   - **Result:** UNVERIFIED. The recommended fix uses `strip()` as well as `casefold()`, so it does not depend on this; the backfill query (Q2) should check it.
6. **Assumption:** Existing duplicate rows (S1) can be merged without data loss.
   - **How validated:** Not possible from the fixture.
   - **Result:** UNVERIFIED. The code fix does not depend on it; the backfill does. Open question Q1.

## 8. Fix proposals

### A. Symptom fix (smallest change that stops the ticket)

- **Files:** `app/db.py:34` only.
- **Approach:** `if u.email.casefold() == email.casefold(): return u`.
- **Tests:** the existing failing test passes.
- **Blast radius:** every caller of `find_by_email` becomes case-insensitive at once, which is what we want; S1 to S3 are closed for *new* operations. Existing duplicate rows remain, and `find_by_email` now returns the first of them, which is arbitrary.
- **Rollback:** revert one line.
- **Why it is not enough:** the canonical form is still undefined. The next person who adds `find_by_domain`, a bulk import, or a SQL-backed store will write `==` again, because the data model still says `email: str` and the docstring still says "case-sensitive".

### B. Root-cause fix (recommended)

- **Files:** `app/db.py`, docstrings in `app/signup.py`, new test file, a one-off backfill.
- **Approach:**
  1. In `db.py`, add `canonical_email(raw) -> CanonicalEmail` (`strip().casefold()`) and a `CanonicalEmail = NewType("CanonicalEmail", str)`. This is the single definition of email identity.
  2. `insert` canonicalises before storing; `find_by_email` canonicalises the query before comparing. Both write and read go through the same function, so a caller cannot get it wrong.
  3. `insert` asserts the uniqueness invariant ("one user per canonical email"), so a bypass of `signup`'s check fails loudly rather than silently duplicating.
  4. `User.email` becomes `CanonicalEmail`, so a raw `str` landing in the field is a type-checker error.
  5. Update the two docstrings that currently state case-sensitivity as the design.
  6. Backfill: canonicalise existing rows; detect collisions (`SELECT lower(trim(email)), count(*) ... GROUP BY 1 HAVING count(*) > 1`) and merge them by an explicit, reviewed rule before adding a unique index on the canonical column.
- **Tests:** the existing test; a `db`-level table test (mixed case, whitespace, repeat signup rejected, reset and invite with varied casing); a test that `insert` refuses a canonical duplicate.
- **Blast radius:** all four flows change behaviour in the intended direction. Displayed email becomes lower-case (assumption 4). The backfill touches every row and must run before the unique index.
- **Rollback:** the code change is a single module and reverts cleanly. The backfill is one-way once duplicates are merged; keep the pre-merge rows in an archive table.

**Recommendation:** B. A alone leaves the rule unstated and the duplicates in place; given S1 is worse than the reported bug, shipping A and stopping would mask the more expensive problem. If a hotfix is needed today, ship A as step 1 of B (it is literally B's step 2 without the type and invariant), not instead of it.

## 9. Counterfactual

Applied fix B to a scratch copy and reran the real test suite: `Ran 2 tests ... OK`. Reran the sibling probes against the fixed copy: duplicate signup `rejected: email already registered`; reset with other casing returns a token; invite reports `already_member`; the lookup of a row inserted as `Bob@Example.COM` with query `bob@example.com` returns `ok`.

- **Which link breaks:** link 2 (comparison) and link 3 (storage) at once, because both now go through `canonical_email`; link 5 (no stated rule) is closed by the function, the type, and the docstring.
- **Verdict: Confirmed, with one survivor outside the code.** Rows already stored mixed-case in production are found by the new `find_by_email` (it canonicalises both sides), so searches work immediately. But existing *duplicate pairs* (S1 history) are not resolved by code; the backfill in B.6 is required, and until it runs `find_by_email` returns the lower-id duplicate.

## 10. Prevention of the class

- **Test (floor):** a `tests/test_email_identity.py` table test across all four flows with casings and surrounding whitespace, plus "second signup with different casing is rejected". This would have caught S0 to S3 the day the flows were written.
- **Guardrails (the actual prevention):**
  - The `CanonicalEmail` NewType on `User.email` and on `find_by_email`'s internal key: a raw `str` cannot be stored or compared without going through `canonical_email`, and a type checker says so in CI.
  - The uniqueness assertion in `db.insert` (a `UNIQUE` index on the canonical column once this is a real database): the class "two rows, one mailbox" becomes impossible, not merely unlikely.
  - A lint or review rule: any new `== email` or `.email ==` outside `db.py` is a review blocker. Cheap to express as a grep in CI.
- **Doc update:** write the identity rule down where new code will see it, for example in `db.py`'s module docstring and the project's invariants file if one exists: "An email identifies a user by its canonical form (`strip().casefold()`). All storage and comparison goes through `db.canonical_email`. Never compare raw email strings." The absence of this sentence is link 5 of the chain.
- **Answer to support's question** ("tell us the rule for which casing to use"): after fix B there is no rule to remember; any casing works. Until then, the rule is "the casing the customer typed at signup", which is the honest reason the tool feels random.

## 11. Open questions

- **Q1.** How many duplicate pairs exist in production? Run `SELECT lower(trim(email)) AS k, count(*) FROM users GROUP BY k HAVING count(*) > 1` before the backfill. The merge rule (keep oldest? keep the one with billing history?) needs a product decision; I have not assumed one.
- **Q2.** Do any stored emails carry whitespace or non-ASCII look-alikes? Same query family; affects whether `strip()` alone is sufficient or whether Unicode normalisation (NFKC) belongs in `canonical_email`.
- **Q3.** Does any surface need the email as the user typed it (display, outgoing mail headers)? If so, add a separate display column rather than weakening the canonical one.
- **Q4.** What changed on or before 2026-05-12 in the signup inputs (new mobile client, an import, a marketing form)? The code is unchanged, so the trigger is upstream; knowing it would tell us whether other fields (usernames, phone numbers) got the same treatment.

## Investigation footprint

- No edits to the fixture copy; verified identical to `evals/rca/fixture` with `diff -r`.
- Probe script and the patched scratch copy live under the session scratchpad (`/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/rca-probe/`), not in the repo.
- Nothing pushed, published, or sent.

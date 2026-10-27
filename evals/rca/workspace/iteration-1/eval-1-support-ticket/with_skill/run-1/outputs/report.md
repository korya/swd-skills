# RCA: user-search misses customers when email casing differs from signup

## 1. Headline

`db.find_by_email` does a case-sensitive `==` comparison, while emails are case-insensitive by spec (RFC 5321 §2.4 — the local part is technically case-sensitive but in practice every major MTA folds it; the domain part is always case-insensitive). The signup flow stores whatever the user typed; every downstream lookup compares verbatim. **Root-cause fix:** normalize email at the storage boundary (signup/insert) and at every lookup, by lower-casing — and enforce it with a single chokepoint (`db.insert` / `db.find_by_email`) so no future call site can re-introduce the bug. Symptom-only fix (search.py-only) is not recommended — it leaves three siblings live, including a duplicate-account creation path.

## 2. Symptom / scope

- **Symptom (verbatim from logs):**
  ```
  2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
  2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
  2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
  ```
  Same customer, three attempts, only the casing that happened to match the stored row succeeded.
- **Scope:** Reported by 4 support agents in 24h (per `BUG_REPORT.md`). Affects every user whose stored email casing differs from the casing the agent types. Latent across the whole user base — only "visible" when casings happen to mismatch.
- **Expected vs. actual:** Expected — search by email is case-insensitive (standard product behaviour for email lookup; what every agent assumed). Actual — search is case-sensitive verbatim.
- **First seen:** 2026-05-12; bug is latent and pre-dates that date — what's new is the volume of mixed-case signups (or the fact that agents only recently started looking up by hand).
- **Repro (deterministic):**
  ```sh
  cd evals/rca/fixture
  python3 -m unittest tests.test_search.SearchTests.test_search_finds_user_signed_up_with_mixed_case -v
  ```
  Result observed (this run):
  ```
  AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
  ```

## 3. Timeline

Git history in the fixture has two commits (`e35cfad` initial, `03ba92a` doc change). No relevant code change between known-good and known-bad — there is no known-good. The defect is **latent from the initial commit**: `db.find_by_email` (`app/db.py:34`) was written with `u.email == email`, and `signup.signup` (`app/signup.py:15`) stores the address verbatim via `db.insert(email=email, ...)`. The "change" exercising it is upstream — more users typing mixed-case emails, or support workflows now hitting the search endpoint more often. Cause is in the *inputs*, not in any code delta.

## 4. 5-whys chain

1. **Why did `search_by_email("bob@example.com")` return `not_found` for a user who signed up as `Bob@Example.COM`?**
   - **Answer:** `search.search_by_email` delegates to `db.find_by_email`, which returned `None`.
   - **Evidence:** `app/search.py:7-9` — `user = db.find_by_email(email); if user is None: return {"status": "not_found"}`. Repro confirms `not_found` (test output above).

2. **Why did `db.find_by_email` return `None` for that input?**
   - **Answer:** It scans `_USERS` and compares with `u.email == email`. The stored value is `"Bob@Example.COM"`, the query is `"bob@example.com"`; Python `str.__eq__` is case-sensitive, so no row matches.
   - **Evidence:** `app/db.py:32-36` —
     ```python
     def find_by_email(email: str) -> Optional[User]:
         for u in _USERS:
             if u.email == email:
                 return u
         return None
     ```

3. **Why is the stored value `"Bob@Example.COM"` rather than a canonical form?**
   - **Answer:** `signup.signup` passes the raw user-supplied string through to `db.insert` with no normalization.
   - **Evidence:** `app/signup.py:10-15` — `def signup(email, name): ... return db.insert(email=email, name=name)`. No `.lower()`, no `.strip()`, no normalization helper.

4. **Why is there no normalization at the storage boundary (or at the lookup boundary)?**
   - **Answer:** The module owns `find_by_email` as a public API but the file's own docstring **promises case sensitivity** as if it were a feature: `"""In-memory user store. Case-sensitive lookups by email."""` (`app/db.py:1`). The case-sensitivity is encoded as intended behaviour, not flagged as a bug. There is no canonicalization helper anywhere in `app/`.
   - **Evidence:** `app/db.py:1` docstring; `grep -rn "\.lower\(\)\|normalize\|canonical" app/` → no matches.

5. **Why was case-sensitive lookup encoded as "intended behaviour" with no contract or invariant calling out that email equality is supposed to be case-insensitive?**
   - **Answer:** No invariant / spec / type captures "email identity is case-insensitive" anywhere in the repo. `User.email` is a plain `str` (`app/db.py:11`), so the type system can't tell a normalized address from a raw one. There is no `EmailAddress` value object, no DB-level unique index with `lower(email)`, no doc that says "store canonical form." The four call sites (`signup.py`, `search.py`, `invite.py`, `password_reset.py`) all independently call `find_by_email(email)` with whatever string they were handed — none of them normalize either. The class of bug is *expressible by default* and *invisible to review*: every new feature that touches email will reproduce it unless the author happens to remember.
   - **Evidence:** `grep -rn "find_by_email" app/` → 4 call sites, none normalize; `app/db.py:7-11` shows `User.email: str` (no wrapper type); no `docs/`, no `AGENTS.md`, no schema enforcing canonical form in the fixture.

Each link is verified against `file:line`. No `UNVERIFIED` links.

## 5. Symptom / proximate / root

- **Symptom:** Support agents get `not_found` for users they know exist; same user requires guess-the-casing to locate.
- **Proximate cause:** `u.email == email` in `app/db.py:34` is a case-sensitive comparison against a non-canonical stored value.
- **Root cause:** No enforced invariant that "stored email = canonical email," combined with no shared chokepoint that normalizes at the boundary. The data model treats email as an arbitrary `str`; the docstring even codifies case sensitivity as a feature. Any current or future code path that writes or reads email is free to introduce this bug, and review has nothing to catch it on.

### Falsifying the root cause

- **What would we see if the root cause were *not* "missing canonicalization invariant"?**
  - If the real cause were a bug in *only* `search.search_by_email` (e.g., wrong helper used), then `invite.is_already_member`, `signup`-uniqueness, and `password_reset.request_reset` would behave correctly under mixed casing. They don't (see Siblings §6) — all four call sites of `find_by_email` exhibit the same defect, which is exactly the fingerprint of a missing shared invariant rather than a local bug.
  - If the real cause were "the stored value is wrong but lookups are fine," then querying with the exact stored casing would also fail. It doesn't — the `test_search_finds_user_signed_up_with_lowercase` test passes, confirming lookup works *when casings match*. That's consistent with "case-sensitive equality on a non-canonical store," i.e., the stated root.
- **Alternative mechanism considered:** Could the test be wrong (e.g., support actually wants case-sensitive search and the report is a UX complaint)? No — the support ticket explicitly says agents want one of {fix the search, tell us the rule}, and "case-insensitive email" is the cross-industry default. Treating email as case-sensitive would be the surprising design, and would need a documented reason. None exists in the repo.
- **Cheapest disconfirming experiment:** ran the sibling probe (§6) — if only `search` were affected, `invite.send_invite("bob@example.com")` would have returned `invite_sent`, not `already_member`-via-luck or the inverse. The probe instead exposed three independent siblings, supporting "shared missing invariant" over "local bug in search."

## 6. Sibling-impact sweep

`grep -rn "find_by_email" app/` returns four call sites. I ran each against the same setup as the failing test (`signup.signup(email="Bob@Example.COM", name="Bob")`) and queried with a different casing.

| # | Call site | Mixed-case behaviour | Severity |
|---|---|---|---|
| 1 | `app/search.py:7` — `search_by_email` | Returns `not_found` for existing user. | P2 — the reported bug. |
| 2 | `app/signup.py:13` — uniqueness check | **Creates a duplicate account.** `signup.signup(email="bob@example.com", ...)` after the original Bob succeeds and returns `id=2`. Verified: `len(db.all_users()) == 2`. | **P1 — data corruption, silent.** Duplicate identity, billing/auth ambiguity. |
| 3 | `app/invite.py:6` — `is_already_member` | Returns `False` for an existing member when casing differs → `invite_sent` is returned for someone who already has an account. Verified: `invite.send_invite("bob@example.com")` → `{"status": "invite_sent", ...}` after Bob exists. After the duplicate account in sibling #2 is created, `send_invite("bob@example.com")` flips to `already_member` — i.e., the answer depends on which account got created last. | P2 — wrong invites; worsens after sibling #2 fires. |
| 4 | `app/password_reset.py:11` — `request_reset` | Without a duplicate: raises `ResetError("no such user")`. With the duplicate from sibling #2 present: returns `reset-token-for-2` — **a reset token bound to the wrong (duplicate) user id**. Verified by repro. | **P1 — auth-adjacent.** Reset tokens routed to a different user record than the one the requester thinks they're using. |

All four are manifestations of the same root cause. A fix only in `search.py` leaves three live, including a data-corruption path that *makes the others worse over time*.

Note: there is no persistent store in this fixture (in-memory `_USERS`), so there is no historical corrupted-data sweep to run. In a real system the equivalent would be `SELECT email, lower(email), count(*) FROM users GROUP BY lower(email) HAVING count(*) > 1` to find pre-existing duplicates created by sibling #2.

## 7. Load-bearing assumptions

1. **Assumption:** Email identity is intended to be case-insensitive (i.e., `Bob@Example.COM` and `bob@example.com` are the same user).
   - **How validated:** (a) Support ticket explicitly asks for case-insensitive lookup or a documented rule; (b) industry default — every major MTA folds the local part; the domain part is case-insensitive per RFC 1035; (c) the lowercase test (`test_search_finds_user_signed_up_with_lowercase`) and the mixed-case test treat them as identical lookups.
   - **Result:** Confirmed (with the standard caveat below).

2. **Assumption:** Lower-casing the entire email string is a safe normalization for this product.
   - **How validated:** Read RFC 5321 §2.4 — the local part is *technically* case-sensitive but in practice every major provider treats it case-insensitively; lower-casing is the standard pragmatic canonicalization (Gmail, Outlook, Apple, etc. all fold). The fixture has no exotic providers and no contractual reason to preserve casing.
   - **Result:** Confirmed for this product context. (Surface as caveat: if the product ever needs strict-RFC equality, switch to "case-insensitive domain, case-sensitive local" canonicalization. Doesn't affect the recommended fix; the chokepoint is the right place to change the rule later.)

3. **Assumption:** All writes go through `db.insert` and all reads go through `db.find_by_email` (i.e., normalizing at these two points covers every path).
   - **How validated:** `grep -rn "_USERS\|db.insert\|find_by_email" app/` — `_USERS` is only mutated in `db.reset` and `db.insert`; every email lookup goes through `find_by_email`. No back-doors.
   - **Result:** Confirmed.

4. **Assumption:** No existing caller depends on preserving the original casing of `User.email` for *display* (e.g., emailing the customer with their preferred casing).
   - **How validated:** `grep -rn "\.email" app/` — no display path; `search.search_by_email` returns the stored email but support is asking to *find* users, not to render their preferred casing. No test asserts casing preservation.
   - **Result:** Confirmed for the fixture. (Caveat for production: if display casing matters, store both `email` (canonical) and `email_display` (raw). Doesn't change the lookup invariant.)

5. **Assumption:** Lower-case ASCII `.lower()` is sufficient for this codebase (no IDN / Unicode-email handling needed).
   - **How validated:** No IDN handling exists in the fixture; emails in the bug report and tests are ASCII. The fixture's scope is the support ticket.
   - **Result:** Confirmed for the fixture. Surface as open question (§10) for production.

No `UNVERIFIED` assumptions remain. The recommended fix depends only on confirmed assumptions; the caveats above are scope-limited and listed transparently.

## 8. Fix proposals

### 8a. Symptom fix (smallest change)

Lower-case the query in `app/search.py` only.

```python
def search_by_email(email: str) -> dict:
    user = db.find_by_email(email.lower())  # <-- only this changes
    ...
```

- **Blast radius:** Only `search.search_by_email`.
- **Pros:** One-line change; ships the support ticket.
- **Cons:** **Does not fix siblings 2/3/4**, and one of them is P1 data corruption. Also, it'll *still* miss users whose stored email is mixed-case (e.g., `Bob@Example.COM` stored, query `bob@example.com` → lower-casing the query gives `bob@example.com`, which still ≠ `Bob@Example.COM` stored). So this one-liner doesn't even fix the reported symptom unless the stored side is *already* lower. To make it work as a symptom fix, you'd need `email.lower() == u.email.lower()` in `find_by_email` — effectively forcing you toward the chokepoint anyway.
- **Test coverage:** `tests/test_search.py` already covers this once the comparison is two-sided.
- **Rollback:** trivial.

### 8b. Root-cause fix (recommended)

Make canonical form a *property of the data model*. Two enforced chokepoints:

1. **`db.insert(email, name)`** — lower-case before storing: `email = email.strip().lower()`.
2. **`db.find_by_email(email)`** — lower-case the query the same way: `key = email.strip().lower(); ... if u.email == key`.

Rationale for normalizing on *both* sides (rather than only inside `find_by_email`):
- Storing the canonical form makes "the stored value is the canonical value" a *visible invariant in the data*, not an implicit promise of every query path.
- It makes sibling #3 (duplicate signup) impossible at the data layer: `db.find_by_email(email)` inside `signup.signup` will hit the existing row and the duplicate-check fires.
- It makes sibling #4 (wrong reset token) impossible because there is at most one row per canonical email.

Also: **delete the misleading docstring** at `app/db.py:1` ("Case-sensitive lookups by email") and replace it with "Email is stored canonical (lowercased, stripped); lookups are case-insensitive by construction." The docstring was actively misdirecting future readers.

- **Files:** `app/db.py` (insert + find_by_email + docstring + `User.email` invariant comment).
- **Blast radius:** All four call sites benefit; none break (none depend on casing preservation — assumption #4).
- **Test coverage:** existing `test_search_finds_user_signed_up_with_mixed_case` passes; add three more (see §9).
- **Rollback:** revert the one file. In a real system with a persistent DB, the rollback would also need to consider already-canonicalized rows; in this fixture, trivial.

### 8c. Recommendation

**Ship 8b (root-cause fix).** Reasons:
- The "symptom fix" doesn't actually fix the symptom unless it lower-cases both sides — at which point you've already done the chokepoint work in `find_by_email` and not doing it in `db.insert` *as well* leaves silent data corruption (sibling #2) shipping in prod every day.
- Blast radius is identical (one file).
- Risk is lower for `8b` than for `8a`, not higher: `8b` makes all four call sites correct at once; `8a` leaves three latent bugs whose interaction (sibling #2 → sibling #4) is the worst kind — silent and auth-adjacent.

## 8.5. Counterfactual check on the recommended fix

If the root-cause fix (8b) had been in place when the captured failure was recorded:

- **Repro walk-through:** `signup.signup(email="Bob@Example.COM", name="Bob")` would have called `db.insert(email="Bob@Example.COM", ...)`, which would strip-and-lower to `"bob@example.com"` before appending to `_USERS`. The subsequent `search.search_by_email("bob@example.com")` → `db.find_by_email("bob@example.com")` would normalize the query to `"bob@example.com"` and match. Returns `{"status": "ok", ...}`.
- **Which link is broken:** Link 3 (no normalization at the storage boundary) **and** Link 4 (no normalization at the lookup boundary) are both broken — the fix sits exactly at the layer the root cause identified. Link 5 (no invariant) is *softened* (the chokepoint now exists) but the invariant could still be re-broken by a future call site that constructs a `User` directly — see §9 for the prevention against that.
- **Sibling counterfactuals (same repro, sibling paths):**
  - Sibling #2 (duplicate signup): `signup.signup(email="bob@example.com", ...)` after the original Bob would normalize to `"bob@example.com"`, `find_by_email` would normalize the existing row's lookup the same way, the uniqueness check returns "already registered." Fixed.
  - Sibling #3 (invite): `invite.is_already_member("bob@example.com")` normalizes to `"bob@example.com"` and matches the canonical stored row. Returns `True`. Fixed.
  - Sibling #4 (password reset): `password_reset.request_reset("bob@example.com")` normalizes, finds Bob (id=1), returns `reset-token-for-1`. Fixed.
- **Verdict: Confirmed.** Repro would not fire under the fix; all listed siblings would also not fire. No survivors at the application layer.

(Survivor at the meta layer: a *new* call site that bypasses `db.insert`/`db.find_by_email` — e.g., by appending to `_USERS` directly or comparing `u.email == something` outside `db.py` — would re-introduce the class. The prevention items in §9 address this.)

## 9. Prevention (kill the class, not the instance)

The point isn't to make this exact test pass; it's to make the class of "email compared raw" hard to write.

1. **Tests** (floor — adds the regression but doesn't prevent the class):
   - Keep `test_search_finds_user_signed_up_with_mixed_case`.
   - Add: `test_signup_rejects_duplicate_with_different_casing` (sibling #2).
   - Add: `test_invite_recognises_existing_member_with_different_casing` (sibling #3).
   - Add: `test_password_reset_finds_user_with_different_casing` and `test_password_reset_is_unambiguous_after_dup_attempt` (sibling #4).

2. **Guardrails** (stronger — make the class harder to express):
   - **Invariant in `db.py`:** add an assertion in `db.insert` that `email == email.strip().lower()`, so any bypass (e.g., a future caller that constructs a `User` and appends to `_USERS` directly) is loud, not silent. Better yet, make `_USERS` private with a single public `insert` and never expose the list for mutation (already the case here — keep it that way).
   - **Type-level fix (strongest in this language):** introduce a `CanonicalEmail` value object — a `dataclass(frozen=True)` with a constructor that normalizes, and make `User.email: CanonicalEmail`. Now `u.email == raw_string` is a *type error*, and `find_by_email(raw: str)` must canonicalize at the boundary by construction. This makes the class of bug *unspellable* outside the canonicalization boundary.
   - **Repository-level:** if/when this codebase grows a real DB, add a `UNIQUE INDEX ON lower(email)` (or store the canonical column and unique-index it). Belt and braces.

3. **Docs / contracts:**
   - Rewrite the `db.py` module docstring from "Case-sensitive lookups by email" to "Email is stored canonical (lowercased, stripped); lookups are case-insensitive by construction. Do not bypass `insert`/`find_by_email`."
   - If the project follows `AGENTS.md` / `docs/invariants.md` conventions (see `repo-docs` skill), add an invariant: **INV-EMAIL-CANONICAL — every persisted email is in canonical form; identity comparison uses canonical form.** Link it from `db.py`.

The "test for this exact bug" line in §9.1 is the *floor*; §9.2's `CanonicalEmail` type is the ceiling and what I'd actually push for.

## 10. Open questions

1. **Strict-RFC semantics:** Do we ever need to honour RFC 5321's strict rule that the *local part* is case-sensitive? (Assumption #2.) If yes, canonicalize as `local + "@" + domain.lower()` and document. Default recommendation: lower-case the whole thing; revisit if a customer ever complains.
2. **Display casing:** Do support/marketing systems want to preserve the casing the user typed, for outbound emails? (Assumption #4.) If yes, store both `email` (canonical, used for identity) and `email_display` (raw, used for rendering). Doesn't change the identity rule; just adds a column/field.
3. **Existing data:** In a real (persistent) deployment, are there already duplicate rows created by sibling #2? Run `SELECT lower(email), count(*) FROM users GROUP BY lower(email) HAVING count(*) > 1` and decide a merge policy before enforcing a `UNIQUE INDEX ON lower(email)`. N/A for the fixture; mandatory for prod.
4. **Unicode / IDN emails:** (Assumption #5.) If the product ever ingests non-ASCII addresses, `.lower()` isn't enough — needs `email_normalize` or equivalent (NFKC + case-fold + IDN ToASCII for the domain). Surface for the production version.
5. **Whitespace and the rest of the canonicalization rule:** I've assumed `strip()` is desirable (trailing spaces from copy-paste). If product disagrees (e.g., wants `"  alice "` rejected as invalid rather than silently trimmed), `signup.signup` should validate-then-canonicalize and `db.insert` should `assert` the canonical form — same chokepoint, different policy.

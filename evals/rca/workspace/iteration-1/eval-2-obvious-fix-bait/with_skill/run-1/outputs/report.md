# RCA: customer-support cannot find users by email when casing differs

## Headline
User lookups silently miss when the searcher's casing differs from the stored email. **Proximate cause:** case-sensitive equality at `app/db.py:34` (`u.email == email`). **Root cause:** emails are stored and looked up as opaque case-sensitive strings with no normalization chokepoint and no type-level constraint encoding the product invariant ("email identity is case-insensitive"). The user's proposed `email.lower() == u.email.lower()` in `app/search.py` **fixes only one of four affected call sites** and leaves a silent duplicate-signup bug active (`signup.py:13`). **Recommended fix: normalize at `db.py` (`insert` + `find_by_email`), not at one caller.**

## Symptom / scope
- **Symptom:** `search.search_by_email("jane.smith@gmail.com") → not_found` for a user stored as `Jane.smith@gmail.com`. ~5–10 min lost per support ticket (BUG_REPORT.md L29).
- **Scope:** Any user whose stored email casing differs from the searcher's input. From the bug logs, ≥1 confirmed; population is "every user the support team searches for who didn't sign up in all-lowercase."
- **Expected:** Case-insensitive lookup (industry norm, matches support's mental model).
- **Actual:** Case-sensitive at the equality check.
- **First seen:** 2026-05-12 — but latent since inception (see Timeline).
- **Repro:** `python3 -m unittest tests.test_search.SearchTests.test_search_finds_user_signed_up_with_mixed_case` — fails `AssertionError: 'not_found' != 'ok'`. Reproduced.

## Timeline
`git log --oneline`: two commits total, `e35cfad Initial commit` and a docs follow-up. **No known-good version exists** — defect is latent from inception. The "change" that started exercising it is a usage pattern shift (support agents now type emails as customers wrote them), not a code change. No deploys / migrations involved.

## 5-whys chain (every link verified)

1. **Why does `search_by_email("bob@example.com")` return `not_found` when Bob signed up as `Bob@Example.COM`?**
   - **Answer:** `db.find_by_email` returned `None`.
   - **Evidence:** `app/search.py:7-9` returns `not_found` when `find_by_email` is `None`. Test output: `AssertionError: 'not_found' != 'ok'`.

2. **Why did `db.find_by_email` return `None` when Bob is in `_USERS`?**
   - **Answer:** The equality `u.email == email` compares `"Bob@Example.COM"` to `"bob@example.com"` byte-for-byte; Python `str.__eq__` is case-sensitive; no row matches.
   - **Evidence:** `app/db.py:32-36`.

3. **Why is the equality check case-sensitive?**
   - **Answer:** The store treats `email` as an opaque string identifier — `db.insert` stores it as passed (`app/db.py:26`), `find_by_email` doesn't canonicalize the needle. The module docstring even codifies the wrong invariant: `"""In-memory user store. Case-sensitive lookups by email."""` (`app/db.py:1`).
   - **Evidence:** `app/db.py:1`, `app/db.py:26`, `app/db.py:34`. `app/signup.py:1` corroborates: `"""Signup flow. Stores email as the user typed it."""`.

4. **Why is `email` treated as an opaque case-sensitive identifier when the product treats it as case-insensitive?**
   - **Answer:** No shared invariant exists for "email identity." Each caller hands raw user input to `db.find_by_email`; the store has no normalization step; no helper enforces a canonical form. The rule support is asking for (BUG_REPORT.md L29) does not exist in code, docs, or tests.
   - **Evidence:** `grep -rn "lower\|casefold\|normalize\|strip" app/` returns nothing. No `email_utils.py`. Four call sites — `search.py:7`, `signup.py:13`, `invite.py:7`, `password_reset.py:11` — all pass raw input.

5. **Why is there no such invariant?**
   - **Answer:** The data model carries no constraint stronger than "a string" — no schema, no validator, no `Email` value type that would force normalization at a single chokepoint. There is nowhere for the rule to live, so reviewers and authors had no surface that required them to think about casing. Design gap, not author oversight.
   - **Evidence:** `app/db.py:7-11` — `User` is three plain fields, no validation, no `__post_init__`. The module docstring actively codifies the wrong invariant ("Case-sensitive lookups by email").

**Stopping criterion:** A fix at link 5 (normalize at the storage chokepoint) prevents siblings — every existing and future caller benefits without each having to remember. A fix at link 4 (a helper everyone must remember to call) prevents this instance but not the class. A fix at link 3 (one call site — the user's proposal) doesn't even prevent all *current* manifestations.

## Symptom / proximate / root
- **Symptom:** `search_by_email("bob@example.com") → not_found` after signup as `"Bob@Example.COM"`.
- **Proximate cause:** `app/db.py:34` — `if u.email == email:` is case-sensitive.
- **Root cause:** Emails are stored and looked up as opaque case-sensitive strings with no normalization chokepoint and no type-level constraint encoding the product invariant.

### Falsifying the root cause
- **What would disprove it?** If only `search.search_by_email` were affected and the other callers handled casing differently, the cause would be local to `search.py` and the user's one-liner would be correct.
- **Cheap disconfirming experiment:** Read each call site of `find_by_email`. **Result:** all four hand raw input to the same case-sensitive store. **Not falsified.**
- **Alternative mechanism?** Could the symptom come from whitespace / Unicode normalization rather than casing? `grep -rn "strip\|lower\|casefold\|NFC\|NFD" app/` returns nothing, and test inputs differ only in case. Implausible.

## Sibling impact sweep
The user's `search.py`-only patch leaves three siblings broken — one critical:

| # | Call site | Symptom under root cause | Severity |
|---|---|---|---|
| 1 | `app/search.py:7` | Support lookups miss (reported). | P2 |
| 2 | `app/signup.py:13` | **Duplicate accounts possible.** `signup("Bob@x.com")` then `signup("bob@x.com")` both succeed → two `User` rows for one person. Split billing, split history, auth ambiguity. | **P1 — silent data corruption** |
| 3 | `app/invite.py:7` | `send_invite` to existing member with different casing returns `invite_sent` instead of `already_member` — re-invites a customer. | P2 |
| 4 | `app/password_reset.py:11` | Reset fails (`ResetError("no such user")`) on different casing than signup. | P2 — user-blocking |

In a real DB (not the fixture), any pre-existing rows with non-canonical casing become latent landmines requiring a backfill (`UPDATE users SET email = LOWER(TRIM(email))`) with a dedupe step before any uniqueness constraint.

A root cause with siblings this obvious is exactly what the skill's "no siblings ⇒ you stopped too early" warning targets — and here the worst sibling (silent duplicate signups) is worse than the reported bug.

## Load-bearing assumptions

1. **Email identity is case-insensitive in this product.**
   - Validated: BUG_REPORT.md L29; logs L20-22 treat three casings as the same customer; industry norm.
   - **Confirmed.**

2. **No other normalization (whitespace, Unicode) is silently in play that the fix would collide with.**
   - Validated: `grep -rn "strip\|lower\|casefold\|normalize\|NFC\|NFD\|encode" app/` — no matches.
   - **Confirmed.**

3. **Lowercasing is a safe canonical form here.**
   - Validated: no case-preserving features; `User.name` carries display name; `str.lower()` matches every real-world MTA including Gmail (the domain in the bug report). Technically RFC 5321 §2.4 allows case-sensitive local-parts, but no real provider honors that.
   - **Confirmed for this product.**

4. **Normalizing in `db.py` (`insert` + `find_by_email`) covers every read/write path.**
   - Validated: `_USERS` is only touched in `db.py`; all four current callers funnel through `db.insert` / `db.find_by_email`.
   - **Confirmed.**

5. **Production data may contain mixed-case rows requiring backfill before uniqueness can be enforced.**
   - **UNVERIFIED** for prod (fixture is in-memory, resets each test). Flagged as open question §11. **The recommended fix does not depend on this assumption being true** — it works correctly regardless.

No `UNVERIFIED` assumption is load-bearing.

## Fix proposals

### Option A — Symptom fix (the user's one-liner, lifted to `search.py` only)
```python
# app/search.py
def search_by_email(email: str) -> dict:
    needle = email.lower()
    for u in db.all_users():
        if u.email.lower() == needle:
            return {"status": "ok", "id": u.id, "email": u.email, "name": u.name}
    return {"status": "not_found"}
```
- **Pro:** Tiny; ships in 5 minutes; unblocks support today.
- **Con (serious):** Leaves duplicate-signup (sibling #2 — silent data corruption), broken invite, broken password reset. Codifies divergence between `search` and the other lookups, which itself becomes a future bug source. The misleading `db.py` docstring stays.

### Option B — Root-cause fix (recommended)
```python
# app/db.py
"""In-memory user store. Email lookups are case-insensitive
(emails are normalized to lowercase at insert and lookup)."""

def _canonical_email(email: str) -> str:
    return email.strip().lower()

def insert(email: str, name: str) -> User:
    global _NEXT_ID
    user = User(id=_NEXT_ID, email=_canonical_email(email), name=name)
    _NEXT_ID += 1
    _USERS.append(user)
    return user

def find_by_email(email: str) -> Optional[User]:
    needle = _canonical_email(email)
    for u in _USERS:
        if u.email == needle:
            return u
    return None
```
- **Files:** `app/db.py` only. Docstring + `insert` + `find_by_email` + one private helper.
- **Blast radius:** Every caller benefits transparently. No call-site changes. `User.email` stored canonical from now on.
- **Tests:** failing test passes; all three sibling classes fixed in one stroke.
- **Rollback:** revert the three hunks. Lowercase strings remain valid emails — rollback is data-safe.
- **Risk in fixture:** negligible. In real prod: backfill + dedupe needed before adding `UNIQUE` (covered in §11).

### Recommendation
**Ship Option B.** The framing "the fix is one line" is the exact anti-pattern the skill's anti-rationalization table calls out. The *symptom* fix is one line per call site, but there are four call sites and one of them is silently corrupting data. Fixing them all one-at-a-time is *more* code than fixing them once at the chokepoint. Optional follow-up: an `Email = NewType("Email", str)` value type with a `make_email(raw)` constructor — makes "forgot to lowercase" un-expressible at the type level.

## Counterfactual: would Option B have prevented the captured repro?
- **Would the repro fire?** No. Walk the test through:
  - `signup.signup(email="Bob@Example.COM", name="Bob")` → `db.insert` canonicalizes to `"bob@example.com"`, stored.
  - `search.search_by_email("bob@example.com")` → `db.find_by_email` canonicalizes needle to `"bob@example.com"`, matches. Returns `{"status": "ok", ...}`.
- **Which link does it break?** Link 5 (the data-model gap), and by construction link 3 (the equality is now case-insensitive in its inputs). Same depth as the identified root cause.
- **Does it address the captured failure?** Yes — and all three siblings.
- **Survivors in the fixture?** None. (Prod-only survivor: legacy rows until backfill — §11.)

**Result: Confirmed.**

(For comparison: Option A's counterfactual is *Confirmed-with-survivors*; survivors are severe — silent duplicate-signup is worse than the reported bug.)

## Prevention — make the class loud or impossible
- **Tests (floor):**
  - The existing `test_search_finds_user_signed_up_with_mixed_case` (repro).
  - New: `test_signup_with_different_case_is_duplicate` — second `signup` with re-cased email raises `SignupError("email already registered")`.
  - New: `test_invite_to_existing_member_with_different_case_returns_already_member`.
  - New: `test_request_reset_with_different_case_finds_user`.
- **Guardrails (ceiling):**
  - Single `_canonical_email()` chokepoint in `db.py` (Option B). Correct the `app/db.py:1` docstring — a wrong docstring is worse than none; it actively misled the original author and reviewers into thinking case-sensitivity was the intent.
  - Stronger: `Email = NewType("Email", str)` with `make_email()` constructor. `User.email: Email`; `find_by_email(email: Email)`. A raw `str` can no longer flow into a lookup without going through the canonicalizer.
- **Docs / invariant:** Add an `invariants.md` entry: "Stored `User.email` is canonical (lowercased, stripped). All comparisons in canonical form. Enforcement: `app/db.py::_canonical_email` at every store boundary." Cross-link from `BUG_REPORT.md`.

## Open questions
1. **(Prod, not fixture.)** Does the real `users` table have mixed-case rows today? If yes, backfill `UPDATE users SET email = LOWER(TRIM(email))` is needed before any `UNIQUE` constraint, with a product decision on dedupe winners on collision.
2. **Display-form emails.** Once canonicalized, `User.email` displays lowercase. Fine for nearly all products; if a UI surface needs the user-typed casing, add a separate `email_display: str`. Reasonable default: drop user-typed casing.
3. **Internationalized emails (IDN / non-ASCII).** `str.lower()` is Unicode-aware but not IDNA. For the fixture irrelevant; for prod, `casefold()` + IDNA-normalize the domain is more correct. Flag, don't block.

## Pushback on the user's framing
The user said "patch `search.py` to do `email.lower() == u.email.lower()` and ship it. The fix is one line." Respectfully: lowercasing is the right idea but `search.py` is the wrong layer. The patch leaves silent duplicate-signup active (sibling #2 — strictly worse than the reported bug). The cost difference between the proposed one-liner and the correct three-line `db.py` fix is essentially zero, and the correct fix removes three latent bugs the user hadn't spotted. The skill's anti-rationalization table predicted this exact framing ("The fix is obvious, skip the RCA"); the framing was itself the signal that RCA was warranted.

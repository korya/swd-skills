# Pre-merge review: `feat(discounts): Add discount codes with API validation`

**Branch:** `feature/discounts` (1 commit, `09fee57`) onto `main` (`e0f443f`)
**Verdict: REQUEST CHANGES — do not merge.** The PR's central claim ("validated at the API boundary per §4") is false: the validation function exists but is never called. Several money-path bugs were confirmed by running the code (negative charges, unlimited reuse of capped codes, unauthenticated arbitrary credits), a sibling module (`app/support.py`) is left crashing, and three of the four documented invariants are violated. Tests pass (4/4) but only because they cover a single happy path.

All findings below marked "verified" were reproduced by executing the branch, not just by reading the diff.

---

## 1. Critical issues

### C1. Discount percent is never validated — the headline claim of the PR is untrue
`app/discount_engine/__init__.py` defines `validate_percent()` (the §4 check), but **no code path calls it**. `api_create_discount` (`app/api.py`) stores `int(payload["percent"])` unchecked, and `billing.charge` applies whatever is stored.

Verified on a live run:

- `percent=90` → charge of `10.00` becomes `100` cents (cap of 30 ignored).
- `percent=150` → `amount = -500`, `total = -525` — a **negative charge**, i.e. the system pays the customer.
- `percent=-50` → amount inflated to `1500` cents — customer silently overcharged.

Consequences: invariant §4 is violated; `MAX_DISCOUNT_PERCENT` is now enforced nowhere (see C5); and the commit message bullet "Discount percent is validated at the API boundary per docs/invariants.md §4" misdescribes the change. Fix: call `validate_percent` in `api_create_discount` and reject out-of-range input; consider a defense-in-depth clamp in `billing.charge`.

### C2. `app/support.py` crashes on any not-found lookup — the contract change was only half propagated
`db.find_user_by_email` was changed from raising `NotFound` to returning `None`. The commit message says "billing was updated to match" — but `app/support.py` was not. It still wraps the call in `except NotFound:` and then dereferences the result:

```python
try:
    u = STORE.find_user_by_email(email)
except NotFound:
    return {"found": False}
return {"found": True, "id": u["id"], ...}   # u is None -> TypeError
```

Verified: `support.lookup("ghost@x.y")` raises `TypeError: 'NoneType' object is not subscriptable`. The support console's not-found path — its whole reason for the marker dict — is now a crash. When changing a function's error contract, every caller must be swept (`grep find_user_by_email`); there were exactly three, and one was missed. The now-dead `NotFound` class also lingers in `app/db.py`.

### C3. `api_apply_credit` mints arbitrary negative money with no user, no validation, no cap
`app/api.py:api_apply_credit` strips a leading `-` and negates, deliberately bypassing `parse_money`'s rejection of negative amounts (its docstring: "money enters the system as a non-negative amount; adjustments are modeled explicitly"). Verified: `{"amount": "-999999.99"}` appends `{"user_id": None, "amount": -99999999, "total": -99999999}` to the ledger.

- Unbounded, unauthenticated credit creation — effectively free refunds of any size.
- `user_id: None` breaks ledger attribution (and clashes with CLAUDE.md's "reference users by id").
- §4 says *any* percentage adjustment "(discount, credit)" is validated at the boundary; this credit path has zero validation.
- **Scope**: credits appear nowhere in the PR description or in SUPPORT-311's ask. This endpoint should be pulled out of the PR entirely; if credits are wanted, they deserve their own designed change.

### C4. `api_redeem` logic is inverted and its blanket `except` hides it
```python
if row is None or row["uses"] < row["max_uses"]:
    try:
        STORE.discounts[code]["uses"] += 1
    except Exception:
        pass  # redemption must never fail the charge path
    return {"redeemed": True}
```
Verified: redeeming a **nonexistent** code returns `{"redeemed": True}` — the `row is None` arm triggers a `KeyError` that the bare `except Exception: pass` swallows, then the function reports success. The condition should be `row is not None and row["uses"] < row["max_uses"]`; the correct code makes the try/except unnecessary. A bare `except Exception: pass` in a money path is exactly the pattern that turned this logic bug into a silent wrong answer.

### C5. `max_uses` is never enforced where discounts are applied
`billing.charge` applies a discount by looking the code up directly in `STORE.discounts` — it neither checks `uses < max_uses` nor increments `uses`, and nothing calls `api_redeem` on the charge path. Verified: a `max_uses=1` code discounted three consecutive charges and its `uses` counter stayed at `0`. Redemption accounting and discount application are two disconnected systems; a single-use code is in practice unlimited. Fix: enforce and increment atomically in the charge path (and decide what a charge does when the code is exhausted — silently full price is a bad customer experience; see M2).

---

## 2. High issues

### H1. Email canonicalization dropped — invariant §1 broken (data corruption)
`users.create_user` replaced `normalize_email(email)` (strip + lowercase) with bare `email.strip()`. Verified: creating `"Bob@X.COM"` stores it verbatim, and a subsequent `billing.charge("bob@x.com", ...)` fails with `unknown user`. §1 warns precisely about this: "a non-canonical write breaks every reader." This also violates CLAUDE.md ("reuse helpers in app/util.py") and is unrelated to discounts — the change isn't even mentioned in the PR description. Restore `normalize_email` at the write path.

### H2. Migration 002 violates invariant §3 and doesn't match the code it migrates for
`migrations/002_drop_plan.py`:
- **Destructive with no `down()`** — §3 requires "additive first; destructive steps only after a release with dual-read, and every migration ships a `down()`." This one pops `plan` immediately and is irreversible (the old value is discarded, so a `down()` can't even be written after the fact — the mapping loses information: both `free` and every non-`legacy` value collapse to `standard`).
- **Application code was not moved to `tier`.** `users.create_user` still writes `plan: "free"` and never writes `tier`. Verified: a user created after running the migration has `plan` and no `tier` — the store immediately diverges into two schemas. `tests/test_users.py` still asserts on `plan`, confirming the codebase hasn't adopted `tier` at all.
- The correct §3 sequence: (1) additive migration writing `tier` alongside `plan` + code dual-writes/dual-reads, (2) later destructive migration with a real `down()`. As shipped, this migration should not merge.

### H3. Missing failure-path tests — explicit project requirement
CLAUDE.md: "Every change to app/billing.py requires failure-path tests"; docs/testing.md: money and lookup paths need invalid-input / not-found / limit-exceeded tests. `tests/test_discounts.py` contains exactly one happy-path test. Absent (and each would have caught a confirmed bug): over-cap / negative / zero percent (C1), unknown discount code on charge (M2), exhausted `max_uses` (C5), redeem of unknown code (C4), credit validation (C3), migration behavior (H2), support lookup (C2). The suite is green (4/4) — which here measures coverage, not correctness.

---

## 3. Medium issues

### M1. The pluggable engine is speculative and mostly dead code (Occam pass)
The task was "percentage discount codes." The PR ships an ABC, a decorator-based `STRATEGY_REGISTRY`, and env-var backend selection (`DISCOUNT_ENGINE_BACKEND`) — and then `billing.py` imports `PercentDiscount` directly, so `get_strategy` and the registry have **zero callers**. Additional smells: selecting money-math via an environment variable is a config-driven billing hazard; `validate_percent` imports from `billing` inside the function body to dodge a circular import — a sign the layering is inverted (billing depends on discount_engine which depends on billing). The right-sized change is a ~10-line percent function (or the single class) with the cap check; add the registry when the second strategy actually arrives. Recommend deleting the registry/ABC/env-var machinery from this PR.

### M2. Unknown or exhausted discount codes are silently ignored at charge time
`billing.charge`: `row = STORE.discounts.get(discount_code); if row: ...` — a typo'd or expired code charges full price with no signal. For a customer-facing money path this should be an explicit `BillingError` (or an explicit "discount not applied" result), not silence.

### M3. The FIN-88 cap change (50 → 30) is bundled and, as shipped, has no effect
A finance-policy change is buried inside a feature PR, and because nothing enforces the cap (C1), the constant change alters no behavior — the PR bullet claiming the lowered cap is live is misleading until validation exists. Prefer shipping the policy change as its own commit once enforcement works; also note pre-existing codes created under the old cap would need a decision (grandfather vs. clamp).

### M4. Undeclared drive-by changes inflate the diff
Not in the PR description: the `source` field on users (plus API plumbing), the `normalize_email` removal (H1), the credit endpoint (C3), and the removed return-type annotation on `find_user_by_email`. Each should be either declared and justified or split out. Reviewers cannot audit what the description does not admit to.

### M5. Merge coordination: `feature/audit-log` conflicts with this branch
The in-flight `feature/audit-log` branch (`48d0c6e`) touches `app/users.py` (still using `normalize_email`) and `app/db.py` (still raising `NotFound`). Whichever lands second gets textual and semantic conflicts — in particular, resolving in favor of this branch would silently re-drop normalization and re-break `support.py`. Flag to whoever merges.

---

## 4. Low issues

- `app/api.py:api_create_discount` doesn't validate `code` (empty string is accepted as a key) and overwrites an existing code, resetting its `uses` counter — a reuse laundering vector once `max_uses` is enforced.
- `int(payload["percent"])` will raise a raw `ValueError`/`TypeError` on bad input instead of a clean API error; same for `max_uses`.
- `PercentDiscount.apply` floors the discount (charge rounds up). Acceptable under §2 (explicit integer arithmetic) but worth a comment/test pinning the rounding direction.
- `NotFound` in `app/db.py` is now unreferenced except by the broken `support.py` handler — remove it or restore the raising contract (C2 decides which).
- `migrations/002_drop_plan.py` guesses at a `"legacy"` plan value that nothing in the repo ever writes (only `"free"` exists); the mapping looks invented.

## 5. What was done well

- Money stays in integer cents throughout the new code (no floats) — §2 upheld.
- `parse_money` and `STORE` helpers are reused on the main charge path rather than re-implemented.
- The intended layering (API validates, billing applies) matches §4's design — the enforcement is just missing, not misplaced.
- A test file for the new feature exists, mirrors `tests/` conventions, and cleans store state in `setUp`.
- Clear commit message structure with claimed rationale per change (even though several claims don't match the code — see C1, C2, M3).

## 6. Suggestions (non-blocking)

- Make charge-time discount application atomic: validate percent, check `uses < max_uses`, apply, increment — one code path, one source of truth; drop `api_redeem` or reduce it to a thin wrapper over it.
- Replace `discount_engine/` with a plain function until a second strategy is real; if the registry survives, pick strategy from the discount row's data (e.g. a `kind` field), not from an environment variable.
- Move the §4 cap out of `billing` into the validation module (or a `policy` module) to fix the circular dependency the right way around.
- Add the failure-path tests listed in H3 before re-requesting review; several are two-liners.

## 7. Known limitations (acceptable as-is)

- In-memory store, no concurrency control — consistent with the existing fixture codebase; the `uses` increment will need atomicity only when a real DB arrives.
- No expiry dates / per-user limits on codes — reasonable v1 scope for SUPPORT-311; worth a tracked follow-up.
- `down()` for migration 001 is a no-op — pre-existing pattern, fine.

---

### Summary for the author

The shape of the feature is right, but the PR cannot merge as-is: the advertised validation doesn't exist (C1), a neighboring module is left crashing (C2), the credit endpoint is an unscoped negative-money hole (C3), redemption logic is inverted (C4) and disconnected from charging (C5), email canonicalization regressed (H1), and the migration is irreversible against an explicit invariant (H2). Minimal path to green: enforce `validate_percent` at both API endpoints, fix `api_redeem`'s condition and remove the bare except, enforce `max_uses` in `charge`, restore `normalize_email`, fix or restore the `find_user_by_email` contract for `support.py`, drop `api_apply_credit` and migration 002 from this PR (redo the migration additively with a `down()`), and add the required failure-path tests.

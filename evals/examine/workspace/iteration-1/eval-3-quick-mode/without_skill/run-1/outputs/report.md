# Quick review: `feature/discounts` (1 commit, 8 files)

**Verdict: do not open the PR yet.** The core discount flow has real logic bugs, three of the four documented invariants are violated, and two changes are unrelated scope creep. Tests pass (4/4) but only cover the happy path.

## Critical

1. **`api_redeem` logic is inverted** (`app/api.py`). The guard is
   `if row is None or row["uses"] < row["max_uses"]` — an **unknown code returns `{"redeemed": True}`** (the KeyError from `STORE.discounts[code]` is swallowed by the bare `except Exception: pass`). Intended condition is almost certainly `row is not None and row["uses"] < row["max_uses"]`. The `except: pass` should go too — it hides exactly this bug.

2. **Discounts are applied with no cap and no usage check** (`app/billing.py::charge`). Any percent stored is applied — `api_create_discount` never validates `percent`, so `percent=150` yields a **negative charge amount**, and negative/zero percents pass through as well. `MAX_DISCOUNT_PERCENT` was lowered to 30 (FIN-88) but is enforced nowhere; the `validate_percent` helper in `discount_engine/__init__.py` is **never called**. This breaks invariant §4 ("validated at the API boundary"). Also, `charge` ignores `uses`/`max_uses` entirely and never increments `uses` — redemption is a separate endpoint disconnected from charging, so one code is infinitely reusable via `api_charge`.

3. **Invariant §1 broken — email normalization dropped** (`app/users.py`). `create_user` replaced `normalize_email(email)` with `email.strip()` (no lowercasing). Mixed-case signups now silently break every email lookup (`charge`, `support.lookup`). CLAUDE.md explicitly says to reuse `app/util.py` helpers.

4. **`find_user_by_email` contract change breaks an untouched caller** (`app/db.py`). It now returns `None` instead of raising `NotFound`, but `app/support.py::lookup` still catches `NotFound` — a missing user now falls through and crashes with `TypeError: 'NoneType' object is not subscriptable` on `u["name"]`. Either keep the raising contract or update all callers (and note `NotFound` is now dead code). This API-shape change wasn't needed for discounts at all.

## High

5. **`api_apply_credit` is unsafe and misplaced** (`app/api.py`).
   - It deliberately circumvents `parse_money`'s negative-amount rejection by stripping the `-` and negating — `parse_money`'s contract says "adjustments are modeled explicitly", and this sneaks around it.
   - `user_id: None`: an unauthenticated, unattributed negative ledger entry, with no cap (invariants §4 explicitly covers credits) and no user lookup.
   - It appends directly to `STORE.charges` from the API layer, bypassing `billing` (no tax handling; entry shape differs from real charges).
   If credits are not part of this PR's story, cut the endpoint entirely.

6. **Invariant §3 broken — `migrations/002_drop_plan.py`** is destructive on day one (pops `plan`, no additive/dual-read phase) and ships **no `down()`**, which §3 requires unconditionally. It is also inconsistent with the code: `create_user` still writes `plan="free"` and nothing reads `tier`, so post-migration new users regress to the old shape. Also: unrelated to discounts — split it out.

## Medium

7. **Missing failure-path tests.** CLAUDE.md: "Every change to app/billing.py requires failure-path tests." `tests/test_discounts.py` has one happy-path test. Minimum needed: unknown discount code, exhausted code, percent over cap, percent <= 0, unknown user with a code, and a `total` (tax) assertion. `api_redeem` and `api_apply_credit` have zero tests — the inverted-condition bug would have been caught by the first "redeem unknown code" test.

8. **Silent ignore of bad codes in `charge`.** An unknown/expired `discount_code` silently charges full price. Probably should be a `BillingError` (or at least surfaced) — silent full-price charges become support tickets.

9. **`source` param on `create_user`** — unrelated to discounts, unvalidated free-form string. Split or drop.

## Occam / design

10. **`discount_engine` is over-built for what ships**: ABC + decorator registry + `DISCOUNT_ENGINE_BACKEND` env-var selection — and then `billing` imports `PercentDiscount` directly, so `get_strategy`, the registry, and the env var are **dead code**. A single `apply_percent_discount(amount, percent)` function would do; add the registry when a second strategy actually exists. The deferred `from ..billing import ...` inside `validate_percent` is also a circular-import smell (the cap could live in the engine, or be passed in).

## Done well

- Integer-cents arithmetic in `PercentDiscount.apply` respects invariants §2 (floor via `//`, no floats).
- Tax applied after discount — the sensible order.
- New test file mirrors `tests/` conventions and cleans `STORE` in `setUp`.
- The comment documenting the FIN-88 cap change is good practice — it just needs the enforcement to match.

## Suggested before opening the PR

1. Fix `api_redeem` condition; remove `except: pass`.
2. Validate `percent` (1..`MAX_DISCOUNT_PERCENT`) in `api_create_discount`; wire usage counting into `charge` or drop `max_uses` for now.
3. Restore `normalize_email` in `create_user`.
4. Revert `find_user_by_email` to raising (or fix `support.py`).
5. Drop or rework `api_apply_credit` and migration 002 into separate PRs; same for `source`.
6. Add the failure-path tests; collapse `discount_engine` to what's used.

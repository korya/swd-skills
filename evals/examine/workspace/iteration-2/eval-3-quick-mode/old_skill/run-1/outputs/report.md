# Examine: Add discount codes with API validation (`feature/discounts` vs `main`, quick mode)

**Target:** `git diff 3c9d83d..bed1927` (merge-base with `main`; no upstream configured; working tree clean, so nothing extra included). 8 files, +129/−14, one commit.
**Mode:** **quick**, as requested. Note: the diff touches a migration and the money path, which would have auto-selected **full** — after reading the findings below I'd run a full pass before this merges anyway.
**Verification:** each Medium+ candidate went to an independent verifier subagent given only the diff, the files, and the candidate; all came back CONFIRMED (inputs and outputs quoted per finding).

## Headline

**Hold.** The commit's central claim — "discount percent is validated at the API boundary per §4" — is not true: `validate_percent` exists but nothing calls it, so a 150% code produces a negative charge. Around that, the branch bundles four unrelated changes (email normalization dropped, `find_user_by_email` contract flipped, a destructive migration, an ad-hoc credit endpoint), each of which independently violates a written invariant (§1, §3, §4) or crashes an existing caller. The discount feature itself is ~15 lines and roughly the right shape; it's everything else in the PR that needs to come out or be fixed.

## Approach fit

Matches the obvious approach (sketch 1: store a `{code, percent}` row, validate at the API layer against `billing.MAX_DISCOUNT_PERCENT`, apply an integer-arithmetic discount in `billing.charge` before tax). Everything beyond that sketch is unexplained by any constraint I could find in the commit message, the docs, or `main`'s history: the strategy registry + env-var backend, the `plan → tier` migration, the `source` field, `api_redeem`, `api_apply_credit`, and dropping `normalize_email`. See S1.

## Issues

### Critical (must fix before merge)

#### C1 — Discount percent is never validated; out-of-range codes produce negative or inflated charges
- **Locator:** `flow: app/api.py:18-27 (api_create_discount) → app/billing.py:19-22 → app/discount_engine/percent.py:10`
- **What:** `api_create_discount` stores `int(payload["percent"])` with no range check. `discount_engine.validate_percent` (correct bounds, cites §4 in its docstring) has zero callers. `billing.charge` applies whatever is in the row. The cap constant `MAX_DISCOUNT_PERCENT` is therefore enforced nowhere, before or after the 50→30 change.
- **Evidence:** Probe on `"10.00"`: `percent=150` → `{'amount': -500, 'total': -525}`; `percent=-20` → `amount=1200`; `percent=31` (over the new cap) → `amount=690`, accepted. Also `percent="10.5"` raises an uncaught `ValueError` from `int()` at the boundary.
- **Verdict:** CONFIRMED — verifier ran the same inputs independently; `grep validate_percent` shows definition only.
- **Why Critical:** Wrong money on the ledger (negative charges, >100% discounts, cap bypass) from a single support-console input, and a direct violation of a written invariant the commit message claims to satisfy. The cap being finance policy (FIN-88) makes the unenforced cap a compliance problem, not just a bug.
- **Fix:** In `api_create_discount`, parse `percent` defensively and reject unless `validate_percent(percent)`; raise a `BillingError`/`ValueError` the API layer already surfaces. Add failure-path tests for 0, 31, 150, −20, "10.5" (see H5). Consider a belt-and-braces check in `PercentDiscount.__init__` so a bad row can never reach `apply`.
- **Cites:** `docs/invariants.md §4` ("validated at the API boundary before it reaches billing"); `docs/invariants.md §2` (negative "amounts" are not modeled amounts).

### High (should fix before merge)

#### H1 — `api_redeem` and `max_uses` are disconnected from charging and inverted
- **Locator:** `flow: app/api.py:12-15 (api_charge) → app/billing.py:19-22; app/api.py:30-39 (api_redeem)`
- **What:** `billing.charge` reads only `row["percent"]`; `uses`/`max_uses` are never checked or incremented on the charge path, and nothing calls `api_redeem`. `api_redeem` itself takes the "redeem" branch when `row is None`, then swallows the resulting `KeyError` with `except Exception: pass` and reports `redeemed: True`.
- **Evidence:** Probe: code `ONCE` with `max_uses=1` applied to three consecutive charges → all `amount=900`, row still `uses=0`. `api_redeem({"code": "BOGUS"})` on an empty store → `{'redeemed': True}`.
- **Verdict:** CONFIRMED — verifier reproduced both.
- **Why High:** Single-use codes are unlimited-use codes (money leak); and the one function that tracks uses lies about unknown codes and hides its own failures. The default `max_uses=1` implies the author intended enforcement.
- **Fix:** Either enforce `uses < max_uses` and increment inside `billing.charge` (same place the discount is applied — that's the atomic point) and delete `api_redeem`; or drop `uses`/`max_uses` from this PR entirely and ship them when they're wired. Either way, remove the bare `except: pass` — the comment "must never fail the charge path" describes a path it is not on.
- **Cites:** `docs/testing.md` lines 4–5 ("limit exceeded" is a required failure-path case).

#### H2 — `find_user_by_email` now returns `None`, but `support.lookup` still catches `NotFound`
- **Locator:** `flow: app/db.py:14-18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:18` (`raise NotFound(email)` → `return None`); `support.py` unchanged.
- **What:** The commit says "billing was updated to match" — `support.py` was not. For any unknown email the support console now raises `TypeError` instead of returning `{"found": False}`. `NotFound` is now dead (defined, caught, never raised).
- **Evidence:** Probe: `support.lookup("nobody@x.y")` → `TypeError: 'NoneType' object is not subscriptable`.
- **Verdict:** CONFIRMED.
- **Why High:** Reachable crash on a primary support workflow, introduced by a contract change that had nothing to do with discounts (the discount path never looks up users by email). Untested because there is no `tests/test_support.py`.
- **Fix:** Simplest: revert the `db.py` change — the exception contract was fine and both callers handled it. If you keep `None`, update `support.lookup` to `if u is None`, delete `NotFound`, and add a support not-found test.
- **Cites:** `docs/testing.md` ("lookup paths require failure-path tests … not-found").

#### H3 — `create_user` no longer canonicalises emails; real customers become unchargeable
- **Locator:** `app/users.py:12`
- **What:** `normalize_email(email)` replaced by `email.strip()`; `util.normalize_email` now has no callers. Any mixed-case signup is stored non-canonical, and every reader (`billing.charge`, `support.lookup`) does an exact match on the canonical form.
- **Evidence:** Probe: `create_user("  A@B.c ", "A")` stores `'A@B.c'`; `billing.charge("a@b.c", "1.00")` → `BillingError("unknown user")`; `support.lookup("a@b.c")` → `TypeError` (via H2).
- **Verdict:** CONFIRMED.
- **Why High:** §1 says it outright: "a non-canonical write breaks every reader." Silent, per-customer, discovered only when a charge fails. Also unrelated to discounts.
- **Fix:** Restore `email = normalize_email(email)`. Add a test that `create_user("A@B.c")` is chargeable as `"a@b.c"`.
- **Cites:** `docs/invariants.md §1`; `CLAUDE.md` line 3 ("Reuse helpers in app/util.py").

#### H4 — Migration 002 is destructive, has no `down()`, and the app still writes the old field
- **Locator:** `flow: migrations/002_drop_plan.py:4-7 → app/users.py:14 → tests/test_users.py:13`
- **What:** `up()` pops `plan` and writes `tier` in one step; there is no `down()`; `create_user` still writes `"plan": "free"` and never writes `tier`; nothing in `app/` reads `tier`. After the migration runs, old users have `tier`/no `plan`, new users have `plan`/no `tier`, and `test_users.py` pins the pre-migration shape.
- **Evidence:** Probe: after `m.up(STORE)` an existing user is `{'tier': 'standard'}`; a freshly created user is `{'plan': 'free'}`; `hasattr(m, "down")` → `False`. Only `001_init.py` defines `down`.
- **Verdict:** CONFIRMED (static; deterministic).
- **Why High:** Irreversible data change with no rollback path, shipped in the same PR as the code that should have been dual-writing first, and mixed-shape user rows on day one. Also: nothing about discounts needs this.
- **Fix:** Pull the migration out of this PR. When it ships: (1) add `tier` alongside `plan` in `create_user` and readers, (2) release, (3) then a migration that drops `plan` and ships a real `down()`.
- **Cites:** `docs/invariants.md §3` (all three clauses: additive first, dual-read release before destruction, every migration ships `down()`).

#### H5 — `billing.py` changed without failure-path tests; every top-3 risk is uncovered
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The only new test is one happy path (10% of 10.00 → 900). No test for: percent out of range / over cap (C1), unknown code (M2), `max_uses` exhaustion (H1), the changed unknown-user path, the migration, the support lookup, or `api_apply_credit`. `grep assertRaises tests/` finds only the pre-existing unknown-user test. Suite is 4/4 green, so CI catches none of the above.
- **Evidence:** All of C1, H1–H4 reproduced with 3–5-line probes that would have been the required tests.
- **Verdict:** CONFIRMED.
- **Why High:** A missing test for a named production risk is functionally a bug, and the repo's instruction file makes it a hard rule for this file. Top-3 risks, all uncovered: (1) out-of-range percent → wrong money, (2) non-canonical email → customer unchargeable, (3) unknown-email support lookup → crash.
- **Fix:** Add `test_discounts.py` cases: invalid percent (0, 31, 150, −20, "10.5"), unknown code, max-uses exhaustion, and `total` (tax after discount). Add `tests/test_support.py::test_lookup_unknown` and a mixed-case email test in `test_users.py`.
- **Cites:** `CLAUDE.md` line 5 ("Every change to app/billing.py requires failure-path tests"); `docs/testing.md` lines 4–5.

### Medium (worth fixing now; acceptable as a follow-up)

#### M1 — `api_apply_credit` bypasses `parse_money`'s non-negative guard and writes ownerless ledger rows
- **Locator:** `app/api.py:42-50`
- **What:** Strips a leading `-` and negates, deliberately routing around `parse_money`'s rule ("money enters the system as a non-negative amount; adjustments are modeled explicitly", `app/util.py:9-10`). No user lookup — every credit is appended with `user_id: None`. No cap, no validation, no relation to any charge.
- **Evidence:** Probe: `api_apply_credit({"amount": "-5.00"})` → `{'user_id': None, 'amount': -500, 'total': -500}` appended to `STORE.charges`.
- **Verdict:** CONFIRMED.
- **Why Medium:** An unattributed negative ledger entry is unreconcilable, and this is the second place in the PR where the API layer works around a validation helper instead of using it (cf. C1, H3). Medium rather than High only because nothing calls it yet.
- **Fix:** Remove from this PR. If credits are needed, model them explicitly (`kind: "credit"`, positive amount, required `user_id`) and validate at the boundary per §4.
- **Cites:** `docs/invariants.md §4` ("Any percentage adjustment (discount, credit) is validated at the API boundary"); `CLAUDE.md` line 3.

#### M2 — Unknown discount code is silently ignored; customer charged full price with no signal
- **Locator:** `app/billing.py:19-22`
- **What:** `row = STORE.discounts.get(discount_code); if row:` — a miss falls through to full price. The returned entry is byte-identical to a charge with no code at all.
- **Evidence:** Probe: `discount_code="TYPO"` → `{'amount': 1000, 'total': 1050}`.
- **Verdict:** CONFIRMED.
- **Why Medium:** Wrong behavior on a common edge path (typos, expired codes) that produces support tickets and refunds rather than a rejected request. The existing not-found paths (`unknown user`) all raise — this one is inconsistent with them.
- **Fix:** `raise BillingError("unknown discount code")`, and test it.
- **Cites:** `docs/testing.md` ("not-found" is a required failure case for lookup paths).

### Low (defer)
- **L1** [`app/billing.py:23`] `total = int(amount * (1 + TAX_RATE_BP / 10_000))` is float arithmetic in a money path (§2). Pre-existing, but the touched function now also feeds negative amounts through it. Probed: no integer/float mismatch for any amount in [0, $20,000), so no wrong output today — replace with `amount + amount * TAX_RATE_BP // 10_000` when you're in there.
- **L2** [`app/api.py:26`] `STORE.discounts[code] = row` silently overwrites an existing code and resets `uses` to 0 (probe: `uses=4` → `0`).
- **L3** [`app/api.py:19`, `app/billing.py:19`] Codes are not normalised: `"save10"` vs `"SAVE10"` are different codes, and `""` is treated as "no code" by the `if discount_code:` truthiness check.
- Further Lows, rolled up: `api_create_user` stores an arbitrary untrusted `source` string (`api.py:8`); `billing.py:11` comment lost its `(§4)` pointer; `discount_code: str = None` should be `Optional[str]`.

## Questions

- **Q1** [`app/billing.py:11`] FIN-88 and SUPPORT-311 aren't reachable from the repo. Can you link them in the PR body? The cap change is a policy decision hiding in a feature commit, and right now the cap isn't enforced anyway (C1), so I can't tell whether 30 was ever meant to be live yet.
- **Q2** [`app/discount_engine/percent.py:10`] `amount - amount*pct//100` rounds the *discount* down, so the customer pays the odd cent. Is that the finance-policy rounding direction, or should it be `amount * (100-pct) // 100` (rounds the *charge* down)? Same integers, different beneficiary.
- **Q3** [`migrations/002_drop_plan.py:7`] `plan == "legacy"` maps to `grandfathered`, but `main` only ever writes `"free"`. Where does `"legacy"` come from?

## Suggestions

#### S1 — Split this PR into the feature and everything else
- **Locator:** `scope: PR`
- **What:** Ship the discount code path alone (`api_create_discount` + validation, `billing.charge` discount application, tests). Move to separate PRs: the cap change (with FIN-88 link), the migration (after dual-write, per §3), the `source` field, `api_apply_credit`, and the `find_user_by_email` contract change (or just drop that one).
- **Why it'd be better:** Every High in this review is in the "everything else" bucket. Reviewed as one thing, the discount feature is a small, sound change; bundled, it's a hold.

#### S2 — Collapse `discount_engine` into `billing` until a second strategy exists
- **Locator:** `app/discount_engine/__init__.py:10-35`, `app/billing.py:2`
- **What:** `STRATEGY_REGISTRY`, `register`, `get_strategy`, and the `DISCOUNT_ENGINE_BACKEND` env var have no callers — `billing.py` imports `PercentDiscount` directly, so the "pluggable" claim in the commit message isn't true of the code either (probe: `DISCOUNT_ENGINE_BACKEND=bogo` changes nothing; `get_strategy()` would `KeyError`). Keep `PercentDiscount.apply` (it's the good part) as a function next to `MAX_DISCOUNT_PERCENT`, together with `validate_percent`, which currently needs a lazy import to avoid a `billing ↔ discount_engine` cycle.
- **Why it'd be better:** Fewer moving parts, no env-var config surface nobody reads, no import cycle to tiptoe around, and the cap + validator + application live in one place. (The Occam pass is skipped in quick mode; this is offered on the evidence above, walked against the one stated constraint — "upcoming fixed-amount and BOGO" — which has no ticket or date. Re-introduce the abstraction when the second strategy is real.)

#### S3 — Record the discount on the charge entry
- **Locator:** `app/billing.py:24`
- **What:** Add `discount_code` and the pre-discount `amount` (or the discount in cents) to the entry.
- **Why it'd be better:** Today a discounted charge is indistinguishable from a smaller undiscounted one. Finance can't reconcile FIN-88 exposure, and support can't answer "was my code applied?" (which M2 makes a live question).

## Gaps

- No changelog / release note for the cap change or the new API functions.
- No manual-test notes for the migration (what data was it run against?).

## Known limitations

- `Store` is an in-memory dict, so "migration" and "ledger" are stand-ins; the review judges them as if they were real because the invariants doc does.
- `_ids` counter is not reset between tests (pre-existing; harmless today).

## What was done well

- [`app/discount_engine/percent.py:10`] Discount application is pure integer arithmetic — exactly what §2 asks for, and the one place in the PR where the money rule is followed to the letter.
- [`app/discount_engine/__init__.py:26-30`] `validate_percent` has the right bounds (`1 <= p <= cap`), reads the cap from `billing` so there's one source of truth, and cites §4 in its docstring. It just needs to be called.
- [`app/billing.py:14`] `discount_code` is an optional trailing parameter — existing callers and `test_billing.py` are untouched and still pass.
- [`app/billing.py:24`] Charge entries reference the user by `id`, not email, per `CLAUDE.md` line 6.
- [`tests/test_discounts.py:8-11`] `setUp` clears all three stores, including `charges`, which the older tests forgot.
- Commit message: lists the non-obvious decisions (cap change, contract change, migration) explicitly. That's what made this review possible — the claims were checkable, even where they turned out false.

## Verified

- **Problem is real in base:** `main` has no discount path at all; `STORE.discounts` and `MAX_DISCOUNT_PERCENT` exist as unused hooks (`db.py:11`, `billing.py:10`), so the feature isn't a reimplementation.
- **Happy path works:** 10% on `"10.00"` → `amount=900`, `total=945`; suite 4/4 green on the branch.
- **Not-found guard in billing re-established:** `except NotFound` → `if user is None` at `billing.py:16` is equivalent for `charge`; `test_charge_unknown_user_fails` still passes. (The dropped guard is in `support.py`, H2.)
- **L1 float tax:** exhaustive check for `amount in [0, 2_000_000)` found zero mismatches vs integer arithmetic — the §2 violation is real but not producing wrong totals at realistic scale.
- **Import cycle:** `discount_engine.validate_percent`'s lazy `from ..billing import` is cycle-safe as written; a top-level import would not be (S2).
- **Approach gate:** matches sketch 1; no constraint found in commit, docs, or `main` history that explains the registry, migration, credit endpoint, or normalization change (S1).
- **Rule sources read:** `~/.claude/CLAUDE.md`, repo `CLAUDE.md`, `docs/invariants.md` and `docs/testing.md` in full (both are cited by `CLAUDE.md` and the commit, so they were load-bearing even in quick mode). No `AGENTS.md`, no per-directory instruction files.

## Not reviewed

- Quick-mode skips: **5e** architecture (no `docs/architecture.md` exists), **5f** conventions beyond `CLAUDE.md`, **5g** security, **5h** data privacy (no `docs/privacy.md`; the diff adds a `source` field but no new PII), **5i** testing as a full axis (covered only where H5 needed it), **5j** load-bearing assumptions (FIN-88 / SUPPORT-311 unverifiable from the repo — Q1), **5l** reversibility as a formal axis (the migration surfaced through §3 anyway, H4), **5m** dependencies (none added). Occam pass and host reviewers skipped; S2 is a suggestion, not an Occam finding.
- `migrations/001_init.py` and whatever runs migrations: accepted as-is.
- `feature/audit-log` branch: not part of this target.

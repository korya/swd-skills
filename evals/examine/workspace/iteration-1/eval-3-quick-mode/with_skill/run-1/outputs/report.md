# Examine: feat(discounts) — discount codes with API validation (`feature/discounts` vs `main`)

**Mode:** quick (user-requested). Reviewed diff: `git diff 835e88d..e09c41e` (merge-base of
`feature/discounts` and `main`; working tree clean, nothing uncommitted). Verification was
single-context (adversarial self-review plus executable probes; no verifier subagents).

## Headline

**Hold.** The commit's central claim — "discount percent is validated at the API boundary per
docs/invariants.md §4" — is false: the validator exists but is never called, and a 150%
discount produces a **negative charge** (probe: amount −500). Four further before-merge
problems: a missed caller of the changed `find_user_by_email` contract crashes the support
console, email canonicalization was silently dropped (§1), the migration is destructive with
no `down()` (§3) and new users still get `plan` instead of `tier`, and `max_uses` is not
enforced anywhere. All confirmed by execution, not speculation.

## Approach fit

The core shape matches the obvious approach (validate at API boundary → store code in
`STORE.discounts` → apply integer-percent reduction in `billing.charge`). Everything beyond
that sketch is unexplained by any stated constraint: a strategy registry + env-var backend
selector that nothing uses (M1), a destructive schema migration (H3), an unrelated credit
endpoint (M2), and a `source` field on users (L1). The cap change 50→30 is explained by a
stated constraint (FIN-88, finance sign-off claimed) — accepted as stated, see Verified.

## Issues

### Critical (must fix before merge)

#### C1 — Discount percent is never validated; out-of-range codes yield negative charges
- **Locator:** `flow: app/api.py:18-27 (api_create_discount) → app/billing.py:19-22 (charge)`
- **What:** `api_create_discount` stores `int(payload["percent"])` with no range check. The
  helper that implements the §4 rule — `validate_percent` at `app/discount_engine/__init__.py:26`
  — is defined but called from nowhere (`grep` finds no call sites in `app/` or `tests/`).
  `charge` then applies whatever percent is stored.
- **Evidence:** probe: create `{"code": "MEGA", "percent": 150}` → accepted; charge of
  `"10.00"` returns `amount: -500, total: -525` — a negative charge appended to
  `STORE.charges`. Negative, zero, and >30 percents are all accepted the same way.
- **Verdict:** CONFIRMED — executed against the branch.
- **Why Critical:** Direct violation of a project invariant the commit message explicitly
  claims to satisfy ("validated at the API boundary per docs/invariants.md §4"), with
  monetary damage on a reachable path (any support-created discount payload). The PR's
  headline feature ships broken in exactly the way the invariant exists to prevent.
- **Fix:** Call `validate_percent` in `api_create_discount` and reject invalid payloads
  (e.g. raise `ValueError`/return an error row) before writing to `STORE.discounts`. Add
  failure-path tests for 0, 31, and negative percent (see H5).
- **Cites:** `docs/invariants.md §4` ("Any percentage adjustment … is validated at the API
  boundary before it reaches billing").

### High (should fix before merge)

#### H1 — `find_user_by_email` contract change breaks `support.lookup` (missed caller)
- **Locator:** `flow: app/db.py:14-18 → app/support.py:5-10`
- **Changed anchor:** `app/db.py:18` (`raise NotFound(email)` → `return None`)
- **What:** The commit changed `find_user_by_email` to return `None` and says "billing was
  updated to match" — but `app/support.py` was not. Its `except NotFound:` handler is now
  dead code; `u` is `None` for unknown emails and `u["id"]` raises.
- **Evidence:** probe: `support.lookup("ghost@x.y")` → `TypeError: 'NoneType' object is not
  subscriptable`. The caller trace finds exactly two production callers of
  `find_user_by_email`: `billing.charge` (updated) and `support.lookup` (not updated).
- **Verdict:** CONFIRMED — executed against the branch.
- **Why High:** Every support-console lookup of a non-existent email now crashes instead of
  returning `{"found": False}` — an outage on a routine path, introduced by an unforced
  refactor of code whose requirements did not change.
- **Fix:** Update `support.lookup` to check `if u is None`; delete the now-unraisable
  `NotFound` class (nothing raises it anymore) or revert the contract change entirely.

#### H2 — Email canonicalization dropped from the user write path (§1 violated)
- **Locator:** `app/users.py:12`
- **Changed anchor:** the `create_user` hunk removing `from .util import normalize_email`
- **What:** `create_user` now stores `email.strip()` instead of `normalize_email(email)` —
  lowercasing is gone from the only user write path. The change is not mentioned in the
  commit message.
- **Evidence:** probe: `create_user("A@B.C", …)` then `billing.charge("a@b.c", "5.00")` →
  `BillingError: unknown user`. Lookups assume canonical form (`docs/invariants.md §1`), so
  every mixed-case signup becomes unchargeable and invisible to support.
- **Verdict:** CONFIRMED — executed against the branch.
- **Why High:** Violates a written invariant ("a non-canonical write breaks every reader")
  and silently regresses existing behavior for real data shapes.
- **Fix:** Restore `normalize_email` at the write path.
- **Cites:** `docs/invariants.md §1`; `CLAUDE.md` ("Reuse helpers in app/util.py before
  writing new parsing or validation code").

#### H3 — Migration 002 is destructive with no `down()`, and new users still get `plan`, not `tier`
- **Locator:** `flow: migrations/002_drop_plan.py:4-7 → app/users.py:14`
- **What:** The migration drops `plan` in a single destructive step with no `down()`,
  violating §3 twice (additive-first with a dual-read release; every migration ships a
  `down()`). Worse, `create_user` still writes `"plan": "free"` and never writes `tier`, so
  after the migration runs, newly created users have `plan` and no `tier` — the migration's
  own target state is not maintained by the code.
- **Evidence:** probe: run `002.up(STORE)` on a store with one user, then `create_user` →
  old user has `tier` only, new user has `plan` only; `hasattr(m, "down")` → `False`.
- **Verdict:** CONFIRMED — executed against the branch.
- **Why High:** Irreversible data destruction by policy, plus a guaranteed post-deploy
  inconsistency between migrated and new rows that breaks any `tier` reader.
- **Fix:** Make the migration additive (`tier` alongside `plan`, dual-read), ship `down()`,
  and update `create_user` (and `tests/test_users.py:13`, which still asserts `plan`) to
  write `tier`.
- **Cites:** `docs/invariants.md §3`.

#### H4 — Usage limits are entirely non-functional; `api_redeem` "redeems" nonexistent codes
- **Locator:** `flow: app/billing.py:19-22 → app/api.py:30-39`
- **What:** Two cooperating defects: (a) `charge` applies a discount without checking or
  incrementing `uses`/`max_uses`, so limits are never enforced on the only path that applies
  discounts; (b) `api_redeem`'s condition is inverted — `if row is None or
  row["uses"] < row["max_uses"]` treats a *missing* code as redeemable, and the
  `except Exception: pass` at `app/api.py:36-37` swallows the resulting `KeyError`.
- **Evidence:** probes: charging twice against a `max_uses: 1` code discounts both times and
  leaves `uses == 0`; `api_redeem({"code": "NOPE"})` → `{"redeemed": True}` for a code that
  does not exist.
- **Verdict:** CONFIRMED — executed against the branch.
- **Why High:** Single-use codes are infinitely reusable at charge time — direct revenue
  leakage — and the redemption endpoint reports success for garbage input while a
  bare-except hides the evidence.
- **Fix:** Enforce and increment `uses` inside the `charge` discount branch (one atomic
  place); fix the condition to `row is not None and row["uses"] < row["max_uses"]`; delete
  the `try/except Exception: pass`.

#### H5 — Zero failure-path tests for a changed money path
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The only new test is one happy path. `app/billing.py` changed, which the repo's
  agent instructions make conditional on failure-path tests; none of the top production
  risks has a test: invalid/over-cap percent (C1), unknown discount code, `max_uses`
  exceeded (H4), post-migration user shape (H3).
- **Evidence:** full suite is 4 tests, all passing, none exercising a failure path of the
  new code (`python3 -m unittest discover tests -v`).
- **Verdict:** CONFIRMED — test files read in full; suite run.
- **Why High:** A missing test for each named top-3 risk (see Risk coverage under
  Verified); every Critical/High above shipped precisely because no failure path is tested.
- **Fix:** Add tests for: percent 0/31/-5 rejected; unknown-code behavior (per Q1); second
  use of a `max_uses: 1` code; mixed-case email charge; migrated + freshly created user both
  exposing `tier`.
- **Cites:** `CLAUDE.md` ("Every change to app/billing.py requires failure-path tests");
  `docs/testing.md` ("Money and lookup paths require failure-path tests … not just the
  happy path").

### Medium (worth fixing now; acceptable as a follow-up)

#### M1 — The "pluggable engine" is dead code; `DISCOUNT_ENGINE_BACKEND` silently does nothing
- **Locator:** `app/discount_engine/__init__.py:10-35`
- **What:** `billing.charge` imports `PercentDiscount` directly (`app/billing.py:2,22`);
  `get_strategy`, `STRATEGY_REGISTRY`, and the `DISCOUNT_ENGINE_BACKEND` env var are
  referenced nowhere else. The commit's claim that "strategies [stay] pluggable … without
  touching billing" is false as shipped.
- **Evidence:** probe: `DISCOUNT_ENGINE_BACKEND=bogus` still discounts via the hardcoded
  class; `grep` finds no callers of `get_strategy`/`validate_percent` outside the module.
- **Verdict:** CONFIRMED — executed and grepped.
- **Why Medium:** A configuration knob that silently does nothing is a maintenance trap
  (someone will set it and believe it worked), and the registry is speculative machinery for
  unscheduled futures. Walked against stated constraints: the commit names upcoming
  fixed-amount/BOGO discounts, but nothing scheduled requires the registry *now*, and the
  current wiring wouldn't use it anyway.
- **Fix:** Either wire `charge` through `get_strategy()` and add a test that the env var
  works, or (simpler) collapse the engine to a single `apply_percent(amount, pct)` function
  and add the registry when a second strategy actually lands.

#### M2 — `api_apply_credit`: unclaimed scope creep that bypasses validation and attribution
- **Locator:** `app/api.py:42-50`
- **What:** A credit endpoint absent from the commit message. It deliberately constructs
  negative cents by stripping the sign before `parse_money` (whose docstring says negative
  amounts are rejected so "adjustments are modeled explicitly"), applies no cap or
  validation, skips tax, and appends `user_id: None` charges no one can attribute.
- **Evidence:** code read; `parse_money` contract (`app/util.py:7-11`); §4 lists "credit"
  among adjustments validated at the API boundary.
- **Verdict:** CONFIRMED (behavior as described); its intent is unstated — see Q2.
- **Why Medium:** Unbounded, unattributed ledger entries in a money path, in a PR whose
  stated scope is discount codes. At minimum it belongs in its own PR with its own rules.
- **Fix:** Drop it from this branch; if wanted, reintroduce with validation, a cap, and a
  `user_id`.
- **Cites:** `docs/invariants.md §4`; `app/util.py` parse_money contract.

### Low (defer)
- **L1** [`app/users.py:9`, `app/api.py:6-8`] Unclaimed `source` field scope creep; plus
  now-dead `NotFound` class (`app/db.py:4`) and its dead handler import
  (`app/support.py:1`) once H1 is fixed — clean up together.

## Questions

- **Q1** [`app/billing.py:19-21`] Is silently charging **full price** when
  `discount_code` is unknown or invalid intended (probe: typo code → full-price charge, no
  error)? Most billing flows reject the charge so the customer isn't surprised; if the
  fallthrough is intentional, say so in a comment and test it.
- **Q2** [`app/api.py:42-50`] Is `api_apply_credit` meant to be in this PR at all (see M2),
  and if so, what validates the amount and who is the counterparty?

## Suggestions

#### S1 — Use integer basis-point math for the tax line
- **Locator:** `app/billing.py:23`
- **What:** `int(amount * (1 + TAX_RATE_BP / 10_000))` is float math in a money path
  (pre-existing, but it is the enclosing function of this diff and now consumes discounted
  amounts). `amount * (10_000 + TAX_RATE_BP) // 10_000` is §2-clean.
- **Why it'd be better:** Complies with the letter of `docs/invariants.md §2` ("floats are
  forbidden in money paths") and makes rounding explicit. A probe found no actual mispricing
  for amounts 1..199,999 cents at 500bp, so this is hygiene, not a live bug — hence a
  Suggestion.

## Gaps

- Commit message documents FIN-88 and the §4 claim well, but omits three real behavior
  changes it ships: dropped email canonicalization (H2), the `source` field, and
  `api_apply_credit` (M2). Stated-vs-shipped drift is what let C1 hide.

## Known limitations

- In-memory `STORE` means no concurrency/atomicity review of the read-modify-write on
  `uses` was meaningful; acceptable for this toy store, worth a note when a real DB lands.

## What was done well

- [`app/discount_engine/percent.py:9-10`] Discount arithmetic is pure integer math
  (`amount - (amount * pct) // 100`), correctly §2-compliant, and rounds the discount down
  (never over-discounts).
- [`app/billing.py:11`] The FIN-88 cap change is annotated with its policy reference right
  at the constant — future readers get the "why" for free.
- [`tests/test_discounts.py:8-11`] `setUp` clears all three store collections, keeping the
  new tests order-independent.
- [`migrations/002_drop_plan.py:7`] The `legacy → grandfathered` mapping shows deliberate
  thought about existing-customer treatment, even though the migration mechanics violate §3.
- Commit message quality: states problem, ticket (SUPPORT-311), constraints (FIN-88), and
  non-obvious decisions explicitly — exactly what a reviewer needs, which is also why the
  false claims in it were checkable.

## Verified

- Problem is real and unsolved in base: at `835e88d`, `STORE.discounts` exists but no code
  reads or writes it; no discount path anywhere. Not a reimplementation.
- Approach core matches the obvious sketch (API validation → store → apply in charge);
  divergences are itemized above, none explained by a found constraint except:
- **Cap 50→30 (FIN-88):** stated constraint with claimed finance sign-off — accepted as
  stated; not independently verifiable from the repo (no FIN-88 doc present). No persisted
  discounts exist to strand in the 31–50 range (in-memory store).
- Existing suite still passes on the branch (4/4) — but see H5: it never exercises the new
  failure paths, so "tests pass" carries little weight here.
- Float-tax mispricing **REFUTED as a live bug**: exhaustive probe over amounts
  1..199,999 cents found zero divergences between the float expression and integer bp math
  at 500bp — kept as hygiene Suggestion S1 only.
- Risk coverage (5k): top-3 production risks are (1) uncapped/negative discount → revenue
  loss and corrupt ledger [C1 — no covering test], (2) unlimited reuse of capped codes
  [H4 — no covering test], (3) migration data loss / `plan`-vs-`tier` split-brain
  [H3 — no covering test].
- Working tree left untouched: probes ran read-only against in-memory state; `git status`
  clean, still on `feature/discounts` at `e09c41e`.

## Not reviewed

Quick mode — skipped per skill definition: axes 5e (architecture), 5f (conventions sweep
beyond the rules cited per-finding), 5g (security), 5h (data privacy — noted in passing that
charges store `user_id`, not raw emails, per `CLAUDE.md`), 5i (testing axis beyond H5),
5j (load-bearing assumptions sweep), 5l (reversibility sweep — H3's migration finding came
from line-reading, not a systematic pass), 5m (dependency hygiene — diff adds no
dependencies), the Occam pass (M1 surfaced via the 5a claim-vs-code check instead), and
host reviewers. `docs/` was consulted only for per-finding citations (`invariants.md`,
`testing.md` read in full for that purpose). No `docs/security.md`/`privacy.md` exist;
neither is needed for this diff.

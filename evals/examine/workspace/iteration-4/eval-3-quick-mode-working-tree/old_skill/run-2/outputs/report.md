# Examine: Add discount codes with API validation (branch feature/discounts vs main)

## Headline

Hold. Do not open this PR yet. Two invariant breaks can lose money or data on deploy, and redemption limits do not work.

Mode: **quick**, as you asked. The diff is `git diff $(git merge-base HEAD main)`, commit `9437d17`. The working tree was clean, so the review holds no uncommitted changes. Skipped axes are under Not reviewed.

## Approach fit

The discount part matches the obvious approach. Store codes in the existing `STORE.discounts` dict, validate the percent at creation, and apply the percent in `billing.charge` with integer cents.

The branch also carries four changes that the discount feature does not need:

- the email write path in `app/users.py`
- the `find_user_by_email` contract in `app/db.py`
- the `plan` to `tier` migration in `migrations/002_drop_plan.py`
- a new credit endpoint, `api_apply_credit`, that the commit message does not mention

Three of the Issues below come from these extra changes. See S2.

## Issues

### Critical (must fix before merge)

#### C1: The API stores any discount percent, so a code can make a charge negative
- **Locator:** `app/api.py:22`
- **Changed anchor:** `app/api.py:18-27` (new `api_create_discount`)
- **What:** `api_create_discount` stores `int(payload["percent"])` with no range check. The commit message says "Discount percent is validated at the API boundary per docs/invariants.md §4". `validate_percent` exists in `app/discount_engine/__init__.py:26`, but no code calls it. So the new 30% cap is not enforced anywhere.
- **Evidence:** A code with `percent: 150` makes a 10.00 charge return `{'amount': -500, 'total': -525}`. A code with `percent: 45` is accepted although the cap is 30.
- **Verdict:** CONFIRMED. An execution probe and an independent verifier both reproduced it.
- **Why Critical:** The change breaks a project invariant that the commit claims to satisfy. A typo by a support agent turns a charge into a payout.
- **Fix:** Call `validate_percent` in `api_create_discount` and reject a percent outside the range before the store write. Parse the percent strictly so that `"12.5"` is rejected, not truncated by `int()`. Optionally assert the range again in `PercentDiscount.__init__`.
- **Cites:** `docs/invariants.md §4 Percentage adjustments`

#### C2: Migration 002 deletes `plan` with no `down()`, and new users still get `plan`
- **Locator:** `flow: migrations/002_drop_plan.py:4-7 → app/users.py:14`
- **What:** `up()` pops `plan` from every user in the same release that introduces `tier`. There is no `down()` and no dual-read release. `create_user` still writes `"plan": "free"` and never writes `tier`.
- **Evidence:** After `up()`, an existing user holds only `{'tier': 'standard'}`. A user created after the migration holds only `{'plan': 'free'}`. `002_drop_plan.py` has no `down` attribute.
- **Verdict:** CONFIRMED. An execution probe and an independent verifier both reproduced it.
- **Why Critical:** A rollback cannot restore the dropped `plan` values. After the deploy, the store holds two user shapes, and no reader handles both.
- **Fix:** Split the migration out of this PR. Ship it per §3. First add `tier` and dual-write it in `create_user`. Drop `plan` only in a later release, and add a `down()` that restores `plan` from `tier`.
- **Cites:** `docs/invariants.md §3 Reversible migrations`

### High (should fix before merge)

#### H1: Redemption limits do not work, so a single-use code works forever
- **Locator:** `flow: app/api.py:13-15 → app/billing.py:19-22`, and `app/api.py:30-39`
- **Changed anchor:** `app/billing.py:19-22` and the new `api_redeem`
- **What:** `billing.charge` applies a discount without a read or an increment of `uses`. `api_redeem` is the only code that increments `uses`, and the charge path never calls it. `api_redeem` also returns `{"redeemed": True}` for a code that does not exist. Its condition `row is None or ...` sends a missing code into the increment. The `except Exception: pass` then swallows the `KeyError`.
- **Evidence:** A code with `max_uses: 1` discounts three charges in a row, and its `uses` stays 0. `api_redeem({"code": "NOPE"})` returns `{'redeemed': True}`.
- **Verdict:** CONFIRMED. An execution probe and an independent verifier both reproduced it.
- **Why High:** Every code is an unlimited coupon. A shared code costs revenue on every reuse.
- **Fix:** Check and increment `uses` inside `billing.charge` when it applies the discount. Raise `BillingError` for an unknown or exhausted code. In `api_redeem`, return `{"redeemed": False}` for a missing row and remove the catch-all.

#### H2: The support console crashes on an unknown email
- **Locator:** `flow: app/db.py:18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:18` (`raise NotFound` became `return None`)
- **What:** `find_user_by_email` now returns `None` for a missing user. `support.lookup` still catches `NotFound` and then reads `u["id"]`. The commit message says "billing was updated to match", but support was not.
- **Evidence:** `support.lookup("nobody@x.y")` raises `TypeError: 'NoneType' object is not subscriptable`. Before the change, it returned `{"found": False}`.
- **Verdict:** CONFIRMED. An execution probe and an independent verifier both reproduced it.
- **Why High:** Support agents look up emails that do not exist all the time. Each such lookup now fails with an error, where it showed "not found" before.
- **Fix:** Revert the `db.py` change and the matching `billing.py` lines. No discount code calls `find_user_by_email`, so the claimed simplification does not exist. If you keep the change, update `support.lookup` and add a not-found test for it.

#### H3: New users are stored with non-canonical emails
- **Locator:** `app/users.py:12`
- **What:** `create_user` dropped `normalize_email` and now only strips whitespace. Mixed-case emails go into the store as typed, and every lookup expects the lowercase form.
- **Evidence:** A signup as `"Alice@Example.com "` stores `'Alice@Example.com'`. A charge for `alice@example.com` then raises `BillingError: unknown user`.
- **Verdict:** CONFIRMED. An execution probe and an independent verifier both reproduced it.
- **Why High:** Each mixed-case signup produces a user who cannot be charged. Every bad row then needs a backfill.
- **Fix:** Restore `email = normalize_email(email)` in `create_user`. Add a test that creates a mixed-case user and charges it by the lowercase address.
- **Cites:** `docs/invariants.md §1 Canonical emails`. `CLAUDE.md` says "Reuse helpers in app/util.py".

#### H4: No test covers any of the top three risks
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The PR adds one happy-path test, a 10% code on a 10.00 charge. `CLAUDE.md` says "Every change to app/billing.py requires failure-path tests". No test covers an invalid percent, an unknown code, an exhausted code, or the migration.
- **Evidence:** All four tests pass at `HEAD`, but C1, C2, and H1 also exist at `HEAD`. So the suite does not catch any of them.
- **Verdict:** CONFIRMED. The verifier read the diff and found only the one new test.
- **Why High:** The top three production risks are C1, C2, and H1. None of them has a test.
- **Fix:** Add tests for a percent of 0, 31, and 150. Add tests for an unknown code and an exhausted code at charge time. Add a migration test that round-trips `up()` and `down()`.
- **Cites:** `CLAUDE.md`, and `docs/testing.md` ("Money and lookup paths require failure-path tests").

### Medium (worth fixing now; acceptable as a follow-up)

#### M1: `api_apply_credit` writes negative ledger entries for no user
- **Locator:** `app/api.py:42-50`
- **What:** This endpoint removes a leading `-` before the call to `parse_money`, so it bypasses the non-negative rule of that helper. It then appends a charge row with `"user_id": None`. The commit message does not mention it, and no code or test calls it.
- **Evidence:** `api_apply_credit({"amount": "-50.00"})` appends `{'user_id': None, 'amount': -5000, 'total': -5000}`.
- **Verdict:** CONFIRMED. An execution probe and an independent verifier both reproduced it.
- **Why Medium:** No caller exists yet. When one does, each credit lowers ledger totals and belongs to no customer.
- **Fix:** Remove it from this PR. If credits are in scope, model them explicitly as the `parse_money` docstring requires. Tie each credit to a user id and validate it at the API boundary.
- **Cites:** `app/util.py:9-10`, the `parse_money` docstring ("adjustments are modeled explicitly").

### Low (defer)
- **L1** [`app/api.py:26`] A second `api_create_discount` call with the same code overwrites the row and resets `uses` to 0.

## Questions

- **Q1** [`app/billing.py:11`] Can you link FIN-88? No code reads `MAX_DISCOUNT_PERCENT` at runtime, so the 30% cap is not enforced until C1 is fixed.
- **Q2** [`app/users.py:15`] Why does a discounts PR add a `source` field to users? Which reader needs it?
- **Q3** [`scope: PR`] Does SUPPORT-311 expect a charge to consume a use automatically? Or is `api_redeem` a separate step that the client calls?

## Suggestions

#### S1: Use integer arithmetic for tax in `charge`
- **Locator:** `app/billing.py:23`
- **What:** Compute `total = amount * (10_000 + TAX_RATE_BP) // 10_000` in place of `int(amount * (1 + TAX_RATE_BP / 10_000))`.
- **Why it would be better:** The float version predates this PR and breaks `docs/invariants.md §2`. It gave no wrong result from 0 to 200,000.00 in the probe. But the rule forbids floats in money paths, and the integer form makes the rounding explicit.

#### S2: Split the unrelated changes out of this PR
- **Locator:** `scope: PR`
- **What:** Keep the discount feature here. Move the migration, the `create_user` and `find_user_by_email` changes, and `api_apply_credit` into their own PRs.
- **Why it would be better:** C2, H2, H3, and M1 all come from these extra changes. Each can then be reviewed and reverted on its own.

## Gaps

- The commit message names no manual test steps.

## What was done well

- [`app/discount_engine/percent.py:10`] `PercentDiscount.apply` uses integer cents with floor division, per `docs/invariants.md §2`.
- [`app/discount_engine/__init__.py:26-30`] `validate_percent` reads the cap from `billing.MAX_DISCOUNT_PERCENT`, so the cap has one source of truth. It only needs a caller.
- [`app/billing.py:19-22`] The discount applies before tax, so the tax is charged on the discounted amount.
- [`scope: PR`] The commit message states each decision and its reason. That made every claim checkable.

## Verified

- The four tests in the suite pass at `HEAD`, from an exported copy of the tree.
- The float tax line gave no off-by-one from 0 to 20,000,000 cents. So S1 is a rule fix, not a live bug.
- The import cycle between `billing` and `discount_engine` is safe. `validate_percent` imports `billing` inside the function, not at module load.
- Verification used execution probes on an exported copy and one independent subagent. The subagent held the diff, the files, and the candidate list, but not my reasoning. It confirmed all eight candidates. I used one verifier for all candidates, not one per candidate.
- The gap sweep found one new candidate, L1. It found no other defect.

## Not reviewed

Quick mode skipped these axes:

- 5e architecture. The repo also has no `docs/architecture.md`.
- 5f conventions, beyond the rules cited above.
- 5g security. The repo has no auth model, so I did not judge who may call the new endpoints.
- 5h privacy, including the new `source` field.
- 5i testing, beyond the 5k risk coverage in H4.
- 5j outside checks of load-bearing assumptions.
- 5l reversibility, beyond the §3 break in C2.
- 5m dependencies. The diff adds none.
- The Occam pass. The `discount_engine` registry, `get_strategy`, and the `DISCOUNT_ENGINE_BACKEND` variable have no caller. They were not judged for speculative generality.
- The host's built-in review.

Other limits:

- SUPPORT-311 and FIN-88 were not available.
- No PR exists yet, so there were no CI checks to read.

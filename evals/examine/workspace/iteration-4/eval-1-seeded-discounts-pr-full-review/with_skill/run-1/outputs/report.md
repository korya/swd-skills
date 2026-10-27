# Examine: Add discount codes with API validation (feature/discounts vs main)

## Headline

Hold. The PR claims percent validation that no code performs, ships an irreversible migration, and breaks the email invariant.

Fix C1 to C3 and H1 to H5 before merge. Then split the PR (M2).

- **Target:** branch `feature/discounts` at `28cdef8`, diffed against the merge-base with `main` (`726d610`).
- **Mode:** full. The diff touches payments, a migration, and user records with personal data.
- **Intent:** taken from the commit message, which is the PR description. No ticket text was available for SUPPORT-311 or FIN-88.
- **Tests on the branch:** 4 of 4 pass. No CI is configured for this local repository.

## Approach fit

The discount math matches the obvious approach. The rest of the PR does not.

My sketch before I read the diff had two options.

- Store codes in the existing `STORE.discounts`, validate the percent in `api.py`, and apply an integer discount inside `billing.charge`.
- Put the same logic in a small `discounts.py` module.

The PR follows the first option for the math. It also adds a strategy engine, a migration, a lookup contract change, a credit endpoint, and a `source` field. The description justifies only the engine and the migration. M1 and M2 cover the extra parts.

## Issues

### Critical (must fix before merge)

#### C1: Discount percent is never validated, so codes can create negative charges
- **Locator:** `flow: app/api.py:18-27 → app/billing.py:19-22 → app/discount_engine/percent.py:10`
- **Changed anchor:** `app/api.py:22` (`"percent": int(payload["percent"])`)
- **What:** The description says the percent "is validated at the API boundary per docs/invariants.md §4". `api_create_discount` stores any integer. `validate_percent` exists in `app/discount_engine/__init__.py:26` but nothing calls it.
- **Evidence:** A probe on the branch gave these results for a 10.00 charge.

  | Code percent | `amount` | `total` |
  |---|---|---|
  | 150 | -500 | -525 |
  | -50 | 1500 | 1575 |
  | 40 (above the new cap of 30) | 600 | 630 |

- **Verdict:** CONFIRMED. I reproduced all three inputs. The host review found the same defect separately. The verification was single-context (see Not reviewed).
- **Why Critical:** It breaks invariant §4 on a payment path. A support typo turns a charge into a payout, and a negative percent silently overcharges a customer.
- **Fix:** Call `validate_percent` in `api_create_discount` and reject the request when it returns `False`. Also check the percent again in `billing.charge`, so codes stored before a cap change cannot exceed it.
- **Cites:** `docs/invariants.md §4`

#### C2: Migration 002 drops `plan` in one irreversible step
- **Locator:** `migrations/002_drop_plan.py:4-7`
- **What:** `up()` pops `plan` from every user and writes a derived `tier`. The file has no `down()`. No earlier release reads `tier`, so the change skips the dual-read step.
- **Evidence:** A probe ran `up()` on users with plans `free`, `pro`, and `legacy`. The result was `standard`, `standard`, and `grandfathered`. The original values were gone, and `hasattr(m2, "down")` returned `False`.
- **Verdict:** CONFIRMED for the missing `down()` and for the drop. PLAUSIBLE for data loss beyond `free`, because the code writes only `free`. Production data can hold other values.
- **Why Critical:** It irreversibly damages data and breaks invariant §3. A rollback after deploy cannot restore any plan value.
- **Fix:** Make 002 additive. Add `tier` and backfill it, and keep `plan`. Add a `down()` that removes `tier`. Drop `plan` in a later migration after a release that reads `tier`. Also see H5, because `create_user` still writes `plan`.
- **Cites:** `docs/invariants.md §3`

#### C3: `create_user` stores emails in non-canonical form
- **Locator:** `app/users.py:12`
- **What:** The diff removes the `normalize_email` call and keeps only `.strip()`. Mixed-case emails reach the store unchanged.
- **Evidence:** `api_create_user({"email": " Bob@Example.COM "})` stored `'Bob@Example.COM'`. A later `api_charge` with `bob@example.com` raised `BillingError("unknown user")`. A second signup with `bob@example.com` created a second account with a new id.
- **Verdict:** CONFIRMED. I reproduced both failures on the branch.
- **Why Critical:** Invariant §1 says "a non-canonical write breaks every reader". Duplicate accounts per person need a manual merge to undo. The description does not mention this change.
- **Fix:** Restore `email = normalize_email(email)` in `create_user`.
- **Cites:** `docs/invariants.md §1`, `CLAUDE.md` ("Reuse helpers in app/util.py")

### High (should fix before merge)

#### H1: The support console crashes on an unknown email
- **Locator:** `flow: app/db.py:14-18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:18` (`return None`)
- **What:** `find_user_by_email` now returns `None` instead of raising `NotFound`. The diff updates `billing.charge` but not `support.lookup`. That function still waits for `NotFound` and then reads `u["id"]`.
- **Evidence:** `support.lookup("nobody@x.y")` raised `TypeError: 'NoneType' object is not subscriptable`. On `main` it returned `{"found": False}`.
- **Verdict:** CONFIRMED. I reproduced it. The host review found it separately.
- **Why High:** The not-found path of the support console fails for every unknown email. This is an outage on a reachable path that no test covers.
- **Fix:** Keep the raising contract and revert `app/db.py`. The discount code paths do not need the change. If a `None` return is wanted, update `support.lookup` and add a not-found test for it.

#### H2: Usage limits on codes are not enforced
- **Locator:** `flow: app/api.py:18-39 → app/billing.py:19-22`
- **What:** `max_uses` has no effect on any charge. Three defects combine.
  - `billing.charge` applies a code without reading or incrementing `uses`.
  - `api_redeem` takes the success branch when the code does not exist, and `except Exception: pass` hides the `KeyError`.
  - `api_create_discount` overwrites an existing code and resets `uses` to 0.
- **Evidence:** A code with `max_uses` 1 discounted three charges in a row, and `uses` stayed at 0. `api_redeem({"code": "NOPE"})` returned `{"redeemed": True}`. Re-creating a used code reset `uses` to 0.
- **Verdict:** CONFIRMED for all three parts. I reproduced each one. The host review found the same three defects.
- **Why High:** A single-use code becomes an unlimited discount. That is a direct revenue loss on the main payment path.
- **Fix:** Check and increment `uses` inside `billing.charge` in the same step that applies the discount. Make `api_redeem` return `{"redeemed": False}` for an unknown code and remove the bare `except`. Make `api_create_discount` reject an existing code.

#### H3: `api_apply_credit` writes unbounded credits that belong to no user
- **Locator:** `app/api.py:42-50`
- **What:** This endpoint is not in the description. It strips a leading `-` to get around the non-negative check in `parse_money`. It then appends an entry with `user_id: None` and any amount.
- **Evidence:** `api_apply_credit({"amount": "-500.00"})` appended `{"user_id": None, "amount": -50000, "total": -50000}` to `STORE.charges`.
- **Verdict:** CONFIRMED. I reproduced it. The host review found it separately.
- **Why High:** The ledger gets entries that no one can reconcile to a customer. The `parse_money` docstring says "adjustments are modeled explicitly". This endpoint models nothing and has no limit.
- **Fix:** Remove the endpoint from this PR. If credits are needed, add them in a separate PR with a user id, a bound, and failure-path tests.
- **Cites:** `app/util.py:10-11` (`parse_money` docstring), `CLAUDE.md` ("Reuse helpers in app/util.py")

#### H4: The money and lookup paths have no failure-path tests
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The PR adds one happy-path test. `CLAUDE.md` says "Every change to app/billing.py requires failure-path tests". The top three production risks have no test.
- **Evidence:** These are the top three risks and their covering tests.

  | Risk | Covering test |
  |---|---|
  | Out-of-range percent creates a negative charge (C1) | none |
  | Single-use code discounts unlimited charges (H2) | none |
  | Support lookup of an unknown email crashes (H1) | none |

  The migration (C2), the email case (C3), and the credit endpoint (H3) also have no test.
- **Verdict:** CONFIRMED. I read `tests/` on the branch. The four tests all pass. None of them covers a failure path in the new code.
- **Why High:** Each named risk is uncovered, and the project rule requires these tests.
- **Fix:** Add tests for an invalid percent, an unknown code, and an exhausted code. Also test a support lookup of an unknown email, a mixed-case signup, and migration 002 with `down()`.
- **Cites:** `CLAUDE.md`, `docs/testing.md`

#### H5: New users still get `plan` and never get `tier`
- **Locator:** `flow: migrations/002_drop_plan.py:4-7 → app/users.py:14`
- **What:** The description says users "are mapped onto the new 'tier' field". `create_user` still writes `"plan": "free"` and never writes `tier`.
- **Evidence:** After `up()`, a new user had the keys `created_at`, `email`, `id`, `name`, `plan`, and `source`. It had no `tier`.
- **Verdict:** CONFIRMED. I reproduced it.
- **Why High:** Users split into two record shapes after deploy. Any reader of `tier` fails for every new signup.
- **Fix:** Write `tier` in `create_user` as part of the additive plan in C2. Update `tests/test_users.py:11-13`.
- **Cites:** `docs/invariants.md §3`

### Medium (fix now or as a follow-up)

#### M1: The strategy engine adds parts that nothing uses
- **Locator:** `arch: app/discount_engine/`
- **What:** The package adds a registry, an abstract base class, and a `DISCOUNT_ENGINE_BACKEND` environment variable for one strategy. `billing.py:2` imports `PercentDiscount` directly. Nothing calls `get_strategy` or `validate_percent`.
- **Evidence:** With `DISCOUNT_ENGINE_BACKEND=bogo`, a 40% code still gave 40% off. `get_strategy()` raised `KeyError: 'bogo'`. `validate_percent` imports `billing` inside the function because `billing` imports the engine at module load.
- **Verdict:** CONFIRMED. The description names fixed-amount and BOGO discounts as "upcoming". It cites no ticket or schedule, so no constraint justifies the parts today.
- **Why Medium:** An operator can set the variable and expect a change that never happens. The circular import is a trap for the next strategy. The dead `validate_percent` also makes a reader believe §4 holds (C1).
- **Fix:** Replace the package with one integer-percent function in `billing.py`. Add the registry when a second strategy lands.

#### M2: The description omits changes, and the PR bundles unrelated work
- **Locator:** `scope: PR`
- **What:** The description does not mention three behavior changes.
  - `create_user` stops calling `normalize_email` (C3).
  - A `source` field comes from the payload and goes into the user record.
  - A new endpoint, `api_apply_credit` (H3), is added.

  The description says "billing was updated to match" but does not mention `support.py` (H1). The PR also mixes a policy cap change, a destructive migration, and a lookup contract change with the discount feature.
- **Evidence:** Compare the commit message of `28cdef8` with `git diff main...feature/discounts`.
- **Verdict:** CONFIRMED. I compared each description bullet with the diff.
- **Why Medium:** A reviewer who trusts the description misses C3, H1, and H3. The bundle also blocks a revert of one part without the others.
- **Fix:** Split the PR into the discount feature, the cap change, and the `tier` migration. Drop the lookup contract change, the credit endpoint, and the `source` field, or give each its own PR and description.

### Low (defer)
- **L1** [`app/billing.py:23`] Tax uses float arithmetic, which `docs/invariants.md §2` forbids. This line exists on `main`. A probe found no wrong cent below 5,000,000 cents, but `2**53` cents gives one cent too many.
- **L2** [`app/api.py:8`] `source` comes from the payload with no allowed-value check. A probe stored `<script>` as the source.
- **L3** [`app/api.py:22-24`] `int(payload["percent"])` raises a bare `ValueError` on input such as `"10%"`, and `int(10.9)` silently truncates to 10.

## Questions
- **Q1** [`app/billing.py:11`] Can you link FIN-88 and the finance sign-off? Also, what happens to codes created at 31% to 50% before this change?
- **Q2** [`app/billing.py:19-22`] An unknown or misspelled code now gives full price with no error. Is that intended, or should `api_charge` reject the code?
- **Q3** [`app/api.py:18`] The description says "Support can now create" codes. The project has no auth layer. Who can call `api_create_discount` in production?
- **Q4** [`migrations/002_drop_plan.py:7`] Which `plan` values exist in production data? The code writes only `free`, but the migration expects `legacy`.

## Suggestions

#### S1: Validate the percent once, in the API layer, against the existing cap
- **Locator:** `app/api.py:18-27`
- **What:** Move the check from `discount_engine` into `api.py` and read `billing.MAX_DISCOUNT_PERCENT` there.
- **Why it would be better:** The API boundary is where §4 puts the check. This also removes the circular import (M1).
- **Sketch:** `if not 1 <= percent <= billing.MAX_DISCOUNT_PERCENT: raise ValueError(...)`

## What was done well
- [`app/discount_engine/percent.py:10`] The discount uses integer arithmetic with floor division. This follows invariant §2, and the rounding goes in the business's favor.
- [`app/billing.py:16-17`] `charge` keeps its unknown-user failure after the lookup contract change. The existing test `test_charge_unknown_user_fails` still passes.
- [`tests/test_discounts.py:8-11`] The new test clears all three stores in `setUp`. This keeps the shared in-memory store from leaking between tests.
- [`app/billing.py:11`] The cap change carries its policy reference in a comment, so the reason stays next to the value.

## Verified
- The problem exists on `main`. `STORE.discounts` exists in `app/db.py:11` on `main`, but no code writes or reads it. No existing utility applies discounts.
- `PercentDiscount.apply` gives correct integer results for a 10.00 charge at 10% (900). The new test checks this value.
- The full suite passes on the branch: 4 tests, 0 failures.
- The sibling branch `feature/audit-log` merges with this branch without conflicts (`git merge-tree` exit 0). The merged result keeps the C3 defect.
- The host built-in review ran in a subagent as an extra source of candidates. It found nothing that this report does not cover.

## Not reviewed
- Independent per-candidate verifiers did not run. The host refused new subagents because its concurrency limit was full. I verified every finding in a single context with probes on a detached worktree. The separate host review reported C1, C2, C3, H1, H2, H3, H4, and H5 on its own.
- Dependencies (axis 5l): the diff adds none.
- Privacy beyond L2: the diff adds no new log of emails. The `CLAUDE.md` rule on raw emails holds for the changed lines.
- Auth: the project has no auth layer to compare against, so Q3 replaces an auth finding.
- CI: the repository has no CI configuration.
- The linked tickets SUPPORT-311 and FIN-88 were not available.

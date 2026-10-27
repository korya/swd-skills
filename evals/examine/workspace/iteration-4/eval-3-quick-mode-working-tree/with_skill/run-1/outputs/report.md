# Examine: Add discount codes with API validation (branch feature/discounts)

## Headline

Hold. Discounts skip the cap, single-use codes never run out, and the branch breaks email lookups and the support console.

- **Target:** branch `feature/discounts` at `520549a`, diffed against its merge-base with `main` (`5f1e0b7`). The branch has no upstream. The working tree is clean.
- **Mode:** quick, because you asked for it. The diff touches a migration and the payment path, so the skill would choose full by default. Run a full review after the fixes.
- **Intent:** taken from the commit body, because no PR description exists yet. The tickets SUPPORT-311 and FIN-88 were not available to read.

## Approach fit

The core matches the obvious approach. My sketches before I read the diff were these:

- Add a create endpoint that validates the percent, and apply the discount inside `billing.charge` with integer math.
- Do the same with one small function instead of a module.
- Consume one use of the code inside the charge, in the same step that applies it.

The pluggable engine diverges from these sketches. The commit body gives the constraint: fixed-amount and BOGO discounts come next. The branch also carries four changes that no sketch needed: the email write path, the lookup contract in `db.py`, migration 002, and the credit endpoint.

## Issues

Seven of eight findings are Critical or High. I checked the calibration. Each one has a reproduced failure on a reachable path.

### Critical (must fix before merge)

#### C1: Discount codes accept any percent, so a charge can go negative

- **Locator:** `flow: app/api.py:22 → app/billing.py:22 → app/discount_engine/percent.py:10`
- **What:** `api_create_discount` stores `int(payload["percent"])` with no check. `validate_percent` exists at `app/discount_engine/__init__.py:26`, but no code calls it. The commit body says the percent "is validated at the API boundary per docs/invariants.md §4".
- **Evidence:** I created codes and charged `"10.00"` (1000 cents) with each one.

  | Percent | Charged amount | Total with tax |
  |---|---|---|
  | 40 (cap is 30) | 600 | 630 |
  | 150 | -500 | -525 |
  | -20 | 1200 | 1260 |

- **Verdict:** CONFIRMED. An independent verifier and my probe in a detached worktree got the same results.
- **Why Critical:** It breaks invariant §4. A 150% code pays the customer. A negative code overcharges the customer.
- **Fix:** Call `validate_percent` in `api_create_discount` and reject the request when it returns false. Add the failure-path tests from H4.
- **Cites:** `docs/invariants.md §4 (Percentage adjustments)`

#### C2: New users no longer get a canonical email, so lookups miss them and duplicates appear

- **Locator:** `app/users.py:12`
- **What:** The diff removes `normalize_email(email)` and stores `email.strip()`. The email is trimmed but not lowercased. The commit body does not mention this change.
- **Evidence:** `api_create_user({"email": "  Alice@Example.COM "})` stores `'Alice@Example.COM'`. Then these calls fail:
  - `api_charge` with `alice@example.com` raises `BillingError: unknown user`.
  - A second signup with `alice@example.com` succeeds and creates a second account.
- **Verdict:** CONFIRMED. An independent verifier reproduced it with `Bob@X.com`.
- **Why Critical:** It breaks invariant §1. That section states that "a non-canonical write breaks every reader". Every row written before the fix needs a cleanup.
- **Fix:** Restore `email = normalize_email(email)` at `app/users.py:10`.
- **Cites:** `docs/invariants.md §1 (Canonical emails)`, `CLAUDE.md` ("Reuse helpers in app/util.py")

#### C3: Migration 002 drops the plan field with no way back, and new users still get the old field

- **Locator:** `migrations/002_drop_plan.py:4-7`
- **Changed anchor:** `app/users.py:14` (unchanged line in a touched function)
- **What:** `up()` pops `plan` from every user. The file has no `down()`. `create_user` still writes `"plan": "free"` and never writes `tier`.
- **Evidence:** I ran `up()` on one user and then created a second user.

  | User | `plan` | `tier` |
  |---|---|---|
  | created before the migration | removed | `standard` |
  | created after the migration | `free` | missing |

- **Verdict:** CONFIRMED in a single-context check. The subagent limit stopped its independent verifier. The probe output and `hasattr(m, "down") == False` back the verdict.
- **Why Critical:** The migration destroys data that it cannot restore. Afterwards the store holds two user shapes, and no code reads `tier`.
- **Fix:** Make it additive. Add `tier` and write it in `create_user`. Read both fields for one release. Drop `plan` in a later migration that ships a `down()`.
- **Cites:** `docs/invariants.md §3 (Reversible migrations)`

### High (should fix before merge)

#### H1: Single-use codes never run out, and unknown codes "redeem"

- **Locator:** `flow: app/billing.py:19-22 → app/api.py:30-39`
- **What:** `billing.charge` applies a code without reading or incrementing `uses`. `api_redeem` treats a missing code as redeemable. It then hits a `KeyError` and the bare `except` hides it.
- **Evidence:** A code with `max_uses=1` discounted three charges in a row, and `uses` stayed at 0. `api_redeem({"code": "NOPE"})` returned `{'redeemed': True}`.
- **Verdict:** CONFIRMED. An independent verifier and my probe agree.
- **Why High:** One leaked code gives unlimited discounts. Nothing in the data shows the abuse, because `uses` never moves.
- **Fix:** Check and increment `uses` inside `billing.charge`, in the same step that applies the discount. Fix the `api_redeem` condition to `row is not None and row["uses"] < row["max_uses"]`, and remove the bare `except`.

#### H2: The support console crashes on every unknown email

- **Locator:** `flow: app/db.py:18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:18`
- **What:** `find_user_by_email` now returns `None` instead of raising `NotFound`. The diff updated `billing.py` but not `support.py`. `support.lookup` still catches `NotFound`, which no code raises now.
- **Evidence:** `support.lookup("nobody@x.y")` raises `TypeError: 'NoneType' object is not subscriptable`. On the base it returns `{"found": False}`.
- **Verdict:** CONFIRMED. An independent verifier found both callers and reproduced the crash.
- **Why High:** A support agent who searches for a customer who does not exist gets an error instead of "not found". Together with C2, mixed-case signups also crash it.
- **Fix:** Change `support.lookup` to test for `None`. Otherwise keep the old raising contract and drop the `db.py` change. Delete `NotFound` if nothing raises it.

#### H3: The credit endpoint writes unlimited ledger entries with no user

- **Locator:** `app/api.py:42-50`
- **What:** `api_apply_credit` strips a leading `-` before it calls `parse_money`, so the non-negative guard in `parse_money` never fires. The entry has `user_id: None`, and no code checks the size. The commit body does not mention this endpoint.
- **Evidence:** `{"amount": "-99999999.99"}` appends `amount: -9999999999` to `STORE.charges`. `"999999.99"` appends a positive charge with no user. `parse_money` still rejects malformed strings such as `"--5"`.
- **Verdict:** CONFIRMED. An independent verifier and my probe agree.
- **Why High:** Any caller can add an unattributed credit of any size to the ledger. The `parse_money` docstring says that "adjustments are modeled explicitly", and this bypasses that rule.
- **Fix:** Remove the endpoint from this branch. If you need it, take a user and a bounded positive amount, and model the credit as its own entry type.
- **Cites:** `app/util.py:7-11` (docstring of `parse_money`). `docs/invariants.md §4` covers only percentage credits, so no project rule covers flat credits.

#### H4: No test covers the three main ways this branch can break production

- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The branch adds one happy-path test. It changes `app/billing.py` but adds no failure-path test. These are the top three risks:
  1. An over-cap or negative discount (C1). No test.
  2. A single-use code applied twice (H1). No test.
  3. An unknown or mixed-case email in a lookup (C2, H2). `test_charge_unknown_user_fails` covers billing only, and it still passes. No test covers `support.lookup`.
- **Evidence:** All four tests pass on `HEAD`, with all six findings above present.
- **Verdict:** CONFIRMED in a single-context check against `tests/`. The subagent limit stopped its independent verifier.
- **Why High:** Each uncovered risk is a top-three risk, and the suite stays green while all three fail.
- **Fix:** Add one failing test per risk, then fix the code until the tests pass.
- **Cites:** `CLAUDE.md` ("Every change to app/billing.py requires failure-path tests"), `docs/testing.md`

### Low (defer)

- **L1** [`app/api.py:26`] `api_create_discount` overwrites an existing code and resets its `uses` to 0.

## Questions

- **Q1** [`app/billing.py:11`] Did finance sign off on FIN-88 for 30%? Do any live codes sit between 31% and 50%?
- **Q2** [`app/billing.py:19-22`] An unknown or used-up code charges full price with no error. Is that the intended behavior for the customer?
- **Q3** [`migrations/002_drop_plan.py:7`] The code only writes `plan = "free"`. Which users have `plan == "legacy"` and become `grandfathered`?
- **Q4** [`app/api.py:37`] The comment says redemption "must never fail the charge path". The charge path does not call `api_redeem`. Who calls it?

## Suggestions

#### S1: Split the branch into one PR per change

- **Locator:** `scope: PR`
- **What:** The branch bundles five changes: discounts, the email write path, the lookup contract, migration 002, and the credit endpoint.
- **Why it would be better:** Each change has its own risk and its own rollback. C2, C3, H2, and H3 have no connection to discounts.
- **Sketch:** Keep discounts here. Move the migration, the lookup contract, and the credit endpoint into their own PRs, each with its own description.

## Gaps

- The commit body says "billing was updated to match" but does not mention `support.py`.
- The commit body does not mention the email change, the credit endpoint, or the new `source` field at `app/users.py:15`.
- No CI ran, because the branch has no remote.

## What was done well

- [`app/discount_engine/percent.py:10`] The discount math uses integers only: `amount_cents - (amount_cents * self.percent) // 100`. This follows invariant §2.
- [`app/billing.py:16-17`] `charge` still raises `BillingError` for an unknown user, so callers of billing see no contract change.
- [`scope: PR`] The commit body cites the invariant, the finance policy, and the ticket for each decision. A reviewer can check each claim.

## Verified

- **Problem is real.** On the base, `STORE.discounts` exists (`app/db.py:11`), but no code creates or applies a code.
- **Approach constraint.** The commit body states the reason for the pluggable engine: fixed-amount and BOGO discounts come next.
- **Test suite.** `python3 -m unittest discover tests -v` runs 4 tests, and all 4 pass on `HEAD`.
- **Import cycle.** `billing` imports `discount_engine`, and `validate_percent` imports `billing` inside the function. The modules load without error.
- **Float tax, REFUTED as a wrong-result bug.** `app/billing.py:23` uses a float, which `docs/invariants.md §2` forbids. This line is unchanged from the base. I compared it with exact integer math for every amount from 0 to 20,000,000 cents and found no difference.
- **Verification method.** Five candidates went to independent subagent verifiers, one each. C3 and H4 got a single-context check, because the host hit its subagent limit.

## Not reviewed

- Quick mode skipped these axes: 5e architecture, 5f conventions, 5g security, 5h privacy, 5j load-bearing assumptions, 5k reversibility, and 5l dependencies. C3 came from the correctness and completeness axes.
- Quick mode skipped the Occam pass. A full run would start with the registry and the `DISCOUNT_ENGINE_BACKEND` variable, because `billing.py` imports `PercentDiscount` directly and never calls `get_strategy`.
- Quick mode skipped the host's built-in review.
- I could not read the tickets SUPPORT-311 and FIN-88.

# Examine: Add discount codes with API validation (feature/discounts vs main)

Target: branch `feature/discounts` at `43be497`, base `main` at merge-base `4450fa8`.
The PR description is the commit message of `43be497`.

Mode: **full**. The change touches payments, adds a migration, and changes a shared lookup contract.

## Headline

Hold. The PR says it validates the discount percent, but nothing calls the validator. Any percent goes through, so a 150% code produces a negative charge. The PR also ships a destructive migration with no `down()`. It removes email normalization and adds an unannounced negative-money endpoint.

## Approach fit

The discount itself matches the obvious approach. That approach validates the percent at the API, stores the code in `STORE.discounts`, and applies it in `charge` with integer math. Five changes ride along, and I found no constraint for any of them in the description, the docs, or the history:

- the strategy engine in `app/discount_engine/`
- the contract change of `db.find_user_by_email`
- migration `002`
- the removal of `normalize_email` from `users.create_user`
- the new endpoint `api_apply_credit`

These changes cause most of the Issues below. S1 proposes to split them out.

## Issues

### Critical (must fix before merge)

#### C1: The discount percent is never validated, so a code can raise the price or pay the customer
- **Locator:** `flow: app/api.py:17-26 → app/billing.py:19-22 → app/discount_engine/percent.py:10`
- **Changed anchor:** `app/api.py:21` (`"percent": int(payload["percent"])`)
- **What:** `api_create_discount` stores any integer percent. `validate_percent` in `app/discount_engine/__init__.py:26` has no caller. The new 30% cap in `billing.py:11` does nothing.
- **Evidence:** A probe in a detached worktree created codes with these percents and charged `10.00` (1000 cents) with each:

  | Percent | Charged amount (cents) | Total with tax (cents) |
  |---|---|---|
  | 31 | 690 | 724 |
  | 100 | 0 | 0 |
  | 150 | -500 | -525 |
  | -50 | 1500 | 1575 |

  `grep validate_percent` finds only its definition.
- **Verdict:** CONFIRMED. I reproduced it and so did the host review. An independent verifier reproduced it again and could not refute it.
- **Why Critical:** The bug breaks the money path on deploy. A code over 100% writes a negative charge. A negative code overcharges the customer. The description claims the opposite, so a reader of the PR will trust it.
- **Fix:** Validate in `api_create_discount` before the write and reject an invalid percent with an error. Read the cap from `billing.MAX_DISCOUNT_PERCENT`. Add the failure-path tests from H4.
- **Cites:** `docs/invariants.md §4`, `docs/invariants.md §2`

#### C2: Migration 002 destroys the `plan` field with no `down()` and no dual-read release
- **Locator:** `flow: migrations/002_drop_plan.py:4-7 → app/users.py:14`
- **What:** `up()` pops `plan` from every user and writes `tier`. The migration has no `down()`, so a rollback cannot restore `plan`. No release reads `tier` first. `create_user` still writes `"plan": "free"` and never writes `tier`. After the migration, old and new user records have different shapes.
- **Evidence:** The probe loaded the module. `hasattr(m, "down")` is `False`. After `up()`, an existing user has `tier` and no `plan`. A user created after the migration has `plan` and no `tier`. The mapping sends every plan except `"legacy"` to `"standard"`. That includes `"free"`, so the free and paid distinction is lost and no `down()` can rebuild it.
- **Verdict:** CONFIRMED. I reproduced it, and the host review found both parts independently.
- **Why Critical:** The step damages data and cannot be undone. That breaks a written invariant. Nothing in this PR reads `tier`, so the migration has no benefit in this release.
- **Fix:** Remove `002` from this PR. Do it later in additive steps. First add `tier` and write both fields from `create_user`. Next, backfill and switch the readers. Last, drop `plan` in a later release. Each step needs a `down()`.
- **Cites:** `docs/invariants.md §3`

#### C3: `create_user` no longer stores the canonical email
- **Locator:** `app/users.py:12`
- **What:** The PR removes the `normalize_email` call and keeps only `.strip()`. Stored emails keep their case. All lookups compare exact strings, so a mixed-case signup cannot be found by its canonical email. The same person can also sign up twice. The description does not mention this change.
- **Evidence:** In the probe, `api_create_user({"email": "  Bob@Example.COM "})` stored `'Bob@Example.COM'`. Then `billing.charge("bob@example.com", "5.00")` raised `BillingError: unknown user`. A second `create_user("bob@example.com")` created a second user.
- **Verdict:** CONFIRMED. I reproduced it, and the host review also found it.
- **Why Critical:** The invariant says "a non-canonical write breaks every reader". Mixed-case users cannot be charged or found by support. Duplicate accounts are hard to merge later.
- **Fix:** Restore `email = normalize_email(email)` in `create_user`.
- **Cites:** `docs/invariants.md §1`

### High (should fix before merge)

#### H1: A code's `max_uses` limit is never enforced, so a single-use code works for every charge
- **Locator:** `flow: app/api.py:17-26 → app/billing.py:19-22 (charge) → app/api.py:30-39 (api_redeem)`
- **What:** `billing.charge` applies a discount whenever the code exists. It never reads or increments `uses`. Only `api_redeem` increments `uses`, and nothing on the charge path calls it. So `max_uses` and `uses` do not affect what a customer pays.
- **Evidence:** In the probe, a code with `max_uses=1` discounted three charges in a row to 900 cents each. A code with `max_uses=0` also applies.
- **Verdict:** CONFIRMED. I reproduced it and so did the host review. An independent verifier reproduced it again with a 20% code and could not refute it.
- **Why High:** A reachable path gives wrong money results. One leaked single-use code becomes a permanent discount.
- **Fix:** In `charge`, check `uses < max_uses` and increment `uses` in the same step as the charge. Record the code on the charge row. In a real database, use a conditional update so two charges cannot both take the last use. Then delete `api_redeem` or make it read-only.

#### H2: The support console crashes when it looks up an unknown email
- **Locator:** `flow: app/db.py:14-18 → app/support.py:5-10`
- **Changed anchor:** `app/db.py:18` (`return None` replaces `raise NotFound(email)`)
- **What:** `find_user_by_email` now returns `None` instead of raising `NotFound`. The PR updated `billing.charge` but not `support.lookup`. That function still catches `NotFound` and then indexes the result.
- **Evidence:** On `main`, `support.lookup("nobody@x")` returns `{'found': False}`. On the PR branch it raises `TypeError: 'NoneType' object is not subscriptable`.
- **Verdict:** CONFIRMED. I reproduced it, and the host review also found it.
- **Why High:** The support lookup fails for every unknown email. That is a common path. C3 makes it more common, because mixed-case users now miss too. The description says "billing was updated to match" but leaves out the other caller.
- **Fix:** Revert the `db.py` contract change, because no new discount code path needs it. If you keep it, change `support.lookup` to check for `None` and delete the dead `NotFound` handler.

#### H3: `api_apply_credit` writes negative ledger rows that belong to no user
- **Locator:** `app/api.py:42-50`
- **What:** The new endpoint removes a leading `-` before it calls `parse_money`. This gets around the helper's rule that money enters as a non-negative amount. It appends a row to `STORE.charges` with `user_id: None`, and it has no cap and no validation. The description does not mention the endpoint, and no test covers it.
- **Evidence:** In the probe, `api_apply_credit({"amount": "-5.00"})` returned `{'user_id': None, 'amount': -500, 'total': -500}`. The `parse_money` docstring at `app/util.py:9-10` says "money enters the system as a non-negative amount. Adjustments are modeled explicitly."
- **Verdict:** CONFIRMED. I reproduced it, and the host review also found it. Verification of this finding was single-context.
- **Why High:** Any caller can put a negative amount of any size into the ledger, and no user owns the row. Any reconciliation or revenue sum over `charges` comes out wrong.
- **Fix:** Remove the endpoint from this PR. If credits are needed, write a spec. Model them as an explicit adjustment type tied to a `user_id`, with a cap and failure-path tests.
- **Cites:** `CLAUDE.md` ("Reuse helpers in app/util.py"), `app/util.py:9-10`

#### H4: The PR adds no failure-path tests for the billing change or the new money paths
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The PR adds one test, and it covers only the happy path of a 10% code. Nothing tests an invalid percent, an unknown code, an exhausted code, a negative credit, or a lookup miss. These are the top three production risks of this change:
  1. A wrong charge amount from an unvalidated percent (C1). No test covers it.
  2. A single-use code that works without limit (H1). No test covers it.
  3. A lookup that fails for a mixed-case or unknown email (C3, H2). No test covers it, because `tests/test_users.py` uses only lowercase emails.
- **Evidence:** The suite of 4 tests passes on the PR branch, although C1, C2, C3, and H1 to H3 all reproduce. The repo has no CI configuration.
- **Verdict:** CONFIRMED. I read the diff and ran the tests. The host review agrees. Verification was single-context.
- **Why High:** The gap leaves the top three risks uncovered. It also breaks a written rule for `app/billing.py`.
- **Fix:** Add tests for these cases:
  - percents `0`, `-1`, `31`, and `101`, which must be rejected
  - an unknown code
  - a code past `max_uses`
  - `support.lookup` on a miss
  - a user created with a mixed-case email, then charged by its canonical email
- **Cites:** `CLAUDE.md` ("Every change to app/billing.py requires failure-path tests"), `docs/testing.md`

### Medium (fix now or as a follow-up)

#### M1: `api_redeem` reports success for a code that does not exist
- **Locator:** `app/api.py:30-39`
- **What:** The condition `row is None or row["uses"] < row["max_uses"]` sends an unknown code into the increment branch. The increment raises `KeyError`, and the bare `except Exception: pass` swallows it. The function then returns `{"redeemed": True}`.
- **Evidence:** In the probe, `api_redeem({"code": "NOPE"})` returned `{'redeemed': True}`, and `"NOPE"` was not in `STORE.discounts`. The host review reproduced the same result.
- **Verdict:** CONFIRMED. Verification of this finding was single-context.
- **Why Medium:** Any client that trusts this response gives a discount for a code that does not exist. Today `charge` ignores the result (H1), so the damage is limited to the response.
- **Fix:** Fold redemption into `charge` as H1 describes. If `api_redeem` stays, return `False` for `row is None` and remove the bare `except`.

#### M2: Re-creating a code overwrites it and resets its use count
- **Locator:** `app/api.py:17-26`
- **What:** `api_create_discount` writes `STORE.discounts[code] = row` with no existence check. A second create with the same code resets `uses` to 0 and can change its percent. It also accepts `max_uses` of 0 or less.
- **Evidence:** In the probe, an exhausted code `ONCE` had `uses == 0` again after a second create.
- **Verdict:** CONFIRMED. Verification of this finding was single-context.
- **Why Medium:** An operator can revive an exhausted code by mistake, or change a code that customers already use. It matters more after H1 is fixed.
- **Fix:** Reject a create for an existing code, and require `max_uses >= 1`.

#### M3: An unknown discount code is ignored, and the customer pays full price with no error
- **Locator:** `app/billing.py:19-22`
- **What:** `charge` applies the discount only `if row:`. A typo or an expired code falls through, and the full amount is charged. The caller gets no signal that the discount was not applied.
- **Evidence:** In the probe, `api_charge(..., "discount_code": "TYPO")` charged 1000 cents and raised nothing.
- **Verdict:** CONFIRMED. Verification of this finding was single-context.
- **Why Medium:** The customer believes the discount applied and is charged in full. That leads to support tickets and refunds. The path is an edge case.
- **Fix:** Raise `BillingError("unknown discount code")` when the PR passes a code that does not exist.

#### M4: The discount engine adds a registry, a base class, and an environment variable that nothing uses
- **Locator:** `arch: app/discount_engine/__init__.py, app/discount_engine/percent.py, app/billing.py:2`
- **What:** The package adds these parts for a single strategy:
  - `STRATEGY_REGISTRY`
  - `register`
  - the base class `DiscountStrategy`
  - `get_strategy`
  - the `DISCOUNT_ENGINE_BACKEND` environment variable

  None of them has a caller. `billing.py` imports `PercentDiscount` directly. `validate_percent` sits in the engine and imports `billing` inside the function to avoid an import cycle. The C1 bug hid there.
- **Evidence:** A grep for `get_strategy`, `STRATEGY_REGISTRY`, and `validate_percent` finds only the definitions. The docstring says the backend "is selected with the DISCOUNT_ENGINE_BACKEND environment variable". Setting the variable changes nothing.
- **Verdict:** CONFIRMED. Verification was single-context. I checked these constraints and none of them needs the engine:
  - the description, which names "upcoming" fixed-amount and BOGO discounts that no ticket schedules
  - `docs/`
  - the callers
  - the tests
- **Why Medium:** The environment variable is documented but has no effect, which misleads anyone who operates the service. The package also creates a cycle between `billing` and `discount_engine`. The next discount type will copy the pattern.
- **Fix:** Delete `app/discount_engine/`. In `charge`, write `amount -= amount * row["percent"] // 100`. Move the percent check into `api_create_discount` (C1). Add the abstraction when a second discount type is scheduled.

### Low (defer)

- **L1** [`app/billing.py:23`] The tax line uses float math, `int(amount * (1 + TAX_RATE_BP / 10_000))`, against `docs/invariants.md §2`. The line comes from `main`, but this PR touches the function. The probe found no wrong result for 0 to 200000 cents. Use `amount * (10_000 + TAX_RATE_BP) // 10_000`.
- **L2** [`app/billing.py:24`] The charge row stores only the discounted amount. It keeps neither the list price nor the code, so reports and refunds cannot see which discount applied.
- **L3** [`app/api.py:21`] `int(payload["percent"])` truncates `12.9` to `12` without an error.
- **L4** [`app/support.py:1`] After the `db.py` change, `NotFound` is never raised, so the import and the `except NotFound` branch are dead code.
- **L5** [`app/users.py:8`] The new `source` field stores any string from the payload. The description does not mention it, and nothing validates or reads it.
- **L6** [`scope: PR`] `feature/audit-log` also changes `users.create_user`. Whichever branch merges second gets a conflict in `users.py`. The person who resolves it must keep `normalize_email`.

## Questions

- **Q1** [`app/billing.py:11`] Where is the FIN-88 sign-off? Does any live code use a percent above 30 and need grandfathering after the cap drops from 50?
- **Q2** [`migrations/002_drop_plan.py:7`] What does `tier` mean, and who will read it? Why does `"free"` map to `"standard"`?
- **Q3** [`app/api.py:42`] Who asked for `api_apply_credit`, and which caller will use it?
- **Q4** [`app/api.py:8`] What is the `source` field on users for, and which values are valid?

## Suggestions

#### S1: Split the PR so the discount ships alone
- **Locator:** `scope: PR`
- **What:** Keep the discount feature in this PR. That covers C1, H1, M1 to M3, and the tests from H4. Move these changes out:
  - migration `002` and the `tier` field
  - the `normalize_email` removal (revert it)
  - the `db.find_user_by_email` contract change
  - `api_apply_credit`
  - the `source` field
- **Why it would be better:** The description justifies none of these changes by the discount, and each one carries its own risk. A small discount PR is quick to review and safe to roll back.

## Gaps

- The description cites SUPPORT-311 and FIN-88 but does not link them.
- `README.md` does not list the new endpoints.

## What was done well

- [`app/discount_engine/percent.py:10`] The discount uses integer arithmetic: `amount_cents - (amount_cents * self.percent) // 100`. It makes the rounding explicit and keeps floats out, as `docs/invariants.md §2` requires.
- [`app/billing.py:16-17`] `charge` still raises `BillingError("unknown user")` after the contract change, so `test_charge_unknown_user_fails` keeps passing.
- [`tests/test_discounts.py:13`] The new test goes through the API layer from end to end. It does not call `billing` directly.
- [`scope: PR`] The description states the intent of each change and cites the invariant it relies on. That made each claim quick to check.

## Verified

- The problem is real. On `main`, nothing creates or applies a discount. `Store.discounts` exists but has no reader or writer.
- Before reading the diff, I sketched two approaches. In both, the API validates the percent and `charge` applies it with integer math. The core discount matches them. The divergences are listed under Approach fit.
- The discount math is correct for valid input. A 10% code turns 1000 cents into 900 cents.
- The 4 existing tests pass on the PR branch.
- The lazy import in `validate_percent` does not break module import. The tests import both modules.
- Privacy: no new code stores or logs a raw email outside the users table. Charge rows carry `user_id` only. That follows the email rule in `CLAUDE.md`.
- The PR adds or bumps no dependencies.
- The float tax line in L1 gives the same result as integer floor division for every amount from 0 to 200000 cents.
- The host review found 18 candidates. Each one maps to a finding above or merges into one. Its race candidate on `api_redeem` merges into H1, because the H1 fix makes the check and the increment one step.
- Independent verifiers ran their own probes for C1 and H1 and confirmed both. One verifier charged 100.00 with a 40% code and got 6000 cents, which is over the 30% cap.
- No candidate was refuted.

## Not reviewed

- CI: the repo has no CI configuration, and the branch has no remote PR. I ran the suite locally instead.
- I could not read the tickets SUPPORT-311 and FIN-88.
- The repo has no architecture, security, or privacy doc. The diff did not need one beyond the checks above.
- Verification was partly single-context. Independent verifiers checked C1 and H1. A limit on concurrent subagents blocked the other verifiers. I verified the rest myself with probes and an adversarial re-read. The host review reproduced or found most of the same defects on its own.

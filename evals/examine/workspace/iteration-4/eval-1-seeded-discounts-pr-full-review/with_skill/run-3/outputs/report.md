# Examine: Add discount codes with API validation (feature/discounts vs main)

## Headline
Hold. The diff never validates the discount percent, it drops email canonicalization, and it ships a destructive migration with no `down()`.

**Target:** branch `feature/discounts` at `e284420`, diffed from its merge-base with `main` (`76b82c4`). The tree was clean.

**Mode:** full. The change touches payments, personal data (the email field), and a migration.

The table below checks each PR claim against the code.

| PR claim | Result |
|---|---|
| Percent is validated at the API boundary (§4) | False. `validate_percent` has no caller. |
| Cap lowered from 50% to 30% (FIN-88) | The constant changed, but nothing enforces it. |
| Pluggable discount engine | Billing bypasses the registry. The engine has one strategy. |
| `plan` dropped, users mapped onto `tier` | Data loss with no `down()`. New users still get `plan`. |
| `find_user_by_email` returns None, billing updated | `app/support.py` was not updated and now crashes. |

The diff also contains changes that the PR does not mention:

- `create_user` no longer calls `normalize_email`.
- A new `api_apply_credit` endpoint writes negative money entries.
- A new `api_redeem` endpoint.
- A new `source` field on users.

## Approach fit
The discount core matches the obvious approach: store codes, validate the percent on create, apply it in `charge` with integer arithmetic.

The bundled changes diverge from that approach. The review found no constraint in the repo that ties them to discounts. The PR says the `find_user_by_email` change "simplifies the new discount code paths". The only discount path that calls `find_user_by_email` is `charge`, and `charge` already handled `NotFound` on `main`. Each bundled change is reviewed below on its own merits.

## Issues

### Critical (must fix before merge)

#### C1: Discount percent is never validated, so out-of-cap and negative discounts reach billing
- **Locator:** `flow: app/api.py:18-27 → app/billing.py:19-22 → app/discount_engine/percent.py:10`
- **Changed anchor:** `app/discount_engine/__init__.py:26-30` (a validator with no caller)
- **What:** `api_create_discount` stores `int(payload["percent"])` with no range check. `charge` applies the stored percent as is. `validate_percent` exists, but no code calls it. The cap change to 30% therefore has no effect.
- **Evidence:** a probe on the branch gave these results for a charge of "10.00":

  | Percent | Stored amount | Stored total |
  |---|---|---|
  | 90 | 100 | 105 |
  | 150 | -500 | -525 |
  | -20 | 1200 | 1260 |

- **Verdict:** CONFIRMED. An independent verifier reproduced the 90% case and a -50% case (amount 1500). It found no call site for `validate_percent`.
- **Why Critical:** The PR claims §4 validation and does not deliver it. A percent over 100 produces a negative charge, which is a payout. A negative percent silently overcharges the customer. Finance policy FIN-88 is not enforced.
- **Fix:** In `api_create_discount`, reject a percent outside `1..MAX_DISCOUNT_PERCENT` before the store write. Accept only an integer. Add tests for 0, the cap, the cap plus 1, a negative value, and 150.
- **Cites:** `docs/invariants.md §4`, `docs/invariants.md §2`

#### C2: User creation stores emails in non-canonical form
- **Locator:** `app/users.py:12`
- **What:** The diff replaces `normalize_email(email)` with `email.strip()`. Mixed-case emails now reach the users table as typed. Every lookup assumes canonical form, so billing and support cannot find these users by their canonical email.
- **Evidence:** a probe created a user with `"Alice@Example.COM "`. The stored email was `'Alice@Example.COM'`. Then `charge("alice@example.com", "1.00")` raised `BillingError("unknown user")`. A second signup as `alice@example.com` created a second account. The base snapshot stores `'alice@example.com'` for the same input.
- **Verdict:** CONFIRMED. An independent verifier reproduced both effects. It noted that `main` has no duplicate guard either. This PR adds a new route to duplicates through case variants.
- **Why Critical:** §1 says "a non-canonical write breaks every reader". The PR does not mention this change. Accounts that split by case after deploy need a manual merge.
- **Fix:** Restore `email = normalize_email(email)` at the top of `create_user`. Add a test that creates a mixed-case user and charges it by the canonical email.
- **Cites:** `docs/invariants.md §1`

#### C3: Migration 002 destroys the `plan` field and has no `down()`
- **Locator:** `migrations/002_drop_plan.py:4-7`
- **What:** `up()` pops `plan` from every user and writes a two-value `tier`. Every plan other than `"legacy"` becomes `"standard"`, so the original value is lost. The file has no `down()`. No earlier release added dual-read of `tier`.
- **Evidence:** a probe ran `up()` on users with plans `"legacy"` and `"pro"`. They ended with tiers `grandfathered` and `standard`, and `plan` was gone. `hasattr(module, "down")` returned `False`. `migrations/001_init.py` does ship a `down()`.
- **Verdict:** CONFIRMED. An independent verifier loaded the module and reproduced the data loss.
- **Why Critical:** A rollback cannot restore the plan values. §3 requires additive steps first, a dual-read release before any destructive step, and a `down()` on every migration.
- **Fix:** Move the migration to its own PR. Make it additive: write `tier` and keep `plan`. Ship dual-read. Drop `plan` in a later release. Add a `down()`.
- **Cites:** `docs/invariants.md §3`

### High (should fix before merge)

#### H1: Support lookup crashes for unknown emails
- **Locator:** `flow: app/db.py:14-18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:18` (`raise NotFound(email)` became `return None`)
- **What:** `find_user_by_email` now returns None instead of raising `NotFound`. `support.lookup` still catches `NotFound`, so that branch is dead. It then subscripts None.
- **Evidence:** `support.lookup("nobody@x.y")` raises `TypeError: 'NoneType' object is not subscriptable` on the branch. The base returns `{"found": False}`.
- **Verdict:** CONFIRMED. An independent verifier reproduced the `TypeError`. It confirmed that `billing.py` is the only caller the diff updated.
- **Why High:** The support console fails on every search for an email with no account. Together with C2, that includes the canonical email of every user who signed up with mixed case.
- **Fix:** Revert the `db.py` change and the lookup change in `billing.py`. The discount feature does not need them. If the team wants the new contract, update `support.py` in the same PR and delete `NotFound`.

#### H2: `max_uses` is never enforced when a discount is applied
- **Locator:** `app/billing.py:19-22`
- **What:** `charge` reads the discount row and applies it. It never checks `uses` against `max_uses` and never increments `uses`. Only the separate `api_redeem` endpoint touches the counter, and `charge` does not call it.
- **Evidence:** a probe made a code with the default `max_uses` of 1 and charged three times with it. All three charges got 10% off. `uses` stayed at 0.
- **Verdict:** CONFIRMED. An independent verifier reproduced three discounted charges on a single-use code.
- **Why High:** Every single-use code is unlimited. That is a direct revenue leak on the main path of the feature.
- **Fix:** Check and increment the counter inside `charge`, in the same step that applies the discount. Reject an exhausted code with `BillingError`. Add a test that charges a single-use code twice.

#### H3: `api_apply_credit` writes unbounded negative money entries attached to no user
- **Locator:** `app/api.py:42-50`
- **What:** The endpoint strips a leading `-`, parses the rest, and negates it. It then appends the entry to `STORE.charges` with `user_id: None`. Nothing bounds the amount. The PR description does not mention this endpoint.
- **Evidence:** `api_apply_credit({"amount": "-999999.99"})` appended `{'user_id': None, 'amount': -99999999, 'total': -99999999}`. A positive "5.00" credit is recorded as a +500 charge, so the sign meaning is unclear too.
- **Verdict:** CONFIRMED. An independent verifier reproduced a -50000 cent entry with no user.
- **Why High:** The `parse_money` docstring says that money enters the system as a non-negative amount. It also says that adjustments are modeled explicitly. This wrapper bypasses both rules. A credit with no user cannot be reconciled or reversed against an account.
- **Fix:** Remove the endpoint from this PR. If credits are needed, model them as an explicit credit record tied to a `user_id`, with a validated bound, in a separate PR.
- **Cites:** `app/util.py:9-10` (the `parse_money` docstring), `CLAUDE.md` rule 2 (reuse helpers in `app/util.py`), `docs/invariants.md §4` (credits are validated at the API boundary)

#### H4: The billing change ships without failure-path tests
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The only new test is one happy-path charge with a valid 10% code. None of the three top production risks below has a test.
- **Evidence:** the full suite passes on the branch with 4 tests. The defects in C1, C2, H1, and H2 all reproduce while the suite passes.
- **Verdict:** CONFIRMED. An independent verifier found no test for an unknown code, an over-cap percent, or an exhausted code.
- **Why High:** `CLAUDE.md` says "Every change to app/billing.py requires failure-path tests". The missing tests are why the defects above pass the suite.
- **Fix:** Add the tests that the fixes for C1, C2, H1, and H2 name. Also test an unknown code and an exhausted code.
- **Cites:** `CLAUDE.md` rule 3, `docs/testing.md`

The top three production risks have no covering test:

| Risk | Covering test |
|---|---|
| A discount outside the cap gives a negative or inflated charge (C1) | None |
| Mixed-case signups cannot be charged or found (C2, H1) | None |
| Migration 002 loses plan data with no rollback (C3) | None |

### Medium (fix now or as a follow-up)

#### M1: `api_redeem` reports success for a code that does not exist
- **Locator:** `app/api.py:33-38`
- **What:** The condition `row is None or row["uses"] < row["max_uses"]` sends an unknown code into the increment. The increment raises `KeyError`, and `except Exception: pass` swallows it. The endpoint returns `{"redeemed": True}`.
- **Evidence:** `api_redeem({"code": "NOPE"})` returned `{'redeemed': True}`.
- **Verdict:** CONFIRMED. An independent verifier reproduced it and traced the swallowed `KeyError`.
- **Why Medium:** A caller that trusts the response grants a discount for any typed string. The bare `except` also hides every other failure. The comment says "redemption must never fail the charge path", but `charge` does not call this endpoint.
- **Fix:** Return `{"redeemed": False}` for an unknown code and remove the `try/except`. If the fix for H2 moves the counter into `charge`, delete this endpoint.

#### M2: Re-creating an existing code resets its usage counter
- **Locator:** `app/api.py:26`
- **What:** `api_create_discount` overwrites `STORE.discounts[code]` with a new row where `uses` is 0.
- **Evidence:** a probe created code `S` with `max_uses` 5, then created `S` again with percent 30. The stored row became `{'percent': 30, 'uses': 0, 'max_uses': 1}`.
- **Verdict:** CONFIRMED. An independent verifier reproduced the reset after two redemptions.
- **Why Medium:** An exhausted single-use code becomes usable again. A support agent who reuses a code name silently changes a live discount.
- **Fix:** Reject a create for a code that already exists.

#### M3: New users still get `plan` and never get `tier`
- **Locator:** `app/users.py:14`
- **Changed anchor:** `migrations/002_drop_plan.py:6-7`
- **What:** After migration 002, migrated users have `tier` and no `plan`. Users created later have `plan: "free"` and no `tier`. No code reads `tier`.
- **Evidence:** a probe ran `up()` and then created a user. The new user had `plan: 'free'` and no `tier`. `tests/test_users.py:13` still asserts `plan`.
- **Verdict:** CONFIRMED. An independent verifier reproduced the two record shapes.
- **Why Medium:** Two record shapes coexist. A future reader of either field gets a `KeyError` on part of the users.
- **Fix:** Fold this into the fix for C3. The additive migration must also change `create_user` to write `tier`.
- **Cites:** `docs/invariants.md §3`

#### M4: An unknown discount code is silently ignored at charge time
- **Locator:** `app/billing.py:19-22`
- **What:** `charge` skips the discount when the code is not in the store. It raises no error and records nothing.
- **Evidence:** a charge with `discount_code="TYPO"` stored `amount` 1000, the full price, with no error.
- **Verdict:** CONFIRMED. An independent verifier reproduced the full-price charge.
- **Why Medium:** A customer who mistypes a code pays full price and gets no signal. Support then receives the complaint that SUPPORT-311 was meant to close.
- **Fix:** Raise `BillingError("unknown discount code")` when a code is given and not found.

#### M5: The discount engine adds a registry and an environment switch that nothing uses
- **Locator:** `arch: app/discount_engine/__init__.py:10-35`
- **What:** The package adds `STRATEGY_REGISTRY`, `register`, `get_strategy`, and the `DISCOUNT_ENGINE_BACKEND` variable. `billing.py:2` imports `PercentDiscount` directly, so the registry and the variable have no effect. `validate_percent` imports `billing` inside the function to avoid a circular import.
- **Evidence:** `get_strategy` and `validate_percent` have no callers. `get_strategy("fixed")` raises a bare `KeyError`.
- **Verdict:** CONFIRMED. An independent verifier searched `CLAUDE.md`, `docs/`, and `README.md` and found no constraint that asks for pluggable strategies.
- **Why Medium:** The environment variable is a configuration surface that does nothing. An operator who sets it gets no change and no error. The dead `validate_percent` looks like the §4 check and hid C1 from the author. Constraints checked: the PR cites "upcoming fixed-amount and BOGO discounts", but no doc or ticket in the repo schedules them.
- **Fix:** Replace the package with one integer function in `billing.py`: `amount - amount * percent // 100`. Keep the cap and its validator in one module. Add a registry when a second strategy exists.

### Low (defer)
- **L1** [`app/billing.py:23`] Tax uses float arithmetic, which breaks §2. The line predates the PR. Probes found no wrong result up to 10^13 cents.
- **L2** [`app/billing.py:24`] The charge entry records neither the code nor the pre-discount amount, so a refund cannot reconstruct the discount.
- **L3** [`app/api.py:8-10`] The new `source` field comes from the payload unchecked. The PR does not mention it.
- **L4** [`app/api.py:22`] `int()` truncates a float percent such as 10.9 to 10 and raises `ValueError` on the string "12.5".

## Questions
- **Q1** [`app/billing.py:11`] Where is FIN-88 recorded? The repo has no reference to it, so the review could not check the sign-off.
- **Q2** [`migrations/002_drop_plan.py:7`] Is the mapping from `free` to `standard` intended? The base code creates every user with `plan: "free"`.
- **Q3** [`flow: app/api.py:18 → app/api.py:42`] Which layer restricts discount and credit creation to support staff? The `api` module has no auth for any endpoint, new or old.
- **Q4** [`app/billing.py:22-23`] Did finance confirm that the discount applies before tax?

## Suggestions

#### S1: Split the PR into the discount feature and the unrelated changes
- **Locator:** `scope: PR`
- **What:** Ship the discount feature alone. Move the migration, the lookup contract change, the credit endpoint, and the `source` field to their own PRs.
- **Why it would be better:** C2, C3, H1, and H3 all come from bundled changes. Each one needs its own rollout plan, and the discount feature needs none of them.

## What was done well
- [`app/discount_engine/percent.py:10`] The discount uses integer arithmetic: `amount_cents - (amount_cents * self.percent) // 100`. It follows §2 and rounds the discount down.
- [`app/billing.py:16-17`] Billing keeps the `BillingError("unknown user")` contract, so `tests/test_billing.py` still passes unchanged.
- [`app/api.py:14`] `discount_code` is optional, so existing `api_charge` callers keep working.

## Verified
- The problem is real in the base snapshot. `main` has `STORE.discounts` and `MAX_DISCOUNT_PERCENT`, but no way to create or apply a code. No existing utility solves it.
- The full suite passes on both `main` (3 tests) and the branch (4 tests).
- `feature/discounts` and `feature/audit-log` merge without conflict (`git merge-tree`).
- The engine import order works. `billing` imports `percent`, and `validate_percent` imports `billing` lazily.
- No raw email reaches discounts, charges, or logs. Charges reference `user_id`, which follows the email rule in `CLAUDE.md`.
- Four independent subagent verifiers tried to refute every Medium and higher candidate. They refuted none.
- The gap sweep looked at moved guards and flipped defaults. It added L2. The cap change from 50 to 30 strands no existing codes, because `main` had no way to create one.

## Not reviewed
- Dependencies (axis 5l): the diff adds none.
- Privacy beyond the email rule: the repo has no privacy policy doc. The only new user field is `source`.
- CI results: the fixture has no CI. The review ran the suite locally instead.
- FIN-88 and SUPPORT-311: the review had no access to these tickets.

Each verifier checked two to four candidates without this reviewer's reasoning. A separate subagent ran a defect-first review as one more source of candidates.

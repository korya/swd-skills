# Examine: Add discount codes with API validation (feature/discounts vs main)

Mode: **full**. The diff touches payments, a data migration, and a lookup contract. The review covers `git diff main...feature/discounts` at `e284420`, a clean tree.

## Headline

Hold. A customer charge can go negative today, and the migration destroys plan data with no way back.

The PR claims that the API validates the discount percent. No code calls the validator. The PR also bundles four changes that the discount feature does not need. Two of them break existing callers.

## Approach fit

The discount core matches the obvious approach: store a code row, then apply an integer percentage inside `billing.charge`.

Four additions go beyond that sketch, and I found no constraint for any of them:

- the pluggable strategy engine (`app/discount_engine/`)
- the `find_user_by_email` contract change (`app/db.py`)
- migration 002, which drops `plan`
- the credit endpoint and the `create_user` changes (`app/api.py`, `app/users.py`)

M1 covers the scope. The line findings on the core are not provisional.

## Issues

### Critical (must fix before merge)

#### C1: The API stores any discount percent, so a charge can go negative

- **Locator:** `app/api.py:22`
- **Changed anchor:** `api_create_discount`, new in this PR. `validate_percent` in `app/discount_engine/__init__.py:26` has no caller.
- **What:** `api_create_discount` stores `int(payload["percent"])` without a range check. `billing.charge` then applies the stored percent with no check of its own. The 30% cap therefore has no effect.
- **Evidence:** I ran these probes in a detached worktree:

  | Percent | Charge of 10.00 | Result |
  |---|---|---|
  | 150 | `amount -500, total -525` | the store pays the customer |
  | 100 | `total 0` | free purchase |
  | -20 | `amount 1200, total 1260` | the customer pays a surcharge |
  | 31 | accepted | the cap is 30 |

- **Verdict:** CONFIRMED. I reproduced each row, and a grep found no caller of `validate_percent`.
- **Why Critical:** It violates the invariant on percentage adjustments. One bad code turns every charge that uses it into a payout.
- **Fix:** Call `validate_percent` in `api_create_discount` and reject a bad value with a clear error. Also reject a non-positive `max_uses`. Add tests for 0, 31, 100, and -1.
- **Cites:** `docs/invariants.md §4 (Percentage adjustments)`. The PR description claims compliance with this section.

#### C2: Migration 002 destroys the plan field with no down() and no dual-read release

- **Locator:** `flow: migrations/002_drop_plan.py:4-7 → app/users.py:14`
- **What:** `up()` pops `plan` from every user and writes `tier`. Every plan except `legacy` becomes `standard`. The migration has no `down()`.
- **Evidence:**
  - A probe user with `plan="pro"` came out as `tier="standard"` with no `plan`.
  - `hasattr(module, "down")` returned `False`.
  - `create_user` still writes `"plan": "free"` and never writes `tier`. A user created after the migration has `plan="free"` and `tier=None`.
- **Verdict:** CONFIRMED for the missing `down()` and the new-user mismatch. The loss of paid plan values is PLAUSIBLE, because it depends on which plan values exist in production data.
- **Why Critical:** The original plan value cannot be restored after `up()` runs. Readers of `tier` will see `None` for every new user.
- **Fix:** Take the migration out of this PR. In its own PR, add `tier` as an additive step, write both fields, and ship a `down()`. Drop `plan` only after a release with dual-read.
- **Cites:** `docs/invariants.md §3 (Reversible migrations)`.

### High (should fix before merge)

#### H1: A support lookup for an unknown email now crashes

- **Locator:** `flow: app/db.py:18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:18`, where `find_user_by_email` returns `None` instead of raising `NotFound`.
- **What:** `support.lookup` still catches `NotFound` and then reads `u["id"]`. A miss now reaches that line with `u = None`.
- **Evidence:** `support.lookup("nobody@x.y")` raised `TypeError: 'NoneType' object is not subscriptable`. On `main` it returns `{"found": False}`.
- **Verdict:** CONFIRMED. I reproduced the crash. A grep found `support.lookup` as the only other caller.
- **Why High:** Support agents get an error for every customer who is not on file. The PR says "billing was updated to match" and misses this caller.
- **Fix:** Keep the `NotFound` contract. The discount code does not need the change, because `charge` handled the exception correctly on `main`. If you keep the new contract, update `support.lookup` and add a not-found test.
- **Cites:** `docs/testing.md` asks for not-found tests on lookup paths.

#### H2: Mixed-case emails are stored as typed, so later lookups miss

- **Locator:** `app/users.py:12`
- **What:** `create_user` replaced `normalize_email(email)` with `email.strip()`. The store now keeps the case that the caller sent.
- **Evidence:** `api_create_user` with `" Bob@Example.COM "` stored `"Bob@Example.COM"`. A charge to `"bob@example.com"` then raised `BillingError: unknown user`. Case variants of one address create separate users.
- **Verdict:** CONFIRMED. I reproduced the stored value and the failed charge.
- **Why High:** Customers cannot pay, and duplicate accounts appear. The PR description does not mention this change.
- **Fix:** Restore `email = normalize_email(email)`.
- **Cites:** `docs/invariants.md §1 (Canonical emails)`. Also `CLAUDE.md`, which says "Reuse helpers in app/util.py".

#### H3: Discount codes ignore their use limit, and redeem reports success for unknown codes

- **Locator:** `flow: app/billing.py:19-22 → app/api.py:31-39`
- **What:** `charge` applies any stored code and never reads or updates `uses`. `api_redeem` is the only code that counts uses, and nothing connects it to `charge`. Its condition `row is None or ...` also sends an unknown code into the success branch.
- **Evidence:**
  - A code with `max_uses=1` discounted three charges in a row. `uses` stayed at 1.
  - `api_redeem({"code": "NOPE"})` returned `{"redeemed": True}`. `except Exception: pass` swallowed the `KeyError`.
- **Verdict:** CONFIRMED. I reproduced both behaviors.
- **Why High:** A single-use code works without limit, so every leaked code costs money. The redeem response misleads any caller that trusts it.
- **Fix:** In `charge`, reject an exhausted code and increment `uses` in the same step that applies the discount. Remove `api_redeem`, or make it return `False` for an unknown code and drop the bare `except`.
- **Cites:** none in the project docs. The judgment rests on the PR's own `max_uses` field.

#### H4: The new credit endpoint writes unbounded negative charges that belong to no user

- **Locator:** `app/api.py:42-50`
- **What:** `api_apply_credit` strips a leading `-`, parses the rest, and negates it. This works around the non-negative rule in `parse_money`. It appends the entry with `user_id: None` and no limit.
- **Evidence:** `api_apply_credit({"amount": "-500.00"})` appended `{"user_id": None, "amount": -50000, "total": -50000}` to `STORE.charges`.
- **Verdict:** CONFIRMED. I reproduced the entry.
- **Why High:** Nobody can attribute, cap, or reconcile these ledger entries. The endpoint has no test, and the PR description does not mention it.
- **Fix:** Remove the endpoint from this PR. If finance needs credits, model them explicitly with a user id, a cap, and failure-path tests, as the `parse_money` docstring says.
- **Cites:** `app/util.py:10-11`, which says that money enters the system as a non-negative amount and that adjustments are modeled explicitly. Also `CLAUDE.md` on failure-path tests for money paths.

### Medium (worth fixing now; acceptable as a follow-up)

#### M1: The PR bundles four unrelated changes, and two descriptions do not match the code

- **Locator:** `scope: PR`
- **What:** The discount feature needs only a code store, a validator, and a change to `charge`. The PR also changes the user lookup contract, the user email write path, the plan schema, and the ledger.
- **Evidence:**
  - "Discount percent is validated at the API boundary" is false (C1).
  - "billing was updated to match" omits `support.py` (H1).
  - The description does not mention the credit endpoint, the `source` field, or the email change.
- **Verdict:** CONFIRMED. I compared each bullet of the description with the diff.
- **Why Medium:** One revert would undo the discount feature, the migration, and the lookup change together. Two of the bundled changes cause H1 and H2.
- **Fix:** Split the PR into the discount feature and separate PRs for the migration and any credit feature. Drop the lookup and email changes.

#### M2: The PR adds money paths with only one happy-path test

- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The only new test charges a valid 10% code. No test covers an invalid percent, an unknown code, an exhausted code, a credit, or the migration.
- **Evidence:** The suite passes with 4 tests while C1, C2, H1, H2, H3, and H4 are all present.
- **Verdict:** CONFIRMED. I ran the suite.
- **Why Medium:** The top three risks are negative charges, unlimited code reuse, and plan data loss. No test covers any of them.
- **Fix:** Add failure-path tests for each of those risks, and a not-found test for `support.lookup`.
- **Cites:** `CLAUDE.md`: "Every change to app/billing.py requires failure-path tests". Also `docs/testing.md`.

#### M3: Re-creating a code resets its use count

- **Locator:** `app/api.py:26`
- **What:** `api_create_discount` overwrites the existing row with `uses: 0`.
- **Evidence:** I exhausted a single-use code and created it again. `uses` went back to 0, so the code worked again.
- **Verdict:** CONFIRMED. I reproduced the reset.
- **Why Medium:** A support agent who re-creates a code by mistake revives it.
- **Fix:** Reject a create for a code that exists, or make the update path explicit.

#### M4: A mistyped discount code is ignored, and the customer pays full price

- **Locator:** `app/billing.py:20-22`
- **What:** `charge` skips the discount when the code is unknown and reports no error.
- **Evidence:** A charge of 10.00 with code `SAVE1O` returned `amount 1000`. The customer gets no message.
- **Verdict:** CONFIRMED. I reproduced the charge.
- **Why Medium:** Customers pay more than they expect and learn only from the receipt.
- **Fix:** Raise `BillingError("unknown discount code")` before the charge.

### Low (defer)

- **L1** [`app/api.py:22`] `int(payload["percent"])` truncates `10.9` to 10 and raises an unhandled `ValueError` for `"10.5"`.
- **L2** [`app/api.py:8`] The API stores `source` from the payload without validation. The description does not mention it.
- **L3** [`app/billing.py:23`] An unchanged line uses floats in a money path, which `docs/invariants.md §2` forbids. Probes over 0 to 2000.00 matched integer math.
- **L4** [`app/db.py:4`] `NotFound` has no raiser after this PR. Only `support.py` still imports it.

## Questions

- **Q1** [`app/billing.py:11`] Can you link FIN-88 and the finance sign-off for the cap of 30%? I could not reach it.
- **Q2** [`app/api.py:18`] Which callers may create discounts and credits? The repo has no access control for any endpoint.
- **Q3** [`app/billing.py:22`] Should the discount apply before tax, as now, or after? The invariants do not say.

## Suggestions

#### S1: Collapse the discount engine into one function in billing

- **Locator:** `app/discount_engine/__init__.py:1-35`
- **What:** Replace the registry, the ABC, `get_strategy`, and `DISCOUNT_ENGINE_BACKEND` with one integer function in `billing.py`.
- **Why it would be better:** `billing.py` imports `PercentDiscount` directly and bypasses the registry. `get_strategy` has no caller, and it raises `KeyError` for an unregistered backend name. The engine also imports `billing` for the cap, so the two modules depend on each other. Add the abstraction when the second discount kind arrives. I walked this against the stated future of fixed-amount and BOGO discounts, and found no ticket for them.
- **Sketch:**

  ```python
  def apply_percent(amount_cents: int, percent: int) -> int:
      return amount_cents - (amount_cents * percent) // 100
  ```

#### S2: Record the code and the original amount on the charge entry

- **Locator:** `app/billing.py:24`
- **What:** Add `discount_code` and `gross_amount` to the entry.
- **Why it would be better:** Finance can then reconcile discounts and refund the right amount. Today the entry keeps only the discounted amount.

## Gaps

- The PR does not link SUPPORT-311 or FIN-88, so I could not read the source requirements.
- The PR describes no manual test.

## Known limitations

- `feature/audit-log` also changes `app/users.py` and `app/db.py`. `git merge-tree` shows that the two branches merge cleanly. I did not review the combined behavior, and this verdict does not depend on it.

## What was done well

- [`app/discount_engine/percent.py:10`] `PercentDiscount.apply` uses integer arithmetic only. It rounds the discount down explicitly, as `docs/invariants.md §2` asks.
- [`tests/test_discounts.py:9-11`] The new test clears the users, discounts, and charges in `setUp`, so it does not depend on test order.
- [`app/billing.py:11`] The PR keeps the cap in `billing.MAX_DISCOUNT_PERCENT`, where `docs/invariants.md §4` places it.

## Verified

- The problem is real. On `main`, `STORE.discounts` exists, but no code writes or reads it.
- The suite passes on the branch: 4 tests, `OK`.
- Python's `int()` truncates a float toward zero and raises `ValueError` for `"10.5"`. I confirmed this against the stdlib behavior (L1).
- The PR adds no dependencies.
- No new field stores a raw email outside the users table, so the `CLAUDE.md` rule on emails holds.
- The description says that the lookup change "simplifies the new discount code paths". The code refutes this. The only discount path that calls `find_user_by_email` is `charge`, which handled `NotFound` correctly on `main`.
- An independent defect-first reviewer in a subagent found the same Critical and High candidates.

Verification of the candidates was single-context. The host refused new verifier subagents at its concurrency limit. I re-read each candidate adversarially and reproduced every Medium and higher one in a detached worktree.

## Not reviewed

- No `docs/architecture.md`, `docs/security.md`, or `docs/privacy.md` exists. I judged layering and access control without a project rule, and I raised access control as Q2.
- I could not reach the tickets SUPPORT-311 and FIN-88.
- The PR has no CI run, because it exists only as a local branch.

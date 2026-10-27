# Examine: Add discount codes with API validation (feature/discounts vs main)

## Headline
Hold. The branch breaks three project invariants and lets a discount code produce a negative charge.

Mode: full. The diff touches payments (`app/billing.py`) and ships a destructive migration (`migrations/002_drop_plan.py`).

Reviewed range: `git diff $(git merge-base HEAD main)`, from base `d7b4cfd` to head `d3313dd`. The working tree was clean.

## Approach fit
The discount flow matches the obvious approach. It stores a code, checks it at the API, and applies an integer percent in `billing.charge`.

The PR also ships five changes that the discount flow does not need. The description gives no valid constraint for them, see M1. The line-level findings below are not provisional.

## Issues

### Critical (must fix before merge)

#### C1: Discount percent is never validated, so a code can make a charge negative
- **Locator:** `flow: app/api.py:18-27 → app/billing.py:19-22 → app/discount_engine/percent.py:10`
- **Changed anchor:** `app/api.py:18-27` (new `api_create_discount`)
- **What:** `api_create_discount` stores `int(payload["percent"])` with no range check. `validate_percent` exists at `app/discount_engine/__init__.py:26`, but no code calls it. The description says the percent "is validated at the API boundary per docs/invariants.md §4". That claim is false.
- **Evidence:** a probe on a detached worktree created a code and charged `"10.00"` with it. The results:

  | percent | amount | total |
  |---|---|---|
  | 150 | -500 | -525 |
  | 100 | 0 | 0 |
  | 31 | 690 | 724 |
  | -20 | 1200 | 1260 |

- **Verdict:** CONFIRMED. The probe reproduced each row. A separate reviewer reproduced the 150 and -50 cases without this review's notes.
- **Why Critical:** A code above 100 percent creates a negative charge, which pays money out. A negative code surcharges the customer. The new 30 percent cap from FIN-88 has no effect. This violates a documented invariant.
- **Fix:** In `api_create_discount`, reject the payload when `validate_percent` returns false. Also reject a non-integer percent. Add the failure-path tests from H4.
- **Cites:** `docs/invariants.md §4` ("Any percentage adjustment ... is validated at the API boundary before it reaches billing")

#### C2: New users are stored with a non-canonical email
- **Locator:** `app/users.py:15`
- **What:** The PR removes the `normalize_email` call from `create_user` and keeps only `email.strip()`. Mixed-case emails now reach the store unchanged. The description does not mention this change.
- **Evidence:** the probe created a user as `" Alice@Example.COM "`. The store held `'Alice@Example.COM'`. A charge for `alice@example.com` then raised `BillingError: unknown user`. A second signup as `alice@example.com` created a second user for the same person.
- **Verdict:** CONFIRMED. The probe reproduced it, and a separate reviewer reproduced it independently.
- **Why Critical:** The invariant says "a non-canonical write breaks every reader". Charges and support lookups fail for these users, and duplicate accounts appear. The store keeps the bad data after a revert.
- **Fix:** Restore `email = normalize_email(email)` in `create_user`.
- **Cites:** `docs/invariants.md §1`. `CLAUDE.md` ("Reuse helpers in app/util.py before writing new parsing or validation code").

#### C3: Migration 002 drops the plan field in one step and has no down()
- **Locator:** `migrations/002_drop_plan.py:4-7`
- **What:** `up()` pops `plan` from every user and writes `tier`. The migration has no `down()`, unlike `001_init.py`. No earlier release reads both fields. Every plan value except `"legacy"` becomes `"standard"`, so the original value is lost.
- **Evidence:** the probe ran `up()` on users with plans `free`, `pro`, and `legacy`. The result was `standard`, `standard`, and `grandfathered`. The module has no `down` attribute. `git grep tier main` finds nothing, so no dual-read release exists.
- **Verdict:** CONFIRMED. The probe reproduced it, and an independent verifier confirmed it from the code and §3.
- **Why Critical:** The migration destroys data that no rollback can restore. The invariant requires additive steps first, a dual-read release, and a `down()`.
- **Fix:** Remove the migration from this PR. In a separate PR, add `tier` additively and backfill it. Ship dual-read code. Drop `plan` in a later release, with a `down()` that restores it.
- **Cites:** `docs/invariants.md §3`

### High (should fix before merge)

#### H1: The support console crashes on an unknown email
- **Locator:** `flow: app/db.py:14-18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:18` (`raise NotFound` replaced by `return None`)
- **What:** `find_user_by_email` now returns `None` for an unknown email. `support.lookup` still catches `NotFound`, which no code raises now. It then reads `u["id"]` on `None`. The description says "billing was updated to match" but does not mention `support.py`.
- **Evidence:** `support.lookup("nobody@x.y")` raised `TypeError: 'NoneType' object is not subscriptable`. On `main` the same call returns `{"found": False}`.
- **Verdict:** CONFIRMED. The probe reproduced it, and two separate agents found it independently.
- **Why High:** Each support lookup for an unknown email now fails with an exception. Before, it showed "not found". The change is an outage of a reachable path. No test covers it.
- **Fix:** Keep the `NotFound` contract and leave `billing.charge` as on `main`. Or update `support.lookup` to check for `None` and add a not-found test for it.
- **Cites:** `docs/testing.md` ("Money and lookup paths require failure-path tests (... not-found ...)")

#### H2: api_apply_credit accepts any negative amount and records it with no user
- **Locator:** `app/api.py:42-50`
- **What:** This endpoint is new, and the description does not mention it. It strips a leading `-`, parses the rest, and negates the result. The entry goes into `STORE.charges` with `user_id: None`. The endpoint has no bound and no user. A positive "credit" is stored as a positive charge, so the sign convention is also unclear.
- **Evidence:** `api_apply_credit({"amount": "-500.00"})` returned `{'user_id': None, 'amount': -50000, 'total': -50000}`.
- **Verdict:** CONFIRMED. The probe reproduced it, and a separate reviewer reproduced it with `-999.00`.
- **Why High:** Any caller can write an unbounded credit into the charge ledger. Nobody can reconcile the credit to a customer. The code also defeats the negative guard in `parse_money`.
- **Fix:** Remove the endpoint from this PR. If credits are needed, model them as an explicit adjustment type with a user id, a bound, and tests.
- **Cites:** `app/util.py:8-11` docstring of `parse_money` says that "money enters the system as a non-negative amount" and that "adjustments are modeled explicitly". `docs/invariants.md §4` names credits as adjustments.

#### H3: Usage limits on codes are not enforced
- **Locator:** `flow: app/api.py:30-39 (api_redeem) ↔ app/billing.py:19-22 (charge)`
- **What:** `charge` applies the code without a check of `uses` against `max_uses`, and it never increments `uses`. `api_redeem` is the only code that counts uses, and `charge` does not call it. Its condition `row is None or row["uses"] < row["max_uses"]` sends an unknown code into the increment branch. The `KeyError` that follows is swallowed, and the call returns `{"redeemed": True}`.
- **Evidence:** the probe charged a code with `max_uses=1` three times. Each charge gave 20 percent off, and `uses` stayed at 0. `api_redeem({"code": "NOPE"})` returned `{"redeemed": True}` with an empty discount table.
- **Verdict:** CONFIRMED. The probe reproduced both paths, and two separate agents found both independently.
- **Why High:** A single-use code is an unlimited-use code. Revenue leaks on each reuse. A client that gates on `api_redeem` accepts any string as a valid code.
- **Fix:** Check and increment `uses` inside `charge`, in the same step that applies the discount. Make `api_redeem` return `{"redeemed": False}` for an unknown code and remove the `except Exception: pass`.
- **Cites:** no project rule. The comment "redemption must never fail the charge path" does not apply, because `charge` never calls `api_redeem`.

#### H4: The billing change ships with only a happy-path test
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The PR changes `app/billing.py` and adds one test, a 10 percent discount on a known user. It adds no test for these cases:
  - an out-of-range percent (C1)
  - an exhausted or unknown code (H3, M4)
  - the support not-found path (H1)
  - mixed-case emails (C2)
  - the migration (C3)
- **Evidence:** the suite on the branch is four tests, and all four pass. Each defect in C1, C2, H1, and H3 passes the suite. `tests/test_billing.py` is unchanged.
- **Verdict:** CONFIRMED. An independent verifier confirmed it against `CLAUDE.md` and `docs/testing.md`.
- **Why High:** The three top production risks have no test. These risks are wrong charge amounts, lost customers through email lookups, and irreversible data loss.
- **Fix:** Add failure-path tests for each case above before merge.
- **Cites:** `CLAUDE.md` ("Every change to app/billing.py requires failure-path tests"). `docs/testing.md` ("invalid input, not-found, limit exceeded").

### Medium (worth fixing now; acceptable as a follow-up)

#### M1: The PR bundles five changes that the discount feature does not need
- **Locator:** `scope: PR`
- **What:** These changes ride along with the discount feature:
  - the `normalize_email` removal (C2), which the description does not mention
  - the new `source` field on users (`app/api.py:7-9`, `app/users.py:16`), which the description does not mention
  - `api_apply_credit` (H2), which the description does not mention
  - the plan-to-tier migration (C3), which the description lists but does not tie to discounts
  - the new `None` return of `find_user_by_email` (H1)
- **Evidence:** the description justifies the last change as one that "simplifies the new discount code paths". No discount code path calls `find_user_by_email`. Only `billing.charge` calls it, as before. Nothing in the PR reads `tier`.
- **Verdict:** CONFIRMED. `git grep` on the branch shows the callers, and an independent verifier confirmed the scope claim.
- **Why Medium:** The extras cause C2, C3, H1, and H2. A revert of the discount feature also reverts them, and a revert cannot undo the migration.
- **Fix:** Split the PR. Keep the discount feature here. Move each extra into its own PR with its own description.

#### M2: Users created after migration 002 still get plan and never get tier
- **Locator:** `app/users.py:15`
- **What:** `create_user` still writes `"plan": "free"` and writes no `tier`. After `up()` runs, old users have only `tier` and new users have only `plan`.
- **Evidence:** after `up()`, the probe created a user. The user had `plan = free` and `tier = None`. `tests/test_users.py:13` still asserts `plan`.
- **Verdict:** CONFIRMED. The probe reproduced it, and an independent verifier confirmed it from the code.
- **Why Medium:** Any later reader of `tier` gets `None` for every new user. No code reads `tier` today, so nothing breaks yet.
- **Fix:** Resolve this in the migration PR from M1. `create_user` must write the field that the current schema expects.

#### M3: Creating a code that exists resets its usage count
- **Locator:** `app/api.py:26`
- **What:** `STORE.discounts[code] = row` overwrites the existing row and sets `uses` to 0.
- **Evidence:** after one redemption of `ONCE`, the probe created `ONCE` again. The row showed `uses: 0` and could be redeemed again.
- **Verdict:** CONFIRMED. The probe reproduced it, and an independent verifier confirmed it from the code.
- **Why Medium:** A repeat create, for example a support retry, revives an exhausted code without notice. The impact grows once H3 is fixed, because `uses` then gates the charge.
- **Fix:** Reject a create when the code exists, or require an explicit update path.

#### M4: An unknown discount code is ignored and the customer pays full price
- **Locator:** `app/billing.py:19-22`
- **What:** When `STORE.discounts.get(discount_code)` returns `None`, `charge` continues with no discount and no error.
- **Evidence:** a charge of `"10.00"` with code `TYPO` returned `amount: 1000, total: 1050`.
- **Verdict:** CONFIRMED. The probe reproduced it, and two separate agents found it independently.
- **Why Medium:** The customer expects a discount and gets charged in full. Support then has to issue a refund by hand.
- **Fix:** Raise `BillingError("unknown discount code")` before the charge is recorded. Add a test.

### Low (defer)
- **L1** [`app/api.py:22,24`] `int(payload["percent"])` turns `29.9` into `29` without notice and raises an uncaught `ValueError` for `"12.5"`. Accept integers only and return a clear error.
- **L2** [`app/api.py:7-9`] `source` comes from the payload and is stored on the user with no allowlist.

## Questions
- **Q1** [`app/billing.py:11`] Where is the FIN-88 sign-off recorded? Must existing codes above 30 percent stop working, or only new ones?
- **Q2** [`scope: PR`] SUPPORT-311 was not available to this review. Does it ask for a redeem endpoint that is separate from charge, or for redemption inside charge?
- **Q3** [`app/api.py:18,42`] Who may call `api_create_discount` and `api_apply_credit`? The API layer has no authorization check on any endpoint, on `main` or on this branch.
- **Q4** [`migrations/002_drop_plan.py:7`] Which code writes `plan = "legacy"`? On `main`, `create_user` writes only `"free"`.

## Suggestions

#### S1: Collapse the discount engine into one function until a second strategy exists
- **Locator:** `app/discount_engine/__init__.py:1-35`
- **What:** Nothing reads `STRATEGY_REGISTRY`, and nothing calls `get_strategy` or reads `DISCOUNT_ENGINE_BACKEND`. Only the `@register("percent")` decorator uses `register`. `billing` imports `PercentDiscount` directly and skips the engine. `validate_percent` reaches back into `billing` for the cap. Replace the package with one integer function next to `MAX_DISCOUNT_PERCENT`.
- **Why it would be better:** It removes an environment variable that does nothing and an extension point that no ticket schedules. It also removes the back-reference from the engine to `billing`. Constraints checked: the description names fixed-amount and BOGO as "upcoming" but cites no ticket. The single function keeps §2 integer arithmetic.
- **Sketch:** `def apply_percent(amount_cents, percent): return amount_cents - amount_cents * percent // 100`

#### S2: Compute tax with integer arithmetic
- **Locator:** `app/billing.py:23` (line unchanged, function touched)
- **What:** `int(amount * (1 + TAX_RATE_BP / 10_000))` uses a float in a money path. Replace it with `amount * (10_000 + TAX_RATE_BP) // 10_000`.
- **Why it would be better:** It follows `docs/invariants.md §2` by construction. A scan of amounts from 0 to 199,999 cents found no difference today, so this is not an Issue.

## Gaps
- The charge entry does not record which discount code it used. Refunds and reconciliation cannot trace a discount back to its code.
- The description has no manual test plan.

## Known limitations
- The check and the increment of `uses` are two steps, so two concurrent redemptions can both pass the check. The store is in memory and single-process, so this is acceptable here. Fix it when the store moves to a database, with an atomic conditional update.

## What was done well
- [`app/discount_engine/percent.py:10`] The discount uses integer floor division on cents. No float enters the discount step, as `docs/invariants.md §2` requires.
- [`app/billing.py:15-17`] `charge` checks the new `None` return before use, so billing keeps its "unknown user" error.
- [`app/discount_engine/__init__.py:26-30`] `validate_percent` states the correct range and reads the cap from the single source of finance policy. The fix for C1 only has to call it.
- [`tests/test_discounts.py:9-11`] The new test clears users, discounts, and charges in `setUp`, so it does not depend on test order.

## Verified
- **Existing tests:** all four tests pass on the branch with `python3 -m unittest discover tests -v`.
- **Load-bearing assumption, Python semantics:** `//` rounds toward negative infinity and `int()` truncates toward zero, per the Python language reference. For positive amounts the customer gets the floor of the discount. This is an explicit integer rounding choice and is fine.
- **Float tax:** a scan of `int(a * 1.05)` against `a * 10500 // 10000` for 0 to 199,999 cents found zero differences. S2 stays a Suggestion.
- **Import cycle, REFUTED as a defect:** `validate_percent` imports `billing` inside the function body, so no cycle exists at import time. Both modules import without error, and `validate_percent(31)` returns `False`. S1 keeps the back-reference only as a layering note.
- **Privacy:** no new code stores or logs a raw email outside the users table. Charges carry `user_id`, as `CLAUDE.md` requires.
- **Dependencies:** the PR adds no third-party package.
- **Sibling branch:** `feature/audit-log` merges into this branch without conflict (`git merge-tree`). The merged `create_user` still lacks `normalize_email`, so C2 survives the merge.
- **Independent verification:** a host-style defect review ran in a separate agent without this review's notes. It reproduced C1, C2, H1, H2, H3, and M4. A second verifier tried to refute C3, H2, H4, M1, M2, M3, M4, and S1 from the code and docs. It confirmed each one and refuted only the import-cycle claim above.
- **Gap sweep:** one more pass over the enclosing functions found the missing code on the charge entry (now a Gap) and nothing else.

## Not reviewed
- SUPPORT-311 and FIN-88 are not in the repository, so this review did not reconcile the PR with them (Q1, Q2).
- CI: the repository has no remote and no PR, so `gh pr checks` does not apply.
- The repository has no `docs/architecture.md`, `docs/security.md`, or `docs/privacy.md`. Security findings are judged against OWASP A01 (broken access control). Privacy is judged against the `CLAUDE.md` email rule.
- The `feature/audit-log` branch was checked only for merge conflicts with this PR.
- Concurrency under a real database was not tested. See Known limitations.

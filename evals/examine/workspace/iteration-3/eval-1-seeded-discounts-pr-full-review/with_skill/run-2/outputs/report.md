# Examine: feat(discounts): Add discount codes with API validation (branch `feature/discounts` vs `main`, full mode)

## Headline

Hold. The PR does not validate discount percent, so any percent is accepted, and it breaks the support console, the email invariant, and the migration policy. Fix C1 to C4 and H1 to H3 before merge, then re-review.

Mode is full, chosen because the branch ships a migration and touches payment code. Target is `git diff main...HEAD` at `16523ff`, 8 files, with a clean working tree.

## Approach fit

APPROACH DISPUTED in part. The discount feature itself matches the obvious approach: store a code, apply it in `billing.charge`, validate at the API. Five changes go beyond that approach and I found no constraint for any of them in the repo, its history, or its docs.

- The discount cap drops from 50 to 30 (`FIN-88`, not in the repo).
- Migration 002 drops the `plan` field.
- `db.find_user_by_email` changes its contract from raising to returning `None`.
- `api_apply_credit` adds a second money-moving endpoint.
- `create_user` gains a `source` field and loses email normalization.

The line findings on the discount path stand on their own. The findings on the five extra changes are provisional on the author's answers to Q1 to Q4. The simplest fix for most of them is to move them out of this PR.

## Issues

### Critical (must fix before merge)

#### C1: Discount percent is never validated, so any percent is accepted
- **Locator:** `flow: app/api.py:18-27 (api_create_discount) → app/billing.py:19-22 → app/discount_engine/percent.py:9`
- **Changed anchor:** `app/api.py:18-27`, `app/discount_engine/__init__.py:26-30`
- **What:** `api_create_discount` stores `int(payload["percent"])` with no range check. `validate_percent` exists in the engine package but nothing calls it. `MAX_DISCOUNT_PERCENT` is therefore dead. The PR title and description both claim "validated at the API boundary per §4".
- **Evidence:** probe in a detached worktree. `percent=500` on a 10.00 charge produced `amount=-4000, total=-4200`. `percent=-20` produced `amount=1200`. `percent=90` and `percent=0` were accepted. `grep -rn validate_percent app tests` shows only the definition.
- **Verdict:** CONFIRMED. Independent verifier read the diff and ran the same inputs.
- **Why Critical:** Negative and over-cap charges on the money path. The feature's one stated safety property is absent, and §4 is a hard invariant.
- **Fix:** In `api_create_discount`, call `validate_percent` and raise a client error when it returns `False`. Move `validate_percent` next to `MAX_DISCOUNT_PERCENT` in `billing.py` to remove the lazy circular import. Add tests for 0, 31, 100, 500, and -1.
- **Cites:** `docs/invariants.md §4 (Percentage adjustments)`, `CLAUDE.md` ("Reuse helpers ... before writing new parsing or validation code").

#### C2: Support-console lookup crashes on every unknown email
- **Locator:** `flow: app/support.py:7-10 → app/db.py:14-18`
- **Changed anchor:** `app/db.py:14-18` (`raise NotFound(email)` became `return None`)
- **What:** `find_user_by_email` now returns `None`. `support.lookup` still catches `NotFound`, which is never raised, and then indexes `u["id"]` on `None`. The description says "billing was updated to match" and omits `support.py`.
- **Evidence:** probe: `support.lookup("nobody@x.y")` raised `TypeError: 'NoneType' object is not subscriptable`. On `main` it returned `{"found": False}`. `grep -rn find_user_by_email app` shows two callers and only one was updated.
- **Verdict:** CONFIRMED. Independent verifier traced both callers and reproduced the crash.
- **Why Critical:** A regression on an unchanged, shipped surface. Every not-found lookup in the support console fails on deploy. No test covers `support.py`.
- **Fix:** Either keep the `NotFound` contract and revert `db.py`, or update `support.lookup` to check for `None`. Add a not-found test for `support.lookup`. The description claim "simplifies the new discount code paths" names no code path that needed the change.
- **Cites:** `docs/testing.md` ("lookup paths require failure-path tests ... not-found").

#### C3: Email normalization dropped at the only write path
- **Locator:** `app/users.py:12`
- **Changed anchor:** `app/users.py:5,12` (`normalize_email(email)` replaced by `email.strip()`)
- **What:** `create_user` no longer lowercases the email. §1 states that all lookups assume canonical form and that one non-canonical write breaks every reader. The change is not mentioned in the description.
- **Evidence:** probe: a user created as `"  Alice@Example.COM "` is stored as `'Alice@Example.COM'`. `billing.charge("alice@example.com", ...)` then raised `BillingError: unknown user`. The `normalize_email` import was removed, and no other write path re-establishes the invariant.
- **Verdict:** CONFIRMED. Independent verifier reproduced the failed charge and checked every write path.
- **Why Critical:** Violates a documented critical invariant and corrupts data. Every user created with a capital letter after deploy becomes unchargeable and unfindable in support. Existing canonical rows are unaffected, so the damage is silent and grows daily.
- **Fix:** Restore `email = normalize_email(email)` and the import. Add a mixed-case create-then-charge test.
- **Cites:** `docs/invariants.md §1 (Canonical emails)`, `CLAUDE.md` ("Reuse helpers in app/util.py").

#### C4: Migration 002 is destructive, forward-only, and the code never writes `tier`
- **Locator:** `flow: migrations/002_drop_plan.py:4-7 → app/users.py:14 → tests/test_users.py:13`
- **What:** `up()` pops `plan` from every user and writes `tier`. There is no `down()`. `create_user` still writes `plan: "free"` and never writes `tier`. No code in `app/` reads `tier`. The mapping `"grandfathered" if plan == "legacy"` tests a value no code ever wrote. The migration is unrelated to discounts.
- **Evidence:** probe: after `up()`, the existing user is `{..., 'tier': 'standard'}` with no `plan`. A user created afterwards is `{'plan': 'free', 'tier': None}`. `hasattr(m, "down")` is `False`. `grep -rn tier app` returns nothing.
- **Verdict:** CONFIRMED. Independent verifier ran the migration and checked for `down()`, readers, and writers.
- **Why Critical:** Irreversible data loss on deploy and a data model split in two. The original `plan` values are discarded, so a code rollback cannot restore them. §3 forbids all three properties: destructive in the first release, no dual-read, no `down()`.
- **Fix:** Remove the migration from this PR. If `tier` is wanted, ship it per §3: add `tier` additively with a `down()`, dual-write in `create_user`, release, then drop `plan` later. Until then `tests/test_users.py:13` keeps asserting `plan == "free"`, which is correct for the code but contradicts the migration.
- **Cites:** `docs/invariants.md §3 (Reversible migrations)`.

### High (should fix before merge)

#### H1: `api_redeem` reports success for unknown codes and `max_uses` is never enforced where money moves
- **Locator:** `flow: app/api.py:30-39 (api_redeem) → app/billing.py:19-22 (charge)`
- **What:** The condition `row is None or row["uses"] < row["max_uses"]` returns `{"redeemed": True}` when the code does not exist. The resulting `KeyError` on `STORE.discounts[code]` is swallowed by `except Exception: pass`. Separately, `billing.charge` applies the discount whenever the row exists and never reads or increments `uses`. Nothing calls `api_redeem` from the charge path.
- **Evidence:** probe: `api_redeem({"code": "NOPE"})` returned `{'redeemed': True}`. A code with the default `max_uses=1` was applied to three consecutive charges, all at 900 cents, while `uses` stayed at 1.
- **Verdict:** CONFIRMED. Independent verifier reproduced both behaviors.
- **Why High:** Unlimited redemption of a single-use code is direct revenue loss, and the redeem endpoint lies to its caller. The bare `except` hides the defect that would have surfaced it. The two steps are also never atomic, so a redeem followed by a failed charge burns a use for nothing.
- **Fix:** Change the condition to `row is not None and row["uses"] < row["max_uses"]`, drop the `try/except`, and enforce and increment `uses` inside `charge` under the same operation that records the entry. Decide whether `api_redeem` should exist at all, since the charge path is where redemption happens.
- **Cites:** `docs/testing.md` ("limit exceeded" failure paths).

#### H2: `api_apply_credit` bypasses the negative-amount guard and attaches money to no user
- **Locator:** `app/api.py:42-50`
- **What:** The endpoint strips a leading `-` and negates the parsed value, which defeats the one rule `parse_money` enforces. It records a charge with `user_id=None`, no tax, and no bound on magnitude. The description does not mention it, and it is not a discount.
- **Evidence:** probe: `api_apply_credit({"amount": "-999999.99"})` appended `{'user_id': None, 'amount': -99999999, 'total': -99999999}` to `STORE.charges`. `app/util.py:11-13` documents that negative input is rejected and that "adjustments are modeled explicitly".
- **Verdict:** CONFIRMED. Independent verifier reproduced the entry and read the `parse_money` docstring.
- **Why High:** A new unauthenticated money-moving path with no owner on the ledger row, in a PR nobody asked to add it to. No project security doc exists, so I judge this against OWASP A04 (Insecure Design) and A01 (Broken Access Control) as the applicable standard.
- **Fix:** Remove it from this PR. If credits are wanted, model them explicitly as the `parse_money` docstring says. Attach them to a user id, cap the magnitude, and ship them in their own PR with failure-path tests.
- **Cites:** `app/util.py:11-13` (the guard's own docstring). No project security rule, judged against OWASP A01 and A04.

#### H3: One happy-path test for a PR that changes billing and adds four money or lookup paths
- **Locator:** `tests/test_discounts.py:14-19`
- **What:** The PR changes `app/billing.py` and ships one test, 10% off 10.00 equals 900. CLAUDE.md requires failure-path tests for every change to `billing.py`. `docs/testing.md` requires invalid-input, not-found, and limit-exceeded tests on money and lookup paths. The description names no manual test steps.
- **Evidence:** `python3 -m unittest discover tests -v` on the branch: 4 tests, OK. Each absent test below would have caught a finding above.
  - percent over cap or negative (C1)
  - `support.lookup` not-found (C2)
  - mixed-case email (C3)
  - migration `up()` and `down()` (C4)
  - `max_uses` exhaustion and unknown-code redeem (H1)
  - negative credit (H2)
  - unknown code at charge time (M1)
- **Verdict:** CONFIRMED. Independent verifier listed the required paths against the test files.
- **Why High:** Every top-3 production risk named under Verified is uncovered. The suite is green while C1 to C4 ship.
- **Fix:** Add the failure-path tests listed in Evidence. `tests/` mirrors `app/`, so `tests/test_support.py` and `tests/test_api.py` are the expected homes.
- **Cites:** `CLAUDE.md` ("Every change to app/billing.py requires failure-path tests"), `docs/testing.md` (second bullet).

### Medium (worth fixing now; acceptable as a follow-up)

#### M1: An unknown discount code is silently ignored and the customer pays full price
- **Locator:** `app/billing.py:19-22`
- **What:** `row = STORE.discounts.get(discount_code); if row:` falls through on a mistyped code. The charge succeeds at full price and the returned entry has no field that says whether a discount applied. The same function raises `BillingError` for an unknown user.
- **Evidence:** probe: `api_charge({... "discount_code": "TYPO"})` returned `{'user_id': 4, 'amount': 1000, 'total': 1050}` with no error.
- **Verdict:** CONFIRMED. Independent verifier showed the entry for a mistyped code is identical to the entry for no code. This may be an intended product choice, but the description does not say so.
- **Why Medium:** Wrong behavior on a reachable edge path that produces support tickets and refunds. Not Critical because money moves in the customer's disfavor only by the discount amount.
- **Fix:** Raise `BillingError("unknown discount code")`, or return `discount_code` and `discount_cents` on the entry so callers can detect the miss. Add the not-found test either way.
- **Cites:** `docs/testing.md` ("not-found" failure paths).

#### M2: The discount engine is an abstraction nothing uses, with a live config knob that does nothing
- **Locator:** `arch: app/discount_engine/`
- **What:** The package adds an ABC, a registry decorator, `get_strategy()`, and an env var `DISCOUNT_ENGINE_BACKEND`. `billing.py:2` imports `PercentDiscount` directly and never calls `get_strategy()`. `validate_percent` lives in the engine and lazily imports `billing` to dodge a circular import. The only justification is "upcoming fixed-amount and BOGO discounts" in the description. I found no ticket, spec, or history for either.
- **Evidence:** `grep -rn get_strategy app` shows only the definition. `DISCOUNT_ENGINE_BACKEND=bogo` makes `get_strategy()` raise `KeyError: 'bogo'`, and nothing else changes. `git grep -i "bogo\|fixed-amount" $(git rev-list --all)` matches only the engine's own docstring. The percent path is one line: `amount - (amount * pct) // 100`.
- **Verdict:** CONFIRMED. Independent verifier searched every ref, test, and config file for a scheduled second strategy and found only the engine's own docstring.
- **Why Medium:** The module docstring tells an operator that an env var selects the backend. It does not. That is a maintenance trap with a named cost, and the registry pattern is what the next discount PR will copy. The knob is also at the wrong altitude. A discount row knows its own kind, and a process-wide env var cannot select a strategy per row. Walked against the constraints from the description and `docs/invariants.md`. None requires the abstraction.
- **Fix:** Collapse to a `percent_off(amount_cents, percent)` function in `billing.py` beside `MAX_DISCOUNT_PERCENT` and `validate_percent`. Add the ABC when the second strategy lands.

#### M3: The cap change from 50 to 30 is a finance policy change bundled into a feature PR
- **Locator:** `app/billing.py:11`
- **What:** `MAX_DISCOUNT_PERCENT` drops from 50 to 30 with the comment "per finance policy FIN-88". Nothing in the repo or its history references `FIN-88`. The constant is dead in this PR anyway (C1), so the change has no runtime effect today, but it will the moment C1 is fixed.
- **Evidence:** `git grep -i FIN-88 $(git rev-list --all)` matches only this line. `git log -S MAX_DISCOUNT_PERCENT` shows the value changed only in this commit.
- **Verdict:** CONFIRMED that the constraint is not in the repo. Whether finance signed off is Q1.
- **Why Medium:** The people who own the policy cannot review a change hidden in a feature PR. The change also cannot be reverted independently of the feature.
- **Fix:** Split it into its own one-line PR that links `FIN-88`, or paste the sign-off into this PR's description.

### Low (defer)
- **L1** [`app/api.py:2`] The API layer now imports and writes `STORE` directly, where `main` routed every write through `users` and `billing`. No architecture doc exists, so this stays Low.
- **L2** [`app/api.py:22`] `int(payload["percent"])` raises an unhandled `ValueError` on `"10.5"`. Validate and return a client error.
- **L3** [`app/api.py:19,26`] Discount codes are not normalized and an existing code is silently overwritten with `uses` reset to 0.
- **L4** [`app/db.py:4`] `NotFound` is now dead code in `db.py` and only `support.py` imports it. Resolve with C2.
- **L5** [`app/billing.py:14`] `discount_code: str = None` should be `Optional[str]` or `str | None`.

## Questions

- **Q1** [`app/billing.py:11`] Where is the `FIN-88` sign-off recorded, and did finance intend it to land with this feature?
- **Q2** [`migrations/002_drop_plan.py`] Who reads `tier`, and what wrote `plan == "legacy"`? Neither appears in the repo.
- **Q3** [`app/users.py:9`] What is `source` for, and should it be in this PR?
- **Q4** [`app/db.py:14`] Which "new discount code path" needed `find_user_by_email` to return `None`? `billing.charge` is the only caller in the diff.
- **Q5** [`app/billing.py:19-23`] Is tax meant to apply to the discounted amount? The code does that, and the description does not say.
- **Q6** [`app/api.py:24`] Is `max_uses=1` the intended default for a marketing code?

## Suggestions

#### S1: Replace the float tax step with integer arithmetic while the function is open
- **Locator:** `app/billing.py:23`
- **What:** `int(amount * (1 + TAX_RATE_BP / 10_000))` is pre-existing and uses a float in a money path. Discounted amounts now flow through it.
- **Why it would be better:** §2 forbids floats in money paths. I measured no divergence from integer math for 1 to 199,999 cents at 500 bp, so this is compliance, not a live bug.
- **Sketch:** `total = amount * (10_000 + TAX_RATE_BP) // 10_000`

#### S2: Document the rounding direction of the discount
- **Locator:** `app/discount_engine/percent.py:9`
- **What:** `amount - (amount * pct) // 100` floors the discount, so the customer pays the ceiling. 999 cents at 33% gives 670.
- **Why it would be better:** §2 says rounding decisions are made explicitly. One comment and one test fix that.

## Gaps
- The description claims "fixes SUPPORT-311" and I could not read the ticket.
- `tests/test_users.py:13` asserts `plan == "free"`, which the migration says is legacy. Resolve with C4.

## Known limitations
- The verifiers for M1 and M2 ran against a sibling checkout of the same fixture content, not my detached worktree. My worktree vanished mid-review, most likely removed by another process in the shared scratch directory. My own probes on the reviewed checkout gave the same results, so both findings stand.

## What was done well
- [`app/discount_engine/percent.py:9`] Integer-only discount arithmetic. It respects §2 where it would have been easy to write `amount * (1 - pct / 100)`.
- [`app/billing.py:17`] `parse_money` is reused rather than re-parsed, per CLAUDE.md.
- [`tests/test_discounts.py:8-11`] The test resets all three store collections in `setUp`, matching the existing test style.
- [`app/billing.py:19`] The `if discount_code:` guard keeps the existing `charge` signature backward-compatible for `test_billing.py` and any other caller.

## Verified
- The problem is real on `main`. `STORE.discounts` exists at `app/db.py:11` and nothing reads or writes it. There is no discount parameter on `charge`.
- Before reading the diff I sketched three approaches. (1) Validate percent in `api_create_discount`, store the row, apply in `charge` with integer math, test failure paths. (2) The same with a small dataclass for the discount. (3) The same with the create call in `support.py`, since the description says support creates codes. The discount path matches sketch 1. The five extra changes match none, and the hunt for constraints (description, `docs/`, `git log --all`, `git grep` over all refs) found none.
- Top three production risks: uncapped or negative discounts (C1, no test), support console crash on not-found (C2, no test), unchargeable mixed-case users (C3, no test).
- Load-bearing assumption checked: `PercentDiscount.apply` with `//` on positive ints floors toward zero, confirmed by probe (S2). The float tax step was measured against integer math over 199,999 values with no divergence (S1).
- The branch test suite passes: 4 tests, OK, run in a detached worktree.
- Dependencies: none added or changed.
- Privacy: `source` is not personal data. Charges reference users by id. No raw email is stored outside the users table. CLAUDE.md's email rule holds.
- Reversibility: the migration is irreversible (C4). Everything else is a code revert.
- The sibling branch `feature/audit-log` also touches `app/users.py` and `app/db.py`. Not in scope, but expect a merge conflict.
- The host's built-in review ran as a candidate source in a subagent. Its findings were deduplicated into the list above.

## Not reviewed
- The ticket SUPPORT-311 and policy FIN-88. Neither is in the repo.
- No `docs/architecture.md`, `docs/security.md`, or `docs/privacy.md` exists. The architecture finding is therefore Low (L1), and the security finding is judged against OWASP (H2).
- CI. There is no remote and no checks to read.
- The migration runner. Nothing in the repo invokes `migrations/*.py`, so I ran `up()` by hand.

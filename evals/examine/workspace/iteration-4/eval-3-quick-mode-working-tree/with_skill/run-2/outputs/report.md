# Examine: discount codes with API validation (branch `feature/discounts`)

## Headline
Hold. The branch breaks three documented invariants, crashes the support lookup, and lets single-use codes repeat.

## Target and mode
- **Target:** branch `feature/discounts` at `520549a`, diffed from the merge-base with `main` (`5f1e0b7`). The branch has no upstream.
- **Working tree:** clean (`git status --porcelain` is empty). The review covers the one commit only.
- **Mode:** quick, because you asked for it.

The skill defaults to full mode for migrations and payments. This branch touches both. Run a full pass before merge, after the fixes below.

## Approach fit
The change diverges from the obvious approach for a stated constraint. The commit message says fixed-amount and BOGO discounts are coming, which explains `app/discount_engine/`. The charge path does not use the registry yet. `app/billing.py:2` imports `PercentDiscount` directly. I could not read SUPPORT-311 or FIN-88.

My sketches before I read the diff:
1. Add an optional `discount_code` to `billing.charge`. Validate the percent at the API against `MAX_DISCOUNT_PERCENT`. Apply it with integer math and count the use in the same step.
2. Do the same with a small `apply_discount` helper in `billing.py` and no new package.
3. Record the discount as a separate adjustment line on the charge entry.

## Issues

### Critical (must fix before merge)

#### C1: No code validates the discount percent, so a code can produce a negative charge
- **Locator:** `app/api.py:22`
- **What:** `api_create_discount` stores `int(payload["percent"])` with no range check. `validate_percent` exists at `app/discount_engine/__init__.py:26`, but nothing calls it. The commit message claims validation at the API boundary.
- **Evidence:** a probe charged 10.00 with each percent. The results follow.
  - 31 gives an amount of 690. This is above the new 30% cap.
  - 150 gives an amount of -500 and a total of -525.
  - -20 gives an amount of 1200. The "discount" raises the price.
- **Verdict:** CONFIRMED. I ran the probe in a detached worktree. `git grep validate_percent` finds only the definition.
- **Why Critical:** The change breaks a documented invariant. It also lets one wrong code send money in the wrong direction on every charge.
- **Fix:** Call `validate_percent` in `api_create_discount` and reject the payload when it returns False. Add a test for 0, 31, 150, and -20.
- **Cites:** `docs/invariants.md §4`

#### C2: Migration 002 destroys plan data, has no `down()`, and new users still get `plan`
- **Locator:** `migrations/002_drop_plan.py:4-7`
- **What:** `up()` pops `plan` and maps every value except `"legacy"` to `"standard"`. The file has no `down()`. `app/users.py:14` still writes `"plan": "free"` and no `tier`.
- **Evidence:** a probe ran `up()` on a `free` user and a `pro` user, then created a new user.
  - Both existing users end with `tier: standard` and no `plan`. The `pro` value is gone.
  - The new user has `plan: free` and no `tier`.
- **Verdict:** CONFIRMED. I ran the probe in a detached worktree.
- **Why Critical:** A rollback cannot restore `plan`. Paid plans collapse into one tier. The store then holds two schemas at once.
- **Fix:** Make it additive. Add `tier` with a full mapping and keep `plan`. Write `tier` in `create_user`. Ship a `down()`. Drop `plan` in a later release after a dual-read release.
- **Cites:** `docs/invariants.md §3`

#### C3: `create_user` no longer stores canonical emails
- **Locator:** `app/users.py:12`
- **What:** The change removes `normalize_email` and keeps only `strip()`. The commit message does not mention this change. Lookups compare exact strings.
- **Evidence:** a probe created `"  Alice@Example.COM "`. The store holds `'Alice@Example.COM'`. A charge for `alice@example.com` raises `BillingError: unknown user`. A second signup with the lowercase form creates a duplicate user.
- **Verdict:** CONFIRMED. I ran the probe in a detached worktree.
- **Why Critical:** The invariant says that "a non-canonical write breaks every reader". Charges fail, and duplicate accounts appear for one person.
- **Fix:** Restore `email = normalize_email(email)` in `create_user`.
- **Cites:** `docs/invariants.md §1`, `CLAUDE.md` (reuse helpers in `app/util.py`)

### High (should fix before merge)

#### H1: The support lookup crashes on an unknown email
- **Locator:** `flow: app/db.py:18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:18` (`return None` replaces `raise NotFound`)
- **What:** `find_user_by_email` now returns `None`. `support.lookup` still catches `NotFound`, which never comes. It then subscripts `None`.
- **Evidence:** `support.lookup("ghost@x.y")` raises `TypeError: 'NoneType' object is not subscriptable`. Before the change it returned `{"found": False}`.
- **Verdict:** CONFIRMED. I ran the probe in a detached worktree. `git grep find_user_by_email` finds two callers. The commit updated only `billing.py`.
- **Why High:** Each support search for an unknown customer fails with an error instead of "not found".
- **Fix:** Check for `None` in `support.lookup`. Alternatively, keep the raising contract and add a separate `get_user_by_email` that returns `None`.

#### H2: A charge ignores `uses` and `max_uses`, so a single-use code works without limit
- **Locator:** `app/billing.py:19-22`
- **What:** `charge` applies the discount whenever the code exists. It never reads or increments `uses`. The only code that increments it is `api_redeem`, and the charge path does not call `api_redeem`.
- **Evidence:** a probe created `ONCE` with `max_uses: 1` and charged three times. All three amounts were 900, and `uses` stayed 0.
- **Verdict:** CONFIRMED. I ran the probe in a detached worktree.
- **Why High:** The store records wrong amounts on a reachable path. One leaked code discounts every later charge.
- **Fix:** In `charge`, reject or ignore the code when `uses >= max_uses`. Increment `uses` in the same step that appends the charge.

#### H3: No test covers the top three production risks
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The branch adds one happy-path test. It changes `app/billing.py`, a money path, and a lookup path. The top three risks and their tests follow.
  - Wrong discounted amounts (C1, H2): no test for a bad percent, an unknown code, or an exhausted code.
  - Broken email lookups (C3, H1): no test for a mixed-case email or for a support lookup that finds nothing.
  - Migration 002 data mapping (C2): no test.
- **Verdict:** CONFIRMED. All four existing tests pass on the branch. Each defect above passes them too.
- **Why High:** Each of the three risks is uncovered, and each one has a confirmed defect today.
- **Fix:** Add the failure-path tests listed above, one per bullet.
- **Cites:** `docs/testing.md` (failure-path tests for money and lookup paths), `CLAUDE.md` (failure-path tests for every change to `app/billing.py`)

### Medium (fix now or as a follow-up)

#### M1: `api_redeem` reports success for a code that does not exist
- **Locator:** `app/api.py:33-38`
- **What:** The condition `row is None or row["uses"] < row["max_uses"]` sends unknown codes into the increment branch. The increment raises `KeyError`. The bare `except` swallows it, and the function returns `{"redeemed": True}`.
- **Evidence:** `api_redeem({"code": "NOPE"})` returns `{'redeemed': True}`. The store has no `NOPE`.
- **Verdict:** CONFIRMED. I ran the probe in a detached worktree.
- **Why Medium:** A caller that trusts the response grants a discount for any string. The impact is lower than H2 because the charge path does not call this function.
- **Fix:** Return `{"redeemed": False}` when `row is None`. Remove the `try/except` so real errors surface.

#### M2: An undisclosed credit endpoint writes negative ledger entries that belong to no user
- **Locator:** `app/api.py:42-50`
- **What:** `api_apply_credit` is not in the commit message. It strips a leading `-` to get past the non-negative check in `parse_money`. It appends a charge with `user_id: None`.
- **Evidence:** `api_apply_credit({"amount": "-500.00"})` stores `{'user_id': None, 'amount': -50000, 'total': -50000}`.
- **Verdict:** CONFIRMED. I ran the probe in a detached worktree.
- **Why Medium:** The ledger gets money that no one can reconcile to a customer. The docstring of `parse_money` says that adjustments "are modeled explicitly", and this entry is not.
- **Fix:** Move the endpoint to its own PR with a user id, an explicit credit entry type, and tests. Otherwise remove it from this branch.
- **Cites:** `app/util.py:9-10` (`parse_money` contract)

## Questions
- **Q1** [`app/billing.py:19-22`] A misspelled or unknown code charges full price with no error. Is the silent fallback what support and customers expect?
- **Q2** [`app/api.py:26`] `api_create_discount` overwrites an existing code and resets `uses` to 0. Should a second create with the same code fail?
- **Q3** [`app/api.py:8`] What consumes the new `source` field on users? The commit message does not mention it.

## What was done well
- [`app/discount_engine/percent.py:10`] The discount uses integer floor division on cents. This follows `docs/invariants.md §2`.
- [`app/billing.py:15-17`] `charge` adapts to the new `None` contract and keeps `BillingError` for unknown users. The existing test `test_charge_unknown_user_fails` still passes.
- [commit `520549a`] The commit message names the non-obvious decisions: the FIN-88 cap change, the migration, and the lookup contract change. This made the review faster.
- [`tests/test_discounts.py:8-11`] `setUp` clears all three stores, so the tests do not leak state.

## Verified
- **The problem is real.** At the merge-base, `Store.discounts` exists but no code reads or writes it.
- **The cap change matches the message.** `MAX_DISCOUNT_PERCENT` changes from 50 to 30. No codes existed before this branch, so no stored code exceeds the new cap.
- **The test suite passes.** `python3 -m unittest discover tests -v` runs four tests, and all pass.
- **The tax line has no observed rounding error.** `app/billing.py:23` uses a float, which `docs/invariants.md §2` forbids. This line predates the branch. A probe compared it with integer math for every amount from 0 to 2000.00 and found no difference. A follow-up can still convert it to integer math.
- **Verification ran in a single context.** No independent subagent checked the candidates. Instead, each verdict above rests on an executable probe in a detached worktree.

## Not reviewed
Quick mode skipped these parts:
- Axes 5e to 5h: architecture, conventions, security, and privacy. Auth on the new endpoints falls here. No endpoint in `app/api.py` checks auth, before or after this branch.
- Axes 5j to 5l: load-bearing assumptions, reversibility, and dependencies. C2 came from the gap sweep, not from a reversibility pass.
- The Occam pass. The unused `STRATEGY_REGISTRY`, `get_strategy`, and `DISCOUNT_ENGINE_BACKEND` are a likely candidate for it.
- Host reviewers.
- CI. The branch has no PR and no upstream.
- The tickets SUPPORT-311 and FIN-88, which I could not access.

# Examine: Add discount codes with API validation (feature/discounts vs main)

## Headline

Hold. The discount path does not enforce its cap or its use limit, and the migration destroys data with no `down()`.

The branch also ships three changes the commit message does not mention. These are a credit endpoint, the removal of email normalization, and a new `source` field.

Mode: **quick**, as you asked. This diff touches payments and a migration. Without your choice, the skill would pick full mode. Run `/examine full` before merge.

| Item | Value |
|---|---|
| Base | `main` at `5f1e0b7` (merge-base) |
| Head | `feature/discounts` at `520549a` |
| Working tree | clean, so the review covers the commit range only |
| Files | 8 changed, 129 insertions, 14 deletions |
| Tests | 4 of 4 pass on the head |

## Approach fit

The discount path matches the obvious approach: a validated create endpoint, then lookup, apply, and count at charge time. The parts beyond that sketch have no constraint in the repo. M3 covers them.

## Issues

### Critical (must fix before merge)

#### C1: Migration 002 drops `plan` in one step, with no `down()` and no dual-read release
- **Locator:** `migrations/002_drop_plan.py:4-7`
- **What:** `up()` pops `plan` from every user and writes `tier`. Only `"legacy"` keeps a distinct value. Every other plan value becomes `"standard"`, so the original value is lost. The file has no `down()`.
- **Evidence:** Input users with plans `pro`, `legacy`, and `free`. After `up()` they hold tiers `standard`, `grandfathered`, and `standard`. `hasattr(m2, "down")` returns `False`. After the migration, `users.create_user` still writes `"plan": "free"` and no `tier` (`app/users.py:14`).
- **Verdict:** CONFIRMED. A probe ran `up()` on a seeded store in a scratch copy of the head.
- **Why Critical:** The step destroys data and has no rollback. A revert of the code cannot restore the `plan` values. New users then get the dropped field and miss the new one. No code reads `tier` yet, so the first reader of `tier` will meet both shapes.
- **Fix:** Split the migration. First add `tier` with a backfill, and keep `plan`. Ship a release that reads both. Drop `plan` in a later migration. Give each migration a `down()`. Change `create_user` to write `tier`, and update `tests/test_users.py`.
- **Cites:** `docs/invariants.md §3 Reversible migrations`

### High (should fix before merge)

#### H1: The discount percent is never validated, so the 30% cap has no effect
- **Locator:** `flow: app/api.py:18-27 → app/billing.py:19-22 → app/discount_engine/percent.py:10`
- **Changed anchor:** `app/api.py:22`, and `validate_percent` at `app/discount_engine/__init__.py:26-30` with no caller
- **What:** The commit says the percent is validated at the API boundary. `api_create_discount` stores `int(payload["percent"])` as is. `validate_percent` exists, but no code calls it. The cap change from 50 to 30 therefore changes nothing.
- **Evidence:** These probes create a code and charge 10.00 with it.

  | Percent | Charged amount | Total |
  |---|---|---|
  | 31 | 690 | 724 |
  | 40 | 600 | 630 |
  | 150 | -500 | -525 |
  | -50 | 1500 | 1575 |

- **Verdict:** CONFIRMED. The probes ran against the head. A grep finds no caller of `validate_percent`. The independent verifier reproduced the result.
- **Why High:** A code above 100% writes a negative charge, so the business pays the customer. A negative percent overcharges the customer. Finance policy FIN-88 is not enforced.
- **Fix:** Call `validate_percent` in `api_create_discount` and return an error for a bad value. Also reject a missing field, a non-integer percent, and `max_uses < 1`. Today `int()` truncates 12.9 to 12 without a warning. Add tests for 0, 31, 150, and -50.
- **Cites:** `docs/invariants.md §4 Percentage adjustments`

#### H2: A single-use code gives its discount on every charge
- **Locator:** `flow: app/billing.py:19-22 → app/api.py:30-39 → app/api.py:26`
- **What:** `billing.charge` applies the discount without a check or an increment of `uses`. `api_redeem` is a separate endpoint that no charge calls. It returns `redeemed: True` for an unknown code because `row is None` passes the condition, and the `except Exception: pass` hides the `KeyError`. A second `api_create_discount` call with the same code resets `uses` to 0.
- **Evidence:** One code with `max_uses` 1, charged three times, gives `amount` 800 each time, and `uses` stays 0. `api_redeem({"code": "NOPE"})` returns `{"redeemed": True}`.
- **Verdict:** CONFIRMED. The probes ran against the head. The independent verifier reproduced the result.
- **Why High:** Each customer can reuse any code without limit. The usage counter is wrong, so reports on code usage are wrong too.
- **Fix:** In `billing.charge`, reject the code when `uses >= max_uses`, apply it, then increment `uses`. Delete `api_redeem`, or make it reject unknown codes. Make `api_create_discount` refuse an existing code. Add a test for an exhausted code.
- **Cites:** `docs/testing.md` ("limit exceeded" is a required failure path)

#### H3: `api_apply_credit` writes negative, unattributed entries to the charge ledger
- **Locator:** `app/api.py:42-50`
- **What:** The endpoint strips a leading `-` and negates the parsed value. This bypasses the non-negative rule in `util.parse_money`. It appends an entry with `user_id: None` to `STORE.charges`. It takes no user, no reason, and no limit. The commit message does not mention it.
- **Evidence:** `api_apply_credit({"amount": "-1000000.00"})` appends `{'user_id': None, 'amount': -100000000, 'total': -100000000}`.
- **Verdict:** CONFIRMED. The probe ran against the head. The independent verifier reproduced the result.
- **Why High:** Any caller can write an unbounded credit that no user owns. Ledger totals become wrong, and nobody can trace the entry back.
- **Fix:** Remove the endpoint from this branch. If you need credits, model them as an explicit adjustment with a user id, a reason, and boundary validation. The `parse_money` docstring asks for that model.
- **Cites:** `docs/invariants.md §4` names a credit as an adjustment that the API boundary must validate. `app/util.py:9-13` is the `parse_money` docstring. The repo has no security doc, so the missing actor is judged against OWASP A01 Broken Access Control.

#### H4: `create_user` no longer normalizes the email
- **Locator:** `app/users.py:12`
- **Changed anchor:** the removed `normalize_email` import and call
- **What:** The branch replaces `normalize_email(email)` with `email.strip()`. Mixed-case emails now go into the users table as typed. Every lookup expects the canonical form.
- **Evidence:** A user created as `" Bob@Example.COM "` is stored as `'Bob@Example.COM'`. A charge for `bob@example.com` then raises `BillingError: unknown user`. A second user with `bob@example.com` is created, so one person has two accounts.
- **Verdict:** CONFIRMED. The probe ran against the head. The independent verifier reproduced the result.
- **Why High:** The users table gets non-canonical rows and duplicate accounts. Charges fail for real customers. Cleanup needs a data fix, not only a revert.
- **Fix:** Restore `normalize_email(email)`. Add a test that creates a mixed-case user and charges it by the lowercase email.
- **Cites:** `docs/invariants.md §1 Canonical emails`. `CLAUDE.md` ("Reuse helpers in app/util.py").

### Medium (worth fixing now; acceptable as a follow-up)

#### M1: The support console crashes on an unknown email
- **Locator:** `flow: app/db.py:14-18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:18` (`return None` replaces `raise NotFound(email)`)
- **What:** `find_user_by_email` now returns `None`. `support.lookup` still catches `NotFound`, which never comes. It then reads `u["id"]` on `None`.
- **Evidence:** `support.lookup("nobody@x.y")` raises `TypeError: 'NoneType' object is not subscriptable`. Before the change it returned `{"found": False}`.
- **Verdict:** CONFIRMED. The probe ran against the head. A grep shows `support.py` as the only other caller.
- **Why Medium:** Every support search for an absent user fails. The impact stays in the support console. The commit says "billing was updated to match" but misses this caller.
- **Fix:** Change `support.lookup` to test `if u is None`. Add a not-found test. Then delete `NotFound` from `db.py` if no caller is left.
- **Cites:** `docs/testing.md` ("not-found" is a required failure path)

#### M2: The billing change ships with a happy-path test only
- **Locator:** `meta: C1, H1, H2, H4`
- **Changed anchor:** `tests/test_discounts.py:13-19`
- **What:** The one new test charges a valid 10% code. No test covers an unknown code, an exhausted code, an over-cap percent, the migration, or email case. The top three production risks below have no covering test.
- **Evidence:** These are the top three risks and their tests.

  | Risk | Covering test |
  |---|---|
  | Over-cap or negative discount (H1) | none |
  | Unlimited reuse of a code (H2) | none |
  | Data loss in migration 002 (C1) | none |

- **Verdict:** CONFIRMED. `tests/` holds four tests in total, and all four pass.
- **Why Medium:** Each risk already has its own Issue. This finding tracks the project rule, so the fixes ship with tests.
- **Fix:** Add one failure-path test per Issue above.
- **Cites:** `CLAUDE.md` ("Every change to app/billing.py requires failure-path tests"). `docs/testing.md`.

#### M3: The commit message omits three behavior changes and bundles unrelated work
- **Locator:** `scope: PR`
- **What:** The message describes discounts, the cap, the engine, the migration, and the lookup change. It does not mention these changes:
  - the `api_apply_credit` endpoint (H3)
  - the removal of email normalization (H4)
  - the new `source` field on users (`app/api.py:8`, `app/users.py:15`)

  The migration and the lookup contract also have no link to discounts. The discount path never calls `find_user_by_email`.
- **Evidence:** `git log main..HEAD` holds one commit, `520549a`. The diff touches `users.py` and `migrations/`, and the message gives no reason for either.
- **Verdict:** CONFIRMED. The message and the diff were compared hunk by hunk.
- **Why Medium:** A reviewer of the PR description will miss three behavior changes. One revert would roll back the discounts and the migration together.
- **Fix:** Split the branch into separate PRs: discounts, the plan-to-tier migration, and the lookup contract change. Drop the credit endpoint and the email change, or give each one its own PR with a reason.

## Questions

- **Q1** [`app/billing.py:19-22`] An unknown or mistyped code silently charges the full price. Is that intended, or must the charge fail so the customer can correct the code?
- **Q2** [`migrations/002_drop_plan.py:7`] Which `plan` values exist in production, and must `free` users map to `standard`?
- **Q3** [`app/billing.py:24`] Must the charge entry record the discount code, so finance can audit discounted charges?

## Suggestions

#### S1: Use the strategy registry or remove it
- **Locator:** `flow: app/billing.py:2,22 → app/discount_engine/__init__.py:10-35`
- **What:** `billing.charge` imports `PercentDiscount` directly. Nothing calls `get_strategy`, and nothing reads `DISCOUNT_ENGINE_BACKEND`. Keep `PercentDiscount` and a plain function now. Add the registry together with the second strategy.
- **Why it would be better:** The module docstring promises a plug point that billing bypasses. An environment variable that does nothing misleads whoever operates the service.

## What was done well

- [`app/discount_engine/percent.py:10`] The discount math uses integer floor division on cents. It keeps the new code free of floats, as `docs/invariants.md §2` requires.
- [`app/billing.py:15-17`] `charge` moved to the new `None` contract cleanly and keeps the `BillingError` for an unknown user. The existing failure test still passes.
- [`app/discount_engine/__init__.py:26-30`] `validate_percent` reads the cap from `billing.MAX_DISCOUNT_PERCENT`, so the cap has one source. It only needs a caller (H1).
- [commit `520549a`] The message names its tickets and the finance sign-off for the cap change.

## Verified

- **The problem is real.** On `main`, `STORE.discounts` exists but no code creates or applies a discount.
- **No import cycle.** `billing` imports `discount_engine.percent` at load. `validate_percent` imports `billing` inside the function, so module load succeeds. The test run proves it.
- **Python floor division.** The Python language reference defines `//` as floor division. For a positive amount the discount rounds down, so the customer pays at most one cent more than the exact value.
- **REFUTED: the float tax line loses a cent.** `app/billing.py:23` still computes tax with a float. This line is unchanged from `main`. A probe compared it with integer math for every amount from 0 to 20,000,000 cents and found no difference. The line breaks the letter of `docs/invariants.md §2`, but the probe found no observable effect.
- **Verification method.** Probes in a scratch copy of the head confirmed each Medium+ Issue. One independent subagent then tried to refute all seven candidates from the diff and the files. It refuted none. The skill asks for one verifier per candidate, and this quick review used one verifier for all.

## Not reviewed

- **Axes skipped in quick mode:** 5e architecture, 5h privacy, and 5m dependencies.
- **Axes covered only in part:** 5f conventions, 5g security, 5i testing, 5j outside sources, and 5l reversibility. Each one appears only where an Issue above cites it.
- **Occam pass and host reviewers:** skipped in quick mode. S1 came from the alignment check, not from an Occam pass.
- **Tickets SUPPORT-311 and FIN-88:** not reachable from this checkout. The cap value of 30 is taken from the commit message.
- **Absent docs:** the repo has no `docs/architecture.md`, `docs/security.md`, or `docs/privacy.md`.
- **Dependencies:** the diff adds none.
- **CI:** no PR exists yet, so there are no checks to read.

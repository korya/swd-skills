# Examine: Add discount codes with API validation (feature/discounts vs main)

## Headline

Hold. The PR claims API validation of the discount percent, but nothing calls the validator. A 150% code produces a negative charge.

The PR also ships an irreversible migration, breaks canonical emails, and crashes the support lookup. Two Critical and five High issues block the merge.

Review facts:

- Mode: full. The diff touches payments and adds a migration.
- Target: `git diff main...feature/discounts`, commit `e284420`, 8 files, +129 / -14.
- Description: the commit message of `e284420`.
- Test suite: 4 tests pass on the branch. Only one test covers the new code, and it covers the happy path.

## Approach fit

The discount core matches the obvious approach. The approach is a stored percent per code, validated at the API, and applied in integer cents inside `billing.charge`.

The PR also bundles four changes that the discount feature does not need:

- a pluggable strategy engine
- a destructive `plan` to `tier` migration
- a change of the not-found contract of `find_user_by_email`
- a new `api_apply_credit` endpoint

I found no constraint in the repo that requires any of them. M2 covers the scope.

## Issues

### Critical (must fix before merge)

#### C1: The discount percent is never validated, so a code can make a charge negative
- **Locator:** `flow: app/api.py:18-27 → app/billing.py:19-22 → app/discount_engine/percent.py:10`
- **Changed anchor:** `app/api.py:22` (`"percent": int(payload["percent"])`)
- **What:** `api_create_discount` stores any integer percent. `validate_percent` in `app/discount_engine/__init__.py:26-30` exists, but no code calls it. The new 30% cap in `app/billing.py:11` therefore has no effect. The description says the opposite: "Discount percent is validated at the API boundary per docs/invariants.md §4."
- **Evidence:** probe in a detached worktree, a charge of `"10.00"` with a code at each percent:

  | percent | amount | total |
  |---|---|---|
  | 150 | -500 | -525 |
  | 100 | 0 | 0 |
  | 31 | 690 | 724 |
  | -10 | 1100 | 1155 |

  A negative percent becomes a surcharge. Python floor division rounds toward negative infinity, so `(1000 * -10) // 100` is `-100`.
- **Verdict:** CONFIRMED. An independent verifier traced the same inputs by hand, and the worktree probe reproduced them.
- **Why Critical:** It violates a project invariant on a money path. Any caller who can create a code can create a negative ledger entry, which is a payout. The finance cap from FIN-88 is not enforced anywhere.
- **Fix:** Call the validator in `api_create_discount` and reject out-of-range values with a client error. Also re-check the percent in `charge`, or store only validated rows. Add failure-path tests for 0, 31, 101, and -10.
- **Cites:** `docs/invariants.md §4`, `CLAUDE.md` ("Every change to app/billing.py requires failure-path tests")

#### C2: Migration 002 drops `plan` for good, and the mapping loses data
- **Locator:** `migrations/002_drop_plan.py:4-7`
- **Changed anchor:** the whole new file
- **What:** The migration has no `down()`. It removes `plan` in the same release that introduces `tier`, with no dual-read release first. It maps every plan except `"legacy"` to `"standard"`, so a `"pro"` user becomes `"standard"`. `app/users.py:14` still writes `"plan": "free"` and never writes `tier`.
- **Evidence:** probe in a detached worktree, after `up()`:

  | before | after |
  |---|---|
  | `plan="legacy"` | `tier="grandfathered"`, no `plan` |
  | `plan="pro"` | `tier="standard"`, no `plan` |
  | new user after `up()` | `plan="free"`, no `tier` |

  `hasattr(m2, "down")` returned `False`. No file in `app/` reads `tier`.
- **Verdict:** CONFIRMED. An independent verifier confirmed each part from the code, and the worktree probe reproduced it. The loss applies to any plan value other than `"free"` and `"legacy"`. Q3 asks which values exist in production.
- **Why Critical:** A revert cannot restore the dropped field. After the deploy, the store holds two schemas, one for old users and one for new users. The discount feature does not need this change.
- **Fix:** Remove the migration from this PR. In a separate PR, add `tier` additively, dual-write it from `create_user`, and backfill it with an explicit map of every plan value. Drop `plan` only in a later release. Ship a `down()` with each step.
- **Cites:** `docs/invariants.md §3`

### High (should fix before merge)

#### H1: Single-use discount codes apply to every charge
- **Locator:** `app/billing.py:19-22`
- **What:** `charge` applies the code but never compares `uses` with `max_uses` and never increments `uses`. Only `api_redeem` touches `uses`, and no charge path calls it. The default `max_uses` is 1, so the default code is single-use on paper only.
- **Evidence:** probe with `max_uses=1`. Three charges of `"10.00"` returned amounts `[900, 900, 900]`. `uses` stayed at 0.
- **Verdict:** CONFIRMED. An adversarial self-pass found no other code that reads `max_uses`. The worktree probe reproduced the failure.
- **Why High:** Every leaked single-use code becomes an unlimited discount. The ledger looks correct, so nothing detects the loss.
- **Fix:** Check and increment `uses` inside `charge`, in one step with the discount. Delete `api_redeem` or make it a read-only status check.
- **Cites:** `docs/testing.md` ("limit exceeded" is a required failure-path case)

#### H2: The new credit endpoint writes unbounded negative ledger entries with no user
- **Locator:** `app/api.py:42-50`
- **What:** `api_apply_credit` strips a leading `-`, parses the rest, and negates it. It then appends an entry with `user_id: None` to `STORE.charges`. No limit, no user binding, and no validation apply. The PR description does not mention the endpoint.
- **Evidence:** `api_apply_credit({"amount": "-500.00"})` appended `{"user_id": None, "amount": -50000, "total": -50000}`. The docstring of `parse_money` in `app/util.py` says that "money enters the system as a non-negative amount". It also says that adjustments "are modeled explicitly". This endpoint bypasses that contract.
- **Verdict:** CONFIRMED. The worktree probe reproduced it. An adversarial self-pass found no guard, no caller, and no doc that sanctions it.
- **Why High:** Any API caller can write a credit of any size that belongs to no customer. Reconciliation cannot attribute it. The repo has no auth layer for any endpoint, so this is judged against OWASP A01 (Broken Access Control) and A04 (Insecure Design).
- **Fix:** Remove the endpoint from this PR. If credits are needed, model them as a separate entry type with a required `user_id`, a cap, and an authorized caller. Add failure-path tests.
- **Cites:** `app/util.py` `parse_money` docstring, `docs/invariants.md §4`. No `docs/security.md` exists.

#### H3: The support lookup crashes on an unknown email
- **Locator:** `flow: app/db.py:14-18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:18` (`return None` replaces `raise NotFound(email)`)
- **What:** `find_user_by_email` now returns `None`. `support.lookup` was not updated and still catches `NotFound`, which nothing raises now. It then reads `u["id"]` on `None`. The description says "billing was updated to match" but omits this caller.
- **Evidence:** `support.lookup("nobody@x.y")` returned `{"found": False}` on `main`. On the branch it raises `TypeError: 'NoneType' object is not subscriptable`.
- **Verdict:** CONFIRMED. The worktree probe ran on both commits. A grep shows `support.py` is the only other caller.
- **Why High:** Every support search for a non-existent customer becomes an error. H4 makes this more frequent, because mixed-case writes make lookups miss.
- **Fix:** Keep the old contract and revert the `db.py` change. The discount code does not need it. Otherwise update `support.lookup` and delete `NotFound`. Add a not-found test for `support.lookup`.
- **Cites:** `docs/testing.md` ("Money and lookup paths require failure-path tests (... not-found ...)")

#### H4: User creation no longer stores canonical emails
- **Locator:** `app/users.py:12`
- **What:** `create_user` dropped the call to `normalize_email` and now only strips. It stores `"Alice@Example.COM"` as given. Every reader assumes lowercase. The description does not mention this change.
- **Evidence:** probe on the branch:
  - `create_user("  Alice@Example.COM ")` stored `'Alice@Example.COM'`.
  - `billing.charge("alice@example.com", "1.00")` raised `BillingError: unknown user`.
  - `support.lookup("alice@example.com")` raised `TypeError`, see H3.
  - A second `create_user("alice@example.com")` succeeded, so the store held two users for one person.

  On `main`, the same input stored `'alice@example.com'` and the charge succeeded.
- **Verdict:** CONFIRMED. An independent verifier found no other read or write path that lowercases the email. The worktree probe ran on both commits.
- **Why High:** Customers who sign up with capitals cannot be charged or found. Duplicate accounts accumulate. Each non-canonical record needs a backfill later.
- **Fix:** Restore `email = normalize_email(email)`. Add a mixed-case test for `create_user` and `charge`.
- **Cites:** `docs/invariants.md §1`, `CLAUDE.md` ("Reuse helpers in app/util.py before writing new parsing or validation code")

#### H5: Tests cover only the happy path of a money change
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The only new test charges a valid 10% code once. No test covers an invalid percent, an unknown code, an exhausted code, a not-found lookup, a mixed-case email, the migration, or the credit endpoint.
- **Evidence:** `python3 -m unittest discover tests -v` ran 4 tests, and all passed on a branch that contains C1, C2, H1, H3, and H4. `tests/test_users.py:13` still asserts `plan == "free"`, so the suite never runs the migration.
- **Verdict:** CONFIRMED by the test run and a read of the test files.
- **Why High:** The top three production risks have no test: negative charges (C1), data loss in the migration (C2), and broken lookups (H3, H4).
- **Fix:** Add the failure-path tests named in C1, H1, H3, and H4. Add a test for `up()` and `down()` if the migration stays.
- **Cites:** `CLAUDE.md` ("Every change to app/billing.py requires failure-path tests"), `docs/testing.md`

### Medium (fix now, or as a committed follow-up)

#### M1: `api_redeem` reports success for a code that does not exist
- **Locator:** `app/api.py:30-39`
- **What:** The condition `row is None or row["uses"] < row["max_uses"]` sends an unknown code into the success branch. `STORE.discounts[code]` then raises `KeyError`. The bare `except Exception: pass` swallows the error, and the function returns `{"redeemed": True}`. The comment "redemption must never fail the charge path" is wrong, because no charge path calls this function.
- **Evidence:** `api_redeem({"code": "NOPE"})` returned `{"redeemed": True}` with an empty `STORE.discounts`.
- **Verdict:** CONFIRMED by the worktree probe and an adversarial self-pass.
- **Why Medium:** Any client that trusts this answer grants a discount for a made-up code. No money moves through this function today, see H1.
- **Fix:** Return `{"redeemed": False}` when `row is None`. Remove the catch-all. Better, fold the check into `charge` as H1 proposes and delete the function.
- **Cites:** `docs/testing.md` ("not-found")

#### M2: The PR bundles four unrelated or undisclosed changes
- **Locator:** `scope: PR`
- **What:** The description presents the PR as discount codes. The diff also contains these changes:
  - The `plan` migration (C2). It is disclosed, but the discount feature does not need it.
  - The not-found contract change of `find_user_by_email` (H3). It is disclosed with an incomplete caller list.
  - The removal of email normalization (H4). It is not disclosed.
  - The `api_apply_credit` endpoint (H2) and the new `source` field on users. Neither is disclosed.
- **Evidence:** `git diff --stat main...feature/discounts` lists `migrations/002_drop_plan.py`, `app/db.py`, `app/users.py`, and `app/api.py:42-50`. None of them is on the discount path.
- **Verdict:** CONFIRMED by a read of the diff against the commit message.
- **Why Medium:** A revert of the discount feature also reverts these changes. C2 cannot be reverted at all. Reviewers who trust the description miss three behavior changes.
- **Fix:** Split the PR into the discount feature and separate PRs for each other change, each with its own description.

#### M3: Re-creating a code resets its usage counter, and input parsing is loose
- **Locator:** `app/api.py:18-27`
- **What:** `STORE.discounts[code] = row` overwrites an existing code and resets `uses` to 0. `max_uses` accepts 0 and negative values. `int(payload["percent"])` truncates the float `10.9` to `10` and raises an unhandled `ValueError` on `"10.5"`.
- **Evidence:** probe results:
  - A second `api_create_discount` call for `ONCE` returned `uses: 0` after the code was exhausted.
  - A percent of `10.9` was stored as `10`.
  - A percent of `"10.5"` raised `ValueError`.
- **Verdict:** CONFIRMED by the worktree probe and an adversarial self-pass.
- **Why Medium:** A support agent who re-enters a code reopens an exhausted promotion. The other cases produce wrong data or a server error on an edge input.
- **Fix:** Reject an existing code, or require an explicit update. Validate `max_uses >= 1`. Reject a non-integer percent with a client error.
- **Cites:** `docs/invariants.md §4`, `CLAUDE.md` (reuse `app/util.py` helpers for validation)

### Low (defer)
- **L1** [`app/billing.py:23`] The tax line uses float math, which `docs/invariants.md §2` forbids. The line predates the PR, but discounted amounts now flow through it. A scan of 0 to 20,000,000 cents found no total that differs from `(amount * 10500) // 10000`.
- **L2** [`app/db.py:4`] `NotFound` is now raised nowhere. Delete it, or keep raising it (see H3).
- **L3** [`app/api.py:8`] The new `source` field stores any client string without validation, and the description does not mention it.
- **L4** [`app/discount_engine/__init__.py:28`] `validate_percent` imports `billing` lazily to avoid a circular import. The engine now depends on the billing module that depends on it.

## Questions

- **Q1** [`app/billing.py:19-22`] Should an unknown or mistyped code fail the charge? Today `charge` silently charges full price for `"SAVE1O"`.
- **Q2** [`app/billing.py:11`] Where can a reviewer read FIN-88 and SUPPORT-311? Neither ticket is linked, so I could not reconcile the 30% cap or the scope with them.
- **Q3** [`migrations/002_drop_plan.py:7`] Which `plan` values exist in production data? The code only writes `"free"`, and the migration only knows `"legacy"`.
- **Q4** [`app/api.py:18`] Which layer authorizes `api_create_discount` and `api_apply_credit`? The description says "Support can now create" codes, but the repo has no auth check for any endpoint.

## Suggestions

#### S1: Collapse the discount engine into one function
- **Locator:** `app/discount_engine/__init__.py:1-35`
- **What:** Replace the registry, the abstract base class, and `get_strategy` with one integer function, for example `apply_percent(amount_cents, percent)`, next to `charge`.
- **Why it would be better:** `billing.py:2` imports `PercentDiscount` directly and never calls `get_strategy`. The `DISCOUNT_ENGINE_BACKEND` variable therefore changes nothing, and an unknown value raises `KeyError` in an unused path. The engine has one implementation. Fixed-amount and BOGO discounts have no ticket or spec in the repo. I checked the description, `docs/`, and `CLAUDE.md` for a constraint that needs the plug-in point and found none. Add the abstraction when the second strategy arrives.

#### S2: Put `validate_percent` in `app/util.py`
- **Locator:** `app/discount_engine/__init__.py:26-30`
- **What:** Move the validator to `app/util.py` and call it from `api_create_discount` (C1).
- **Why it would be better:** `CLAUDE.md` says to reuse and keep validation helpers in `app/util.py`. The move also removes the lazy import in L4.

## Gaps

- The PR has no manual test plan for the discount flow.
- The description does not say how support creates codes in practice: an API client, a console, or a script.

## Known limitations

- `api_redeem` checks and increments `uses` in two steps, so two concurrent calls can both pass. The store is in memory and single-process today, so the race cannot occur. It becomes real with a database. The fix in H1 should use one atomic update.

## What was done well

- [`app/discount_engine/percent.py:10`] The discount uses integer arithmetic on cents, `amount_cents - (amount_cents * self.percent) // 100`, as `docs/invariants.md §2` requires.
- [`app/billing.py:14`] The new `discount_code` parameter has a default, so existing callers of `charge` keep working.
- [`app/api.py:14`] `api_charge` reads the code with `payload.get`, so old clients that send no code are not affected.
- [`app/billing.py:18`] The PR reuses `parse_money` for the amount instead of a new parser.

## Verified

- The problem is real. On `main`, `STORE.discounts` exists but no code creates or reads it.
- The lowered cap affects no existing codes. `main` has no code path that writes `STORE.discounts`, so no code above 30% can exist yet.
- The branch merges cleanly with `feature/audit-log`. `git merge-tree` produced a tree with no conflict, although both branches edit `app/users.py` and `app/db.py`.
- `PercentDiscount.apply` rounds the discount down to whole cents, so the customer pays at most one cent more. The rounding is explicit integer arithmetic, so it complies with `docs/invariants.md §2`.
- The load-bearing assumption about Python floor division with negative operands was checked against Python semantics: it rounds toward negative infinity. This turns a negative percent into a surcharge (C1).
- Privacy: the diff stores and logs no new email copies. Discount rows and charge entries reference users by id, as `CLAUDE.md` requires.
- Verification: independent subagents checked C1, C2, and H4. The host limit on concurrent subagents blocked the other verifiers. H1, H2, H3, M1, and M3 were checked in an adversarial single-context pass, and an executed probe backs each one.
- Gap sweep: one fresh pass over the diff and the enclosing functions added Q1 and nothing else.

## Not reviewed

- The tickets SUPPORT-311 and FIN-88. They are not linked or present in the repo.
- CI status. The branch is local and has no PR, so `gh pr checks` does not apply.
- Architecture rules. The repo has no `docs/architecture.md` or `docs/guidelines.md`.
- Security policy. The repo has no `docs/security.md`, so H2 is judged against OWASP.
- Privacy policy. The repo has no `docs/privacy.md`. The diff adds no new personal data except the `source` field.
- Dependencies. The diff adds none.

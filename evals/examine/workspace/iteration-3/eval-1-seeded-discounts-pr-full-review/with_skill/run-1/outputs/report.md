# Examine: Discount codes with API validation (feature/discounts vs main)

Mode: **full**, chosen because the change touches a payment path and ships a migration.
Target: `git diff ddb5aa6..839b891` (merge-base of `feature/discounts` and `main`). The
working tree was clean. The PR description is the HEAD commit message.

## Headline

Hold. The discount cap is never enforced (C1). An unrelated edit breaks the canonical-email
invariant (C2). Five of the six bullets in the description are not what the code does.
Split the PR. Keep the discount feature, fix C1 and the High items, and move the rest into
their own reviewable changes.

## Approach fit

APPROACH DISPUTED for the out-of-scope half of the diff. The discount feature itself matches
one of my sketches, a strategy engine, with more generality than the ticket schedules (S1).
The other five changes have no constraint I could find in the repo, the docs, or the
history. These are the `find_user_by_email` contract change, the dropped email
normalization, migration 002, `api_apply_credit`, and the `source` field. The line findings
on the discount feature stand on their own. The findings on the five extra changes stand
too, but the first question for the author is why they travel in this PR.

## Issues

### Critical (must fix before merge)

#### C1: Discount percent is never validated, so any percent reaches billing
- **Locator:** `flow: app/api.py:22 → app/billing.py:20-22 → app/discount_engine/percent.py:9-10`
- **Changed anchor:** `app/api.py:18-27` (new `api_create_discount`)
- **What:** `api_create_discount` stores `int(payload["percent"])` with no range check.
  `validate_percent` exists at `app/discount_engine/__init__.py:26-30` and has zero callers.
  `charge` applies whatever percent is stored.
- **Evidence:** Reproduced. With a 10.00 charge, percent 150 yields `amount -500`, percent
  -50 yields `amount 1500` (a surcharge), percent 90 yields `amount 100`. Percent 0 and 31
  are also accepted. `grep -rn 'validate_percent('` in `app/` and `tests/` returns only the
  definition. The description says the percent "is validated at the API boundary per
  docs/invariants.md §4". It is not.
- **Verdict:** CONFIRMED. The verifier reproduced negative and over-cap charges and found no
  caller of `validate_percent`.
- **Why Critical:** Negative and over-cap money rows enter the ledger on a reachable path. It
  violates invariant §4 directly. The FIN-88 cap change in the same PR (`billing.py:11`) is a
  comment with no behavior behind it.
- **Fix:** Call the validator in `api_create_discount` and reject the row with an error when
  it returns false. Per `CLAUDE.md` ("Reuse helpers in app/util.py before writing new parsing
  or validation code"), move it to `util.parse_percent(raw) -> int` beside `parse_money` and
  let it raise `ValueError` on non-integers too. Add the failure-path tests H5 lists.
- **Cites:** `docs/invariants.md §4 (Percentage adjustments)`, `CLAUDE.md` line 3.

#### C2: `create_user` no longer lowercases emails, so mixed-case users are unreachable
- **Locator:** `app/users.py:12`
- **What:** The base called `util.normalize_email(email)` before the write. HEAD stores
  `email.strip()`. The import of `normalize_email` was removed. Nothing in the diff needs
  this change.
- **Evidence:** Reproduced. `create_user(" Alice@Example.COM ", ...)` stores
  `'Alice@Example.COM'`. `billing.charge("alice@example.com", "1.00")` then raises
  `BillingError("unknown user")`, and `support.lookup("alice@example.com")` raises `TypeError`
  (H1). The description does not mention the change.
- **Verdict:** CONFIRMED. The verifier reproduced both failures and confirmed the base used
  `normalize_email`.
- **Why Critical:** Invariant §1 states "a non-canonical write breaks every reader". Every
  user who signs up with a capital letter cannot be charged or found. The failure is silent
  and permanent for the stored row. No merge conflict will surface it: the sibling branch
  `feature/audit-log` merges cleanly on top (see Verified).
- **Fix:** Restore `email = normalize_email(email)` as the first line of `create_user`. Add
  a test that creates `"A@B.C"` and charges `"a@b.c"`.
- **Cites:** `docs/invariants.md §1 (Canonical emails)`.

### High (should fix before merge)

#### H1: `find_user_by_email` returns `None` now, and `support.lookup` still expects an exception
- **Locator:** `flow: app/db.py:14-18 → app/support.py:8-10`
- **Changed anchor:** `app/db.py:18` (`raise NotFound(email)` became `return None`)
- **What:** `support.lookup` catches `NotFound`, which is never raised anymore, then
  subscripts the `None` result. The description says "billing was updated to match".
  `support.py` was not.
- **Evidence:** Reproduced. `support.lookup("nobody@x.y")` raises
  `TypeError: 'NoneType' object is not subscriptable` instead of returning `{"found": False}`.
  `grep -rn find_user_by_email app/` lists two callers. Only `billing.py` was updated.
- **Verdict:** CONFIRMED. The verifier reproduced the crash and traced both callers.
- **Why High:** Every support-console lookup for an unknown email crashes. The suite does not
  cover the not-found path of `lookup`, so the regression is invisible to CI.
- **Fix:** Either keep the `NotFound` contract (the diff does not need the change) or update
  `support.lookup` to `if u is None: return {"found": False}` and delete the dead
  `NotFound` import. Add the not-found test `docs/testing.md` requires for lookup paths.
- **Cites:** `docs/testing.md` ("lookup paths require failure-path tests ... not-found").

#### H2: Redemption accounting is not wired to charging, so `max_uses` never limits anything
- **Locator:** `flow: app/billing.py:19-22 → app/api.py:30-38`
- **What:** `charge` applies a discount whenever the code exists and never reads or
  increments `uses`. `api_redeem` is the only code that touches `uses`, and nothing calls
  it. `api_redeem` itself has an inverted condition at `api.py:33`. The test `row is None or
  ...` enters the success branch for an unknown code, the `KeyError` is swallowed at
  `api.py:36-37`, and the call returns `{"redeemed": True}`.
- **Evidence:** Reproduced. A code with the default `max_uses` of 1 discounted three
  consecutive charges and `uses` stayed 0. After `api_redeem` exhausted the code,
  `charge` still discounted. `api_redeem({"code": "NOPE"})` on an empty store returned
  `{"redeemed": True}`. The description says customers "redeem them at charge time".
- **Verdict:** CONFIRMED. The verifier reproduced unlimited reuse and the inverted branch.
- **Why High:** Any shared code is unlimited, which is a direct revenue leak. The redeem
  endpoint reports success for codes that do not exist, so a client cannot trust it.
- **Fix:** Move the uses check and increment into `charge`, under the same step that applies
  the discount, and raise `BillingError` when the code is exhausted. Delete `api_redeem` or
  make it a thin wrapper over that step. Change the condition to `row is not None and
  row["uses"] < row["max_uses"]` and drop the bare `except Exception`.
- **Cites:** `docs/testing.md` ("limit exceeded" is a required failure path).

#### H3: Migration 002 is destructive, has no `down()`, and the code never adopts `tier`
- **Locator:** `flow: migrations/002_drop_plan.py:4-7 → app/users.py:14`
- **What:** `up()` pops `plan` and writes `tier`. There is no `down()`. `create_user` still
  writes `"plan": "free"` and never writes `tier`. Nothing in `app/` reads `tier`. The
  `"legacy"` value it maps from never existed in the base, whose only default is `"free"`.
- **Evidence:** Reproduced. After `up()`, an existing user is `{'tier': 'standard'}` with no
  `plan`. A user created afterwards is `{'plan': 'free'}` with no `tier`. `hasattr(m002,
  "down")` is `False`. `grep -rn tier app/` is empty. `tests/test_users.py:13` still asserts
  `plan == "free"`.
- **Verdict:** CONFIRMED. The verifier reproduced the split state and confirmed the base
  default.
- **Why High:** Invariant §3 forbids a destructive step without a dual-read release and
  requires a `down()`. After deploy the store holds two incompatible user shapes and the
  migration cannot be reverted. It is High rather than Critical because the lost value is
  the constant `"free"` for every user and can be reconstructed.
- **Fix:** Remove the migration from this PR. If `tier` is wanted, ship it per §3: add
  `tier` additively with a `down()`, make `create_user` write both, switch readers, and drop
  `plan` in a later release.
- **Cites:** `docs/invariants.md §3 (Reversible migrations)`.

#### H4: `api_apply_credit` writes unattributed, untaxed, negative ledger rows
- **Locator:** `app/api.py:42-50`
- **What:** The function strips a leading `-`, calls `parse_money` on the rest, negates the
  result, and appends `{"user_id": None, "amount": cents, "total": cents}` to
  `STORE.charges`. It is not mentioned in the description and has no test.
- **Evidence:** Reproduced. `{"amount": "-5.00"}` appends
  `{'user_id': None, 'amount': -500, 'total': -500}`. `"- 5.00"` with a space is accepted
  too. `parse_money`'s docstring (`app/util.py:9-10`) says negatives are rejected because
  "adjustments are modeled explicitly". This endpoint routes around that rule.
- **Verdict:** CONFIRMED. The verifier reproduced the rows and confirmed the util contract.
- **Why High:** Money rows with no user and no tax enter the same list `charge` writes to.
  Any downstream total per user or per tax period is now wrong, and nothing can attribute
  the credit.
- **Fix:** Drop it from this PR. A credit feature needs a user, an explicit sign convention
  in `util`, and its own tests. If kept, take a `user_id`, model the credit as a typed
  adjustment, and reuse `parse_money` without the manual sign handling.
- **Cites:** `docs/invariants.md §2 (Integer cents)` on explicit rounding and adjustments,
  `CLAUDE.md` line 3 on reusing `util` helpers.

#### H5: No failure-path tests, though three rulebook lines require them for this change
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The PR adds one test, the happy path at 10 percent. It changes `app/billing.py`,
  adds a money path, and changes a lookup contract. None of the required failure paths is
  tested.
- **Evidence:** Suite at HEAD is 4 tests, all passing, while C1, C2, H1, H2, and H3 are all
  live. The missing cases are over-cap percent, non-integer percent, unknown code, exhausted
  code, unknown email after the `None` change, and the support not-found path. `tests/` does
  not mirror `app/`. There is no `test_discount_engine.py`, `test_api.py`, or
  `test_support.py`.
- **Verdict:** CONFIRMED. The verifier listed the files and ran the suite.
- **Why High:** The top three production risks of this PR (wrong discount amounts, a support
  console crash, unreachable users) are each uncovered. Green CI here carries no information.
- **Fix:** Add a failing test per Issue above before fixing it. At minimum: percent 31 and
  150 rejected, unknown code raises or is reported, second charge on a single-use code
  fails, `support.lookup` unknown returns `{"found": False}`, mixed-case signup charges.
- **Cites:** `CLAUDE.md` line 4 ("Every change to app/billing.py requires failure-path
  tests"), `docs/testing.md` ("Money and lookup paths require failure-path tests").

### Medium (worth fixing now; acceptable as a follow-up)

#### M1: An unknown discount code is silently ignored and the customer pays full price
- **Locator:** `app/billing.py:21`
- **What:** `if row:` falls through when the code is unknown. The returned entry carries no
  sign that the code was dropped. The same function raises `BillingError` for an unknown
  user two lines earlier.
- **Evidence:** Reproduced. `charge("a@b.c", "10.00", "TYPO")` returns `{'amount': 1000,
  'total': 1050}` with no error.
- **Verdict:** CONFIRMED. The verifier reproduced it and noted the inconsistency with the
  unknown-user path.
- **Why Medium:** A customer who mistypes a code is charged full price and learns it from the
  statement. Whether to fail the charge or to report the dropped code is a product call.
  Silent is the one option that is wrong either way.
- **Fix:** Raise `BillingError("unknown discount code")`, or return the applied code and
  percent on the entry so the caller can show it. Test both.
- **Cites:** `docs/testing.md` ("not-found" is a required failure path).

#### M2: Re-creating an existing code resets its counters
- **Locator:** `app/api.py:26`
- **What:** `STORE.discounts[code] = row` overwrites without a check. `uses` goes back to 0
  and `max_uses` back to the default of 1.
- **Evidence:** Reproduced. A code with `max_uses 5` and `uses 2` became `{'uses': 0,
  'max_uses': 1}` after a second create with a new percent.
- **Verdict:** CONFIRMED.
- **Why Medium:** Once H2 is fixed, this is the remaining way to un-exhaust a code, and it
  happens by accident on a retry.
- **Fix:** Reject a duplicate code with an error, or require an explicit `overwrite` flag.

#### M3: The PR bundles six changes and the description misstates four of them
- **Locator:** `scope: PR`
- **What:** One commit carries seven changes. These are the discount feature, a cap policy
  change, a lookup contract change, a dropped invariant, a destructive migration, a credit
  endpoint, and a `source` field. The description claims validation that is absent (C1). It
  claims a billing-only update that missed `support.py` (H1). It claims a user mapping the
  code never completes (H3). It omits C2, H4, and the `source` field entirely.
- **Evidence:** `git diff main HEAD --stat` and the HEAD commit message, compared bullet by
  bullet above.
- **Verdict:** CONFIRMED.
- **Why Medium:** A reviewer cannot sign off on a description that does not describe the
  diff. A revert of any one problem takes the feature with it.
- **Fix:** Split into at least three PRs: the discount feature, the db contract change with
  both callers, and the migration under §3. Drop or separately justify the credit endpoint,
  the `source` field, and the cap change (Q1).

### Low (defer)
- **L1** [`app/billing.py:14`] `discount_code: str = None` should be `Optional[str]` or
  `str | None`.
- **L2** [`app/api.py:22`] `int(payload["percent"])` raises a raw `ValueError` for `"abc"` or
  `"10.5"` at the trust boundary. Folds into the C1 fix.
- **L3** [`app/api.py:8`, `app/users.py:15`] The `source` field is unrelated, unvalidated
  free text with a silent `"web"` default. Drop it from this PR or name its allowed values.
- **L4** [`app/db.py:4`] `NotFound` is dead after H1 either way. Delete it or restore its
  use.
- **L5** [`app/billing.py:11`] The comment lost its pointer to §4 ("validated at the API
  boundary"). Restore it once C1 makes it true.

## Questions

- **Q1** [`app/billing.py:11`] Where is FIN-88 recorded, and did finance intend the 30
  percent cap to ship inside the discounts feature rather than as its own change?
- **Q2** [`app/api.py:30`] Who is meant to call `api_redeem`? The description says
  redemption happens at charge time, and the comment at `api.py:37` suggests it was meant
  to run inside `charge`.
- **Q3** [`migrations/002_drop_plan.py:7`] Where does a `"legacy"` plan come from? The base
  only ever writes `"free"`, and nothing reads `tier`.
- **Q4** [`app/discount_engine/__init__.py:1-5`] Are fixed-amount and BOGO discounts
  scheduled with a ticket, or is the engine built for a possible future?

## Suggestions

#### S1: Collapse `discount_engine` into one function in `billing`
- **Locator:** `arch: app/discount_engine/`
- **What:** Replace the package with `def apply_percent_discount(cents: int, percent: int)
  -> int` in `billing.py`, keeping the integer formula from `percent.py:10`.
- **Why it would be better:** The package adds an ABC, a decorator registry, and an
  environment variable for a single strategy. `get_strategy` has no callers and
  `DISCOUNT_ENGINE_BACKEND` is a dead configuration knob that would `KeyError` on any value
  but `"percent"`. `validate_percent` imports `billing` lazily to dodge the circular import
  the package created. I checked the constraints. §2 integer math is preserved by the
  function. §4 lives at the API boundary regardless. No ticket in the repo schedules
  another discount kind (Q4). The verifier confirmed `PercentDiscount(p).apply(c) == c -
  (c * p) // 100` for all tested values. Reintroduce the abstraction when the second kind
  arrives with its own requirements.

#### S2: Record the applied code and the pre-discount amount on the charge entry
- **Locator:** `app/billing.py:24`
- **What:** Add `"discount_code"` and `"list_amount"` to the entry when a discount applies.
- **Why it would be better:** Finance cannot audit FIN-88 compliance or reconcile revenue
  when the ledger shows only the discounted number. It also gives M1 a place to report a
  dropped code.

#### S3: Normalize the email at the lookup boundary too
- **Locator:** `app/api.py:13-15`
- **What:** Pass `normalize_email(payload["email"])` into `billing.charge`.
- **Why it would be better:** §1 says lookups assume canonical form, but `api_charge` passes
  the raw payload value. This is pre-existing, and C2 made it visible. Fixing both sides
  makes the invariant hold without depending on the caller.

#### S4: Replace the float in the tax line with basis-point integer math
- **Locator:** `app/billing.py:23`
- **What:** `total = amount * (10_000 + TAX_RATE_BP) // 10_000`.
- **Why it would be better:** §2 forbids floats in money paths. The line is pre-existing.
  I found no divergence between the two formulas for amounts 1 to 200,000 cents at 500 bp.
  There is no numeric bug today. The discounted amount now flows through it, which makes
  this the moment to align the line with the rule.

## Gaps

- No manual test plan or statement of how SUPPORT-311 was validated.
- The sibling branch `feature/audit-log` edits `create_user` too and merges cleanly over this
  branch. Its tests use lowercase emails, so neither a conflict nor a test would catch C2
  after the merge.
- `README.md` does not list the new API functions or the `discount_code` payload field.
- `tests/test_users.py:13` still asserts `plan == "free"`, which contradicts migration 002.

## Known limitations

- No authentication or authorization exists anywhere in the repo, so `api_create_discount`
  has no access control. Every other `api_*` function is in the same state and the repo has
  no `docs/security.md`. Out of scope for this PR, but worth a line in the README before the
  service grows a network edge.
- The float tax line (S4) is pre-existing. It produces identical results to integer math in
  the tested range, so it is not filed as an Issue.

## What was done well

- [`app/discount_engine/percent.py:10`] The discount is computed with integer arithmetic
  (`amount_cents - (amount_cents * percent) // 100`), as §2 requires. The rounding direction
  is explicit.
- [`app/billing.py:15-17`] `charge` was updated to the new `None` contract and still raises
  `BillingError` for an unknown user, so the existing test keeps its meaning.
- [`app/billing.py:24`] Charge entries reference the user by `id`, never by email, per the
  `CLAUDE.md` privacy rule.
- [`app/discount_engine/__init__.py:27`] `validate_percent` cites §4 in its docstring and
  encodes the right bounds. The intent is correct. Only the call is missing.
- [`tests/test_discounts.py:8-11`] `setUp` clears all three stores, so the new test does not
  leak state into the others.

## Verified

- Suite at HEAD: 4 tests, all pass (`python3 -m unittest discover tests -v`).
- The problem exists in the base. `main` has `STORE.discounts` and `MAX_DISCOUNT_PERCENT`
  but no way to create or apply a discount. No existing utility solves it.
- Approach gate: the discount feature matches my third sketch (a strategy engine). I hunted
  for a constraint that justifies the five unrelated changes in the commit message, the docs,
  `git log`, and the sibling branch. None found. See Approach fit.
- REFUTED: "feature/audit-log will conflict on `app/users.py`". A dry-run merge in a
  scratchpad clone reported "Automatic merge went well" with zero conflicts. The merged file
  has no `normalize_email`. Reframed as the Gap above.
- The lazy `from ..billing import MAX_DISCOUNT_PERCENT` works in both import orders
  (`discount_engine` first and `billing` first). No runtime circular-import failure.
- Python semantics behind C1 and L2, checked by execution. `int("10.5")` and `int("abc")`
  raise `ValueError`, and `amount * -50 // 100` floors to `-500`, which is why a negative
  percent becomes a surcharge.
- `PercentDiscount(p).apply(c)` equals `c - (c * p) // 100` for `c` in `range(0, 5000, 7)`
  and `p` in 0 to 100 (verifier run), which supports S1.
- Float tax line: no divergence from integer math for amounts 1 to 200,000 cents at 500 bp.
- Dependencies: the diff adds none, so axis 5m has nothing to audit.
- The checkout matches the baseline: HEAD 839b891, `git status --porcelain --ignored` empty.
  Experiments ran from the scratchpad with `PYTHONDONTWRITEBYTECODE=1`. One verifier's
  first run wrote `__pycache__` directories into the repo and removed them before finishing.

## Not reviewed

- SUPPORT-311 and FIN-88. There is no remote, ticket system, or document in the repo, so the
  stated finance sign-off and the original ask are unverified claims (Q1).
- CI. No remote and no PR, so there are no checks to read.
- `docs/architecture.md`, `docs/security.md`, `docs/privacy.md`: absent. Architecture
  observations are filed as Suggestions (S1), not Issues. The diff adds no personal data
  beyond the existing email field, so no privacy policy was needed.
- `feature/audit-log` beyond its overlap with `app/users.py`.
- `migrations/001_init.py` and whatever runs the migrations, accepted as is.

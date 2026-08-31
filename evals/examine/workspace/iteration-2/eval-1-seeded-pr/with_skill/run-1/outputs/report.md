# Examine: feat(discounts): Add discount codes with API validation (`feature/discounts` vs `main`)

Target: branch `feature/discounts` (`9911202`) against `main` (`0074c2b`, also the merge-base);
one commit, 8 files, working tree clean. Mode: **full** (auto-chosen: payments path, a data
migration, and a store-contract change). Verification: three independent verifier subagents
(each given only the diff, the files, and the bare candidate) plus the host's built-in review
as an extra candidate source.

## Headline

**Hold.** The PR's three load-bearing claims are false in the diff (percent is *not* validated,
`support.py` was *not* updated to the new `find_user_by_email` contract, new users still get
`plan` not `tier`), it breaks three documented invariants (§1 canonical emails, §3 reversible
migrations, §4 percentage validation), and the discount core lets a 150% code produce a
negative charge. Roughly half of the diff is unrelated to SUPPORT-311 and unmentioned in the
description.

## Approach fit

**APPROACH DISPUTED.** The obvious change for "support creates percentage codes, customers
redeem at charge time" is ~40 lines: a `discount_code` argument on `billing.charge`, a percent
check against `MAX_DISCOUNT_PERCENT` in `api_create_discount`, integer-cents application, and
failure-path tests. The diff additionally ships a pluggable strategy registry selected by an
environment variable, a destructive `plan`→`tier` migration, a semantic change to
`db.find_user_by_email`, removal of email normalization, a `source` field on users, an
`api_redeem` endpoint decoupled from charging, and an `api_apply_credit` endpoint. I looked for
a constraint that would justify any of these (docs/, CLAUDE.md, README, git history, adjacent
code, the sibling branch): none exists in the repo, and SUPPORT-311 / FIN-88 are not available
to me. Findings on the discount core (C1, H2, M1, M2) stand on their own; findings on the
extras (C2, H4, M3, M4) are provisional on the author producing the constraint that motivates
them.

## Issues

### Critical (must fix before merge)

#### C1 — Discount percent is never validated; a 150% code yields a negative charge
- **Locator:** `flow: app/api.py:18-27 (api_create_discount) → app/billing.py:19-22 → app/discount_engine/percent.py:10`
- **What:** `api_create_discount` stores `int(payload["percent"])` unchecked. `validate_percent`
  (`app/discount_engine/__init__.py:26-30`) exists but has zero callers, and `billing.charge`
  applies whatever is stored. The description's "validated at the API boundary per §4" is not
  true of this diff. Lowering `MAX_DISCOUNT_PERCENT` to 30 (`app/billing.py:11`) therefore has
  no runtime effect at all.
- **Evidence:** Probe in a detached worktree: percent 150 → `amount=-500, total=-525`; percent
  -50 → `amount=1500` (a surcharge); percent 100 → `amount=0`; percent 31 and 50 accepted.
  `grep -rn validate_percent app/` returns only the definition.
- **Verdict:** CONFIRMED — verifier reproduced negative and inflated charges from the API.
- **Why Critical:** Wrong money on the main charge path, and a direct violation of a documented
  invariant. Any caller who can reach the endpoint (see Q3) can create a code that refunds
  instead of charging.
- **Fix:** In `api_create_discount`, reject the request when
  `not (1 <= percent <= billing.MAX_DISCOUNT_PERCENT)` (reuse or delete `validate_percent`;
  if kept, move it next to `MAX_DISCOUNT_PERCENT` so it needs no circular import). Add tests
  for 0, 31, 150 and non-numeric input.
- **Cites:** `docs/invariants.md §4` ("validated at the API boundary before it reaches
  billing"); CLAUDE.md ("Reuse helpers in app/util.py before writing new parsing or
  validation code").

#### C2 — Migration 002 is destructive, irreversible, and leaves the schema half-migrated
- **Locator:** `flow: migrations/002_drop_plan.py:4-7 → app/users.py:14 → tests/test_users.py:13`
- **What:** The migration pops `plan` and writes `tier` in one step with no `down()`. The mapping
  `"grandfathered" if plan == "legacy" else "standard"` collapses every other value (`free`,
  `pro`, …) to `standard`, so the original values cannot be recovered. Meanwhile
  `users.create_user` still writes `"plan": "free"` and never writes `tier`, nothing in `app/`
  reads `tier`, and `tests/test_users.py:13` still asserts `plan == "free"`. After deploy,
  migrated users have `tier` and no `plan`; new users have `plan` and no `tier`.
- **Evidence:** `hasattr(m, "down")` → `False` (migration 001 has one). Ran `up()` then
  `create_user`: old user `{'tier': 'standard'}`, new user `{'plan': 'free'}` with no `tier`.
  `grep -rn tier app/` → nothing.
- **Verdict:** CONFIRMED — verifier reproduced the half-migrated state and the lossy mapping.
- **Why Critical:** Irreversible data damage shipped in the same PR as a feature, contradicting
  the project's migration invariant on every clause (additive first, dual-read release,
  `down()` shipped). A rollback of the feature cannot restore `plan`.
- **Fix:** Drop the migration from this PR entirely (nothing in the discounts feature uses
  `tier`). If `tier` is genuinely needed: add it additively with a backfill and a `down()`,
  make `create_user` write both fields, release, then drop `plan` in a later migration.
- **Cites:** `docs/invariants.md §3` ("additive first; destructive steps only after a release
  with dual-read, and every migration ships a `down()`").

#### C3 — Email normalization dropped at the write path; mixed-case users cannot be charged
- **Locator:** `app/users.py:12`
- **What:** `normalize_email(email)` (strip + lowercase) was replaced with `email.strip()`, and
  the `util` import removed. `find_user_by_email` compares exactly (`app/db.py:16`), so a user
  created as `A@B.C` is not found by a charge for `a@b.c`, and every persisted email from now
  on may be non-canonical. Not mentioned in the description.
- **Evidence:** Probe: `api_create_user({"email": "  A@B.C "})` stores `'A@B.C'`;
  `api_charge({"email": "a@b.c", ...})` → `BillingError: unknown user`.
- **Verdict:** CONFIRMED — verifier reproduced with `Bob@Example.COM`.
- **Why Critical:** Violates a documented invariant whose own text says "a non-canonical write
  breaks every reader"; the symptom is failed charges (revenue loss) and, worse, persisted
  non-canonical rows that need a data fix after the fact.
- **Fix:** Restore `email = normalize_email(email)` and the import; add a test that creates
  with mixed case and charges with the canonical form.
- **Cites:** `docs/invariants.md §1` ("`util.normalize_email` at every write path");
  CLAUDE.md ("Reuse helpers in app/util.py").

### High (should fix before merge)

#### H1 — `find_user_by_email` contract change crashes `support.lookup`
- **Locator:** `flow: app/db.py:14-18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:18` (`return None` replacing `raise NotFound(email)`)
- **What:** The description says "billing was updated to match", but `support.py` was not: it
  still catches `NotFound` (now never raised) and then indexes `u["id"]` on `None`. `NotFound`
  is now dead in `db.py` yet still imported by `support.py`.
- **Evidence:** `support.lookup("nobody@x.y")` → `TypeError: 'NoneType' object is not
  subscriptable` (was `{"found": False}` on `main`). No test covers `support.lookup`.
- **Verdict:** CONFIRMED — reproduced by me and by the verifier.
- **Why High:** Outage of the support console's not-found path, introduced by a contract change
  the feature does not need (billing's `try/except NotFound` was fine).
- **Fix:** Either revert the `db.py` change (simplest; the discount code paths never call it),
  or update `support.lookup` to `if u is None` and delete `NotFound`. Add a
  `tests/test_support.py` not-found case either way.
- **Cites:** `docs/testing.md` ("lookup paths require failure-path tests … not-found").

#### H2 — `max_uses` is never enforced on the charge path; `api_redeem` is inverted and swallows errors
- **Locator:** `flow: app/billing.py:19-22 → app/api.py:30-39`
- **What:** `billing.charge` reads `row["percent"]` and never touches `uses`, so a `max_uses=1`
  code discounts unlimited charges. The separate `api_redeem` endpoint has an inverted guard
  (`row is None or …` reports an unknown code as redeemed), and the `except Exception: pass`
  hides the resulting `KeyError`. Its comment ("must never fail the charge path") is
  misleading: `api_redeem` is not on the charge path.
- **Evidence:** Three charges with a `max_uses=1` code → 900/900/900, `uses` still 0.
  `api_redeem({"code": "NOPE"})` on an empty store → `{'redeemed': True}`.
- **Verdict:** CONFIRMED — verifier reproduced both behaviours.
- **Why High:** Wrong money (single-use promotions are unlimited) plus a predicate that lies to
  its caller and silently discards its own failure.
- **Fix:** Enforce and increment `uses` inside `billing.charge` (the one place that knows a
  redemption happened), raise `BillingError` when exhausted, and delete `api_redeem` — or, if
  a separate reservation step is required, fix the condition to `row is not None and …` and
  drop the blanket `except`. Test the exhausted-code path.
- **Cites:** `docs/testing.md` ("limit exceeded"); CLAUDE.md (failure-path tests for
  `billing.py`).

#### H3 — Failure-path tests required by the project are absent; none of the top-3 risks is covered
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The only new test is one happy path. There is no test for an over-cap or
  non-numeric percent, an unknown or exhausted code, `api_redeem`, `api_apply_credit`,
  migration 002, or the `support.lookup` regression. The suite passes 4/4 on a branch with
  C1–C3 and H1–H2 present, which is the definition of "green but unguarded".
- **Evidence:** `python3 -m unittest discover tests -v` → `Ran 4 tests … OK` at HEAD.
- **Verdict:** CONFIRMED.
- **Why High:** The project makes failure-path tests a hard rule for `billing.py` changes, and
  every named production risk in this review (negative charge, lossy migration,
  canonical-email regression, support crash) is currently uncovered.
- **Fix:** Add, at minimum: percent 0/31/150/"abc" rejected; unknown code; exhausted code;
  mixed-case email chargeable; `support.lookup` not-found; migration `up`/`down` round-trip if
  the migration survives.
- **Cites:** CLAUDE.md ("Every change to app/billing.py requires failure-path tests");
  `docs/testing.md` ("invalid input, not-found, limit exceeded — not just the happy path").

#### H4 — `api_apply_credit` creates unattributed negative ledger entries with no validation
- **Locator:** `app/api.py:42-50`
- **What:** An endpoint unrelated to discounts and absent from the description. It sidesteps
  `parse_money`'s deliberate rejection of negative amounts (`app/util.py:13`) by stripping the
  sign and negating, then appends `{"user_id": None, "amount": -N, "total": -N}` to
  `STORE.charges` with no user lookup, no cap, no test.
- **Evidence:** `api_apply_credit({"amount": "-5.00"})` → `{'user_id': None, 'amount': -500,
  'total': -500}`.
- **Verdict:** CONFIRMED.
- **Why High:** Arbitrary negative money can be pushed into the ledger attached to no user; the
  ledger can no longer be reconciled by `user_id`. No project security doc exists; judged
  against OWASP A01 (Broken Access Control) and A04 (Insecure Design) explicitly.
- **Fix:** Remove from this PR. If credits are wanted, model them as a separate, user-bound
  entry type in `billing` with an explicit amount contract, per `util.py`'s own note
  ("adjustments are modeled explicitly").
- **Cites:** CLAUDE.md ("reference users by id"); no project security rule — OWASP named above.

### Medium (worth fixing now; acceptable as a follow-up)

#### M1 — An unknown discount code is silently ignored and the customer is charged full price
- **Locator:** `app/billing.py:20-22`
- **What:** `row = STORE.discounts.get(discount_code); if row: …` has no else branch. A
  mistyped or deleted code produces a full-price charge with no error and no marker on the
  returned entry.
- **Evidence:** `api_charge({... "discount_code": "NOPE"})` → `{'amount': 1000, 'total': 1050}`.
- **Verdict:** CONFIRMED.
- **Why Medium:** Wrong behaviour on a common edge path; customers are charged more than they
  expect and nobody is told.
- **Fix:** `raise BillingError("unknown discount code")` (consistent with "unknown user"), and
  test it.
- **Cites:** `docs/testing.md` ("not-found").

#### M2 — `api_create_discount` overwrites existing codes and does no input validation
- **Locator:** `app/api.py:18-27`
- **What:** `STORE.discounts[code] = row` unconditionally replaces an existing code, resetting
  `uses` to 0 and changing its percent. `int(payload["percent"])` /
  `int(payload.get("max_uses", 1))` raise raw `ValueError` on non-numeric input; `max_uses`
  of 0 or negative is accepted; codes are not normalized (case-sensitive lookup).
- **Evidence:** Re-posting `ONE` turned `{'percent': 10, 'uses': 5}` into `{'percent': 25,
  'uses': 0}`; `percent: "ten"` → uncaught `ValueError`.
- **Verdict:** CONFIRMED.
- **Why Medium:** A trust-boundary endpoint that neither validates nor protects existing
  state; it is the natural home for the §4 check from C1.
- **Fix:** Reject duplicates (or make update explicit), validate `percent` and
  `max_uses >= 1`, translate parse errors to an API error, decide on code normalization.
- **Cites:** `docs/invariants.md §4`; no project rule on input validation — OWASP A03 sweep.

#### M3 — `discount_engine` is speculative generality with real operational cost
- **Locator:** `arch: app/discount_engine/__init__.py:1-35, app/billing.py:2`
- **What:** The registry, `register`, `get_strategy`, and the `DISCOUNT_ENGINE_BACKEND` env var
  have no callers; `billing` imports `PercentDiscount` directly. There is one implementation.
  `validate_percent` does a function-local `from ..billing import …` purely to dodge the
  `billing → percent → __init__ → billing` cycle. `get_strategy()` raises a bare `KeyError` on
  an unknown backend, and `KeyError: 'percent'` when `app.discount_engine` is imported without
  `percent.py` (registration is an import side effect). Selecting money logic by env var is a
  moving part ops must manage, with no ticket or doc asking for it.
- **Evidence:** `grep -rn "get_strategy\|STRATEGY_REGISTRY\|DISCOUNT_ENGINE_BACKEND" app/` →
  only the engine package; `DISCOUNT_ENGINE_BACKEND=bogo` → `KeyError: 'bogo'`.
- **Verdict:** CONFIRMED (Occam candidate; the verifier found no constraint justifying it —
  the only justification is the PR's own "upcoming fixed-amount and BOGO" claim,
  uncorroborated by any ticket or doc in the repo).
- **Why Medium:** Concrete cost: a dead configuration surface with a crash failure mode, a
  circular-import workaround adjacent code will copy, and three files where one function
  would do. Promoted from Suggestion per the "new moving part to operate" rule.
- **Fix:** See S1 — collapse to `apply_percent_discount(amount_cents, percent)` in
  `billing.py` next to `MAX_DISCOUNT_PERCENT`. Reintroduce a strategy type when the second
  strategy exists.

#### M4 — The description misstates the diff and the PR bundles unrelated, non-atomic changes
- **Locator:** `scope: PR`
- **What:** Three stated claims are false in the diff (validation at the API boundary — C1;
  "billing was updated to match" — H1; users mapped onto `tier` — C2). Unmentioned entirely:
  removal of `normalize_email` (C3), the `source` field, `api_redeem` (H2), `api_apply_credit`
  (H4). The single commit mixes a customer feature, a finance policy change, a store contract
  change, a destructive migration, and a credits endpoint, so it cannot be reviewed, reverted,
  or bisected as a unit.
- **Evidence:** `git log -1 --format=%B` vs `git diff main`; single commit `9911202`.
- **Verdict:** CONFIRMED.
- **Why Medium:** Reviewers and future readers are actively misled; the revert story is
  entangled with C2.
- **Fix:** See S4 — split; rewrite the description to describe what the code does.

### Low (defer)
- **L1** [`app/billing.py:23`] `int(amount * (1 + TAX_RATE_BP / 10_000))` is float arithmetic in a money path (CLAUDE.md, `docs/invariants.md §2`). Pre-existing on `main`; brute-forced 0–5,000,000 cents against `amount * 10_500 // 10_000` with zero divergences, so currently benign. See S5.
- **L2** [`app/api.py:8`, `app/users.py:15`] Client-controlled, unvalidated, undocumented `source` stored on every user; unrelated to discounts.
- **L3** [`app/db.py:4`] `NotFound` is dead after this diff but still exported (and still imported by `support.py`, see H1).

## Questions

- **Q1** [`app/billing.py:11`] Is there a written FIN-88 decision, and was it meant to land in this PR? Nothing in the repo references it, and the cap is unenforced (C1), so today the change is a comment.
- **Q2** [`scope: PR`] Does SUPPORT-311 ask for redemption limits, credits, or a `source` field? If not, why are they here?
- **Q3** [`app/api.py:18`, `app/api.py:42`] "Support can now create" codes — what layer restricts `api_create_discount` and `api_apply_credit` to support staff? No auth exists anywhere in this repo (pre-existing), but these two endpoints move money.
- **Q4** [`app/users.py:12`] Was dropping `normalize_email` intentional? If so, what replaces the §1 guarantee?
- **Q5** [`migrations/002_drop_plan.py`] Was `tier` meant to feed the discount feature (e.g. grandfathered users)? Nothing reads it.

## Suggestions

#### S1 — Collapse `discount_engine` into one function in `billing.py`
- **Locator:** `arch: app/discount_engine/`
- **What:** Replace the package with
  `def apply_percent_discount(amount_cents: int, percent: int) -> int: return amount_cents - (amount_cents * percent) // 100`
  beside `MAX_DISCOUNT_PERCENT`, and a `def validate_percent(percent) -> bool` beside it.
- **Why it'd be better:** Fewest concepts and failure modes: no registry, no env var, no
  circular import, no import-order-dependent registration. Walked against the constraints from
  steps 1–2: §2 (integer cents — preserved), §4 (validation at the API boundary — orthogonal,
  and easier because the constant and the check live together), CLAUDE.md helper reuse
  (satisfied). No constraint in the repo requires pluggability; when a second strategy is
  scheduled, an abstraction extracted from two real implementations will be better shaped than
  one guessed from zero.

#### S2 — Record the applied discount on the ledger entry
- **Locator:** `app/billing.py:24`
- **What:** Add `discount_code` and `discount_cents` (or the pre-discount `gross`) to the
  charge entry when a code is applied.
- **Why it'd be better:** Finance can reconcile a `900` back to `SAVE10`; today the ledger
  cannot distinguish a discounted charge from a smaller purchase.

#### S3 — Keep `api.py` a thin adapter
- **Locator:** `app/api.py:2, 26, 35, 49`
- **What:** On `main`, `api.py` only delegated to `users`/`billing`. The diff has it import
  `STORE` and mutate it directly. Route discount creation through a `discounts.py` (or
  `billing`) function, as `api_charge` does.
- **Why it'd be better:** One place to enforce §4 and CLAUDE.md's rules, and `tests/` can
  mirror `app/` as `docs/testing.md` asks. No `docs/architecture.md` exists, so this is an
  offer, not a rule.

#### S4 — Split the PR
- **Locator:** `scope: PR`
- **What:** (1) discounts: `charge(discount_code)`, validated `api_create_discount`, usage
  enforcement, tests; (2) if still wanted, the `find_user_by_email` contract change with *all*
  callers and `NotFound` removed; (3) the `tier` migration done additively with a `down()`;
  (4) credits, designed separately. Drop the `source` field and the normalization change
  unless Q2/Q4 justify them.
- **Why it'd be better:** Each piece becomes reviewable, revertible, and describable in one
  honest paragraph.

#### S5 — Integer tax arithmetic
- **Locator:** `app/billing.py:23`
- **What:** `total = amount * (10_000 + TAX_RATE_BP) // 10_000`.
- **Why it'd be better:** Satisfies §2 literally and makes the rounding rule (floor) explicit
  rather than an accident of `int()` on a float. Pre-existing, so optional here.

## Gaps
- `docs/invariants.md §4` still points at `billing.MAX_DISCOUNT_PERCENT` as "the cap"; if the cap moves or is enforced elsewhere, the doc should say where.
- README lists no endpoints; the four new API functions are undocumented.
- `tests/test_discounts.py` resets the three stores but not `users._ids`; harmless today (ids are never asserted).
- No manual test plan or changelog entry in the description.

## Known limitations
- The store is in-memory and single-process, so there is no concurrency race on `uses` or on
  `charges.append`; a real database would need the increment and the exhausted check to be
  atomic. Accepted for this fixture; worth a comment where the counter lives.
- No authentication or authorization layer exists anywhere in the repo (pre-existing, not
  introduced here); Q3 asks where it is expected to live.

## What was done well
- [`app/discount_engine/percent.py:10`] `amount_cents - (amount_cents * percent) // 100` is pure integer arithmetic with an explicit floor, exactly what `docs/invariants.md §2` asks for; the rounding direction (discount rounded down, in the merchant's favour) is deterministic.
- [`app/billing.py:14`] `discount_code: str = None` keeps the old two-argument `charge` signature working; `test_billing.py` passes unchanged and `if discount_code:` treats `""`/`None` uniformly.
- [`app/billing.py:24`] The charge entry still references the user by `id`, not email, honouring CLAUDE.md's privacy rule; no raw email is written outside the users table anywhere in the diff.
- [`tests/test_discounts.py:8-11`] `setUp` clears all three stores, so the new test is order-independent.
- The commit message is structured, cites the invariants doc and a ticket, and explains each non-obvious decision. The structure is right; the content needs to match the diff (M4).

## Verified
- Problem exists in the base snapshot: `main` has an unused `Store.discounts` and an unused `MAX_DISCOUNT_PERCENT`; `billing.charge` takes no discount argument. The feature is real work, not a misdiagnosis.
- Approach gate: divergence hunted in `docs/`, CLAUDE.md, README, `git log --all`, and the sibling `feature/audit-log` branch; no constraint found for the engine, migration, contract change, or credits. Hence APPROACH DISPUTED above.
- Load-bearing assumptions checked: "validated at the API boundary" (false, C1); "billing was updated to match" (true for billing, false for `support.py`, H1); "existing users are mapped onto `tier`" (true for the migration, but new users are not, C2); "finance signed off" (unverifiable, Q1).
- REFUTED candidate (from the host review): "existing discount rows with 31–50% become invalid under the new cap" — `STORE.discounts` is empty on `main` and nothing on `main` writes to it, so there are no pre-existing rows.
- `validate_percent` itself is correct for its stated contract (`1 <= p <= 30`); it is simply never called.
- `PercentDiscount.apply` cannot see a negative `amount_cents` from `charge` because `parse_money` rejects negatives (`app/util.py:13`); the negative outputs in C1 come only from the unvalidated percent.
- Float tax line (`app/billing.py:23`): brute-forced 0–5,000,000 cents at 5% against integer arithmetic, zero mismatches (L1).
- Privacy (CLAUDE.md email rule): no raw email stored or logged outside `STORE.users` in the diff; `charges` and `discounts` carry ids or codes only.
- Dependencies: none added or changed (no manifest in the repo; stdlib only).
- Tests at HEAD: 4/4 pass in a detached worktree (`python3 -m unittest discover tests -v`).
- No trace: experiments ran in a detached worktree under the scratchpad, since removed (`git worktree prune`); `git status --porcelain` on the primary checkout is empty and HEAD is still `9911202`. Nothing pushed, posted, or commented.

## Not reviewed
- `feature/audit-log` is a sibling branch, not the target; noted only that it also edits `app/users.py` and `app/db.py`, so a merge after this PR will conflict with C3/H1.
- No `docs/architecture.md`, `docs/security.md`, or `docs/privacy.md` exists; the architecture (5e) finding was downgraded to S3, and security/privacy findings name OWASP explicitly where no project rule applies.
- No PR object or CI: `gh pr checks` not applicable; only the local test run was observed.
- The host's built-in `code-review` skill was invoked in a subagent but diffed the wrong repository (the parent `swd-skills` checkout); its output was discarded and that subagent's manual fallback review was used as the candidate source instead. Every candidate it contributed was independently verified or refuted above.
- The `migrations/` runner (how `up()` is invoked in deployment) is not in the repo and was accepted as-is.

# Examine: feat(discounts): Add discount codes with API validation (`feature/discounts` vs `main`, full mode)

Target: `git diff main HEAD` in the fixture repo, branch `feature/discounts`, HEAD `f2c7a76`, tree clean. Mode: **full**, auto-chosen — the diff carries a migration and touches the payments path (`app/billing.py`). The "PR description" is the commit message of `f2c7a76`. Verification: one independent read-only subagent re-derived every Medium+ candidate from the code (11 CONFIRMED / 1 PLAUSIBLE / 0 REFUTED); the host's built-in `code-review` ran in a second subagent as an extra candidate source — all 14 of its findings overlapped with the list below.

## Headline

**Hold.** The description's central claim — "discount percent is validated at the API boundary per §4" — is false: `validate_percent` is never called, so a `percent` of 500 produces a negative charge (C1). On top of that, three bundled changes that have nothing to do with discounts each break something on their own (support console crash H1, dropped email canonicalization H2, irreversible migration H3), and the redemption limit is not wired to the money path at all (H4). The discount feature itself is ~20 lines of the 129 added; the rest is scope the sketches never needed.

## Approach fit

**APPROACH DISPUTED.** The obvious approach (a `create_discount` that validates percent at the boundary, an optional `discount_code` on `charge` applying integer-only math, failure-path tests — no migration, since `STORE.discounts` already exists on `main`) is in the diff, but wrapped in five things no sketch called for and no constraint in the repo justifies: a registry/env-var strategy engine with one implementation, a destructive `plan → tier` migration, a changed `find_user_by_email` contract, a `source` field on users, and an `api_apply_credit` endpoint the description never mentions. I searched for the constraint (SUPPORT-311 and FIN-88 are not in the repo; the history is a single commit; no architecture doc) and found none. Until the author answers Q1 and Q5, the shape of this PR is the open question; the line-level findings below are provisional in the sense that half of them disappear if the unrelated changes are split out (see M3).

## Issues

### Critical (must fix before merge)

#### C1 — Discount percent is never validated; any integer is accepted and `charge` goes negative
- **Locator:** `flow: app/api.py:18-27 (api_create_discount) → app/billing.py:19-22 (charge) → app/discount_engine/percent.py:10`
- **Changed anchor:** `app/api.py:22` (`"percent": int(payload["percent"])`), `app/discount_engine/__init__.py:26-30` (`validate_percent`, zero callers), `app/billing.py:11` (`MAX_DISCOUNT_PERCENT`, read only inside the uncalled validator)
- **What:** `api_create_discount` stores whatever integer the payload carries. `validate_percent` exists and has the right bounds (`1 <= percent <= MAX_DISCOUNT_PERCENT`) but nothing calls it, and `MAX_DISCOUNT_PERCENT` is read on no execution path. `PercentDiscount.apply` then does `amount - amount*percent//100` with the unchecked value.
- **Evidence:** Reproduced in a scratch copy: `api_create_discount({"code":"BIG","percent":500})` then `api_charge({... "amount":"10.00","discount_code":"BIG"})` → `{'amount': -4000, 'total': -4200}`; `percent=-50` → `amount 1500` (a 50% surcharge); `percent=45` (above the new cap of 30) applied unchanged. `grep -rn validate_percent app tests` shows only the definition. Also, `payload["percent"]="10.5"` raises a raw `ValueError` out of the boundary.
- **Verdict:** CONFIRMED — independent verifier reproduced the negative and inflated charges and confirmed zero callers of `validate_percent`.
- **Why Critical:** Negative and inflated amounts on the money path from one unvalidated field at a trust boundary, in direct violation of a project invariant the PR explicitly claims to satisfy. The cap change (50 → 30, "per FIN-88") is a no-op for the same reason, so the finance decision the description announces did not ship.
- **Fix:** In `api_create_discount`, parse `percent` with a `util` helper that raises on non-integer / out-of-range input (CLAUDE.md asks for `util.py` reuse), call `validate_percent` (or inline the bound check) and reject with an error before writing to `STORE.discounts`. Add the failure-path tests (H5). Consider also asserting the bound in `charge` as defence-in-depth against rows written by other paths.
- **Cites:** `docs/invariants.md §4` ("validated at the API boundary before it reaches billing"); `CLAUDE.md` ("Reuse helpers in app/util.py before writing new parsing or validation code").

### High (should fix before merge)

#### H1 — `find_user_by_email` contract change crashes the support console on every unknown email
- **Locator:** `flow: app/db.py:14-18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:14-18` (returns `None` instead of raising `NotFound`); `app/support.py` unchanged
- **What:** The description says "billing was updated to match". Billing was; `support.lookup` was not. It still wraps the call in `try/except NotFound` (now never raised anywhere) and then dereferences `u["id"]` on `None`.
- **Evidence:** `support.lookup("nobody@x.y")` on HEAD → `TypeError: 'NoneType' object is not subscriptable`; on `main` → `{"found": False}`. `grep -rn NotFound app` shows the class is raised nowhere after the change.
- **Verdict:** CONFIRMED — reproduced by me and by the verifier.
- **Why High:** A reachable, common path (support looks up an email that doesn't exist) turns from a handled not-found into an unhandled exception — an outage of the support console introduced by a change the discount feature did not need.
- **Fix:** Either revert the contract change (the `NotFound` exception is a fine design and both callers already handled it) or update `support.lookup` to `if u is None: return {"found": False}` and delete the dead `NotFound` class and its import. Add a `tests/test_support.py` not-found case either way (docs/testing.md: lookup paths require not-found tests).
- **Cites:** `docs/testing.md` ("lookup paths require failure-path tests (… not-found)").

#### H2 — `create_user` dropped `normalize_email`; mixed-case signups become unreachable by canonical lookups
- **Locator:** `app/users.py:12`
- **Changed anchor:** `app/users.py:4-5,12` (import removed; `email.strip()` replaces `normalize_email(email)`)
- **What:** Lowercasing was removed from the only write path for emails; only trimming survives. Every reader (`billing.charge`, `support.lookup`) does an exact match on the stored value.
- **Evidence:** `api_create_user({"email": "  A@B.C ", ...})` stores `A@B.C`; `api_charge({"email": "a@b.c", ...})` → `BillingError: unknown user`; `support.lookup("a@b.c")` → the H1 TypeError. On `main` both succeed. `util.normalize_email` now has zero callers.
- **Verdict:** CONFIRMED — reproduced by me and by the verifier.
- **Why High:** Wrong data at the identity layer: a customer who signs up with any capital letter cannot be charged or found by support, and duplicate accounts per casing become possible. Explicit invariant: "a non-canonical write breaks every reader."
- **Fix:** Restore `email = normalize_email(email)` in `create_user` (and, if the `source` parameter stays, keep it — but see L2). Add a canonicalization test to `tests/test_users.py`.
- **Cites:** `docs/invariants.md §1` ("`util.normalize_email` at every write path"); `CLAUDE.md` ("Reuse helpers in app/util.py").

#### H3 — Migration 002 is irreversible and destructive in one step, and the code never adopts `tier`
- **Locator:** `flow: migrations/002_drop_plan.py:4-7 → app/users.py:14 → tests/test_users.py:13`
- **Changed anchor:** `migrations/002_drop_plan.py` (new); `app/users.py:14` (still writes `"plan": "free"`)
- **What:** `up()` pops `plan` from every user and writes `tier`; there is no `down()`, no additive/dual-read release, and nothing in `app/` reads or writes `tier`. `create_user` still writes `plan`, so after the migration the user population is split: migrated users have `tier` and no `plan`, new users the reverse. The `plan == "legacy"` branch is unreachable for anything this codebase writes (the only value ever written is `"free"`), so every migrated user silently becomes `"standard"`. `tests/test_users.py:13` still asserts on `plan`.
- **Evidence:** Reproduced: `create_user(...)`, `002.up(STORE)` → `{'tier': 'standard'}`; `create_user(...)` again → `{'plan': 'free'}`. `hasattr(module, "down")` → `False`. `migrations/001_init.py` ships both `up` and `down`.
- **Verdict:** CONFIRMED — verifier reproduced the split population and the missing `down()`.
- **Why High:** A reversibility failure (no `down()`, destructive step in the same release) explicitly forbidden by §3, bundled into an unrelated feature PR, leaving schema and code disagreeing. Not Critical only because the data destroyed is a constant (`"free"`) and no app code reads `plan` today — the blast radius is the invariant and the mixed population, not lost information.
- **Fix:** Pull the migration out of this PR entirely. If the `plan → tier` move is wanted, do it per §3: an additive migration writing `tier` alongside `plan` (with `down()`), code switched to read/write `tier` with the test updated, then a later destructive drop after a release of dual-read.
- **Cites:** `docs/invariants.md §3` ("additive first; destructive steps only after a release with dual-read, and every migration ships a `down()`").

#### H4 — Redemption limits are not wired to the money path: `api_redeem` says yes to unknown codes, `charge` never counts uses, re-creating a code resets the counter
- **Locator:** `flow: app/api.py:30-39 (api_redeem) ↔ app/billing.py:19-22 (charge) ↔ app/api.py:26 (api_create_discount overwrite)`
- **Changed anchor:** `app/api.py:33` (`row is None or row["uses"] < row["max_uses"]`), `app/api.py:34-37` (`except Exception: pass`), `app/api.py:26` (unconditional `STORE.discounts[code] = row`), `app/billing.py:19-22` (no `uses`/`max_uses` check)
- **What:** Three defects with one root cause — the `uses`/`max_uses` model is never enforced where money moves. (a) `api_redeem`'s condition takes the success branch when `row is None`; the `KeyError` from `STORE.discounts[code]` is swallowed by the bare `except`, so an unknown code returns `{"redeemed": True}`. (b) `charge` applies a discount without checking or incrementing `uses`, so a `max_uses=1` code works on every charge forever; `api_redeem` is not on the charge path at all (the comment "must never fail the charge path" describes a path that does not exist). (c) `api_create_discount` overwrites an existing code and resets `uses` to 0, so even a correctly enforced limit could be bypassed by re-creating the code.
- **Evidence:** Reproduced: `api_redeem({"code":"NOPE"})` → `{'redeemed': True}`; a `SAVE10` code with default `max_uses=1`, already redeemed once, applied to three consecutive charges (`[900, 900, 900]`) with `uses` still `1`; re-creating `X` after it was exhausted → `uses: 0`.
- **Verdict:** CONFIRMED — verifier reproduced all three symptoms.
- **Why High:** The limit the feature advertises (`max_uses`, defaulting to 1) does not exist in practice — unbounded discount use is money leakage on a reachable path, and the endpoint reports success on failure.
- **Fix:** Decide where redemption lives. Simplest: drop `api_redeem`, have `charge` check `row["uses"] < row["max_uses"]` (raise `BillingError("discount exhausted")` otherwise) and increment `uses` after a successful charge; make `api_create_discount` refuse an existing code. If `api_redeem` stays, fix the condition to `row is not None and row["uses"] < row["max_uses"]`, remove the `except Exception: pass`, and let `charge` call it. Tests for each branch (H5).
- **Cites:** `docs/testing.md` ("limit exceeded" is a named required failure path on money paths).

#### H5 — Only a happy-path test ships for a change to `billing.py`; none of the top-3 production risks is covered
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** One test: a valid 10% code on a known user. No test for invalid or over-cap percent, unknown code, `max_uses` exhaustion, `api_redeem`, `api_apply_credit`, migration 002, canonical emails, or `support.lookup` not-found. The suite is green on HEAD (4/4) while C1, H1, H2, H3 and H4 are each reproducible in three lines.
- **Evidence:** `python3 -m unittest discover tests -v` on a copy of HEAD: 4 passed. The only failure-path test in the suite (`tests/test_billing.py:17-19`, unknown user) predates the PR.
- **Verdict:** CONFIRMED — verifier enumerated the uncovered paths against the testing doc.
- **Why High:** The project's own rule makes failure-path tests mandatory for exactly this file, and the three named top-3 risks (negative charge from bad percent, support console crash, mixed-case users unreachable) are all uncovered — a missing test for a named top-3 risk is High by definition here.
- **Fix:** Add, at minimum: `test_percent_above_cap_rejected`, `test_percent_negative_rejected`, `test_unknown_code_*` (whatever M2 decides), `test_max_uses_exhausted`, `tests/test_support.py::test_lookup_unknown`, a canonical-email test in `test_users.py`, and a migration test asserting `down(up(x)) == x` once H3 is redone.
- **Cites:** `CLAUDE.md` ("Every change to app/billing.py requires failure-path tests (docs/testing.md)"); `docs/testing.md` ("Money and lookup paths require failure-path tests (invalid input, not-found, limit exceeded)").

### Medium (worth fixing now; acceptable as a follow-up)

#### M1 — Undocumented `api_apply_credit` bypasses `parse_money`'s guard and writes unattributed money rows
- **Locator:** `app/api.py:42-50`
- **What:** A new endpoint the description never mentions. It strips a leading `-` and negates, deliberately routing around `parse_money`'s negative-input rejection (whose docstring says "adjustments are modeled explicitly"), appends to `STORE.charges` with `user_id: None`, ignores any `email` in the payload, and skips tax. Hand-rolled parsing at the boundary is exactly what CLAUDE.md says to avoid.
- **Evidence:** `api_apply_credit({"amount": "-5.00"})` → `{'user_id': None, 'amount': -500, 'total': -500}` appended; `parse_money("-5.00")` itself raises.
- **Verdict:** CONFIRMED — reproduced; verifier also notes the `user_id: None` row breaks "reference users by id".
- **Why Medium:** A money-creating path with no owner, no tax decision, no tests and no mention in the PR. Not High only because it is additive and nothing reads `charges` yet; it will be the first thing a reconciliation report trips on.
- **Fix:** Remove from this PR. If credits are wanted, model them explicitly (a `credit` entry type or a signed `kind` field) attributed to a `user_id`, parsed by a `util` helper, in their own PR with tests.
- **Cites:** `CLAUDE.md` ("Reuse helpers in app/util.py before writing new parsing or validation code"; "reference users by id"); `app/util.py:9-10` docstring contract.

#### M2 — An unknown `discount_code` is silently ignored and the customer is charged full price
- **Locator:** `app/billing.py:19-22`
- **What:** `row = STORE.discounts.get(discount_code); if row:` — a typo'd or expired code falls through and the charge proceeds at full price with no error, no flag in the returned entry. `charge` raises for an unknown user but says nothing for an unknown code.
- **Evidence:** `api_charge({... "discount_code": "TYPO"})` → `{'amount': 1000, 'total': 1050}`, indistinguishable from a charge with no code.
- **Verdict:** CONFIRMED — reproduced.
- **Why Medium:** Wrong behaviour on an edge path of a money flow: the customer's stated intent (use this code) is dropped without signal, which is a support ticket generator and arguably an incorrect charge. The not-found failure path is also untested.
- **Fix:** Raise `BillingError("unknown discount code")` (consistent with the unknown-user branch), or at least record `discount_code`/`discount_applied` on the entry so callers can tell. Test both outcomes.
- **Cites:** `docs/testing.md` ("not-found" is a required failure path on money paths).

#### M3 — Five unrelated changes bundled into one feature PR
- **Locator:** `scope: PR`
- **What:** Alongside the discount feature, the commit changes finance policy (`MAX_DISCOUNT_PERCENT` 50 → 30), drops the `plan` field via migration, changes the `db.find_user_by_email` contract, adds a `source` field to users, and adds a credit endpoint. Each is independently reviewable and independently revertable; together they make the PR impossible to revert cleanly (reverting it would also undo a finance decision and a schema change).
- **Evidence:** `git diff main HEAD --stat` — 8 files; the discount feature proper touches `api.py`, `billing.py`, `discount_engine/`, `test_discounts.py`. H1, H2, H3 and M1 are all defects in the bundled, non-discount changes.
- **Verdict:** CONFIRMED — the bundling is a fact of the diff; the cost is the four Highs/Mediums it carried in.
- **Why Medium:** A maintenance and reversibility trap with concrete cost already realized in this review. Medium rather than High because splitting is mechanical.
- **Fix:** Split into: (1) discounts; (2) cap change, once Q1 is answered; (3) `plan → tier` per §3; (4) any `db` contract change with all callers; (5) credits, if wanted. Drop `source` or justify it.

### Low (defer)
- **L1** [`app/billing.py:23`] `total = int(amount * (1 + TAX_RATE_BP / 10_000))` is a float in a money path (CLAUDE.md rule 1, invariants §2). Pre-existing on `main`, but this PR rewrites `charge` and now feeds discounted amounts through it. Verdict PLAUSIBLE: exhaustive check 0..10,000,000 cents shows no numeric divergence from `amount * 10_500 // 10_000` (first mismatch at 2^53); negatives diverge, but reach this line only via C1. Convention fix: integer form.
- **L2** [`app/users.py:7,16`, `app/api.py:8`] New `source` parameter is unrelated to discounts, unmentioned in the description, and stored as unvalidated free text (`"<script>…"` round-trips verbatim).
- **L3** [`app/db.py:4`, `app/support.py:1`] `NotFound` is now raised nowhere — dead class and dead import once H1 is resolved either way.
- **L4** [`app/api.py:19`] `code` is unvalidated: an empty string is storable but can never be applied (`if discount_code:` in `charge`); codes are also case-sensitive with no normalization (see Q4).

## Questions

- **Q1** [`app/billing.py:11`] Where is FIN-88 recorded, and does finance expect the 30% cap to take effect with this deploy? (Today it cannot — see C1 — and shipping a policy change inside a feature PR means a revert of the feature reverts the policy.)
- **Q2** [`app/api.py:18,42`] Is there an authorization layer above `app/api.py` that restricts `api_create_discount` and `api_apply_credit` to support staff? Nothing in the repo distinguishes them from customer-facing `api_charge`; no `docs/security.md` exists, so judged against OWASP A01 (Broken Access Control) — a question because the base has no auth on any endpoint either.
- **Q3** [`app/billing.py:19-23`] Tax is applied after the discount and the discount is floored (house-favouring: `999` at 10% → `900`, saving 99 not 99.9 cents). Both are defensible; are both intended, and should §2's "rounding decisions are made explicitly" get a sentence in the docs?
- **Q4** [`app/api.py:19`, `app/billing.py:20`] Are discount codes meant to be case-sensitive? `save10` will not match `SAVE10`.
- **Q5** [`migrations/002_drop_plan.py:7`] What produces `plan == "legacy"`, and what will read `tier`? Nothing in this repo does either.

## Suggestions

#### S1 — Collapse `discount_engine/` into a single function until a second strategy exists
- **Locator:** `app/discount_engine/__init__.py`, `app/discount_engine/percent.py`, `app/billing.py:2`
- **What:** The ABC, `register` decorator, `STRATEGY_REGISTRY`, `get_strategy` and the `DISCOUNT_ENGINE_BACKEND` env var have one implementation and zero callers — `billing.py` imports `PercentDiscount` directly, so the "pluggable" claim in the description is not what ships. `get_strategy()` raises `KeyError: 'percent'` in a fresh interpreter unless `percent.py` happens to have been imported first, and `validate_percent` does a lazy `from ..billing import` to paper over the resulting import cycle (billing → percent → engine → billing).
- **Why it'd be better:** Fewer concepts and failure modes: no import-order dependency, no env flag that silently does nothing, no cycle, and the cap constant can live next to the only code that enforces it. Walked against the constraints from steps 1–2: the only justification offered is "upcoming fixed-amount and BOGO" — unscheduled in the repo; nothing in CLAUDE.md or docs asks for a strategy layer. Occam: speculative generality; kept as a Suggestion because dead code has no production cost today.
- **Sketch:** `def apply_percent_discount(amount_cents: int, percent: int) -> int: return amount_cents - (amount_cents * percent) // 100` in `billing.py` (or `util.py`), with `MAX_DISCOUNT_PERCENT` and `validate_percent` beside it. Reintroduce the strategy abstraction in the PR that adds the second strategy.

#### S2 — Make `max_uses` a required, explicit field (or default to unlimited)
- **Locator:** `app/api.py:24`
- **What:** `max_uses` defaults to `1`, which for support-created codes is a surprising default once H4 makes it enforced — most promotional codes are multi-use.
- **Why it'd be better:** Avoids a wave of "my code stopped working" tickets the day the limit starts being honoured; forces the creator to state intent.

## Gaps
- No documentation of the discount model (code / percent / max_uses) anywhere in `docs/`; §4 only references the cap.
- No manual-test notes in the description; the feature is API-only, so automated tests (H5) would cover it.
- `README.md` not updated to mention the new endpoints.

## Known limitations
- `uses` increments are not concurrency-safe; acceptable because the store is in-process and single-threaded by design (`app/db.py` docstring), document if a real DB lands.
- `find_user_by_email` is a linear scan — pre-existing, fine at fixture scale.

## What was done well
- [`app/discount_engine/percent.py:10`] `amount_cents - (amount_cents * self.percent) // 100` — integer-only arithmetic with an explicit floor, exactly what invariants §2 asks for.
- [`app/discount_engine/__init__.py:26-30`] `validate_percent` has the right inclusive bounds and cites §4 in its docstring; it just needs a caller.
- [`app/api.py:13-16`, `app/billing.py:14`] `discount_code` is optional with a `None` default, so existing `api_charge` callers are unaffected.
- [`tests/test_discounts.py:9-11`] `setUp` clears all three stores, not just the one under test — avoids cross-test leakage.
- [commit `f2c7a76`] The description states its non-obvious decisions (cap change, migration, contract change) rather than hiding them — which is what made this review tractable.

## Verified
- Problem is real in the base: `main` has `STORE.discounts = {}` and `MAX_DISCOUNT_PERCENT` but no create/redeem path.
- Approach gate: hunted for a constraint justifying the engine, migration, and `db` contract change — SUPPORT-311 and FIN-88 are not in the repo, history is one commit, no architecture doc. None found; see Approach fit.
- Tests: `main` 3/3, HEAD 4/4, run on `git archive` copies outside the repo.
- Load-bearing assumption checked against the stdlib: `int("10.5")` raises `ValueError` (C1 boundary behaviour) and `int()` on a float truncates toward zero while `//` floors — the source of the negative-amount divergence noted in L1.
- Float tax (L1): exhaustive 0..10,000,000 cents, no divergence from the integer form.
- Privacy (CLAUDE.md "never store raw emails outside the users table"): no new email storage; `charges` carry `user_id` — except M1's `None`. `source` is not PII.
- Dependencies (5m): none added or changed.
- Verification: 12 Medium+ candidates sent to an independent subagent; 11 CONFIRMED, 1 PLAUSIBLE (L1), 0 REFUTED. Host `code-review` (14 findings) added no finding not already on the list; it did sharpen H4(c) (overwrite resets `uses`) and the `except Exception: pass` in `api_redeem`.
- Gap sweep (fresh pass): produced only L3, L4, Q2 and the Gaps — no new Medium+.
- Baseline: checkout matches `f2c7a76`, `git status --porcelain` empty at the end (a subagent's `__pycache__` was removed; no tracked file touched). Nothing pushed, commented, or posted.

## Not reviewed
- `docs/architecture.md`, `docs/security.md`, `docs/privacy.md`: absent. Security judged against OWASP A01 where raised (Q2); privacy against CLAUDE.md's logging rule only.
- The migration runner: none exists in the repo; `001_init.py`'s `up/down` shape taken as the contract.
- Tickets SUPPORT-311 and FIN-88: no access; their claims are recorded as Q1/Q5 rather than assumed.
- Concurrency and persistence: the store is in-memory and single-process by design.
- Branch `feature/audit-log` (sibling branch in the fixture): out of scope.

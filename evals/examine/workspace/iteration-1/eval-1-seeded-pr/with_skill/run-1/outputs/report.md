# Examine: feat(discounts): Add discount codes with API validation (`feature/discounts` → `main`)

Mode: **full** (auto-chosen: the diff touches payments/billing, a destructive migration, and money-path semantics — maximum blast radius for this repo). Merge-base `5dac977`; branch tip `0bcf605`; working tree clean, so the reviewed diff is exactly `git diff main...feature/discounts`. Tests on the branch: 4/4 pass — all happy-path. Verification was probe-backed (a throwaway script exercised the live code paths; results quoted per finding) plus an independent defect-first finder pass whose candidates were deduped into the list below.

## Headline

**Hold — do not merge.** The PR's three central claims are each contradicted by the code: "validated at the API boundary per §4" — the validator exists but is never called, and a 150% or −50% discount flows straight into charges; the plan→tier migration violates §3 (destructive, no `down()`) *and* disagrees with the code, which still writes `plan`; "billing was updated to match" the new `find_user_by_email` contract — but `support.py` was not, and now crashes on any unknown-email lookup.

## Approach fit

The core — percent codes created via the API, applied at charge time with integer-cent arithmetic — matches the obvious approach (sketch: boundary-validated `create_discount` + optional `discount_code` on `charge`). Three divergences from that sketch were hunted for a justifying constraint (docs, git history, adjacent code; the linked SUPPORT-311 and FIN-88 tickets are not accessible from this checkout) and none was found, so each surfaces as a finding: the pluggable engine (M2), the bundled destructive migration (C2), and the `find_user_by_email` contract change (H1). The gate passes for the core; line-level findings below are not provisional.

## Issues

### Critical (must fix before merge)

#### C1 — Discount percent is never validated; negative and >100% percents produce negative or inflated charges
- **Locator:** `flow: app/api.py:18-27 → app/billing.py:19-22 → app/discount_engine/percent.py:9-10`
- **Changed anchor:** `app/api.py:18` (`api_create_discount`), `app/billing.py:19-22`
- **What:** The PR description says "Discount percent is validated at the API boundary per docs/invariants.md §4." No validation exists on any path: `api_create_discount` stores `int(payload["percent"])` unchecked, and `charge` applies whatever the row contains. `discount_engine.validate_percent` implements exactly the §4 rule — and has **zero callers** (grep: only its definition). Worse, `validate_percent` is the *only* reader of `MAX_DISCOUNT_PERCENT`, so the cap constant — old 50 or new 30 — is enforced by nothing at all: the FIN-88 policy change (billing.py:11) is currently a comment edit.
- **Evidence:** Probe: `percent=150` accepted → `charge("10.00")` records `amount=-500, total=-525` (a negative charge). `percent=-50` accepted → `amount=1500` (a 50% *surcharge*). A pre-existing 50% code also still applies in full. Also unhandled at the boundary: a malformed `percent` raises a raw `ValueError`/`KeyError`.
- **Verdict:** CONFIRMED — reproduced end-to-end through the public API; `grep -rn validate_percent` shows no call site; independently re-found by the second finder pass.
- **Why Critical:** Violates invariants §4 outright, and ships a money path that writes negative and inflated charge entries to the ledger — wrong financial data on a directly reachable path, plus a description that asserts a safety property the code does not have.
- **Fix:** Call `validate_percent` (or an equivalent bounds check) in `api_create_discount` and reject out-of-range/malformed percents with a clear error before the row is stored. Per CLAUDE.md ("Reuse helpers in app/util.py before writing new parsing or validation code"), the validator arguably belongs in `app/util.py` beside `parse_money`, which also removes the circular-import workaround inside `validate_percent`.
- **Cites:** `docs/invariants.md §4` ("Any percentage adjustment … is validated at the API boundary before it reaches billing"); `CLAUDE.md` helper-reuse rule.

#### C2 — Migration 002 is destructive with no `down()`, and the code still writes `plan`, never `tier`
- **Locator:** `flow: migrations/002_drop_plan.py:4-7 ↔ app/users.py:14`
- **What:** Two halves of one broken migration. (a) `002_drop_plan.py` pops `plan` from every user in a single forward step — no `down()`, not additive-first, no dual-read release, and the original `plan` values are discarded (everything not `"legacy"` collapses to `"standard"`), so the step is irreversible with data loss. (b) The application code was never moved to `tier`: `app/users.py:14` still writes `"plan": "free"` and nothing anywhere reads or writes `tier`. After running the migration, old users have `tier` and no `plan` while newly created users have `plan` and no `tier` — split-brain user records, and any reader of `u["plan"]` breaks for migrated users.
- **Evidence:** Probe: `hasattr(m002, "down") == False`; after `up()`, a migrated user is `{"tier": "standard"}` while a freshly created user is `{"plan": "free"}`. Note also: no `"legacy"` plan value exists anywhere in the codebase (only `"free"`), so the `"grandfathered"` branch is dead and the mapping's basis is unverifiable.
- **Verdict:** CONFIRMED — reproduced; the `tier` grep shows no application-code usage.
- **Why Critical:** Violates invariants §3 on every clause ("additive first; destructive steps only after a release with dual-read, and every migration ships a `down()`"), irreversibly damages data, and leaves the user schema inconsistent the moment the next signup happens. Cannot be shipped around.
- **Fix:** Split the migration out of this PR entirely (see M3). When it does ship: add `tier` additively with a `down()`, move the code to write/read `tier` (dual-read `plan` for one release), and only then drop `plan` in a later migration.
- **Cites:** `docs/invariants.md §3`; review axes 5l (irreversible migration → Critical/High).

### High (should fix before merge)

#### H1 — `find_user_by_email` contract change breaks `support.py`: unknown-email lookup now raises `TypeError`
- **Locator:** `flow: app/db.py:14-18 → app/support.py:6-10`
- **Changed anchor:** `app/db.py:18` (`raise NotFound(email)` → `return None`)
- **What:** The store's not-found signal changed from raising `NotFound` to returning `None`. The PR updated `billing.py` but not the other caller: `support.lookup` still wraps the call in `except NotFound` — which can no longer fire — then dereferences `u["id"]` on `None`. The description's claim "billing was updated to match" is true and is exactly the tell that the caller sweep stopped one file short.
- **Evidence:** Probe: `support.lookup("ghost@x.y")` raises `TypeError: 'NoneType' object is not subscriptable`. Base behavior returned `{"found": False}`.
- **Verdict:** CONFIRMED — reproduced; grep shows `support.py` is the only other caller.
- **Why High:** A previously working, reachable path (support console, not-found case — its designed-for case) now crashes. Also leaves `db.NotFound` and support's import of it as dead code (L2).
- **Fix:** Either update `support.lookup` to the `None` contract (`u is None → {"found": False}`) and delete `NotFound`, or — simpler — revert the contract change entirely: the claimed benefit ("simplifies the new discount code paths") is hollow, since `billing.charge` still handles the not-found case explicitly either way.
- **Cites:** no project rule needed — behavioral regression demonstrated against the base snapshot.

#### H2 — `create_user` dropped `normalize_email`: invariant §1 violated, mixed-case signups become unfindable
- **Locator:** `app/users.py:9-13`
- **Changed anchor:** the removal of `from .util import normalize_email` and the change to `"email": email.strip()`
- **What:** The base normalized (strip + lowercase) at the write path; the diff silently narrows this to `.strip()` only. Invariants §1: "Emails are stored lowercased and trimmed (`util.normalize_email` at every write path). All lookups assume canonical form; a non-canonical write breaks every reader." This is a removed guard with no replacement — and it is unrelated to discounts, so nothing in the PR's stated intent explains it.
- **Evidence:** Probe: `api_create_user({"email": "A@B.c"})` then `api_charge({"email": "a@b.c", …})` → `BillingError: unknown user`. On base, the same sequence succeeds.
- **Verdict:** CONFIRMED — reproduced against both snapshots.
- **Why High:** Every reader breaks for any user who signs up with mixed case: billing can't charge them, support can't find them. Silent, data-shaped, and grows with every signup until fixed — plus stored non-canonical rows will need a backfill.
- **Fix:** Restore `email = normalize_email(email)` in `create_user`.
- **Cites:** `docs/invariants.md §1`; `CLAUDE.md` ("Reuse helpers in app/util.py…").

#### H3 — Usage limits are never enforced: single-use codes are infinitely redeemable, and `api_redeem` is both uncalled and inverted
- **Locator:** `flow: app/billing.py:19-22 (no uses check) ↔ app/api.py:30-39 (api_redeem, uncalled)`
- **What:** Discounts carry `uses`/`max_uses` (default 1), but `charge` neither checks nor increments them — the counting logic lives in `api_redeem`, which no code calls (grep: zero call sites, no test). And `api_redeem` itself is wrong twice over: the guard is inverted (`if row is None or row["uses"] < row["max_uses"]` — should be `is not None and`), and the bare `except Exception: pass` swallows the resulting `KeyError`, so an **unknown code reports `{"redeemed": True}`**; the same swallow-all would hide any real increment failure while still reporting success. The comment "redemption must never fail the charge path" defends a connection to the charge path that does not exist.
- **Evidence:** Probe: a `max_uses=1` code applied on three consecutive charges, all discounted, `uses` stays 0; `api_redeem({"code": "NOPE"})` → `{"redeemed": True}` for a code that was never created.
- **Verdict:** CONFIRMED — both behaviors reproduced.
- **Why High:** Direct revenue loss on a reachable path — every "single-use" promo code is unlimited — plus an endpoint that reports success for nonexistent codes. The swallow-all `except` is precisely the fallback-that-masks-the-error anti-pattern.
- **Fix:** Enforce and increment `uses` inside `charge` where the discount is applied (atomically with the charge append); fix or delete `api_redeem` — as written it has no caller and no correct behavior to preserve. Remove the `except Exception: pass`.
- **Cites:** `docs/testing.md` ("limit exceeded" is a named required failure path); the swallow-all judged per the review's over-defensive-code axis (no project rule on exception handling — stated as such).

#### H4 — No failure-path tests for a changed money path; the top production risks are all uncovered
- **Locator:** `tests/test_discounts.py` (whole file)
- **What:** `app/billing.py` changed, which per CLAUDE.md "requires failure-path tests"; `docs/testing.md` requires "invalid input, not-found, limit exceeded — not just the happy path" for money paths. The PR adds exactly one test: a valid 10% discount. The top three production risks this PR carries — out-of-range percent (C1), the plan/tier migration (C2), and usage-limit enforcement (H3) — have no covering test; nor do unknown-code charge, `api_redeem`, or `api_apply_credit`.
- **Evidence:** `tests/test_discounts.py:13-19` is the only new test; the suite passes 4/4 while probes demonstrate C1/H1/H2/H3 — direct proof the suite doesn't cover the failure modes.
- **Verdict:** CONFIRMED — by inspection of the test file against the named risks.
- **Why High:** A missing test for a named top-3 risk is High per the severity rubric, and here it is a documented project requirement, not a preference. The green suite actively misleads: it certifies a build that writes negative charges.
- **Fix:** Add failure-path tests alongside the fixes: invalid/boundary percent (0, 31, 100, 150, −1), unknown code at charge, `max_uses` exhaustion, unknown-email support lookup, and a migration round-trip test.
- **Cites:** `CLAUDE.md` ("Every change to app/billing.py requires failure-path tests"); `docs/testing.md` failure-path rule.

### Medium (worth fixing now; acceptable as a committed follow-up)

#### M1 — `api_apply_credit`: an undeclared endpoint that bypasses `parse_money`'s negative-amount guard and writes user-less ledger entries
- **Locator:** `app/api.py:42-49`
- **What:** The PR description never mentions credits, yet the diff adds an API-boundary function that strips a leading `-` and negates — deliberately circumventing `parse_money`'s documented contract ("Raises ValueError for … negative input — money enters the system as a non-negative amount; adjustments are modeled explicitly"). The entries it appends have `user_id: None` and `total == amount` (no tax treatment), a shape no other charge entry has, and there is no validation, cap, or test.
- **Evidence:** Probe: `api_apply_credit({"amount": "-5.00"})` → `{"user_id": None, "amount": -500, "total": -500}` appended to `STORE.charges`. Any consumer that groups charges by `user_id` will mis-attribute or crash on it.
- **Verdict:** CONFIRMED — reproduced; contract quoted from `app/util.py:7-11`.
- **Why Medium:** Unreviewed money-mutation surface smuggled in without a stated requirement. (Ranked Medium not High only because the fixture has no auth model anywhere to violate; the right fix is removal, not hardening.)
- **Fix:** Drop it from this PR. If credits are a real requirement, model them explicitly (a signed adjustment type attached to a user) in their own reviewed change.
- **Cites:** `app/util.py` docstring contract; `docs/invariants.md §4` (credits are named as boundary-validated adjustments).

#### M2 — The discount "engine" is dead machinery: registry, env-var backend, and ABC serve one strategy that billing imports directly
- **Locator:** `app/discount_engine/__init__.py:10-35`
- **What:** The module ships a strategy registry, a `@register` decorator, an ABC, and env-var backend selection (`DISCOUNT_ENGINE_BACKEND`) — and none of it is on the runtime path: `billing.py:2` imports `PercentDiscount` directly, and `get_strategy` / `STRATEGY_REGISTRY` have zero callers. Registration only happens as a side effect of billing's import — `discount_engine/__init__.py` never imports `percent`, so a standalone `get_strategy()` raises `KeyError: 'percent'` even for the default backend. `validate_percent` (also uncalled — C1) needs a circular-import workaround to reach `billing.MAX_DISCOUNT_PERCENT`. A process-global env var is also the wrong shape even for the stated future: discount kind is a property of each code (this row is percent, that one BOGO), not of the deployment.
- **Evidence:** Probe: with `DISCOUNT_ENGINE_BACKEND=bogus` set, charges still apply percent discounts (registry ignored); `get_strategy()` then raises a bare `KeyError`. Grep confirms no callers.
- **Verdict:** CONFIRMED (Occam candidate — the cost is concrete: a dead moving part, an env var that promises behavior it doesn't deliver, and a pattern adjacent code will copy). Walked against the stated constraint — "upcoming fixed-amount and BOGO discounts" — which justifies at most a `kind` field on the discount row, not a registry; no scheduled requirement was found in docs or history.
- **Why Medium:** Concrete citable cost per the promotion rule: an operational knob (env var) that silently does nothing, plus dead abstraction that misleads the next author about how discounts are selected.
- **Fix:** Collapse to a single function, e.g. `apply_percent_discount(amount_cents, percent) -> int` (in `util.py` or a flat `discounts.py`), keeping the integer arithmetic. Delete the registry, ABC, and env var. When a second discount kind actually lands, branch on a per-row `kind` field.
- **Cites:** `CLAUDE.md` helper-reuse rule; Occam pass (speculative generality — no project rule mandates plugin architecture, stated as such).

#### M3 — Scope sprawl: one PR bundles the feature, a finance-policy change, a destructive migration, and two undeclared changes
- **Locator:** `scope: PR`
- **What:** Five separable concerns travel together: (1) the discount feature; (2) the cap change 50→30 (declared, policy-driven — Q1); (3) the plan→tier migration (declared, destructive — C2); (4) `api_apply_credit` (undeclared — M1); (5) the `source` field on users (undeclared, an unvalidated free-form payload value stored on every user, `app/users.py:9,15`). The two undeclared changes mean the description does not describe the diff; the destructive migration means a revert of the feature also reverts a schema step.
- **Evidence:** Diff-vs-description comparison; (4) and (5) appear in no bullet of the commit message.
- **Verdict:** CONFIRMED — by enumeration.
- **Why Medium:** Reviewability and reversibility: this PR cannot be reverted or bisected as a unit, and undeclared changes dodge review scrutiny (M1 proved the point).
- **Fix:** Split into: discounts feature; cap change (with FIN-88 reference); migration series (per C2, if actually scheduled); credits (if actually required); `source` attribution (if actually required).
- **Cites:** `docs/invariants.md §3` for the migration-bundling half; no project rule on PR atomicity — judged against standard review practice, stated as such.

### Low (defer)
- **L1** [`app/billing.py:11`] The rewritten `MAX_DISCOUNT_PERCENT` comment dropped the "validated at the API boundary (§4)" anchor — restore it with the fix for C1.
- **L2** [`app/db.py:4`, `app/support.py:1`] `NotFound` is dead code under the new contract; resolve with H1 (delete it or restore raising semantics).
- **L3** [`app/api.py:26`] `api_create_discount` silently overwrites an existing code, resetting its `uses` counter — reject or explicitly upsert. *(Found in the gap sweep.)*
- **L4** [`app/billing.py:23`] `total = int(amount * (1 + TAX_RATE_BP / 10_000))` is float math in a money path (invariants §2). Pre-existing and unchanged, but in a touched function; probe found no rounding divergence from integer math for amounts ≤ $2,000, so impact is currently nil. Prefer `amount * (10_000 + TAX_RATE_BP) // 10_000` when next touching this line.

## Questions

- **Q1** [`app/billing.py:11`] FIN-88 and the finance sign-off can't be verified from this checkout — can you link it? And what should happen to already-issued codes in the 31–50% range once validation (C1) starts enforcing the new 30 cap: honored, capped, or invalidated?
- **Q2** [`app/api.py:30`] SUPPORT-311 isn't accessible — was redemption tracking (`api_redeem`) meant to be called by `charge`, by an external caller, or is it half of an abandoned design? The answer decides whether H3's fix is "wire it in" or "delete it."
- **Q3** [`app/billing.py:20-22`] A charge with an unknown (or, post-fix, exhausted) discount code silently proceeds at full price. Is that the intended product behavior, or should it be a `BillingError` so the customer isn't quietly charged more than they expected?

## Suggestions

#### S1 — Record the discount on the charge entry
- **Locator:** `app/billing.py:24`
- **What:** Store `discount_code` and the pre-discount amount in the charge entry when a discount applies.
- **Why it'd be better:** Support (the requesters, per SUPPORT-311) can see *why* an amount is lower; refunds and audits don't have to reverse-engineer the percentage from two numbers.

#### S2 — Normalize emails at the API boundary for lookups too
- **Locator:** `app/api.py:13`, `app/support.py:7`
- **What:** Pass lookup emails through `util.normalize_email` before calling `find_user_by_email` (complements H2, which fixes the write path).
- **Why it'd be better:** §1 says lookups assume canonical form, but callers feed raw payload strings; normalizing at the boundary makes charge/support lookups case-robust for free.

## Gaps

- No documentation of the new API surface (`api_create_discount`, `api_charge`'s `discount_code`) — README/docs unchanged.
- No manual-test notes in the PR description; with the suite being happy-path only (H4), nothing attests the failure paths were ever exercised.

## Known limitations

- The in-memory `Store` has no concurrency or persistence semantics, so read-modify-write races on `uses` (once H3 wires it) weren't assessed — acceptable for this fixture; note it wherever the store grows a real backend.
- Discount is applied *before* tax, so tax is computed on the discounted base. Taken as intended (it matches the common rule); worth one line in the code comment.

## What was done well

- [`app/discount_engine/percent.py:9-10`] `apply` is pure integer arithmetic (`amount - (amount * percent) // 100`) — exactly what invariants §2 demands; the floor-of-discount rounding is deterministic and errs in the house's favor.
- [`app/billing.py:15`] `discount_code` is an optional parameter with a `None` default, so the `charge` signature stays backward-compatible for existing callers and tests.
- [`app/billing.py:19-23`] Discount is applied before tax in a single, readable sequence — the money flow through `charge` is easy to audit.
- [`tests/test_discounts.py:8-12`] The new test resets all three stores in `setUp`, following the established convention of the existing suites.
- [`migrations/002_drop_plan.py:6`] `u.pop("plan", None)` with a default makes the (otherwise flawed — C2) migration at least re-runnable without crashing.

## Verified

- **The problem is real:** at merge-base `5dac977`, `STORE.discounts` exists but no code path creates or redeems a discount — the feature genuinely doesn't exist in base. Not a reimplementation of an existing utility.
- **Test suite:** `python3 -m unittest discover tests` passes 4/4 on the branch (and the pre-existing tests still pass), for what happy-path coverage is worth (H4).
- **Tax float math (load-bearing §2 assumption on the touched line):** probed `int(a * 1.05)` against `a * 105 // 100` for every amount up to 200,000 cents — zero divergences; L4 is currently latent, not active.
- **`PercentDiscount.apply` bounds:** for in-range percents (1–30) output is always in `[0, amount]`; the negative/oversized failures in C1 come solely from missing validation, not from the arithmetic.
- **Redeem exhaustion branch:** `api_redeem` on an existing, exhausted code does correctly return `{"redeemed": False}` — the inversion in H3 bites only on the `None` side.
- **Approach-gate constraint hunt:** ticket references (SUPPORT-311, FIN-88) are not resolvable from this checkout; docs and git history contain no constraint explaining the engine, the migration bundling, or the contract change — hence findings rather than accepted divergences.
- **Independent finder pass:** a second, defect-first reviewer was run over the same diff (11 candidates). All deduped into the findings above; two sharpened the evidence — the cap constant having no effective reader (folded into C1) and the registry populated only by import side effect (folded into M2). Nothing surfaced beyond this list.

## Not reviewed

- **Architecture axis:** no `docs/architecture.md` exists; layering judged only against CLAUDE.md. No architecture findings were needed for this diff.
- **Data-privacy axis:** no `docs/privacy.md`; the diff logs nothing and stores no new PII (the `source` field is a channel tag — its scope problem is M3). CLAUDE.md's email rule was checked: no raw emails leave the users table in this diff.
- **Dependency audit:** stdlib only, no dependency manifests — nothing to audit.
- **CI:** no CI configuration or remote in this fixture; `gh pr checks` not applicable. Local test run substituted.
- **`feature/audit-log`:** a sibling in-flight branch; out of scope (noted only that it does not call `find_user_by_email`, so H1 does not cross it).

---

*Review conducted with the `examine` skill, full mode: intent extracted from the commit message (the PR description); rulebook read in full (`CLAUDE.md`, `docs/invariants.md`, `docs/testing.md`); baseline approaches sketched before the diff was opened; every Medium+ finding carries a probe- or grep-backed CONFIRMED verdict; primary checkout left untouched (clean tree on `feature/discounts` @ `0bcf605`, verified before and after).*

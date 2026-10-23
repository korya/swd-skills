# Examine: feat(discounts): Add discount codes with API validation (branch `feature/discounts` → `main`, 216d337)

Mode: **full** (user asked for a rigorous pre-merge review; the diff also touches payments and ships a migration). Target: `git diff main...HEAD` (merge-base comparison; working tree clean, so nothing extra). Verification: one independent read-only subagent per Medium+ candidate; the host's built-in review ran in a subagent as an additional candidate source (all 12 of its findings dedup into the list below).

## Headline

**Hold.** The PR's central claim is false: discount percent is not validated anywhere, so a 500% code produces a negative charge. Beyond that, the PR bundles five unrelated changes (a destructive migration, a `db` contract change that crashes the support console, a `users.py` rewrite that breaks email canonicalisation, an undisclosed credit endpoint, and a speculative strategy engine) with the discounts feature, and its only test is one happy path. Nothing here needs a redesign; it needs to be split, wired, and tested.

## Approach fit

**APPROACH DISPUTED.** Before reading the diff I sketched the obvious shape for "percentage discount codes redeemed at charge time" against this codebase: `api_create_discount` validates `1 <= percent <= billing.MAX_DISCOUNT_PERCENT` at the API boundary (§4) and writes to the already-existing `STORE.discounts`; `billing.charge` grows an optional `discount_code` and applies `amount - amount*pct//100` in integer cents; failure-path tests per `docs/testing.md`. About 30 lines and two files.

The diff does that core (minus the validation) and additionally: lowers the cap 50→30, adds a strategy registry with an env-var backend selector, drops `users.plan` via a one-way migration, changes `Store.find_user_by_email` to return `None`, removes `normalize_email` from `create_user`, adds a `source` field to users, and adds `api_apply_credit` and `api_redeem`. The description gives a constraint for only two of these (FIN-88 for the cap, "upcoming fixed-amount and BOGO" for the engine), and neither is verifiable from the repo: no ticket, doc, or history mentions FIN-88, SUPPORT-311, BOGO, `tier`, or a backend selector. The rest have no stated constraint at all.

Because the gate did not pass, every line-level finding below is provisional on the author's answer to **Q1–Q4**; the Critical and High findings stand regardless of that answer.

## Issues

### Critical (must fix before merge)

#### C1 — Discount percent is never validated; a 500% code yields a negative charge
- **Locator:** `flow: app/api.py:22 (api_create_discount) → app/billing.py:19-22 (charge) → app/discount_engine/percent.py:10`
- **Changed anchor:** `app/api.py:17-27` (new), `app/billing.py:11` (comment "validated at the API boundary (§4)" deleted), `app/discount_engine/__init__.py:26-30` (`validate_percent`, never called)
- **What:** `api_create_discount` stores `int(payload["percent"])` with no bounds check. `validate_percent` exists but has zero call sites. `charge` applies whatever is stored. The PR description's first bullet ("Discount percent is validated at the API boundary per docs/invariants.md §4") does not describe the shipped code.
- **Evidence:** Probe in a detached worktree, user `a@b.c`, charge `"10.00"`: percent 500 → `{'amount': -4000, 'total': -4200}`; percent -50 → `{'amount': 1500, 'total': 1575}` (a surcharge); percent 0 and 31 both accepted. `grep -rn validate_percent` hits only its definition.
- **Verdict:** CONFIRMED — independent verifier reproduced all four rows and found no guard between payload and store.
- **Why Critical:** Negative and inflated charges are direct money loss or over-billing on a reachable path, and §4 is a hard invariant the PR claims to satisfy. The dead helper means the new 30% cap is also unenforced (H-level on its own).
- **Fix:** In `api_create_discount`, call `validate_percent(percent)` (or inline `1 <= percent <= billing.MAX_DISCOUNT_PERCENT`) and raise a `ValueError`/API error on failure, before writing the row. Parse `percent` through a `util` helper rather than bare `int()` (CLAUDE.md: reuse `app/util.py`). Add failure-path tests for 0, 31, 500, -50, `"abc"`. Restore the §4 pointer comment on `MAX_DISCOUNT_PERCENT`.
- **Cites:** `docs/invariants.md §4 (Percentage adjustments)`; `CLAUDE.md` ("Reuse helpers in app/util.py before writing new parsing or validation code")

### High (should fix before merge)

#### H1 — `support.lookup` now crashes on every unknown email
- **Locator:** `flow: app/db.py:14-18 (find_user_by_email) → app/support.py:6-10 (lookup)`
- **Changed anchor:** `app/db.py:14-18` (`raise NotFound(email)` → `return None`)
- **What:** The description says "billing was updated to match" the new `None` contract. `support.lookup`, the other caller, was not: its `except NotFound` is now dead and `u["id"]` runs on `None`.
- **Evidence:** `support.lookup("nobody@x.y")` → `TypeError: 'NoneType' object is not subscriptable` (main returns `{"found": False}`). Callers enumerated by grep: `billing.charge` (handles `None`), `support.lookup` (does not). No test exercises `support.lookup`.
- **Verdict:** CONFIRMED — verifier reproduced and enumerated all callers.
- **Why High:** The support console's documented not-found path becomes an unhandled exception on the first lookup of an unknown or mistyped email — a user-facing outage introduced by an unrelated contract change.
- **Fix:** Either revert the `db.py` change (the discount code never calls `find_user_by_email`, so the stated simplification is not real) or update `support.lookup` to `if u is None: return {"found": False}` and delete the now-dead `NotFound` class. Add a `support` not-found test either way.
- **Cites:** `docs/testing.md` ("lookup paths require failure-path tests ... not-found")

#### H2 — `create_user` drops email canonicalisation; mixed-case signups become unfindable
- **Locator:** `app/users.py:10-14`
- **Changed anchor:** `app/users.py:5,10,13` (`from .util import normalize_email` and `email = normalize_email(email)` removed; `"email": email.strip()` added)
- **What:** `normalize_email` is `strip().lower()`; the replacement keeps the strip and drops the lower. `find_user_by_email` compares exactly. Nothing re-establishes lowercasing anywhere (`grep -rn '\.lower()\|normalize_email' app tests` hits only `util.py`). `normalize_email` now has zero callers.
- **Evidence:** `create_user("A@B.c", ...)` stores `'A@B.c'`; `billing.charge("a@b.c", "1.00")` → `BillingError: unknown user`; `charge("A@B.c", ...)` succeeds. On main the same signup stores `'a@b.c'` and both lookups succeed.
- **Verdict:** CONFIRMED — verifier reproduced on HEAD and on a `git archive main` snapshot.
- **Why High:** §1 states the consequence outright: "a non-canonical write breaks every reader." Every user who signs up with any uppercase letter after this ships cannot be charged or found by canonical lookups, and the bad rows persist until backfilled. The change is unrelated to discounts and unexplained.
- **Fix:** Restore `email = normalize_email(email)` in `create_user`. If `source` must stay, add it without touching the email line.
- **Cites:** `docs/invariants.md §1 (Canonical emails)`; `CLAUDE.md` ("Reuse helpers in app/util.py")

#### H3 — Discount usage limits are not enforced anywhere; `api_redeem` reports success for unknown codes
- **Locator:** `flow: app/api.py:30-39 (api_redeem) ↔ app/billing.py:19-22 (charge)`
- **Changed anchor:** both hunks are new in this diff
- **What:** Two halves of one missing feature. (a) `api_redeem`'s condition `row is None or row["uses"] < row["max_uses"]` sends an unknown code into the "redeem" branch, where `STORE.discounts[code]["uses"] += 1` raises `KeyError`, the bare `except Exception: pass` swallows it, and the endpoint returns `{"redeemed": True}`. (b) `charge` never reads `uses`/`max_uses`, never increments, and never calls `api_redeem`, so the counter has no effect on real charges. The comment "redemption must never fail the charge path" describes a path that does not exist.
- **Evidence:** `api_redeem({"code": "NOPE"})` → `{'redeemed': True}`. Code `ONE` with `max_uses: 1`: three `api_charge(..., discount_code="ONE")` calls each return `amount=900`, `uses` stays 0; after `api_redeem` exhausts it, `charge` still discounts.
- **Verdict:** CONFIRMED — verifier reproduced both halves; `grep -rn 'uses\|redeem'` finds no other enforcer.
- **Why High:** A single-use code is reusable without limit at the point where money moves; the redeem endpoint lies about unknown codes to whoever calls it. Both are silent (nothing logged, tests green).
- **Fix:** Decide where redemption lives. Simplest: in `charge`, after `parse_money`, look up the row, reject (`BillingError`) when missing or `uses >= max_uses`, apply the discount, and increment `uses` only after the charge entry is appended. Delete `api_redeem` or make it a thin wrapper that returns `False` for `None` and never catches broad exceptions. Add tests for unknown code, exhausted code, and the increment.
- **Cites:** `docs/testing.md` ("limit exceeded" failure path required)

#### H4 — Migration 002 is one-way, destructive in the same PR, and leaves two user shapes live
- **Locator:** `migrations/002_drop_plan.py:4-7`
- **What:** `up()` pops `plan` and writes `tier` in a single step; there is no `down()` (001 has one); no release with dual-read precedes it; `create_user` (`app/users.py:14`) still writes `"plan": "free"` and never `tier`; nothing in `app/` or `tests/` reads `tier`; the only `plan` value ever written is `"free"`, so the `"legacy" → "grandfathered"` branch cannot fire; `tests/test_users.py:13` still asserts on `plan`. None of this relates to discount codes.
- **Evidence:** `hasattr(m002, "down")` → `False`. After `up(STORE)`: migrated user `{'tier': 'standard'}` with no `plan`; a user created afterwards `{'plan': 'free'}` with no `tier`.
- **Verdict:** CONFIRMED — verifier checked every sub-claim against main and HEAD.
- **Why High:** Irreversible by construction (no `down()`), and it splits the store into two incompatible row shapes that any future `u["plan"]` or `u["tier"]` reader will `KeyError` on. §3 names exactly this pattern as forbidden.
- **Fix:** Pull the migration out of this PR. When it returns: add `tier` additively (write both in `create_user`), ship `down()`, run a dual-read release, then drop `plan` in a later migration. Update `test_users.py` with it.
- **Cites:** `docs/invariants.md §3 (Reversible migrations)`

#### H5 — The billing change ships with no failure-path tests; the top production risks are uncovered
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The only new test asserts one 10% happy path. CLAUDE.md makes failure-path tests mandatory for any `app/billing.py` change; `docs/testing.md` names the required paths (invalid input, not-found, limit exceeded). None exist for: percent over cap / ≤ 0 (C1), unknown code (M2), exhausted `max_uses` or redeem of an unknown code (H3), `support.lookup` not-found (H1), mixed-case email (H2), negative credit (M1), migration 002 (H4). The suite is green (4/4) while all of those paths are broken.
- **Evidence:** `git diff main...HEAD --stat -- tests` shows one file, one method. Verifier grepped tests for `max_uses|redeem|apply_credit|validate_percent|MAX_DISCOUNT|migrat|assertRaises`: only the pre-existing `assertRaises(BillingError)` in `test_billing.py`.
- **Verdict:** CONFIRMED.
- **Why High:** Each of the top-three production risks of this PR (negative charges, unlimited code reuse, user lookup breakage) has no covering test; the rule requiring them is explicit.
- **Fix:** Add `tests/test_discounts.py` cases for each path above and a `tests/test_support.py` not-found case; mirror `app/` layout per `docs/testing.md`.
- **Cites:** `CLAUDE.md` ("Every change to app/billing.py requires failure-path tests"); `docs/testing.md` ("Money and lookup paths require failure-path tests (invalid input, not-found, limit exceeded) — not just the happy path")

### Medium (worth fixing now; acceptable as a follow-up)

#### M1 — `api_apply_credit` is undisclosed, bypasses `parse_money`'s negative guard, and writes ownerless ledger rows
- **Locator:** `app/api.py:42-50`
- **What:** A new endpoint not mentioned in the description. It mirrors `parse_money`'s own `startswith("-")` check to route around the guard whose docstring says "money enters the system as a non-negative amount; adjustments are modeled explicitly". It appends to `STORE.charges` with `user_id: None` (the payload has no user field) and `total = cents` with no tax, so credit rows are unattributable and shaped differently from charge rows.
- **Evidence:** `api_apply_credit({"amount": "-5.00"})` → `{'user_id': None, 'amount': -500, 'total': -500}` in `STORE.charges`; `api_charge` for the same 5.00 gives `total: 525`.
- **Verdict:** CONFIRMED — verifier reproduced; no doc or test sanctions ownerless credits.
- **Why Medium:** Wrong financial data on a reachable path, but the endpoint is not wired into any described flow yet, and the fix is likely removal.
- **Fix:** Drop it from this PR. If credits are wanted, model them explicitly (a `credit(user_id, cents)` in `billing` using `parse_money` on a positive amount with a sign carried by the operation type), attributed to a user id per CLAUDE.md.
- **Cites:** `app/util.py:parse_money` docstring; `CLAUDE.md` ("reference users by id"; "Reuse helpers in app/util.py")

#### M2 — Unknown or mistyped discount code is silently ignored and the customer pays full price
- **Locator:** `app/billing.py:19-22`
- **What:** `if row:` has no else branch, raise, or flag on the returned entry. A rejected code produces output byte-identical to no code.
- **Evidence:** `api_charge({... "discount_code": "SAVE1O"})` (typo) → `{'amount': 1000, 'total': 1050}`, same as with no code.
- **Verdict:** CONFIRMED — verifier found no doc or test establishing silent fall-through as intended; the same PR's `api_redeem` does signal rejection, so the author evidently considers rejection visible elsewhere.
- **Why Medium:** The customer-facing redemption point ("customers redeem them at charge time") cannot tell the customer the code was rejected; a wrong-price charge goes through instead of failing fast.
- **Fix:** Raise `BillingError("unknown discount code")` (or return a `discount_applied` field) when the code is given but not found. Folds naturally into the H3 fix.
- **Cites:** `docs/testing.md` ("not-found" failure path required)

#### M3 — The PR bundles six unrelated changes and cannot be reverted as a unit
- **Locator:** `scope: PR`
- **What:** One commit carries: discount codes (the feature), the cap change, the strategy engine, migration 002, the `db` contract change, the `users.py` rewrite with a new `source` field, and two extra endpoints. Reverting the discounts feature would also revert a migration and a data-model change; cherry-picking a fix to any one of them drags the others.
- **Evidence:** `git diff --stat main...HEAD` — eight files, of which `db.py`, `users.py`, `migrations/002_drop_plan.py` and `api_apply_credit` have no dependency on discounts (verified: nothing in `discount_engine/` or the discount path in `charge` calls `find_user_by_email` or touches `plan`/`source`).
- **Verdict:** CONFIRMED.
- **Why Medium:** Reversibility and reviewability. Three of the Highs above exist because side changes rode along unreviewed.
- **Fix:** Split: (1) discounts + validation + tests; (2) cap change with FIN-88 reference; (3) users `source` field; (4) `tier` migration done per §3; (5) credits, if wanted. Drop the `db` contract change and the engine unless Q1/Q4 supply a reason.

### Low (defer)
- **L1** [`app/api.py:17-27`] `api_create_discount` silently overwrites an existing code and resets `uses` to 0; `int(payload["percent"])` raises a bare `ValueError` for `"10.5"` or `"abc"` instead of an API-level error.
- **L2** [`app/db.py:4,14`] `NotFound` is now raised nowhere but still imported by `support.py`; the `-> dict` return annotation was dropped rather than changed to `Optional[dict]`.
- **L3** [`app/discount_engine/__init__.py:33-35`] `get_strategy` raises a raw `KeyError` on an unknown `DISCOUNT_ENGINE_BACKEND` value; the env var is undocumented.

## Questions

- **Q1** [`app/billing.py:11`] Where is FIN-88 recorded, and does the 50→30 cap apply retroactively to codes already created at 31–50%? Nothing enforces either today (C1), so the constant is currently decorative.
- **Q2** [`app/discount_engine/__init__.py`] Are fixed-amount and BOGO discounts actually scheduled (ticket, quarter)? If not, see S1.
- **Q3** [`app/users.py:15`] Why does a discounts PR add a `source` field to users, what values are allowed, and is `"web"` the right default for API-created users?
- **Q4** [`app/db.py:14`] The description says returning `None` "simplifies the new discount code paths" — which path? The discount code never calls `find_user_by_email`.
- **Q5** [`app/billing.py:23`] The charge entry records the discounted `amount` but neither the code applied nor the pre-discount amount. Is finance reconciling discounts somewhere else, or should the row carry `discount_code`/`list_amount`?
- **Q6** [`scope: PR`] Does SUPPORT-311 ask for `max_uses`, a separate redeem endpoint, or credits, or only for percentage codes at charge time?

## Suggestions

#### S1 — Collapse `discount_engine` into one function in `billing`
- **Locator:** `app/discount_engine/__init__.py`, `app/discount_engine/percent.py`
- **What:** Replace the ABC, `@register` decorator, `STRATEGY_REGISTRY`, env-var selector and `get_strategy` with `def apply_percent_discount(amount_cents: int, percent: int) -> int` in `billing.py`, and move `validate_percent` next to `MAX_DISCOUNT_PERCENT`.
- **Why it'd be better:** One implementation, zero callers of the registry (`billing.py:2` imports `PercentDiscount` directly, bypassing its own engine), a new operational knob (`DISCOUNT_ENGINE_BACKEND`) nobody reads, and a lazy `from ..billing import` to dodge a circular import that would not exist without the package. Walked against constraints: §2 (integer cents — satisfied by the one-liner), §4 (validation at the API boundary — easier when the validator lives beside the cap), and the description's "upcoming fixed-amount and BOGO" (no ticket, doc, or history found; if Q2 produces one, add the abstraction when the second strategy lands). Simplicity here is fewer concepts and failure modes, not fewer lines.
- **Sketch:** `return amount_cents - (amount_cents * percent) // 100` (the existing `percent.py:10` body, already correct).

#### S2 — Make the tax total integer arithmetic while the function is open
- **Locator:** `app/billing.py:23`
- **What:** `int(amount * (1 + TAX_RATE_BP / 10_000))` → `amount * (10_000 + TAX_RATE_BP) // 10_000`.
- **Why it'd be better:** Pre-existing on main, so not an Issue against this PR, but it is the one float in a money path (§2, CLAUDE.md), it sits in the function this PR rewrites, and it now receives discounted (and, until C1 is fixed, negative) amounts where `int()` truncates toward zero while `//` floors. A probe over 0–99999 cents found no divergence today; the fix removes the undefined rounding rule rather than a known wrong total.

#### S3 — Record the discount on the charge row
- **Locator:** `app/billing.py:24`
- **What:** Add `"discount_code": discount_code` and `"list_amount": <pre-discount cents>` (or `"discount_cents"`) to `entry`.
- **Why it'd be better:** Reconciliation and support can see which code was applied and what it cost without re-deriving it; also makes M2's "was it applied?" answerable from the response. Depends on Q5.

## Gaps
- No manual-test plan or steps in the description; the new endpoints (`api_create_discount`, `api_redeem`, `api_apply_credit`) and the `DISCOUNT_ENGINE_BACKEND` variable are undocumented in `README.md` or `docs/`.
- `tests/` does not mirror `app/` for the new modules (`docs/testing.md`): no `test_support.py`, `test_api.py`, or `test_discount_engine.py`.
- Commit message says "finance signed off, product notified" for FIN-88 with no link or date.

## Known limitations
- The store is in-memory, so concurrency (double-redeem races on `uses`) was not evaluated; if a real DB replaces `STORE`, the H3 increment needs to be atomic with the charge.
- `users._ids` is never reset in test `setUp`, so ids drift across tests. Pre-existing, harmless today.

## What was done well
- [`app/discount_engine/percent.py:10`] `amount_cents - (amount_cents * self.percent) // 100` is pure integer arithmetic with an explicit floor, exactly what §2 asks for; the merchant-favouring rounding is a defensible default.
- [`app/billing.py:14`] `discount_code: str = None` keeps `charge` backward compatible; both pre-existing `test_billing.py` cases pass untouched.
- [`app/billing.py:15-17`] The `None` contract change was at least propagated to `billing` with an explicit `BillingError`, preserving the existing failure-path test.
- [`tests/test_discounts.py:8-11`] `setUp` clears all three stores, including the new `discounts` dict, so tests stay independent.
- [commit message] The description enumerates its non-obvious decisions (cap change, engine, migration, `db` contract) rather than hiding them; that is what made this review tractable, even where the claims turned out not to match the code.

## Verified
- Problem is real in the base snapshot: `main` has `STORE.discounts` and `MAX_DISCOUNT_PERCENT` but no code path creates or applies a discount; `api_charge` takes only `email` and `amount`.
- Test suite on HEAD: `python3 -m unittest discover tests -v` → 4 tests OK (happy paths only).
- Import ordering: `import app.discount_engine`, `import app.billing`, and `import app.discount_engine.percent` each succeed first; the lazy `from ..billing import` inside `validate_percent` does not currently cause a cycle (candidate REFUTED by running all three orders).
- Float tax path: probe compared `int(amt * 1.05)` with `amt * 10500 // 10000` for discounted amounts; no divergence found in 0–99999 cents (host review probe), so S2 is hygiene, not a live wrong-total.
- `find_user_by_email` callers enumerated: `billing.charge` (handles `None`), `support.lookup` (does not — H1). No others.
- `if discount_code:` treats `""` as absent, consistent with `payload.get("discount_code")` returning `None`.
- Python semantics relied on: `int("10.5")` raises `ValueError` (confirmed by run); `//` floors toward negative infinity, which is why percent -50 inflates rather than truncates (confirmed by run).
- Discount is applied before tax, so tax is charged on the discounted amount — consistent with the usual treatment; no project rule either way.
- CLAUDE.md "never log or store raw emails outside the users table": the PR adds no email storage or logging outside `users` (`charges` rows carry `user_id` only; `api_apply_credit` stores no email).
- Constraint hunt for the step-4 divergence: `grep -rni 'FIN-88|SUPPORT-311|BOGO|fixed-amount|tier|backend'` over the repo and `git log --all -S tier` find nothing outside the diff itself. No constraint found; hence the disputed approach.

## Not reviewed
- 5e Architecture: no `docs/architecture.md` exists; layering judged only against the module boundaries visible in `main` (API → billing/users → db).
- 5h Privacy: no `docs/privacy.md`; the diff adds one non-PII field (`source`) and no logging, so no privacy finding was possible or needed.
- 5m Dependencies: none added or bumped (stdlib only).
- CI: no remote, no pipeline; `gh pr checks` not applicable.
- The sibling branch `feature/audit-log` and any migration runner (none exists in the repo; 001/002 are plain modules) were accepted as-is.
- Nothing was posted, pushed, or committed. Experiments ran in a detached worktree in the scratchpad; the primary checkout at `OUTPUT_DIR/repo` matches its recorded baseline (branch `feature/discounts`, HEAD 216d337, clean tree).

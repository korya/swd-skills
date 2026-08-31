# Examine: feat(discounts): Add discount codes with API validation (branch `feature/discounts` vs `main`)

**Mode:** quick, as requested. Note: the auto-selected mode would have been **full** — the diff
contains a migration and touches the payments path. Axes skipped by quick mode are listed under
*Not reviewed*; two of the Critical findings below surfaced through 5c/5k and would also have
been 5l findings in full mode.

**Target:** `git diff 79ef07d..c11dc93` (merge-base with `main`; no upstream configured, working
tree clean). 8 files, +129/−14. Tests at HEAD: 4/4 pass.

## Headline

**Hold.** The discount feature ships without the percent validation its own commit message
claims (C1), the branch silently drops email canonicalization for every new signup (C2), and it
bundles an irreversible, half-finished `plan`→`tier` migration that nothing in the feature
needs (C3). The branch violates three of the four documented invariants. Split it and fix the
discount path before opening the PR.

## Approach fit

The core discount path (create code at the API → store in `STORE.discounts` → apply at charge
time with integer math) matches the obvious approach. Everything else in the branch diverges
from it and I could not find a constraint that justifies any of it in the commit, the docs, or
the history:

- **Pluggable strategy engine** (`app/discount_engine/`) — justified by "upcoming fixed-amount
  and BOGO"; nothing is scheduled, and `billing.py:2` imports `PercentDiscount` directly, so the
  registry/env-var machinery has zero callers. Speculative; see S1.
- **`plan`→`tier` migration** — not part of SUPPORT-311 as described, no code reads `tier`.
  APPROACH DISPUTED for this part: what is it for, and why in this PR? (Q1)
- **`db.find_user_by_email` returns `None`** — commit says it "simplifies the new discount code
  paths", but no discount code path calls it. (Q2)
- **`api_apply_credit`, `api_redeem`, `source` field, removal of `normalize_email`** — not
  mentioned in the commit at all.

Findings on the discount path stand regardless. Findings on the bundled changes (C2, C3, H1,
H3) disappear if those changes are split out — which is the recommended fix for each.

## Issues

### Critical (must fix before merge)

#### C1 — Discount percent is never validated; 100%+ codes produce free or negative charges
- **Locator:** `flow: app/api.py:18-27 (api_create_discount) → app/billing.py:19-22 → app/discount_engine/percent.py:10`
- **What:** The commit says "Discount percent is validated at the API boundary per
  docs/invariants.md §4". `validate_percent` (`app/discount_engine/__init__.py:26-30`) exists
  but has no callers; `api_create_discount` does `int(payload["percent"])` and stores it.
  `MAX_DISCOUNT_PERCENT` (lowered to 30 per FIN-88) is therefore dead — the cap is not enforced
  anywhere.
- **Evidence:** Probe on a `10.00` charge: `percent=100` → `amount=0, total=0`;
  `percent=200` → `amount=-1000, total=-1050`; `percent=-50` → `amount=1500`. Also
  `percent="10.5"` raises an uncaught `ValueError` from `int()`.
- **Verdict:** CONFIRMED — grep shows `validate_percent` referenced only at its definition;
  probe reproduces the negative charge.
- **Why Critical:** Money path with an explicit invariant (§4) that the description claims is
  satisfied and is not. A single support-created code makes the product free or issues
  negative charges.
- **Fix:** Call the validator in `api_create_discount` and raise (e.g. `ValueError`/a
  `BillingError`) when it fails; parse `percent` through a helper in `app/util.py` per
  CLAUDE.md rather than bare `int()`. Add failure-path tests for `0`, `31`, `100`, `-1`,
  `"10.5"`. Consider a belt-and-braces assertion in `PercentDiscount.__init__` too — the
  invariant says the API boundary is the gate, so billing may trust it, but the strategy is
  the last thing that touches the money.
- **Cites:** `docs/invariants.md §4 (Percentage adjustments)`; `CLAUDE.md` "Reuse helpers in
  app/util.py before writing new parsing or validation code".

#### C2 — Email canonicalization removed from `create_user`; mixed-case signups cannot be charged
- **Locator:** `app/users.py:12`
- **Changed anchor:** the hunk that removes `from .util import normalize_email` and replaces
  `email = normalize_email(email)` with `"email": email.strip()`.
- **What:** Emails are now stored trimmed but not lowercased. Every lookup assumes canonical
  form (§1: "a non-canonical write breaks every reader"). Unrelated to discounts; not
  mentioned in the commit.
- **Evidence:** Probe: `api_create_user({"email": " A@B.C "})` stores `'A@B.C'`;
  `api_charge({"email": "a@b.c", ...})` → `BillingError: unknown user`;
  `support.lookup(" A@B.C ")` → `TypeError` (via H1).
- **Verdict:** CONFIRMED — probe reproduces; `normalize_email` now has no callers (grep).
- **Why Critical:** Violates a documented critical invariant on deploy; any customer who types
  an uppercase letter at signup becomes uncharge-able and un-lookup-able. Revenue loss with no
  error at write time.
- **Fix:** Restore `email = normalize_email(email)` in `create_user`. Add a test that creates
  `" A@B.C "` and charges `"a@b.c"` — the existing tests only use lowercase input, which is
  why they still pass.
- **Cites:** `docs/invariants.md §1 (Canonical emails)`; `CLAUDE.md` "Reuse helpers in
  app/util.py".

#### C3 — Migration 002 is destructive, has no `down()`, and the code still writes `plan` and never reads `tier`
- **Locator:** `flow: migrations/002_drop_plan.py:4-7 → app/users.py:14 → tests/test_users.py:13`
- **What:** `up()` pops `plan` and maps it lossily (`legacy`→`grandfathered`, everything else
  →`standard`; `free`, `pro`, etc. are collapsed). There is no `down()`. Meanwhile
  `users.create_user` still writes `"plan": "free"` and never writes `tier`; nothing in `app/`
  reads `tier`; `test_users.py:13` still asserts on `plan`.
- **Evidence:** Probe: after `up()`, existing user is `{'tier': 'standard'}` with no `plan`; a
  user created afterwards is `{'plan': 'free'}` with no `tier`. `hasattr(m, "down")` → `False`.
  `grep -rn tier app tests` → no matches.
- **Verdict:** CONFIRMED — probe shows split-brain; `down()` absent by inspection.
- **Why Critical:** Irreversible data loss on deploy (original `plan` values gone, no way
  back), directly against §3 ("additive first; destructive steps only after a release with
  dual-read, and every migration ships a `down()`"). Also unrelated to SUPPORT-311.
- **Fix:** Drop the migration from this PR. If `tier` is a real requirement, ship it as its own
  change: add `tier` alongside `plan`, dual-write in `create_user`, migrate readers, then a
  later migration drops `plan` — with a `down()`.
- **Cites:** `docs/invariants.md §3 (Reversible migrations)`.

### High (should fix before merge)

#### H1 — `support.lookup` crashes with `TypeError` for any unknown or non-canonical email
- **Locator:** `flow: app/db.py:14-18 → app/support.py:7-10`
- **Changed anchor:** `app/db.py:18` (`raise NotFound(email)` → `return None`)
- **What:** The commit says "billing was updated to match". `support.py` was not: it still
  wraps the call in `except NotFound`, which is now never raised, then dereferences `u["id"]`
  on `None`.
- **Evidence:** Probe: `support.lookup("nobody@x.y")` → `TypeError: 'NoneType' object is not
  subscriptable`. `grep NotFound` shows `support.py` as the only remaining consumer; `NotFound`
  itself is now dead code.
- **Verdict:** CONFIRMED — probe reproduces; 5d tracer found the unchanged call site.
- **Why High:** Outage of the support-console path on the most common input (a typo'd email).
  Not caught by any test — `tests/` has no `test_support.py`.
- **Fix:** Either revert the `db.py` change (nothing in the discount path needs it — see Q2), or
  update `support.lookup` to check `is None` and delete the now-unused `NotFound` class. Add a
  not-found test for `support.lookup` either way.
- **Cites:** `docs/testing.md` "Money and lookup paths require failure-path tests (…
  not-found …)".

#### H2 — Redemption limits are never enforced; `api_redeem` is disconnected from `charge` and its condition is inverted
- **Locator:** `flow: app/api.py:30-39 (api_redeem) ↔ app/billing.py:19-22 (charge)`
- **What:** `charge` applies a code without checking or incrementing `uses`/`max_uses`.
  `api_redeem` increments `uses` but applies nothing to any charge. And `api_redeem`'s
  condition `if row is None or row["uses"] < row["max_uses"]` enters the success branch for a
  nonexistent code; the resulting `KeyError` is swallowed by `except Exception: pass` and the
  function reports `{"redeemed": True}`. Re-creating a code with the same name also silently
  resets `uses` to 0 (`api.py:26`).
- **Evidence:** Probe: single-use code `ONE` (`max_uses=1`) applied on three successive charges,
  `amount=900` each time, `uses` stays `0`. `api_redeem({"code": "NOPE"})` on an empty store →
  `{'redeemed': True}`.
- **Verdict:** CONFIRMED — both behaviours reproduced.
- **Why High:** "Single-use" codes are unlimited on the only path that actually discounts money.
  The comment "redemption must never fail the charge path" describes a linkage that does not
  exist.
- **Fix:** Decide on one model. Simplest: delete `api_redeem`, and in `charge` (inside the
  `if row:` branch) reject when `row["uses"] >= row["max_uses"]` and increment `uses` on
  success. Refuse to overwrite an existing code in `api_create_discount`. Remove the
  `except Exception: pass`.
- **Cites:** `docs/testing.md` "limit exceeded" failure path; the inverted condition and
  swallowed exception are plain correctness, no project rule needed.

#### H3 — `api_apply_credit` writes arbitrary negative amounts with no user, bypassing `parse_money`'s guard
- **Locator:** `app/api.py:42-50`
- **What:** New, undisclosed endpoint. It strips a leading `-` and negates the parsed value,
  deliberately circumventing `parse_money`'s documented rejection of negative input
  (`app/util.py` docstring: "money enters the system as a non-negative amount; adjustments are
  modeled explicitly"). The entry has `user_id: None`, no tax, and lands in `STORE.charges`
  next to real charges.
- **Evidence:** Probe: `api_apply_credit({"amount": "-999999.00"})` →
  `{'user_id': None, 'amount': -99999900, 'total': -99999900}` appended to `charges`.
- **Verdict:** CONFIRMED.
- **Why High:** Unbounded credits attributable to nobody on a reachable path, and a charges
  ledger that other code will now have to defend against. Security review (5g) was skipped in
  quick mode; in full mode this would also be an authZ question.
- **Fix:** Remove from this PR. If credits are needed, model them explicitly (a `credits` store
  or a typed `kind` field, keyed by user id per CLAUDE.md), validated at the API boundary.
- **Cites:** `CLAUDE.md` "reference users by id"; `app/util.py` `parse_money` docstring.

#### H4 — No failure-path tests for the billing change; none of the top-3 production risks is covered
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The only new test is the 10% happy path. CLAUDE.md: "Every change to app/billing.py
  requires failure-path tests." The named risks — over-cap / negative percent (C1),
  non-canonical email (C2), migration split-brain (C3) — plus unknown code (M1), single-use
  reuse (H2) and support not-found (H1) have no test. The suite passes precisely because it
  only exercises lowercase emails and a valid percent.
- **Evidence:** `python3 -m unittest discover tests -v` → 4 tests, all happy-path; every probe
  above failed on first try against a green suite.
- **Verdict:** CONFIRMED.
- **Why High:** A missing test for a named top-3 risk; the project's own rule for `billing.py`
  changes.
- **Fix:** Add `tests/test_discounts.py` cases for invalid percent (0, 31, 100, -1, "10.5"),
  unknown code, exhausted code; `tests/test_users.py` case for mixed-case email round-trip;
  `tests/test_support.py` not-found case.
- **Cites:** `CLAUDE.md` "Every change to app/billing.py requires failure-path tests";
  `docs/testing.md` "Money and lookup paths require failure-path tests (invalid input,
  not-found, limit exceeded)".

### Medium (worth fixing now; acceptable as a follow-up)

#### M1 — Unknown discount code is silently ignored; customer is charged full price with no signal
- **Locator:** `app/billing.py:19-22`
- **What:** `if row:` falls through when the code does not exist. The charge succeeds at the
  undiscounted amount and the caller cannot tell the code was rejected.
- **Evidence:** Probe: `api_charge({..., "discount_code": "BOGUS"})` → `amount=1000`, no error,
  no field in the returned entry.
- **Verdict:** CONFIRMED.
- **Why Medium:** Wrong behaviour on an edge path that will generate support tickets ("I used
  the code and was charged full price"), and it is the not-found path docs/testing.md says
  must be tested.
- **Fix:** Raise `BillingError("unknown discount code")` (consistent with "unknown user"), or
  return the applied discount in the entry so the caller can see it was zero. Test it.
- **Cites:** `docs/testing.md` not-found failure path.

## Questions

- **Q1** [`migrations/002_drop_plan.py`] What ticket owns the `plan`→`tier` change, and is it
  meant to land with SUPPORT-311? Nothing in the branch reads `tier`.
- **Q2** [`app/db.py:18`] Which "new discount code path" needed `find_user_by_email` to return
  `None`? None of `api_create_discount`, `api_redeem`, or the discount branch of `charge` calls
  it — if none, revert and H1 disappears.
- **Q3** [`app/billing.py:11`] Is FIN-88 linkable? The cap change is unverifiable from here, and
  since the cap is not enforced (C1), does finance know 30% is currently advisory?

## Suggestions

#### S1 — Collapse `discount_engine/` into a single function until a second strategy is scheduled
- **Locator:** `app/discount_engine/__init__.py`, `app/discount_engine/percent.py`
- **What:** `STRATEGY_REGISTRY`, `register`, `get_strategy`, the `DISCOUNT_ENGINE_BACKEND` env
  var and the `DiscountStrategy` ABC have no callers — `billing.py:2` imports `PercentDiscount`
  directly, so the "pluggable" claim in the commit is not true of the code as written.
  `validate_percent` lives in the engine but must import from `billing` lazily to dodge a
  circular import — a sign it belongs in `app/util.py` next to `parse_money`.
- **Why it'd be better:** One fewer package, no env-var-selected behaviour to operate or
  document, no circular-import workaround, and the fixed-amount/BOGO work can introduce the
  abstraction when it actually has two implementations to abstract over. (Occam pass was not
  run in quick mode; this is the one deletion candidate visible from 5a.)
- **Sketch:** `def apply_percent_discount(amount_cents: int, percent: int) -> int: return
  amount_cents - (amount_cents * percent) // 100` in `billing.py`, and `parse_percent()` in
  `util.py` enforcing `1 <= p <= MAX_DISCOUNT_PERCENT`.

#### S2 — Split the branch before opening the PR
- **Locator:** `scope: PR`
- **What:** Four independent changes are bundled: discount codes (the feature), `plan`→`tier`
  migration, `find_user_by_email` semantics + `support` fallout, and `api_apply_credit` /
  `source` field. Only the first has a description that matches the code.
- **Why it'd be better:** Each piece gets a reviewer who can say yes to it on its own; a revert
  of one does not take the feature down with it; and C2/C3/H1/H3 stop being this PR's problem.

#### S3 — Keep an `Optional[dict]` return type on `find_user_by_email` if the `None` contract stays
- **Locator:** `app/db.py:14`
- **What:** The diff removed the `-> dict` annotation instead of changing it to
  `Optional[dict]` / `dict | None`.
- **Why it'd be better:** A type checker would have flagged `support.py:10` (H1).

## Gaps

- `source` field on users (`app/users.py:15`, `app/api.py:8`) is accepted unvalidated from the
  payload and is not mentioned in the commit.
- `db.NotFound` is now unused by `db.py` but still imported by `support.py`.
- No test for migration 002 (nor for 001; there is no migration test convention to cite).
- SUPPORT-311 and FIN-88 are referenced without links; neither could be read.

## Known limitations

- `billing.py:23` computes tax with a float (`amount * (1 + TAX_RATE_BP / 10_000)`), contrary
  to the letter of §2. Pre-existing and unchanged by this diff; probe found zero
  float-vs-integer mismatches for every cent value in [0, $50,000.00), so it is not a
  practical defect today. Worth an integer rewrite (`amount * (10_000 + TAX_RATE_BP) //
  10_000`) in a separate hygiene PR, not this one.

## What was done well

- [`app/discount_engine/percent.py:10`] `amount_cents - (amount_cents * self.percent) // 100`
  — integer-only arithmetic that rounds the discount down (in the merchant's favour), exactly
  what §2 asks for.
- [`app/api.py:12-15`, `app/billing.py:14`] `discount_code` is optional on both layers, so
  existing callers and `tests/test_billing.py` keep working unchanged.
- [`tests/test_discounts.py:8-11`] `setUp` clears all three stores, not just the one under
  test — avoids cross-test bleed through the shared `STORE`.
- [commit message] Every non-obvious decision is called out with a reason (cap change, engine,
  migration, db semantics). The structure is right even where the claims turned out to be
  false — it made this review much faster.

## Verified

- **Problem is real in the base snapshot:** at `79ef07d` there is no way to create or apply a
  discount; `STORE.discounts` and `MAX_DISCOUNT_PERCENT` exist but are unused.
- **Sketches before reading the diff:** (a) `api_create_discount` + validate via a `util`
  helper + optional `discount_code` on `charge` with integer math; (b) same, in a small
  `discounts.py` mirroring `users.py`; (c) a strategy engine, only if a second strategy is a
  stated constraint. The diff is (c) plus unrelated changes; see Approach fit.
- **REFUTED candidate — float tax rounding** (`billing.py:23`): exhaustive probe over
  [0, 5,000,000) cents shows `int(c * 1.05) == c * 10_500 // 10_000` for every value. Kept as
  a Known limitation for the §2 letter, not as an Issue.
- **`PercentDiscount.apply`** stays in integers for all inputs; `//` floors (stdlib semantics,
  probed).
- **5d tracer:** `create_user` callers (`api.py`, tests) tolerate the new optional `source`;
  `charge` callers (`api.py`, `test_billing.py`) tolerate the new optional `discount_code`;
  `find_user_by_email` callers: `billing.py` updated, `support.py` **not** (H1).
- **Tests at HEAD:** 4/4 pass (`python3 -m unittest discover tests -v`); every probe above ran
  against that green suite.
- **Verification method:** single-context adversarial pass backed by executable probes in a
  detached worktree (`git worktree add --detach`), removed afterwards; no subagent verifiers
  were used. Every non-Low finding has a reproduced probe.
- **Load-bearing external assumption:** only Python stdlib (`int()`, `//`, `dict.get`); no
  libraries added, so no outside-source check beyond the probes was needed.

## Not reviewed

Quick mode. Skipped axes:

- **5e architecture** — no `docs/architecture.md` in the repo; nothing to cite.
- **5f conventions** — only `CLAUDE.md` was consulted (quick mode reads instruction files
  only); no `docs/guidelines.md` exists. `docs/invariants.md` and `docs/testing.md` were read
  in full because the diff makes them load-bearing and they are one screen each.
- **5g security** — not swept. Note for full mode: `api_create_discount` and
  `api_apply_credit` have no authZ layer visible in this fixture, and H3 has a security
  character beyond the correctness finding recorded here.
- **5h privacy** — not swept; no `docs/privacy.md`. The diff adds a `source` string to the
  users row and no new email storage outside it.
- **5i testing** as a full axis — the test finding (H4) is derived from 5k risk coverage plus
  the `CLAUDE.md` rule, not from a full testing-axis walk.
- **5j** — no new libraries; see Verified.
- **5l reversibility** as an axis — C3 surfaced through 5c/5k; a full-mode 5l pass would also
  look at the `MAX_DISCOUNT_PERCENT` policy change and whether the engine env var counts as a
  flag.
- **5m dependencies** — none added.
- **Occam pass** and host built-in reviewers — not run; S1 is the one deletion candidate
  visible from the alignment axis.
- **External references** — SUPPORT-311, FIN-88 not accessible.
- Existing migration runner (none exists in the fixture; migrations were executed by importing
  the module directly).

Baseline at start: `feature/discounts` @ `c11dc93`, `git status --porcelain` empty. Checkout
unchanged at end (pycache from the test run removed; worktree removed).

# Examine: feat(discounts): Add discount codes with API validation (`feature/discounts` vs `main`)

**Target:** `git diff 9108191..b6c355b` (merge-base = `main` tip; working tree clean, so no uncommitted changes included). 8 files, +129/-14.
**Mode:** full — auto-chosen because the diff touches a migration and the payments/money path.
**Verification:** every Medium+ finding was probed by script in a detached worktree (`git worktree add --detach`, removed afterwards) and independently re-checked by an adversarial verifier and a defect-first reviewer that were given only the diff and the files, not this reviewer's reasoning. Verdicts below are theirs and the probes', not mine alone.

## Headline

**Hold.** Three of the commit message's five claims are false in the code, and each false claim is a project-invariant violation: percent is *not* validated at the API boundary (§4 — a 150% code produces a negative charge), the canonical-email invariant is silently dropped (§1 — mixed-case signups become unbillable), and migration 002 is destructive with no `down()` and disagrees with the code that still writes `plan` (§3). Add a crashed support console (`support.py` was not updated for the `find_user_by_email` contract change) and a redemption counter that nothing on the charge path consults, and the discount feature is currently unsafe to ship. The good news: the core shape — create a code, pass it to `charge`, apply integer-percent arithmetic — is the right one and most fixes are small. The PR also bundles four unrelated changes (cap change, migration, db contract change, credit endpoint); see S1.

## Approach fit

Matches the obvious approach for the stated problem — "API creates a percent code; `charge` accepts an optional code and applies it with integer arithmetic" (sketch 1 below) — **plus** a large halo that no stated constraint explains.

Sketches written before reading the diff:
1. *Minimal:* `api_create_discount` validates `1 <= percent <= MAX_DISCOUNT_PERCENT` via a `util` helper and stores the row; `api_charge` takes an optional `discount_code`; `billing.charge` looks it up and applies `amount - amount*pct // 100`; failure-path tests. No migration, no new package.
2. *Module-shaped:* same, with an `app/discounts.py` (create/apply/redeem) mirroring `users.py`, so `tests/test_discounts.py` mirrors it per `docs/testing.md`.
3. *Strategy objects:* only if fixed-amount/BOGO are actually scheduled.

The diff is sketch 1 wrapped in sketch 3's machinery (registry, ABC, env var — none of it called), plus: dropping `plan` via migration, changing `db.find_user_by_email`'s contract, a `source` field on users, and a negative-money `api_apply_credit` endpoint. I hunted for a constraint that would justify each (ticket, docs, `git log --all`, adjacent code, the sibling `feature/audit-log` branch): SUPPORT-311 and FIN-88 are not in the repo or history, `tier` is read by nothing, and the "simplifies the new discount code paths" claim for the `None` return is unsupported — the discount paths never call `find_user_by_email`. The extras therefore feed the Occam pass (M2) and the scope finding (M3) rather than being excused.

## Issues

### Critical (must fix before merge)

#### C1 — Discount percent is never validated; out-of-range codes produce negative or inflated charges
- **Locator:** `flow: app/api.py:18-27 (api_create_discount) -> app/billing.py:19-22 (charge) -> app/discount_engine/percent.py:10`
- **Changed anchor:** `app/api.py:22` (`"percent": int(payload["percent"])`)
- **What:** The commit message says "Discount percent is validated at the API boundary per docs/invariants.md §4." `validate_percent` exists (`app/discount_engine/__init__.py:26`) but has zero callers; `api_create_discount` stores whatever integer it is given and `charge` applies it unconditionally.
- **Evidence:** Probe: `percent=150` -> `charge("10.00")` returns `{'amount': -500, 'total': -525}`; `percent=-40` -> customer pays `1400` on a `1000` charge; `percent=45` -> applied despite `MAX_DISCOUNT_PERCENT = 30`. `grep validate_percent` finds only the definition. The FIN-88 cap change is therefore cosmetic: nothing enforces 30 (or 50).
- **Verdict:** CONFIRMED — probed on the branch; verifier reproduced independently.
- **Why Critical:** Negative and inflated money entries land in `STORE.charges`, and it violates a named invariant (§4) while the description claims compliance — the reviewer of the next PR will trust the constant. This is exactly the failure §4 exists to prevent.
- **Fix:** Call the validator in `api_create_discount` and reject on failure (raise `ValueError` / an API error). Put it in `app/util.py` next to `parse_money` per `CLAUDE.md` ("reuse helpers in app/util.py before writing new parsing or validation code"), which also removes the lazy circular import at `discount_engine/__init__.py:28`. Add a belt-and-braces guard in `charge` that the post-discount amount is `>= 0`. Add failure-path tests for `0`, `31`, `150`, `-1`, and non-integer input.
- **Cites:** `docs/invariants.md §4` ("validated at the API boundary before it reaches billing"); `CLAUDE.md` line 3.

#### C2 — Canonical-email invariant dropped at the write path; mixed-case signups become unbillable
- **Locator:** `app/users.py:12`
- **Changed anchor:** `app/users.py:5,12` (`normalize_email` import removed; `email.strip()` substituted)
- **What:** `create_user` no longer lowercases the email. `db.find_user_by_email` compares exactly (`app/db.py:16`), so a user who signed up as `A@B.C` cannot be charged as `a@b.c`, and vice versa. Unrelated to discounts and not mentioned in the description.
- **Evidence:** Probe: create `"  A@B.C "` -> stored `'A@B.C'`; `api_charge({"email": "a@b.c", ...})` -> `BillingError: unknown user`; charging with `A@B.C` succeeds. `tests/test_users.py` passes only because its fixture email is already canonical.
- **Verdict:** CONFIRMED — probed; verifier reproduced.
- **Why Critical:** §1 states the consequence explicitly: "a non-canonical write breaks every reader." Every lookup path (billing, support) now misses a class of users, and the bad rows persist after the code is fixed.
- **Fix:** Restore `email = normalize_email(email)` in `create_user`. Add a test that creates `"A@B.C "` and charges `"a@b.c"`.
- **Cites:** `docs/invariants.md §1`; `CLAUDE.md` line 3 (reuse `app/util.py` helpers).

#### C3 — Migration 002 is destructive, has no `down()`, and disagrees with the code that still writes `plan`
- **Locator:** `flow: migrations/002_drop_plan.py:4-7 -> app/users.py:14 -> tests/test_users.py:13`
- **What:** `up()` pops `plan` and writes `tier`; there is no `down()`; `users.create_user` still writes `"plan": "free"` and never writes `tier`; nothing in the repo reads `tier`; `test_users` still asserts `plan == "free"`. The mapping `plan == "legacy" -> "grandfathered"` matches no value that has ever been written (base writes only `"free"`), so 100% of users become `"standard"` and the distinction is lost.
- **Evidence:** Probe: after `up(STORE)`, an existing user is `{... 'tier': 'standard'}` (no `plan`); a user created afterwards is `{'plan': 'free'}` (no `tier`). `hasattr(m, "down") == False`; `001_init.py` defines `down`.
- **Verdict:** CONFIRMED — probed; verifier reproduced.
- **Why Critical:** Irreversible data loss (`plan` is gone, no rollback), in the same PR as the code change, with the old code path still live — the opposite of the additive -> dual-read -> drop sequence §3 mandates. Also unrelated to discount codes.
- **Fix:** Remove the migration from this PR. If `tier` is wanted, do it as its own PR: (1) add `tier` alongside `plan` with `create_user` writing both and a `down()`; (2) ship dual-read; (3) drop `plan` in a later release. Name the source of `"legacy"`.
- **Cites:** `docs/invariants.md §3` ("additive first; destructive steps only after a release with dual-read, and every migration ships a `down()`").

### High (should fix before merge)

#### H1 — `support.lookup` now crashes on unknown email
- **Locator:** `app/support.py:6-10` (unchanged file)
- **Changed anchor:** `app/db.py:14-18` (`find_user_by_email` returns `None` instead of raising `NotFound`)
- **What:** The description says "billing was updated to match" — `support.py` was not. Its `except NotFound` branch is now dead and `u["id"]` dereferences `None`. `db.NotFound` is now referenced only by this broken caller.
- **Evidence:** Probe: `support.lookup("nobody@x.y")` -> `TypeError: 'NoneType' object is not subscriptable` (base returns `{"found": False}`). Callers of `find_user_by_email`: `billing.py:15` (updated), `support.py:7` (not).
- **Verdict:** CONFIRMED — probed; verifier reproduced.
- **Why High:** Reachable outage in the support console on the most common support query (a customer who mistyped their email). No test covers it.
- **Fix:** Either revert the contract change (it buys nothing — see Approach fit) or update `support.py` to `if u is None: return {"found": False}` and delete `NotFound`. Add a not-found test for `support.lookup` per `docs/testing.md` ("lookup paths require failure-path tests").
- **Cites:** `docs/testing.md` lines 4-5.

#### H2 — Redemption accounting is disconnected from charging: single-use codes are unlimited, unknown codes report "redeemed"
- **Locator:** `flow: app/api.py:30-39 (api_redeem) <-> app/billing.py:19-22 (charge) <-> app/api.py:26 (api_create_discount)`
- **What:** Three symptoms, one root cause — `uses`/`max_uses` live in a separate, uncalled endpoint: (a) `charge` reads only `row["percent"]` and never checks or increments `uses`; (b) `api_redeem`'s condition is inverted — `if row is None or ...` takes the "redeem" branch for a missing code, the resulting `KeyError` is swallowed by `except Exception: pass`, and it returns `{"redeemed": True}`; (c) `api_create_discount` unconditionally overwrites an existing code with `uses: 0`, so re-creating a code resets its counter.
- **Evidence:** Probe: a `max_uses=1` code applied on three consecutive charges, `uses` stays `0`; `api_redeem({"code": "GHOST"})` -> `{'redeemed': True}` with `STORE.discounts == {}`; re-create after exhaustion -> redeemable again. No caller of `api_redeem` exists in the repo.
- **Verdict:** CONFIRMED — probed; verifier reproduced all three.
- **Why High:** Wrong money outcome on the main path: any customer can reuse a one-time code indefinitely, and the endpoint meant to stop it lies. The `try/except Exception: pass` also hides any future bug in this path.
- **Fix:** Do redemption inside `charge` (look up -> check `uses < max_uses` -> apply -> increment) so it is one operation, and delete `api_redeem` or make it call the same function. Fix the predicate to `row is not None and row["uses"] < row["max_uses"]` and remove the blanket `except`. Reject `api_create_discount` for an existing code (or make it an explicit update). Tests for exhausted and unknown codes.
- **Cites:** `docs/testing.md` lines 4-5 ("limit exceeded" is a named failure path).

#### H3 — `api_apply_credit` writes unbounded negative money with no user reference and is undisclosed
- **Locator:** `app/api.py:42-50`
- **What:** New endpoint, absent from the commit message, that strips a leading `-` to bypass `parse_money`'s deliberate non-negative guard (`app/util.py:10-13`: "adjustments are modeled explicitly") and appends `{"user_id": None, "amount": -N, "total": -N}` to the charges ledger — no user, no tax, no cap, no test.
- **Evidence:** Probe: `{"amount": "-5.00"}` -> `{'user_id': None, 'amount': -500, 'total': -500}` in `STORE.charges`. `"-"` -> `ValueError: malformed amount: ''` (original input lost in the message).
- **Verdict:** CONFIRMED — probed; verifier reproduced.
- **Why High:** A money path that produces ledger entries attributable to nobody, in a PR whose description does not mention it, with no failure-path test. `CLAUDE.md` requires charges to reference users by id.
- **Fix:** Drop it from this PR. If credits are wanted, model them explicitly (a `credit` entry type bound to a `user_id`, positive magnitude, own validation and tests) in their own PR.
- **Cites:** `CLAUDE.md` line 6 ("reference users by id"); `docs/testing.md` lines 4-5; `app/util.py:10-13` docstring.

#### H4 — No failure-path tests for any new money or lookup path
- **Locator:** `tests/test_discounts.py:13-19`
- **What:** The PR modifies `billing.py` (which `CLAUDE.md` says "requires failure-path tests") and adds four money/lookup paths, but ships one happy-path test asserting only `amount` (not `total`). Uncovered: percent out of range, unknown code, exhausted `max_uses`, redeem of unknown code, `api_apply_credit`, `support.lookup` not-found, migration up/down.
- **Evidence:** `python3 -m unittest discover tests -v` -> 4 tests, all green — on a branch with C1-C3 and H1-H3 present. Every issue above was reproducible with a five-line test.
- **Verdict:** CONFIRMED — test file read; suite run.
- **Why High:** The three top production risks (negative charges, support crash, irreversible migration) have no covering test; the suite being green is what let the false claims in the description survive.
- **Fix:** Add the tests named in C1, C2, H1, H2 (each is ~5 lines); assert `total` as well as `amount`.
- **Cites:** `CLAUDE.md` line 5; `docs/testing.md` lines 4-5.

### Medium (worth fixing now; acceptable as a follow-up)

#### M1 — Unknown discount code is silently ignored; customer is charged full price with no signal
- **Locator:** `app/billing.py:20-22`
- **What:** `row = STORE.discounts.get(discount_code); if row:` falls through on a typo or expired code and charges the full amount. The caller cannot distinguish "discount applied" from "discount ignored".
- **Evidence:** Probe: `discount_code="NOPE"` -> `{'amount': 1000, 'total': 1050}`, no error. A trailing space in the code has the same effect.
- **Verdict:** CONFIRMED — probed; verifier reproduced.
- **Why Medium:** Wrong behavior on an edge path that support will field as "my code didn't work" tickets with no diagnostic; also the natural place for the max-uses check (H2) to fail loudly.
- **Fix:** Raise `BillingError("unknown discount code")` (or return an explicit `discount_applied` field). Consider `.strip()`ing the code at the API boundary.
- **Cites:** `docs/testing.md` lines 4-5 ("not-found" is a named failure path); no project rule on API error shape — judged as wrong data.

#### M2 — The discount "engine" is dead machinery with a misleading operator knob
- **Locator:** `app/discount_engine/__init__.py:1-35`, `app/billing.py:2`
- **What:** `STRATEGY_REGISTRY`, `register`, `DiscountStrategy` (ABC), `get_strategy`, and the `DISCOUNT_ENGINE_BACKEND` env var have no callers; `billing.py` imports `PercentDiscount` directly and bypasses the registry. `validate_percent` lives here (uncalled, see C1) with a lazy `from ..billing import` to dodge the circular import created by splitting cap and validator. Registration is an import side effect, so `get_strategy("percent")` raises `KeyError` unless `percent.py` was imported first.
- **Evidence:** Probe: `DISCOUNT_ENGINE_BACKEND=bogo` -> `get_strategy()` raises `KeyError`, while `api_charge` still applies the percent discount unchanged. `grep -r get_strategy STRATEGY_REGISTRY` -> definitions only.
- **Verdict:** CONFIRMED (Occam candidate: cost is concrete, no justifying constraint found) — the "upcoming fixed-amount and BOGO" future is stated but nowhere scheduled, and the registry is not even used by the one strategy that exists.
- **Why Medium:** A documented configuration variable that does nothing is an operational trap, the registry pattern is the kind adjacent code copies, and the lazy import is a smell the split created. Promoted from Suggestion on the strength of the env-var cost.
- **Fix:** Collapse to a function `apply_percent(amount_cents, percent) -> int` (in `billing.py` or a small `app/discounts.py` mirroring `users.py`) and move `validate_percent` to `app/util.py` next to `parse_money`. Add the strategy abstraction when the second strategy arrives. Walked against constraints: §2 (integer math preserved), §4 (validator placement improves), `CLAUDE.md` helper-reuse rule (satisfied), commit message's "pluggable" goal (unscheduled; the registry does not deliver it today anyway).
- **Cites:** `CLAUDE.md` line 3 (validation helpers belong in `app/util.py`).

#### M3 — Five unrelated changes in one PR; three of them undisclosed or mis-described
- **Locator:** `scope: PR`
- **What:** Bundled with the discount feature: (1) cap 50->30 (policy change), (2) migration dropping `plan`, (3) `find_user_by_email` contract change, (4) `source` field on users, (5) `api_apply_credit`. (4) and (5) are absent from the description; (2) and (3) are described with claims the code contradicts (C3, H1).
- **Evidence:** Commit body vs diff; Approach fit section above.
- **Verdict:** CONFIRMED — by inspection.
- **Why Medium:** A revert of the discount feature would also revert a finance policy change and an irreversible migration; reviewers reading the description will approve behaviour that isn't there. Maintenance/atomicity cost, not a runtime defect.
- **Fix:** See S1 — split.
- **Cites:** no project rule on PR atomicity; judged against reversibility (`docs/invariants.md §3` for the migration part).

### Low (defer)
- **L1** [`app/billing.py:23`] `int(amount * (1 + TAX_RATE_BP / 10_000))` is float arithmetic in a money path (`docs/invariants.md §2`, `CLAUDE.md` line 2). Pre-existing, and probed exhaustively to 10^7 cents and randomly to 10^13 with zero divergence from integer math (first divergence ~2^52 cents), so not a live bug — but the touched function now feeds discounted values through it. One-line fix: `amount * (10_000 + TAX_RATE_BP) // 10_000`.
- **L2** [`app/api.py:22,24`] `int(payload["percent"])` / `int(payload.get("max_uses", 1))` raise bare `ValueError`/`KeyError` at the API boundary (`"10.5"`, `"x"`, missing `code`); `True` is accepted as `1`. Folds into the C1 validator.
- **L3** [`app/api.py:6-9`, `app/users.py:9,15`] `source` field added to users, unvalidated and undocumented; harmless. Mention it or drop it.
- **L4** [`app/billing.py:14`, `app/db.py:14`] `discount_code: str = None` should be `Optional[str]`; `find_user_by_email` lost its return annotation (`-> Optional[dict]` if the `None` contract stays).
- **L5** [`app/billing.py:11`] The constant's comment lost its pointer to §4 ("validated at the API boundary") — the only in-code reminder of where the cap must be enforced.

## Questions

- **Q1** [`app/billing.py:11`] Where is FIN-88 recorded, and should existing codes between 31 and 50 percent be invalidated or grandfathered? (Nothing enforces either value today — see C1 — so the answer decides what the validator does with stored rows.)
- **Q2** [`scope: PR`] Does SUPPORT-311 ask for `max_uses`, a separate redeem endpoint, or credits at all? The stated problem is "create percentage codes; redeem at charge time."
- **Q3** [`migrations/002_drop_plan.py:7`] What reads `tier`, and what ever wrote `plan == "legacy"`? Neither appears in the repo or its history.
- **Q4** [`app/api.py:24`] Is `max_uses` defaulting to 1 (every code single-use unless stated) intended for support-created promo codes?
- **Q5** [`app/db.py:14-18`] What does the `None` return simplify? The discount paths never call `find_user_by_email`; the only effect I can find is H1.

## Suggestions

#### S1 — Split into four PRs
- **Locator:** `scope: PR`
- **What:** (a) discount codes (api + billing + tests); (b) cap 50->30 with the FIN-88 reference — a one-line policy PR finance can sign off on its own; (c) `plan`->`tier` as a §3-compliant additive/dual-read/drop sequence, if wanted at all; (d) drop or redo `find_user_by_email`'s contract with `support.py` updated in the same commit. `source` and `api_apply_credit` go to their own tickets or nowhere.
- **Why it'd be better:** Each becomes independently revertable and reviewable; the description stops making claims for code that isn't there.

#### S2 — Make `charge` the single owner of discount application
- **Locator:** `app/billing.py:14-26`
- **What:** `charge(email, raw_amount, discount_code=None)`: normalize the email, look up the user, parse money, then `if discount_code: amount = _apply_discount(discount_code, amount)` where `_apply_discount` validates existence, checks and increments `uses`, and applies integer percent — raising `BillingError` on any failure. Delete `api_redeem`.
- **Why it'd be better:** One operation, one failure surface, one place to test; resolves H2 and M1 together and gives the "must never fail the charge path" comment a true home (it fails the charge *before* money moves, which is the desired behaviour).
- **Sketch:**
  ```python
  def _apply_discount(code: str, amount: int) -> int:
      row = STORE.discounts.get(code)
      if row is None:
          raise BillingError("unknown discount code")
      if row["uses"] >= row["max_uses"]:
          raise BillingError("discount code exhausted")
      row["uses"] += 1
      return amount - (amount * row["percent"]) // 100
  ```

#### S3 — Put `validate_percent` in `app/util.py` and read the cap from `billing`
- **Locator:** `app/discount_engine/__init__.py:26-30`
- **What:** `util.validate_percent(percent) -> int` that parses, range-checks against `billing.MAX_DISCOUNT_PERCENT`, and raises `ValueError` like `parse_money` does. Call it from `api_create_discount`.
- **Why it'd be better:** Matches the existing `parse_money` shape and the `CLAUDE.md` helper rule; kills the lazy circular import.

#### S4 — Assert `total` in the discount test and add a boundary table
- **Locator:** `tests/test_discounts.py:19`
- **What:** Assert `total == 945` too, and parametrize over `{0, 1, 30, 31, -1, "10.5"}` for creation and `{unknown, exhausted, ""}` for charging.
- **Why it'd be better:** Turns the one test that exists into the failure-path coverage `docs/testing.md` asks for.

## Gaps

- No documentation of the new API fields (`discount_code`, `max_uses`, `source`) or the new endpoints; `README.md` still describes "user + billing".
- No manual-test notes for the migration (how it was run, against what data). There is no migration runner in the repo to run it with.
- `feature/audit-log` (in flight) also edits `app/users.py` and `app/db.py`; whichever lands second will conflict on `create_user`.
- No `.gitignore` — running the suite writes `__pycache__/` into the checkout.

## Known limitations

- `PercentDiscount.apply` floors the discount, so the customer pays up to 1 cent more than the exact percentage (`999 x 15% -> 850`, exact 849.15). Integer, explicit, §2-compliant; document the rounding direction in the docstring.
- `api_create_discount` has no authorization, but neither does any other endpoint in this codebase and there is no `docs/security.md`; judged against OWASP A01 (Broken Access Control) this is a codebase-wide property, not something this PR should solve. Worth a ticket.
- `find_user_by_email` is a linear scan — pre-existing and fine for an in-memory fixture.

## What was done well

- [`app/discount_engine/percent.py:10`] `amount_cents - (amount_cents * self.percent) // 100` is pure integer arithmetic with an explicit rounding decision — exactly what §2 asks for.
- [`app/api.py:12-15`] `payload.get("discount_code")` keeps the existing `api_charge` payload backward-compatible; `charge`'s new parameter defaults to `None` so the base tests pass unchanged.
- [`app/billing.py:24`] Charges still reference `user_id` only, and the discount rows carry no email or other PII — `CLAUDE.md`'s "reference users by id" rule is respected on the discount path (H3 is the exception).
- [`tests/test_discounts.py:8-11`] `setUp` clears all three stores, including the new `discounts` one — no leakage between tests.
- [`migrations/002_drop_plan.py:6`] `u.pop("plan", None)` makes `up()` idempotent; the right instinct even though the migration itself should not ship (C3).
- The commit message names its non-obvious decisions (cap change with a policy reference, engine rationale). The structure is what a good description looks like — it is the content that needs to match the code.

## Verified

- **Problem is real:** base `9108191` has no code path that creates or applies a discount; `STORE.discounts` exists unused (`app/db.py:11`), so the PR fills a genuine hole and is not reimplementing an existing utility.
- **Approach:** core matches sketch 1 (see Approach fit); no constraint was found justifying the registry, migration, db contract change, `source`, or credits — hunted in the repo, docs, `git log --all`, and the sibling branch.
- **Suite:** `python3 -m unittest discover tests -v` -> 4/4 pass on the branch (run in a detached worktree).
- **Tax float truncation (candidate K11) — REFUTED as a live bug:** exhaustive probe 0..10^7 cents and 2M random amounts to 10^13 cents show `int(a * 1.05) == (a * 10500) // 10000` everywhere; first divergence at ~2^52 cents. The §2 wording violation stands as L1.
- `billing.charge`'s unknown-user path was correctly adapted to the `None` return (`app/billing.py:15-17`); `test_charge_unknown_user_fails` still passes.
- `validate_percent`'s lazy `from ..billing import` does not cycle at runtime (probed); it returns `False` for 45 and 150 — it would work if called.
- `docs/invariants.md §4` still points at `billing.MAX_DISCOUNT_PERCENT`, which still exists.
- No dependencies added or changed (no manifest in the repo; imports are stdlib only). No logging added anywhere, so no new PII sinks.
- SUPPORT-311 and FIN-88 do not appear in the repo, its docs, or `git log --all`; claims resting on them are unverifiable from here (Q1, Q2).
- No-trace check: primary checkout is on `feature/discounts` at `b6c355b`, `git status --porcelain` empty before and after; the detached worktree used for probes was removed.

## Not reviewed

- **5e Architecture:** no `docs/architecture.md`; layering judged only from the existing `api -> users/billing -> db` file layout (the engine's lazy import into `billing` is noted under M2 rather than as an architecture finding).
- **5g Security:** no `docs/security.md`; the codebase has no authN/authZ at all, so endpoint authorization is out of scope for this PR (Known limitations). No injection surface — in-memory dicts, no SQL/shell/templates.
- **5h Privacy:** no `docs/privacy.md`; judged only against the `CLAUDE.md` email rule. No new PII fields beyond `source`.
- **5m Dependencies:** none added.
- **CI:** no CI configuration or hosted PR exists for this fixture; "tests pass" is the local run above.
- **Migration runner:** none exists in the repo; `002` was exercised by importing it directly.
- **`feature/audit-log` interplay:** noted as a merge-conflict gap; not reviewed.

# Examine: Record an audit event on user creation (feature/audit-log vs main)

**Mode:** full, auto-chosen — the diff sits on the personal-data surface (audit logging adjacent to the CLAUDE.md email rule), and full is cheap on a 31-line diff.
**Target:** `git diff main...feature/audit-log` (merge-base = `dd9933c`, the only commit on main). Suite run on the branch in a detached worktree: 5 tests, all pass.

## Headline

Merge with one fix: audit entries carry no timestamp, so the trail answers "who" but not "when" — half the stated ask (M1). Everything else is clean, right-sized, and honors the project's privacy rule with a test to pin it.

## Approach fit

Matches the obvious approach — a small `app/audit.py` seam appending to a new `STORE.audit` list, called from `users.create_user`, mirroring the existing `STORE.charges` pattern. Everything the diff does is explained by the stated constraints (additive-only, id-only entries). No Occam findings: the separate module is justified as the seam that carries the id-only rule; `**fields` is mild generality with no operating cost.

## Issues

### Medium (worth fixing now; acceptable as a follow-up)

#### M1 — Audit entries record no timestamp, so the trail itself cannot answer "when"
- **Locator:** `flow: app/users.py:21 → app/audit.py:6-7`
- **What:** The stated problem is "Support asked for a trail of who was created and when." The entry written is exactly `{"event": "user.created", "user_id": <id>}` — no time field. "When" is recoverable only by joining to `STORE.users[user_id]["created_at"]`, a mutable row on the very table the trail is supposed to be an independent record of.
- **Evidence:** `app/audit.py` builds `entry = {"event": event, **fields}` with no clock and doesn't import `time`; the sole caller passes only `user_id`. `git grep` on the branch finds `time.` only at `app/users.py:18` (the user row). `tests/test_audit.py` pins event, user_id, and no-email — nothing would catch this.
- **Verdict:** CONFIRMED — independent verifier reproduced the mechanism and found no timestamp mechanism, no documented decision to omit it, and no test pinning a time field. It also refuted my aggravator: no delete/mutate path for users exists anywhere on the branch, so the join fallback currently always works (see Verified).
- **Why Medium:** The change only partially solves the stated problem; the gap is invisible today (join works) but silently undermines the trail's purpose the moment user rows become mutable or deletable. One-line fix, no migration.
- **Fix:** Add `"at": time.time()` in `audit.record` (keeps every event stamped by construction), extend `test_user_creation_is_audited` to assert it.
- **Cites:** PR's own stated intent (commit message: "who was created and when"). No project rule mandates audit timestamps — judged against the stated requirement.

### Low (defer)
- **L1** [scope: PR] The description claims "failure paths covered in tests/test_audit.py," but the two tests are a happy path and a privacy negative; no failure path is exercised (arguably none exists — a list append can't realistically fail). Reword the claim or add the test the claim implies.

## Suggestions

#### S1 — Enforce the id-only rule in `record()` instead of by docstring
- **Locator:** `app/audit.py:4-7`
- **What:** `record(event, **fields)` accepts arbitrary fields; the CLAUDE.md rule "Never log or store raw emails outside the users table; reference users by id" is enforced only by the docstring and one test on one call site. A future caller passing `email=...` violates the rule silently.
- **Why it'd be better:** Turns a convention into a mechanism at the single choke point every audit write passes through; the existing test then guards the guard.
- **Sketch:** `if "email" in fields: raise ValueError("audit entries carry ids, never emails (CLAUDE.md)")`

#### S2 — Clear `STORE.audit` in the other test files' `setUp`
- **Locator:** `tests/test_users.py:9`, `tests/test_billing.py:9-10`
- **What:** Both files create users and therefore now append audit entries they never clear; entries accumulate across those tests. Harmless today (only `test_audit.py` asserts on the trail, and it clears first), but it is setup/teardown asymmetry a future assertion will trip over.
- **Why it'd be better:** Keeps every test file's `setUp` resetting all the state its tests now mutate, matching the existing convention of clearing `users`/`charges`.

## Gaps
- No doc trace of the new subsystem: the audit trail, its event-name convention (`user.created`), and the id-only field rule live only in code and CLAUDE.md; a line in `docs/` would help the next event's author.

## Known limitations
- `STORE.audit` grows without bound in memory — same pattern as `STORE.charges`; acceptable in this in-memory fixture, worth a note if this ever fronts a real store.
- Only `user.created` is audited (no charge/discount events) — explicitly in-scope per the commit message ("additive only"); fine as-is.
- Unlocked shared-global append — identical to the pre-existing `charges` pattern; no new concurrency hazard introduced.

## What was done well
- [tests/test_audit.py:18-20] The privacy rule isn't just followed, it's pinned: a dedicated test asserts no `email` key in the entry, turning the CLAUDE.md rule into a regression guard.
- [app/users.py:21] Audit write happens after the user insert and passes only `user_id` — exactly the id-referencing shape CLAUDE.md demands.
- [app/db.py:13] Additive-only and trivially reversible: no migration, no schema change, `docs/invariants.md §3` never comes into play; revert is a clean three-hunk removal.
- [tests/test_audit.py:9-10] New test file clears both `users` and `audit` in `setUp` — order-independent against the existing suite.
- [scope: PR] The commit message states problem, approach, constraint, and cites the governing rule ("never the raw email (CLAUDE.md logging rule)") — a model description, modulo L1.

## Verified
- Problem real on base: main has no audit code anywhere (`git grep audit` on main: none); `create_user` writes only the user row.
- Approach matches sketch #2 of three pre-diff sketches (dedicated audit module + store list); the api-layer variant was rightly avoided — it would miss non-API callers.
- "Tests pass" claim verified empirically: full suite run on the branch in a detached worktree — 5 tests, OK.
- No import cycle: `users → audit → db`, `db` imports nothing from the package (independent defect scan confirmed).
- Call-site tracer (5d): `create_user`'s only caller is `app/api.py:5`; signature and return unchanged, nothing breaks. `record`'s keyword cannot collide with the positional `event`.
- `self.audit` initialized in `Store.__init__` before any `record` call is reachable — no `AttributeError` path.
- REFUTED (my candidate aggravator for M1): "join fallback fails when a user row is deleted" — no delete/update path for users exists on the branch (`app/users.py` only creates; no `del`/`.pop(`/mutation in `api.py`, `support.py`, `billing.py`). M1's severity rests on the goal mismatch, not on a reachable deletion.
- Top-3 production risks and their coverage: (1) audit call breaks user creation — covered by `test_user_creation_is_audited` plus the green suite; (2) PII leaks into the trail — covered by `test_audit_entries_carry_no_email` (residual foot-gun → S1); (3) trail can't answer support's actual question — uncovered → M1.

## Not reviewed
- 5e architecture: no `docs/architecture.md`; layering judged only against the existing `billing`/`db` pattern, which the diff matches.
- 5g security: no new trust boundary, endpoint, or external input; no `docs/security.md` — absent and not needed for this diff.
- 5h privacy: no `docs/privacy.md`; the CLAUDE.md email rule is the project's operative privacy rule and was applied (M1/S1/done-well).
- 5m dependencies: none added or bumped.
- CI: local fixture, no remote or checks to consult.
- `feature/discounts` (the checked-out branch) — out of scope for this review.

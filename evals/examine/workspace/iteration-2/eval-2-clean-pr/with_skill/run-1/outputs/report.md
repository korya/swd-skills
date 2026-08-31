# Examine: Record an audit event on user creation (`feature/audit-log` vs `main`)

- **Target:** `feature/audit-log` @ `a1440c8`, merge-base with `main` = `e7f4e0d` (branch is one commit ahead; tree clean). Diff: `git diff main...feature/audit-log` — 4 files, +31 / −0.
- **Mode:** **full**, auto-chosen. The blast radius is tiny (4 files, no deps, no migration), but the change adds a new persistence surface for user-related events and the description itself invokes the repo's personal-data logging rule, which is a "personal data" trigger. Full costs ~nothing at this size.
- **Verification:** independent subagent verdict on the one Medium candidate; host built-in review (`code-review`, high effort) run as an additional candidate source; Low candidates and Suggestions self-verified.

## Headline

**Merge with one fix:** the audit entry records *who* but not *when*, and "who was created and when" is the entire stated problem — add a timestamp to the entry (M1). Everything else is clean; the description's claim of failure-path tests is inflated but harmless.

## Approach fit

Matches the obvious approach — sketch A below (a list on `Store`, one `record()` helper, one call in `create_user`). Nothing in the diff exceeds the sketch; the only shortfall is the missing timestamp.

Sketches made before opening the diff:

- **A.** Add `STORE.audit = []`; append `{event, user_id, at}` from `create_user`. Smallest additive change; mirrors how `charges` is stored. *(Chosen by the PR, minus `at`.)*
- **B.** No new store — support reads `created_at` off the user row (already set at `app/users.py:17`). Rejected: a mutable row is not an append-only trail; it cannot survive a future user update/delete and has no event semantics. Base already has this "solution" and support still asked, so it does not satisfy them.
- **C.** Generic event/observer hook that every write path publishes to. Over-scoped for one event nobody else consumes.

## Issues

### Critical (must fix before merge)

None.

### High (should fix before merge)

None.

### Medium (worth fixing now; acceptable as a follow-up)

#### M1 — Audit entry has no timestamp, so the trail cannot answer "when"
- **Locator:** `app/users.py:21` (call site) / `app/audit.py:6` (entry shape)
- **What:** The stated problem is "a trail of who was created and when". The entry written is `{"event": "user.created", "user_id": <id>}` — no time field. The only "when" in the system is `users[id]["created_at"]`, a field on a mutable row in a different store, which is exactly what an append-only trail exists to be independent of.
- **Evidence:** `app/audit.py:6` `entry = {"event": event, **fields}`; `app/users.py:21` `audit.record("user.created", user_id=user["id"])` — no `time.time()` passed, and `record()` does not stamp one. `tests/test_audit.py` asserts on `event` and `user_id` only, so no test would notice. No reader exists yet (`app/support.py` never touches `STORE.audit`) that could reconstruct it.
- **Verdict:** CONFIRMED — independent verifier reproduced the entry shape `{"event": "user.created", "user_id": 42}` from the two quoted lines and confirmed no existing test asserts a time key.
- **Why Medium:** The feature ships half of its stated requirement; support gets the same answer they could already get from the users table. No data is corrupted and nothing crashes, but the follow-up is inevitable, and adding the field later means the first N entries have no time — a gap in an audit trail is the kind of thing auditors ask about.
- **Fix:** Stamp inside `record()` so every event gets it for free and callers cannot forget: `entry = {"event": event, "at": time.time(), **fields}`. Add an assertion in `tests/test_audit.py` that `"at"` is present and close to `u["created_at"]`.
- **Cites:** PR description ("who was created and when") — no project rule; this is a stated-problem shortfall (axis 5b).

### Low (defer)
- **L1** [`scope: PR`] The description says "failure paths covered in tests/test_audit.py"; the file has two happy-path tests (`test_user_creation_is_audited`, `test_audit_entries_carry_no_email`) and no failure path. CONFIRMED by reading the file. Not a coverage violation — `docs/testing.md` requires failure-path tests only for money and lookup paths — but reviewers reading the description will assume coverage that is not there. Reword the description (or add the tests; see S2).

## Questions

- **Q1** [`app/db.py:13`] `docs/invariants.md §3` frames schema changes as migrations ("additive first … every migration ships a `down()`"). Adding `Store.audit` is the in-memory equivalent of `CREATE TABLE`. Precedent cuts both ways: `discounts` was added to `Store` on `main` with no migration and `migrations/001_init.py` is a no-op stub, yet a sibling branch (`feature/discounts`) does ship `migrations/002_drop_plan.py`. Is "no migration" the intended convention for additive stores, or should a `002_add_audit.py` stub with `down()` accompany this?
- **Q2** [`app/db.py:13`] What is the retention expectation for audit entries? `STORE.audit` grows without bound and has no erasure path. Today that matches every other list on `Store` (in-memory, restart-reset) and there is no user deletion in the codebase, so nothing to erase — but if the users table ever gets a delete, `user_id` in the audit log is pseudonymous personal data (GDPR Art. 4(1)) and will need a policy. Is "same lifetime as the store" the intended answer for now?

## Suggestions

#### S1 — Narrow `record()`'s signature so the "no raw emails" rule is enforced, not documented
- **Locator:** `app/audit.py:4`
- **What:** `record(event: str, **fields)` accepts anything; the CLAUDE.md rule ("Never log or store raw emails outside the users table; reference users by id") lives only in the docstring. `test_audit_entries_carry_no_email` tests the one existing call site, not the API. A future `audit.record("user.login", email=...)` passes review and tests unchanged.
- **Why it'd be better:** The privacy rule becomes a shape constraint rather than a convention; the test can then cover the API instead of one caller.
- **Sketch:** `def record(event: str, *, user_id: int, **extra) -> dict:` and either reject keys named `email` or drop `**extra` entirely until a second event needs it (Occam pass: `**fields` is used with exactly one field, and `return entry` has no caller).
- **Walked against:** CLAUDE.md logging rule (supports it); description constraint "additive only" (unaffected — the signature is new code with one caller).

#### S2 — Give the tests the failure-path shape the description promises, and reset `STORE.audit` symmetrically
- **Locator:** `tests/test_audit.py`, `tests/test_users.py:9`, `tests/test_billing.py:9-10`
- **What:** If L1 is resolved by adding tests rather than rewording: (a) `record()` rejects an `email` field (once S1 lands); (b) no entry is written when user creation fails (currently unreachable — `create_user` cannot fail — so this test only earns its keep once validation exists). Independently: `tests/test_users.py` and `tests/test_billing.py` both call `create_user` but clear only `users`/`charges` in `setUp`, so audit entries now leak across test modules. Harmless today because only `test_audit` asserts on the list, but a setup/teardown asymmetry waiting to bite.
- **Why it'd be better:** Description and tests say the same thing, and `STORE` resets stay symmetric across test modules.

## Gaps

- `migrations/001_init.py`'s docstring ("create the initial stores (users, charges)") does not mention `audit` — already stale before this PR (omits `discounts`), so not this change's debt.
- Nothing in `app/support.py` exposes the trail; the requester cannot read it yet. Fine for an "additive only" first step, but the feature is not usable by support until a follow-up lands.

## Known limitations

- **In-memory, lost on restart.** Stated in the description. Acceptable because every store on `Store` has the same property ("Tiny in-memory store standing in for a database", `app/db.py:1`) and the README calls the whole service a fixture — the audit list is no less durable than the users it describes.
- **"Append-only" is by convention.** `STORE.audit` is a plain list; anything can `.clear()` it (the tests do). Consistent with the rest of `Store`, which has no access control at all; a tamper-evident log is out of scope for a fixture-grade store. Worth a comment at `app/db.py:13` if it ever grows up.
- **Returned entry aliases the stored one.** `record()` returns the same dict it appended, so a caller can mutate history. Same pattern as `create_user` returning the stored user dict; not worth diverging from for one call site that ignores the return value.

## What was done well

- [`app/users.py:21`] Audit call placed *after* `STORE.users[...] = user`, so an entry can never exist for a user that was not stored. Right ordering for a trail.
- [`app/users.py:21`] Passes `user_id` only — complies with the CLAUDE.md rule ("reference users by id") on the first try, and the description names the rule it is honouring.
- [`tests/test_audit.py:18-20`] `test_audit_entries_carry_no_email` pins the privacy rule as a test, not a comment. It should grow to cover the API (S1), but the instinct is exactly right.
- [`tests/test_audit.py`] Mirrors `app/audit.py` per `docs/testing.md` ("tests/ mirrors app/"); uses `unittest` like the rest of the suite.
- [`app/audit.py`] Separate module rather than a method on `Store` — matches the repo's layout (`billing`, `users`, `support` are each thin modules over `STORE`) and gives the test its mirror location. Occam pass considered collapsing it into `users.py` and rejected: the module is the natural home for the second event, and the cost is eight lines.
- [`scope: PR`] Commit subject follows the repo's `type(scope): Sentence` convention; description states problem, approach, constraints and the rule it respects — a model description, apart from L1.

## Verified

- **Problem exists in base:** `main` has no audit store and no event trail; `created_at` on the user row (`app/users.py:17`) is the only timestamp and lives on a mutable record (sketch B rejected above).
- **"No behavior change for existing callers":** `create_user`'s return value and the user dict shape are unchanged; the only caller (`app/api.py:5`) and `app/support.py` are untouched. Base suite (3 tests) and branch suite (5 tests) both pass — run in a detached worktree.
- **"Additive only, no migration":** no line removed; `Store.__init__` gains one attribute; the only `Store()` construction is `app/db.py:22`, so no other instance lacks `.audit`. Revert is a clean removal with no external side effects (5l). Whether the convention wants a migration stub is open — Q1.
- **Import graph:** `users → audit → db`; `audit` does not import `users`, no cycle. Confirmed by the test run (import succeeds).
- **Load-bearing assumption checked outside the diff:** `from . import audit` (relative submodule import inside a package) and `**fields` combined with a positional `event` — both confirmed by executing the suite under the local Python 3, not by reading.
- **Conventions (5f):** CLAUDE.md rules on integer cents, `util` reuse, and `billing.py` tests do not apply (no money, no parsing, `billing.py` untouched). Logging rule: complied.
- **Security (5g):** no new trust boundary — `record()` takes internal arguments; `api_create_user` is unchanged. No project security doc; nothing in OWASP Top 10 is reachable from this diff.
- **Dependencies (5m):** none added.
- **Top-3 production risks and coverage:** (1) trail cannot answer "when" — uncovered, M1; (2) unbounded in-memory growth — uncovered, accepted as Known limitation (same as every other store list); (3) future caller stuffs an email into `**fields` — covered for the one existing call site only, S1.
- **Host built-in review:** `code-review` (high effort, single-pass — its fan-out was unavailable) plus the subagent's own manual pass produced five candidates, all already on this list: `**fields` accepts an email (S1; it executed `audit.record("user.created", user_id=2, email="raw@example.com")` and confirmed it is stored silently), returned-dict aliasing (Known limitations), cross-module `STORE.audit` leakage (S2; it also ran the suite in reversed order, still green), missing timestamp (M1), and non-atomic insert + audit append at `app/users.py:20-21` — dropped by both of us: the in-memory `append` cannot fail, so there is no partial state to reach today; worth a note only when `record()` grows a real backend. It found no correctness bug in the 31 lines, which matches this review.
- **Gap sweep (fresh pass after verification):** nothing new. Checked test setup/teardown symmetry (folded into S2), definition-time defaults (none), predicate side effects (none), the module-global `_ids` counter (never reset across tests, but `test_audit` compares against the returned `u["id"]`, so robust).

## Not reviewed

- No `docs/architecture.md`, `docs/security.md`, or `docs/privacy.md` in the repo; the diff needs none of them beyond CLAUDE.md's logging rule (5e/5g/5h judged against that rule and, for retention, GDPR by name).
- `feature/discounts` is a sibling branch that also edits `app/db.py` and `app/users.py`; a merge-order conflict is possible but is not this PR's defect and was not analysed.
- No CI configured in the fixture; no `gh pr checks` to consult.
- Nothing posted, pushed, or commented. Detached worktree used for test runs and removed; primary checkout unchanged from baseline (`feature/discounts` @ `dc87adc`, clean).

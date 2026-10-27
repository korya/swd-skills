# Examine: Record an audit event on user creation (`feature/audit-log` vs `main`)

Target: `git diff main...feature/audit-log` (merge-base `9582ef7`, head `93ba905`), 4 files, +31/−0. Working tree clean, so no `git diff HEAD` added. Description = the branch's commit message.
Mode: **full**, auto-chosen — the change persists a new record about users and its central claim is a privacy property (CLAUDE.md logging rule), which I read as the "personal data" trigger. The diff is small enough that full cost nothing extra.

## Headline
**Merge.** No qualifying issues. The change does exactly what the description says, is the simplest shape that solves the stated ask, obeys every project rule that applies, and the suite (5 tests) is green on the branch and the baseline. Two offers below, neither blocking.

## Approach fit
Matches the obvious approach — "append an entry to a new list on `Store` from `create_user`" (sketch 1 of 3; details under Verified). The only thing beyond the sketch is an 8-line `app/audit.py` module instead of an inline `STORE.audit.append(...)`; it earns its place as the single enforcement point for the id-not-email rule and the obvious home for the next event type, so I did not raise it as an Occam finding.

## Issues

No qualifying issues.

## Questions

- **Q1** [`app/audit.py:4`] Is "append-only" meant to be enforced in code eventually (e.g. no public clear/remove), or is it a convention like the other `STORE` collections? Today `tests/test_audit.py:10` relies on `STORE.audit.clear()`, which is fine for tests but means the list is append-only by agreement, not by type.

## Suggestions

#### S1 — Give each audit entry its own timestamp
- **Locator:** `app/audit.py:6` (and the call at `app/users.py:21`)
- **What:** The entry is `{"event": "user.created", "user_id": N}`. The stated ask is a trail of "who was created **and when**"; today "when" is only recoverable by joining `STORE.users[N]["created_at"]`.
- **Why it'd be better:** The trail becomes self-contained. The join works now because nothing deletes users, but the first erasure/delete path (the very reason to key audit by id rather than email) would strip "when" from the history. A `ts` field costs one line and keeps the log honest on its own.
- **Sketch:** `entry = {"event": event, "ts": time.time(), **fields}` and assert `"ts" in STORE.audit[0]` in `test_user_creation_is_audited`.

#### S2 — Make `record()` reject the one thing the docstring forbids
- **Locator:** `app/audit.py:5-6`
- **What:** The CLAUDE.md rule ("never log or store raw emails outside the users table") is enforced at the single current caller and pinned by `tests/test_audit.py:18-20`, but `record(**fields)` itself accepts any key. The docstring is the only guard for the next caller.
- **Why it'd be better:** One check at the choke point (`if "email" in fields: raise ValueError(...)`) turns a convention into a mechanism, and the existing no-email test becomes a test of `record` rather than of one call site. Cheap, and it is exactly the kind of trust-boundary guard the rule asks for; decline freely if you'd rather keep `record` dumb.

## Gaps
- The description says "failure paths covered in tests/test_audit.py". The file has a happy-path test and a negative privacy assertion; there is no failure path in `record()` to cover (a list append cannot fail), and `docs/testing.md` demands failure-path tests only for money and lookup paths, which this is not. Wording nit, not a coverage gap.
- No CHANGELOG/README mention of the new `STORE.audit` collection. Low consequence; the README only documents how to run tests.
- `tests/test_users.py:9` and `tests/test_billing.py:8-10` clear `users`/`charges` but not the new `STORE.audit`, so entries leak across those classes. Harmless today (nothing outside `test_audit` reads it; reversed-order run passes), but a future audit assertion that forgets its own `setUp` would become order-dependent. One `STORE.audit.clear()` each closes it.

## Known limitations
- `STORE.audit` grows unbounded for the life of the process. Same property as `STORE.users` and `STORE.charges`; the whole store is in-memory by design (`app/db.py:1`), so this is the fixture's model, not this PR's defect. Worth a line in whatever doc eventually describes the store.
- Only `user.created` is audited. That is the stated scope ("audit event on user creation"); charges are already recorded in `STORE.charges`.

## What was done well
- [`app/users.py:20-21`] The audit write happens *after* the user is persisted and ignores `record`'s return, so `create_user`'s return value and shape are untouched — verified by probe (`set(u) == {id, email, name, plan, created_at}`) and by the untouched `tests/test_users.py` passing.
- [`app/users.py:21`] Passes `user_id=user["id"]` and nothing else — complies with CLAUDE.md "reference users by id" and `docs/invariants.md §1` is unaffected (no new email read/write path).
- [`tests/test_audit.py:18-20`] A negative test for the privacy rule (`assertNotIn("email", ...)`), not just a happy path. That is the one failure mode that matters here and it is pinned.
- [`tests/test_audit.py:8-10`] `setUp` clears both `STORE.users` and `STORE.audit`, matching the isolation pattern in `tests/test_billing.py:8-10`; `tests/` mirrors `app/` per `docs/testing.md`.
- [`app/audit.py:5`] The docstring states the rule at the point of use; the commit message cites the rule it is honouring and says what it does *not* do (no migration, no behaviour change) — which made the review cheap to verify.

## Verified
- **Problem is real on `main`:** `git grep -i audit main` returns nothing; there is no trail of user creation anywhere in the base.
- **Sketches made before reading the diff:** (1) append an entry to a new list on `Store` from `users.create_user`; (2) emit through a dedicated `logging` logger — rejected because support needs a queryable trail and the logging rule makes log sinks the risky place; (3) record at `api.api_create_user` — rejected because it misses direct `users.create_user` callers (`tests/test_billing.py:13`, future support tooling). The diff is sketch 1.
- **5a alignment, claim by claim:** in-memory append-only list (`app/db.py:13`, only `.append` in app code); id never email (`app/users.py:21`, `git grep email -- app/audit.py` hits only the docstring); additive only (diff is +31/−0, no deletions — 5c angle 2 has nothing to check); no migration (`Store` is process memory and `migrations/001_init.py` is a no-op, so there is no schema to migrate); no behaviour change for existing callers (sole non-test caller `app/api.py:5` consumes the unchanged return value; full suite green).
- **5c line-by-line / pitfalls:** `from . import audit` introduces no cycle (`audit → db` only; import graph grepped). `record(..., event=...)` collides loudly (`TypeError`), not silently. `record` returns the stored dict object itself (`e is STORE.audit[-1]` → True) — same pattern as `create_user` returning the stored user dict, so not a new hazard. `audit.py` binds `STORE` at import exactly as `users.py`/`billing.py`/`support.py` do; tests mutate in place and never rebind.
- **5d tracer:** callers of `create_user`: `app/api.py:5`, `tests/test_billing.py:13`, `tests/test_users.py:12`, `tests/test_audit.py:13,19`. No new precondition, exception, or return shape. `Store()` is constructed once (`app/db.py:22`).
- **Test isolation of the shared singleton:** `tests/test_users.py` and `tests/test_billing.py` do not clear `STORE.audit`, so entries accumulate across them; harmless because nothing there asserts on it and `test_audit.setUp` clears it. Confirmed by running the suite in reversed module order (users → billing → audit): 5/5 pass.
- **5e architecture:** no `docs/architecture.md`; `audit` depends only on `db`, same layer as `billing`/`support`.
- **5f conventions:** `unittest`, `tests/` mirrors `app/`, commit subject matches the repo's `type(scope): Sentence` style. CLAUDE.md "reuse helpers in app/util.py" — no parsing/validation added. "Every change to app/billing.py requires failure-path tests" — `billing.py` untouched.
- **5g security:** no new external input; `create_user` already receives a parsed payload; nothing user-controlled reaches the entry except the integer id.
- **5h privacy:** only `user_id` stored (CLAUDE.md rule); `name` and `email` excluded; retention = process lifetime, identical to every other collection. No `docs/privacy.md` exists; judged against the CLAUDE.md rule, which is the project's policy here.
- **5i testing:** 2 new tests, both exercised live; suite 5/5 on the branch, 3/3 on `main`.
- **5j load-bearing assumptions:** the change rests on nothing external; the one runtime assumption (dict-display `**fields` merge, relative import of a sibling module) was verified by execution rather than docs.
- **5k top-3 production risks:** (1) an entry leaks email/PII → covered by `test_audit_entries_carry_no_email`; (2) `create_user` regresses or the new import breaks startup → covered by any test run importing `app.users` plus `test_users`/`test_billing`; (3) unbounded growth of `STORE.audit` in a long-lived process → uncovered, but inherent to the in-memory store (Known limitations).
- **5l reversibility:** pure addition; `git revert` is clean; no migration, no external side effects, no flag needed.
- **5m dependencies:** none added.
- **Occam pass:** `app/audit.py` as a module with one caller was walked against the CLAUDE.md id-only rule and the "trail" ask — it is the natural choke point (see S2) and will have a second caller the moment any other event is audited; collapse declined. `record` returning the entry is unused by its one caller — trivial, not raised. No premature optimisation, speculative flags, over-defence, reinvention, or band-aids found.
- **Gap sweep:** fresh re-read of the three app hunks and both tests for dropped guards, flipped defaults, setup/teardown asymmetry, predicate side effects, and definition-time defaults — nothing new. Empty sweep.
- **Independent defect-first read (subagent, un-anchored — given only the worktree, the diff and the rulebook):** "no defects found" after reading every hunk, the enclosing modules, the untouched neighbours and running the suite in three module orders. Its non-defect observations were the same three as mine (S1 timestamp, S2 docstring-only guard, the "failure paths covered" wording) plus the cross-class `STORE.audit` leak, which I added to Gaps. Its first attempt reviewed the wrong checkout because the shared scratchpad path was swapped by a parallel process; that output was discarded and the read redone on a uniquely named worktree.

## Not reviewed
- CI: no remote and no PR, so no `gh pr checks`; the local suite stands in.
- `migrations/001_init.py` and the (no-op) migration framework, accepted as-is.
- `app/billing.py`, `app/support.py`, `app/api.py` beyond their roles as callers/neighbours — unchanged by this diff.
- Absent docs not needed for this diff: `docs/architecture.md`, `docs/privacy.md`, `docs/security.md`.
- The sibling branch `feature/discounts` (the checkout's current HEAD) — out of scope.

Baseline check: primary checkout remained on `feature/discounts` at `e933af9` with a clean `git status` throughout; experiments ran in detached worktrees under the scratchpad, since removed. Nothing pushed, posted, or triggered.

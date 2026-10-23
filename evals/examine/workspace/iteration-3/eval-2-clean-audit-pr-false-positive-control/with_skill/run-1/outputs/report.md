# Examine: Record an audit event on user creation (feature/audit-log vs main)

## Headline
Merge. The change does what the description says, honours every project rule it touches, and carries no issue above Low.

Mode: full, chosen because the change touches user identity data and the diff is small enough that full costs little. Target: `git diff main...feature/audit-log` (merge-base `ddb5aa6`, head `f3b98d6`, 4 files, 31 insertions). The working tree was clean.

## Approach fit
Matches the obvious approach. The sketch was "add `STORE.audit`, append an event dict from `create_user`, keep the entry shape in one small helper". The diff is that sketch.

## Issues

### Low (defer)
- **L1** [app/audit.py:6, app/users.py:21] The entry carries `event` and `user_id` but no timestamp. Support asked for "who and when", so "when" needs a join to `STORE.users[user_id]["created_at"]`. Consider `at=user["created_at"]`.
- **L2** [tests/test_audit.py:20] The test asserts the key `email` is absent, not the address. `assertNotIn("a@b.c", str(STORE.audit[0]))` tests the rule the test is named for.

## Questions
- **Q1** [tests/test_audit.py] The description says "failure paths covered in tests/test_audit.py". Which failure path did you mean? The file has a happy-path test and a no-email property test, and `record` has no failure branch to test.

## Suggestions

#### S1: Make `record` reject an `email` field instead of relying on the docstring
- **Locator:** `app/audit.py:4-7`
- **What:** `record(event, **fields)` accepts any keyword. A probe `record("probe", email="leak@x.y")` stores the email. Today the only caller passes `user_id`, and `test_audit_entries_carry_no_email` guards that one caller.
- **Why it would be better:** The CLAUDE.md rule "Never log or store raw emails outside the users table" becomes a check, not a convention. The next caller cannot leak by accident, and the test suite no longer has to grow one no-email test per event type.
- **Sketch:**
  ```python
  if "email" in fields:
      raise ValueError("audit entries reference users by id, never by email")
  ```

## Gaps
- The commit body overstates the test coverage. See Q1. The tests that exist are the right ones for this code.

## Known limitations
- `STORE.audit` grows without bound for the life of the process. `STORE.charges` already behaves the same way, and `app/db.py:1` describes the store as a stand-in for a database. Document it where the real persistence lands.
- The store write and the audit append are two steps (`app/users.py:20-21`). Today `record` has no raising path, so the pair cannot split. With a real sink, a failed append would leave a stored but unaudited user. Note it where the sink is introduced.
- "Append-only" (`app/db.py:13`) is a convention. `STORE.audit` is a plain list and `record` returns the stored dict, so any caller can rewrite an entry. Every collection in `Store` is mutable the same way, so a guard here alone would buy little.

## What was done well
- [app/users.py:21] The audit call comes after the store write. No event is recorded for a user that failed to persist.
- [app/audit.py:5] The docstring restates the id-only rule from CLAUDE.md at the one place a future caller will read.
- [tests/test_audit.py:18] The privacy rule is a test, not only a comment. A regression fails CI instead of a review.
- [tests/test_audit.py:8-10] `setUp` clears both `users` and `audit`, so the two tests are order-independent.
- [commit body] The constraints are stated and the diff honours them: additive only, no migration, no change for existing callers.

## Verified
- Tests: 5 of 5 pass on `feature/audit-log`, 3 of 3 on `main`, Python 3.15.0, run in a throwaway clone.
- Imports: `app.audit` imports `app.db`, and `app.users` imports both. No cycle. `app.audit.STORE is app.db.STORE` holds.
- 5a alignment: in-memory, append-only, id only, additive, no migration. Each claim matches a hunk.
- 5b problem: "who" is answered by `user_id`. "When" is answered through the users table. See L1.
- 5c, five angles: no removed lines, no wrapper, one append per creation. `record("x", event="y")` raises `TypeError`, so the `event` key cannot be overwritten through `**fields`.
- 5d tracer: the only production caller of `create_user` is `app/api.py:5`. Signature and return shape are unchanged. `Store()` is constructed once, at `app/db.py:22`.
- 5f conventions: `tests/test_audit.py` mirrors `app/audit.py` per `docs/testing.md`. The commit subject follows the repo's `type(scope): Subject` form. CLAUDE.md rules on money, `app/util.py` reuse, and `app/billing.py` tests do not apply to this diff.
- 5h privacy: entries hold a user id, which CLAUDE.md names as the allowed reference. No `docs/privacy.md` exists. Judged against the CLAUDE.md logging rule.
- 5i testing: `docs/testing.md` requires failure-path tests for money and lookup paths. Audit is neither, so no rule is violated.
- 5k top three production risks, each with its covering test:
  - An import error at startup. Covered: every test module imports `users`.
  - A half-committed create, where the user is stored but the event is not. Covered: `test_user_creation_is_audited`.
  - An email in the trail. Covered for the current caller by `test_audit_entries_carry_no_email`. Future callers are not covered, see S1.
- 5l reversibility: no migration and no schema. Reverting removes four hunks and loses only the in-memory trail.
- Refuted, new store without a migration: `migrations/001_init.py` names users and charges, but `main` already added `discounts` to `Store` with no migration, and `up()` is a no-op. The precedent holds.
- Refuted, test teardown asymmetry: `tests/test_users.py` and `tests/test_billing.py` do not clear `STORE.audit`. No test outside `test_audit.py` reads the trail, and `test_audit.py` clears it in `setUp`.
- Refuted, module-level `STORE` binding: `app/audit.py:1` binds `STORE` at import, so swapping `app.db.STORE` would not redirect it. `users.py`, `billing.py`, and `support.py` bind the same way. Consistent with the codebase.
- Occam, `app/audit.py` as a separate module: collapsing `record` into `create_user` saves six lines and removes the one place that documents the id-only rule. Walked against the CLAUDE.md email rule and the `tests/` mirrors `app/` convention. No operational cost, no finding.
- Host built-in review (`code-review`, effort high) ran in a subagent against a throwaway clone. It found no correctness bug. Its five candidates map to L1, L2, S1, the two refutations above, and the two-step write under Known limitations.
- Verification was single-context for L1, L2, and S1, which the rubric allows for Low and Suggestions. No Medium or higher candidate survived to need an independent verifier.

## Not reviewed
- No `docs/architecture.md`, `docs/security.md`, or `docs/privacy.md` exists. The diff adds no external input and no new personal field, so none was needed.
- 5m dependencies: none added.
- The pre-existing absence of a duplicate-email check in `create_user` (`app/users.py:20`). The diff does not change it.
- The sibling branch `feature/discounts` and its merge order relative to this one.
- Pre-existing, outside the diff: `app/billing.py:19` computes tax with float arithmetic, which `docs/invariants.md §2` forbids. Worth its own fix. This change does not touch it.

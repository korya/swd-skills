# Examine: Record an audit event on user creation (feature/audit-log vs main)

## Headline

Merge. The change is small, additive, and correct, and it keeps raw emails out of the audit trail. No issue blocks the merge. One question and three suggestions are optional follow-ups.

Review facts:

| Item | Value |
|---|---|
| Target | `feature/audit-log` at `df4cef6`, merge base `9dc8a5c` on `main` |
| Diff | 4 files, 31 insertions, 0 deletions |
| Mode | full |
| Tests | 5 of 5 pass on the branch (`python3 -m unittest discover tests -v`, Python 3.15.1) |

The mode is full because the change touches user records and makes a privacy claim. The diff is small, so the full pass was cheap.

## Approach fit

The change matches the obvious approach: an append-only list in the store, written from `create_user`.

Before I read the diff, I sketched three approaches for "a trail of who was created and when":

- Append an entry to an in-memory list on `Store` from `users.create_user`.
- Emit a line through Python `logging` with the user id.
- Add a generic event hook that observers subscribe to.

The first sketch fits a codebase whose store is in memory, and the diff implements it. The other two add moving parts that nothing in the repo asks for.

## Issues

No qualifying issues.

## Questions

- **Q1** [`app/audit.py:6`] Do you want the audit entry to carry its own timestamp? Support asked for "who was created and when". Today the "when" comes only from `STORE.users[user_id]["created_at"]`, so a reader must join the two stores.

## Suggestions

#### S1: Enforce the "no raw email" rule in code, not only in a docstring
- **Locator:** `app/audit.py:4-5`
- **What:** `record` accepts any keyword. The rule "callers pass ids, never raw emails" lives only in the docstring. A guard such as `assert "email" not in fields` makes a breach fail loudly in tests.
- **Why it would be better:** The next caller of `record` gets an immediate signal instead of a silent breach. The CLAUDE.md rule says "Never log or store raw emails outside the users table". This is optional. The only caller today passes `user_id` alone.

#### S2: Check the stored values in the "no email" test, not only the key name
- **Locator:** `tests/test_audit.py:18-20`
- **What:** `assertNotIn("email", STORE.audit[0])` checks the dict keys only. An entry such as `{"event": ..., "who": "a@b.c"}` passes it. Also assert that the email string is absent from the values, for example `self.assertNotIn("a@b.c", repr(STORE.audit))`.
- **Why it would be better:** The test then protects the CLAUDE.md rule itself, not one field name.

#### S3: Return a copy, or nothing, from `record`
- **Locator:** `app/audit.py:8`
- **What:** `record` returns the same dict it stores. A caller that changes the returned dict also changes the "append-only" trail. A probe showed this: `e = audit.record("x", user_id=1); e["user_id"] = 99` changes `STORE.audit[-1]`.
- **Why it would be better:** The append-only promise in `app/db.py:13` then holds for every caller. No current caller uses the return value. This is a foot-gun for later, not a defect now.

## Gaps

- The commit message says "failure paths covered in tests/test_audit.py". The file has a happy-path test and a "no email" test. `record` has no failure path to test, so the code misses nothing. Only the wording of the description overstates the tests. No project rule requires failure-path tests here. `docs/testing.md` asks for them on money and lookup paths only.

## What was done well

- [`app/users.py:21`] The audit call passes `user_id=user["id"]` and nothing else. This follows the CLAUDE.md rule "reference users by id".
- [`app/users.py:20-21`] The audit entry is written after the user is stored. A reader of the audit log never sees an id that the users store does not have.
- [`app/db.py:13`] The new `audit` list sits beside `users`, `discounts`, and `charges` and follows their pattern. The change adds no new storage mechanism.
- [`tests/test_audit.py:8-10`] `setUp` clears both `STORE.users` and `STORE.audit`. The test therefore does not depend on audit entries left by `test_users` or `test_billing`.
- [`tests/test_audit.py:16`] The test compares against `u["id"]`, not a literal `1`. It stays correct while the global `_ids` counter keeps counting across test modules.
- [`tests/test_audit.py`] The new test file mirrors `app/audit.py`, as `docs/testing.md` asks ("`tests/` mirrors `app/`").

## Verified

Each check below passed, with the evidence named.

- **The problem is real.** On `main`, `Store` has no audit field and `create_user` records nothing (`git show main:app/users.py`).
- **No caller breaks.** `api.api_create_user` and three tests are the only callers of `create_user`. The return value keeps the same keys: `created_at`, `email`, `id`, `name`, `plan`. `record` adds no exception path that a realistic input reaches.
- **No import cycle.** `users` imports `audit`, which imports `db`. The full test suite passes on the branch.
- **A caller cannot overwrite the event name.** Python binds a keyword `event` to the named parameter, so `fields` never holds a second `event`. The probe `audit.record("x", event="y")` raises `TypeError: record() got multiple values for argument 'event'`.
- **No migration is needed.** The store is in memory and the constructor creates the field. `migrations/001_init.py` is a no-op. The existing `discounts` store has no migration either. `docs/invariants.md` §3 does not apply, because nothing persists.
- **Reversibility is clean.** The change has no external side effect, no persisted data, and no deleted line. A revert removes it fully.
- **Test isolation is sound.** `test_users` and `test_billing` do not clear `STORE.audit`, so entries pile up across modules. This has no effect, because `test_audit` clears the list before each test.
- **Ordering is safe.** The user is stored before `record` runs. If `record` raised, a user would exist without an audit entry. It cannot raise on this path. It only builds a dict and appends it to a list.

Top three production risks and their coverage:

| Risk | Covering test |
|---|---|
| A raw email reaches the audit trail | `test_audit_entries_carry_no_email` (key name only, see S2) |
| User creation breaks or changes shape | `test_creates_user_with_default_plan`, `test_charge_known_user` |
| The audit entry is missing or names the wrong user | `test_user_creation_is_audited` |

The Occam pass found nothing to cut. Collapsing `app/audit.py` into `users.py` would remove the one place that states the email rule. It would also scatter future event writes. I walked this against the CLAUDE.md email rule and the commit's "additive only" constraint.

The host's built-in review ran in a subagent as one more candidate source. It reported no defects. No candidate reached Medium, so no per-candidate verifier ran. The gap sweep found nothing new.

## Not reviewed

- No `docs/architecture.md`, `docs/security.md`, or `docs/privacy.md` exists. The diff adds no endpoint, no input parsing, and no new personal data. The privacy check used the CLAUDE.md email rule.
- No CI or PR checks exist for this local branch. The local test run replaces them.
- The diff changes no dependencies, so the dependency audit had nothing to check.
- The review does not judge retention of the audit trail. The whole store is in memory, and no retention policy exists to compare against.

# Examine: Record an audit event on user creation (feature/audit-log vs main)

## Headline

Merge. The change does what it claims and follows the privacy rule in `CLAUDE.md`. It breaks no caller. The findings below are two Low issues and two optional improvements.

**Target:** branch `feature/audit-log` at `b3c7a94`, diffed against the merge-base with `main` (`6c6bffa`).
The diff adds 31 lines in 4 files.

**Mode:** full. The change stores data about users, and the skill runs full mode for personal data.
The host's built-in review ran in a subagent as one more source of candidates.

## Approach fit

The change matches the most obvious approach. A new `audit` list on the store holds the entries, and `create_user` appends one entry after the insert.

The sketches made before the diff was opened were:

- Append `{event, user_id}` to a new list on `Store` from `create_user`.
- Write a line through the Python `logging` module, with the user id.
- Add a separate append-only table and a migration with `down()`.

The change is the first sketch with an 8-line helper module. The repo has no real migration for the existing stores, so the third sketch adds nothing here.

## Issues

### Low (defer)

- **L1** [`tests/test_audit.py:18-20`] The test against email leaks checks only the key `"email"`. A mutation that stored `who=email` passed all 5 tests. Assert the exact key set, or assert that the email value appears in no entry value.
- **L2** [`scope: PR`] The description says "failure paths covered in tests/test_audit.py", but both tests use valid input. The behavior is correct. A probe with `create_user(None, "X")` raised `AttributeError` and left 0 users and 0 audit entries. Add that case as a test, or drop the claim.

## Questions

- **Q1** [`app/audit.py:6`] Support asked "who was created and when". The entry holds no time, so support must join `user_id` to `users[id]["created_at"]`. Is that join the intended way to answer "when"?

## Suggestions

#### S1: Put a timestamp in each audit entry

- **Locator:** `app/audit.py:6`
- **What:** `record` stores only the event name and the fields that the caller gives.
- **Why it would be better:** An audit trail usually stands on its own. Today "when" depends on the user row. That row exists now because no code deletes users. A future delete or anonymization path would remove the only time of the event.
- **Sketch:** `entry = {"event": event, "at": time.time(), **fields}`.

#### S2: State "append-only" as a convention, or enforce it

- **Locator:** `app/db.py:13`
- **What:** The comment calls `STORE.audit` append-only, but it is a plain list. Any code can call `clear()` or `pop()`, and the tests call `clear()`. Also, `record` returns the stored dict (`app/audit.py:8`), so a caller can change an entry after the write.
- **Why it would be better:** A reader can take the comment for a guarantee. For an in-memory fixture, a reworded comment is enough. A real store needs a write path that only appends.

## Gaps

- The `setUp` methods in `tests/test_users.py` and `tests/test_billing.py` do not clear `STORE.audit`. Entries collect across test modules. `TestAudit` clears the list itself, so no test fails today.

## What was done well

- [`app/users.py:21`] The record call comes after the insert at line 20. A failed creation therefore writes no audit entry. The probe in L2 confirmed this.
- [`app/users.py:21`] The entry carries `user_id` only. This follows the rule in `CLAUDE.md` that bans raw emails outside the users table.
- [`app/audit.py:4`] `event` is a positional parameter, so `**fields` cannot overwrite it. A probe with `record("x", event="y")` raised `TypeError`.
- [`tests/test_audit.py:12-16`] The test checks the event name and the exact `user_id`, not only that an entry exists.

## Verified

- **Problem in the base.** `main` has no audit trail and no logging helper. `git grep -i "audit\|log" main` finds only the privacy rule in `CLAUDE.md`.
- **Tests.** `python3 -m unittest discover tests -v` on `b3c7a94` ran 5 tests. All 5 passed.
- **Callers.** `create_user` keeps its return shape (`created_at, email, id, name, plan`). Its only callers are `api.api_create_user` and the tests. No other code path writes to `STORE.users`.
- **Imports.** `audit` imports `db`, and `users` imports both. The import graph has no cycle.
- **Privacy.** `CLAUDE.md` bans raw emails outside the users table. The entry holds no email and no name.
- **Testing rule.** `docs/testing.md` requires failure-path tests for money and lookup paths. `create_user` is neither, and the diff does not touch `app/billing.py`. No documented test rule applies.
- **No migration (REFUTED as a finding).** The host review asked whether `STORE.audit` needs a migration under `docs/invariants.md §3`. `migrations/001_init.py` has empty `up()` and `down()` bodies, and the `discounts` store on `main` has no migration either. The repo does not treat in-memory stores as migrated schema.
- **Write atomicity (REFUTED as a finding).** The host review noted that the user insert and the audit append are two writes. The append is `STORE.audit.append(entry)` on a plain list (`app/audit.py:7`), with a dict built from keyword arguments. No realistic input makes it raise after the insert.
- **Reversibility.** The change is additive and in memory. A revert removes it with no data to migrate.
- **Dependencies.** The diff adds no dependency.
- **Occam pass.** `app/audit.py` is a one-function module with one caller. It could fold into `users.py`. The pass checked it against the privacy rule in `CLAUDE.md` and the stated scope. The module keeps the rule "ids, never emails" in one place. The next audited event can reuse it. The cost is one small file, so no finding.
- **Gap sweep.** The diff moves and deletes no code. It adds a side effect after the insert. No code constructs `Store` again or iterates over its attributes. The sweep found no new candidate.
- **Verification method.** No candidate reached Medium, so no candidate needed an independent verifier. The two Low issues rest on the probes quoted above.

The top three production risks and their tests:

| Risk | Covering test |
|---|---|
| Creation writes no entry, or the wrong `user_id` | `test_user_creation_is_audited` |
| An email reaches the audit list | `test_audit_entries_carry_no_email`, key `"email"` only (L1) |
| The new side effect breaks `create_user` callers | `test_users`, `test_billing`, all pass |

## Not reviewed

- Pre-existing code on `main` that the diff does not touch is out of scope. Two items deserve a separate ticket:
  - `billing.charge` computes the total with float arithmetic (`app/billing.py:18`). This conflicts with `docs/invariants.md §2`.
  - `billing.charge` and `support.lookup` do not normalize the incoming email before `find_user_by_email`. A charge for `"A@B.c"` fails for a user stored as `"a@b.c"`. See `docs/invariants.md §1`. The host review reported this, and this review did not run it.
- Retention and growth of `STORE.audit`. The repo has no retention policy, and the store is an in-memory fixture.
- CI. The repo has no CI configuration and no remote.
- No security axis applies. The diff reads no outside input and adds no endpoint.

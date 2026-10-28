# Examine: Record an audit event on user creation (feature/audit-log vs main)

Target: branch `feature/audit-log` at `2dcd943`, diffed from the merge-base `5f1e0b7` with `main`.

Mode: full. The change exists to route personal data correctly, so the email rule in `CLAUDE.md` is load-bearing.

## Headline

Merge. The change does what its description says, keeps raw emails out of the audit trail, and breaks no existing caller.

The two Low issues below are optional polish. Neither blocks the merge.

## Approach fit

The change matches the obvious approach: an append-only list on the store, written from `create_user` with the user id.

I sketched three approaches from the description:

- Add an append-only audit list to `Store` and record an event in `users.create_user`.
- Answer Support from the existing `STORE.users` records, which already hold `id` and `created_at`.
- Emit a structured log line with the user id at creation.

The diff uses the first. Process note: the diff appeared in the same tool output as the base files, so the sketch was not fully blind.

## Issues

### Low (defer)

- **L1** [`app/audit.py:6`] The entry holds `event` and `user_id` only, with no timestamp. A probe printed `{'event': 'user.created', 'user_id': 1}`. The "when" half of the request needs a join to `users.created_at`. Fix: add `"at": time.time()` in `record`.
- **L2** [`tests/test_audit.py:20`] The privacy test checks the key name `email` only. A probe that stored the email under a key `who` passed both tests. Cites the email rule in `CLAUDE.md`.

## Questions

- **Q1** [`scope: PR`] The description says "failure paths covered in tests/test_audit.py", but both tests exercise the success path. Which failure path did you mean? `docs/testing.md` requires failure-path tests only for money and lookup paths, so no rule is broken.
- **Q2** [`scope: PR`] The users table already answers "who was created and when". Does Support need the trail to outlive later edits or deletes of user records? If yes, L1 matters more.

## Suggestions

#### S1: Enforce the no-email rule inside `audit.record`

- **Locator:** `app/audit.py:4`
- **What:** Only the docstring enforces "Callers pass ids, never raw emails". Any future caller can pass an email in `**fields`.
- **Why it would be better:** The rule in `CLAUDE.md` would then hold for every caller, not only for the one caller in this diff.
- **Sketch:** Reject a key named `email` and any string value that contains `@`. Raise `ValueError`.

## Known limitations

- The audit list lives in memory. It grows without a bound and resets on restart. `STORE.charges` behaves the same way, and the store is a stand-in for a database.

## What was done well

- [`app/users.py:21`] The event carries `user_id=user["id"]` and nothing else. This follows the `CLAUDE.md` rule to reference users by id.
- [`app/users.py:21`] The record call comes after the write to `STORE.users`. An entry never names a user that the store does not hold.
- [`tests/test_audit.py:8-10`] `setUp` clears both `users` and `audit`. The `len == 1` assertion therefore holds in any test order.
- [`tests/test_audit.py`] The new test file mirrors `app/audit.py`, as `docs/testing.md` asks.

## Verified

The top three production risks and their covering tests:

| Risk | Covering test | Status |
|---|---|---|
| A raw email reaches the audit trail | `test_audit_entries_carry_no_email` | Partial, see L2 |
| `create_user` stops recording, or records the wrong id | `test_user_creation_is_audited` | Covered |
| An existing caller of `create_user` breaks | `test_users`, `test_billing` | Covered, all pass |

Other checks:

- **Tests.** `python3 -m unittest discover tests -v` in a detached worktree ran 5 tests. All passed. The repo has no CI configuration.
- **Callers.** The signature and return value of `create_user` are unchanged. `api.api_create_user` and the test fixtures call it as before.
- **Imports.** `users` imports `audit`, and `audit` imports `db`. There is no import cycle.
- **Migrations.** The diff adds no migration, and none is needed. `Store.discounts` exists on `main` without a migration, because `migrations/001_init.py` lists only users and charges. `docs/invariants.md §3` governs migrations, and the diff adds none.
- **Reversibility.** A revert drops an in-memory list. No persisted data or external side effect is involved.
- **Sibling branch.** `git merge-tree` of `feature/audit-log` and `feature/discounts` completed with no conflict.
- **Host review.** A read-only subagent ran a defect-first review. It found the same three low candidates and no defect. Its third candidate is below.
- **Refuted.** `record` returns the stored dict, so a caller could mutate the trail. The only caller discards the return value (`app/users.py:21`), so the effect is not observable today.
- **Occam pass.** `app/audit.py` is one small function with one caller. It is not speculative generality, because Support asked for a trail. I checked it against the request and the email rule. The overlap with `users.created_at` is Q2.
- **Verification.** No candidate reached Medium, so no independent verifier ran. Probes confirmed L1 and L2. The gap sweep found nothing new.

## Not reviewed

- **Security (5g).** The diff adds no outside input, endpoint, or query.
- **Dependencies (5l).** The diff adds no dependency.
- **Architecture (5e).** The repo has no layering doc. The new module follows the existing pattern of a module that writes to `STORE`.
- **Load-bearing assumptions (5j).** The change rests on no library or runtime behavior beyond core Python.

# Examine: Record an audit event on user creation (feature/audit-log vs main)

## Headline
Merge. The change does what its description says, keeps raw emails out of the audit trail, and passes all 5 tests.

The review ran in full mode. The diff touches the CLAUDE.md rule on raw emails, and personal data triggers full mode. The review compared `main...feature/audit-log` at merge base `76b82c4` and head `c002166`.

## Issues
No qualifying issues.

## Questions
- **Q1** [scope: PR] The description says "failure paths covered in tests/test_audit.py". Which failure path does this mean? The only non-happy test is `test_audit_entries_carry_no_email`, and `create_user` has no failure branch to cover.

## Suggestions

#### S1: Put the timestamp in the audit entry
- **Locator:** `app/users.py:21`
- **What:** Record the creation time in the entry, for example `audit.record("user.created", user_id=user["id"], at=user["created_at"])`.
- **Why it would be better:** Support asked for "who was created and when". Today the entry answers "when" only through a join into `STORE.users`. A self-contained entry still answers it if the user record changes or goes away later.

#### S2: Assert that no email value appears in the entry
- **Locator:** `tests/test_audit.py:20`
- **What:** Also assert that the email string is absent from the entry values, for example `self.assertNotIn("a@b.c", STORE.audit[0].values())`.
- **Why it would be better:** The current test checks only the key name `email`. It does not catch an email stored under another key, such as `actor="a@b.c"`.

## Known limitations
- The audit trail lives in memory and is lost on restart. This is acceptable because the whole `Store` is an in-memory stand-in for a database (`app/db.py:1`).
- The trail is append-only by convention only. `STORE.audit` is a plain list, and `record()` returns the stored dict, so a caller can mutate or clear it. `STORE.charges` has the same shape, so the change follows the existing pattern.
- `audit.record(**fields)` enforces the "ids, never raw emails" rule through its docstring only. No current caller passes an email. A guard for a caller that does not exist would be speculative.

## What was done well
- [app/users.py:21] The call passes only `user_id`. This follows the CLAUDE.md rule "Never log or store raw emails outside the users table".
- [app/users.py:20-21] The audit append runs after the insert into the users table. A user cannot get an audit entry without a stored record.
- [tests/test_audit.py:18-20] A dedicated test guards the privacy rule, not only the happy path.
- [app/audit.py:5] The docstring states the rule at the place a future caller reads it.
- [app/db.py:13] The new store follows the existing field pattern in `Store.__init__`.

## Verified
- **Problem exists in the base.** `main` has no audit module and no audit store. Nothing records user creation.
- **Approach fit.** Before the diff was read, the review sketched three approaches. The first was an in-memory list on `Store` with an append in `create_user`. The second was the Python `logging` module. The third was a persisted table with a migration. The change matches the first sketch.
- **Alignment (5a).** Every claim in the description holds, except the wording in Q1. The log is additive and holds only the user id. The tests exist.
- **Correctness (5c).** A probe with `"  A@B.C "` produced `{'event': 'user.created', 'user_id': 1}`, with no email in the entry. A list append cannot raise, so `create_user` gains no new exception.
- **Language pitfall (5c).** `record("x", event="y")` raises `TypeError: multiple values for argument 'event'`. No caller passes `event` as a field, so the error is unreachable today.
- **Callers (5d).** The only caller of `create_user` outside the tests is `app/api.py:5`. The return shape of `create_user` is unchanged. Nothing else constructs `Store`.
- **Migrations (docs/invariants.md §3).** No migration is needed. `migrations/001_init.py` is a no-op and already omits the `discounts` store, so the repo does not declare stores in migrations.
- **Money and lookup rules (docs/invariants.md §1, §2, docs/testing.md).** The diff does not touch a money path or a lookup path. Normalization in `create_user` still runs before the write.
- **Test isolation.** `tests/test_users.py` does not clear `STORE.audit`. `tests/test_audit.py` clears it in `setUp`, so the order of the test files does not matter. The tests passed in both discovery order and the order audit, users, billing.
- **Top three production risks (5k).**
  - Audit recording breaks user creation. `test_user_creation_is_audited` and `test_creates_user_with_default_plan` cover it.
  - A raw email leaks into the trail. `test_audit_entries_carry_no_email` covers the `email` key. S2 widens the check.
  - The trail grows without bound. No test covers it. It is acceptable because `STORE.users` and `STORE.charges` grow the same way and no scale requirement exists.
- **Reversibility (5l).** A revert removes one module, one field, one call, and one test file. No external side effect, schema change, or data migration exists.
- **Occam pass (6).** The review checked whether `app/audit.py` could collapse into `create_user`. It was walked against the CLAUDE.md email rule and the support request. The module is 8 lines and holds the email rule in one place. Collapsing it saves no concept, so the review makes no proposal.
- **Independent review.** A separate defect-first reviewer read the same checkout and found no defects. Its two nits became S2 and the third known limitation. Verification was not needed because no candidate reached Medium. The gap sweep found nothing new.

## Not reviewed
- Security (5g): the diff adds no input surface, endpoint, or secret.
- Dependencies (5m): the diff adds no dependency.
- Architecture (5e): the repo has no `docs/architecture.md`, and the diff adds no layer.
- No `docs/privacy.md` exists. The privacy check used the CLAUDE.md email rule.
- CI: the fixture has no remote and no PR, so `gh pr checks` does not apply. The review ran the tests locally.
- The unmerged branch `feature/discounts` also changes `app/users.py` and `app/db.py`. Its interaction with this change is out of scope.

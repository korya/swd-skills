# Examine: Record an audit event on user creation (feature/audit-log vs main)

## Headline
Merge after one small fix. The audit entry records who was created but not when, and the commit names both.

## Issues

### Medium (worth fixing now; acceptable as a follow-up)

#### M1: Audit entries carry no timestamp, so the trail cannot answer "when"
- **Locator:** `flow: app/users.py:21 → app/audit.py:6`
- **Changed anchor:** `app/users.py:21` and `app/audit.py:6` (both new)
- **What:** The commit states the problem as "a trail of who was created and when". `record` builds `{"event": event, **fields}` and the only caller passes `user_id`. The entry is `{"event": "user.created", "user_id": 1}`. A reader must join to `STORE.users[user_id]["created_at"]` to learn the time.
- **Evidence:** A probe run against the exported branch returned the entry above with no time key. `tests/test_audit.py:14-16` assert only `event` and `user_id`. No code in `app/` deletes a user row today, so the join works for now.
- **Verdict:** CONFIRMED. An independent verifier reproduced the entry shape from the code and rated the impact low while no delete path exists.
- **Why Medium:** The change leaves half of its stated requirement to a join on a mutable table. A future `user.deleted` event, or any erasure, removes the row and with it the "when" for exactly the cases an audit trail exists for. The fix is one line, so a committed follow-up is acceptable.
- **Fix:** Stamp the time inside `record`, so every event carries it without each caller remembering. For example `entry = {"event": event, "ts": time.time(), **fields}`. Add an assertion for the key in `test_user_creation_is_audited`.

No Critical, High, or Low issues.

## Questions

- **Q1** [`app/support.py`] How will support read the trail? The diff adds no read path in `support.py` or `api.py`. Is that a planned follow-up?
- **Q2** [`app/users.py:18`] The user row already holds `created_at`. Is the log meant to outlive user rows or to carry more event types? If neither, a sorted read of `STORE.users` answers the request with no new storage.

## Suggestions

#### S1: Make `record` refuse the keys the logging rule forbids
- **Locator:** `app/audit.py:4-6`
- **What:** `record(event, **fields)` accepts any key. The docstring asks callers to pass ids, never raw emails. A check for a small reserved set, such as `email`, would turn the rule into an error at the one place every caller passes through.
- **Why it would be better:** CLAUDE.md forbids raw emails outside the users table. Today one caller complies and one test checks it by key name. The next caller has no guard, and `assertNotIn("email", ...)` would not catch an email passed under another key.
- **Sketch:** `if "email" in fields: raise ValueError("audit entries carry ids, not emails")`, plus a test that `record("x", email="a@b.c")` raises.

## Gaps
- The commit says "failure paths covered in tests/test_audit.py". Both tests are happy-path. `record` is an unconditional append and has no failure path. Reword the description.
- `tests/test_users.py:9` and `tests/test_billing.py:9-10` clear `users` and `charges` but not the new `STORE.audit`. Entries leak across test classes. Nothing asserts on them outside `test_audit`, whose `setUp` clears first, so no test is affected today.
- `tests/test_audit.py:20` checks for an `email` key only, not for an email value under another key.

## Known limitations
- `STORE.audit` grows without bound for the life of the process. `STORE.charges` already behaves this way, and `db.py:1` declares the store an in-memory stand-in for a database. Acceptable for this fixture. Note it in `db.py` next to the attribute.
- "Append-only" is a convention, not an enforcement. `STORE.audit` is a plain list and tests call `.clear()` on it. Acceptable while only `record` writes to it.

## What was done well
- [`app/users.py:21`] The entry carries `user_id`, not the email. This follows the CLAUDE.md rule "never log or store raw emails outside the users table" at the first write site.
- [`tests/test_audit.py:18-20`] A test pins the privacy rule, so a future regression fails CI rather than a compliance review.
- [`app/users.py:20-21`] The audit call runs after the insert. A failed insert leaves no phantom audit entry.
- [`app/db.py:13`] The new store sits next to its siblings with the same shape. No new concept, no new lifecycle.
- [`tests/test_audit.py`] The test file mirrors `app/audit.py`, as `docs/testing.md` asks.
- [commit message] The description names the problem, the approach, the privacy constraint, and the non-goals. It made the review faster.

## Verified
- Target: `git diff d5ab5c0..0e4eca4` (merge-base equals `main`). Four files, 31 added lines, no deletions. The primary checkout sits on `feature/discounts` and was not touched. Code was read with `git show` and tests ran in an exported copy, since removed.
- Mode: full. The diff adds a new store of per-user records and the description invokes the privacy rule, so the "personal data" trigger applies.
- Problem exists in the base snapshot. `create_user` writes only the user row and no module records creation events.
- Three approaches sketched before reading the diff. The change matches sketch 1. Q2 asks whether sketch 3 would have sufficed.
  - Sketch 1: a new `audit` module with a list on `Store`, called after the insert.
  - Sketch 2: a bare `STORE.audit.append` inside `create_user`.
  - Sketch 3: a support query over `created_at` with no new storage.
- No behavior change for existing callers. All 5 tests pass on the branch, including the 3 unchanged ones. `api_create_user` returns the same keys as before.
- "No migration" holds. `migrations/001_init.py` is a no-op, and the `discounts` store was added to `Store` without a migration. Invariants §3 is not engaged.
- Invariants §1 holds. `normalize_email` still runs before the write at `app/users.py:12`. §2 and §4 are not touched.
- Import graph: `users → audit → db`, no cycle. Confirmed by running the test suite.
- REFUTED candidate, partial state on audit failure: `record` does a list append and a dict build. Neither raises on realistic input. The user row cannot exist without its audit entry.
- REFUTED candidate, `event` key collision: `record("x", event="y")` raises `TypeError` at the call, confirmed by a probe. No silent override.
- Reversibility: additive, in-memory, no external side effects. A revert removes the module and the call and leaves nothing behind.
- Dependencies: none added.
- Top three production risks and their coverage.
  - The audit call breaks user creation. Covered by `test_user_creation_is_audited` and the unchanged `test_users`.
  - An email reaches the trail. Covered by `test_audit_entries_carry_no_email` for the one current caller. See S1.
  - The trail cannot serve its reader. Uncovered. See M1 and Q1.
- Occam pass: the `audit` module could collapse into `users.py` (sketch 2). Kept, because it gives the privacy rule one enforcement point and a second event type would otherwise duplicate the entry shape. No premature optimization, speculative flag, or over-defence found.
- Verification used subagents. One blind verifier judged M1. A defect-first reviewer walked the exported checkout and found no medium-or-higher candidate. Its four low-confidence notes are M1 and the three Gaps.

## Not reviewed
- `docs/architecture.md`, `docs/security.md`, `docs/privacy.md`, and `docs/guidelines.md` do not exist. The diff needs none of them beyond the CLAUDE.md email rule, which is cited above.
- CI: there is no remote and no PR, so no checks to read.
- The `feature/discounts` branch checked out in the working tree. It is not part of this change.
- The migration framework, accepted as is.

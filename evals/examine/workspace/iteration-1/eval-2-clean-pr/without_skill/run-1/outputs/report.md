# Review: feature/audit-log → main

**PR intent** (from commit `e6a5fd2`): Support asked for a trail of who was created and when. Adds an in-memory append-only audit log; entries carry the user id, never the raw email. Claims: additive only, no behavior change for existing callers, failure paths covered in `tests/test_audit.py`.

**Scope of diff**: 4 files, +31/−0 — `app/audit.py` (new), `app/db.py` (+1 line, `Store.audit` list), `app/users.py` (+2 lines, record `user.created`), `tests/test_audit.py` (new).

**Verification performed**: full test suite run on the branch (`python3 -m unittest discover tests -v`) — 5 tests, all pass. Diff audited against `CLAUDE.md`, `docs/invariants.md`, and `docs/testing.md`.

## Verdict

**Approve with minor comments.** The change is right-sized, additive, and complies with the repo's privacy rule. Two things deserve attention before merge: audit entries record no timestamp despite "and when" being half of the stated requirement, and the PR description's claim of failure-path coverage is not borne out by the tests.

## What was done well

- Minimal, additive diff that exactly matches its stated scope: no migration needed (in-memory store), no signature or return-value changes, existing callers (`app/api.py`) unaffected.
- Complies with the `CLAUDE.md` rule "never log or store raw emails outside the users table; reference users by id": the entry carries `user_id` only, and `test_audit_entries_carry_no_email` pins that down as a regression test rather than leaving it to convention alone.
- Tests follow the repo conventions in `docs/testing.md`: `unittest`, `tests/` mirrors `app/` (`test_audit.py` ↔ `app/audit.py`), and `setUp` clears shared state (`STORE.users`, `STORE.audit`) so tests are order-independent.
- `audit.record` is a small generic helper (`event` + `**fields`) rather than a user-creation-specific one, so future events (`charge.created`, etc.) can reuse it without rework.

## Issues

### Medium

1. **Audit entries carry no timestamp, but the requirement is "who was created and when".**
   `app/audit.py:record` stores only `{"event": ..., **fields}`; `app/users.py` passes only `user_id`. The "when" is currently recoverable from `user["created_at"]`, but that couples the audit trail to the users table surviving unchanged — if a user record is ever deleted or mutated, the trail loses its "when", which defeats the point of an independent audit log. Fix is one line: stamp `time.time()` (or pass `at=user["created_at"]`) inside `record` so every entry is self-contained.

2. **PR description overclaims test coverage: "failure paths covered in tests/test_audit.py".**
   Both tests are happy-path assertions (event recorded; no email present). There is no failure-path test — nothing exercises what happens if `record` raises mid-`create_user`, or guards against a bad caller. Either add a failure-path test or correct the description; a reviewer relying on the claim would be misled. (Strictly, `docs/testing.md` mandates failure-path tests only for money and lookup paths, so this is a description-accuracy issue more than a convention violation.)

### Low

3. **The no-email rule is enforced only by docstring convention at the write site.**
   `record`'s docstring says "Callers pass ids, never raw emails", but nothing stops a future caller from `audit.record("x", email=...)`. The existing test only checks the `user.created` path. Consider a cheap guard in `record` (e.g., reject an `email` key) so the invariant holds for all future events, not just this one.

4. **`record` returns the same mutable dict it appended**, so a caller mutating the return value silently edits the "append-only" trail. Returning a copy (or nothing) would make the append-only claim structural. Cosmetic at current call sites — the return value is unused.

5. **Ordering: the user is committed to `STORE.users` before `audit.record` runs.** If `record` ever raised, a user would exist with no audit entry. With an in-memory list append this cannot realistically fail today, but it's the kind of gap that matters when the audit sink becomes a real database or network call — worth a comment or a deliberate decision on whether creation should fail when auditing fails.

## Gaps

- No timestamp (issue 1) — the "when" half of the requirement.
- No failure-path tests despite the claim (issue 2).
- Only `user.created` is audited. That matches the PR's stated scope (fine for this PR), but support-relevant mutations like charges (`billing.charge`) have no trail; presumably a follow-up.

## Suggestions

- Add `"at": time.time()` inside `record` plus one assertion in `test_user_creation_is_audited`.
- Guard `record` against an `email` field and test the guard directly (module-level test rather than only via `create_user`).
- Reword the commit/PR description to drop or substantiate "failure paths covered".

## Known limitations (accepted)

- The audit trail is in-memory and lost on restart — consistent with the rest of the fixture app (`app/db.py` is explicitly "a tiny in-memory store standing in for a database"), so acceptable here; durability is a platform concern, not this PR's.
- Unbounded list growth — same in-memory caveat as above.

## Occam pass

The solution is right-sized: a dict-append helper, one store field, one call site, focused tests. No speculative abstraction (no event classes, no listener framework), and nothing simpler would still leave a testable seam. The one thing it under-delivers on is the timestamp (issue 1); with that one-line fix the PR fully meets its stated intent.

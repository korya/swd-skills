# Questions I would have asked (nobody available; proceeding on the stated assumptions)

## Risk gate (step 5)

**Headline: commit 1 conflicts with a new invariant on `main`.** INV-006 (added in 9d38390)
says a command that depends on the current time reads it from the store's clock, never the
system clock. `TicketService.overdue()` as authored defaults `now` to `time.time()`.

Three points: `curr` = 3e7ddfe (feature/overdue), `old_base` = b61ba70 (merge-base),
`new_base` = 9d38390 (main). I took `main` as the target because you named it; `old_base` is
the merge-base, which matches the fixture history (no earlier rebase).

### Q1. How should `overdue()` get the current time?
Options:
- (a) `now = self.store.clock()`; drop the `now=None` parameter. One time source, upholds
  INV-006, tests inject a fake clock through `EventStore(clock=...)` exactly as the
  existing service tests do.
- (b) Keep `now=None` but default it to `self.store.clock()`. More flexible, but opens a
  side door for callers to pass the system clock in, which is what INV-006 forbids.
- (c) Keep `time.time()` and ask to revise INV-006. No: the invariant exists to keep replay
  and tests deterministic, and overdue is exactly the kind of command it targets.

**Assumption: (a), the lowest-risk option.** Nothing on the branch passes `now`.

### Q2. Tests were missing on the branch. Add them inside the feature commits or separately?
The guidelines on `main` (unchanged from `old_base` on this point) say new logic ships
with tests; the new CLI-test convention (delta) says each subcommand ships with its test in
`tests/test_cli.py`. **Assumption: a service unit test goes into commit 1 and a subprocess
CLI test into commit 2**, since the tests belong to the logical change they verify and the
skill says intent-preserving edits stay in the same commit. I did not make separate
"add tests" commits.

### Q3. The uncommitted `debug_notes.md`
It says "notes while debugging the due-time math; delete before merge". Is it related to the
rebase? It reads like scratch notes, not a half-applied fix. **Assumption: unrelated;
stash it, restore it unchanged after the rebase, do not delete it.** Deleting is your
call.

## Plan (step 8)

| Commit | Action | Edits |
|---|---|---|
| e6cdf67 feat(tickets): overdue detection | replay with edits | `ticketdesk/tickets.py`: read `self.store.clock()`, remove `import time` and the `now` param, cite TKT-014/INV-006 in a comment. `tests/test_tickets.py`: add overdue tests (filter, closed excluded, oldest-due-first order). Commit message gains the INV-006 note. |
| e9e90a3 feat(cli): overdue subcommand | replay with edits | `ticketdesk/cli.py`: resolve the two conflicts with `export` (keep both subcommands), print via `_line(t)` instead of a duplicated format string. `tests/test_cli.py`: add `test_overdue` per the new convention. Message cites CLI-010. |
| 3e7ddfe docs(specs): TKT-014, CLI-010 | replay as-is | None. |

### Q4. CLI-001 says `ticketdesk` takes "one of four subcommands"
That was already stale on `main` after `export` landed (the delta added no CLI spec for
`export` either). Commit 3 as authored does not touch CLI-001. Updating a spec needs your
confirmation per `docs/README.md`, so **assumption: leave CLI-001 alone and flag it in the
report.** Same for the "CLI is not covered by tests" lines in `AGENTS.md`,
`docs/architecture.md`, and `docs/guidelines.md`, which the delta made stale.

### Q5. Backup ref
I keep the pre-rebase tip as branch `feature/overdue.pre-rebase` so the old history is one
`git branch -D` away from gone rather than reflog-only. Delete it when you are happy.

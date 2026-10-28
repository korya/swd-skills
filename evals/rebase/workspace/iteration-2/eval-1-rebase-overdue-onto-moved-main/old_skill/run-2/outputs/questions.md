# Questions I would have asked before the rebase

Nobody was available during this run. Each question below states the stop point, the options, and the assumption I proceeded on. I picked the lowest-risk option each time.

## Risk gate (step 5): `overdue()` breaks the new INV-006

Main added INV-006 after the branch started. It says a command that depends on the current time reads the store clock, never the system clock. Commit `4348871` calls `time.time()` directly in `TicketService.overdue()`. A plain replay would land a violation of the floor.

Options:

1. Replay with one edit. When `now` is not given, `overdue()` reads `self.store.clock()`. The `now` parameter, the filter, and the sort stay the same.
2. Replay as is and open a follow-up to fix INV-006 later.
3. Stop the rebase and leave the branch on the old base.

Question: may I take option 1 and keep the edit inside commit `4348871`?

Assumption: yes. Option 1 keeps the original intent, satisfies INV-006, and changes no behavior for a real run. The CLI builds the store with the default clock, which is `time.time`.

## Plan approval (step 8)

The plan replays all three commits in order, with edits to the first two and one new test commit.

| Commit | Action | Change |
|---|---|---|
| `4348871` feat(tickets): overdue detection | replay with edits | Read the time from `self.store.clock()` per INV-006. Drop `import time`. |
| `ec61e0d` feat(cli): overdue subcommand | replay with edits | Resolve the conflict with `export`. Print through the shared `_line()` helper that main added. |
| `638b218` docs(specs): TKT-014 and CLI-010 | replay as is | No change. |
| new | new commit | Add the overdue tests: one subprocess test in `tests/test_cli.py`, one service test in `tests/test_tickets.py`. |

Question: do you approve this plan?

Assumption: yes. Each edit keeps the intent of its commit. The new commit only adds tests.

## The new CLI test convention

Main added a rule to `docs/guidelines.md`. A new subcommand ships with its test in `tests/test_cli.py`. The branch adds `overdue` without a test.

Question: should the test go in its own commit or inside `ec61e0d`?

Assumption: its own commit. The skill puts a fix found during a rebase in a separate commit. The commit also adds a service test that proves the INV-006 edit with the fake clock.

## CLI-001 still says "four subcommands"

CLI-001 lists `create`, `assign`, `close`, and `list`. Main added `export` without an update. The branch adds `overdue` through CLI-010 and leaves CLI-001 unchanged too.

Question: should I update CLI-001 to list six subcommands?

Assumption: no edit. The repo rules say every spec change needs your confirmation. I report the gap instead.

## Other stale docs on main

`docs/architecture.md` and `AGENTS.md` still name `due_at()` in `sla.py`. Main renamed it to `deadline_for()`. `AGENTS.md` says `make test` runs 7 cases and that the CLI has no tests.

Question: should I fix these docs as part of this branch?

Assumption: no. The branch did not cause them. I report them for a separate change.

## The untracked `debug_notes.md`

The working tree had one untracked file, `debug_notes.md`. Its one line says it holds notes from debugging the due-time math and asks to delete it before merge.

Question: is this file related to the rebase, and should it be deleted?

Assumption: it is related to the overdue work but is not part of the branch. I stashed it with a label before the rebase and restored it after. I did not delete it.

## Backup of the old branch

Question: may I keep a backup branch at the old tip?

Assumption: yes. I created `backup/feature-overdue-pre-rebase` at `638b218`. Delete it once you accept the result.

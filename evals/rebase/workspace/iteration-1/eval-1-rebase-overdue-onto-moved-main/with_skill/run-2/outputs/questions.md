# Questions I would have asked before touching code

Nobody was available, so each question records the assumption I proceeded on. Every
assumption picks the option with the least risk to your work.

## Three points

| Point | Ref | Commit |
|---|---|---|
| curr | `feature/overdue` | `33f6a20` |
| old_base | merge-base | `d06bbc3` |
| new_base | `main` | `f94de3a` |

## Step 0: the dirty tree

The working tree held one untracked file, `debug_notes.md`. Its one line reads
`notes while debugging the due-time math; delete before merge`.

Question: is this note related to the rebase, and do you want it deleted now?

Assumption: it is a scratch note, not code. I stashed it under the label
`swd-rebase-preflight-20261027-083140`, restored it after the rebase, and left it in
place. Deleting your file is your call, not mine.

## Risk gate: INV-006 blocks a plain replay

Headline: commit `023139c` reads the current time from `time.time()`. Main added INV-006
after your branch started. It says a command that depends on the current time reads it
from the store's clock, never from the system clock directly. A plain replay would land
code that breaks an invariant.

The conflict is in one place, `TicketService.overdue()` in `ticketdesk/tickets.py`. The
method also takes an optional `now` argument that no caller uses.

Options:

1. Replay with an edit. Read `now` from `self.store.clock()` and drop the `now` argument.
   The store clock is injectable, so tests stay deterministic without a second override.
2. Replay with an edit but keep `now=None` as an override. INV-005 says time never comes
   from the caller, so the override is a side door that invites the same break later.
3. Replay as is and ask you to revise INV-006. The invariant is two commits old and the
   architecture doc already describes the injectable clock. Nothing suggests it is wrong.

Assumption: option 1. It satisfies INV-006, keeps TKT-014's behavior unchanged, and
removes a parameter nobody calls.

## Plan questions

Question: your branch shipped no tests. Main now requires a subprocess test per subcommand
in `tests/test_cli.py`, and `docs/guidelines.md` already required tests for new logic.
May I add a service test and a CLI test inside the replayed commits?

Assumption: yes. The tests prove the two edits and are the only way to show INV-006 holds.
They go in the commit whose behavior they cover, so each commit stays one logical change.

Question: `docs/product-specs/cli.md` CLI-001 still says the command takes four
subcommands. Main's `export` already made that stale, and `overdue` makes it two behind.
May I update CLI-001?

Assumption: no. The repo rules say no drive-by edits to specs without your confirmation.
I left CLI-001 alone and listed it in the report for you to decide.

Question: TKT-014 says "the current time". Do you want a cross-reference to INV-006 in the
spec text?

Assumption: no. I replayed your docs commit unchanged. The reference lives in the code
comment and the commit body instead.

## The plan I proceeded on

| Commit | Class | Action |
|---|---|---|
| `023139c` feat(tickets): overdue detection | Adjusted | Replay with edits. `now` comes from `self.store.clock()`. Drop the `now` argument and the inline `import time`. Add a fake-clock test in `tests/test_tickets.py`. |
| `4acb140` feat(cli): overdue subcommand | Adjusted and Extended | Replay with edits. Resolve the text conflict with `export` in `ticketdesk/cli.py`. Print through `_line()` instead of a copy of the format string. Add a subprocess test in `tests/test_cli.py`. |
| `33f6a20` docs(specs): TKT-014 and CLI-010 | Untouched | Replay as is. Main did not touch `cli.md` or `tickets.md`, and the IDs are the next free numbers. |

Main does not solve the overdue problem already. `export` prints `due_at` but filters
nothing.

Mechanics: I cherry-pick each commit onto `main` by hand instead of running `git rebase`.
Two of three commits need edits and the host cannot run an interactive rebase. The branch
`feature/overdue` moves to the new history. The old tip stays reachable as
`backup/feature-overdue-pre-rebase`.

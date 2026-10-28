# Questions for Dmitri: rebase of feature/overdue onto main

Nobody was available during this run. Each section below is a stop the skill makes for your approval. Each one states the question, the assumption I used, and the option I picked.

## Three points

| Point | Commit |
|---|---|
| `curr` (feature/overdue) | `638b218` |
| `old_base` (merge-base) | `d29de19` |
| `new_base` (main) | `b8411e7` |

## Step 0: the untracked file debug_notes.md

The tree had one untracked file, `debug_notes.md`. It holds one line of debug notes on the due-time math. The line asks to delete the file before merge.

- **Question.** Is this file related to the rebase, and do you want to keep it?
- **Assumption.** It is your scratch note and not part of the branch.
- **Action.** I stashed it as `swd-rebase-preflight-20261028-080351` and restore it after the rebase. I do not commit it and I do not delete it.

## Risk gate: commit 1 breaks INV-006 on main

Main added INV-006 in `b8411e7`. A command that depends on the current time must read it from the store clock, not from the system clock. Commit `4348871` reads `time.time()` in `TicketService.overdue()`. A plain replay of that commit breaks INV-006.

Options:

1. **Replay with an edit (picked).** `overdue()` reads `self.store.clock()` when the caller passes no `now`. The signature and the behavior stay the same. Tests can inject a fake clock.
2. Replay as is and open a follow-up. This lands a known invariant break on the branch.
3. Change INV-006 to allow the system clock. This rewrites a spec that main added on purpose.

- **Question.** Do you approve option 1?
- **Assumption.** INV-006 is intentional and the branch must comply.

## Risk gate: commit 2 conflicts with the new export command

Commit `ec61e0d` adds `overdue` at the same lines in `ticketdesk/cli.py` where main added `export` and the `_line` helper. Git reports this as a text conflict. The intents do not contradict each other.

- **Question.** Do you approve keeping both commands and printing `overdue` lines with `_line(t)`?
- **Assumption.** CLI-010 says "in the `list` line format". Main extracted `_line` so commands share that format. A copied f-string would drift from `list` later.

## Plan step: tests the branch does not have

The branch adds no tests. Main now requires a test in `tests/test_cli.py` for each new subcommand. The guidelines on both bases require tests for new logic.

- **Question.** Do you want the tests inside the feature commits, or in a separate commit?
- **Assumption.** Inside the feature commits. The guideline says "A new subcommand ships with its test in that file." The service test proves the INV-006 edit in the same commit.
- **Action.** Commit 1 gets `test_overdue_*` cases in `tests/test_tickets.py`. Commit 2 gets `test_overdue_*` cases in `tests/test_cli.py`.

## Plan step: spec text I did not change

These docs are stale on main or after this branch. The repo rules say "Doc changes need user confirmation". So I report them and do not edit them.

- `docs/product-specs/cli.md` CLI-001 lists four subcommands. Main has five with `export`, and six with `overdue`.
- Main has no CLI spec for `export`.
- `docs/architecture.md` still names `due_at()` in `sla.py`. Main renamed it to `deadline_for()`.
- `AGENTS.md` says "7 unittest cases" and "Not covered by tests: the CLI". Both are false on main.

- **Question.** Do you want a follow-up commit that fixes these docs?
- **Assumption.** No. That is a separate change for you to approve.

## The plan I would have presented

| Commit | Action | Change |
|---|---|---|
| `4348871` feat(tickets) | Replay with edits | `overdue()` uses `self.store.clock()`. Remove `import time`. Add service tests with a fake clock. |
| `ec61e0d` feat(cli) | Replay with edits | Resolve the conflict to keep `export` and `overdue`. Print with `_line(t)`. Add subprocess tests in `tests/test_cli.py`. |
| `638b218` docs(specs) | Replay as is | TKT-014 and CLI-010 are free IDs on main. |

I keep a backup branch `backup/feature-overdue-pre-rebase` at `638b218`. I do not push.

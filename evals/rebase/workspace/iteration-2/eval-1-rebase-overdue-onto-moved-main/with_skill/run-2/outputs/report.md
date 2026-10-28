# Rebase of feature/overdue onto main

**Succeeded with adjustments.** `feature/overdue` now sits on `main` as three commits.
Two commits needed edits to follow rules that `main` added. Lint and all 11 unit tests
pass. Nothing was pushed.

| Point | Hash |
|---|---|
| `curr` before the rebase | `638b218` |
| `old_base`, the merge-base | `d29de19` |
| `new_base`, `main` | `b8411e7` |
| `feature/overdue` after the rebase | `65e2d4b` |

The old branch tip stays on the local branch `backup/overdue-pre-rebase`. Delete it once
you accept the result.

## Per-commit outcome

| Old | New | Class | Outcome |
|---|---|---|---|
| `4348871` feat(tickets): overdue detection | `da1926b` | Conflicting | Replayed with edits |
| `ec61e0d` feat(cli): overdue subcommand | `dccc7e3` | Adjusted and Extended | Replayed with edits after a conflict |
| `638b218` docs(specs): TKT-014, CLI-010 | `65e2d4b` | Untouched | Replayed as is |

### `4348871`: the service now reads the store clock

The old `overdue()` read the system clock through `time.time()`. INV-006 on `main` forbids
this. A command must read the current time from the store's clock.

- `overdue()` now calls `self.store.clock()`.
- The optional `now` parameter is gone. The injectable store clock already serves tests.
- A new unit test, `test_overdue_uses_store_clock`, moves the fake clock past the P1 due
  time. It fails if the code goes back to the system clock.

### `ec61e0d`: the CLI uses `_line` and ships a CLI test

Git stopped on a conflict in `ticketdesk/cli.py`. Both sides added a subcommand at the
same lines. `main` added `export`, and the branch added `overdue`. I kept both.

- The `overdue` branch calls `_line(t)`, which `main` extracted from `list`. CLI-010
  requires the `list` line format, so a shared formatter keeps the two in step.
- `main` added a guideline that a new subcommand ships with its test in
  `tests/test_cli.py`. The commit adds `test_overdue_lists_oldest_due_first`. The test
  writes a log with timestamps from 1970, so its result does not depend on today's date.

### `638b218`: no change

The spec IDs TKT-014 and CLI-010 are still free on `main`. The commit applied without
edits.

## Spec and invariant deviations

None remain after the edits. `main` does not already solve the problem. No `overdue` code
existed there.

- **TKT-014.** Open and assigned tickets past their due time are overdue. Closed tickets
  are not. The unit test and the CLI test cover both cases.
- **CLI-010.** The command prints `list` lines, oldest due time first. With nothing
  overdue it prints nothing and exits 0.
- **INV-006.** No module except `store.py` reads the system clock.

## Verification

I ran `make lint` and `make test` after each commit and again at the end.

| Point | Tests | Result |
|---|---|---|
| `main` before the rebase | 9 | pass |
| After `da1926b` | 10 | pass |
| After `dccc7e3` | 11 | pass |
| After `65e2d4b` | 11 | pass |

An end-to-end run through `python3 -m ticketdesk.cli` gave the same `overdue` output as
the old branch. The run covered these commands:

- `overdue` with old open, assigned, and closed tickets and one new ticket
- `overdue` after a close, and `overdue` on an empty log
- `list`, `export`, `create`, `assign`, and `close`, the surfaces `main` changed and the
  branch did not
- an unknown subcommand, which exits 2 and now lists `overdue` among the choices

Nothing was broken on the surfaces that `main` changed. `list` and `export` print as on
`main`. The rename to `deadline_for` does not reach the branch, because `overdue()` reads
the `Ticket.due_at` field.

## Your working tree

Your untracked `debug_notes.md` is back in place. I stashed it before the rebase under the
label `swd-rebase-preflight-20261028-080352`. The stash popped cleanly.

## What to check by hand

- **The `now` parameter.** I removed `now=None` from `overdue()`. Tell me if a caller
  outside this repo passes it.
- **Doc drift on `main`.** These docs were stale before the rebase. I did not edit them,
  because the repo asks for your approval on doc changes.
  - CLI-001 lists four subcommands. Six exist after the rebase.
  - No spec describes `export`.
  - `AGENTS.md` says the suite has 7 cases and that the CLI has no tests.
  - `docs/architecture.md` still names `due_at()` in `sla.py`.
- **Known gap.** An unknown priority still exits with a traceback. The CLI-007 TODO on
  `main` tracks this.

The questions I would have asked are in `questions.md` next to this report.

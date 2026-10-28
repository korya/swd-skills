# Rebase report: feature/overdue onto main

**Succeeded with adjustments.** `feature/overdue` now sits on `main` with three commits.
Lint and the 13 unit tests pass. One commit broke INV-006, which main added, so I changed
it to read the time from the store clock. Nothing was pushed.

Four questions for you are in `questions.md`. The most important one is the INV-006 fix,
option A.

## Three points

| Point | Ref | Hash |
|---|---|---|
| `curr` | `feature/overdue` before the rebase | `6eefb33` |
| `old_base` | merge-base of the branch and `main` | `4a11cda` |
| `new_base` | `main` | `280060f` |
| result | `feature/overdue` after the rebase | `267c8a5` |

The original branch is kept as `backup/feature-overdue-pre-rebase` at `6eefb33`.

## Per-commit outcome

| Old | New | Class | Outcome |
|---|---|---|---|
| `822ed1d` feat(tickets) | `d765e19` | Conflicting | Replayed with edits |
| `a235e66` feat(cli) | `0575b72` | Adjusted and Extended | Replayed with edits |
| `6eefb33` docs(specs) | `267c8a5` | Untouched | Replayed as is |

### 822ed1d: overdue detection in the service

This commit broke INV-006 on main. `TicketService.overdue()` read `time.time()` when the
caller passed no `now`. INV-006 says that a command reads the current time from the store
clock. Git replayed the commit without a text conflict.

Changes in `ticketdesk/tickets.py` and `tests/test_tickets.py`:

- `overdue()` reads `self.store.clock()` and no longer imports `time`.
- Two new unit tests use the fake clock. They cover the clock source, the closed-ticket
  rule, and the order.
- The clock test fails against the old code. I checked this with a patched copy of the
  method.

The rename of `due_at()` to `deadline_for()` did not affect this commit. It reads only
the `Ticket.due_at` field, and main kept that field.

### a235e66: the overdue subcommand

This commit had a text conflict in `ticketdesk/cli.py`. Main added the `export`
subcommand at the same two places. I kept both subcommands.

Changes in `ticketdesk/cli.py` and `tests/test_cli.py`:

- `overdue` prints with the shared `_line()` formatter from main, not a copy of the
  format string.
- Two new subprocess tests follow the CLI test rule in main's `docs/guidelines.md`. They
  cover the order, the closed-ticket rule, and the empty case.

### 6eefb33: the TKT-014 and CLI-010 specs

Main did not change `tickets.md` or `cli.md`. TKT-014 and CLI-010 are still free IDs on
main. The commit replayed with no change.

## Spec and invariant check

Main did not already solve the overdue problem. The branch still meets its specs, now
with tests:

- **TKT-014.** An open or assigned ticket past its due time is overdue. A closed ticket
  is never overdue.
- **CLI-010.** The command uses the `list` line format and sorts the oldest due time
  first. It prints nothing and exits 0 when no ticket is overdue.
- **INV-006.** The service reads the time from the store clock. No module in
  `ticketdesk/` other than `store.py` imports `time`.

## Verification

| Check | Result |
|---|---|
| `make lint` after each commit | Pass |
| `make test` after each commit | 11, 13, and 13 tests pass |
| `make test` on `main` before the rebase | 9 tests pass |
| End-to-end run against a temporary log | Pass |

The end-to-end run used `create`, `assign`, `overdue`, `list`, `export`, and `close`. A
ticket with an old creation time showed in `overdue`. It disappeared after `close`. The
`--help` output lists all six subcommands. A call with no subcommand exits 2.

I also checked the surfaces that main changed and the branch did not. I found nothing
broken there:

- Main's CLI tests for `list` and `export` still pass. Both commands worked in the
  end-to-end run.
- The package exports `deadline_for`, and no code still calls `due_at()`.

## Stash

The tree held one untracked file, `debug_notes.md`. I stashed it under the label
`swd-rebase-preflight-20261028-080432` and restored it after the rebase. The pop was
clean. The file is untracked again and no commit contains it. Its own text says to delete
it before merge.

The stash also caught `__pycache__` folders from my first test run. I deleted them after
the pop.

## Follow-ups for you

- **Confirm option A for INV-006.** Also decide whether `overdue()` keeps its `now`
  parameter. The parameter lets a caller skip the store clock.
- **Update CLI-001.** It still says that `ticketdesk` takes four subcommands. Main has
  five, and this branch adds the sixth. I made no spec edit without your confirmation.
- **Fix the stale docs on main.** `docs/architecture.md` still names `due_at()` in
  `sla.py`. `AGENTS.md` still says "7 unittest cases" and "Not covered by tests: the CLI".
- **Delete `debug_notes.md`** before you merge.
- **Delete the backup branch** `backup/feature-overdue-pre-rebase` when you approve the
  result.

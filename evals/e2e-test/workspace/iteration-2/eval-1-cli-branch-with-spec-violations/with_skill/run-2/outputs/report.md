# E2e report: feature/cli-tidy

**27/36 PASS, 8 FAILURE, 1 BLOCKED. Not ready to merge.** The branch breaks three product specs: TKT-008, TKT-010, and CLI-006. It also reopens closed tickets, which breaks the forward-only rule of tickets.md. The other four failures exist on main too and do not block this branch.

The PR describes the TKT-008, TKT-010, and CLI-006 breaks as intended, but it changes no spec. AGENTS.md says a change that contradicts a spec must stop for discussion. The owner must decide: revert the behavior, or change the specs on purpose. Even judged by its own promise, the note-length change is wrong, because the error text still says 10 characters.

## Scope, surface, environment

- **Scope.** The diff of feature/cli-tidy against main, the promises in PR.md, all of `cli.md` and `tickets.md`, and `event-log.md` as blast radius.
- **Persona and surface.** A shell user of the help desk. Every case ran `python3 -m ticketdesk.cli` from the repo root, as the task directed. Case 25 ran from a scratch directory with `PYTHONPATH` set, so the default `./tickets.jsonl` did not land in the repo.
- **Environment.** Local machine, Python 3.15.2, throwaway log files. All mutations went to those files.
- **Depth.** Comprehensive. The request said "comprehensively, before it merges".
- **Baseline.** A `git archive main` export ran the changed scenarios, to separate regressions from old defects.

## Cases

| # | Case | Spec/ref | Status |
|---|------|----------|--------|
| 1 | `--help` shows the new description line, spelled correctly | PR, CLI-001 | FAILURE |
| 2 | Smoke: `--help` prints usage, exit 0 | readiness | PASS |
| 3 | No subcommand, unknown subcommand: usage on stderr, exit 2 | CLI-001 | PASS |
| 4 | `create` with default priority prints `#1 open <title>`, logs P3, exit 0, empty stderr | CLI-003, CLI-008, TKT-001 | PASS |
| 5 | `create --priority P1` logs P1 | CLI-003, TKT-003 | PASS |
| 6 | Empty and whitespace-only title rejected with `title is required` | TKT-002, CLI-007 | PASS |
| 7 | Unknown priority `P9` rejected with a clean error | TKT-003, CLI-007 TODO | FAILURE |
| 8 | IDs start at 1 and rise by one | TKT-004, INV-003 | PASS |
| 9 | `list` line is `#<id> [<priority>] <state> <title>` | CLI-006 | FAILURE |
| 10 | `list` pads the state to 8 characters | CLI-006 | PASS |
| 11 | `list` on a missing log prints nothing and creates no file | CLI-006, LOG-006 | PASS |
| 12 | `list` shows every ticket in ID order, closed included | TKT-013 | PASS |
| 13 | `assign` an open ticket prints `#<id> assigned -> <name>` | CLI-004, TKT-006 | PASS |
| 14 | Reassigning an assigned ticket replaces the assignee | TKT-006 | PASS |
| 15 | Empty and whitespace-only assignee rejected with `assignee is required` | TKT-007, CLI-007 | PASS |
| 16 | `assign` a closed ticket fails with `ticket <id> is closed` | TKT-008, forward-only rule | FAILURE |
| 17 | `close` with a 10-character note succeeds | TKT-010, CLI-005 | PASS |
| 18 | `close` with the 9-character note `duplicate` is rejected | TKT-010 | FAILURE |
| 19 | `close` with an 8-character note is rejected | TKT-010 | PASS |
| 20 | `close` with a short note padded by spaces is rejected | TKT-010 | PASS |
| 21 | Closing an assigned ticket keeps the assignee | TKT-009 | BLOCKED |
| 22 | Closing a closed ticket fails with `ticket <id> is already closed` | TKT-011 | PASS |
| 23 | Unknown ticket ID fails with `no ticket <id>` for `assign` and `close` | TKT-012 | PASS |
| 24 | Non-integer ID gets a usage error, exit 2, no event | CLI-009 | PASS |
| 25 | Log path precedence: `--log`, then `TICKETDESK_LOG`, then `./tickets.jsonl` | CLI-002 | PASS |
| 26 | Each change appends one event, `list` appends none | LOG-001 | PASS |
| 27 | Event kinds, fields, sorted keys, `at` in epoch seconds | LOG-002 to LOG-005, INV-005 | PASS |
| 28 | Blank and whitespace lines in the log are ignored | LOG-005 | PASS |
| 29 | A corrupt line stops every command with a clean error | LOG-007, INV-004, CLI-007 TODO | FAILURE |
| 30 | Appending leaves the existing bytes of the log unchanged | LOG-008, INV-002 | PASS |
| 31 | Two replays of the same log print the same list | LOG-009 | PASS |
| 32 | `list` in a pipe, including `head` closing the pipe early | shell contract | FAILURE |
| 33 | Subcommand `--help` matches the spec | shell contract | PASS |
| 34 | Main baseline follows CLI-006, TKT-008, TKT-010 | regression check | PASS |
| 35 | Ctrl-C during a command leaves the log intact (added during the run) | shell contract, INV-002 | PASS |
| 36 | A title with a newline keeps `list` at one line per ticket (added during the run) | CLI-006 | FAILURE |

## Non-PASS details

Commands below use `T="python3 -m ticketdesk.cli --log $LOG"` with `LOG` set to a fresh file path.

### Case 1: typo in the new `--help` description (regression)

- **Steps.** Run `python3 -m ticketdesk.cli --help`.
- **Expected.** A description line with correct spelling.
- **Observed.** The line reads `Manage support tikets from the shell.`
- **Most likely cause.** A typo in the `description=` string that the branch added to the `ArgumentParser` call in `ticketdesk/cli.py`.

### Case 7: unknown priority prints a Python traceback (pre-existing)

- **Steps.** Run `$T create "Bad prio" --priority P9`. Repeat with `--priority p1`.
- **Expected.** `error: <message>` on stderr, naming `P9` and `P1`, `P2`, `P3`, exit 2 (TKT-003, CLI-007).
- **Observed.** A traceback of about 15 lines on stderr, exit 1. The last line is the only useful one:

```text
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
```

- **Notes.** No ticket is created, so the TKT-003 content holds. Lowercase `p1` gets the same traceback. Main behaves the same. The `cli.md` TODO under CLI-007 records this conflict as open.
- **Most likely cause.** `sla.py` raises `ValueError`, and `cli.py` catches only `TicketError`.

### Case 9: `list` dropped the priority column (regression)

- **Steps.** Run `$T create "Printer on fire"`, then `$T create "VPN drops hourly" --priority P1`, then `$T list`.
- **Expected (CLI-006).** `#1 [P3] open     Printer on fire`
- **Observed.** `#1 open     Printer on fire`. Main prints `#1 [P3] closed   Printer on fire` for a ticket of the same kind.
- **Impact.** No command now shows a ticket's priority after `create`. A user cannot tell a P1 ticket, due in 4 hours, from a P3 ticket.
- **Most likely cause.** The branch removed `[{t.priority}]` from the `list` format string in `cli.py`. The PR calls this intended, but CLI-006 is unchanged.

### Case 16: `assign` reopens a closed ticket (regression)

- **Steps.**
  1. Run `$T create "Printer on fire"`.
  2. Run `$T close 1 "Replaced the toner cartridge"`.
  3. Run `$T assign 1 lee`.
  4. Run `$T list`.
  5. Run `$T close 1 "Second resolution overwrites the first"`.
- **Expected.** Step 3 fails with `error: ticket 1 is closed` and exit 2. The ticket stays closed.
- **Observed.** Step 3 prints `#1 assigned -> lee` and exits 0. Step 4 shows `#1 assigned Printer on fire`, so the ticket is open again. Step 5 succeeds and appends a second `closed` event. The first resolution is superseded. Main rejects step 3 with `error: ticket 1 is closed`.
- **Specs broken.**
  - TKT-008: a closed ticket cannot be assigned.
  - The forward-only rule in `tickets.md`: nothing reopens a closed ticket.
  - The intent of TKT-011: closing twice must leave the recorded resolution unchanged. The reopen path gets around that check.
- **Most likely cause.** The branch deleted the `closed` check in `TicketService.assign`. Replay then treats the `assigned` event as a state change back to `assigned`.

### Case 18: a 9-character note closes a ticket, and the error text disagrees (regression)

- **Steps.** Run `$T create a`, then `$T close 1 "duplicate"`. Repeat with the notes `"Toner out"` and `"   duplicate   "`.
- **Expected (TKT-010).** `error: resolution note must be at least 10 characters`, exit 2, ticket still open.
- **Observed.** Each prints `#<id> closed` and exits 0. An 8-character note still gets the 10-character error. Main rejects `duplicate` with that error.
- **Notes.** The PR wants `duplicate` accepted. The code now enforces a minimum of 9 characters, but the message still says 10. Users get a message that does not match the rule. If the intent is "short notes are fine", 9 is an arbitrary floor that still rejects `dup` or `wontfix`.
- **Most likely cause.** The branch changed `< 10` to `< 9` in `TicketService.close` and left the message text alone.

### Case 21: no surface shows the assignee after close (BLOCKED)

- **Steps.** Run `$T create a`, `$T assign 1 dana`, `$T close 1 "Replaced the toner cartridge"`, then `$T list`.
- **Observed.** The ticket shows as `closed`. No command prints an assignee except the `assign` confirmation. The log shows that no event clears the assignee, but the replayed state is not visible.
- **Unblocks it.** A `show <id>` command, or an assignee column in `list`.

### Case 29: a corrupt log line prints a Python traceback (pre-existing)

- **Steps.** Create two tickets. Insert the line `{"at": 1, "id": 3, "kind": "crea` as line 3 of the log with a text editor. Run `$T list` and `$T create "after corruption"`.
- **Expected.** `error: <path>:3: corrupt event ...` on stderr, exit 2, no stdout.
- **Observed.** Both commands print a chained traceback of about 30 lines and exit 1. The last line is correct and names the path, line 3, and `corrupt event`. `create` appends nothing, so INV-004 holds.
- **Notes.** The LOG-007 message content is met. The presentation is the open CLI-007 TODO, and main behaves the same.
- **Most likely cause.** `store.py` raises `ValueError`, and `cli.py` catches only `TicketError`.

### Case 32: `list | head` prints a BrokenPipeError traceback (pre-existing)

- **Steps.** Use a log of 20,000 `created` events. I wrote it with a script, because 20,000 `create` calls would take minutes. Run `$T list | head -1`.
- **Expected.** One line of output and a quiet exit.
- **Observed.** `head` prints the first line. Then `ticketdesk` prints a `BrokenPipeError` traceback on stderr and exits 120. A pipe into `wc -l` on a small log works. Main behaves the same.
- **Most likely cause.** The CLI does not handle `SIGPIPE` or `BrokenPipeError` on stdout.

### Case 36: a title with a newline breaks the one-line-per-ticket list (pre-existing)

- **Steps.** Run `$T create $'Two\nlines'`, then `$T list`.
- **Expected.** One line per ticket (CLI-006), or a rejected title.
- **Observed.** `create` accepts the title. `list` prints `#2 open     Two` and then `lines` on its own line. A script that reads one ticket per line misreads this. The log stores the title as `"Two\nlines"` on one line, so the log is fine. Main behaves the same.
- **Most likely cause.** Neither TKT-002 nor `cli.py` handles control characters in titles.

## Missing or untested cases

- **TKT-005, due time by priority.** No command shows a due time, and the log does not store one. Only the code or the unit tests can check it.
- **The installed `ticketdesk` entry point.** The task fixed the surface as `python3 -m ticketdesk.cli`. A `pip install` of the package was out of scope.
- **Concurrent writers.** `architecture.md` states a single writer, so two parallel writers are outside the product's promise.

## Issues found

Ordered by severity. Issues 1 to 4 are regressions from this branch. Issues 5 to 7 exist on main.

1. **High. `assign` reopens closed tickets** (case 16). It breaks TKT-008 and the forward-only rule. It also lets a second `close` supersede the recorded resolution. Support history becomes misleading, and the log keeps the bad events forever (INV-002).
2. **High. `list` hides the priority** (case 9). It breaks CLI-006. After this branch no command shows priority, so users cannot triage by urgency.
3. **Medium. The note-length rule is 9, but the message says 10** (case 18). It breaks TKT-010, and the error text no longer matches the rule.
4. **Low. Typo `tikets` in `--help`** (case 1).
5. **Medium. Unknown priority and corrupt log escape as tracebacks with exit 1** (cases 7, 29). The open TODO under CLI-007 tracks this.
6. **Low. `BrokenPipeError` traceback when a pager or `head` closes the pipe** (case 32).
7. **Low. A newline in a title splits the `list` line** (case 36).

## UX gaps

- **The PR changes intended behavior without changing the specs.** Issues 1 to 3 need a decision, not only a fix. Either revert the code, or update TKT-008, TKT-010, and CLI-006 with the owner's confirmation.
- **The README gives no run instructions.** The task said to run the CLI "as the README says", but only AGENTS.md shows the commands. A new user who reads the README first does not learn how to start it.
- **`--help` gives little help.** Subcommands have no descriptions. `--priority` lists neither the allowed values nor the default `P3`.
- **The missing-subcommand error names an internal field.** It reads `the following arguments are required: cmd`. A user does not know what `cmd` is.
- **Priority is case-sensitive with no hint.** `p1` gets a traceback instead of acceptance or a short error.
- **Ctrl-C prints a `KeyboardInterrupt` traceback.** The log stays intact, but the output looks like a crash.

## Improvements worth doing

- **Add CLI tests.** AGENTS.md says the CLI has no tests. So the PR's "All tests pass locally" says nothing about issues 2 and 4. This run did not execute the unit tests.
- **Add a `show <id>` command.** It would show the assignee, resolution, priority, and due time. Case 21 and TKT-005 could then be tested from the shell.

## Leftover artifacts

All files are under `run-2/outputs/`. No tracked file in the repo changed.

- `logs/a.jsonl`: the lifecycle log for cases 4 to 23, including the reopened ticket #1.
- `logs/b.jsonl`, `logs/b.before`, `logs/l1`, `logs/l2`: the event-log format, append, and replay cases.
- `logs/c.jsonl`: the log with blank lines, case 28.
- `logs/d.jsonl`: the log with a corrupt line, case 29.
- `logs/e.jsonl`: odd titles and IDs, case 36.
- `logs/m.jsonl`: the main baseline, case 34.
- `logs/big.jsonl` and `logs/huge.jsonl`: logs of 20,000 and 400,000 events, written by script for cases 32 and 35.
- `logs/cwd/tickets.jsonl`, `env.jsonl`, `opt.jsonl`: the log-path precedence case 25.
- `main-snapshot/`: the `git archive main` export.
- `case-list.md`: the case list written before execution.
- `repo/ticketdesk/__pycache__/`: Python wrote bytecode there when the CLI ran. It is untracked.

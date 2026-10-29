# E2e report: feature/cli-tidy

**29/40 PASS, 10 FAILURE, 1 BLOCKED. No-go: the branch breaks three ticket and CLI specs, and `assign` now reopens closed tickets.**

Eight of the ten failures come from the branch. The other two are older defects that also show on `main`. The branch changes behavior that `tickets.md` and `cli.md` forbid, and it does not change those specs. AGENTS.md requires such a conflict to go to the user before it merges.

- **Surface and user.** A support agent in a shell, running `python3 -m ticketdesk.cli` from the repo root.
- **Environment.** Local. Every log file is a throwaway file under `outputs/logs/`.
- **Scope.** The four PR items, every item of `cli.md` and `tickets.md`, and the event log and invariants as blast radius.
- **Depth.** Comprehensive, because the task says "comprehensively" and the run gates a merge.
- **Evidence log.** `outputs/evidence.log` holds every command, its stdout, its stderr, and its exit code. The case list is in `outputs/cases.md`.

All commands below run from `outputs/repo` with `PYTHONDONTWRITEBYTECODE=1`. The product tree stayed unmodified, and `git status` is clean.

## Case table

| # | Case | Spec/ref | Status |
|---|---|---|---|
| 1 | `--help` shows the new description, spelled right, with four subcommands | PR item 4, CLI-001 | FAILURE |
| 2 | Subcommand `--help` for create, assign, close, list | CLI-003 to CLI-006 | PASS |
| 3 | No subcommand | CLI-001 | PASS |
| 4 | Unknown subcommand | CLI-001 | PASS |
| 5 | Missing positional arguments | CLI-001 | PASS |
| 6 | Create with `--priority P1` | CLI-003, TKT-001, CLI-008 | PASS |
| 7 | Create with no priority defaults to P3, visible in `list` and the log | CLI-003 | FAILURE |
| 8 | Create with empty and whitespace-only title | TKT-002, CLI-007 | PASS |
| 9 | Create with priority P9 | TKT-003 | PASS |
| 10 | IDs rise by one, not reused after close | TKT-004, INV-003 | PASS |
| 11 | Title with unicode, quotes, HTML, 300 characters | CLI-003 | PASS |
| 12 | `list` line format with priority | CLI-006, PR item 1 | FAILURE |
| 13 | `list` includes closed tickets, sorted by ID | TKT-013 | PASS |
| 14 | `list` with a missing log file | CLI-006, LOG-006 | PASS |
| 15 | `list` in a pipe, including an early-closing reader | Shell contract | FAILURE |
| 16 | Assign an open ticket | TKT-006, CLI-004 | PASS |
| 17 | Reassign an assigned ticket | TKT-006 | PASS |
| 18 | Assign with empty and whitespace-only assignee | TKT-007, CLI-007 | PASS |
| 19 | Assign a closed ticket | TKT-008, CLI-007, PR item 3 | FAILURE |
| 20 | A closed ticket never reopens | tickets.md forward-only rule, TKT-011 | FAILURE |
| 21 | Assign an unknown ID | TKT-012 | PASS |
| 22 | Non-integer ID for assign and close | CLI-009 | PASS |
| 23 | Close an assigned ticket with a 10-character note | TKT-009, CLI-005 | PASS |
| 24 | Close with the 9-character note `duplicate` | TKT-010, PR item 2 | FAILURE |
| 25 | Close with `   duplicate   `, 9 characters after trim | TKT-010 | FAILURE |
| 26 | Short-note error text matches the enforced limit | TKT-010, CLI-007 | FAILURE |
| 27 | Close with a whitespace-only note | TKT-010 | PASS |
| 28 | Close a closed ticket | TKT-011 | PASS |
| 29 | Close an unknown ID | TKT-012 | PASS |
| 30 | Due time by priority | TKT-005 | BLOCKED |
| 31 | Log path order: `--log`, then `TICKETDESK_LOG`, then `./tickets.jsonl` | CLI-002 | PASS |
| 32 | `--log` at a directory or under a missing directory | CLI-002 error path | FAILURE |
| 33 | One event per change, none for `list` or a rejected command | LOG-001 | PASS |
| 34 | Event kinds and fields | LOG-002, LOG-003 | PASS |
| 35 | Timestamp is epoch seconds at append | LOG-004, INV-005 | PASS |
| 36 | Sorted keys, newline-terminated lines, blank lines ignored | LOG-005 | PASS |
| 37 | Missing log file: first create makes ticket 1 and the file | LOG-006 | PASS |
| 38 | Corrupt line stops every command | LOG-007, INV-004 | PASS |
| 39 | Appending never rewrites earlier lines | LOG-008, INV-002 | PASS |
| 40 | Replay is deterministic | LOG-009 | PASS |

Some PASS rows carry a note:

- **Cases 9 and 38.** The rule holds. The error names the value or the file, line, and `corrupt event`, and nothing is written. The message still arrives as a Python traceback with exit code 1. The CLI-007 TODO records this as an open conflict, and `main` behaves the same. Issue 7 tracks it.
- **Case 23.** The output and the state pass. No command shows the assignee after a close, so "the assignee is kept" stays untested. See the missing cases.

## Non-PASS details

### Case 19: `assign` accepts a closed ticket

**Steps.**

```console
$ python3 -m ticketdesk.cli --log ../logs/c19.jsonl create "Printer on fire" --priority P1
#1 open Printer on fire
$ python3 -m ticketdesk.cli --log ../logs/c19.jsonl assign 1 dana
#1 assigned -> dana
$ python3 -m ticketdesk.cli --log ../logs/c19.jsonl close 1 "Replaced the toner cartridge"
#1 closed
$ python3 -m ticketdesk.cli --log ../logs/c19.jsonl assign 1 lee
#1 assigned -> lee
(stderr empty, exit 0)
$ wc -l < ../logs/c19.jsonl; tail -1 ../logs/c19.jsonl
4
{"assignee": "lee", "at": 1793302366.432658, "id": 1, "kind": "assigned"}
```

**Expected.** Per TKT-008, the stderr shows `error: ticket 1 is closed`, the exit code is 2, and the log stays at 3 lines.

**Observed.** The command succeeds with exit code 0 and appends an `assigned` event.

**Most likely cause.** The branch deletes the closed-state guard from `TicketService.assign` in `ticketdesk/tickets.py`. `main` still rejects this with `error: ticket 1 is closed`, see the `main` entries in the evidence log.

### Case 20: the closed ticket reopens and takes a second resolution

This case continues on the log from case 19.

```console
$ python3 -m ticketdesk.cli --log ../logs/c19.jsonl list
#1 assigned Printer on fire
$ python3 -m ticketdesk.cli --log ../logs/c19.jsonl close 1 "Closed it a second time"
#1 closed
$ python3 -m ticketdesk.cli --log ../logs/c19.jsonl list; cat ../logs/c19.jsonl
#1 closed   Printer on fire
{"at": 1793302366.228362, "id": 1, "kind": "created", "priority": "P1", "title": "Printer on fire"}
{"assignee": "dana", "at": 1793302366.27575, "id": 1, "kind": "assigned"}
{"at": 1793302366.3265102, "id": 1, "kind": "closed", "resolution": "Replaced the toner cartridge"}
{"assignee": "lee", "at": 1793302366.432658, "id": 1, "kind": "assigned"}
{"at": 1793302366.556643, "id": 1, "kind": "closed", "resolution": "Closed it a second time"}
```

**Expected.** The ticket stays `closed`. Per `tickets.md`, "Nothing reopens a closed ticket." TKT-011 keeps the recorded resolution unchanged.

**Observed.** The `list` command shows the ticket as `assigned` after the reassignment. A second `close` then succeeds, and the log now holds two resolutions for one ticket. No command shows which resolution counts, so TKT-011 no longer protects the first one.

**Most likely cause.** The same removed guard as case 19. The PR says support asked for this, but `tickets.md` was not changed to allow it.

### Case 12: `list` drops the priority

```console
$ python3 -m ticketdesk.cli --log ../logs/c12.jsonl create "Printer on fire" --priority P1
#1 open Printer on fire
$ python3 -m ticketdesk.cli --log ../logs/c12.jsonl create "VPN drops hourly" --priority P2
#2 open VPN drops hourly
$ python3 -m ticketdesk.cli --log ../logs/c12.jsonl create "New monitor request"
#3 open New monitor request
$ python3 -m ticketdesk.cli --log ../logs/c12.jsonl assign 2 dana
#2 assigned -> dana
$ python3 -m ticketdesk.cli --log ../logs/c12.jsonl close 3 "Ordered a 27 inch monitor"
#3 closed
$ python3 -m ticketdesk.cli --log ../logs/c12.jsonl list
#1 open     Printer on fire
#2 assigned VPN drops hourly
#3 closed   New monitor request
```

**Expected.** Per CLI-006, each line reads `#<id> [<priority>] <state> <title>`:

```text
#1 [P1] open     Printer on fire
#2 [P2] assigned VPN drops hourly
#3 [P3] closed   New monitor request
```

**Observed.** The `[P1]`, `[P2]`, and `[P3]` fields are missing. No other command shows a ticket's priority, so a user cannot tell a P1 ticket from a P3 ticket without reading the raw log. The state padding to 8 characters still holds.

**Most likely cause.** The branch removes `[{t.priority}]` from the list format string in `ticketdesk/cli.py`. The PR defers the priority to a flag in a later PR. That flag does not exist yet, and CLI-006 was not changed.

### Case 7: the default priority is not visible in `list`

```console
$ python3 -m ticketdesk.cli --log ../logs/c7.jsonl create "Wifi slow"
#1 open Wifi slow
$ python3 -m ticketdesk.cli --log ../logs/c7.jsonl list
#1 open     Wifi slow
$ cat ../logs/c7.jsonl
{"at": 1793302301.176568, "id": 1, "kind": "created", "priority": "P3", "title": "Wifi slow"}
```

**Expected.** The `list` command shows `[P3]`, and the log records `"priority": "P3"`.

**Observed.** The log records P3, so the CLI-003 default is correct. The `list` command does not show it. This is the same defect as case 12.

### Case 24: `close` accepts the 9-character note `duplicate`

```console
$ python3 -m ticketdesk.cli --log ../logs/r24.jsonl create 'Printer on fire'
#1 open Printer on fire
$ python3 -m ticketdesk.cli --log ../logs/r24.jsonl close 1 duplicate
#1 closed
$ python3 -m ticketdesk.cli --log ../logs/r24.jsonl list
#1 closed   Printer on fire
```

**Expected.** Per TKT-010, the stderr shows `error: resolution note must be at least 10 characters`, the exit code is 2, and the ticket stays `open`.

**Observed.** The ticket closes with exit code 0. On `main`, the same note is rejected with the TKT-010 error.

**Most likely cause.** The branch changes the check in `TicketService.close` in `ticketdesk/tickets.py` from `< 10` to `< 9`. The PR intends this, but TKT-010 still says 10.

### Case 25: a padded 9-character note closes the ticket

```console
$ python3 -m ticketdesk.cli --log ../logs/c25.jsonl create 'Printer on fire'
#1 open Printer on fire
$ python3 -m ticketdesk.cli --log ../logs/c25.jsonl close 1 '   duplicate   '
#1 closed
$ python3 -m ticketdesk.cli --log ../logs/c25.jsonl list; cat ../logs/c25.jsonl
#1 closed   Printer on fire
{"at": 1793302390.467201, "id": 1, "kind": "created", "priority": "P3", "title": "Printer on fire"}
{"at": 1793302390.5166001, "id": 1, "kind": "closed", "resolution": "   duplicate   "}
```

**Expected.** The note has 9 characters after the trim, so TKT-010 rejects it, as in case 24.

**Observed.** The ticket closes. This is the same defect as case 24.

### Case 26: the error message states a limit the product does not enforce

```console
$ python3 -m ticketdesk.cli --log ../logs/r26.jsonl create 'Printer on fire'
#1 open Printer on fire
$ python3 -m ticketdesk.cli --log ../logs/r26.jsonl close 1 '12345678'
error: resolution note must be at least 10 characters
(stderr, exit 2)
$ python3 -m ticketdesk.cli --log ../logs/r26.jsonl close 1 '123456789'
#1 closed
```

**Expected.** The limit in the message is the limit the product applies.

**Observed.** The message says 10 characters, but a 9-character note passes. A user who reads the error and counts gets the wrong answer.

**Most likely cause.** The branch changed the comparison in `tickets.py` and left the message text unchanged. The two values are separate literals.

### Case 1: the new `--help` description has a typo

```console
$ python3 -m ticketdesk.cli --help
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...

Manage support tikets from the shell.

positional arguments:
  {create,assign,close,list}

options:
  -h, --help            show this help message and exit
  --log LOG             path of the event log
```

**Expected.** The description reads "Manage support tickets from the shell."

**Observed.** The description reads "tikets". The exit code and the four subcommands are correct.

**Most likely cause.** A typo in the new `description=` argument in `ticketdesk/cli.py`.

### Case 15: an early-closing reader produces a Python error

Setup: 300 runs of `python3 -m ticketdesk.cli --log ../logs/c15.jsonl create "Bulk $i <300 y>"`, which makes about 97 KB of `list` output. The output must be larger than the pipe buffer.

```console
$ python3 -m ticketdesk.cli --log ../logs/c15.jsonl list | head -1 | cut -c1-40; echo "pipestatus: ${PIPESTATUS[*]}"
#1 open     Bulk 1 yyyyyyyyyyyyyyyyyyyyy
pipestatus: 120 0 0
Exception ignored while flushing sys.stdout:
BrokenPipeError: [Errno 32] Broken pipe
```

**Expected.** The `list` command stops without a message on stderr, as `cat` or `ls` do.

**Observed.** The stderr shows a `BrokenPipeError`, and the exit code is 120. Plain pipes such as `| grep` and `| wc` work. `main` shows the same error, so this defect is older than the branch.

**Most likely cause.** The CLI does not handle `SIGPIPE` or `BrokenPipeError` on stdout.

### Case 32: a bad `--log` path produces a traceback

```console
$ python3 -m ticketdesk.cli --log ../logs create 'Log is a dir'
Traceback (most recent call last):
  ...
IsADirectoryError: [Errno 21] Is a directory: '../logs'
(exit 1)
$ python3 -m ticketdesk.cli --log ../logs/no/such/dir/t.jsonl create 'Parent missing'
Traceback (most recent call last):
  ...
FileNotFoundError: [Errno 2] No such file or directory: '../logs/no/such/dir/t.jsonl'
(exit 1)
$ python3 -m ticketdesk.cli --log ../logs/no/such/dir/t.jsonl list
(no output, exit 0)
```

The evidence log holds the full tracebacks. The `...` lines mark frames removed here.

**Expected.** The CLI prints one line that names the path and the problem, then exits with a nonzero code.

**Observed.** A traceback of about 20 lines with absolute source paths, and exit code 1. The `list` command on the missing directory exits 0 with no output, so the user does not learn that the path is wrong until a `create` fails. `main` shows the same traceback.

**Most likely cause.** The CLI catches only `TicketError`. File-system errors from `store.py` are not caught.

### Case 30: BLOCKED, no surface shows the due time

**Expected.** Per TKT-005, the due time is the creation time plus 4, 24, or 72 hours.

**Observed.** No command prints a due time, and no `--help` text mentions one. The `created` event in the log has no due field either. The case needs a surface that shows the due time, or a product decision that the due time is internal.

## Missing or untested cases

- **TKT-005, due time.** BLOCKED, see case 30.
- **TKT-009, assignee kept after close.** No command shows the assignee, and the `closed` event carries no assignee. A user cannot see this rule from outside.
- **The installed `ticketdesk` entry point.** The task names `python3 -m ticketdesk.cli` as the surface. An install would write build files into the product tree.
- **Out-of-order IDs for TKT-013.** IDs only rise through the CLI, so the sort cannot be exercised without a hand-edited log.
- **Interrupted runs.** Each command finishes in about 36 ms, so a Ctrl-C mid-write was not attempted.
- **Concurrent writers.** `docs/architecture.md` declares a single writer, so this is out of scope.
- **`make test` and the PR claim that all tests pass.** The test suite is not the user surface, so it was not run.

## Issues found

1. **High. `assign` reopens a closed ticket, and a second `close` records a second resolution.** Cases 19 and 20. This is a regression from `main`. It breaks TKT-008, the forward-only rule in `tickets.md`, and the TKT-011 guarantee. Closed tickets show as `assigned` in `list` again. The PR claims a support request, but no spec change came with it.
2. **High. `list` no longer shows the priority.** Cases 7 and 12. This is a regression that breaks CLI-006. After this change, no command shows a ticket's priority, and scripts that parse `[P1]` stop working. The promised flag is not in this PR.
3. **Medium. The resolution note minimum is 9 characters, but TKT-010 says 10.** Cases 24, 25, and 26. This is a regression. The error message still says 10, so the CLI now tells the user a false limit.
4. **Low. A typo in the new `--help` description reads "tikets".** Case 1. This is a regression.
5. **Low. A bad `--log` path produces a traceback with exit code 1.** Case 32. This defect is older than the branch.
6. **Low. An early-closing reader produces a `BrokenPipeError` and exit code 120.** Case 15. This defect is older than the branch.
7. **Low, known. An unknown priority and a corrupt log line produce tracebacks with exit code 1.** Cases 9 and 38 pass their specs. The CLI-007 TODO records this conflict, and it is older than the branch.

## UX gaps

- **No command shows one ticket.** The assignee, the resolution, the due time, and now the priority have no surface. A `show <id>` command would cover TKT-005, TKT-009, and the priority at once.
- **The `--help` texts say little.** The subcommands have no one-line summaries. The `--priority` option does not list `P1`, `P2`, `P3`, or the default. The arguments `id`, `assignee`, and `resolution` have no help text.
- **A missing subcommand reports the internal name.** The message reads `the following arguments are required: cmd`.
- **Tracebacks print absolute source paths.** This affects issues 5 and 7, and it shows file-system layout to the user.
- **The README does not show how to run the CLI.** The run commands are only in AGENTS.md.

## Improvements worth doing

- **Write down the closed-ticket rule before you build it.** If support needs to reassign closed tickets, decide whether the state stays `closed` or a separate `reopen` command exists. Then update TKT-008 and the forward-only rule.
- **Change TKT-010, the check, and the message together.** One constant for the limit would keep the message and the check in step.
- **Keep the priority in `list` until the flag exists.** Otherwise a release can ship with no way to see the priority.
- **Add CLI tests.** AGENTS.md says the CLI has no tests. The PR says all tests pass, yet three spec rules changed. The suite likely has no case for TKT-008, for the TKT-010 boundary, or for CLI-006.

## Leftover artifacts

Everything is under `outputs/` of this run. Nothing is in the product tree.

- **Log files.** `outputs/logs/*.jsonl`, one per case group, such as `c19.jsonl` and `r24.jsonl`. `outputs/logs/c31cwd/tickets.jsonl` comes from the default-path case.
- **Captured output.** `outputs/logs/c40-a.txt`, `outputs/logs/c40-b.txt`, and `outputs/logs/c39-before.jsonl`.
- **Operator error.** In `outputs/logs/c23.jsonl`, a stray `assign 1 lee` reopened ticket 1. Case 23 was rerun on `c23b.jsonl`. The evidence log records this.
- **Baseline.** `outputs/main-baseline/` is a `git archive` of `main`, used only to tell regressions from older defects.
- **Tools.** `outputs/tools/t.sh` is the evidence-logging wrapper.

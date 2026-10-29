# E2e test report: feature/cli-tidy

**28/36 PASS, 7 FAILURE, 1 BLOCKED. No-go for merge.** Three of the four PR promises break product specs. The worst one lets anyone reopen a closed ticket and overwrite its resolution.

Four failures come from this branch. Three failures exist on `main` too, so they do not block this PR.

| Origin | Cases | Issues |
|---|---|---|
| Introduced by the branch | 2, 14, 18, 21 | 1 to 4 |
| Present on `main` too | 33, 34, 35 | 5 to 7 |
| No CLI surface | 23 | none |

## Scope, surface, environment

- **Scope.** The diff of `feature/cli-tidy` against `main` (`ticketdesk/cli.py`, `ticketdesk/tickets.py`), the four promises in `PR.md`, every item of the four affected specs, and the shell contract.
- **Surface and persona.** A shell user who runs `python3 -m ticketdesk.cli` from the repo root.
- **Environment.** Local only. Every log file is a throwaway file under the `outputs/work/` directory. No shared or prod-like system was touched.
- **Depth.** Comprehensive, because the request said "comprehensively, before it merges".
- **Baseline.** A separate clone of `main` at `8c5d958` ran the same commands. It shows which failures the branch introduced.

## Case table

| # | Case | Spec/ref | Status |
|---|---|---|---|
| 1 | `--help` answers, exit 0, lists 4 subcommands | readiness, CLI-001 | PASS |
| 2 | `--help` description line reads correctly | PR item 4 | FAILURE |
| 3 | No subcommand | CLI-001 | PASS |
| 4 | Unknown subcommand | CLI-001 | PASS |
| 5 | Missing log file: empty list, first create is #1, file created | LOG-006, TKT-004 | PASS |
| 6 | `create` without `--priority` gets P3 | CLI-003, TKT-001 | PASS |
| 7 | `create` with `--priority P1` and `P2` | CLI-003, TKT-003 | PASS |
| 8 | `create` with priority `P9` and `p1` | TKT-003 | PASS |
| 9 | Empty and whitespace-only title | TKT-002, CLI-007 | PASS |
| 10 | `create` without a title argument | shell contract | PASS |
| 11 | Assign an open ticket | CLI-004, TKT-006 | PASS |
| 12 | Reassign an assigned ticket | TKT-006 | PASS |
| 13 | Empty and whitespace-only assignee | TKT-007, CLI-007 | PASS |
| 14 | Assign a closed ticket | TKT-008, CLI-007, forward-only rule | FAILURE |
| 15 | Assign and close an unknown ticket | TKT-012, CLI-007 | PASS |
| 16 | Non-integer ID for `assign` and `close` | CLI-009 | PASS |
| 17 | Close with a 10-character note | CLI-005, TKT-009, TKT-010 | PASS |
| 18 | Close with the 9-character note `duplicate` | TKT-010, PR item 2 | FAILURE |
| 19 | Close with an 8-character note, bare and padded | TKT-010, CLI-007 | PASS |
| 20 | Close a closed ticket | TKT-011, CLI-007 | PASS |
| 21 | `list` line includes the priority | CLI-006, PR item 1 | FAILURE |
| 22 | `list` order, closed tickets included | TKT-013 | PASS |
| 23 | Due time by priority | TKT-005 | BLOCKED |
| 24 | `--log` beats `TICKETDESK_LOG` beats `./tickets.jsonl` | CLI-002 | PASS |
| 25 | Success writes nothing to stderr, exit 0 | CLI-008 | PASS |
| 26 | One event per change, none per `list` | LOG-001, LOG-002 | PASS |
| 27 | Event fields and `at` timestamp | LOG-003, LOG-004, INV-005 | PASS |
| 28 | Sorted keys, trailing newline, blank lines ignored | LOG-005 | PASS |
| 29 | Corrupt line stops every operation | LOG-007, INV-004 | PASS |
| 30 | Appending keeps every earlier byte | LOG-008, INV-002 | PASS |
| 31 | Replay is deterministic, a copy replays the same | LOG-009, INV-001 | PASS |
| 32 | IDs are not reused after a close | INV-003, TKT-004 | PASS |
| 33 | `list` into a pipe that closes early | shell contract | FAILURE |
| 34 | Unusual legal titles: unicode, quotes, 500 chars, leading dash, newline | edge | FAILURE |
| 35 | `--log` points at a directory or a missing parent directory | error path | FAILURE |
| 36 | Extra and garbage arguments | shell contract | PASS |

## Details for every non-PASS case

### Case 14: assigning a closed ticket reopens it (FAILURE)

The product accepts an assignment on a closed ticket and moves it back to `assigned`. TKT-008 requires the error `ticket <id> is closed`. The forward-only rule in `tickets.md` says nothing reopens a closed ticket.

Steps, on a fresh log:

```
$ python3 -m ticketdesk.cli --log /tmp/t.jsonl create "Printer on fire"
#1 open Printer on fire
$ python3 -m ticketdesk.cli --log /tmp/t.jsonl close 1 "0123456789"
#1 closed
$ python3 -m ticketdesk.cli --log /tmp/t.jsonl assign 1 sam
#1 assigned -> sam            (exit 0, expected "error: ticket 1 is closed", exit 2)
$ python3 -m ticketdesk.cli --log /tmp/t.jsonl list
#1 assigned Printer on fire
$ python3 -m ticketdesk.cli --log /tmp/t.jsonl close 1 "Reopened by accident, closing again"
#1 closed                     (exit 0, a second resolution is recorded)
```

The cascade defeats TKT-011. A direct second `close` still fails with `ticket 1 is already closed`. An `assign` followed by a `close` writes a second `closed` event with a new resolution, and the original note no longer reflects the ticket's state. On `main` the same `assign` fails with `error: ticket 1 is closed` and exit 2.

Most likely cause: the branch deleted the closed-state check at the top of `TicketService.assign` in `ticketdesk/tickets.py`. The PR describes this as "assigning a ticket now works at any point in its life". That request conflicts with TKT-008 and the forward-only rule, and the PR does not update either one.

### Case 18: a 9-character note closes a ticket (FAILURE)

`close 4 "duplicate"` succeeds with `#4 closed` and exit 0. TKT-010 rejects any note shorter than 10 characters after trimming. `"  123456789  "` also closes ticket 5.

The error text now disagrees with the behavior. An 8-character note still fails with `resolution note must be at least 10 characters`, but 9 characters pass. A user who reads the message and counts gets the wrong rule. On `main`, `close 1 "duplicate"` fails with that same message and exit 2.

Most likely cause: the branch changed the threshold in `TicketService.close` from `< 10` to `< 9` and left the message and TKT-010 at 10. The PR intends this change, but it ships without a spec update or a matching message.

### Case 21: `list` drops the priority column (FAILURE)

CLI-006 requires `#<id> [<priority>] <state> <title>`. The branch prints the line without the priority.

| | `list` output for a P1 ticket |
|---|---|
| `main` | `#1 [P1] closed   Printer on fire` |
| branch | `#1 closed   Printer on fire` |

After this change no CLI command shows a ticket's priority. The only place a user can find it is the raw log file. Any script that parses `list` output by the CLI-006 format also breaks.

Most likely cause: the branch removed `[{t.priority}]` from the `list` format string in `ticketdesk/cli.py`. The PR promises a flag "in a later PR" to bring the column back. Until then the branch breaks CLI-006 and leaves no CLI command that shows priority.

### Case 2: the help description misspells "tickets" (FAILURE)

`--help` now prints `Manage support tikets from the shell.` The word should be "tickets". Help text is the first thing a new user reads, so a typo there is a visible defect.

Most likely cause: a typo in the `description` argument of `argparse.ArgumentParser` in `ticketdesk/cli.py`.

### Case 23: no CLI output shows the due time (BLOCKED)

TKT-005 defines the due time as creation time plus 4, 24, or 72 hours by priority. No command prints the due time, and the log does not store it. The case cannot run through the shell surface.

Unblocked by: a command or output field that shows the due time. With case 21 the gap grows, because the user can no longer see the priority that sets the due time.

### Case 33: `list | head` prints a Python traceback (FAILURE)

With 20,000 tickets, `list | head -1` prints the first line and then a `BrokenPipeError` traceback on stderr. The `list` process exits with code 120.

```
$ python3 -m ticketdesk.cli --log big.jsonl list | head -1
#1 open     t1
Traceback (most recent call last):
  ...
BrokenPipeError: [Errno 32] Broken pipe
Exception ignored while flushing sys.stdout:
BrokenPipeError: [Errno 32] Broken pipe
```

The `main` clone shows the same traceback and exit code. The branch did not introduce it. The 20,000-ticket log was written by a short script, because 20,000 `create` calls through the CLI take about 13 minutes. With 7 tickets the pipe works.

Most likely cause: the CLI does not handle `SIGPIPE` or `BrokenPipeError` around its `print` calls.

### Case 34: a newline in a title breaks the list format (FAILURE)

A title with an embedded newline creates a ticket whose `list` entry spans two lines. CLI-006 promises one line per ticket, so any line-based consumer miscounts.

```
$ python3 -m ticketdesk.cli --log titles.jsonl create $'line one\nline two'
#4 open line one
line two
```

Unicode, quotes, shell metacharacters, a 500-character title, and a title after `--` all store and list without change. The `main` clone shows the same newline behavior.

Most likely cause: the product accepts control characters in titles and prints them without escaping. TKT-002 only rejects empty and whitespace-only titles.

### Case 35: a bad `--log` path prints a Python traceback (FAILURE)

`--log` pointing at a directory or at a file in a missing directory makes `create` print a full traceback and exit 1. The last line is readable, but the user sees about ten lines of Python internals first.

```
IsADirectoryError: [Errno 21] Is a directory: '.../outputs/work'
FileNotFoundError: [Errno 2] No such file or directory: '/nonexistent-dir/t.jsonl'
```

`list` with the missing-directory path prints nothing and exits 0. That matches LOG-006, but a typo in `--log` then looks like an empty help desk. The `main` clone shows the same traceback for the directory path.

Most likely cause: the CLI maps only `TicketError` to an `error:` line and exit 2. Every `OSError` escapes as a traceback.

## Missing or untested cases

- **Installed `ticketdesk` entry point.** Not run. The request named `python3 -m ticketdesk.cli` as the surface. `pyproject.toml` declares a `ticketdesk` script that the run did not install.
- **TKT-009 "the assignee is kept" after a close.** Not observable. No command prints the assignee after the `assign` output line. The log shows the `closed` event carries no assignee field, but the replayed assignee is not visible.
- **Interrupted run (Ctrl-C during append).** Not run. Each command finishes in about 40 ms, so a manual interrupt cannot land mid-write.
- **Concurrent writers.** Out of scope. `docs/architecture.md` assumes a single writer.
- **The unit test suite.** Not run, because it is not the user's surface. `PR.md` claims "all tests pass", but the specs above break, so the tests do not cover these rules.

## Issues found, by severity

1. **Critical. A closed ticket can be reopened and given a second resolution.** Case 14, with the TKT-011 bypass in its details. It breaks TKT-008, TKT-011 in effect, and the forward-only rule. It loses the audit meaning of a close.
2. **High. A 9-character resolution note closes a ticket.** Case 18. It breaks TKT-010, and the error message now states a rule the product does not enforce.
3. **High. `list` no longer shows priority.** Case 21. It breaks CLI-006, and no CLI command shows priority until the promised flag ships.
4. **Low. Typo in the help description.** Case 2. `tikets` for `tickets`.
5. **Low, present on `main`. A closed pipe prints a traceback and exit 120.** Case 33.
6. **Low, present on `main`. A newline in a title breaks one line per ticket.** Case 34.
7. **Low, present on `main`. Filesystem errors on `--log` escape as tracebacks.** Case 35.

The PR changes behavior that three specs define. `AGENTS.md` and `docs/product-specs/README.md` ask for confirmation before such a change. The branch changes no spec file, so the specs and the code now disagree on TKT-008, TKT-010, and CLI-006.

## UX gaps

- **Help text is thin.** No subcommand has a help line. `--priority` does not list `P1`, `P2`, `P3`. `--log` does not mention `TICKETDESK_LOG` or the `tickets.jsonl` default.
- **A missing subcommand names an internal variable.** The error reads `the following arguments are required: cmd`, and `cmd` appears nowhere in the help.
- **Priority is case-sensitive.** `--priority p1` fails with a traceback. Users will type lowercase.
- **Unknown priority and corrupt log print tracebacks.** The spec content holds for TKT-003 and LOG-007, so cases 8 and 29 pass. The user still sees a Python traceback with exit 1 instead of an `error:` line with exit 2. This is the open TODO under CLI-007.
- **Ticket details are invisible.** No command shows the assignee, priority, resolution, or due time of one ticket.
- **The README does not show how to run the CLI.** It mentions only `make test` and `make lint`. The run commands are in `AGENTS.md`.

## Improvements worth doing

- Decide the TKT-008 and TKT-010 changes with the spec owner first. If support wants reassignment of closed tickets, define what the state becomes and whether the resolution survives.
- Keep the priority column until the replacement flag exists, or ship the flag in this PR.
- Add CLI-level tests. `AGENTS.md` lists the CLI as "not covered by tests", which is how cases 14, 18, and 21 can pass `make test`.

## Leftover artifacts

All artifacts are kept on purpose under `/Users/dmitri/dev/swd-skills-e2simplify/evals/e2e-test/workspace/iteration-2/eval-1-cli-branch-with-spec-violations/old_skill/run-2/outputs/work/`.

- `life.jsonl`: the lifecycle log. Ticket 1 shows the reopen and the second close. Ticket 4 shows the `duplicate` close.
- `corrupt.jsonl` and `corrupt.before`: the corrupt-line fixture and its untouched copy.
- `big.jsonl`: the 20,000-ticket log for the pipe case.
- `titles.jsonl`: the unusual titles, including the newline title.
- `cwd/tickets.jsonl`, `env.jsonl`, `flag.jsonl`: the three log-path cases.
- `blank.jsonl`, `before.jsonl`, `copy.jsonl`, `list1`, `list2`: the log-format and replay checks.
- `main-copy/`, `main.jsonl`, `main-nl.jsonl`: the `main` baseline clone and its logs.
- `repo/ticketdesk/__pycache__/`: bytecode that Python wrote when it ran the module. No tracked file in the repo changed.

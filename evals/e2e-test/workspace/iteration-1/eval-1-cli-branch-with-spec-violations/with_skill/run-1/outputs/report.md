# E2e report: feature/cli-tidy

31/40 PASS, 9 FAILURE, 0 BLOCKED. Not ready to merge. The branch lets a closed ticket reopen and accepts resolution notes the spec forbids. Both break the ticket rules in `docs/product-specs/tickets.md`. The PR description also states that all tests pass, and one test fails.

## Scope, surface, environment

Scope is the branch `feature/cli-tidy` against `main`, as described in `PR.md`, plus the specs it touches and the blast radius. The affected specs are CLI-001 to CLI-009, TKT-001 to TKT-013, LOG-001 to LOG-009, and INV-001 to INV-005. The surface is the shell, running `python3 -m ticketdesk.cli` from the repo root as `AGENTS.md` documents. The user is a support agent at a terminal.

The environment is local dev, with the log at `OUTPUT_DIR/tickets.jsonl`. The depth is comprehensive. The case list in `OUTPUT_DIR/cases.md` was written before execution.

`OUTPUT_DIR` stands for `/Users/dmitri/dev/swd-skills/evals/e2e-test/workspace/iteration-1/eval-1-cli-branch-with-spec-violations/with_skill/run-1/outputs` throughout.

## Case table

| # | Case | Spec/ref | Status |
|---|---|---|---|
| 1 | `--help` exits 0, lists the four subcommands, `--log`, and a correctly spelled description | CLI-001, PR | FAILURE |
| 2 | No subcommand: usage on stderr, nothing on stdout, exit 2 | CLI-001 | PASS |
| 3 | Unknown subcommand: usage on stderr, exit 2 | CLI-001 | PASS |
| 4 | `list` on a missing log prints nothing, exit 0, creates no file | LOG-006, CLI-006 | PASS |
| 5 | First `create` without `--priority` prints `#1 open <title>`, exit 0, creates the file | CLI-003, CLI-008, LOG-006 | PASS |
| 6 | Second `create --priority P1` prints `#2 open ...` | CLI-003, TKT-004 | PASS |
| 7 | Empty and whitespace titles: `error: title is required`, exit 2, no event | TKT-002, CLI-007, LOG-001 | PASS |
| 8 | `--priority P9`: error names the value and the allowed values, exit 2 | TKT-003, CLI-007 | FAILURE |
| 9 | `--priority p1` (lowercase) is rejected with the same error | TKT-003 | FAILURE |
| 10 | `list` line format `#<id> [<priority>] <state> <title>` | CLI-006 | FAILURE |
| 11 | `list` order: ID ascending, closed tickets included | TKT-013 | PASS |
| 12 | `assign 1 dana` prints `#1 assigned -> dana`, `list` shows `assigned` | CLI-004, TKT-006 | PASS |
| 13 | Reassigning replaces the assignee | TKT-006 | PASS |
| 14 | Empty and whitespace assignees: `error: assignee is required`, exit 2, no event | TKT-007, CLI-007 | PASS |
| 15 | `assign 99 dana`: `error: no ticket 99`, exit 2 | TKT-012 | PASS |
| 16 | `assign abc dana`: usage error, exit 2, no event | CLI-009 | PASS |
| 17 | `assign 1` with no assignee: usage error, exit 2 | CLI-001 | PASS |
| 18 | `close 2 "Replaced the toner cartridge"` prints `#2 closed`, `list` shows `closed` | CLI-005, TKT-009 | PASS |
| 19 | Closing an assigned ticket keeps the assignee in the log | TKT-009 | PASS |
| 20 | 9-character note `duplicate` is rejected | TKT-010 | FAILURE |
| 21 | 8-character note is rejected with `resolution note must be at least 10 characters` | TKT-010 | PASS |
| 22 | 10-character note is accepted | TKT-010 | PASS |
| 23 | Notes that reach 10 characters only through surrounding whitespace are rejected | TKT-010 | FAILURE |
| 24 | Closing a closed ticket: `error: ticket 2 is already closed`, resolution unchanged | TKT-011 | PASS |
| 25 | Assigning a closed ticket: `error: ticket 1 is closed`, ticket stays `closed` | TKT-008, TKT-001 | FAILURE |
| 26 | `close 99 ...`: `error: no ticket 99`, exit 2 | TKT-012 | PASS |
| 27 | `close abc ...`: usage error, exit 2 | CLI-009 | PASS |
| 28 | `TICKETDESK_LOG` is used when `--log` is absent | CLI-002 | PASS |
| 29 | `--log` wins over `TICKETDESK_LOG` | CLI-002 | PASS |
| 30 | Without either, `tickets.jsonl` in the current directory is used | CLI-002 | PASS |
| 31 | Log lines: sorted keys, `kind`/`id`/`at` on every event, extra fields per kind, `at` is epoch seconds | LOG-002 to LOG-005 | PASS |
| 32 | `list` appends nothing, each mutation appends one line | LOG-001 | PASS |
| 33 | Appending leaves existing lines unchanged | LOG-008, INV-002 | PASS |
| 34 | Blank lines in the log are ignored on replay | LOG-005 | PASS |
| 35 | A corrupt line stops every operation with an error, not a traceback | LOG-007, INV-004, CLI-007 | FAILURE |
| 36 | Creating after a close continues the ID sequence | INV-003, TKT-004 | PASS |
| 37 | A title with spaces and non-ASCII characters is listed verbatim | CLI-003, CLI-006 | PASS |
| 38 | `list | head -1` exits cleanly with no traceback | shell contract | PASS |
| 39 | Subcommand `--help` describes the arguments | shell contract | FAILURE |
| 40 | Success commands write nothing to stderr | CLI-008 | PASS |

Every command below was run from `OUTPUT_DIR/repo` with `--log OUTPUT_DIR/tickets.jsonl` unless stated otherwise.

## Non-PASS details

### Case 25: assigning a closed ticket succeeds and reopens it

Steps, from a fresh log. Create a ticket, assign it, close it, then assign it again.

```
$ python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl close 1 "Reset the VPN tunnel config"
#1 closed
$ python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl assign 1 frank
#1 assigned -> frank
exit=0
$ python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl list
#1 assigned Printer on fire
```

Expected: `error: ticket 1 is closed` on stderr, exit 2, no event appended, state stays `closed` (TKT-008). Observed: exit 0, an `assigned` event is appended, and `list` shows ticket 1 as `assigned`. The ticket then accepts a second close. The log for ticket 1 now holds two `closed` events with different resolutions. TKT-001 says a ticket moves forward only and nothing reopens a closed ticket.

Most likely cause: the branch removes the `closed` check from `TicketService.assign` in `ticketdesk/tickets.py`. The same scenario on an extracted copy of `main` prints `error: ticket 1 is closed` with exit 2. The repo's own test `test_assign_requires_open_ticket` fails on this branch for this reason.

### Cases 20 and 23: a 9-character resolution note closes a ticket

Steps. Create a ticket, then close it with a note that is 9 characters after trimming.

```
$ python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl close 3 "duplicate"
#3 closed
exit=0
$ python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl close 4 "  abcdefghi  "
#4 closed
exit=0
$ python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl close 4 "dupe fix"
error: resolution note must be at least 10 characters
exit=2
```

Expected: both 9-character notes rejected with `resolution note must be at least 10 characters` (TKT-010). Observed: both accepted. An 8-character note is still rejected, and the error still says 10 characters. The product now enforces a minimum of 9 while telling the user 10. The note `  abcdefghi  ` is stored in the log with its surrounding whitespace.

Most likely cause: the branch changes the length check in `TicketService.close` from `< 10` to `< 9` without changing the message or TKT-010. On an extracted copy of `main`, `close 3 duplicate` is rejected.

### Case 10: `list` no longer shows the priority

```
$ python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl list
#1 open     Printer on fire
#2 open     VPN drops every hour
#3 open     Café laptop — ñ keyboard  double space
```

Expected per CLI-006: `#<id> [<priority>] <state> <title>`, for example `#2 [P1] open     VPN drops every hour`. Observed: no priority column. The user can no longer see which tickets are P1 without reading the raw log. The PR description names this change and defers the flag that restores the column to a later PR. CLI-006 was not updated.

Most likely cause: the branch removes `[{t.priority}]` from the `list` print in `ticketdesk/cli.py`. This is a deliberate change that contradicts the spec. `AGENTS.md` asks that such a conflict be surfaced and discussed before the change lands.

### Case 1: the new `--help` description misspells "tickets"

```
$ python3 -m ticketdesk.cli --help
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...

Manage support tikets from the shell.
```

Expected: a correctly spelled description. Observed: `tikets`. Everything else in the case passes. The exit code is 0, the four subcommands and `--log` are listed.

Most likely cause: a typo in the `description` argument added to `ArgumentParser` in `ticketdesk/cli.py` on this branch.

### Cases 8 and 9: an unknown priority prints a Python traceback

```
$ python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl create "Bad priority" --priority P9
Traceback (most recent call last):
  ...
  File ".../ticketdesk/sla.py", line 8, in due_at
    raise ValueError(f"unknown priority {priority!r}; expected one of {sorted(SLA_HOURS)}")
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
exit=1
```

The lowercase `p1` behaves the same way. Expected per TKT-003 and CLI-007: `error: <message>` on stderr naming the value and the allowed values, exit 2. Observed: a 13-line traceback and exit 1. The message at the bottom does name the value and the allowed values, and no ticket is created. The log stays at 2 lines.

Most likely cause: `due_at` raises `ValueError`, and `cli.py` only catches `TicketError`. The TODO under CLI-007 records this gap. It predates the branch and the branch does not change it.

### Case 35: a corrupt log line prints a Python traceback

Steps. Write a log whose second line is `this is not json`, then run any command against it.

```
$ python3 -m ticketdesk.cli --log OUTPUT_DIR/corrupt.jsonl list
Traceback (most recent call last):
  ...
ValueError: OUTPUT_DIR/corrupt.jsonl:2: corrupt event: Expecting value: line 1 column 1 (char 0)
exit=1
```

`create` and `assign` behave the same way. Expected per LOG-007 and CLI-007: an error naming the path, the line number, and `corrupt event`, with exit 2 and no traceback. Observed: the final line of a 30-line traceback carries the right content, with exit 1. No ticket state is printed and the file is left unchanged, which satisfies INV-004.

Most likely cause: `store.replay` raises `ValueError`, which `cli.py` does not catch. The TODO under CLI-007 records this gap. It predates the branch.

### Case 39: subcommand help lists arguments without describing them

```
$ python3 -m ticketdesk.cli create --help
usage: ticketdesk create [-h] [--priority PRIORITY] title

positional arguments:
  title

options:
  -h, --help           show this help message and exit
  --priority PRIORITY
```

Expected: each argument carries a one-line description. Observed: no argument of `create`, `assign`, or `close` has one. `--priority` shows neither the allowed values nor the default `P3`. A first-time user has to guess the values and then meets the traceback from case 8.

Most likely cause: the `add_argument` calls in `ticketdesk/cli.py` pass no `help`. This predates the branch.

## Missing or untested cases

- TKT-005, due time by priority. No command shows the due time and the log stores only the priority, so the surface cannot observe it.
- Interrupted runs. Each invocation runs for a few milliseconds and appends one line, so there is no meaningful window to interrupt.
- Case 30 ran from `OUTPUT_DIR/cwd-default` with `PYTHONPATH=OUTPUT_DIR/repo`, because the documented invocation needs the repo root as the current directory. Running it from the repo root would have left a `tickets.jsonl` inside the repo.
- Concurrent writers to one log. Out of scope, and no spec covers it.

## Issues found

1. **High. A closed ticket can be assigned and reopened.** Cases 25. Introduced by this branch. Breaks TKT-008 and the forward-only rule of TKT-001. Also lets a ticket be closed twice, which TKT-011 forbids. The PR frames it as a support request, but the spec was not changed and `test_assign_requires_open_ticket` fails.
2. **High. The resolution minimum is 9 while the spec and the error message say 10.** Cases 20, 23. Introduced by this branch. Breaks TKT-010. The user who types an 8-character note is told the minimum is 10, then succeeds with 9.
3. **Medium. `list` lost the priority column.** Case 10. Introduced by this branch. Contradicts CLI-006 and leaves no way to see priority from the CLI until the deferred flag lands.
4. **Medium. Unknown priority and corrupt log lines escape as tracebacks with exit 1.** Cases 8, 9, 35. Pre-existing. Recorded as an open TODO under CLI-007 and in `AGENTS.md`. The branch neither fixes it nor resolves the TODO.
5. **Medium. The PR description says all tests pass, and `make test` fails.** `test_assign_requires_open_ticket` fails with `TicketError not raised`. Not a case in the contract, observed while diagnosing issue 1.
6. **Low. `--help` misspells "tickets" as "tikets".** Case 1. Introduced by this branch, in the one line the PR added to help.
7. **Low. Subcommand help carries no argument descriptions.** Case 39. Pre-existing.
8. **Low. `--log` pointing into a missing directory prints a traceback.** Observed outside the contract: `create` with `--log OUTPUT_DIR/no-such-dir/t.jsonl` ends in `FileNotFoundError` with exit 1. Not compared against `main`.

## UX gaps

- `list` shows no assignee, so after `assign` there is no command that answers "who has ticket 3". Only the raw log does.
- There is no `show` command. The resolution note and the assignee of a ticket are visible only in the log file.
- The `[P1]` column was the only priority signal in the CLI. Removing it before the replacement flag exists leaves a gap for the P1 queue.
- `--priority` help does not list `P1`, `P2`, `P3` or the default, and the wrong value answers with a traceback.
- The `close` error says 10 characters. With issue 2 in place, a user who counts to 9 and succeeds learns not to trust the message.

## Improvements worth doing

- Decide the spec conflicts before merging. Each of the three deliberate changes (assign on closed, minimum 9, no priority column) contradicts a spec ID. `AGENTS.md` asks for discussion and a doc change first.
- Resolve the CLI-007 TODO. Catching `ValueError` at the CLI boundary would turn issues 4 and 8 into `error: ...` lines with exit 2.
- Add `help=` text to each argument, with the allowed priorities and the default.
- Trim the resolution note before storing it, or state in LOG-003 that it is stored verbatim. The log now holds `"  abcdefghi  "`.

## Leftover artifacts

All under `OUTPUT_DIR`, kept to reproduce the findings.

| File | Holds |
|---|---|
| `tickets.jsonl` | the main log, 14 events, tickets 1 to 5, with the reopen and the two `closed` events for ticket 1 |
| `snap-after-create.jsonl` | the first 3 lines of the main log, used for the LOG-008 comparison |
| `env.jsonl`, `flag.jsonl` | the CLI-002 logs for cases 28 and 29 |
| `cwd-default/tickets.jsonl` | the CLI-002 default-path log for case 30 |
| `blank.jsonl` | the LOG-005 log with blank lines, 3 tickets |
| `corrupt.jsonl`, `corrupt-before.jsonl` | the LOG-007 log with `this is not json` on line 2, and its unchanged copy |
| `cases.md` | the case list written before execution |
| `runner.sh` | the shell helper that captured stdout, stderr, and exit codes |

No file under `OUTPUT_DIR/repo` was modified. `make test` wrote `__pycache__` directories, which were removed.

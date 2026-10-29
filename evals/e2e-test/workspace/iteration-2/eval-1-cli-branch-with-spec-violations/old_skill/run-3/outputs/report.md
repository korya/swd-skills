# E2e test report: feature/cli-tidy

**39/50 PASS, 10 FAILURE, 1 BLOCKED. Do not merge: the branch lets a closed ticket reopen and take a second resolution, and it breaks three product specs.**

Six of the ten failures come from this branch. The PR changes TKT-008, TKT-010, and CLI-006 without a spec update or a user decision. AGENTS.md requires both. The other four failures exist on `main` too and are not regressions. The PR claims "All tests pass locally". A diagnostic `make test` run on this branch shows one failing unit test, `test_assign_requires_open_ticket`.

- **Scope.** The diff of `feature/cli-tidy` against `main`, the four PR items, the specs they touch (`cli.md`, `tickets.md`, `event-log.md`, `invariants.md`), and every other subcommand as blast radius.
- **Surface and persona.** A shell user who runs `python3 -m ticketdesk.cli` from the repo root. Python 3.15.2 on macOS.
- **Environment.** Local throwaway log files. No shared state.
- **Depth.** Comprehensive, because the request says "comprehensively" and "before it merges".

## Case table

| # | Case | Spec/ref | Status |
|---|---|---|---|
| R | Readiness: `--help` answers | CLI-001 | PASS |
| 1 | No subcommand | CLI-001 | PASS |
| 2 | Unknown subcommand | CLI-001 | PASS |
| 3 | `--help` description line | PR item 4 | FAILURE |
| 4 | `--log` selects the path | CLI-002 | PASS |
| 5 | `TICKETDESK_LOG` used without `--log` | CLI-002 | PASS |
| 6 | `--log` beats `TICKETDESK_LOG` | CLI-002 | PASS |
| 7 | Default `tickets.jsonl` in the current directory | CLI-002 | PASS |
| 8 | Create with the default priority | CLI-003, TKT-001 | PASS |
| 9 | Create with `--priority P1` and `P2` | CLI-003, TKT-003 | PASS |
| 10 | Create with an empty title | TKT-002, CLI-007 | PASS |
| 11 | Create with a whitespace title | TKT-002, CLI-007 | PASS |
| 12 | Create with priority `P9` | TKT-003, CLI-007 TODO | FAILURE |
| 13 | Create with lowercase `p1` is rejected | TKT-003 | PASS |
| 14 | IDs rise by one and are not reused after a close | TKT-004, INV-003 | PASS |
| 15 | List on a missing log file | LOG-006, CLI-006 | PASS |
| 16 | First create on a missing log file | LOG-006 | PASS |
| 17 | Assign an open ticket | CLI-004, TKT-006 | PASS |
| 18 | Reassign an assigned ticket | TKT-006 | PASS |
| 19 | Assign with an empty assignee | TKT-007, CLI-007 | PASS |
| 20 | Assign with a whitespace assignee | TKT-007, CLI-007 | PASS |
| 21 | Assign a closed ticket | TKT-008, CLI-007, PR item 3 | FAILURE |
| 22 | A closed ticket stays closed | tickets.md forward-only rule, TKT-011 | FAILURE |
| 23 | Assign an unknown ID | TKT-012, CLI-007 | PASS |
| 24 | Close an unknown ID | TKT-012, CLI-007 | PASS |
| 25 | Assign with a non-integer ID | CLI-009 | PASS |
| 26 | Close with a non-integer ID | CLI-009 | PASS |
| 27 | Close an open ticket | CLI-005, TKT-009 | PASS |
| 28 | Close an assigned ticket and keep the assignee | TKT-009 | BLOCKED |
| 29 | Accept a note of exactly 10 characters | TKT-010 | PASS |
| 30 | Reject the 9-character note `duplicate` | TKT-010, PR item 2 | FAILURE |
| 31 | Reject an 8-character note with a true message | TKT-010 | FAILURE |
| 32 | Reject a short note padded with spaces | TKT-010 | PASS |
| 33 | Close a closed ticket | TKT-011 | PASS |
| 34 | List format and order | CLI-006, TKT-013, PR item 1 | FAILURE |
| 35 | List appends nothing, and each change appends one event | LOG-001 | PASS |
| 36 | Event kinds and fields | LOG-002, LOG-003 | PASS |
| 37 | Timestamp is epoch seconds at append | LOG-004, INV-005 | PASS |
| 38 | Sorted-key JSON lines, blank lines ignored | LOG-005 | PASS |
| 39 | A corrupt line stops replay | LOG-007, INV-004 | PASS |
| 40 | The corrupt-line error follows CLI-007 | CLI-007 TODO | FAILURE |
| 41 | Appending never rewrites | LOG-008, INV-002 | PASS |
| 42 | Replay is deterministic | LOG-009 | PASS |
| 43 | Success writes nothing to stderr and exits 0 | CLI-008 | PASS |
| 44 | Subcommand `--help` lists the arguments | shell contract | PASS |
| 45 | Missing positional arguments | shell contract | PASS |
| 46 | `list` piped into `head` on a large log | shell contract | FAILURE |
| 47 | Unicode title round trip | edge | PASS |
| 48 | Log path in a missing directory | error path | FAILURE |
| 49 | Branch differs from `main` only where the PR says | blast radius | PASS |

## Details for each non-PASS case

### 21. Assign a closed ticket: FAILURE

**Regression from this branch.** The CLI accepts an assignment on a closed ticket, and the ticket goes back to `assigned`.

Steps, on a fresh log. The run used `artifacts/repro.jsonl` in place of `/tmp/x.jsonl`.

```
python3 -m ticketdesk.cli --log /tmp/x.jsonl create "VPN drops hourly" --priority P1
python3 -m ticketdesk.cli --log /tmp/x.jsonl close 1 "Router firmware upgraded"
python3 -m ticketdesk.cli --log /tmp/x.jsonl assign 1 sam
python3 -m ticketdesk.cli --log /tmp/x.jsonl list
```

| | Output of `assign` | Exit | `list` shows |
|---|---|---|---|
| Expected (TKT-008) | stderr `error: ticket 1 is closed` | 2 | `closed` |
| Observed | stdout `#1 assigned -> sam` | 0 | `#1 assigned VPN drops hourly` |
| `main` | stderr `error: ticket 1 is closed` | 2 | `closed` |

The log also gains an `assigned` event, so TKT-008's "the ticket is unchanged" fails too.

Most likely cause: the branch removes the closed-state check from `TicketService.assign` in `ticketdesk/tickets.py`. Replay then sets the state to `assigned` for every `assigned` event. The unit test `test_assign_requires_open_ticket` covers this rule and now fails.

### 22. A closed ticket stays closed: FAILURE

**Regression from this branch.** After the reopen in case 21, the CLI closes the ticket a second time and records a second resolution.

Steps: continue from case 21.

```
$ python3 -m ticketdesk.cli --log /tmp/x.jsonl close 1 "Closed a second time after reassign"
#1 closed
```

The log `repro.jsonl` now holds two `closed` events for ticket 1:

```
{"at": 1793296987.1001291, "id": 1, "kind": "created", "priority": "P1", "title": "VPN drops hourly"}
{"at": 1793296987.129083, "id": 1, "kind": "closed", "resolution": "Router firmware upgraded"}
{"assignee": "sam", "at": 1793296987.157263, "id": 1, "kind": "assigned"}
{"at": 1793296987.2131772, "id": 1, "kind": "closed", "resolution": "Closed a second time after reassign"}
```

`tickets.md` says "Nothing reopens a closed ticket." TKT-011 promises that the recorded resolution does not change. Both fail. The direct "close twice" path in case 33 still holds, so the guard on `close` works. The `assign` path goes around it.

Most likely cause: the same removed check as case 21. The PR text says "Assigning a ticket now works at any point in its life." That intent contradicts TKT-008 and the forward-only rule. The PR does not surface that conflict.

### 30. Reject the 9-character note `duplicate`: FAILURE

**Regression from this branch, on purpose.** The branch accepts a 9-character note. TKT-010 still requires at least 10 characters.

```
$ python3 -m ticketdesk.cli --log /tmp/x.jsonl close 5 duplicate
#5 closed
```

Expected per TKT-010: stderr `error: resolution note must be at least 10 characters`, exit 2. `main` gives exactly that. The note `"  duplicate  "` also closes a ticket, so trimming applies with the new limit of 9.

Most likely cause: the branch changes the comparison in `TicketService.close` from `< 10` to `< 9`. The spec stays unchanged. Either the code or TKT-010 must change, and the user must confirm which.

### 31. Reject an 8-character note with a true message: FAILURE

**Regression from this branch.** The rejection message states a limit of 10, but the real limit is now 9.

```
$ python3 -m ticketdesk.cli --log /tmp/x.jsonl close 6 "dup of 2"
error: resolution note must be at least 10 characters
```

A user who reads this message and types a 9-character note sees it succeed. The message is false. Most likely cause: the branch changes the number in the comparison but not in the error text.

### 34. List format and order: FAILURE

**Regression from this branch, on purpose.** `list` no longer prints the priority column that CLI-006 requires.

| | Line for ticket 1 |
|---|---|
| Expected (CLI-006), and `main` | `#1 [P3] closed   Printer on fire` |
| Observed | `#1 closed   Printer on fire` |

ID order, closed tickets, and the 8-character state padding are correct. A user now has no way to see a ticket's priority from the CLI. A script that parses the old format breaks.

Most likely cause: the branch drops `[{t.priority}]` from the `list` line in `ticketdesk/cli.py`. The PR defers the flag to "a later PR". CLI-006 stays unchanged.

### 3. `--help` description line: FAILURE

**Regression from this branch, low severity.** The new description line has a typo.

```
$ python3 -m ticketdesk.cli --help
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...

Manage support tikets from the shell.
```

Expected: `tickets`. Most likely cause: a typo in the `description` argument in `ticketdesk/cli.py`.

### 12. Create with priority `P9`: FAILURE

**Exists on `main`, known.** The CLI rejects `P9` with a Python traceback and exit code 1, not with `error: <message>` and exit code 2.

```
$ python3 -m ticketdesk.cli --log /tmp/x.jsonl create "Bad prio" --priority P9
Traceback (most recent call last):
  ...
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
exit=1
```

The TKT-003 content holds. The message names `P9` and the allowed values, and no ticket appears. The traceback is the problem. The CLI-007 TODO documents this conflict and asks for a user decision.

Most likely cause: `sla.due_at` raises `ValueError`, and the CLI catches only `TicketError`.

### 40. The corrupt-line error follows CLI-007: FAILURE

**Exists on `main`, known.** A corrupt log line produces a two-part Python traceback and exit code 1.

```
$ python3 -m ticketdesk.cli --log corrupt.jsonl list
Traceback (most recent call last):
  ...
ValueError: .../corrupt.jsonl:3: corrupt event: Expecting property name enclosed in double quotes: line 1 column 30 (char 29)
exit=1
```

LOG-007 passes in case 39. The last line names the path, line 3, and `corrupt event`, and `create` appends nothing. The CLI-007 TODO covers the traceback. Most likely cause: the store raises `ValueError`, which the CLI does not catch.

### 46. `list` piped into `head` on a large log: FAILURE

**Exists on `main`.** On a log of 1,500 tickets, `list | head -1` prints the first line, then leaks a Python error and exits with code 120.

```
$ python3 -m ticketdesk.cli --log big.jsonl list | head -1
#1 open     Ticket number 1 with a longer title for the pipe test
Exception ignored while flushing sys.stdout:
BrokenPipeError: [Errno 32] Broken pipe
pipestatus=120 0
```

Expected: no stderr output and a quiet exit, like other shell tools. The `list` output for that log is 105,786 bytes. Most likely cause: the CLI does not handle `SIGPIPE` or `BrokenPipeError`.

### 48. Log path in a missing directory: FAILURE

**Exists on `main`.** A `--log` path in a directory that does not exist gives a traceback.

```
$ python3 -m ticketdesk.cli --log artifacts/no/such/dir/t.jsonl create Nowhere
Traceback (most recent call last):
  ...
FileNotFoundError: [Errno 2] No such file or directory: 'artifacts/no/such/dir/t.jsonl'
exit=1
```

No spec covers this case. The expected outcome is a one-line `error:` message with the path. Most likely cause: the store opens the file for append without a check, and the CLI does not catch `OSError`.

### 28. Close an assigned ticket and keep the assignee: BLOCKED

The CLI has no command that shows a ticket's assignee after a close. `close` prints `#1 closed`. `list` prints ID, state, and title. The log holds the `assigned` and `closed` events, but the kept assignee exists only in the replayed state. A `show` command, or an assignee column in `list`, unblocks this case.

## Missing or untested cases

- **TKT-005, due time by priority.** No CLI output shows a due time. Only the library API exposes it, and that is a different surface.
- **The installed `ticketdesk` entry point.** The task said to run `python3 -m ticketdesk.cli`. A `pip install` run of the console script is out of scope.
- **An interrupted run.** Each command finishes in about 50 ms. No reliable way exists to send Ctrl-C during the append.
- **Concurrent writers.** `docs/architecture.md` documents a single-writer assumption with no lock. Out of scope for this PR.
- **Python 3.11 and 3.12.** All cases ran on Python 3.15.2. CI uses 3.12, and the package claims 3.11 or newer.

## Issues found

1. **Critical. A closed ticket reopens on `assign` and takes a second resolution.** This breaks TKT-008, TKT-011, and the forward-only rule in `tickets.md`. It also corrupts history, because one ticket now has two resolutions. Cases 21 and 22. Regression.
2. **High. The PR contradicts three specs and does not update or cite them.** TKT-008, TKT-010, and CLI-006 still describe the `main` behavior. AGENTS.md says "If a change contradicts a spec or invariant, stop and discuss." Cases 21, 30, and 34.
3. **High. `list` drops the priority column.** It breaks CLI-006, and no other command shows priority. Case 34. Regression.
4. **High. The PR claims "All tests pass locally", but one unit test fails.** `make test` on this branch reports `FAILED (failures=1)` in `test_assign_requires_open_ticket`. This is diagnostic evidence, not a case verdict.
5. **Medium. The resolution limit is 9, but the spec and the error message say 10.** Cases 30 and 31. Regression.
6. **Medium. Unknown priority and corrupt log lines escape as tracebacks with exit code 1.** Cases 12 and 40. Exists on `main`, open as the CLI-007 TODO.
7. **Low. A missing log directory gives a traceback.** Case 48. Exists on `main`.
8. **Low. `list | head` leaks `BrokenPipeError` and exits 120.** Case 46. Exists on `main`.
9. **Low. The help description says "tikets".** Case 3. Regression.

## UX gaps

- **The CLI cannot show one ticket.** A user cannot see the assignee, resolution, or due time of a ticket. With the priority column gone, `list` shows even less.
- **The help text is thin.** No subcommand has a description. `--priority` does not list `P1`, `P2`, `P3`. The `id`, `assignee`, and `resolution` arguments have no help text. No `--version` flag exists.
- **The README does not say how to run the CLI.** It mentions only `make test` and `make lint`. The invocation is in AGENTS.md alone.
- **The log escapes non-ASCII text.** The title `Écran cassé` is stored as `Écran cassé`. `grep Écran tickets.jsonl` finds nothing, yet `event-log.md` says users read the file with any text tool.
- **The short-note error does not give the note's length.** A user must count characters to see how far off the note is.

## Improvements worth doing

- **Add CLI tests.** AGENTS.md says the CLI has no tests. A test of the `list` line and of exit codes catches issues 3 and 6 before review.
- **Settle the CLI-007 TODO.** Two of the four failures that exist on `main` come from that open decision.
- **Cite spec IDs in the PR description.** AGENTS.md asks for it, and it makes a spec conflict visible at review time.

## Leftover artifacts

All files are under `outputs/artifacts/` unless the path says otherwise. They are kept to reproduce the findings.

- `repro.jsonl`: the exact repro of cases 21 and 22. Ticket 1 has two `closed` events.
- `flow.jsonl`: the main lifecycle log. Ticket 2 has two `closed` events (issue 1). Tickets 5 and 10 closed with 9-character notes (issue 5).
- `main-tree/` and `main-flow.jsonl`: a `git archive` export of `main` and the log used to compare behavior (case 49).
- `big.jsonl`: 1,500 tickets created through the CLI for the pipe case. `pipe-stderr.txt` holds the leaked error.
- `corrupt.jsonl`: a log with a corrupt line 3 (cases 39 and 40).
- `blank.jsonl`: the flow log with blank lines between events (case 38).
- `unicode.jsonl`: Unicode and dash-leading titles (case 47).
- `c04.jsonl`, `c05.jsonl`, `c06-flag.jsonl`, and `outputs/repo/tickets.jsonl`: the log path cases 4 to 7.
- `flow-before-append.jsonl`, `l1.txt`, `l2.txt`: snapshots for cases 41 and 42.
- `r.sh`: the helper that runs one command and prints stdout, stderr, and the exit code.
- `outputs/case-list.md`: the case list, written before execution.
- `outputs/repo/ticketdesk/__pycache__/` and `outputs/repo/tests/__pycache__/`: bytecode from the runs. No tracked file in `outputs/repo` changed.

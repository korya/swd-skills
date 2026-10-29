# E2e test report: feature/cli-tidy

**36/49 PASS, 11 FAILURE, 2 BLOCKED. Do not merge.** On this branch a closed ticket can be
assigned again. That reopens the ticket and lets an agent close it a second time with a new
resolution. The branch also breaks three specs: TKT-008, TKT-010, and CLI-006. Each of
these breaks is a PR promise, so the spec or the PR must change first.

The PR says "All tests pass locally". On this branch `make test` fails one of 7 tests.
The failing test is `test_assign_requires_open_ticket`. On main all 7 pass.

## Scope, surface, and environment

- **Scope.** Branch `feature/cli-tidy` (commit 4659f59) against `main`. It covers the four
  PR promises, the specs they touch in full (`cli.md`, `tickets.md`), and `event-log.md` and
  `invariants.md` as blast radius.
- **User and surface.** A support agent at a shell. The surface is
  `python3 -m ticketdesk.cli`, run from the repo root as the task instructs.
- **Environment.** Local macOS, Python 3.15.2. Every case used its own throwaway log file
  under `outputs/artifacts/`. Mutation was safe.
- **Depth.** Comprehensive. The request said "comprehensively" and "before it merges".
- **Baseline.** I ran seven key cases against an export of `main` (`outputs/main-baseline/`)
  to separate regressions from old defects. Those runs are tagged `BASE-*` in the log.

The evidence log is
`/Users/dmitri/dev/swd-skills-e2claims/evals/e2e-test/workspace/iteration-5/eval-1-cli-branch-with-spec-violations/with_skill/run-1/outputs/evidence.log`.
In it, `$C` means `python3 -m ticketdesk.cli` and `$A` means the `outputs/artifacts` directory.
The case list, written before execution, is in `outputs/cases.md`.

## Case table

| # | Case | Spec/ref | Status |
|---|------|----------|--------|
| R1 | Readiness: `--help` answers | smoke | PASS |
| 1 | Top-level `--help` description line | PR, CLI-001 | FAILURE |
| 2 | Subcommand `--help` for each command | CLI-003 to CLI-006 | PASS |
| 3 | No subcommand | CLI-001 | PASS |
| 4 | Unknown subcommand | CLI-001 | PASS |
| 5 | Missing required arguments | CLI-001 | PASS |
| 6 | Log path from `--log` | CLI-002 | PASS |
| 7 | Log path from `TICKETDESK_LOG` | CLI-002 | PASS |
| 8 | `--log` wins over `TICKETDESK_LOG` | CLI-002 | PASS |
| 9 | Default `tickets.jsonl` in the current directory | CLI-002 | PASS |
| 10 | Missing log file | LOG-006, CLI-006 | PASS |
| 11 | create with default priority | CLI-003, TKT-001, TKT-004 | PASS |
| 12 | create with `--priority P1` and `P2` | CLI-003, TKT-003 | PASS |
| 13 | Empty title | TKT-002, CLI-007 | PASS |
| 14 | Whitespace-only title | TKT-002, CLI-007 | PASS |
| 15 | Unknown priority `P9` | TKT-003, CLI-007 TODO | FAILURE |
| 16 | Unicode, quotes, and a leading dash in a title | edge | PASS |
| 17 | IDs rise by one and are not reused | TKT-004, INV-003 | PASS |
| 18 | Due time by priority | TKT-005 | BLOCKED |
| 19 | Assign an open ticket | PR, TKT-006, CLI-004 | PASS |
| 20 | Reassign an assigned ticket | TKT-006 | PASS |
| 21 | Assign a closed ticket | PR, TKT-008 | FAILURE |
| 22 | State after assigning a closed ticket | TKT-001, forward-only rule | FAILURE |
| 23 | Close again after assigning a closed ticket | TKT-011 | FAILURE |
| 24 | Whitespace-only and empty assignee | TKT-007 | PASS |
| 25 | Assign an unknown ticket | TKT-012 | PASS |
| 26 | Assign with a non-integer ID | CLI-009 | PASS |
| 27 | Close with a 10-character note | TKT-009, TKT-010, CLI-005 | PASS |
| 28 | Close with `duplicate` (9 characters) | PR, TKT-010 | FAILURE |
| 29 | Close with an 8-character note | TKT-010 | FAILURE |
| 30 | Close with `   duplicate   ` | TKT-010 | FAILURE |
| 31 | Close with an empty or blank note | TKT-010 | PASS |
| 32 | Close keeps the assignee | TKT-009 | BLOCKED |
| 33 | Close twice | TKT-011 | PASS |
| 34 | Close an unknown ticket | TKT-012 | PASS |
| 35 | Close with a non-integer ID | CLI-009 | PASS |
| 36 | list line format with priorities | PR, CLI-006 | FAILURE |
| 37 | list order, closed tickets included | TKT-013 | PASS |
| 38 | list in a pipe | shell contract | FAILURE |
| 39 | Success exits 0 with empty stderr | CLI-008 | PASS |
| 40 | Rule errors leave stdout empty | CLI-007 | PASS |
| 41 | One event per change, none for list | LOG-001, LOG-002 | PASS |
| 42 | Event fields, sorted keys, newline | LOG-003, LOG-005 | PASS |
| 43 | Timestamp is the append time | LOG-004, INV-005 | PASS |
| 44 | Blank lines ignored on replay | LOG-005 | PASS |
| 45 | Corrupt line stops replay | LOG-007, INV-004 | FAILURE |
| 46 | Appending never rewrites | LOG-008, INV-002 | PASS |
| 47 | Replay is deterministic | LOG-009 | PASS |
| 48 | Interrupted run (Ctrl-C) | shell contract | PASS |

## Non-PASS details

### Cases 21, 22, 23: a closed ticket can be assigned, reopened, and closed again

TKT-008 requires `error: ticket <id> is closed` and an unchanged ticket. Instead the assign
succeeds and the ticket moves from `closed` back to `assigned`. A second close then records a
new resolution. This breaks the rule in `tickets.md` that a ticket moves forward only. It also
defeats TKT-011, because the ticket now has two `closed` events with two resolutions.

What was done, from the repo root:

```
$ python3 -m ticketdesk.cli --log ../artifacts/repro1.jsonl create "Printer on fire"
#1 open Printer on fire
[exit 0]
$ python3 -m ticketdesk.cli --log ../artifacts/repro1.jsonl close 1 "Replaced the toner cartridge"
#1 closed
[exit 0]
$ python3 -m ticketdesk.cli --log ../artifacts/repro1.jsonl assign 1 dana
#1 assigned -> dana
[exit 0]
$ python3 -m ticketdesk.cli --log ../artifacts/repro1.jsonl list
#1 assigned Printer on fire
[exit 0]
$ python3 -m ticketdesk.cli --log ../artifacts/repro1.jsonl close 1 "Actually it was the fuser"
#1 closed
[exit 0]
$ grep closed ../artifacts/repro1.jsonl
{"at": 1793305041.0238998, "id": 1, "kind": "closed", "resolution": "Replaced the toner cartridge"}
{"at": 1793305041.128354, "id": 1, "kind": "closed", "resolution": "Actually it was the fuser"}
[exit 0]
```

Expected at the `assign` step: `error: ticket 1 is closed` on stderr, exit 2, and the ticket
still `closed` in the list. On `main` the same steps give exactly that (block `BASE-21`):

```
--- stdout
#1 closed
[exit 2]
#1 [P3] closed   Printer on fire
--- stderr
error: ticket 1 is closed
```

Most likely cause: the branch deletes the `closed` check from `TicketService.assign` in
`ticketdesk/tickets.py`. The PR calls this intended ("Assigning a ticket now works at any
point in its life"). It contradicts TKT-008 and the forward-only rule, and the PR cites
neither. The repo's own test for the rule fails on this branch (block `DIAG-tests`):

```
FAIL: test_assign_requires_open_ticket (test_tickets.TicketTests.test_assign_requires_open_ticket)
...
AssertionError: TicketError not raised
```

### Cases 28, 29, 30: the resolution minimum is 9 characters, but the error says 10

TKT-010 rejects any note shorter than 10 characters after trimming. The branch accepts a
9-character note. It still rejects 8 characters, with a message that names 10 as the minimum.

```
$ python3 -m ticketdesk.cli --log ../artifacts/repro2.jsonl create "Printer on fire"
#1 open Printer on fire
[exit 0]
$ python3 -m ticketdesk.cli --log ../artifacts/repro2.jsonl close 1 "wontfix"
error: resolution note must be at least 10 characters
[exit 2]
$ python3 -m ticketdesk.cli --log ../artifacts/repro2.jsonl close 1 "duplicate"
#1 closed
[exit 0]
```

Expected per TKT-010: the CLI rejects `duplicate` with the same error, and the ticket stays
`open`. On `main` the CLI rejects it (block `BASE-28`). Case 30 shows that `   duplicate   `
also closes the ticket, because 9 characters remain after trimming.

The change also delivers less than the PR promises. Only notes of exactly 9 characters gain
anything. The CLI still refuses `wontfix` (7 characters) and `12345678` (8 characters, case
29). The error then tells the agent the wrong minimum.

Most likely cause: the comparison in `TicketService.close` changed from `< 10` to `< 9`, and
the message string stayed the same. The repo test `test_close_needs_resolution_note` uses
the 4-character note `done`, so it cannot catch a shift at the boundary.

### Case 36: list no longer shows the priority

CLI-006 defines each list line as `#<id> [<priority>] <state> <title>`. The branch drops
the `[<priority>]` part.

```
$ python3 -m ticketdesk.cli --log ../artifacts/repro3.jsonl create "Server down" --priority P1
#1 open Server down
[exit 0]
$ python3 -m ticketdesk.cli --log ../artifacts/repro3.jsonl create "New mouse"
#2 open New mouse
[exit 0]
$ python3 -m ticketdesk.cli --log ../artifacts/repro3.jsonl list
#1 open     Server down
#2 open     New mouse
[exit 0]
```

Expected: `#1 [P1] open     Server down` and `#2 [P3] open     New mouse`. The `main` baseline
prints that format (block `BASE-36`).

After this change no command shows the priority of a ticket. A P1 ticket with a 4-hour target
looks the same as a P3 ticket. The PR says a flag brings the column back "in a later PR".
Until then, an agent must read the JSON log to find urgent tickets.

Most likely cause: the branch edits the list `print` in `ticketdesk/cli.py` on purpose. The
PR does not cite CLI-006, and the spec is unchanged.

### Case 1: the new `--help` description has a typo

```
$ python3 -m ticketdesk.cli --help | grep tikets
Manage support tikets from the shell.
[exit 0]
```

Expected: "Manage support tickets from the shell." The typo is new on this branch.

### Cases 15 and 45: an unknown priority and a corrupt log print a Python traceback

Both errors carry the right content, but the user gets a traceback and exit code 1. For an
unknown priority, the last line names `P9` and the allowed values, as TKT-003 requires. For a
corrupt log, the last line names the file, the line number, and `corrupt event`, as LOG-007
requires. No ticket is created, and no state is returned.

```
$ python3 -m ticketdesk.cli --log ../artifacts/repro5.jsonl create "Bad prio" --priority P9 2>&1 | tail -2; echo "[python exit ${PIPESTATUS[0]}]"
    raise ValueError(f"unknown priority {priority!r}; expected one of {sorted(SLA_HOURS)}")
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
[python exit 1]
[exit 0]
$ echo "{not json" > ../artifacts/repro5b.jsonl; python3 -m ticketdesk.cli --log ../artifacts/repro5b.jsonl list 2>&1 | grep -c "^Traceback"; python3 -m ticketdesk.cli --log ../artifacts/repro5b.jsonl list 2>&1 | tail -1; echo "[python exit ${PIPESTATUS[0]}]"
2
ValueError: ../artifacts/repro5b.jsonl:1: corrupt event: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
[python exit 1]
[exit 0]
```

Expected for a shell user: one `error: ...` line on stderr and a defined exit code. The
corrupt-log case prints two chained tracebacks, 35 lines in total. This defect is old, and
`main` behaves the same (blocks `BASE-15`, `BASE-45`). The open TODO under CLI-007 already
records it, so it does not block this PR on its own.

Most likely cause: `cli.py` catches only `TicketError`. The `ValueError` from `sla.py` and
`store.py` escapes to the interpreter.

### Case 38: `list | head` prints a BrokenPipeError traceback

When a reader closes the pipe early, the CLI prints a traceback to stderr and exits 120. The
log for this case holds 4000 tickets, all created through the CLI.

```
$ python3 -m ticketdesk.cli --log ../artifacts/c38.jsonl list | head -1; echo "[python exit ${PIPESTATUS[0]}]"
#1 open     Bulk ticket number 1 with a longer title
Traceback (most recent call last):
...
BrokenPipeError: [Errno 32] Broken pipe
Exception ignored while flushing sys.stdout:
BrokenPipeError: [Errno 32] Broken pipe
[python exit 120]
[exit 0]
```

Expected: the first line, no traceback, and a quiet exit. This defect is old, and `main`
shows the same traceback (block `BASE-38`). Most likely cause: the CLI does not handle
`BrokenPipeError`. Small lists probably avoid it because their output fits in the pipe
buffer.

### Cases 18 and 32: blocked, because no command shows due time or assignee

- **Case 18, TKT-005.** No command output and no log field carries a due time. The log
  stores only the creation time and the priority. A command or field that shows the due
  time unblocks this case.
- **Case 32, TKT-009.** After a close, no command shows the assignee. The log keeps the
  `assigned` event, but the derived state is not visible. A command that shows one ticket in
  full, or an assignee column in `list`, unblocks it.

## Missing or untested cases

- **The installed `ticketdesk` entry point.** Not run. The task fixed the invocation as
  `python3 -m ticketdesk.cli`. A `pip install` would also write build files into the repo
  tree.
- **Python 3.11 and 3.12.** Not run. CI uses 3.12, and this machine has 3.15.2. The failing
  test checks a ticket rule, so it will likely fail on 3.12 too. I did not verify that.
- **Two writers at once.** Not run. It is outside the change, but INV-003 depends on it.
- **LOG-007, lines after the corrupt line.** Partly run. Replay stopped at the corrupt line,
  but no valid line followed it in the test log.

## Issues found

1. **High, regression.** A closed ticket can be assigned. That reopens it and allows a second
   close with a new resolution. It breaks TKT-008, the forward-only rule, and in effect
   TKT-011. Cases 21, 22, 23. It also fails the repo's own test suite.
2. **Medium, regression.** The resolution minimum is 9 characters, and the error says 10. It
   breaks TKT-010. Cases 28, 29, 30.
3. **Medium, regression.** `list` drops the priority, and no other command shows it. It
   breaks CLI-006. Case 36.
4. **Low, regression.** The `--help` description reads "tikets". Case 1.
5. **Low, old.** An unknown priority and a corrupt log print a traceback with exit 1. This is
   the known CLI-007 TODO. Cases 15, 45.
6. **Low, old.** `list` piped into `head` prints a BrokenPipeError traceback and exits 120.
   Case 38.

The PR's claim "All tests pass locally" does not hold on this branch. Here `make test`
reports `FAILED (failures=1)`. On `main` it reports `OK` (blocks `DIAG-tests`,
`DIAG-tests-main`).

## UX gaps

- **Help text is bare.** Subcommand help lists argument names only. It does not state the
  allowed priorities, the default `P3`, or the resolution minimum (case 2).
- **An internal name leaks.** With no subcommand, the error reads
  `the following arguments are required: cmd` (case 3). A user knows the word "command".
- **The `#` prefix is not accepted back.** The CLI prints IDs as `#1`, but `close "#1" ...`
  fails with `invalid int value: '#1'` (case 35). A copy and paste from the output fails.
- **No command shows one ticket in full.** Assignee, resolution, and due time are visible only
  in the raw JSON log (cases 18, 20, 32). After this branch, priority joins that list.
- **An interrupted create can still succeed.** One Ctrl-C run printed `KeyboardInterrupt` and
  exited 130, but its ticket was in the log (case 48, ticket 4001). An agent who retries
  creates a duplicate.
- **The log escapes non-ASCII text.** The log stores the title `Café` as `Café` (case
  16). `event-log.md` says users may read the file with any text tool.
- **The README does not say how to run the CLI.** It covers only `make test` and `make lint`.
  The run commands are only in `AGENTS.md`.

## Improvements worth doing

- **Settle the spec first.** The PR intends all three spec breaks. `AGENTS.md` says a change
  that contradicts a spec must stop for discussion. Either revert the code, or change TKT-008,
  TKT-010, and CLI-006 with the user's confirmation.
- **Cite spec IDs in the PR.** `AGENTS.md` asks for them, and the PR cites none.
- **Add CLI tests.** `AGENTS.md` lists the CLI as untested. A test at the 9 and 10 character
  boundary would have caught issue 2.
- **Close the CLI-007 TODO.** A handler for `ValueError` and `BrokenPipeError` in `cli.py`
  would likely fix issues 5 and 6.

## Leftover artifacts

All of these come from driving the CLI or from running Python. No tracked file changed.
`git status` shows only untracked files, and `git diff` is empty (block `FINAL-tree`).

- `outputs/artifacts/*.jsonl`: one log per case, the `repro*` logs, and the `base*` logs.
  `c38.jsonl` holds 4000 tickets. `c48b.jsonl` holds the Ctrl-C runs.
- `outputs/artifacts/c21.before`, `c39.err`, `c46.prev`, `c48.err`: helper files from the cases.
- `repo/tickets.jsonl`: ticket `#1 Default path`, from case 9.
- `repo/ticketdesk/__pycache__/` and `repo/tests/__pycache__/`: Python bytecode caches.
- `outputs/main-baseline/`: an export of `main` for the `BASE-*` runs.
- `outputs/harness/t.sh` and `outputs/harness/repro.sh`: the scripts that wrote the evidence log.

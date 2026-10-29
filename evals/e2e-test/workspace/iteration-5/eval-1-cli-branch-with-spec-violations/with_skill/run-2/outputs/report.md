# E2e test report: feature/cli-tidy

**31/39 PASS, 7 FAILURE, 1 BLOCKED. No-go.** The branch breaks three specified behaviors that work on `main`. A closed ticket reopens when you assign it. The `list` command no longer shows priority. A 9-character resolution note now closes a ticket.

The repo's own `make test` also fails on this branch, although the PR says all tests pass.

The PR changes CLI-006, TKT-008, and TKT-010 but edits no spec. AGENTS.md requires a stop and a discussion when a change contradicts a spec. Decide each change with the spec owner first. Then either revert the change or update the spec in the same PR.

## Scope, surface, and environment

- **Scope.** The diff of `feature/cli-tidy` against `main` and the four PR promises. Every criterion in `cli.md`, `tickets.md`, `event-log.md`, and `invariants.md`, because all four share the changed code paths.
- **User and surface.** A support agent in a shell. The surface is `python3 -m ticketdesk.cli` from the repo root, as the task named. Case 39 also checks the installed `ticketdesk` entry point.
- **Environment.** Local, macOS, Python 3.15.2. Every run used throwaway log files. CI uses Python 3.12, and this run did not cover it.
- **Depth.** Comprehensive, because the request says "comprehensively" and the run gates a merge.
- **Baseline.** For diagnosis only, the run extracted `main` with `git archive` and ran the failing cases there.
- **Evidence log.** `outputs/evidence.log` holds every command, its stdout, stderr, and exit code, tagged by case. The case list was written before execution in `outputs/cases.md`.

## Case table

| # | Case | Spec/ref | Status |
|---|------|----------|--------|
| 1 | `--help` shows the new description line, spelled correctly | PR item 4 | FAILURE |
| 2 | Subcommand `--help` is accurate | shell contract | PASS |
| 3 | No subcommand: usage on stderr, exit 2 | CLI-001 | PASS |
| 4 | Unknown subcommand: usage on stderr, exit 2 | CLI-001 | PASS |
| 5 | Missing log file: `list` prints nothing, exit 0, no file created | LOG-006, CLI-006 | PASS |
| 6 | First create prints `#1 open <title>`, creates the file, priority P3 | CLI-003, TKT-001, TKT-004, LOG-006 | PASS |
| 7 | Create with `--priority P1` | CLI-003, TKT-003 | PASS |
| 8 | Empty and whitespace titles fail with `title is required`, exit 2 | TKT-002, CLI-007 | PASS |
| 9 | Priority P9 fails with a clean error naming P9 and the allowed values | TKT-003, CLI-007 TODO | FAILURE |
| 10 | IDs rise by one, and closing does not free an ID | TKT-004, INV-003 | PASS |
| 11 | Due time is creation time plus the hours for the priority | TKT-005 | BLOCKED |
| 12 | `list` line is `#<id> [<priority>] <state> <title>` | CLI-006, PR item 1 | FAILURE |
| 13 | `list` includes closed tickets in ID order | TKT-013 | PASS |
| 14 | Assign an open ticket | CLI-004, TKT-006 | PASS |
| 15 | Assign again replaces the assignee | TKT-006 | PASS |
| 16 | Empty and whitespace assignees fail with `assignee is required` | TKT-007 | PASS |
| 17 | Assign a closed ticket fails with `ticket <id> is closed` | TKT-008, PR item 3 | FAILURE |
| 18 | Unknown ID fails with `no ticket <id>` for assign and close | TKT-012 | PASS |
| 19 | Non-integer ID gives a usage error, exit 2, no event | CLI-009 | PASS |
| 20 | A 10-character note closes the ticket | TKT-010, CLI-005 | PASS |
| 21 | A 9-character note (`duplicate`) is rejected | TKT-010, PR item 2 | FAILURE |
| 22 | An 8-character note is rejected with the TKT-010 message | TKT-010 | PASS |
| 23 | A short note padded with spaces is rejected after trimming | TKT-010 | FAILURE |
| 24 | Close keeps the assignee and records the note | TKT-009 | PASS |
| 25 | Close a closed ticket fails, resolution unchanged | TKT-011 | PASS |
| 26 | Rule errors go to stderr as `error: <message>`, stdout empty, exit 2 | CLI-007 | PASS |
| 27 | Successful commands exit 0 with empty stderr | CLI-008 | PASS |
| 28 | `--log` beats `TICKETDESK_LOG`, which beats `./tickets.jsonl` | CLI-002 | PASS |
| 29 | Create, assign, and close append one event each, and list appends none | LOG-001 | PASS |
| 30 | Event kinds and fields match the table | LOG-002, LOG-003 | PASS |
| 31 | `at` holds Unix-epoch seconds set at append | LOG-004, INV-005 | PASS |
| 32 | One JSON line per event, keys sorted, newline at the end | LOG-005 | PASS |
| 33 | Blank lines in the log are ignored | LOG-005 | PASS |
| 34 | A corrupt line stops every command with a clean error naming path and line | LOG-007, INV-004, CLI-007 TODO | FAILURE |
| 35 | Appending leaves existing lines byte-identical | LOG-008, INV-002 | PASS |
| 36 | Two replays of the same log give identical output | LOG-009, INV-001 | PASS |
| 37 | `list` works in a pipe | shell contract | PASS |
| 38 | Titles with quotes, non-ASCII, and a leading `--` round-trip | edge | PASS |
| 39 | The installed `ticketdesk` entry point works | AGENTS.md | PASS |

## Non-PASS details

Each repro below ran from the repo root on a fresh log file. Any new log path works in place of `../artifacts/rNN.jsonl`.

### Case 17: assigning a closed ticket reopens it (TKT-008)

**Steps and observed output:**

```
$ python3 -m ticketdesk.cli --log ../artifacts/r17.jsonl create "Printer on fire" --priority P1
#1 open Printer on fire
(exit 0)
$ python3 -m ticketdesk.cli --log ../artifacts/r17.jsonl close 1 "Replaced the toner cartridge"
#1 closed
(exit 0)
$ python3 -m ticketdesk.cli --log ../artifacts/r17.jsonl assign 1 omar
#1 assigned -> omar
(exit 0)
$ python3 -m ticketdesk.cli --log ../artifacts/r17.jsonl list
#1 assigned Printer on fire
(exit 0)
$ python3 -m ticketdesk.cli --log ../artifacts/r17.jsonl close 1 "A different resolution note"
#1 closed
(exit 0)
```

**Expected.** The `assign` command prints `error: ticket 1 is closed` to stderr, exits 2, and appends no event. The ticket stays `closed`.

**Observed.** The `assign` command succeeds, and the ticket goes back to `assigned`. A second `close` then succeeds and records a new resolution note. The ticket spec says "Nothing reopens a closed ticket." The repro breaks that rule. It also gets past TKT-011, because the ticket now carries a second resolution.

**Baseline.** On `main`, the same `assign` prints `error: ticket 1 is closed` and exits 2.

**Most likely cause.** The branch deletes the closed-state guard from `TicketService.assign` in `ticketdesk/tickets.py`. The repo's own test `test_assign_requires_open_ticket` fails for the same reason. The PR calls this change a support request. If support wants it, TKT-008 and the forward-only rule need a spec decision first.

### Case 12: `list` no longer shows priority (CLI-006)

**Steps and observed output:**

```
$ python3 -m ticketdesk.cli --log ../artifacts/r12.jsonl create "Printer on fire" --priority P1
#1 open Printer on fire
(exit 0)
$ python3 -m ticketdesk.cli --log ../artifacts/r12.jsonl create "New mouse"
#2 open New mouse
(exit 0)
$ python3 -m ticketdesk.cli --log ../artifacts/r12.jsonl list
#1 open     Printer on fire
#2 open     New mouse
(exit 0)
```

**Expected.** CLI-006 specifies the line `#<id> [<priority>] <state> <title>`. So the first line reads `#1 [P1] open     Printer on fire`.

**Observed.** The P1 ticket and the P3 ticket look the same. No flag brings the priority back, because `list --help` shows only `-h`. Any script that parses the old line format now reads the state where it expects the priority.

**Baseline.** On `main`, `list` prints `#1 [P1] open     Printer on fire`.

**Most likely cause.** The branch removes `[{t.priority}]` from the format string in `ticketdesk/cli.py`. The PR says the priority comes back "with a flag in a later PR". Until then, an agent cannot see which tickets are urgent.

### Cases 21 and 23: a 9-character resolution note closes a ticket (TKT-010)

**Steps and observed output:**

```
$ python3 -m ticketdesk.cli --log ../artifacts/r21.jsonl create "Duplicate report"
#1 open Duplicate report
(exit 0)
$ python3 -m ticketdesk.cli --log ../artifacts/r21.jsonl create "Another duplicate"
#2 open Another duplicate
(exit 0)
$ python3 -m ticketdesk.cli --log ../artifacts/r21.jsonl close 1 "duplicate"
#1 closed
(exit 0)
$ python3 -m ticketdesk.cli --log ../artifacts/r21.jsonl close 2 "   duplicate   "
#2 closed
(exit 0)
$ python3 -m ticketdesk.cli --log ../artifacts/r21.jsonl create "Eight chars"
#3 open Eight chars
(exit 0)
$ python3 -m ticketdesk.cli --log ../artifacts/r21.jsonl close 3 "Rebooted"
error: resolution note must be at least 10 characters
(exit 2)
```

**Expected.** TKT-010 rejects any note shorter than 10 characters after trimming. Both `duplicate` notes have 9 characters. Each `close` prints `error: resolution note must be at least 10 characters` and exits 2.

**Observed.** Both 9-character notes close their tickets. An 8-character note is still rejected, and the message still says "at least 10 characters". The message now states a rule that the product does not apply.

**Baseline.** On `main`, `close 1 'duplicate'` prints the error and exits 2.

**Most likely cause.** The branch changes the check in `TicketService.close` from `< 10` to `< 9`. It leaves the message and TKT-010 unchanged. The PR describes this change as a relaxed minimum. If the new minimum is 9, the spec and the message both need the new number.

### Case 1: the new help line misspells "tickets"

**Steps and observed output:**

```
$ python3 -m ticketdesk.cli --help | sed -n 3p
Manage support tikets from the shell.
(exit 0)
```

**Expected.** `Manage support tickets from the shell.`

**Most likely cause.** A typo in the new `description` argument in `ticketdesk/cli.py`.

### Case 9: an unknown priority prints a Python traceback (pre-existing)

**Steps and observed output:**

```
$ python3 -m ticketdesk.cli --log ../artifacts/r09.jsonl create "Bad priority" --priority P9 2>&1 | tail -1; exit ${PIPESTATUS[0]}
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
(exit 1)
$ python3 -m ticketdesk.cli --log ../artifacts/r09.jsonl list
(exit 0)
```

**Expected.** One line on stderr, such as `error: unknown priority 'P9'; expected one of P1, P2, P3`, and exit 2, like every other rule error.

**Observed.** The full stderr is a 14-line Python traceback. The last line names P9 and the allowed values, and no ticket is created. So the letter of TKT-003 holds, but the user sees a crash and exit code 1.

**Baseline.** The behavior on `main` is the same. This branch did not cause it. The open TODO under CLI-007 already records it.

**Most likely cause.** `sla.due_at` raises `ValueError`, and the CLI catches only `TicketError`.

### Case 34: a corrupt log line prints a Python traceback (pre-existing)

**Steps and observed output:**

```
$ python3 -m ticketdesk.cli --log ../artifacts/r34.jsonl create "Good ticket"
#1 open Good ticket
(exit 0)
$ echo "this is {not json" >> ../artifacts/r34.jsonl
(exit 0)
$ python3 -m ticketdesk.cli --log ../artifacts/r34.jsonl list 2>&1 | grep -c '^Traceback'; exit ${PIPESTATUS[0]}
2
(exit 1)
$ python3 -m ticketdesk.cli --log ../artifacts/r34.jsonl list 2>&1 | tail -1 | sed 's#.*/artifacts/#.../artifacts/#'; exit ${PIPESTATUS[0]}
.../artifacts/r34.jsonl:2: corrupt event: Expecting value: line 1 column 1 (char 0)
(exit 1)
```

**Expected.** One line on stderr that names the file, line 2, and `corrupt event`, with a non-zero exit code.

**Observed.** The fail-fast part works. In the case-34 run, `create`, `list`, `assign`, and `close` all stopped, and the log kept its 2 lines. But each command prints two chained Python tracebacks. For `list`, stderr is 34 lines long. The useful line comes last.

**Baseline.** The behavior on `main` is the same. The open TODO under CLI-007 already records it.

**Most likely cause.** `EventStore.replay` raises `ValueError`, and the CLI catches only `TicketError`.

### Case 11: due time is not visible anywhere (BLOCKED)

No user-facing output shows the due time. The `list` and `--help` output do not mention it, and the log stores only `at` and `priority`. So TKT-005 cannot be checked through the surface. A command or a `list` column that shows the due time unblocks this case.

## Missing or untested cases

- **Interrupted runs.** Each command finished in well under a second, so no Ctrl-C window existed to test.
- **Unwritable or invalid log path.** This error path is in the blast radius of CLI-002, but it was not on the case list.
- **Concurrent writers to one log.** No spec covers it.
- **Python 3.11 and 3.12.** The run used Python 3.15.2 only. CI uses 3.12.
- **The PR claim "All tests pass locally".** It is not an e2e case, so it is not in the table. The run checked it for diagnosis. See issue 4.

## Issues found

1. **High. A closed ticket reopens on `assign`, and it can then take a second resolution.** Case 17. This breaks TKT-008, the forward-only rule in `tickets.md`, and the intent of TKT-011. The branch introduces it.
2. **High. `list` drops the priority column.** Case 12. This breaks CLI-006. Agents can no longer see urgency, and scripts that parse the line break. The branch introduces it.
3. **Medium. The resolution minimum is 9 characters, but the error message and TKT-010 say 10.** Cases 21 and 23. The branch introduces it.
4. **Medium. `make test` fails on this branch, although the PR says "All tests pass locally".** The output ends with `FAILED (failures=1)` for `test_assign_requires_open_ticket`. CI runs `make test`, so CI will fail too. This is the same defect as issue 1.
5. **Low. The new `--help` line reads "tikets".** Case 1. The branch introduces it.
6. **Low, pre-existing. An unknown priority and a corrupt log line crash with a traceback and exit 1.** Cases 9 and 34. The behavior on `main` is the same. The CLI-007 TODO tracks it, and it waits for a user decision.

## UX gaps

- **The help text is thin.** No subcommand has a one-line summary. The `--priority` help does not list P1, P2, and P3. The `close` help does not state the minimum note length.
- **The `--log` help hides the fallbacks.** It says "path of the event log" and does not mention `TICKETDESK_LOG` or `./tickets.jsonl`.
- **The missing-subcommand error names an internal field.** It says `the following arguments are required: cmd`. A user never sees the word `cmd` anywhere else.
- **The assignee is not visible.** `list` shows no assignee, so an agent must read the raw log to see who owns a ticket.
- **The due time is not visible.** The product computes it per TKT-005, but no command shows it. See case 11.
- **The log escapes non-ASCII text.** The title `Café` is stored as `Café`. The event-log spec says users read the file with any text tool, and escapes make that harder.

## Improvements worth doing

- **Add CLI tests.** AGENTS.md lists the CLI as untested. A test on the `list` line format would have caught issue 2.
- **Document the run command in the README.** The task says the README documents `python3 -m ticketdesk.cli`. It does not. Only AGENTS.md shows how to run the CLI.
- **Make the PR cite spec IDs.** AGENTS.md asks for spec IDs in PR descriptions. This PR cites none, and that hid the three spec conflicts.

## Leftover artifacts

All of these come from test runs through the surface. No tracked file in the repo changed, and `git diff` on the branch is empty.

- `outputs/artifacts/*.jsonl`: one log file per case and per repro, such as `c17.jsonl` and `r17.jsonl`. Also `m.jsonl` from the `main` baseline.
- `outputs/artifacts/c26.stdout`, `c26.stderr`, `c27.err`, `c35.before`, `c36.a`, `c36.b`: captured output for cases 26, 27, 35, and 36.
- `outputs/repo/tickets.jsonl`: one ticket, "Default wins", from the default-path check in case 28.
- `outputs/repo/build/` and `outputs/repo/ticketdesk.egg-info/`: pip build output from case 39.
- `outputs/venv/`: the virtual environment with the installed `ticketdesk` package from case 39.
- `outputs/baseline-main/`: an extract of `main` for the baseline comparisons.
- `outputs/tools/run.sh` and `outputs/tools/session.sh`: the helpers that wrote `outputs/evidence.log`.

All `outputs/` paths are relative to `/Users/dmitri/dev/swd-skills-e2claims/evals/e2e-test/workspace/iteration-5/eval-1-cli-branch-with-spec-violations/with_skill/run-2/`.

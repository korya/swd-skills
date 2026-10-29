# E2e test report: feature/cli-tidy

**40/51 PASS, 9 FAILURE, 2 BLOCKED. Do not merge.** Three of the four PR items break a spec,
and the fourth ships a typo. The worst defect lets anyone reopen a closed ticket with
`assign` and then close it again with a new resolution.

Six failures are new on this branch. Three are pre-existing on `main` and are not caused
by this PR.

## Scope, surface, environment

- **Change.** `feature/cli-tidy` against `main`: the four items in `PR.md`, the specs they
  touch (CLI-006, TKT-006 to TKT-011), and the blast radius through `cli.py` and
  `tickets.py`. The blast radius covers create, the log path, the log format, and replay.
- **Persona and surface.** A support agent at a shell. Every command ran as
  `python3 -m ticketdesk.cli` from the repo root, as the task specified.
- **Environment.** Local only. Each case used its own throwaway log under `outputs/logs/`.
- **Depth.** Comprehensive, because the request said "comprehensively" and "before it
  merges".
- **Regression check.** Seven key cases also ran against an extract of `main`
  (`outputs/main-copy/`) to label each finding as new or pre-existing.

The case list was written before execution and is in `outputs/case-list.md`. Two cases
were split during execution, C34 and C44. In both, the error content met the spec but the
shell presentation did not, so each half gets its own verdict. Full command output for
every case is in `outputs/harness/evidence.log`.

## Case table

| # | Case | Spec/ref | Status |
|---|---|---|---|
| R0 | Readiness: `--help` answers | smoke | PASS |
| C01 | list shows the priority column | CLI-006, PR item 1 | FAILURE (new) |
| C02 | list on a missing log | LOG-006, CLI-006 | PASS |
| C03 | list order, closed tickets included | TKT-013 | PASS |
| C04 | state padded to 8 characters | CLI-006 | PASS |
| C05 | list appends nothing | LOG-001 | PASS |
| C06 | list in a pipe | shell contract | PASS |
| C07 | list piped to `head` on a large log | shell contract | FAILURE (pre-existing) |
| C08 | close with the 9-character note "duplicate" | TKT-010, PR item 2 | FAILURE (new) |
| C09 | close with a 10-character note | TKT-010, CLI-005 | PASS |
| C10 | close with an 8-character note | TKT-010, CLI-007 | PASS |
| C11 | close with a padded short note | TKT-010 | PASS |
| C12 | close with an empty or blank note | TKT-010 | PASS |
| C13 | close an open ticket directly | TKT-009 | PASS |
| C14 | close keeps the assignee | TKT-009 | BLOCKED |
| C15 | close twice | TKT-011 | PASS |
| C16 | close an unknown ID | TKT-012, CLI-007 | PASS |
| C17 | close with a non-integer ID | CLI-009 | PASS |
| C18 | assign an open ticket | TKT-006, CLI-004 | PASS |
| C19 | reassign an assigned ticket | TKT-006 | PASS |
| C20 | assign a closed ticket | TKT-008, PR item 3 | FAILURE (new) |
| C21 | closed ticket stays closed after an assign attempt | tickets.md forward-only rule | FAILURE (new) |
| C22 | close again after assign-on-closed | TKT-011 | FAILURE (new) |
| C23 | empty or blank assignee | TKT-007 | PASS |
| C24 | assign an unknown ID | TKT-012 | PASS |
| C25 | assign with a non-integer ID | CLI-009 | PASS |
| C26 | `--help` description line | PR item 4 | FAILURE (new) |
| C27 | subcommand `--help` | shell contract | PASS |
| C28 | no subcommand | CLI-001 | PASS |
| C29 | unknown subcommand | CLI-001 | PASS |
| C30 | create, happy path | CLI-003, CLI-008 | PASS |
| C31 | create gets default priority P3 | CLI-003 | PASS |
| C32 | due time follows priority | TKT-005 | BLOCKED |
| C33 | create with an empty or blank title | TKT-002, CLI-007 | PASS |
| C34 | unknown priority: error content | TKT-003 | PASS |
| C34b | unknown priority: shell error, exit 2 | CLI-007 TODO | FAILURE (pre-existing) |
| C35 | IDs rise and are never reused | TKT-004, INV-003 | PASS |
| C36 | log path from `--log` | CLI-002 | PASS |
| C37 | log path from `TICKETDESK_LOG` | CLI-002 | PASS |
| C38 | default log `tickets.jsonl` in the current directory | CLI-002 | PASS |
| C39 | `--log` wins over `TICKETDESK_LOG` | CLI-002 | PASS |
| C40 | first create on a missing log is #1 and creates the file | LOG-006 | PASS |
| C41 | event kinds, fields, sorted keys, epoch `at` | LOG-002 to LOG-005, INV-005 | PASS |
| C42 | append leaves earlier lines unchanged | LOG-008, INV-002 | PASS |
| C43 | blank lines ignored on replay | LOG-005 | PASS |
| C44 | corrupt line: error content and fail-fast | LOG-007, INV-004 | PASS |
| C44b | corrupt line: shell error, exit 2 | CLI-007 TODO | FAILURE (pre-existing) |
| C45 | replay is deterministic | LOG-009 | PASS |
| C46 | Unicode title | edge | PASS |
| C47 | title that starts with a dash | edge | PASS |
| C48 | interrupted create leaves no partial event | shell contract | PASS |

## Non-PASS details

Paths below are relative to the repo root. `$TD` stands for
`python3 -m ticketdesk.cli --log ../logs/<case>.jsonl`.

### C01: list no longer shows the priority column (new)

- **Steps.** Create `'Printer on fire' --priority P1`, then `'VPN drops hourly'`, then run
  `$TD list`.
- **Expected.** Per CLI-006, each line is `#<id> [<priority>] <state> <title>`.
- **Observed on the branch.**

  ```text
  #1 open     Printer on fire
  #2 assigned VPN drops hourly
  #3 closed   Reset password
  ```

- **Observed on `main`.** `#1 [P1] open     Printer on fire`.
- **Most likely cause.** The list format string in `ticketdesk/cli.py` dropped
  `[{t.priority}]`. CLI-006 was not updated. The PR promises a flag "in a later PR". This
  branch has no flag, so no CLI command shows a ticket's priority.

### C07: `list | head` prints a BrokenPipeError and exits 120 (pre-existing)

- **Steps.** Create 1000 tickets with long titles (about 118 KB of list output). Run
  `$TD list | head -1`.
- **Expected.** One line on stdout, nothing on stderr.
- **Observed.** The first line, then this on stderr, and exit code 120:

  ```text
  Exception ignored while flushing sys.stdout:
  BrokenPipeError: [Errno 32] Broken pipe
  ```

- **On `main`.** The same output and exit code 120.
- **Most likely cause.** The CLI does not handle `SIGPIPE` or `BrokenPipeError` on stdout.

### C08: a 9-character resolution note is accepted (new)

- **Steps.** Create a ticket. Run `$TD close 1 duplicate`.
- **Expected.** Per TKT-010, a note under 10 characters fails with
  `resolution note must be at least 10 characters`.
- **Observed.** `#1 closed`, exit 0. `main` rejects the same command with exit 2.
- **Most likely cause.** The check in `TicketService.close` changed from `< 10` to `< 9`.
  The error message still says 10, and TKT-010 still says 10.
- **Conflict to decide.** The PR intends this change, but nobody updated TKT-010. The
  owner must choose one outcome. Option one: update TKT-010 and the message to 9. Option
  two: keep 10 and revert.

### C14: close keeps the assignee (BLOCKED)

- **Why blocked.** No command shows a ticket's assignee. The log shows the `assigned` and
  `closed` events, but derived state is not visible at any surface.
- **Unblocks it.** A command or list column that shows the assignee.

### C20, C21, C22: assigning a closed ticket reopens it (new)

These three cases fail from one defect, Issue 1 below.

- **Steps.**
  1. `$TD create 'Mail bounce'`
  2. `$TD close 2 'Mail server quota raised'`
  3. `$TD assign 2 dana`
  4. `$TD list`
  5. `$TD close 2 'Second resolution overwrites'`
- **Expected.** Step 3 fails with `error: ticket 2 is closed`, exit 2, and appends no
  event (TKT-008). The ticket stays `closed` (forward-only rule). Step 5 fails with
  `ticket 2 is already closed` (TKT-011).
- **Observed.** Step 3 prints `#2 assigned -> dana`, exits 0, and appends one line. Step 4
  shows `#2 assigned Mail bounce`. Step 5 prints `#2 closed` and exits 0. The log now
  holds two `closed` events for ticket 2 with different resolutions:

  ```text
  {"at": 1793297519.314811, "id": 2, "kind": "closed", "resolution": "Mail server quota raised"}
  {"assignee": "dana", "at": 1793297519.343078, "id": 2, "kind": "assigned"}
  {"at": 1793297519.436268, "id": 2, "kind": "closed", "resolution": "Second resolution overwrites"}
  ```

- **On `main`.** Step 3 prints `error: ticket 2 is closed` and exits 2.
- **Most likely cause.** The branch removed the closed-state check from
  `TicketService.assign`. The PR item "assigning works at any point in its life" conflicts
  with TKT-008 and with the forward-only rule in `tickets.md`. Neither was updated.

### C26: the new `--help` description has a typo (new)

- **Steps.** Run `python3 -m ticketdesk.cli --help`.
- **Expected.** A correctly spelled description line.
- **Observed.** `Manage support tikets from the shell.` The word should be "tickets".
- **Most likely cause.** A typo in the `description=` argument in `ticketdesk/cli.py`.

### C32: due time follows priority (BLOCKED)

- **Why blocked.** No command and no log field shows a due time. TKT-005 cannot be checked
  at any user surface.
- **Unblocks it.** A command or list column that shows the due time.

### C34b: an unknown priority escapes as a traceback (pre-existing)

- **Steps.** `$TD create 'Bad priority' --priority P9`. Also tried `--priority p1`.
- **Expected.** If CLI-007 covers it: `error: <message>` on stderr and exit 2.
- **Observed.** A Python traceback of about 15 lines and exit 1. The last line is
  `ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']`. No ticket was
  created, so C34 passes. Lowercase `p1` is rejected the same way.
- **On `main`.** The same traceback and exit 1.
- **Most likely cause.** The CLI catches only `TicketError`, and the priority check raises
  `ValueError`. The CLI-007 TODO already names this open conflict.

### C44b: a corrupt log line escapes as a traceback (pre-existing)

- **Steps.** Copy a valid log, append `{not json`, then append a valid event. Run
  `$TD list`, then `$TD create 'Should not append'`.
- **Expected.** If CLI-007 covers it: `error: <message>` on stderr and exit 2.
- **Observed.** A chained traceback of about 30 lines and exit 1. The last line is
  `ValueError: ../logs/corrupt.jsonl:6: corrupt event: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)`.
  The message names the path, the line, and `corrupt event`. Nothing printed to stdout,
  and the create appended nothing, so C44 passes.
- **On `main`.** The same traceback and exit 1.
- **Most likely cause.** The same as C34b. The CLI-007 TODO already names it.

## Missing or untested cases

- **The installed `ticketdesk` entry point.** Not tested. The task specified
  `python3 -m ticketdesk.cli`, and an install would write outside the run directory.
- **`make test` and `make lint`.** Not run. They test code, not the product surface. The
  PR's claim "all tests pass" was not checked.
- **Concurrent writers on one log.** Not tested. The change does not touch the store.
- **C14 and C32.** Blocked, see above.

## Issues found

1. **High, new. `assign` reopens a closed ticket.** Cases C20, C21, C22. A closed ticket
   becomes `assigned`, and a second `close` records a second resolution. This breaks
   TKT-008, the forward-only rule, and the intent of TKT-011. Support asked for the
   behavior, but the specs forbid it. The owner must decide before merge.
2. **Medium, new. `list` drops the priority column.** Case C01. This breaks CLI-006. No
   CLI command now shows priority, so a P1 outage looks the same as a P3 request. Any
   script that parses `list` output breaks.
3. **Medium, new. The resolution minimum is 9, but the spec and the message say 10.**
   Case C08. This breaks TKT-010. A user who sees "at least 10 characters" and types 9
   succeeds, so the message is now wrong.
4. **Low, new. Typo in `--help`.** Case C26. The text says "tikets".
5. **Low, pre-existing. Unknown priority and corrupt log print tracebacks with exit 1.**
   Cases C34b, C44b. The CLI-007 TODO tracks this.
6. **Low, pre-existing. `list | head` prints `BrokenPipeError` and exits 120.** Case C07.

## UX gaps

- **Ticket state is mostly invisible.** No command shows priority (after this branch),
  assignee, resolution, or due time. A user must read the raw JSON log to check their own
  work.
- **Subcommand help explains nothing.** `create --help` shows `--priority PRIORITY`
  without the allowed values P1, P2, P3. No argument has a description.
- **Ctrl-C can create a ticket silently.** In one interrupted run, the event was appended
  but the user saw only a `KeyboardInterrupt` traceback and no `#1007 open` line. A user
  who retries creates a duplicate ticket. The log stayed well-formed in every interrupted
  run.
- **Ctrl-C prints a raw traceback.** An interrupted run prints a `KeyboardInterrupt`
  traceback instead of a short message.

## Improvements worth doing

- **The PR changes behavior without updating the specs.** It contradicts TKT-008, TKT-010,
  and CLI-006. It cites no spec IDs, though `AGENTS.md` asks for both.
- **`PR.md` is committed to the repo root.** It is a PR description, not a product file.
- **The README does not show how to run the CLI.** The `python3 -m ticketdesk.cli` usage
  is only in `AGENTS.md`.

## Leftover artifacts

All artifacts stay in place for reproduction. No product file was modified. `git diff` in
`outputs/repo` is empty.

- `outputs/logs/*.jsonl`: one test log per case group. `assign.jsonl` reproduces Issue 1.
  `corrupt.jsonl` reproduces C44. `big.jsonl` holds 1007 tickets for C07 and C48.
- `outputs/logs/det1.txt`, `det2.txt`, `int.out`, `int.err`: captured output for C45 and
  C48.
- `outputs/repo/tickets.jsonl`: one ticket from C38, the default-path case.
- `outputs/repo/ticketdesk/__pycache__/`: bytecode that Python wrote when it ran the CLI.
- `outputs/main-copy/`: an extract of `main` for the regression check.
- `outputs/case-list.md` and `outputs/harness/`: the case list, the runner script, and
  the evidence log.

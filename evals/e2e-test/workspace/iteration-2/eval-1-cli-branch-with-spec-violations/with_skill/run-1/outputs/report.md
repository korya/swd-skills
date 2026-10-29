# E2e test report: feature/cli-tidy

**25/33 PASS, 8 FAILURE, 0 BLOCKED. Do not merge.** Three of the four PR changes break
their specs. The worst lets an agent reopen a closed ticket and overwrite its resolution.

- Scope is the branch `feature/cli-tidy` against `main`, as `PR.md` and the diff describe it.
  The cases cover the specs it touches (CLI, TKT) and the LOG and INV specs that every command reaches.
- The user is a support agent in a shell. The surface is `python3 -m ticketdesk.cli` from
  the repo root, with Python 3.15.2.
- The environment is local. Every log file is a throwaway file under `outputs/artifacts/`.
- Depth is comprehensive, because the request says "comprehensively" and "before it merges".

Six of the eight failures come from this branch. A snapshot of `main` passes the five
behavior cases among them, and has no help line to misspell. The other two failures are
tracebacks that exist on `main` too.

## Case table

| # | Case | Spec/ref | Status |
|---|---|---|---|
| 1 | `--help` shows the new description line, spelled correctly | PR, CLI-001 | FAILURE |
| 2 | Subcommand `--help` lists the right arguments | CLI-003 to CLI-006 | PASS |
| 3 | No subcommand, or an unknown one, prints usage to stderr, exit 2 | CLI-001 | PASS |
| 4 | Create with default priority on a missing log | CLI-003, TKT-001, TKT-004, LOG-006 | PASS |
| 5 | Create with `--priority P1` and `P2` | CLI-003, TKT-003 | PASS |
| 6 | Create with an empty or whitespace-only title | TKT-002 | PASS |
| 7 | Create with priority `P9` or `p1` | TKT-003, CLI-007 | FAILURE |
| 8 | `list` line format `#<id> [<priority>] <state> <title>` | CLI-006 | FAILURE |
| 9 | `list` sorts by ID and includes closed tickets | TKT-013 | PASS |
| 10 | `list` on a missing log prints nothing and creates no file | LOG-006, LOG-001 | PASS |
| 11 | Assign an open ticket | TKT-006, CLI-004 | PASS |
| 12 | Reassign an assigned ticket | TKT-006 | PASS |
| 13 | Assign with an empty or whitespace-only assignee | TKT-007 | PASS |
| 14 | Assign a closed ticket | TKT-008 | FAILURE |
| 15 | A closed ticket never reopens | tickets.md forward-only rule, TKT-011 | FAILURE |
| 16 | Close with a 10-character note | TKT-009, TKT-010, CLI-005 | PASS |
| 17 | Close with the 9-character note `duplicate` | TKT-010 | FAILURE |
| 18 | Close with a padded note that trims to 9 characters | TKT-010 | FAILURE |
| 19 | Close with an 8-character note | TKT-010 | PASS |
| 20 | Close a closed ticket | TKT-011 | PASS |
| 21 | Assign or close an unknown ID | TKT-012 | PASS |
| 22 | Non-integer ID for assign or close | CLI-009 | PASS |
| 23 | Rule errors go to stderr only, exit 2 | CLI-007 | PASS |
| 24 | Success writes nothing to stderr, exit 0 | CLI-008 | PASS |
| 25 | Log path from `--log`, then `TICKETDESK_LOG`, then `./tickets.jsonl` | CLI-002 | PASS |
| 26 | IDs rise by one and closing frees no ID | TKT-004, INV-003 | PASS |
| 27 | Log lines are sorted-key JSON with the right fields per kind | LOG-002 to LOG-005, INV-005 | PASS |
| 28 | An append leaves every earlier byte unchanged | LOG-008, INV-002 | PASS |
| 29 | Blank lines in the log are ignored | LOG-005 | PASS |
| 30 | A corrupt line stops every command with a clear error | LOG-007, INV-004, CLI-007 | FAILURE |
| 31 | Two replays of one log give the same list | LOG-009 | PASS |
| 32 | `list` into `head` closes cleanly | shell contract | PASS |
| 33 | Unicode, quotes, and a 300-character title round-trip | CLI-003 | PASS |

## Non-PASS details

### Case 14: a closed ticket accepts a new assignee

**Steps.**

```bash
L=/tmp/e2e-14.jsonl; rm -f $L
python3 -m ticketdesk.cli --log $L create "Printer on fire"
python3 -m ticketdesk.cli --log $L close 1 "Toner done"
python3 -m ticketdesk.cli --log $L assign 1 sam; echo "exit=$?"
```

**Expected.** TKT-008 requires `error: ticket 1 is closed` on stderr, exit 2, and no new event.

**Observed.** The command succeeds and appends an event.

```text
#1 assigned -> sam
exit=0
{"assignee": "sam", "at": 1793296709.410113, "id": 1, "kind": "assigned"}
```

On `main`, the same steps print `error: ticket 1 is closed` and exit 2.

**Most likely cause.** The diff deletes the closed-state check from `TicketService.assign` in
`ticketdesk/tickets.py`. The PR states this as intended ("assigning a ticket now works at any
point in its life"). That intent contradicts TKT-008 and nobody updated the spec.

### Case 15: the reassigned ticket reopens, and its resolution is overwritten

**Steps.** Continue from case 14, then close the ticket again.

```bash
python3 -m ticketdesk.cli --log $L list
python3 -m ticketdesk.cli --log $L close 1 "Closing it a second time"; echo "exit=$?"
grep '"id": 1' $L
```

**Expected.** The ticket stays `closed`, because tickets.md says nothing reopens a closed
ticket. A second close fails per TKT-011, and the first resolution stays.

**Observed.** `list` shows the ticket as `assigned`. The second close succeeds.

```text
#1 assigned Printer on fire
#1 closed
exit=0
{"at": 1793296701.3230011, "id": 1, "kind": "closed", "resolution": "Toner done"}
{"assignee": "sam", "at": 1793296709.410113, "id": 1, "kind": "assigned"}
{"at": 1793296709.4857311, "id": 1, "kind": "closed", "resolution": "Closing it a second time"}
```

The log now has two `closed` events for ticket 1. The replayed ticket carries the second
resolution, so the first resolution is lost from the ticket state.

**Most likely cause.** The same deleted check as in case 14. Assign sets the state to
`assigned` without regard to the current state, so the close guard for TKT-011 no longer
sees `closed`.

### Case 17: the note `duplicate` closes a ticket

**Steps.**

```bash
L=/tmp/e2e-17.jsonl; rm -f $L
python3 -m ticketdesk.cli --log $L create "VPN down" --priority P1
python3 -m ticketdesk.cli --log $L close 1 "duplicate"; echo "exit=$?"
```

**Expected.** TKT-010 rejects any note shorter than 10 characters after trimming. The
expected output is `error: resolution note must be at least 10 characters`, exit 2.

**Observed.**

```text
#1 closed
exit=0
```

On `main`, the same note is rejected with the error above and exit 2.

**Most likely cause.** The diff changes the check in `TicketService.close` from `< 10` to
`< 9`. The error text still says "at least 10 characters". The product now states one limit
and enforces another. This is wrong even under the PR's own intent.

### Case 18: a padded note that trims to 9 characters closes a ticket

**Steps.**

```bash
L=/tmp/e2e-18.jsonl; rm -f $L
python3 -m ticketdesk.cli --log $L create "Password reset" --priority P2
python3 -m ticketdesk.cli --log $L close 1 "  not a bug  "; echo "exit=$?"
```

**Expected.** `not a bug` has 9 characters after trimming, so TKT-010 rejects it.

**Observed.**

```text
#1 closed
exit=0
```

**Most likely cause.** The same threshold change as in case 17.

### Case 8: `list` drops the priority column

**Steps.**

```bash
L=/tmp/e2e-8.jsonl; rm -f $L
python3 -m ticketdesk.cli --log $L create "VPN down" --priority P1
python3 -m ticketdesk.cli --log $L list
```

**Expected.** CLI-006 requires the line format `#<id> [<priority>] <state> <title>`.

```text
#1 [P1] open     VPN down
```

**Observed.**

```text
#1 open     VPN down
```

`main` prints the expected line.

**Most likely cause.** The diff removes `[{t.priority}]` from the `list` format string in
`ticketdesk/cli.py`. The PR promises the column back "with a flag in a later PR". Until
then, no command shows the priority of a ticket. Scripts that parse `list` output also break.

### Case 1: the new help line misspells "tickets"

**Steps.** Run `python3 -m ticketdesk.cli --help`.

**Expected.** A correctly spelled description line.

**Observed.**

```text
Manage support tikets from the shell.
```

**Most likely cause.** A typo in the new `description=` argument in `ticketdesk/cli.py`.

### Case 7: an unknown priority escapes as a Python traceback

**Steps.**

```bash
python3 -m ticketdesk.cli --log /tmp/e2e-7.jsonl create "Bad prio" --priority P9; echo "exit=$?"
```

**Expected.** TKT-003 requires an error that names `P9` and the allowed values. CLI-007
requires the form `error: <message>` and exit 2 for rule errors.

**Observed.** A 15-line traceback on stderr ends in the line below, with exit 1. No ticket
is created. The lowercase `p1` gives the same result.

```text
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
```

**Most likely cause.** `sla.due_at` raises `ValueError`, and the CLI catches only
`TicketError`. This exists on `main` too. The TODO under CLI-007 records it as an open
decision. The branch did not cause it.

### Case 30: a corrupt log line escapes as a Python traceback

**Steps.**

```bash
L=/tmp/e2e-30.jsonl; rm -f $L
python3 -m ticketdesk.cli --log $L create "Before corruption"
echo '{"kind": "created", "id": 2, "title": "broken' >> $L
python3 -m ticketdesk.cli --log $L list; echo "exit=$?"
```

**Expected.** LOG-007 requires an error that names the file, the line, and `corrupt event`,
with no ticket state returned.

**Observed.** `list`, `create`, `assign`, and `close` all stop, and none appends an event. The
right message is present, but only as the last line of a 40-line traceback, with exit 1.

```text
ValueError: /tmp/e2e-30.jsonl:2: corrupt event: Unterminated string starting at: line 1 column 39 (char 38)
```

**Most likely cause.** `EventStore.replay` raises `ValueError`, and the CLI does not catch it.
This exists on `main` too and the TODO under CLI-007 records it. The branch did not cause it.

## Missing or untested cases

- **TKT-005, due time by priority.** No command shows a due time, so the shell user cannot
  observe it.
- **TKT-009, assignee kept on close.** No command shows the assignee of a closed ticket.
  The log shows only events, not the replayed state.
- **Interrupted runs.** Each command finishes in about 30 ms. A Ctrl-C has no window to land.
- **The installed `ticketdesk` entry point.** The task names `python3 -m ticketdesk.cli` as
  the surface, so I did not install the package.
- **A broken pipe on a large output.** The `list` of 1,500 tickets is about 40 KB. That
  probably fits the pipe buffer, so `head` may not have forced a real SIGPIPE.
- **Two agents writing one log at once.** No spec covers it, so it is out of scope.

## Issues found

1. **High. Assigning a closed ticket reopens it and lets a second close overwrite the
   resolution.** Cases 14 and 15. This breaks TKT-008, TKT-011 in effect, and the
   forward-only rule in tickets.md. `make test` also fails on it in
   `test_assign_requires_open_ticket`.
2. **Medium. The resolution note minimum is 9, but the error message and TKT-010 say 10.**
   Cases 17 and 18. The PR wants short notes such as `duplicate`. The fix is either a
   spec change with user confirmation or a revert. A one-off threshold of 9 is neither.
3. **Medium. `list` no longer shows priority, and no other command does.** Case 8. This
   breaks CLI-006. A P1 ticket and a P3 ticket now look the same to the agent.
4. **Low. The new help line misspells "tickets" as "tikets".** Case 1.
5. **Low, exists on `main`. An unknown priority and a corrupt log line end in a traceback
   with exit 1.** Cases 7 and 30. The open TODO under CLI-007 covers both.

## UX gaps

- **Subcommand help is bare.** No subcommand has a description. `create --help` does not
  list `P1`, `P2`, `P3`, or say that `P3` is the default.
- **The missing-subcommand error leaks an internal name.** It reads
  `the following arguments are required: cmd`. A user never sees the word `cmd` anywhere else.
- **Most ticket state is invisible.** The CLI never shows the assignee, the resolution, or
  the due time. After this branch, it also hides the priority.
- **The README does not say how to run the CLI.** Only AGENTS.md shows the
  `python3 -m ticketdesk.cli` form and the `--log` option.

## Improvements worth doing

- **The PR description says "All tests pass locally", but `make test` fails.** The run shows
  `FAILED (failures=1)` out of 7 tests. CI will likely fail on this branch.
- **The PR changes three specified behaviors without a spec change.** AGENTS.md says a change
  that contradicts a spec must stop for discussion. CLI-006, TKT-008, and TKT-010 each need
  that decision.
- **The log escapes non-ASCII text.** The title `Ünïcødé` is stored as `Ünïcødé`.
  The event-log spec says users read the file with any text tool, and this makes that harder.
- **The `at` field holds fractional seconds, such as `1793296683.055315`.** LOG-004 says
  "seconds since the Unix epoch" and does not say whether fractions are allowed.
- **The CLI has no tests.** AGENTS.md already lists this gap. Cases 1, 8, and 17 would each
  fail a simple CLI test.

## Leftover artifacts

Every file below came from the CLI or from the Python interpreter. `git status` shows no
tracked file changed in the repo.

| Path under `outputs/` | Contents |
|---|---|
| `artifacts/main.jsonl` | Tickets 1 to 6, including the reopened ticket 1 |
| `artifacts/before.jsonl` | A copy of `main.jsonl` from before ticket 4, for the LOG-008 byte check |
| `artifacts/blank.jsonl` | Tickets 1 and 2 with two blank lines between them |
| `artifacts/corrupt.jsonl` | Ticket 1 and a corrupt line 2 |
| `artifacts/env.jsonl`, `artifacts/flag.jsonl` | One ticket each, from the CLI-002 tests |
| `artifacts/pipe.jsonl` | 1,500 tickets named "Bulk ticket N" |
| `artifacts/main-src/`, `artifacts/main-baseline.jsonl` | A `git archive` snapshot of `main` and its test log |
| `artifacts/o`, `e`, `r.out`, `r.err`, `l1`, `l2`, `pipe.err` | Captured command output |
| `repo/tickets.jsonl` | Ticket 1 "Default path ticket", from the default-path test |
| `repo/ticketdesk/__pycache__/`, `repo/tests/__pycache__/` | Bytecode that Python wrote |
| `case-list.md` | The case list, written before execution |

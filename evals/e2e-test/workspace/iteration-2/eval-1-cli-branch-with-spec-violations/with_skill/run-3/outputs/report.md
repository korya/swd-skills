# E2e test report: feature/cli-tidy

**Verdict: 28/38 PASS, 9 FAILURE, 1 BLOCKED. Do not merge.** Three of the four PR changes
break the product specs. A closed ticket can now reopen and take a second resolution. A
9-character note now closes a ticket while the error text still demands 10. The `list`
output lost the priority column that CLI-006 requires.

The PR also states "All tests pass locally". On this branch `make test` fails 1 of 7 tests:
`test_assign_requires_open_ticket`.

## Scope, persona, and environment

- **Change.** Branch `feature/cli-tidy` against `main`, one commit `4659f59`. It edits
  `ticketdesk/cli.py` and `ticketdesk/tickets.py`, and adds `PR.md`.
- **Specs in scope.** All of `cli.md` (CLI) and `tickets.md` (TKT). The blast radius adds
  `event-log.md` (LOG) and INV-002, INV-003, and INV-004.
- **Persona.** A support agent at a shell.
- **Surface.** `python3 -m ticketdesk.cli` from the repo root, on Python 3.15.2, macOS.
- **Environment.** Local only. Every log file is a scratch file. No shared data was touched.
- **Depth.** Comprehensive. The request said "comprehensively" and "before it merges".
- **Baseline.** For the failures, I ran the same commands on an extract of `main`. Each
  failure below says whether it is a regression or pre-existing.

## Cases

In the repro steps, `td` stands for `python3 -m ticketdesk.cli`, run from the repo root.

| # | Case | Spec/ref | Status |
|---|---|---|---|
| R0 | Smoke: `--help` answers, exit 0 | readiness | PASS |
| C1 | `--help` shows the new description line, spelled correctly | PR | FAILURE |
| C2 | `list` line is `#<id> [<priority>] <state> <title>` | CLI-006 | FAILURE |
| C3 | `list` pads the state to 8 characters | CLI-006 | PASS |
| C4 | `list` on a missing log prints nothing, exits 0, creates no file | CLI-006, LOG-006 | PASS |
| C5 | `list` includes closed tickets in ID order | TKT-013 | PASS |
| C6 | Close with the 9-character note `duplicate` is rejected | TKT-010, PR | FAILURE |
| C7 | Close with an exactly 10-character note succeeds | TKT-010, CLI-005 | PASS |
| C8 | Close with an 8-character note is rejected, state unchanged | TKT-010, CLI-007 | PASS |
| C9 | Close with `  duplicate  ` (9 after trimming) is rejected | TKT-010 | FAILURE |
| C10 | Close with an empty or whitespace-only note is rejected | TKT-010 | PASS |
| C11 | Assign a closed ticket fails with `ticket <id> is closed` | TKT-008, PR | FAILURE |
| C12 | A closed ticket stays closed and keeps its resolution | tickets.md forward-only rule, TKT-011 | FAILURE |
| C13 | Assign an open ticket prints `#<id> assigned -> <name>` | CLI-004, TKT-006 | PASS |
| C14 | Reassign replaces the assignee | TKT-006 | PASS |
| C15 | Empty or whitespace assignee fails with `assignee is required` | TKT-007 | PASS |
| C16 | Assign or close an unknown ID fails with `no ticket <id>` | TKT-012 | PASS |
| C17 | Non-integer ID gives a usage error, exit 2, no event | CLI-009 | PASS |
| C18 | Create prints `#<id> open <title>`, default priority P3 | CLI-003, TKT-001 | PASS |
| C19 | `--priority P1` records P1 | TKT-003 | PASS |
| C20 | Empty or whitespace title fails with `title is required` | TKT-002 | PASS |
| C21 | Unknown priority `P9` or `p1` fails with a clean error | TKT-003, CLI-007 | FAILURE |
| C22 | A corrupt log line fails with a clean error | LOG-007, INV-004, CLI-007 | FAILURE |
| C23 | First create on a missing log gives ID 1 and creates the file | LOG-006, TKT-004 | PASS |
| C24 | IDs rise by one and are not reused after a close | TKT-004, INV-003 | PASS |
| C25 | Log path order is `--log`, then `TICKETDESK_LOG`, then `./tickets.jsonl` | CLI-002 | PASS |
| C26 | Events carry `kind`, `id`, `at`, the kind's fields, and sorted keys | LOG-002 to LOG-005, INV-005 | PASS |
| C27 | One event per change, and `list` appends nothing | LOG-001 | PASS |
| C28 | An append leaves the earlier bytes of the log unchanged | LOG-008, INV-002 | PASS |
| C29 | Blank lines in the log are ignored | LOG-005 | PASS |
| C30 | No subcommand or an unknown one prints usage to stderr, exit 2 | CLI-001 | PASS |
| C31 | Every successful command exits 0 with empty stderr | CLI-008 | PASS |
| C32 | Closing an assigned ticket keeps the assignee | TKT-009 | BLOCKED |
| C33 | A second close fails with `ticket <id> is already closed` | TKT-011 | PASS |
| C34 | Two `list` runs on the same log give identical output | LOG-009 | PASS |
| C35 | `list \| head -1` on a large log ends cleanly | shell contract | FAILURE |
| C36 | Subcommand `--help` output is accurate | shell contract | PASS |
| C37 | Titles with quotes and non-ASCII characters round-trip | CLI-003, CLI-006 | PASS |

## Non-PASS details

### C1: the help description has a typo (regression)

The new description line reads "tikets".

```text
$ td --help
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...

Manage support tikets from the shell.
```

- **Expected.** `Manage support tickets from the shell.`
- **Most likely cause.** A typo in the `description=` string that this branch adds to
  `argparse.ArgumentParser` in `ticketdesk/cli.py`.

### C2: `list` drops the priority column (regression)

CLI-006 requires `#<id> [<priority>] <state> <title>`. The branch prints the line without
`[<priority>]`.

```text
$ td --log t.jsonl create "Printer on fire"
$ td --log t.jsonl create "VPN down" --priority P1
$ td --log t.jsonl create "Mouse sticky" --priority P2
$ td --log t.jsonl list
#1 open     Printer on fire
#2 open     VPN down
#3 open     Mouse sticky
```

The same steps on `main` print `#1 [P3] open     Printer on fire`.

- **Impact.** No CLI command now shows a ticket's priority. A P1 ticket looks the same as a
  P3 ticket.
- **Most likely cause.** The branch removed `[{t.priority}]` from the `list` format string
  in `ticketdesk/cli.py`. The PR says the column "comes back with a flag in a later PR". The
  spec was not changed, so the branch ships a CLI-006 violation in the meantime.

### C6 and C9: a 9-character note closes a ticket (regression)

TKT-010 rejects notes shorter than 10 characters after trimming. The branch accepts 9.

```text
$ td --log t.jsonl create "Ticket 1"
$ td --log t.jsonl close 1 "duplicate"
#1 closed                                   (exit 0)
$ td --log t.jsonl create "Ticket 2"
$ td --log t.jsonl close 2 "  duplicate  "
#2 closed                                   (exit 0)
$ td --log t.jsonl create "Ticket 3"
$ td --log t.jsonl close 3 "8charsxx"
error: resolution note must be at least 10 characters      (exit 2)
```

On `main`, `close 1 "duplicate"` fails with the 10-character error and exit 2.

- **Contradiction in the product.** The error text still says "at least 10 characters". A
  user who reads it learns the wrong rule.
- **Most likely cause.** `ticketdesk/tickets.py` changed the check from `< 10` to `< 9`. The
  message and TKT-010 stayed at 10.
- **Process note.** The PR wants this change on purpose. AGENTS.md requires a spec conflict
  to be raised before the change. The spec and the error text must change together, or the
  code must go back to 10.

### C11 and C12: a closed ticket reopens and takes a second resolution (regression)

TKT-008 rejects any assignment of a closed ticket. The branch accepts it, and the ticket
moves back to `assigned`.

```text
$ td --log t.jsonl create "Laptop will not boot" --priority P1
#1 open Laptop will not boot
$ td --log t.jsonl assign 1 dana
#1 assigned -> dana
$ td --log t.jsonl close 1 "Replaced the SSD and reimaged"
#1 closed
$ td --log t.jsonl assign 1 sam
#1 assigned -> sam                          (exit 0, expected: error: ticket 1 is closed, exit 2)
$ td --log t.jsonl list
#1 assigned Laptop will not boot
$ td --log t.jsonl close 1 "Second resolution text"
#1 closed                                   (exit 0)
```

The log now holds two `closed` events for ticket 1:

```text
{"at": 1793296710.597172, "id": 1, "kind": "closed", "resolution": "Replaced the SSD and reimaged"}
{"assignee": "sam", "at": 1793296710.635631, "id": 1, "kind": "assigned"}
{"at": 1793296710.707018, "id": 1, "kind": "closed", "resolution": "Second resolution text"}
```

On `main`, `assign 1 sam` on the closed ticket fails with `error: ticket 1 is closed` and
exit 2.

- **Impact.** This breaks the rule in `tickets.md` that "nothing reopens a closed ticket".
  It also defeats TKT-011, because a reopen then lets a second close record a new
  resolution. A closed ticket is no longer final.
- **Most likely cause.** The branch removed the `if t.state == "closed"` guard from
  `TicketService.assign` in `ticketdesk/tickets.py`. The assigned event then sets the state
  back to `assigned` on replay.
- **Process note.** The PR says "support asked for" this. It needs a spec decision first.
  "Assign without reopening" and "reopen on assign" are different features, and the branch
  chose the second without saying so.

### C21: an unknown priority prints a Python traceback (pre-existing)

TKT-003 and CLI-007 expect `error: <message>` on stderr and exit 2. The CLI prints a
traceback and exits 1. No ticket is created, and the last line names the value and the
allowed values.

```text
$ td --log t.jsonl create "Bad prio" --priority P9
Traceback (most recent call last):
  ...
  File ".../ticketdesk/sla.py", line 8, in due_at
    raise ValueError(f"unknown priority {priority!r}; expected one of {sorted(SLA_HOURS)}")
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
(exit 1)
```

The lowercase `--priority p1` gives the same traceback. `main` behaves the same way.

- **Most likely cause.** `sla.due_at` raises `ValueError`, and `cli.py` catches only
  `TicketError`. The TODO under CLI-007 already records this conflict.

### C22: a corrupt log line prints a Python traceback (pre-existing)

LOG-007 expects an error with the path, the line number, and `corrupt event`. The final
line has all three, but it arrives inside a 34-line chained traceback with exit 1.

```text
$ td --log t.jsonl create "First"
$ td --log t.jsonl create "Second"
$ printf 'not json at all\n' >> t.jsonl
$ td --log t.jsonl list
Traceback (most recent call last):
  ...
ValueError: <log path>:3: corrupt event: Expecting value: line 1 column 1 (char 0)
(exit 1)
```

`create` and `assign` on the same log fail the same way. The log still has 3 lines, so no
event was appended, and no ticket state was printed.

- **Most likely cause.** `store.replay` raises `ValueError`, and `cli.py` catches only
  `TicketError`. The TODO under CLI-007 records this one too.

### C35: `list` piped into `head` prints a BrokenPipeError (pre-existing)

A user who pipes a long list into `head` sees a Python error on stderr. The CLI exits 120.

```text
$ td --log big.jsonl list | head -1
#1 open     Bulk 1
Exception ignored while flushing sys.stdout:
BrokenPipeError: [Errno 32] Broken pipe
(exit status of td: 120)
```

`big.jsonl` holds 3000 `created` events. I wrote that file by hand in the event format,
because 3000 `create` calls each replay the whole log. `main` behaves the same way.

- **Most likely cause.** The CLI does not handle `SIGPIPE` or `BrokenPipeError` on stdout.

### C32: no CLI command shows the assignee after a close (BLOCKED)

TKT-009 says a close keeps the assignee. No command prints the assignee of a closed ticket.
`close` prints `#<id> closed`, and `list` prints no assignee. The log shows that the
`closed` event carries no `assignee` field, but the kept assignee is replay state, and the
CLI never displays it.

- **Unblocks it.** A command or output line that shows a ticket's assignee.

## Missing or untested cases

- **TKT-005, the due time by priority.** No CLI output and no log field shows the due time.
  Nothing to observe at this surface.
- **The installed `ticketdesk` entry point.** The request set `python3 -m ticketdesk.cli`
  as the surface. A `pip install` would also write build files into the repo.
- **An interrupted run.** Every command finishes in under a second, so there is no run to
  interrupt.

## Issues found

Ordered by severity.

1. **High. Assigning a closed ticket reopens it, and it can then close again with a new
   resolution.** Regression of TKT-008. It breaks the forward-only rule and undoes TKT-011.
   Cases C11 and C12.
2. **High. A 9-character resolution note closes a ticket, but the error text says the
   minimum is 10.** Regression of TKT-010. Cases C6 and C9.
3. **Medium. `list` no longer shows the priority.** Regression of CLI-006. No other command
   shows it. Case C2.
4. **Medium. An unknown priority exits 1 with a traceback.** Pre-existing, see the TODO
   under CLI-007. Case C21.
5. **Medium. A corrupt log line exits 1 with a traceback.** Pre-existing, see the TODO
   under CLI-007. Case C22.
6. **Low. Piping `list` into `head` prints a BrokenPipeError and exits 120.** Pre-existing.
   Case C35.
7. **Low. The new help text says "tikets".** Regression. Case C1.

## UX gaps

- **The CLI shows almost nothing about a ticket.** After this branch, a user cannot see a
  ticket's priority, assignee, resolution, or due time without reading the JSON log.
- **The `list` columns misalign at ID 10.** `#9 open` and `#10 open` put the state in
  different columns, so the title column is ragged.
- **The missing-subcommand error names an internal field.** It says
  `the following arguments are required: cmd`. A user does not know what `cmd` is.
- **The help gives no rules.** `create --help` does not list the allowed priorities or the
  P3 default. `close --help` does not state the 10-character minimum. The top-level help
  lists the subcommands with no one-line description.
- **The README does not say how to run the CLI.** The commands are only in AGENTS.md.
- **The log escapes every non-ASCII character.** A title `Café` is stored as `Café`.
  The event-log spec says users read the file with any text tool, and escaped text is hard
  to read that way.

## Improvements worth doing

- **Correct the PR description.** It says "All tests pass locally". On this branch
  `make test` reports `FAILED (failures=1)` for `test_assign_requires_open_ticket`. That
  test guards TKT-008, and the branch removed the rule it tests.
- **Resolve the spec conflicts before the code.** The PR cites no spec IDs. AGENTS.md
  requires a change that contradicts a spec to stop and be discussed. TKT-008, TKT-010, and
  CLI-006 need a decision, and then the spec and the code change together.
- **Test the boundary of the resolution rule.** The unit test uses `done`, 4 characters, so
  it passes with a minimum of either 9 or 10.
- **Add CLI tests.** AGENTS.md lists the CLI as untested. Every regression in this report is
  visible at the CLI.
- **Add a `.gitignore`.** Each run leaves untracked `__pycache__` directories in the repo.

## Leftover artifacts

Every artifact is a scratch file. None is a product file. `git status` shows no tracked
file changed.

- **Repo root.** `outputs/repo/tickets.jsonl`, 1 event, from case C25 (the default log
  path).
- **Repo, created by Python.** `ticketdesk/__pycache__/` and `tests/__pycache__/`.
- **Scratch logs.** In `run-3/work/logs/`: `c18.jsonl`, `res.jsonl`, `res8.jsonl`,
  `assign.jsonl`, `create.jsonl`, `corrupt.jsonl`, `blank.jsonl`, `env.jsonl`, `flag.jsonl`,
  `unicode.jsonl`, `dash.jsonl`, `pipe.jsonl`, `baseline.jsonl`.
- **Seed and helpers.** In `run-3/work/`: `pipe-seed.jsonl` (the hand-written 3000-event
  log), `main-baseline/` (an extract of `main`), `case-list.txt`, `t.sh`, `c18.before`,
  `list1.txt`, `list2.txt`.

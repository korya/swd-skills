# E2e report: feature/cli-tidy

**41 cases: 30 PASS, 11 FAILURE, 0 BLOCKED. No-go.** The branch breaks three specified behaviors and adds a typo to `--help`.

The four regressions are these:

- A closed ticket can be assigned again, and the assignment reopens it (TKT-008).
- `list` no longer shows the priority (CLI-006).
- A 9-character resolution note now closes a ticket (TKT-010). The error text still says 10.
- The new `--help` line reads "tikets".

PR.md announces the first three as intended. The branch changes no spec, and the PR cites no spec ID. AGENTS.md requires a stop and user sign-off for any change that contradicts a spec. Either the code or the specs must change before merge. The decision belongs to the spec owner, not to this report.

The other five failures exist on `main` too. They are tracebacks on bad input, a broken pipe, and bare subcommand help. They do not block this branch.

## Scope, surface, environment

- **Scope.** Commit 4659f59 on `feature/cli-tidy` against `main` (8c5d958). The scope covers the four PR.md items, every spec they touch (CLI, TKT, LOG, INV), and the rest of `cli.py` and `tickets.py`.
- **User and surface.** A support agent in a shell. Every case runs `python3 -m ticketdesk.cli` from the repo root, as the task instructs.
- **Environment.** Local only. Each case uses its own fresh log file under the work directory. No shared or prod-like system was touched.
- **Depth.** Comprehensive, because the request says "comprehensively, before it merges".

The evidence log is `outputs/evidence.log` in the run directory. The case list, written before execution, is `outputs/case-list.md`. In the steps below, `W` is the run's work directory:

```
W=/Users/dmitri/dev/swd-skills-e2evidence/evals/e2e-test/workspace/iteration-4/eval-1-cli-branch-with-spec-violations/with_skill/run-2/work
```

Every quoted block below comes from the "REPRO RUNS" section at the end of the evidence log. Each repro ran on a fresh log with exactly the steps shown.

## Case table

| # | Case | Spec/ref | Status |
|---|------|----------|--------|
| 1 | Smoke: top-level `--help` | CLI-001 | PASS |
| 2 | `--help` description line | PR item 4 | FAILURE |
| 3 | No subcommand | CLI-001 | PASS |
| 4 | Unknown subcommand | CLI-001 | PASS |
| 5 | Create with default priority on a missing log | CLI-003, TKT-001, TKT-004, LOG-006 | PASS |
| 6 | Create with `--priority P1` and `P2` | CLI-003, TKT-003 | PASS |
| 7 | Create with an empty or whitespace title | TKT-002, CLI-007 | PASS |
| 8 | Create with unknown priority `P9` | TKT-003, CLI-007 TODO | FAILURE |
| 9 | Unicode title, title that starts with a dash | CLI-003 | PASS |
| 10 | List on a missing or empty log | CLI-006, LOG-006 | PASS |
| 11 | List line format | CLI-006, PR item 1 | FAILURE |
| 12 | List order, closed tickets included | TKT-013 | PASS |
| 13 | List in a pipe | shell contract | FAILURE |
| 14 | List appends nothing, replay is deterministic | LOG-001, LOG-009 | PASS |
| 15 | Assign an open ticket | CLI-004, TKT-006 | PASS |
| 16 | Reassign an assigned ticket | TKT-006 | PASS |
| 17 | Assign with an empty or whitespace assignee | TKT-007, CLI-007 | PASS |
| 18 | Assign a closed ticket | TKT-008, CLI-007, PR item 3 | FAILURE |
| 19 | A closed ticket stays closed | forward-only rule in tickets.md, TKT-011 | FAILURE |
| 20 | Assign an unknown ticket | TKT-012 | PASS |
| 21 | Non-integer ID for assign and close | CLI-009 | PASS |
| 22 | Close with a 10- and an 11-character note | CLI-005, TKT-009, TKT-010 | PASS |
| 23 | Close with the 9-character note "duplicate" | TKT-010, PR item 2 | FAILURE |
| 24 | Close with an 8- or 1-character note | TKT-010 | PASS |
| 25 | Trimmed note length decides | TKT-010 | FAILURE |
| 26 | Close an assigned ticket | TKT-009 | PASS |
| 27 | Close twice | TKT-011 | PASS |
| 28 | Close an unknown ticket | TKT-012 | PASS |
| 29 | Missing positional arguments | CLI-001 | PASS |
| 30 | IDs rise by one, not reused after close | TKT-004, INV-003 | PASS |
| 31 | Log path from `TICKETDESK_LOG` | CLI-002 | PASS |
| 32 | `--log` overrides `TICKETDESK_LOG` | CLI-002 | PASS |
| 33 | Default `tickets.jsonl` in the current directory | CLI-002 | PASS |
| 34 | Log line format and event fields | LOG-002 to LOG-005, INV-005 | PASS |
| 35 | Blank lines in the log are ignored | LOG-005 | PASS |
| 36 | Appending never rewrites existing lines | LOG-008, INV-002 | PASS |
| 37 | Corrupt log line | LOG-007, INV-004, CLI-007 TODO | FAILURE |
| 38 | Rejected commands append nothing | TKT-002, TKT-007, TKT-010, CLI-009 | PASS |
| 39 | Success writes nothing to stderr | CLI-008 | PASS |
| 40 | Log path in a directory that does not exist | unspecified error path | FAILURE |
| 41 | Subcommand `--help` describes the arguments | shell contract | FAILURE |

## Non-PASS details

### Cases 18 and 19: a closed ticket can be assigned, and the assignment reopens it

Regression. Severity High.

What was done:

```
python3 -m ticketdesk.cli --log $W/repro/r18.jsonl create 'Printer on fire'
python3 -m ticketdesk.cli --log $W/repro/r18.jsonl close 1 'Replaced the toner cartridge'
python3 -m ticketdesk.cli --log $W/repro/r18.jsonl assign 1 dana; echo "exit=$?"
python3 -m ticketdesk.cli --log $W/repro/r18.jsonl list
python3 -m ticketdesk.cli --log $W/repro/r18.jsonl close 1 'A different resolution'; echo "exit=$?"
cut -c1-200 $W/repro/r18.jsonl
```

Expected, per TKT-008 and CLI-007: `error: ticket 1 is closed` on stderr, exit 2, and no new event. The ticket stays `closed`. The tickets.md rule "Nothing reopens a closed ticket" holds, so a second close fails per TKT-011.

Observed:

```
#1 open Printer on fire
#1 closed
#1 assigned -> dana
exit=0
#1 assigned Printer on fire
#1 closed
exit=0
{"at": 1793302448.358848, "id": 1, "kind": "created", "priority": "P3", "title": "Printer on fire"}
{"at": 1793302448.3867, "id": 1, "kind": "closed", "resolution": "Replaced the toner cartridge"}
{"assignee": "dana", "at": 1793302448.41463, "id": 1, "kind": "assigned"}
{"at": 1793302448.471276, "id": 1, "kind": "closed", "resolution": "A different resolution"}
```

The assignment moves the ticket back to `assigned`. A second close then succeeds and records a second resolution. A support agent cannot tell from `list` that the ticket was ever closed. On `main` the same assign prints `error: ticket 1 is closed` and exits 2.

Most likely cause: the branch deletes the `closed` check from `TicketService.assign` in `ticketdesk/tickets.py`. Replay then applies the `assigned` event to a closed ticket and sets its state to `assigned`. PR item 3 says support asked for this. If that request stands, TKT-008 and the forward-only rule need a spec change with sign-off. The spec change must also say what state an assigned closed ticket ends in.

### Case 11: list drops the priority

Regression. Severity Medium.

What was done:

```
python3 -m ticketdesk.cli --log $W/repro/r11.jsonl create 'Printer on fire' --priority P1 && python3 -m ticketdesk.cli --log $W/repro/r11.jsonl list
```

Expected, per CLI-006: `#1 [P1] open     Printer on fire`.

Observed:

```
#1 open Printer on fire
#1 open     Printer on fire
```

The priority is now visible nowhere in the CLI. `create` does not echo it, and `list` no longer prints it. An agent cannot find the P1 tickets without reading the JSON log. A script that parses `[P1]` from `list` breaks. On `main` the same steps print `#1 [P1] open     Printer on fire`.

Most likely cause: the branch removes `[{t.priority}]` from the `list` format string in `ticketdesk/cli.py`. PR item 1 calls this intended and promises a flag in a later PR. CLI-006 was not changed.

### Cases 23 and 25: a 9-character resolution note closes the ticket

Regression. Severity Medium.

What was done:

```
python3 -m ticketdesk.cli --log $W/repro/r23.jsonl create 'Ticket A'
python3 -m ticketdesk.cli --log $W/repro/r23.jsonl create 'Ticket B'
python3 -m ticketdesk.cli --log $W/repro/r23.jsonl create 'Ticket C'
python3 -m ticketdesk.cli --log $W/repro/r23.jsonl close 1 'duplicate'; echo "exit=$?"
python3 -m ticketdesk.cli --log $W/repro/r23.jsonl close 2 '  Fixed it!  '; echo "exit=$?"
python3 -m ticketdesk.cli --log $W/repro/r23.jsonl close 3 'dup of 3'; echo "exit=$?"
```

Expected, per TKT-010: notes 1 and 2 have 9 characters after trimming, so both are rejected. Each prints `error: resolution note must be at least 10 characters` and exits 2.

Observed on stdout:

```
#1 open Ticket A
#2 open Ticket B
#3 open Ticket C
#1 closed
exit=0
#2 closed
exit=0
exit=2
```

Observed on stderr:

```
error: resolution note must be at least 10 characters
```

The 9-character notes close their tickets. The 8-character note is rejected with a message that still says 10. So the error now misstates the rule. Trimming still works, because `'  Fixed it!  '` counts as 9. On `main`, `close 2 'duplicate'` is rejected with the 10-character error.

Most likely cause: the branch changes the check in `TicketService.close` from `< 10` to `< 9`. The error string was not changed. The relaxation admits the PR's own example and little else. "duplicate" is exactly 9 characters, and any 8-character note still fails. TKT-010 was not changed.

### Case 2: the new --help line has a typo

Regression. Severity Low.

What was done:

```
python3 -m ticketdesk.cli --help | sed -n 3p
```

Expected: a correctly spelled description line.

Observed:

```
Manage support tikets from the shell.
```

Most likely cause: a typo in the new `description=` argument in `ticketdesk/cli.py`. "tikets" should read "tickets".

### Case 8: an unknown priority prints a Python traceback

Pre-existing on `main`. A known open question under CLI-007. Severity Low for this branch.

What was done:

```
python3 -m ticketdesk.cli --log $W/repro/r08.jsonl create 'Bad priority' --priority P9 2>$W/repro/r08.err; echo "exit=$?"
head -1 $W/repro/r08.err
tail -1 $W/repro/r08.err
ls $W/repro/r08.jsonl
```

Expected: one readable error line that names `P9` and the allowed values, per TKT-003. No ticket is created.

Observed:

```
exit=1
Traceback (most recent call last):
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
```

The `ls` reports that the log file does not exist, so no ticket was created. The message content satisfies TKT-003. The user still gets a 14-line traceback on stderr and exit code 1, where every other rule error gives `error: ...` and exit 2.

Most likely cause: `sla.due_at` raises `ValueError`, and `cli.py` catches only `TicketError`. The CLI-007 TODO already records this.

### Case 37: a corrupt log line prints a Python traceback

Pre-existing on `main`. A known open question under CLI-007. Severity Low for this branch.

What was done:

```
python3 -m ticketdesk.cli --log $W/repro/r37.jsonl create 'Good ticket'
echo '{not json' >> $W/repro/r37.jsonl
python3 -m ticketdesk.cli --log $W/repro/r37.jsonl list 2>$W/repro/r37.err; echo "exit=$?"
head -1 $W/repro/r37.err
tail -1 $W/repro/r37.err
```

Expected, per LOG-007: an error that names the path, the line number, and `corrupt event`, with no ticket state shown.

Observed:

```
#1 open Good ticket
exit=1
Traceback (most recent call last):
ValueError: /Users/dmitri/dev/swd-skills-e2evidence/evals/e2e-test/workspace/iteration-4/eval-1-cli-branch-with-spec-violations/with_skill/run-2/work/repro/r37.jsonl:2: corrupt event: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
```

The last line satisfies LOG-007 and INV-004, and `list` prints no tickets. A later `create` also refuses to append, see case 37 in the evidence log. The message arrives inside a 35-line traceback on stderr, with exit code 1.

Most likely cause: the store raises `ValueError`, and `cli.py` catches only `TicketError`.

### Case 40: a log path in a missing directory gives a traceback on create and silence on list

Pre-existing on `main`. Not specified. Severity Low.

What was done:

```
python3 -m ticketdesk.cli --log $W/repro/missing-dir/t.jsonl create 'Nowhere to go' 2>$W/repro/r40.err; echo "exit=$?"
head -1 $W/repro/r40.err
tail -1 $W/repro/r40.err
python3 -m ticketdesk.cli --log $W/repro/missing-dir/t.jsonl list; echo "list exit=$?"
```

Expected: a one-line error that names the missing directory.

Observed:

```
exit=1
Traceback (most recent call last):
FileNotFoundError: [Errno 2] No such file or directory: '/Users/dmitri/dev/swd-skills-e2evidence/evals/e2e-test/workspace/iteration-4/eval-1-cli-branch-with-spec-violations/with_skill/run-2/work/repro/missing-dir/t.jsonl'
list exit=0
```

`create` fails with a traceback. `list` on the same path prints nothing and exits 0, as LOG-006 allows. A mistyped `--log` path therefore shows an empty help desk without a warning.

Most likely cause: `store.append` opens the file without creating its directory, and `cli.py` does not catch `OSError`.

### Case 13: list into a closed pipe prints a traceback and exits 120

Pre-existing on `main`. Severity Low.

What was done:

```
python3 -c 'import json
for i in range(1, 40001): print(json.dumps({"at": 1793300000.0, "id": i, "kind": "created", "priority": "P3", "title": "Bulk ticket %d" % i}, sort_keys=True))' > $W/repro/r13.jsonl
python3 -m ticketdesk.cli --log $W/repro/r13.jsonl list 2>$W/repro/r13.err | head -1; echo "exit=${PIPESTATUS[0]}"
tail -2 $W/repro/r13.err
```

The script writes a 40,000-ticket log in the documented line format. A small log does not trigger the failure, because its output fits in the pipe buffer.

Expected: the first line, then a quiet exit.

Observed:

```
#1 open     Bulk ticket 1
exit=120
Exception ignored while flushing sys.stdout:
BrokenPipeError: [Errno 32] Broken pipe
```

The full stderr also holds a `BrokenPipeError` traceback from the `print` call in `cli.py`.

Most likely cause: the CLI does not handle `SIGPIPE` or `BrokenPipeError`.

### Case 41: subcommand help does not describe any argument

Pre-existing on `main`. Severity Low.

What was done:

```
python3 -m ticketdesk.cli create --help
```

Expected: each argument described. The `--priority` line names `P1`, `P2`, `P3` and the default `P3`.

Observed:

```
usage: ticketdesk create [-h] [--priority PRIORITY] title

positional arguments:
  title

options:
  -h, --help           show this help message and exit
  --priority PRIORITY
```

`assign --help`, `close --help`, and the top-level subcommand list are equally bare, see case 41 in the evidence log. Nothing in the help mentions the 10-character note rule.

Most likely cause: the `add_parser` and `add_argument` calls in `cli.py` pass no `help=` text.

## Missing or untested cases

- **Installed `ticketdesk` entry point.** Not run. The task fixes the surface as `python3 -m ticketdesk.cli`. A `pip install` run would test the `[project.scripts]` wiring.
- **TKT-005, due time by priority.** Not testable at this surface. No command prints a due time.
- **TKT-009, assignee kept after close.** Not testable at this surface. No command prints the assignee after close. The log shows no event that clears it.
- **Interrupted run.** Not run. Each command finishes in about 50 ms, so a shell user cannot interrupt one mid-append.
- **Concurrent writers.** Out of scope. No spec covers it.
- **Python 3.11 and 3.12.** Not run. Every case ran on Python 3.15.2. CI uses 3.12.

Case 33 has one deviation. It ran from a scratch directory with `PYTHONPATH` set to the repo root. A run from the repo root would have written `tickets.jsonl` into the product tree.

## Issues found

1. **High. A closed ticket can be assigned, which reopens it, and it can then be closed again with a new resolution.** Breaks TKT-008, the forward-only rule, and in effect TKT-011. Regression. Cases 18, 19.
2. **Medium. `list` omits the priority, so the CLI shows the priority nowhere.** Breaks CLI-006. Regression. Case 11.
3. **Medium. A 9-character resolution note closes a ticket, while the error still says "at least 10".** Breaks TKT-010. Regression. Cases 23, 25.
4. **Medium, process. Three spec-breaking behavior changes ship without a spec change, a spec ID, or recorded sign-off.** AGENTS.md and docs/README.md require all three. Covers issues 1 to 3.
5. **Low. The new `--help` description reads "tikets".** Regression. Case 2.
6. **Low. Unknown priority and corrupt log line escape as tracebacks with exit 1.** Pre-existing. Known under the CLI-007 TODO. Cases 8, 37.
7. **Low. A missing log directory gives a traceback on `create` and silence on `list`.** Pre-existing. Case 40.
8. **Low. `list` into a closed pipe prints a `BrokenPipeError` traceback and exits 120.** Pre-existing. Case 13.
9. **Low. Subcommand help describes no argument.** Pre-existing. Case 41.

## UX gaps

- The no-subcommand error says `the following arguments are required: cmd`. "cmd" is an internal name. A user expects "command".
- No command shows a ticket's assignee, resolution, or due time. The JSON log is the only place to see them.
- A resolution note is stored with its surrounding spaces. `close 5 '     duplicate     '` records `"resolution": "     duplicate     "`. The length check trims, but the stored value does not.
- Without `--log`, each working directory gets its own `tickets.jsonl`. An agent who changes directory sees an empty desk and gets no warning.

## Improvements worth doing

- Add subprocess tests for the CLI that cite spec IDs. AGENTS.md lists the CLI as untested. PR.md says "All tests pass locally" while three specs break, so the suite cannot see these regressions.
- Put the run commands in README.md. They are only in AGENTS.md today.
- State in LOG-004 whether `at` is an integer or a float. The log holds fractional seconds, such as `1793302448.358848`.

## Leftover artifacts

Every artifact is in the run's work directory `W`. The product tree is unchanged. `git status --porcelain` printed nothing at the end of the run.

- Log files from the cases: `base.jsonl`, `c05.jsonl`, `c07.jsonl`, `c08.jsonl`, `c09.jsonl`, `c10-empty.jsonl`, `c11.jsonl`, `c13-big.jsonl`, `c13-huge.jsonl`, `c15.jsonl`, `c18.jsonl`, `c19-open-closed.jsonl`, `c22b.jsonl`, `c26.jsonl`, `c31-env.jsonl`, `c32-opt.jsonl`, `c33-cwd/tickets.jsonl`, `c35.jsonl`, `c36.jsonl`, `c36-before.jsonl`, `c37.jsonl`.
- List snapshots for case 14: `c14-a.txt`, `c14-b.txt`.
- Repro logs and stderr captures in `repro/`: `r08.err`, `r11.jsonl`, `r13.jsonl`, `r13.err`, `r18.jsonl`, `r23.jsonl`, `r37.jsonl`, `r37.err`, `r40.err`.
- `main-baseline/`: an export of `main` by `git archive`. It served only to label failures as regressions or pre-existing. No verdict comes from it.
- `ev.sh`: the harness that wrote the evidence log.

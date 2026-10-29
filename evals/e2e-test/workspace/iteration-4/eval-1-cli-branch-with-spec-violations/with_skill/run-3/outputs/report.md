# E2e report: feature/cli-tidy

**28/40 PASS, 11 FAILURE, 1 BLOCKED. No-go: the branch breaks three specs, and an `assign` on a closed ticket reopens it.**

The branch introduces seven of the failures. They map to four issues:

- `assign` on a closed ticket succeeds and reopens the ticket. It can then close again with a second resolution. This breaks TKT-008 and the "moves forward only" rule.
- `list` no longer shows the priority. This breaks CLI-006. No other command shows the priority.
- `close` accepts a 9-character note. TKT-010 and the error message still say 10.
- `--help` prints "tikets".

The other four failures also occur on `main`. Three are Python tracebacks where the user expects a one-line error. One is a broken-pipe warning.

PR.md promises three of these changes. Each one contradicts a spec, and the PR neither updates the spec nor cites its ID. AGENTS.md requires the author to stop and discuss such a conflict. The specs or the PR must change before merge.

## Scope, surface, environment

- **Scope.** The diff of `feature/cli-tidy` (4659f59) against `main` (8c5d958), the promises in PR.md, and every criterion of `cli.md` and `tickets.md`. The blast radius adds `event-log.md`, INV-002 to INV-004, and the shell contract.
- **Persona and surface.** A support agent at a shell. The task fixes the surface as `python3 -m ticketdesk.cli`, run from the repo root.
- **Environment.** Local. Every test used a throwaway log file under `outputs/work/`.
- **Depth.** Comprehensive. The ask says "end to end", "comprehensively", and "before it merges".
- **Baseline.** Case 40 ran the failing cases against an export of `main`. It separates new failures from old ones.

Evidence log, with every command and its verbatim output:
`/Users/dmitri/dev/swd-skills-e2evidence/evals/e2e-test/workspace/iteration-4/eval-1-cli-branch-with-spec-violations/with_skill/run-3/outputs/evidence-log.md`

Case list, written before execution:
`/Users/dmitri/dev/swd-skills-e2evidence/evals/e2e-test/workspace/iteration-4/eval-1-cli-branch-with-spec-violations/with_skill/run-3/outputs/case-list.md`

Unless a block says otherwise, the commands ran with the repo root as the working directory. The log paths are relative to it.

## Case table

| # | Case | Spec/ref | Status | New on branch |
|---|------|----------|--------|---------------|
| 1 | `list` with P1, P2, P3 tickets | CLI-006, PR item 1 | FAILURE | yes |
| 2 | `list` on a missing log | CLI-006, LOG-006 | PASS | |
| 3 | `list` order, closed tickets included | TKT-013 | PASS | |
| 4 | `list` pads the state to 8 characters | CLI-006 | PASS | |
| 5 | `close` with a 10-character note | TKT-010, CLI-005 | PASS | |
| 6 | `close` with `duplicate` (9 characters) | TKT-010, PR item 2 | FAILURE | yes |
| 7 | `close` with an 8-character note | TKT-010 | FAILURE | yes |
| 8 | `close` with a note of 9 characters after trimming | TKT-010 | FAILURE | yes |
| 9 | rejected `close` leaves ticket and log unchanged | TKT-010, CLI-007 | PASS | |
| 10 | `assign` a closed ticket | TKT-008, PR item 3 | FAILURE | yes |
| 11 | state after `assign` on a closed ticket, then a second `close` | tickets.md "moves forward only", TKT-011 | FAILURE | yes |
| 12 | `assign` an open ticket | TKT-006, CLI-004 | PASS | |
| 13 | reassign an assigned ticket | TKT-006 | PASS | |
| 14 | empty or whitespace assignee | TKT-007, CLI-007 | PASS | |
| 15 | `assign` or `close` an unknown ID | TKT-012, CLI-007 | PASS | |
| 16 | `--help` shows the new description | PR item 4, CLI-001 | FAILURE | yes |
| 17 | `--help` for each subcommand | shell contract | PASS | |
| 18 | no subcommand, unknown subcommand | CLI-001 | PASS | |
| 19 | log path: `--log`, then `TICKETDESK_LOG`, then `./tickets.jsonl` | CLI-002 | PASS | |
| 20 | `create` output and default priority P3 | CLI-003, TKT-001 | PASS | |
| 21 | `create --priority P1` | CLI-003, TKT-003 | PASS | |
| 22 | empty or whitespace title | TKT-002, CLI-007 | PASS | |
| 23 | `create --priority P9` | TKT-003, CLI-007 TODO | FAILURE | no |
| 24 | IDs rise by one and are not reused | TKT-004, INV-003 | PASS | |
| 25 | due time by priority | TKT-005 | BLOCKED | |
| 26 | `close` an open and an assigned ticket | TKT-009 | PASS | |
| 27 | close twice | TKT-011 | PASS | |
| 28 | success writes nothing to stderr, exit 0 | CLI-008 | PASS | |
| 29 | non-integer ID for `assign` and `close` | CLI-009 | PASS | |
| 30 | one event per change, none for `list` | LOG-001 | PASS | |
| 31 | event kinds, fields, timestamp | LOG-002, LOG-003, LOG-004 | PASS | |
| 32 | sorted keys, blank lines ignored | LOG-005 | PASS | |
| 33 | a corrupt line stops every operation | LOG-007, INV-004, CLI-007 TODO | FAILURE | no |
| 34 | appending never rewrites existing lines | LOG-008, INV-002 | PASS | |
| 35 | replay is deterministic | LOG-009 | PASS | |
| 36 | `list` piped into `head -1` | shell contract | FAILURE | no |
| 37 | missing positional arguments | shell contract | PASS | |
| 38 | `--log` in a directory that does not exist | shell contract | FAILURE | no |
| 39 | non-ASCII title round-trip | edge | PASS | |
| 40 | baseline of the failing cases on `main` | regression check | PASS | |

## Non-PASS details

### Case 1: `list` drops the priority column (FAILURE)

**Steps.**

```
python3 -m ticketdesk.cli --log ../work/c01.jsonl create 'Printer on fire' --priority P1 && python3 -m ticketdesk.cli --log ../work/c01.jsonl create 'VPN drops hourly' --priority P2 && python3 -m ticketdesk.cli --log ../work/c01.jsonl create 'Update wiki' --priority P3 && python3 -m ticketdesk.cli --log ../work/c01.jsonl list
```

**Expected.** CLI-006 requires each line to be `#<id> [<priority>] <state> <title>`, for example `#1 [P1] open     Printer on fire`.

**Observed.** Exit 0. The output shows the three `create` lines, then `list` lines with no priority:

```
#1 open Printer on fire
#2 open VPN drops hourly
#3 open Update wiki
#1 open     Printer on fire
#2 open     VPN drops hourly
#3 open     Update wiki
```

On `main`, the `list` line for a P1 ticket is `#1 [P1] open     Printer on fire` (evidence log, case 40-1).

**Most likely cause.** The diff removes `[{t.priority}] ` from the `list` format string in `ticketdesk/cli.py`. PR.md says the flag to restore the column comes "in a later PR". Until then, no command shows the priority. The P1 ticket in this run looks the same as the P3 ticket.

### Cases 6, 7, 8: the resolution minimum is 9, but the spec and the error say 10 (FAILURE)

**Steps, case 6.**

```
python3 -m ticketdesk.cli --log ../work/c06.jsonl create 'Same as #4' && python3 -m ticketdesk.cli --log ../work/c06.jsonl close 1 duplicate; echo exit=$?; python3 -m ticketdesk.cli --log ../work/c06.jsonl list
```

**Expected.** TKT-010 requires rejection of any note shorter than 10 characters after trimming. The output must be `error: resolution note must be at least 10 characters`, with exit 2 and the ticket still open.

**Observed.** The 9-character note closes the ticket:

```
#1 open Same as #4
#1 closed
exit=0
#1 closed   Same as #4
```

Case 8 shows the same result for `'   duplicate   '`, which trims to 9 characters. Case 9's first run accepted `'too short'`, also 9 characters. On `main`, `close 1 duplicate` prints the TKT-010 error with exit 2 (case 40-6).

**Steps, case 7.**

```
python3 -m ticketdesk.cli --log ../work/c07.jsonl create 'Noise ticket' && python3 -m ticketdesk.cli --log ../work/c07.jsonl close 1 'not repr'; echo exit=$?; python3 -m ticketdesk.cli --log ../work/c07.jsonl list
```

**Observed.** The CLI rejects the 8-character note with exit 2. The error names a limit that the product does not enforce. stderr:

```
error: resolution note must be at least 10 characters
```

A user who reads this message and shortens a note to 9 characters finds that it works. The message and the behavior disagree.

**Most likely cause.** The diff changes the check in `ticketdesk/tickets.py` from `< 10` to `< 9` and leaves the message unchanged. PR.md asks for this change. TKT-010 still says 10, and the PR does not mention it.

### Cases 10 and 11: `assign` reopens a closed ticket (FAILURE)

**Steps, case 11.**

```
python3 -m ticketdesk.cli --log ../work/c11.jsonl create 'Printer on fire' --priority P1 && python3 -m ticketdesk.cli --log ../work/c11.jsonl close 1 'Replaced the toner cartridge' && python3 -m ticketdesk.cli --log ../work/c11.jsonl assign 1 dana && python3 -m ticketdesk.cli --log ../work/c11.jsonl list && python3 -m ticketdesk.cli --log ../work/c11.jsonl close 1 'Second, different resolution'; echo exit=$?; python3 -m ticketdesk.cli --log ../work/c11.jsonl list; cat ../work/c11.jsonl
```

**Expected.**

- TKT-008: `assign 1 dana` fails with `error: ticket 1 is closed` and exit 2. The ticket is unchanged.
- tickets.md: "Nothing reopens a closed ticket."
- TKT-011: a second `close` fails, and the recorded resolution is unchanged.

**Observed.** The assignment succeeds. `list` shows the closed ticket as `assigned`. The second `close` then succeeds:

```
#1 open Printer on fire
#1 closed
#1 assigned -> dana
#1 assigned Printer on fire
#1 closed
exit=0
#1 closed   Printer on fire
{"at": 1793302322.3986828, "id": 1, "kind": "created", "priority": "P1", "title": "Printer on fire"}
{"at": 1793302322.436595, "id": 1, "kind": "closed", "resolution": "Replaced the toner cartridge"}
{"assignee": "dana", "at": 1793302322.468566, "id": 1, "kind": "assigned"}
{"at": 1793302322.536575, "id": 1, "kind": "closed", "resolution": "Second, different resolution"}
```

The log now holds two `closed` events with different resolutions for one ticket. The CLI shows no resolution, so this run could not see which one the product reports. Case 10 shows the event count rise from 2 to 3 on the assignment. On `main`, the same assignment prints `error: ticket 1 is closed` with exit 2 (case 40-10).

**Most likely cause.** The diff deletes the `closed` check at the start of `TicketService.assign` in `ticketdesk/tickets.py`. The replay then applies the `assigned` event to a closed ticket, and the state goes back to `assigned`. That state lets the TKT-011 guard in `close` pass. PR.md calls the change "assigning a ticket now works at any point in its life". TKT-008 and the forward-only rule still forbid it.

### Case 16: typo in the new `--help` description (FAILURE)

**Steps.**

```
python3 -m ticketdesk.cli --help
```

**Expected.** A correct description line.

**Observed.** Exit 0. The description line has a misspelling:

```
Manage support tikets from the shell.
```

**Most likely cause.** The `description=` string that the diff adds to `ticketdesk/cli.py`.

### Case 23: an unknown priority prints a traceback (FAILURE, also on `main`)

**Steps.**

```
python3 -m ticketdesk.cli --log ../work/r23.jsonl create 'Bad priority' --priority P9 2>&1 | tail -1; echo pipestatus=${PIPESTATUS[*]}; python3 -m ticketdesk.cli --log ../work/r23.jsonl create 'Bad priority' --priority P9 2>&1 | wc -l; ls ../work/r23.jsonl
```

**Expected.** One line on stderr, such as `error: ...`, that names `P9` and `P1`, `P2`, `P3`. Exit 2, the same as every other rejected input. No ticket.

**Observed.** The text names the right values, and no log file appears. But the user gets a traceback of 14 lines and exit 1:

```
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
pipestatus=1 0
14
```

**Most likely cause.** `sla.due_at` raises `ValueError`, which the CLI does not catch. The CLI-007 TODO records this conflict and asks the user to decide. The behavior is the same on `main` (case 40-23).

### Case 25: due time has no surface (BLOCKED)

TKT-005 defines a due time per priority. No command prints it, and the `created` event does not store it. The case cannot run through the CLI. A command or `list` column that shows the due time unblocks it.

### Case 33: a corrupt log line prints a traceback (FAILURE, also on `main`)

**Steps.**

```
python3 -m ticketdesk.cli --log ../work/r33.jsonl create 'Before corruption' && echo '{not json' >> ../work/r33.jsonl && python3 -m ticketdesk.cli --log ../work/r33.jsonl list 2>&1 | tail -1; echo pipestatus=${PIPESTATUS[*]}
```

**Expected.** LOG-007 and INV-004 require an error that names the path, the line number, and `corrupt event`. For a shell user, that is one line on stderr.

**Observed.** The last line meets LOG-007. But it is the end of a long traceback, with exit 1:

```
#1 open Before corruption
ValueError: ../work/r33.jsonl:2: corrupt event: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
pipestatus=1 0
```

Case 33 shows the same traceback for `create`, `list`, and `assign`. No event was appended. The CLI returned no partial state.

**Most likely cause.** `store.replay` raises `ValueError`, which the CLI does not catch. The CLI-007 TODO records this conflict. The behavior is the same on `main` (case 40-33).

### Case 36: `list` in a pipe prints a broken-pipe warning (FAILURE, also on `main`)

**Steps.**

```
L=../work/c36.jsonl; for i in $(seq 1 3000); do printf '{"at": 1.0, "id": %d, "kind": "created", "priority": "P3", "title": "Bulk %d"}\n' $i $i; done > $L; python3 -m ticketdesk.cli --log $L list | head -1; echo pipestatus=${PIPESTATUS[*]}
```

The loop writes a log of 3000 `created` events directly, because 3000 `create` calls take too long. The test then reads the log through `list`.

**Expected.** One line on stdout, nothing on stderr.

**Observed.** The right first line, then a Python warning on stderr and exit 120. stdout:

```
#1 open     Bulk 1
pipestatus=120 0
```

stderr:

```
Exception ignored while flushing sys.stdout:
BrokenPipeError: [Errno 32] Broken pipe
```

**Most likely cause.** The CLI does not handle `SIGPIPE` or `BrokenPipeError`. The behavior is the same on `main` (case 40-36).

### Case 38: a missing log directory prints a traceback (FAILURE, also on `main`)

**Steps.**

```
python3 -m ticketdesk.cli --log ../work/no/such/dir/t.jsonl create 'Nowhere to write' 2>&1 | tail -1; echo pipestatus=${PIPESTATUS[*]}
```

**Expected.** A one-line error that names the path, and a non-zero exit.

**Observed.** A traceback with exit 1. Its last line:

```
FileNotFoundError: [Errno 2] No such file or directory: '../work/no/such/dir/t.jsonl'
pipestatus=1 0
```

`list` on the same path prints nothing and exits 0, which LOG-006 allows.

**Most likely cause.** `store.append` opens the file and does not check for the parent directory. The CLI does not catch `OSError`. The behavior is the same on `main` (case 40-38).

## Missing or untested cases

- **The installed `ticketdesk` entry point.** The task fixes the surface as `python3 -m ticketdesk.cli`. This run did not install the package.
- **Interrupted runs.** Each command finishes in about 30 ms. No interrupt test was meaningful.
- **TKT-009, "the assignee is kept" on close.** No command shows the assignee after close.
- **Which resolution wins after a second close (case 11).** No command shows the resolution.
- **Default log path from the repo root (case 19).** The test ran in `outputs/work/c19/` with `PYTHONPATH` set to the repo. This kept `tickets.jsonl` out of the repo.
- **PR.md's "All tests pass locally".** `make test` is not the user surface. This run did not verify the claim.
- **Two agents that write to one log at the same time.** No spec covers it. Out of scope.

## Issues found

1. **High. `assign` reopens a closed ticket, and a second `close` then records a second resolution.** New on the branch. Cases 10 and 11. It breaks TKT-008 and the forward-only rule, and it gets around TKT-011. The log keeps both resolutions, so INV-002 holds (case 34). But the derived state no longer matches the lifecycle that the specs promise.
2. **High. `list` no longer shows the priority.** New on the branch. Case 1. It breaks CLI-006. A P1 ticket and a P3 ticket look the same, and scripts that parse `[P1]` break.
3. **Medium. `close` accepts 9-character notes, but the error still says 10.** New on the branch. Cases 6, 7, 8. It breaks TKT-010, and the error now misleads the user.
4. **Medium. An unknown priority and a corrupt log line print tracebacks with exit 1.** Also on `main`. Cases 23 and 33. The CLI-007 TODO records this open conflict.
5. **Low. The `--help` description says "tikets".** New on the branch. Case 16.
6. **Low. A missing log directory prints a traceback.** Also on `main`. Case 38.
7. **Low. `list | head` prints a `BrokenPipeError` warning and exits 120.** Also on `main`. Case 36.

## UX gaps

- **No command shows the details of a ticket.** `list` shows only ID, state, and title. The CLI does not show the assignee, the resolution, the due time, or now the priority.
- **`--help` gives no help for the arguments.** `create --help` does not list the allowed priorities. `close --help` does not mention the minimum note length.
- **The "missing subcommand" error uses an internal name.** It says `the following arguments are required: cmd`.
- **A forgotten subcommand gives a confusing error.** `--priority P1` without `create` prints `invalid choice: 'P1'`.
- **The README does not say how to run the CLI.** The task cites the README for `python3 -m ticketdesk.cli`, but only AGENTS.md documents that command.
- **The close error does not say how long the note was.** The user must count characters.

## Improvements worth doing

- **Settle the spec conflicts before merge.** PR.md changes the behavior of TKT-008, TKT-010, and CLI-006 but edits none of them. It cites no spec ID. AGENTS.md asks the author to surface such conflicts and to cite IDs.
- **Store non-ASCII titles as readable text.** The log writes `Принтер` as `Пр...` (case 39). The LOG spec says users may read the log with any text tool. A `grep` for the title finds nothing.
- **Add CLI tests.** AGENTS.md says the tests do not cover the CLI. Each failure in this report shows only at the CLI.

## Leftover artifacts

All under `/Users/dmitri/dev/swd-skills-e2evidence/evals/e2e-test/workspace/iteration-4/eval-1-cli-branch-with-spec-violations/with_skill/run-3/outputs/`:

- `work/c01.jsonl` to `work/c39.jsonl` and `work/r33.jsonl`: one log per case. Case 23 created no `r23.jsonl`.
- `work/*.before`, `work/c35.a`, `work/c35.b`, `work/c28.err`: snapshots for the comparisons.
- `work/c19/`: `tickets.jsonl`, `env.jsonl`, `flag.jsonl` from the log path case.
- `work/main-tree/`: an export of `main` for the baseline. `work/main-logs/`: its logs.
- `harness/ev.sh`: the wrapper that wrote the evidence log.

The repo copy has no changes. `git status --porcelain --ignored` printed nothing after the run.

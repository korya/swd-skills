# E2e report: feature/cli-tidy

**35/48 PASS, 11 FAILURE, 2 BLOCKED. No-go: the branch lets a closed ticket reopen and get a new resolution, and `list` hides every ticket's priority.**

Seven of the 11 failures come from this branch and break three specs: TKT-008, CLI-006, and TKT-010. The other four failures exist on `main` too. Section 4 lists the issues in severity order.

## Scope, surface, environment

- **Scope.** The change is commit 4659f59 on `feature/cli-tidy` against `main` (8c5d958), plus the four claims in `PR.md`. The affected specs are `cli.md` and `tickets.md`, covered in full. The blast radius covers `event-log.md`, `invariants.md`, and the shell contract.
- **User and surface.** The user is a support agent at a shell. The surface is `python3 -m ticketdesk.cli`, run from the repo root, as the task asked.
- **Environment.** The run used a local macOS machine with Python 3.15.2. Every case wrote to its own throwaway log file under `outputs/e2e/logs/`. No shared environment was touched.
- **Depth.** The run is comprehensive, because the task asked for comprehensive testing before merge.
- **Evidence log.** Every command, its stdout, its stderr, and its exit code are in `outputs/e2e/evidence.log`, tagged by case. Cases tagged `R-<n>` are fresh-state reruns with short paths, quoted below. Cases tagged `base-<n>` ran the same steps on an extract of `main`.

The PR says "All tests pass locally." That claim is false. The run executed `make test` as a diagnosis step, and 1 of 7 tests fails (see issue 1).

## 1. Case table

| # | Case | Spec/ref | Status |
|---|---|---|---|
| 1 | Smoke: `--help` answers | surface | PASS |
| 2 | `--help` description line is correct | PR item 4 | FAILURE |
| 3 | Subcommand help lists the arguments | shell contract | PASS |
| 4 | No subcommand gives usage and exit 2 | CLI-001 | PASS |
| 5 | Unknown subcommand gives usage and exit 2 | CLI-001 | PASS |
| 6 | Missing positional arguments give a usage error | shell contract | PASS |
| 7 | `--log` selects the file | CLI-002 | PASS |
| 8 | `TICKETDESK_LOG` applies without `--log` | CLI-002 | PASS |
| 9 | `--log` wins over `TICKETDESK_LOG` | CLI-002 | PASS |
| 10 | Default `tickets.jsonl` in the current directory | CLI-002 | PASS |
| 11 | Create with the default priority | CLI-003, TKT-001 | PASS |
| 12 | Create with `--priority P1` | CLI-003 | PASS |
| 13 | Empty or whitespace title is rejected | TKT-002 | PASS |
| 14 | Unknown priority `P9` is rejected cleanly | TKT-003, CLI-007 TODO | FAILURE |
| 15 | IDs rise by one and survive a close | TKT-004, INV-003 | PASS |
| 16 | Due time follows the priority | TKT-005 | BLOCKED |
| 17 | Assign an open ticket | CLI-004, TKT-006 | PASS |
| 18 | Reassign replaces the assignee | TKT-006 | PASS |
| 19 | Empty or whitespace assignee is rejected | TKT-007 | PASS |
| 20 | Assign a closed ticket is rejected | TKT-008 | FAILURE |
| 21 | A closed ticket stays closed after an assign attempt | tickets.md "moves forward only" | FAILURE |
| 22 | A second close keeps the first resolution | TKT-011 | FAILURE |
| 23 | Unknown ID for assign and close | TKT-012 | PASS |
| 24 | Non-integer ID for assign and close | CLI-009 | PASS |
| 25 | Close an open ticket | CLI-005, TKT-009 | PASS |
| 26 | Close an assigned ticket keeps the assignee | TKT-009 | BLOCKED |
| 27 | 9-character note `duplicate` is rejected | TKT-010 | FAILURE |
| 28 | 8-character note is rejected | TKT-010 | PASS |
| 29 | Exactly 10-character note is accepted | TKT-010 | PASS |
| 30 | Padded note that trims to 9 characters is rejected | TKT-010 | FAILURE |
| 31 | Empty note is rejected | TKT-010 | PASS |
| 32 | Close twice is rejected | TKT-011 | PASS |
| 33 | List line shows `[<priority>]` | CLI-006 | FAILURE |
| 34 | List on an empty or missing log prints nothing | CLI-006, LOG-006 | PASS |
| 35 | List includes closed tickets in ID order | TKT-013 | PASS |
| 36 | Rule errors go to stderr only, with exit 2 | CLI-007 | PASS |
| 37 | Success exits 0 with empty stderr | CLI-008 | PASS |
| 38 | One event per change, none for list | LOG-001 | PASS |
| 39 | Event kinds, fields, `at`, sorted keys | LOG-002 to LOG-005, INV-005 | PASS |
| 40 | First create on a missing file makes ID 1 and the file | LOG-006 | PASS |
| 41 | Corrupt line stops replay with a clean error | LOG-007, INV-004, CLI-007 TODO | FAILURE |
| 42 | Append leaves earlier lines unchanged | LOG-008, INV-002 | PASS |
| 43 | Blank lines are ignored on replay | LOG-005 | PASS |
| 44 | Replay is deterministic | LOG-009 | PASS |
| 45 | Output works in a pipe | shell contract | PASS |
| 46 | Unusual titles list as one line each | CLI-006, edge | FAILURE |
| 47 | Ctrl-C leaves the log intact | shell contract | PASS |
| 48 | README tells the user how to run the tool | docs | FAILURE |

## 2. Non-PASS details

All steps run from the repo root. The log paths point at `../e2e/logs/`, which is `outputs/e2e/logs/`.

### Cases 20, 21, 22: a closed ticket reopens and takes a second resolution

**What was done.** Create a ticket, close it, assign it, list it, and close it again.

```bash
python3 -m ticketdesk.cli --log ../e2e/logs/r20.jsonl create 'Printer on fire'
python3 -m ticketdesk.cli --log ../e2e/logs/r20.jsonl close 1 'Replaced the toner cartridge'
python3 -m ticketdesk.cli --log ../e2e/logs/r20.jsonl assign 1 dana; echo "exit=$?"
python3 -m ticketdesk.cli --log ../e2e/logs/r20.jsonl list
python3 -m ticketdesk.cli --log ../e2e/logs/r20.jsonl close 1 'duplicate of ticket 7'; echo "exit=$?"
cat ../e2e/logs/r20.jsonl
```

**Expected.** The assign fails with `error: ticket 1 is closed` and exit 2, per TKT-008. The list shows `closed`. The second close fails with `error: ticket 1 is already closed`, per TKT-011. The log holds two events.

**Observed** (evidence log, case R-20):

```text
#1 open Printer on fire
#1 closed
#1 assigned -> dana
exit=0
#1 assigned Printer on fire
#1 closed
exit=0
{"at": 1793304803.2628999, "id": 1, "kind": "created", "priority": "P3", "title": "Printer on fire"}
{"at": 1793304803.303637, "id": 1, "kind": "closed", "resolution": "Replaced the toner cartridge"}
{"assignee": "dana", "at": 1793304803.336134, "id": 1, "kind": "assigned"}
{"at": 1793304803.4069839, "id": 1, "kind": "closed", "resolution": "duplicate of ticket 7"}
```

The same steps on `main` stop at the assign with `error: ticket 1 is closed` and exit 2 (case base-20). This is a regression.

**Most likely cause.** The branch removes the closed-state check from `TicketService.assign` in `ticketdesk/tickets.py`. Replay then applies the `assigned` event to a closed ticket and moves it back to `assigned`. The close check then sees an open ticket and accepts a second resolution. The repo's own test `test_assign_requires_open_ticket` fails on this branch for the same reason.

### Case 33: `list` no longer shows the priority

**What was done.**

```bash
python3 -m ticketdesk.cli --log ../e2e/logs/r33.jsonl create 'Printer on fire' --priority P1
python3 -m ticketdesk.cli --log ../e2e/logs/r33.jsonl create 'VPN down' --priority P2
python3 -m ticketdesk.cli --log ../e2e/logs/r33.jsonl list
```

**Expected.** Per CLI-006, the list lines are `#1 [P1] open     Printer on fire` and `#2 [P2] open     VPN down`.

**Observed** (evidence log, case R-33):

```text
#1 open Printer on fire
#2 open VPN down
#1 open     Printer on fire
#2 open     VPN down
```

On `main`, the list line is `#1 [P1] open     Printer on fire` (case base-33). The PR says a later PR brings the priority back with a flag. No such flag exists now. `list -h` shows only `-h`, and `list --priority` fails with `unrecognized arguments: --priority`. After this branch, no command shows a ticket's priority.

**Most likely cause.** The `list` print format in `ticketdesk/cli.py` drops the `[{t.priority}]` field.

### Cases 27 and 30: a 9-character note closes the ticket

**What was done.**

```bash
python3 -m ticketdesk.cli --log ../e2e/logs/r27.jsonl create 'Printer on fire'
python3 -m ticketdesk.cli --log ../e2e/logs/r27.jsonl close 1 duplicate; echo "exit=$?"
python3 -m ticketdesk.cli --log ../e2e/logs/r27.jsonl list
python3 -m ticketdesk.cli --log ../e2e/logs/r30.jsonl create 'Printer on fire'
python3 -m ticketdesk.cli --log ../e2e/logs/r30.jsonl close 1 '  duplicate  '; echo "exit=$?"
```

**Expected.** Per TKT-010, both closes fail with `error: resolution note must be at least 10 characters` and exit 2. The ticket stays `open`.

**Observed** (evidence log, cases R-27 and R-30):

```text
#1 open Printer on fire
#1 closed
exit=0
#1 closed   Printer on fire
```

```text
#1 open Printer on fire
#1 closed
exit=0
```

An 8-character note still fails with the old text (case R-28):

```text
error: resolution note must be at least 10 characters
```

The error now states a 10-character minimum, but the tool enforces 9. On `main`, `close 1 duplicate` fails with that error and exit 2 (case base-27).

**Most likely cause.** The length check in `TicketService.close` changes from `< 10` to `< 9`. The error text and TKT-010 stay at 10. The PR intends this change, so it needs a product decision. Either TKT-010 and the message change to 9, or the code goes back to 10.

### Case 2: the help description has a typo

**What was done.**

```bash
python3 -m ticketdesk.cli --help | sed -n 3p
```

**Expected.** A correctly spelled description, such as "Manage support tickets from the shell."

**Observed** (evidence log, case R-2):

```text
Manage support tikets from the shell.
```

**Most likely cause.** The new `description=` string in `ticketdesk/cli.py` misspells "tickets".

### Case 14: an unknown priority crashes with a traceback

**What was done.**

```bash
python3 -m ticketdesk.cli --log ../e2e/logs/r14.jsonl create 'Bad prio' --priority P9 2>&1 | sed -n '1p;$p'; echo "exit=${PIPESTATUS[0]}"
```

**Expected.** One clean line that names `P9` and the allowed values, with no ticket created. The user does not see a Python traceback.

**Observed** (evidence log, case R-14). The full output is a 14-line traceback (case R-14, piped to `wc -l`). The first and last lines are:

```text
Traceback (most recent call last):
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
exit=1
```

No ticket is created, and the message content meets TKT-003. The same traceback and exit 1 appear on `main` (case base-14). This defect exists before the branch, and the CLI-007 TODO in `docs/product-specs/cli.md` records it.

**Most likely cause.** `sla.due_at` raises `ValueError`, and `cli.py` catches only `TicketError`.

### Case 41: a corrupt log line crashes with a traceback

**What was done.**

```bash
python3 -m ticketdesk.cli --log ../e2e/logs/r41.jsonl create 'Printer on fire'
printf 'this is not json\n' >> ../e2e/logs/r41.jsonl
python3 -m ticketdesk.cli --log ../e2e/logs/r41.jsonl list 2>&1 | sed -n '1p;$p'; echo "exit=${PIPESTATUS[0]}"
```

**Expected.** Per LOG-007, an error that names the file, the line, and `corrupt event`. The user does not see a Python traceback.

**Observed** (evidence log, case R-41):

```text
#1 open Printer on fire
Traceback (most recent call last):
ValueError: ../e2e/logs/r41.jsonl:2: corrupt event: Expecting value: line 1 column 1 (char 0)
exit=1
```

The content meets LOG-007 and INV-004. No list output appears, and a `create` after the corruption appends nothing (case 41). The full output is a chained traceback of 34 lines (case R-41, piped to `wc -l`). The CLI-007 TODO records this defect, which exists before the branch.

**Most likely cause.** `store.replay` raises `ValueError`, and `cli.py` catches only `TicketError`.

### Case 46: a title with a newline prints as two list lines

**What was done.**

```bash
python3 -m ticketdesk.cli --log ../e2e/logs/r46.jsonl create 'Line one
line two'
python3 -m ticketdesk.cli --log ../e2e/logs/r46.jsonl create 'VPN down'
python3 -m ticketdesk.cli --log ../e2e/logs/r46.jsonl list
```

**Expected.** Per CLI-006, `list` prints one line per ticket. Either `create` rejects the newline or `list` escapes it.

**Observed** (evidence log, case R-46):

```text
#1 open Line one
line two
#2 open VPN down
#1 open     Line one
line two
#2 open     VPN down
```

A script that reads `list` line by line now sees a line without an ID. `main` behaves the same (case base-46). Unicode and 300-character titles store and list intact (case 46).

**Most likely cause.** Neither `create` nor `list` handles control characters in the title.

### Case 48: the README does not say how to run the tool

**What was done.** Read `README.md`.

**Expected.** The README tells a first-time user how to invoke the CLI.

**Observed** (evidence log, case 48). The README holds one description paragraph and this line:

```text
Run `make test` before you push and `make lint` for a syntax pass. CI runs both.
```

The run instructions and the `ticketdesk` entry point appear only in `AGENTS.md`. This gap exists before the branch.

### Case 16: due time is BLOCKED

No command prints a due time, and the log does not store one. A user cannot observe TKT-005 through the surface. A command that shows one ticket, or a due column in `list`, unblocks it.

### Case 26: assignee after close is BLOCKED

The close of an assigned ticket succeeds with `#1 closed`, and the log keeps the `assigned` event (case 26). No command shows the assignee of a ticket, so the kept assignee cannot be observed. A command that shows one ticket unblocks it.

## 3. Missing or untested cases

- **The installed `ticketdesk` entry point.** Not run. The task named `python3 -m ticketdesk.cli`, and an install needs a virtual environment outside the task's scope.
- **`make lint`.** Not run. It writes bytecode files into the repo.
- **Other platforms and Python versions.** Only Python 3.15.2 on macOS ran. `pyproject.toml` allows 3.11 and later, and CI uses 3.12.
- **Concurrent writers on one log.** No spec covers it, so it is out of scope.

## 4. Issues found

1. **High, regression. A closed ticket reopens on assign and takes a second resolution.** Cases 20, 21, 22. This breaks TKT-008, TKT-011, and the "moves forward only" rule in `tickets.md`. A closed ticket's resolution can change after the fact. The repo's test `test_assign_requires_open_ticket` fails on this branch, so "All tests pass locally" in the PR is false.
2. **High, regression. No command shows a ticket's priority any more.** Case 33. This breaks CLI-006. Priority sets the due time, so an agent can no longer triage from `list`. The flag the PR promises does not exist yet.
3. **Medium, regression. The tool accepts 9-character notes, but its error still demands 10.** Cases 27, 30. This breaks TKT-010, and the error message is now false. The PR intends the relaxed rule, so the spec and the message need a decision.
4. **Low, regression. The help description misspells "tickets" as "tikets".** Case 2.
5. **Low, exists on main. An unknown priority and a corrupt log line crash with a traceback and exit 1.** Cases 14, 41. The CLI-007 TODO tracks this.
6. **Low, exists on main. A title with a newline breaks the one-line-per-ticket list.** Case 46.
7. **Low, exists on main. The README has no run instructions.** Case 48.

The PR changes three specified behaviors and edits no spec. `AGENTS.md` asks that any conflict with a spec stop for discussion. The PR cites no spec IDs.

## 5. UX gaps

- **The CLI hides most ticket state.** No command shows the assignee, the resolution, or the due time. After this branch, it also hides the priority. A user must read the raw JSON log to see them.
- **Ctrl-C prints a `KeyboardInterrupt` traceback.** The run exits 130 and the log stays intact (case 47). A one-line message or silent exit would fit a shell tool.
- **The no-subcommand error leaks an internal name.** It says `the following arguments are required: cmd` (case 4). The help calls the argument `{create,assign,close,list}`.
- **The help gives no per-command text.** `--priority` does not list `P1`, `P2`, `P3`, and the subcommands carry no descriptions (cases 1, 3).
- **The state column shifts after ID 9.** `#9 open     Ticket 9` and `#10 open     Ticket 10` do not align (case 35).

## 6. Improvements worth doing

- **Add CLI tests.** `AGENTS.md` says the CLI has no tests. A CLI test of the `list` line would catch issue 2.
- **Settle the spec conflicts before merge.** Issues 1 to 3 each change a behavior the specs fix. Each needs a spec edit with user confirmation, or a code revert.
- **Split the PR.** The cosmetic help line and the rule changes have different risk and different reviewers.

## 7. Leftover artifacts

All artifacts are under `outputs/`. The repo working tree is clean (`git status --porcelain` printed nothing). The run set `PYTHONDONTWRITEBYTECODE=1`, so no `__pycache__` was written.

- `outputs/e2e/logs/c*.jsonl`: one log per case, made through the CLI.
- `outputs/e2e/logs/r*.jsonl`: the fresh-state reruns quoted above.
- `outputs/e2e/logs/b*.jsonl`: the `main` baseline runs.
- `outputs/e2e/logs/c47.jsonl`: 400,000 seeded `created` events, 34 MB. A script wrote them, because the CLI needs too long to make a log large enough to interrupt. Delete it when done.
- `outputs/e2e/c10cwd/tickets.jsonl`: the default-path log from case 10.
- `outputs/e2e/main-src/`: an extract of `main` from `git archive`, for the baseline.
- `outputs/e2e/cases.md`: the case list, written before execution.
- `outputs/e2e/evidence.log`: the evidence log.

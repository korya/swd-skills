# E2e report: feature/cli-tidy

**Verdict: 35/44 PASS, 9 FAILURE, 0 BLOCKED. Not ready to merge.**

Six failures come from four regressions on this branch. The first three regressions break product specs that the branch did not update:

- Assigning a closed ticket now reopens it. A second close then replaces the recorded resolution. This breaks TKT-008, TKT-011, and the forward-only rule.
- A 9-character resolution note now closes a ticket. TKT-010 requires 10, and the error text still says 10.
- `list` no longer shows the priority. CLI-006 requires `#<id> [<priority>] <state> <title>`.
- `--help` says "tikets".

The PR also says "All tests pass locally". That is false. `make test` on this branch fails `test_assign_requires_open_ticket` with `AssertionError: TicketError not raised`.

Three failures exist on `main` too. Each one is a Python traceback with exit code 1 instead of an `error:` line with exit code 2. They are not regressions, and two of them are the open TODO under CLI-007.

## Scope, surface, environment

- **Scope.** Branch `feature/cli-tidy` against `main`, as `PR.md` describes it. The cases cover the specs it touches (CLI, TKT, LOG, INV) and the paths it shares with close, list, and replay.
- **Surface.** A shell user runs `python3 -m ticketdesk.cli` from the repo root.
- **Environment.** Local. Every log file is a throwaway file under `outputs/artifacts/`.
- **Depth.** Comprehensive, because the request said "comprehensively" and the branch is about to merge.

I wrote the case list before execution. It is in `outputs/artifacts/case-list.md`. To tell regressions from old defects, I ran the failing scenarios again on `main` in a git worktree.

## Case table

| # | Case | Spec/ref | Status |
|---|------|----------|--------|
| R1 | Readiness: `--help` answers, exit 0 | CLI-001 | PASS |
| 1 | `--help` lists 4 subcommands, description reads correctly | CLI-001, PR | FAILURE |
| 2 | No subcommand: usage on stderr, exit 2 | CLI-001 | PASS |
| 3 | Unknown subcommand: usage on stderr, exit 2 | CLI-001 | PASS |
| 4 | `--log` selects the file | CLI-002 | PASS |
| 5 | `TICKETDESK_LOG` selects the file | CLI-002 | PASS |
| 6 | Default `tickets.jsonl` in the current directory | CLI-002 | PASS |
| 7 | `--log` wins over `TICKETDESK_LOG` | CLI-002 | PASS |
| 8 | create with default priority P3 | CLI-003, TKT-001, TKT-004 | PASS |
| 9 | create `--priority P1` | CLI-003, TKT-003 | PASS |
| 10 | create with empty title | TKT-002, CLI-007 | PASS |
| 11 | create with whitespace title | TKT-002, CLI-007 | PASS |
| 12 | create `--priority P9` | TKT-003, CLI-007 | FAILURE (on main too) |
| 13 | create with no title argument | shell contract | PASS |
| 14 | assign an open ticket | CLI-004, TKT-006 | PASS |
| 15 | reassign replaces the assignee | TKT-006 | PASS |
| 16 | assign a whitespace assignee | TKT-007, CLI-007 | PASS |
| 17 | assign a closed ticket is rejected | TKT-008, CLI-007 | FAILURE |
| 18 | a closed ticket stays closed after an assign attempt | TKT forward-only rule | FAILURE |
| 19 | a closed ticket cannot get a second resolution | TKT-011 | FAILURE |
| 20 | assign an unknown ID | TKT-012 | PASS |
| 21 | assign a non-integer ID | CLI-009 | PASS |
| 22 | close an assigned ticket with a 10+ character note | CLI-005, TKT-009 | PASS |
| 23 | close an open ticket directly | TKT-009 | PASS |
| 24 | close with the 9-character note `duplicate` is rejected | TKT-010 | FAILURE |
| 25 | close with an 8-character note is rejected | TKT-010 | PASS |
| 26 | close with exactly 10 characters is accepted | TKT-010 | PASS |
| 27 | close with a whitespace-padded 8-character note is rejected | TKT-010 | PASS |
| 28 | close a closed ticket | TKT-011 | PASS |
| 29 | close an unknown ID | TKT-012 | PASS |
| 30 | close a non-integer ID | CLI-009 | PASS |
| 31 | list line format includes the priority | CLI-006 | FAILURE |
| 32 | list on a missing log prints nothing, creates no file | CLI-006, LOG-006 | PASS |
| 33 | list includes closed tickets, in ID order | TKT-013 | PASS |
| 34 | one event per change, list appends nothing | LOG-001 | PASS |
| 35 | event kinds, fields, sorted keys, epoch `at` | LOG-002 to LOG-005, INV-005 | PASS |
| 36 | blank lines are ignored on replay | LOG-005 | PASS |
| 37 | missing log: first create gives #1 and creates the file | LOG-006 | PASS |
| 38 | a corrupt line stops replay with a clear error | LOG-007, INV-004, CLI-007 | FAILURE (on main too) |
| 39 | an append leaves earlier lines byte-identical | LOG-008, INV-002 | PASS |
| 40 | two replays print identical lists | LOG-009 | PASS |
| 41 | IDs are not reused after close | INV-003, TKT-004 | PASS |
| 42 | `list` output works in a pipe | shell contract | PASS |
| 43 | an unwritable log path gives a useful error | shell contract | FAILURE (on main too) |

## Failure details

In every block below, `$L` is a fresh log file path. Prefix each command with `python3 -m ticketdesk.cli --log $L`.

### Cases 17, 18, 19: a closed ticket reopens on assign and takes a second resolution

Assign on a closed ticket succeeds and moves the ticket back to `assigned`. A second close then succeeds and replaces the resolution.

Steps:

```text
create "Printer on fire"                   -> #1 open Printer on fire
close 1 "Replaced the toner cartridge"     -> #1 closed
assign 1 sam                               -> #1 assigned -> sam     (exit 0)
list                                       -> #1 assigned Printer on fire
close 1 "Closed a second time"             -> #1 closed              (exit 0)
```

| | Expected | Observed |
|---|----------|----------|
| Case 17 | `error: ticket 1 is closed` on stderr, exit 2, no event | `#1 assigned -> sam`, exit 0, one `assigned` event appended |
| Case 18 | `list` shows `#1 [P3] closed ...` | `list` shows `#1 assigned Printer on fire` |
| Case 19 | the resolution stays "Replaced the toner cartridge" | a second `closed` event with "Closed a second time" is appended and accepted |

The same steps on `main` print `error: ticket 1 is closed` with exit 2.

Most likely cause: the branch deleted the closed-state guard from `TicketService.assign` in `ticketdesk/tickets.py`. Replay then applies the `assigned` event to a closed ticket. `close` checks only the current state, so the reopened ticket closes again. The PR says "support asked for" this behavior. TKT-008 and the forward-only rule in `tickets.md` still forbid it. The branch changed no spec, and AGENTS.md requires user confirmation for a spec conflict.

### Case 24: a 9-character resolution note closes the ticket

The note `duplicate` has 9 characters, and the branch accepts it. TKT-010 requires at least 10 characters after trim.

```text
create "Duplicate of #2"     -> #3 open Duplicate of #2
close 3 "duplicate"          -> #3 closed     (exit 0)
create "Padded note"         -> #6 open Padded note
close 6 "   abcdefghi   "    -> #6 closed     (exit 0)
```

Expected: `error: resolution note must be at least 10 characters` on stderr, exit 2, the ticket stays open. Observed: the ticket closes. On `main` the same `close 1 duplicate` prints the expected error with exit 2.

The error text now contradicts the rule. An 8-character note still prints "must be at least 10 characters", but a 9-character note passes.

Most likely cause: the branch changed the check in `TicketService.close` from `< 10` to `< 9`. It did not change the message or TKT-010. The new threshold looks chosen to fit the one word "duplicate".

### Case 31: `list` drops the priority

`list` prints `#<id> <state> <title>` with no priority. CLI-006 requires `#<id> [<priority>] <state> <title>`.

```text
create "First"     -> #1 open First
list               -> #1 open     First
```

Expected: `#1 [P3] open     First`. On `main`, the same two steps on a fresh log list `#1 [P3] open     Baseline`.

No other command shows a priority. After this branch, a user cannot tell a P1 ticket from a P3 ticket at the CLI. Scripts that parse the bracketed field also break. The PR says a flag brings the column back "in a later PR". Until then the spec and the product disagree.

Most likely cause: the branch removed `[{t.priority}]` from the list format string in `ticketdesk/cli.py`.

### Case 1: the `--help` description has a typo

```text
$ python3 -m ticketdesk.cli --help
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...

Manage support tikets from the shell.
```

Expected: "tickets". Observed: "tikets". This line is new on this branch.

### Cases 12, 38, 43: three errors escape as Python tracebacks (on main too)

Three error paths print a full traceback on stderr and exit with code 1. CLI-007 asks for one `error: <message>` line and exit code 2.

| Case | Command | Last line of the traceback |
|------|---------|----------------------------|
| 12 | `create "Bad prio" --priority P9` | `ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']` |
| 38 | `list`, after appending the line `this is not json` | `ValueError: <path>/c38-corrupt.jsonl:2: corrupt event: Expecting value: line 1 column 1 (char 0)` |
| 43 | `--log /nonexistent-dir/t.jsonl create Nowhere` | `FileNotFoundError: [Errno 2] No such file or directory: '/nonexistent-dir/t.jsonl'` |

The content of each error is correct. Case 12 names P9 and the allowed values, and no ticket is created. Case 38 names the file, line 2, and `corrupt event`, and a later `create` appends nothing. The delivery is the defect. A user sees about 20 lines of Python internals, and scripts see exit code 1 instead of 2.

`main` behaves the same for all three. Cases 12 and 38 are the open TODO under CLI-007. Case 43 is not in that TODO.

Most likely cause: `cli.py` catches only `TicketError`. The `ValueError` from `sla.py` and `store.py` and the `OSError` from opening the file pass through to the interpreter.

## Missing or untested cases

- **TKT-005, due time by priority.** No command shows a due time, and the `created` event does not store one. The CLI surface cannot observe it.
- **TKT-009, the assignee is kept on close.** No command shows the assignee after close. The log has no event that clears it, but that is not an observation of the derived ticket.
- **The installed `ticketdesk` entry point.** The task named `python3 -m ticketdesk.cli` as the surface. I did not install the package.
- **An interrupted run.** Each command finishes in well under a second, so an interrupt mid-append was not reproducible by hand.
- **Concurrent writers.** Two agents appending to one log at the same time is outside this change.

## Issues by severity

1. **Critical. A closed ticket reopens, and its resolution can be replaced.** Cases 17, 18, 19. Regression. The history stays in the log, but every read of the ticket shows the new state and the new resolution. A support lead loses the "closed means done" guarantee.
2. **High. The resolution minimum drops to 9 characters without a spec change.** Case 24. Regression. The error message now states a rule that the product does not enforce.
3. **Medium. `list` hides the priority, and no other command shows it.** Case 31. Regression. It breaks CLI-006 and any script that parses the list output.
4. **Medium. Three error paths print tracebacks with exit code 1.** Cases 12, 38, 43. Not a regression. Two are the known CLI-007 TODO.
5. **Low. The `--help` description says "tikets".** Case 1. Regression.

Issues 1 to 3 have one process cause in common. The branch changes behavior that three specs define and updates none of them. AGENTS.md says such a conflict needs user confirmation first.

## UX gaps

- **No command shows one ticket in full.** The CLI never shows an assignee, a resolution, or a due time. After this branch it does not show the priority either. A user must read the raw JSON log to learn who owns a ticket.
- **Assign on a closed ticket gives no warning.** It prints the normal success line `#1 assigned -> sam`. The user gets no sign that a closed ticket reopened.
- **The missing-subcommand error leaks an internal name.** It says `the following arguments are required: cmd`. A user never sees the word "cmd" anywhere else.
- **The subcommands have no help text.** `--help` lists `{create,assign,close,list}` without a description of each. `create --help` shows `--priority PRIORITY` without the allowed values P1, P2, P3.
- **Priority is case-sensitive.** `--priority p1` gives a traceback instead of P1 or a short error.
- **The README does not say how to run the CLI.** It mentions only `make test` and `make lint`. The usage examples are in AGENTS.md, which a first-time user does not open.

## Improvements worth doing

- **Run the suite before the PR claims it passes.** `make test` fails 1 of 7 tests on this branch. The failing test guards TKT-008, which is issue 1.
- **Add CLI tests.** AGENTS.md says the CLI has no tests. Two of the four regressions live only in `cli.py`: the list format and the help text. The suite has no test for the TKT-010 boundary at 9 characters either.
- **Change the spec in the same PR as the behavior.** If support wants reassignment after close, TKT-008 and the forward-only rule need a decision first. Then the PR can cite the changed IDs.
- **Make the resolution error message read the threshold from the check.** Then the message and the rule cannot drift apart again.

## Leftover artifacts

Everything below is under `outputs/`. I kept it all because it reproduces the findings.

- `artifacts/case-list.md`: the case list, written before execution.
- `artifacts/main.jsonl`: tickets #1 to #8. Ticket #1 shows the reopen and second close. Ticket #3 shows the 9-character close.
- `artifacts/c04-flag.jsonl`, `artifacts/c05-env.jsonl`, `artifacts/c07-flag.jsonl`, `artifacts/c06-cwd/tickets.jsonl`: one ticket each, from the log path cases.
- `artifacts/c36-blank.jsonl`: two tickets with two blank lines between them.
- `artifacts/c38-corrupt.jsonl`: one ticket and the corrupt line `this is not json`.
- `artifacts/c-main-baseline.jsonl`: the baseline run on `main`.
- `artifacts/main-wt/`: a git worktree of `main`, registered in the `.git` of `outputs/repo`.
- `artifacts/main.before.jsonl`, `artifacts/list1.txt`, `artifacts/list2.txt`: snapshots for cases 39 and 40.
- `repo/ticketdesk/__pycache__/` and `repo/tests/__pycache__/`: bytecode that Python wrote during the runs and `make test`. No product file changed.

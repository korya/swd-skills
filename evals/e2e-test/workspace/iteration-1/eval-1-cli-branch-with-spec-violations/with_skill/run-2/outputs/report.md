# E2e test report: feature/cli-tidy

44/53 PASS, 9 FAILURE, 0 BLOCKED. Not ready to merge. The branch lets a closed ticket be reopened and closed a second time, and it accepts resolution notes the spec rejects.

Six of the nine failures are regressions introduced by this branch. Three are pre-existing tracebacks that main also shows. The branch's own test suite fails on one test, although the PR says all tests pass.

## Scope, surface, environment

The scope is the four changes named in `PR.md`, every criterion of the specs they touch, and the blast radius. The touched specs are `CLI-001` to `CLI-009`, `TKT-001` to `TKT-013`, and `LOG-001` to `LOG-009`.

| Item | Value |
|---|---|
| Surface | the shell, `python3 -m ticketdesk.cli` from the repo root, as `AGENTS.md` documents |
| Persona | a support agent at a terminal, first time using the tool |
| Environment | local dev, logs under `OUTPUT_DIR` via `--log` |
| Depth | comprehensive, because the ask says "comprehensively" and "before it merges" |
| Baseline for diagnosis | a `git archive` snapshot of `main`, run the same way |

`OUTPUT_DIR` below is `/Users/dmitri/dev/swd-skills/evals/e2e-test/workspace/iteration-1/eval-1-cli-branch-with-spec-violations/with_skill/run-2/outputs`.

## Case table

| # | Case | Spec/ref | Status |
|---|---|---|---|
| R1 | `--help` answers from the repo root | CLI-001 | PASS |
| C1 | `--help` shows a correctly spelled description line | PR item 4 | FAILURE |
| C2 | `list` line is `#<id> [<priority>] <state> <title>`, state padded to 8 | CLI-006, PR item 1 | FAILURE |
| C3 | `close` with the 9-character note `duplicate` is rejected | TKT-010, PR item 2 | FAILURE |
| C4 | `close` with an 8-character note is rejected, message says "at least 10" | TKT-010 | PASS |
| C5 | `close` with a 10-character note after trimming is accepted | TKT-010 | PASS |
| C6 | `close` with ` duplicate ` (9 after trimming) is rejected | TKT-010 | FAILURE |
| C7 | `assign` on a closed ticket is rejected with `ticket <id> is closed`, no event | TKT-008, PR item 3 | FAILURE |
| C8 | a closed ticket stays `closed` in `list` after an assign attempt | TKT-001 | FAILURE |
| S1 | no subcommand prints usage to stderr, exit 2 | CLI-001 | PASS |
| S2 | unknown subcommand prints usage to stderr, exit 2 | CLI-001 | PASS |
| S3 | `--log` path is used and the file is created there | CLI-002 | PASS |
| S4 | `TICKETDESK_LOG` is used when `--log` is absent | CLI-002 | PASS |
| S5 | `--log` wins over `TICKETDESK_LOG` | CLI-002 | PASS |
| S6 | `tickets.jsonl` in the current directory when neither is set | CLI-002 | PASS |
| S7 | `create` prints `#<id> open <title>`, default priority `P3` in the log | CLI-003 | PASS |
| S8 | `create --priority P1` is accepted and recorded | CLI-003, TKT-003 | PASS |
| S9 | `create ""` fails with `title is required`, exit 2, no event | TKT-002 | PASS |
| S10 | `create "   "` fails the same way | TKT-002 | PASS |
| S11 | `create --priority P4` fails with a message naming the value and the allowed values, exit 2 | TKT-003, CLI-007 | FAILURE |
| S12 | IDs run 1, 2, 3, then 4 and 5 after closes, never reused | TKT-004, INV-003 | PASS |
| S13 | `assign` on an open ticket prints `#<id> assigned -> <who>`, `list` shows `assigned` | CLI-004, TKT-006 | PASS |
| S14 | a second `assign` replaces the assignee | TKT-006 | PASS |
| S15 | `assign <id> ""` fails with `assignee is required`, no event | TKT-007 | PASS |
| S16 | `assign <id> "  "` fails the same way | TKT-007 | PASS |
| S17 | `assign 99 dana` fails with `no ticket 99`, exit 2 | TKT-012 | PASS |
| S18 | `close 99 <note>` fails with `no ticket 99`, exit 2 | TKT-012 | PASS |
| S19 | `assign abc dana` is a usage error on stderr, exit 2, no event | CLI-009 | PASS |
| S20 | `close abc <note>` is a usage error on stderr, exit 2, no event | CLI-009 | PASS |
| S21 | `close` on an open ticket prints `#<id> closed`, exit 0, note in the log | CLI-005, TKT-009 | PASS |
| S22 | `close` on an assigned ticket closes it and keeps the assigned events | TKT-009 | PASS |
| S23 | second `close` on a cleanly closed ticket fails with `ticket <id> is already closed` | TKT-011 | PASS |
| S24 | `list` is sorted by ID ascending, closed tickets included | TKT-013, CLI-006 | PASS |
| S25 | `list` on a missing log prints nothing, exit 0 | LOG-006 | PASS |
| S26 | every successful command exits 0 with an empty stderr | CLI-008 | PASS |
| S27 | every rule error leaves stdout empty and prints `error: ...` to stderr | CLI-007 | PASS |
| L1 | `list` appends nothing | LOG-001 | PASS |
| L2 | events carry `kind`, `id`, `at` plus the kind's fields, keys sorted, one line each | LOG-002, LOG-003, LOG-005 | PASS |
| L3 | `at` is epoch seconds matching the wall clock | LOG-004 | PASS |
| L4 | first `create` on a missing file makes ticket 1 and the file | LOG-006 | PASS |
| L5 | a corrupt line makes `list` fail with an error naming the path, line, and `corrupt event` | LOG-007, INV-004 | FAILURE |
| L6 | a corrupt line makes `create` fail and appends nothing | LOG-007 | PASS |
| L7 | existing bytes are unchanged after an append | LOG-008 | PASS |
| L8 | two `list` runs give identical output | LOG-009 | PASS |
| L9 | blank lines in the log are ignored | LOG-005 | PASS |
| X1 | `create` with no title is a usage error, exit 2 | shell contract | PASS |
| X2 | unknown option `--foo` is a usage error, exit 2 | shell contract | PASS |
| X3 | `--priority` with no value is a usage error, exit 2 | shell contract | PASS |
| X4 | `list` piped through `cat` and `head -1` works, exit 0 | shell contract | PASS |
| X5 | `create`, `assign`, `close`, `list` each answer `--help` accurately | shell contract | PASS |
| X6 | a title with accents, quotes, and an emoji round-trips through `list` | edge | PASS |
| X7 | `--log` pointing at a directory fails with a readable error | CLI-002 error path | FAILURE |
| X8 | `--log` after the subcommand is rejected as a usage error | CLI-002 | PASS |

## Non-PASS details

Every command below runs from `OUTPUT_DIR/repo`. `$L` is `OUTPUT_DIR/tickets.jsonl`.

### C1: `--help` description is misspelled

What was done: `python3 -m ticketdesk.cli --help`.

Expected: a correctly spelled description line. Observed, verbatim:

```text
Manage support tikets from the shell.
```

Most likely cause: a typo in the new `description=` argument of the parser.

### C2: `list` dropped the priority column

What was done: create three tickets with priorities `P1`, `P2`, and default, then `python3 -m ticketdesk.cli --log $L list`.

Expected per CLI-006: `#1 [P1] open     Printer on fire`. Observed:

```text
#1 open     Printer on fire
#2 open     Laptop will not boot
#3 open     Request new mouse
```

`main` prints `#1 [P1] open     Printer on fire`. The priority of a ticket is now visible nowhere except by reading the raw JSON log.

Most likely cause: the PR removes the column on purpose, see item 1 of `PR.md`. CLI-006 was not updated and no flag restores the column. `docs/README.md` requires that such a conflict is surfaced and the spec changed with sign-off.

### C3 and C6: notes of 9 characters are accepted

What was done:

```text
python3 -m ticketdesk.cli --log $L close 3 "duplicate"
python3 -m ticketdesk.cli --log $L close 1 " duplicate "
```

Expected per TKT-010: exit 2 and `error: resolution note must be at least 10 characters`. Observed for both: exit 0 and `#3 closed`, then `#1 closed`. The log gained lines 4 and 5 with those notes.

An 8-character note is still rejected, with the message that names 10 characters. The threshold is 9 and the message says 10, so the message is now wrong. `main` rejects `duplicate`.

Most likely cause: the branch lowered the length check by one without changing the spec, the message, or the tests. The PR calls this intended, but the spec says 10.

### C7 and C8: a closed ticket can be assigned, and that reopens it

What was done: ticket 1 was closed, then:

```text
python3 -m ticketdesk.cli --log $L assign 1 frank
python3 -m ticketdesk.cli --log $L list
```

Expected per TKT-008: exit 2, `error: ticket 1 is closed`, no event. Observed: exit 0, `#1 assigned -> frank`, and line 9 of the log is an `assigned` event. `list` then shows:

```text
#1 assigned Printer on fire
```

The ticket left the `closed` state, which TKT-001 forbids. A second `close 1 "Closing it again for real"` was then accepted with exit 0 and appended line 10, a second resolution for the same ticket. TKT-011 says a closed ticket cannot be closed again. `main` rejects the assign with `error: ticket 1 is closed`.

Most likely cause: the branch removed the closed-state check from `assign`, see item 3 of `PR.md`. Replay then applies the `assigned` event and moves the state back to `assigned`. The branch's own test `test_assign_requires_open_ticket` fails for the same reason.

### S11: unknown priority is a traceback

What was done: `python3 -m ticketdesk.cli --log $L create "Bad prio" --priority P4`.

Expected per TKT-003 and CLI-007: exit 2 and an `error:` line naming `P4` and the allowed values. Observed: exit 1 and a 12-line Python traceback ending in:

```text
ValueError: unknown priority 'P4'; expected one of ['P1', 'P2', 'P3']
```

Lowercase `p1` behaves the same. The content of the message meets TKT-003. The form does not meet CLI-007.

Most likely cause: pre-existing. `main` behaves the same, and the TODO under CLI-007 names this case. Not introduced by this branch.

### L5: a corrupt log line is a traceback

What was done: copy `$L`, insert `{not json` as line 3, then `python3 -m ticketdesk.cli --log OUTPUT_DIR/logs/corrupt.jsonl list`.

Expected per LOG-007: an error naming the path, the line number, and `corrupt event`. Observed: exit 1 and a 30-line traceback whose last line does name all three:

```text
ValueError: .../logs/corrupt.jsonl:3: corrupt event: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
```

No ticket state was printed and `create` on the same file appended nothing, so INV-004 holds.

Most likely cause: pre-existing. The TODO under CLI-007 names this case. Not introduced by this branch.

### X7: a directory as the log path is a traceback

What was done: `python3 -m ticketdesk.cli --log OUTPUT_DIR/logs list`.

Expected: a one-line error saying the path is a directory, exit 2. Observed: exit 1 and a traceback ending in `IsADirectoryError: [Errno 21] Is a directory: '.../outputs/logs'`. `create` behaves the same.

Most likely cause: the store opens the path without checking it is a file. The diff does not touch the store, so this is most likely pre-existing. It was not run on `main`.

## Missing or untested cases

| Case | Why |
|---|---|
| Due time by priority, TKT-005 | not observable on the surface. No command prints a due time and the log does not store one. |
| Assignee kept after close, TKT-009 | only partly observable. `list` never shows the assignee, so S22 rests on the `assigned` events staying in the log. |
| Interrupted run, shell contract | each invocation is one short append. No meaningful point to interrupt. |
| Priority shown by a flag, PR item 1 | the PR defers the flag to a later PR. Nothing to test. |
| Installed `ticketdesk` entry point | `AGENTS.md` documents the module form for this repo. The package was not installed. |

## Issues found

Ordered by severity. One issue can fail several cases.

### 1. High: a closed ticket can be reopened and closed again (C7, C8)

The branch accepts `assign` on a closed ticket and the ticket shows as `assigned` afterwards. A second `close` then succeeds and appends a second resolution. This breaks TKT-001, TKT-008, and TKT-011, and the branch's own test suite catches it. Regression against `main`.

### 2. High: the resolution minimum is 9 while the spec and the error message say 10 (C3, C6)

A 9-character note is accepted and an 8-character one is rejected with "at least 10 characters". The spec, the message, and the behavior disagree three ways. Regression against `main`.

### 3. Medium: `list` no longer shows the priority (C2)

CLI-006 requires the `[<priority>]` column. The PR removes it and defers a replacement flag to a later PR. Until then a user cannot see a priority without reading the JSON log. Regression against `main`.

### 4. Medium: the branch's test suite fails, the PR says it passes

`make test` on the branch fails `test_assign_requires_open_ticket` with `TicketError not raised`. `PR.md` says "All tests pass locally". CI runs `make test`, so the PR cannot pass CI as it stands. `main` passes all 7 tests.

### 5. Low: `--help` says "tikets" (C1)

The one line this PR added to the help text has a typo.

### 6. Low, pre-existing: three error paths are Python tracebacks (S11, L5, X7)

Unknown priority, a corrupt log line, and a directory as the log path each print a traceback and exit 1. The first two are the open TODO under CLI-007. The third is unspecified.

## UX gaps

- The too-short note error does not say how long the note was or how many characters are missing.
- Subcommand help has no descriptions. `create --help` shows `--priority PRIORITY` with no allowed values and no default. `close --help` does not mention the minimum note length.
- `list` never shows the assignee, so an agent cannot tell who owns a ticket without reading the JSON log.
- `--log` must come before the subcommand. Placed after it, the error is `unrecognized arguments: --log ...`, which does not say where the option belongs.
- `README.md` does not say how to run the tool. Only `AGENTS.md` does.
- The error for a corrupt log, when it appears, is buried at the bottom of a 30-line traceback.

## Improvements worth doing

- Add CLI-level tests. `AGENTS.md` records that the CLI has none, and all six regressions in this PR are visible only at the CLI or the service boundary.
- Decide the resolution minimum once and align TKT-010, the message, and the check. If "duplicate" must pass, the spec and the message should say 9.
- If assigning a closed ticket is wanted, specify it. The event should not move the state away from `closed`, or TKT-001 and TKT-011 stop holding.
- Store the resolution note trimmed, or say in LOG-003 that it is stored as typed. Lines 5 and 8 of the log hold notes with surrounding spaces.
- Catch `ValueError` and `OSError` at the CLI boundary so every failure is one `error:` line with exit 2, closing the CLI-007 TODO.

## Leftover artifacts

All under `OUTPUT_DIR`. The repo is unchanged. `git status` is clean and `git diff` is empty.

| Path | Holds |
|---|---|
| `tickets.jsonl` | the main run: 6 tickets, 15 events, including the reopen on lines 9 and 10 |
| `logs/env.jsonl`, `logs/flag.jsonl` | S4 and S5, one ticket each |
| `logs/cwd-default/tickets.jsonl` | S6, one ticket, created with the module on `PYTHONPATH` so the default path lands outside the repo |
| `logs/missing.jsonl` | S25 and L4 |
| `logs/before.jsonl`, `logs/list1.txt`, `logs/list2.txt` | L7 and L8 comparisons |
| `logs/blank.jsonl` | L9, the main log with two blank lines after line 2 |
| `logs/corrupt.jsonl`, `logs/corrupt.before` | L5 and L6, `{not json` on line 3 |

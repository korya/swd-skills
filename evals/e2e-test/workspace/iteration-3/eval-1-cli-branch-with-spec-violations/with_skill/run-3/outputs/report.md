# E2e test report: feature/cli-tidy

**29/40 PASS, 10 FAILURE, 1 BLOCKED. Not ready to merge.** An `assign` now reopens a closed
ticket, and a second `close` then replaces its resolution. The branch also breaks TKT-010
and CLI-006 without a spec change.

Six of the ten failures are regressions from this branch. They come from four issues, and
each issue matches an item in `PR.md`. The PR presents them as intended, but the specs
still forbid three of them. AGENTS.md
requires a spec conflict to go to the user before the code changes. That has not
happened. Either the specs change with user sign-off, or the code goes back.

The other four failures are pre-existing. The same commands fail the same way on `main`.
They do not block this branch, but they are listed below so nobody mistakes them for
regressions.

## Scope, surface, and environment

- **Change.** Branch `feature/cli-tidy`, one commit `4659f59` over merge base `8c5d958` on `main`.
- **Specs in scope.** `cli.md` (CLI), `tickets.md` (TKT), `event-log.md` (LOG), and `invariants.md` (INV).
- **Blast radius.** The whole CLI. It is one module with four commands and one log file.
- **Persona.** A support agent in a shell.
- **Surface.** `python3 -m ticketdesk.cli` from the repo root, as the task names it. Python 3.15.2 on macOS.
- **Environment.** Local only. Every log is a throwaway file under `outputs/artifacts/`.
- **Depth.** Comprehensive. The request said "comprehensively" and "before it merges".

I wrote the case list before I ran anything. It is in `outputs/artifacts/caselist.md`. To
tell regressions from old defects, I ran the changed commands against `main` as well. I
extracted `main` with `git archive` into `outputs/artifacts/main-src/` and left the repo
untouched.

## Case table

| # | Case | Spec/ref | Status |
|---|---|---|---|
| R0 | Readiness: `--help` answers, exit 0 | smoke | PASS |
| 1 | `--help` shows the new description line, spelled right | PR item 4 | FAILURE |
| 2 | Help lists the four subcommands and `--log` | CLI-001 | PASS |
| 3 | No subcommand: usage on stderr, exit 2 | CLI-001 | PASS |
| 4 | Unknown subcommand: usage on stderr, exit 2 | CLI-001 | PASS |
| 5 | `create` with default priority prints `#1 open <title>`, logs P3, exit 0, empty stderr | CLI-003, CLI-008, TKT-001 | PASS |
| 6 | `create --priority P1` and `P2` | CLI-003, TKT-003 | PASS |
| 7 | Empty and whitespace title: `error: title is required`, exit 2, no ticket | TKT-002, CLI-007 | PASS |
| 8 | Unknown priority `P9` and `p1`: clean error naming the value, no ticket | TKT-003, CLI-007 TODO | FAILURE |
| 9 | IDs rise 1, 2, 3 and keep rising after a close | TKT-004, INV-003 | PASS |
| 10 | `list` line is `#<id> [<priority>] <state> <title>` | CLI-006, PR item 1 | FAILURE |
| 11 | `list` on a missing log prints nothing, exit 0, creates no file | CLI-006, LOG-006 | PASS |
| 12 | `list` includes closed tickets, in ID order | TKT-013 | PASS |
| 13 | `assign` an open ticket prints `#1 assigned -> dana` | CLI-004, TKT-006 | PASS |
| 14 | Reassign replaces the assignee | TKT-006 | PASS |
| 15 | Empty and whitespace assignee: `error: assignee is required` | TKT-007 | PASS |
| 16 | `assign` a closed ticket: `error: ticket 1 is closed` | TKT-008, PR item 3 | FAILURE |
| 17 | A closed ticket stays closed, and its resolution never changes | tickets.md forward-only rule, TKT-011 | FAILURE |
| 18 | `assign` an unknown ID: `error: no ticket 99` | TKT-012 | PASS |
| 19 | `close` with a 10-character note prints `#1 closed` | CLI-005, TKT-009, TKT-010 | PASS |
| 20 | `close` with the 9-character note `duplicate` is rejected | TKT-010, PR item 2 | FAILURE |
| 21 | `close` with an 8-character note is rejected | TKT-010 | PASS |
| 22 | `close` with `"   duplicate   "` is rejected after trimming | TKT-010 | FAILURE |
| 23 | `close` with an empty note is rejected | TKT-010 | PASS |
| 24 | `close` keeps the assignee | TKT-009 | BLOCKED |
| 25 | `close` twice: `error: ticket 1 is already closed` | TKT-011 | PASS |
| 26 | `close` an unknown ID: `error: no ticket 99` | TKT-012 | PASS |
| 27 | Non-integer ID for `assign` and `close`: usage error, exit 2, no event | CLI-009 | PASS |
| 28 | `--log` beats `TICKETDESK_LOG`, which beats `./tickets.jsonl` | CLI-002 | PASS |
| 29 | One event per change, failed commands and `list` append nothing | LOG-001 | PASS |
| 30 | Event kinds and fields | LOG-002, LOG-003 | PASS |
| 31 | `at` is epoch seconds at append time | LOG-004, INV-005 | PASS |
| 32 | Sorted keys, newline at end, blank lines ignored on replay | LOG-005 | PASS |
| 33 | First `create` on a missing file gives `#1` and creates the file | LOG-006 | PASS |
| 34 | Corrupt line: clean error naming path, line, `corrupt event`, no state | LOG-007, INV-004, CLI-007 TODO | FAILURE |
| 35 | Append leaves existing lines byte-identical | LOG-008, INV-002 | PASS |
| 36 | `list` twice gives identical output | LOG-009 | PASS |
| 37 | `list \| head -n 1` exits quietly | shell contract | FAILURE |
| 38 | Odd but legal titles: unicode, leading dash, 300 characters, padding, newline | CLI-006 edge | FAILURE |
| 39 | ID `0` and `-1`: `error: no ticket <id>` | TKT-012 edge | PASS |

## Non-PASS details

In every repro below, `L` is a fresh log path such as `/tmp/t.jsonl`. Run each repro from
the repo root.

### Case 16: assigning a closed ticket succeeds (regression)

**What was done.**

```bash
python3 -m ticketdesk.cli --log $L create "Printer on fire" --priority P1
python3 -m ticketdesk.cli --log $L assign 1 dana
python3 -m ticketdesk.cli --log $L close 1 "Replaced the toner cartridge"
python3 -m ticketdesk.cli --log $L assign 1 sam
python3 -m ticketdesk.cli --log $L list
```

**Expected.** TKT-008 says the fourth command prints `error: ticket 1 is closed` to stderr
and exits 2. The ticket stays closed. On `main` it does exactly that.

**Observed.**

```text
$ python3 -m ticketdesk.cli --log $L assign 1 sam
#1 assigned -> sam            (exit 0)
$ python3 -m ticketdesk.cli --log $L list
#1 assigned Printer on fire
```

**Most likely cause.** The commit deletes the closed-state guard in `TicketService.assign`
in `ticketdesk/tickets.py`. Replay then applies the `assigned` event on top of `closed`.

### Case 17: a reopened ticket accepts a second resolution (regression)

**What was done.** Continue from case 16, then close the ticket again.

```bash
python3 -m ticketdesk.cli --log $L close 1 "Different resolution text"
cat $L
```

**Expected.** The ticket stays closed after its first close. `tickets.md` says "nothing
reopens a closed ticket". TKT-011 says the recorded resolution does not change.

**Observed.** The second close succeeds with `#1 closed` and exit 0. The log now holds two
resolutions for one ticket, and the second one wins on replay.

```text
{"at": 1793297515.272032, "id": 1, "kind": "closed", "resolution": "Replaced the toner cartridge"}
{"assignee": "sam", "at": 1793297515.3641899, "id": 1, "kind": "assigned"}
{"at": 1793297515.46084, "id": 1, "kind": "closed", "resolution": "Different resolution text"}
```

**Most likely cause.** This cascades from case 16. The `already closed` check in `close`
still works, but the reopen moves the ticket out of `closed` first.

### Case 20 and case 22: 9-character notes now close tickets (regression)

**What was done.**

```bash
python3 -m ticketdesk.cli --log $L create "Ticket 1"
python3 -m ticketdesk.cli --log $L create "Ticket 2"
python3 -m ticketdesk.cli --log $L close 1 "duplicate"
python3 -m ticketdesk.cli --log $L close 2 "   duplicate   "
```

**Expected.** TKT-010 rejects both notes. Each is 9 characters after trimming. The error is
`resolution note must be at least 10 characters`, exit 2. On `main`, `duplicate` is
rejected this way.

**Observed.** Both commands print `#<id> closed` and exit 0. The log stores the padded note
untrimmed as `"   duplicate   "`.

**Most likely cause.** The commit changes the check in `TicketService.close` from `< 10` to
`< 9`. It leaves the error text at "at least 10". An 8-character note such as `dupe1234` is
still rejected with that message, so the message now states a rule the code does not
apply.

### Case 10: `list` drops the priority column (regression)

**What was done.**

```bash
python3 -m ticketdesk.cli --log $L create "Printer on fire"
python3 -m ticketdesk.cli --log $L create "VPN drops hourly" --priority P1
python3 -m ticketdesk.cli --log $L list
```

**Expected against observed.**

| | Output |
|---|---|
| CLI-006, and `main` | `#2 [P1] open     VPN drops hourly` |
| This branch | `#2 open     VPN drops hourly` |

**Most likely cause.** The commit removes `[{t.priority}]` from the `list` format string in
`ticketdesk/cli.py`. No other command shows the priority. A P1 ticket now looks the same as
a P3 ticket unless the user reads the raw log.

### Case 1: typo in the new help description (regression)

**What was done.** `python3 -m ticketdesk.cli --help`

**Expected.** A correctly spelled description line.

**Observed.** `Manage support tikets from the shell.` The word "tickets" is misspelled.

**Most likely cause.** The typo is in the new `description=` argument in `ticketdesk/cli.py`.

### Case 8: unknown priority escapes as a traceback (pre-existing)

**What was done.**

```bash
python3 -m ticketdesk.cli --log $L create "Bad prio" --priority P9
python3 -m ticketdesk.cli --log $L create "Lower prio" --priority p1
```

**Expected.** CLI-007 asks for `error: <message>` on stderr and exit 2. TKT-003 asks the
message to name the value and the allowed values.

**Observed.** A 15-line Python traceback and exit 1. The last line holds the right content,
and no ticket is created.

```text
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
```

**Most likely cause.** `sla.due_at` raises `ValueError`, and the CLI catches only
`TicketError`. The TODO under CLI-007 already records this conflict. `main` behaves the same.

### Case 34: corrupt log line escapes as a traceback (pre-existing)

**What was done.**

```bash
python3 -m ticketdesk.cli --log $L create "Good one"
printf '{not json\n' >> $L
python3 -m ticketdesk.cli --log $L list
python3 -m ticketdesk.cli --log $L create "Never reached"
```

**Expected.** LOG-007 and INV-004 ask for an error that names the path, the line, and
`corrupt event`, with no state returned. CLI-007 asks for a clean `error:` line.

**Observed.** The content rules hold. The message names the path, line 2, and `corrupt
event`. `list` prints no tickets, and `create` appends nothing. The CLI still shows a
30-line chained traceback and exits 1 instead of 2. `main` behaves the same.

**Most likely cause.** `store.replay` raises `ValueError`, which the CLI does not catch.
This is the second half of the CLI-007 TODO.

### Case 37: `list` in a closed pipe prints a traceback (pre-existing)

**What was done.** Create 3,000 tickets through the CLI so `list` writes 201,786 bytes, then
run `python3 -m ticketdesk.cli --log $L list | head -n 1`.

**Expected.** The first line, and nothing on stderr. Shell tools stop quietly on a closed
pipe.

**Observed.** The first line prints, then stderr shows `BrokenPipeError: [Errno 32] Broken
pipe` with a traceback. The CLI exits 120. `main` behaves the same.

**Most likely cause.** The CLI does not handle `BrokenPipeError` or `SIGPIPE` around its
`print` loop.

### Case 38: a newline in a title breaks the one-line-per-ticket rule (pre-existing)

**What was done.**

```bash
python3 -m ticketdesk.cli --log $L create "line one
line two"
python3 -m ticketdesk.cli --log $L list
```

**Expected.** CLI-006 prints one line per ticket.

**Observed.** The ticket takes two lines, so `list | wc -l` miscounts and line-based tools
misread the second line. The other odd titles work. These are unicode, a leading dash after
`--`, 300 characters, and surrounding spaces. `main` behaves the same.

**Most likely cause.** `create` accepts any title that is not blank, and `list` prints it
raw.

### Case 24: assignee retention after close is not observable

**Status.** BLOCKED.

**Why.** TKT-009 says the assignee stays after a close. No command prints the assignee
after an `assign`. The log shows the `assigned` event and no event that clears it, but the
replayed state is not visible from outside.

**What unblocks it.** A command or `list` column that shows the assignee.

## Missing or untested cases

- **TKT-005, due time by priority.** No command and no log field shows the due time. The branch does not touch `sla.py`.
- **Interrupted runs.** Each command finishes in about 30 ms, so a Ctrl-C mid-write cannot be timed by hand.
- **The installed `ticketdesk` entry point.** The task named `python3 -m ticketdesk.cli`. I did not install the package.
- **`make test`.** The PR says all tests pass. An e2e run does not verify that claim. AGENTS.md says the tests do not cover the CLI.

## Issues found

1. **High, regression. An `assign` reopens a closed ticket, and a second `close` replaces the resolution.** It breaks TKT-008, TKT-011, and the forward-only rule. Cases 16 and 17.
2. **High, regression. The resolution minimum drops to 9 characters, but TKT-010 still says 10.** The error text still says "at least 10". Cases 20 and 22, with the message mismatch seen in case 21.
3. **Medium, regression. `list` no longer shows the priority, against CLI-006.** No other command shows it either. Case 10.
4. **Medium, pre-existing. An unknown priority and a corrupt log line print tracebacks and exit 1.** This is the open CLI-007 TODO. Cases 8 and 34.
5. **Low, regression. The new help line misspells "tickets" as "tikets".** Case 1.
6. **Low, pre-existing. `list` into a closed pipe prints a `BrokenPipeError` traceback.** Case 37.
7. **Low, pre-existing. A newline in a title splits one ticket across two `list` lines.** Case 38.

Issues 1 to 3 also form a process gap. The PR changes three specified behaviors and
updates no spec. It cites no spec IDs, though AGENTS.md asks PRs to cite them.

## UX gaps

- **Priority, due time, and assignee have no view.** After this branch, a user cannot see which tickets are P1 or who owns a ticket without reading JSON.
- **Subcommand help is bare.** `create --help` does not list `P1`, `P2`, `P3` or the `P3` default. `assign` and `close` have no description of `id` or the note rule.
- **`--log` help hides the default.** It does not mention `TICKETDESK_LOG` or `tickets.jsonl`.
- **The missing-subcommand error says `the following arguments are required: cmd`.** `cmd` is an internal name, not a word the user typed.
- **`list` misaligns at two-digit IDs.** The state column is padded, but the ID is not. At `#10` and `#3000` the columns shift.
- **The resolution note is stored untrimmed.** `"   duplicate   "` keeps its spaces in the log.
- **The README does not show how to run the CLI.** It covers only `make test` and `make lint`. The run commands are in AGENTS.md alone.

## Improvements worth doing

- **Add CLI-level tests for TKT-008 and TKT-010.** Both regressions shipped with "all tests pass", so the suite does not guard these rules at the surface the user sees.
- **Add a `.gitignore` entry for `tickets.jsonl`.** The default path lands in the repo root, and `git status` lists it as untracked.
- **Resolve the CLI-007 TODO.** It covers issue 4, and AGENTS.md already flags it as an open conflict.

## Leftover artifacts

All logs are under `outputs/artifacts/`. The repo has no product file changes.

| Artifact | What it holds |
|---|---|
| `caselist.md` | The case list, written before execution |
| `run.sh` | The shell helper that printed each command, its stdout, stderr, and exit code |
| `c05-create.jsonl` | Tickets #1 to #3 from cases 5 to 9 |
| `c13-assign-close.jsonl` | Tickets #1 to #8 from cases 13 to 26 |
| `c16-assign-closed.jsonl` | Ticket #1 reopened and closed twice, ticket #2 created after the close |
| `c27-nonint.jsonl` | Ticket #1 from cases 27 and 39 |
| `c28-flag.jsonl`, `c28-env.jsonl` | One ticket each from case 28 |
| `c32-blank.jsonl` | Two tickets with blank lines between them |
| `c34-corrupt.jsonl` | One good line and one corrupt line |
| `c35-append.jsonl` | Ticket #1 created, assigned, and closed |
| `c36-a.txt`, `c36-b.txt` | Two identical `list` outputs |
| `c37-pipe.jsonl` | 3,000 tickets |
| `c38-titles.jsonl` | Five tickets with odd titles |
| `main-src/`, `base-main.jsonl` | The `main` extract and its baseline log |
| `repo/tickets.jsonl` | Ticket #1 from the default-path check in case 28. It is untracked in the repo. |
| `repo/ticketdesk/__pycache__/` | Bytecode that Python wrote when the CLI ran |

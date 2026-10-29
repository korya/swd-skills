# E2e report: `feature/cli-tidy` against `main`

26/38 PASS, 11 FAILURE, 1 BLOCKED, so the branch is not ready to merge.

A closed ticket can now be reassigned. The reassignment reopens the ticket, and a second close then records a second resolution. The branch also breaks three specs that it does not update: TKT-008, TKT-010, and CLI-006. Six of the 11 failures are new on this branch. The other five also occur on `main`.

| Item | Value |
|---|---|
| Persona | A support agent who uses the shell |
| Surface | `python3 -m ticketdesk.cli` from the repo root, plus the JSON lines log read with `cat` |
| Environment | Local machine, Python 3.15.2, throwaway logs under `outputs/work/logs/` |
| Scope | The four PR items, the specs they touch (`tickets.md`, `cli.md`), and the event log they write |
| Depth | Comprehensive, because the request says "comprehensively, before it merges" |
| Baseline | `git archive main`, unpacked to `outputs/work/main/`, used to tell new failures from old ones |

## Case table

| # | Case | Spec/ref | Status |
|---|---|---|---|
| 1 | `--help` shows a correctly spelled description line | PR item 4 | FAILURE |
| 2 | Top-level and subcommand help are accurate | CLI-001 | PASS |
| 3 | `list` line is `#<id> [<priority>] <state> <title>`, state padded to 8 | CLI-006 | FAILURE |
| 4 | `list` on a missing log prints nothing, exits 0, creates no file | CLI-006, LOG-006, LOG-001 | PASS |
| 5 | `list` shows closed tickets in ID order | TKT-013 | PASS |
| 6 | `list \| head -1` on a 3000-ticket log is clean | Shell contract | FAILURE |
| 7 | Close with the 9-character note `duplicate` is rejected | TKT-010 | FAILURE |
| 8 | Close with `   duplicate   ` (9 characters after trim) is rejected | TKT-010 | FAILURE |
| 9 | Close with an 8-character note is rejected with the TKT-010 message | TKT-010 | PASS |
| 10 | Close with a 10-character note succeeds | TKT-010, CLI-005 | PASS |
| 11 | Close with an empty or whitespace-only note is rejected | TKT-010 | PASS |
| 12 | Assign a closed ticket fails with `ticket <id> is closed`, exit 2 | TKT-008, CLI-007 | FAILURE |
| 13 | After an assign attempt, the closed ticket still lists as `closed` | Forward-only rule in `tickets.md` | FAILURE |
| 14 | After an assign attempt, a second close fails with `already closed` | TKT-011 | FAILURE |
| 15 | Assign an open ticket | TKT-006, CLI-004 | PASS |
| 16 | Reassign an assigned ticket to a new name | TKT-006 | PASS |
| 17 | No subcommand or an unknown one prints usage to stderr, exit 2 | CLI-001 | PASS |
| 18 | `--log` wins over `TICKETDESK_LOG`, which wins over `./tickets.jsonl` | CLI-002 | PASS |
| 19 | A log path in a missing directory, or a directory, fails with a clear message | CLI-002 | FAILURE |
| 20 | `create` prints `#<id> open <title>` and defaults to `P3` | CLI-003, TKT-001 | PASS |
| 21 | `create --priority P1` and `P2` record those priorities | TKT-003 | PASS |
| 22 | An empty or whitespace title fails with `title is required` | TKT-002, CLI-007 | PASS |
| 23 | Priority `P9` fails with an error that names `P9` and the allowed values | TKT-003 | FAILURE |
| 24 | IDs start at 1, rise by one, and are not reused after a close | TKT-004, INV-003 | PASS |
| 25 | The user can see the due time of a ticket | TKT-005 | BLOCKED |
| 26 | A whitespace assignee fails with `assignee is required` | TKT-007 | PASS |
| 27 | Assign or close of ID 99 fails with `no ticket 99` | TKT-012 | PASS |
| 28 | A non-integer ID for `assign` or `close` gives a usage error, exit 2 | CLI-009 | PASS |
| 29 | Close an open ticket and an assigned ticket | TKT-009 | PASS |
| 30 | Close a closed ticket fails with `ticket <id> is already closed` | TKT-011 | PASS |
| 31 | Each ticket rule error writes only to stderr and exits 2 | CLI-007 | PASS |
| 32 | Each success exits 0 with empty stderr | CLI-008 | PASS |
| 33 | One event per change, `list` appends none, correct kinds and fields, sorted keys | LOG-001 to LOG-005 | PASS |
| 34 | An append leaves earlier lines byte-identical | LOG-008, INV-002 | PASS |
| 35 | Blank lines in the log are ignored | LOG-005 | PASS |
| 36 | A corrupt line stops the command with an error naming file, line, and `corrupt event` | LOG-007, INV-004 | FAILURE |
| 37 | Two `list` runs on the same log give the same output | LOG-009 | PASS |
| 38 | Missing and extra arguments give usage on stderr, exit 2 | CLI-001 | PASS |

## Non-PASS details

Every repro below starts from an empty log. Set it up once:

```bash
export LOG=$(mktemp -d)/t.jsonl
td() { python3 -m ticketdesk.cli --log "$LOG" "$@"; }
```

### Case 1: the help description has a typo (new on this branch)

The new description line says "tikets" instead of "tickets".

```text
$ python3 -m ticketdesk.cli --help
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...

Manage support tikets from the shell.
```

- **Expected.** `Manage support tickets from the shell.`
- **Most likely cause.** The `description=` string that this branch adds in `ticketdesk/cli.py` is misspelled.

### Case 3: `list` drops the priority (new on this branch)

The branch prints `#<id> <state> <title>`, but CLI-006 still requires `#<id> [<priority>] <state> <title>`.

```text
$ td create "Printer on fire" --priority P1
$ td create "VPN drops hourly" --priority P2
$ td create "Typo on login page"
$ td list
#1 open     Printer on fire
#2 open     VPN drops hourly
#3 open     Typo on login page
```

On `main` the same steps print `#1 [P1] open     Printer on fire`.

- **Expected.** The format of CLI-006, with the priority in brackets.
- **Impact.** No command now shows the priority. A `P1` ticket looks the same as a `P3` ticket. The only place a user can find the priority is the raw log file.
- **Most likely cause.** The `list` format string in `ticketdesk/cli.py` lost `[{t.priority}]`. The PR says a flag will restore it "in a later PR". The branch adds no flag and does not change CLI-006.

### Case 6: `list` in a pipe prints a Python error (also on `main`)

When the reader of the pipe exits early, `list` writes a Python error to stderr and exits 120.

```text
$ for i in $(seq 1 3000); do td create "Bulk ticket $i" >/dev/null; done
$ td list | head -1
#1 open     Bulk ticket 1
Exception ignored while flushing sys.stdout:
BrokenPipeError: [Errno 32] Broken pipe
```

In zsh, `${pipestatus[@]}` then shows `120 0`.

- **Expected.** The first line, no stderr noise, and a quiet exit, as `cat` or `grep` give.
- **Most likely cause.** The CLI does not handle `SIGPIPE` or `BrokenPipeError`.

### Cases 7 and 8: a 9-character note closes the ticket (new on this branch)

TKT-010 rejects any note shorter than 10 characters after a trim. The branch accepts 9.

```text
$ td create "Resolution case 1"
$ td create "Resolution case 2"
$ td create "Resolution case 3"
$ td close 1 "duplicate"
#1 closed
$ td close 2 "   duplicate   "
#2 closed
$ td close 3 "dup note"
error: resolution note must be at least 10 characters
```

On `main`, `td close 1 "duplicate"` prints `error: resolution note must be at least 10 characters` and exits 2.

- **Expected.** Both closes fail with `resolution note must be at least 10 characters`, and the tickets stay open.
- **Impact.** The error message still says 10, but the product now accepts 9. The message and the behavior disagree. The change also helps only notes of exactly 9 characters. Other short notes, such as `dup` or `wontfix`, are still rejected.
- **Most likely cause.** The check in `TicketService.close` changed from `< 10` to `< 9`. The message and TKT-010 did not change.

### Case 12: a closed ticket accepts a new assignee (new on this branch)

Assigning a closed ticket now succeeds and appends an `assigned` event. TKT-008 requires the error `ticket <id> is closed`.

```text
$ td create "Laptop will not boot" --priority P1
$ td assign 1 dana
$ td close 1 "Reseated the RAM module"
#1 closed
$ td assign 1 erik
#1 assigned -> erik
$ echo $?
0
```

On `main`, `td assign 1 erik` prints `error: ticket 1 is closed` and exits 2.

- **Expected.** `error: ticket 1 is closed` on stderr, exit 2, and no new event.
- **Most likely cause.** The branch deletes the closed-state guard from `TicketService.assign`. PR item 3 asks for this change. TKT-008 and the forward-only rule in `tickets.md` still forbid it.

### Case 13: the reassignment reopens the closed ticket (new on this branch)

After case 12, `list` shows the ticket as `assigned`. The forward-only rule in `tickets.md` says "Nothing reopens a closed ticket."

```text
$ td list
#1 assigned Laptop will not boot
```

- **Expected.** `#1 [P1] closed   Laptop will not boot`.
- **Most likely cause.** Replay applies each `assigned` event as a move to `assigned`, whatever the previous state was. The guard from case 12 was the only protection.

### Case 14: the reopened ticket closes a second time (new on this branch)

After case 13, a second close succeeds and the log now holds two resolutions for one ticket. TKT-011 requires `ticket <id> is already closed` and an unchanged resolution.

```text
$ td close 1 "Second resolution after reassign"
#1 closed
$ cat "$LOG"
{"at": 1793297631.0628219, "id": 1, "kind": "created", "priority": "P1", "title": "Laptop will not boot"}
{"assignee": "dana", "at": 1793297631.10507, "id": 1, "kind": "assigned"}
{"at": 1793297631.1489332, "id": 1, "kind": "closed", "resolution": "Reseated the RAM module"}
{"assignee": "erik", "at": 1793297631.1954648, "id": 1, "kind": "assigned"}
{"at": 1793297631.281369, "id": 1, "kind": "closed", "resolution": "Second resolution after reassign"}
```

- **Expected.** `error: ticket 1 is already closed`, exit 2, and the first resolution kept.
- **Most likely cause.** The same as case 13. The close guard checks the current state, and the reassignment changed that state back to `assigned`.

### Case 19: a bad log path gives a Python traceback (also on `main`)

A `--log` path in a missing directory, or a path that is a directory, ends in a traceback and exit 1.

```text
$ python3 -m ticketdesk.cli --log /nonexistent-dir/t.jsonl create "Nowhere to go"
Traceback (most recent call last):
  ...
FileNotFoundError: [Errno 2] No such file or directory: '/nonexistent-dir/t.jsonl'
$ python3 -m ticketdesk.cli --log "$(dirname "$LOG")" create "Log is a directory"
Traceback (most recent call last):
  ...
IsADirectoryError: [Errno 21] Is a directory: '...'
```

In the same missing directory, `list` prints nothing and exits 0. It does not warn that the path cannot be used.

- **Expected.** One line on stderr, such as `error: cannot write log /nonexistent-dir/t.jsonl: no such directory`, and a nonzero exit.
- **Most likely cause.** The CLI catches only `TicketError`. The store raises `OSError` from `open()`.

### Case 23: an unknown priority gives a Python traceback (also on `main`)

The last traceback line names `P9` and the allowed values, and no ticket is created. But the user sees a traceback of about 15 lines and exit 1. Lowercase `p1` fails the same way.

```text
$ td create "Wrong priority" --priority P9
Traceback (most recent call last):
  ...
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
$ echo $?
1
```

- **Expected.** `error: unknown priority 'P9'; expected one of P1, P2, P3` on stderr, exit 2.
- **Most likely cause.** `sla.due_at` raises `ValueError`, and the CLI catches only `TicketError`. The TODO under CLI-007 already records this conflict.

### Case 25: no command shows the due time (BLOCKED)

TKT-005 defines a due time per priority, but no command prints it, and the log does not store it. A user cannot check this spec through the product.

- **Unblocks it.** A command or an output field that shows the due time.

### Case 36: a corrupt log line gives a Python traceback (also on `main`)

The error text names the file, line 2, and `corrupt event`, and no tickets are listed. But the user sees two chained tracebacks of about 40 lines and exit 1.

```text
$ td create "Before the corruption"
$ printf '{"kind": "created", "id": 2, oops\n' >> "$LOG"
$ td list
Traceback (most recent call last):
  ...
ValueError: /.../t.jsonl:2: corrupt event: Expecting property name enclosed in double quotes: line 1 column 30 (char 29)
$ echo $?
1
```

The CLI cannot write a corrupt line, so this case appends one with `printf`.

- **Expected.** One line on stderr, such as `error: /.../t.jsonl:2: corrupt event`, and a nonzero exit.
- **Most likely cause.** The store raises `ValueError`, and the CLI catches only `TicketError`. The TODO under CLI-007 already records this conflict.

## Missing or untested cases

- **The installed `ticketdesk` entry point.** The request named `python3 -m ticketdesk.cli`. A `pip install` would write build files into the repo, which this run must not change.
- **An interrupted run.** A command finishes in about 40 ms. The shell gives no reliable way to stop it in the middle of an append.
- **Two agents that write to one log at the same time.** No spec covers it, so it is out of scope.
- **`make test` and `make lint`.** They do not test the product from the user's seat. The PR says "All tests pass locally". This run did not check that claim.
- **The default `./tickets.jsonl` path in case 18.** The case ran in a scratch directory with `PYTHONPATH` set to the repo, so the repo root got no `tickets.jsonl`.

## Issues found

1. **High. A closed ticket can be reassigned, which reopens it and lets it close again.** Cases 12, 13, and 14. New on this branch. A team that relies on "closed means closed" can lose that guarantee with one mistyped ID. Even if support wants to reassign closed tickets, the change must not move a closed ticket back to `assigned`. TKT-008 and the forward-only rule need a decision from the spec owner before this lands.
2. **High. The resolution minimum is 9, but the spec and the error message say 10.** Cases 7 and 8. New on this branch. The user reads "at least 10" and then sees 9 succeed. If the team wants shorter notes, TKT-010, the message, and the check must change together.
3. **Medium. `list` no longer shows the priority, and no other command does.** Case 3. New on this branch. CLI-006 still requires the priority. A user who triages from `list` cannot tell a `P1` from a `P3`.
4. **Medium. Three error paths end in a Python traceback with exit 1.** Cases 19, 23, and 36. All three also occur on `main`. Two of them are the known TODO under CLI-007. The bad log path is not in that TODO.
5. **Low. The new help description misspells "tickets".** Case 1. New on this branch.
6. **Low. `list` in a pipe prints `BrokenPipeError` and exits 120.** Case 6. Also on `main`.

## UX gaps

- **The tool hides most ticket data.** No command shows the assignee, the resolution, or the due time. After this branch, no command shows the priority either. The `assign` output is the only place an assignee appears.
- **The help is thin.** The subcommands have no descriptions. The `--priority` help does not list `P1`, `P2`, and `P3`. The help does not mention `TICKETDESK_LOG`, the default `./tickets.jsonl`, or the 10-character minimum.
- **The README does not say how to run the CLI.** It covers only `make test` and `make lint`. The run commands are in `AGENTS.md`.
- **`list` on an unusable log path is silent.** Case 19 shows that `list` exits 0 with no output, so a typo in `--log` looks like an empty help desk.
- **Prefixes of options work silently.** `create "Bad flag" --prio P1` created a `P1` ticket. That is the argparse default. A new option that starts with `prio` would change what old scripts do.

## Improvements worth doing

- **Change the specs together with the behavior, or drop the behavior change.** `AGENTS.md` says that a change that contradicts a spec must stop for discussion. This branch changes TKT-008, TKT-010, and CLI-006 in code only.
- **Add CLI tests.** `AGENTS.md` lists the CLI as not covered by tests. Each of the six new failures is visible in one CLI call, so a CLI test for each spec item would have caught them.
- **Decide the CLI-007 TODO.** One catch for `ValueError` and `OSError` in the CLI would turn cases 19, 23, and 36 into one-line errors with exit 2.

## Leftover artifacts

All are under `outputs/work/` and stay in place to help reproduce the findings.

| Path | Content |
|---|---|
| `logs/c03.jsonl` | Three tickets for the `list` format, case 3 |
| `logs/c06.jsonl` | 3000 bulk tickets for the pipe case |
| `logs/c07b.jsonl` | Six tickets for the resolution cases |
| `logs/c12.jsonl`, `logs/c12.before` | The reopened ticket with two resolutions, and the log before the reassignment |
| `logs/c15.jsonl` | Assign and reassign cases |
| `logs/c18-cwd/tickets.jsonl`, `logs/c18-env.jsonl`, `logs/c18-flag.jsonl` | One ticket per log path source |
| `logs/c20.jsonl` | Create cases with each priority |
| `logs/c24.jsonl`, `logs/c24.snap1`, `logs/c24.snap2` | The ID, close, and append cases, with snapshots |
| `logs/c35.jsonl` | A log with blank lines |
| `logs/c36.jsonl` | A log with a corrupt line 2 |
| `logs/c38.jsonl` | The ticket created with `--prio P1` |
| `logs/base.jsonl` | Baseline runs against `main` |
| `logs/c06.stderr`, `logs/c06-main.stderr` | The broken pipe stderr from the branch and from `main` |
| `main/` | The `main` tree, unpacked with `git archive` |
| `bin/t.sh` | The runner that prints stdout, stderr, and the exit code of one command |
| `caselist.md` | The case list, written before the first case ran |

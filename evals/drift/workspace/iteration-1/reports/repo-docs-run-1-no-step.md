# Drift report: ticketdesk 0.3.0 against docs/product-specs/

The run covered 29 criteria and found 23 MATCH, 1 DRIFT, 4 BLOCKED, 1 OPEN, and 1 UNCOVERED behaviour.
The DRIFT item is CLI-009. The OPEN item is CLI-008. The BLOCKED items are TKT-001, TKT-004, TKT-008, and LOG-004.
The run took about 10 minutes of work and the host reported a cost of about $0.24.

## Scope and surface

Scope is every feature criterion in `tickets.md` (13), `cli.md` (9), and `event-log.md` (7). That makes 29 criteria. The four `INV` criteria were checked only where a feature criterion makes them observable (INV-001 through INV-004 appear in the notes under TKT-005, CLI-002, and LOG-005).

- **User:** a support agent in a shell.
- **Surface:** the `ticketdesk` command line and the `tickets.jsonl` file, which `event-log.md` declares a product surface.
- **Environment:** local, on Darwin, with scratch logs only.
- **Invocation:** `python3 -m ticketdesk.cli`, with `PYTHONPATH` set to the repo and `PYTHONDONTWRITEBYTECODE=1`. `AGENTS.md` says the console script install was not verified and the module form is the one known to work. Assumption: the module form is the surface users get. Nobody was available to confirm.
- **Evidence logs:** `drift-scratch/evidence.log` and `drift-scratch/evidence2.log` next to this report. Scripts are `run.sh` and `run2.sh` in the same directory.

Commands below are shortened to `td`, which means `python3 -m ticketdesk.cli`. Rows say which log file they used.

## tickets.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| TKT-001 | BLOCKED | `td --log l1.jsonl create "Printer on fire" --priority P1`, then `list` and `cat l1.jsonl` | Prints `#1 open Printer on fire`. The list shows state `open`. No command prints the due time. See BLOCKED below. |
| TKT-002 | MATCH | `td --log l1.jsonl create ""` and `create "   "` | `error: title is required`, status 2, log stays at 3 lines. |
| TKT-003 | MATCH | `td --log l1.jsonl create Bad --priority P9`, also `--priority p1` | Last line of stderr is `ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']`. The log stays at 3 lines. Presentation is CLI-008. |
| TKT-004 | BLOCKED | `td --log l1.jsonl create` for P1, P2, P3, then `cat l1.jsonl` | The log holds only creation time. No surface shows a due time. See BLOCKED below. |
| TKT-005 | MATCH | `td create "Default priority"` on a missing log, then `td --log g.jsonl create next` on a log whose only ticket is `id` 7 | First ticket is `#1`. The next ticket after 7 is `#8`. Gaps do not reuse numbers (INV-004). |
| TKT-006 | MATCH | `td --log l1.jsonl assign 1 dana`, then `assign 1 erik`, then `list` | `#1 assigned -> dana`, then `#1 assigned -> erik`. The list shows `assigned`. |
| TKT-007 | MATCH | `td --log l1.jsonl assign 1 "  "` and `assign 1 ""` | `error: assignee is required`, status 2, log unchanged. |
| TKT-008 | BLOCKED | `td --log z.jsonl create Z`, then `close 1 "closed without assign"`. Also `close 1 "Replaced the toner cartridge"` on an assigned ticket | Unassigned and assigned tickets both close and print `#1 closed`. The resolution is in the log. No surface shows that the assignee stays. See BLOCKED below. |
| TKT-009 | MATCH | `td --log y.jsonl close 1 123456789`, then `close 1 "  1234567890  "` | 9 characters: `error: resolution note must be at least 10 characters`, status 2. 10 characters after trimming: `#1 closed`. |
| TKT-010 | MATCH | `td --log l1.jsonl close 2 "again long enough"`, then `assign 2 bob` on closed ticket 2 | `error: ticket 2 is already closed` and `error: ticket 2 is closed`. Both status 2. |
| TKT-011 | MATCH | `td --log l1.jsonl assign 9 x`, `close 9 "long enough note"`, `assign 0 a`, `assign -1 a` | `error: no ticket 9`, `error: no ticket 9`, `error: no ticket 0`, `error: no ticket -1`. Log unchanged. |
| TKT-012 | MATCH | open to assigned, assigned to assigned, open to closed, assigned to closed, then any command on a closed ticket | All four allowed moves worked. Closed tickets rejected both commands. No command moves a ticket back to `open`. |
| TKT-013 | MATCH | `td --log o.jsonl list` on a log written with ticket 3 before ticket 1 | `#1 [P2] open     one` then `#3 [P1] open     three`. An empty log lists nothing, status 0. |

## cli.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| CLI-001 | MATCH | `td` with no arguments | stderr: `ticketdesk: error: the following arguments are required: cmd`, preceded by the usage line. Status 2. |
| CLI-002 | MATCH | `td list` with no log, `TICKETDESK_LOG=env.jsonl td create Env`, then `TICKETDESK_LOG=env.jsonl td --log opt.jsonl create "Opt wins"` | No log reads as empty. The first `create` made `tickets.jsonl`. The variable chose `env.jsonl`. `--log` won and `env.jsonl` stayed at 1 line. |
| CLI-003 | MATCH | `td create "Default priority"` | `#1 open Default priority`, status 0, priority `P3` in the log. |
| CLI-004 | MATCH | `td --log l1.jsonl assign 1 dana` | `#1 assigned -> dana`, status 0. |
| CLI-005 | MATCH | `td --log l1.jsonl close 1 "Replaced the toner cartridge"` | `#1 closed`, status 0. |
| CLI-006 | MATCH | `td --log l1.jsonl list` after mixed states | Lines such as `#1 [P1] closed   Printer on fire` and `#3 [P3] open     Low`. State is padded to 8 characters. Status 0. |
| CLI-007 | MATCH | The rejected commands under TKT-002, 007, 009, 010, 011 | Each printed `error: <message>` on stderr, nothing on stdout, status 2, and no new log line. |
| CLI-008 | OPEN | `td --log l1.jsonl create Bad --priority P9` | The settled part matches. Python traceback on stderr, last line `ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']`, status 1. The TODO is quoted below. |
| CLI-009 | DRIFT | `td --log c.jsonl list` on a log with a corrupt line | Status 1 from a path other than CLI-008. See DRIFT details. Statuses 0 and 2 matched in every other run. |

## event-log.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| LOG-001 | MATCH | `td --log x.jsonl` with create, assign, close, rejected close, list, then `wc -l` | Log grew by exactly 1 line per create, assign, and close. Rejected commands and `list` added none (3 lines, then 4 after the next create). |
| LOG-002 | MATCH | `cat l1.jsonl`, `tail -c 1 x.jsonl \| xxd` | One object per line, keys in alphabetical order, last byte `0a`. A non-ASCII title is stored as `Ü` escapes, which is valid UTF-8 text. |
| LOG-003 | MATCH | `cat l1.jsonl` | `created` carries `title` and `priority`. `assigned` carries `assignee`. `closed` carries `resolution`. All carry `kind`, `id`, `at`. Write-time of `at` was not checked. |
| LOG-004 | BLOCKED | none possible | No surface prints a due time, so two runs cannot be compared. See BLOCKED below. |
| LOG-005 | MATCH | `td --log c.jsonl list`, then `create y` and `close 1 "long enough note"` on the same log | Each run stopped. Last stderr line is `ValueError: c.jsonl:2: corrupt event: Expecting value: line 1 column 1 (char 0)`. No tickets printed and `c.jsonl` stayed at 2 lines. Line numbers count blank lines (`c.jsonl:4`). |
| LOG-006 | MATCH | `td --log bl.jsonl list` on a log with blank and whitespace-only lines around one event | Prints `#1 [P1] open     Printer on fire`, status 0. |
| LOG-007 | MATCH | `td --log none.jsonl close 1 "long enough note"`, `create ""`, `td --log e.jsonl list`, then `ls none.jsonl` | Missing log lists as empty. Rejected commands did not create `none.jsonl`. An empty existing file read as empty and the first `create` wrote 1 line. |

## DRIFT details

### CLI-009: exit status 1 also comes from a corrupt log

The spec says: "| 1 | an uncaught error, today only CLI-008 |".

Command and output, from `evidence.log`:

```
$ td --log c.jsonl list      (c.jsonl line 2 is "not json")
[stdout]
[stderr]
Traceback (most recent call last):
  ...
  File ".../ticketdesk/store.py", line 35, in replay
    raise ValueError(f"{self.path}:{lineno}: corrupt event: {exc}") from exc
ValueError: c.jsonl:2: corrupt event: Expecting value: line 1 column 1 (char 0)
[rc=1]
```

`create` and `close` on the same log gave the same traceback and status 1.

Likely cause: the command line does not catch the error the event store raises. This is a likelihood, read from the traceback only.

## UNCOVERED behaviours

### `--help` and `-h`

The product prints usage and exits 0 for `td --help`, `td create --help`, `td assign --help`, `td close --help`, and `td list --help`.

```
$ td create --help
usage: ticketdesk create [-h] [--priority PRIORITY] title
...
[rc=0]
```

No criterion mentions help output or its status. The nearest is CLI-001 (commands) and CLI-009 (status 0 means the command succeeded).

## BLOCKED and OPEN

- **BLOCKED, TKT-001:** needs a command that prints the due time, and one that prints the assignee and resolution of a new ticket.
- **BLOCKED, TKT-004:** needs a command that prints each ticket's due time, so 4, 24, and 72 hours can be compared with the creation time.
- **BLOCKED, TKT-008:** needs a command that prints a closed ticket's assignee, so a reader can see it stayed.
- **BLOCKED, LOG-004:** needs the same command as TKT-004, run twice on one log.
- **OPEN, CLI-008:** the TODO reads "decide whether this is a defect. See `questions.md` of the 2026-11-09 docs run, Q2." The settled part matched in this run: traceback, final line from TKT-003, status 1. The file `questions.md` is not in the repo.

## Artifacts

All under `drift-scratch/` next to this report: `run.sh`, `run2.sh`, `evidence.log`, `evidence2.log`, and the scratch directories `a/` and `b/` with their `.jsonl` logs. The repo is unchanged. `git status` shows only the two untracked paths that existed before the run, `AGENTS.md` and `docs/`.

## Decision

You decide now whether the spec or the product changes for CLI-009, and whether the `--help` item gets a criterion.

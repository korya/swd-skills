# Drift report: ticketdesk 0.3.0 against docs/product-specs/

The run covered 29 criteria and found 25 MATCH, 0 DRIFT, 2 BLOCKED, 2 OPEN, and 3 UNCOVERED behaviours. No criterion is DRIFT. TKT-004 and LOG-008 are BLOCKED, CLI-006 and LOG-007 are OPEN, and both OPEN items cite a `questions.md` that does not exist. The run cost about $0.45 on the host meter. I did not time it.

## Scope and surface

The scope is every feature criterion in `cli.md` (CLI-001 to CLI-008), `event-log.md` (LOG-001 to LOG-008), and `tickets.md` (TKT-001 to TKT-013). That makes 29 criteria. The invariants INV-001 to INV-005 were checked only where a feature criterion makes them observable.

- **User:** a support agent in a shell.
- **Surface:** the `ticketdesk` binary, installed with `pip install` into a fresh virtual environment, as `AGENTS.md` says.
- **Environment:** local, on a scratch copy of the repo. No other environment was touched.
- **Evidence logs:** `scratch/evidence.log` and `scratch/evidence2.log`, next to this report.

The specs were new and uncommitted. That did not change the check. The specs say the interface is only the command line, so the `.jsonl` log was read as a surface only where `event-log.md` declares it.

## cli.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| CLI-001 | MATCH | `ticketdesk --log a.jsonl create "Default prio"` | Printed `#2 open Default prio`, exit 0. Listed as `[P3]`. |
| CLI-002 | MATCH | `ticketdesk --log a.jsonl assign 1 dana` | Printed `#1 assigned -> dana`, exit 0. |
| CLI-003 | MATCH | `ticketdesk --log a.jsonl close 1 "Replaced the toner cartridge"` | Printed `#1 closed`, exit 0. |
| CLI-004 | MATCH | `ticketdesk --log a.jsonl list \| cat -A` | `#2 [P2] closed   t2$`. State padded to 8. Empty log printed nothing, exit 0. |
| CLI-005 | MATCH | `ticketdesk --log a.jsonl close 1 "Replaced the toner again"` | stderr `error: ticket 1 is already closed`, stdout empty, exit 2. Also seen for TKT-002, 007, 008, 010, 012. |
| CLI-006 | OPEN | `ticketdesk --log a.jsonl create "bad" --priority P9` | Settled part matches. Exit 1, traceback, last line is the TKT-003 message, no `error:` line. |
| CLI-007 | MATCH | `TICKETDESK_LOG=env.jsonl ticketdesk --log flag.jsonl create "flag"` | Default wrote `tickets.jsonl`. The variable wrote `env.jsonl`. The flag wrote `flag.jsonl` and won. |
| CLI-008 | MATCH | `ticketdesk`, `ticketdesk close abc "long enough note"`, `ticketdesk --help` | Missing subcommand and `abc` exit 2 with a usage line and an error line on stderr. `--help` exit 0. |

## event-log.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| LOG-001 | MATCH | create, assign, close, then a rejected close, then `wc -l a.jsonl` | 3 lines after 3 changes. The rejected close added none. A rejected create (`"   "`) also added none. |
| LOG-002 | MATCH | `cat a.jsonl` | `{"assignee": "amy", "at": ..., "id": 3, "kind": "assigned"}`. Keys sorted. Created and closed events carry the declared extra keys. |
| LOG-003 | MATCH | `date +%s` before and after three writes, then `cat a.jsonl` | `at` was `1794283824.7250292`, between the two `date` readings of `1794283824`. A decimal number. |
| LOG-004 | MATCH | `ticketdesk --log a.jsonl list`, `assign 1 bob`, `create "   "`, then `ls` | No file after each. `create "first"` printed `#1 open first` and made the file. |
| LOG-005 | MATCH | Appended an empty line, spaces, and a tab to a copy of the log, then `list` | Listed `#1 [P2] closed   t1`, exit 0. |
| LOG-006 | MATCH | Appended `not json` to a copy of the log, then `list`, `create`, `assign`, `close` | Each ended with `ValueError: c.jsonl:4: corrupt event: Expecting value: line 1 column 1 (char 0)`. The file kept 4 lines. |
| LOG-007 | OPEN | `ticketdesk --log e.jsonl list` on an `assigned` event for id 5 | Settled part matches. `KeyError: 5` traceback, exit 1. Same for a `closed` event and for `create`. |
| LOG-008 | BLOCKED | `list` on a log with three `assigned` events, the last with the earliest `at` | Listed `#1 [P3] assigned ord`. The output has no assignee, so the last-wins rule is not visible. |

## tickets.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| TKT-001 | MATCH | `create "t2" --priority P2`, `create "t3"` after `#1` | `#2 open t2`, `#3 open t3`. The created event has no assignee or resolution key. |
| TKT-002 | MATCH | `create "   "` and `create ""` | stderr `error: title is required`, exit 2, no new line in the log. |
| TKT-003 | MATCH | `create "bad" --priority P9` and `--priority p1` | Message `unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']`. Log stayed at 1 line. |
| TKT-004 | BLOCKED | none | No command prints or stores a due time. Needs a command or log field that shows it. |
| TKT-005 | MATCH | `assign 3 amy`, then `list` | `#3 [P3] assigned t3`. |
| TKT-006 | MATCH | `assign 1 dana`, `assign 1 erin`, then `cat a.jsonl` | Both `assigned` events stay in the log. State stays `assigned`. |
| TKT-007 | MATCH | `assign 1 "  "` and `assign 1 ""` on an open ticket | stderr `error: assignee is required`, exit 2. |
| TKT-008 | MATCH | `assign 1 bob` after ticket 1 was closed | stderr `error: ticket 1 is closed`, exit 2. |
| TKT-009 | MATCH | `close 2 "  ten chars.  "` on an unassigned ticket | `#2 closed`. Log has a `closed` event. |
| TKT-010 | MATCH | `close 3 "short"`, `"   123456789   "`, `"1234567890"` | First two: `error: resolution note must be at least 10 characters`. Third: `#3 closed`. |
| TKT-011 | MATCH | `close 1 "Replaced the toner again"` on a closed ticket | stderr `error: ticket 1 is already closed`, exit 2. |
| TKT-012 | MATCH | `assign 99 bob` and `close 99 "long enough note"` | stderr `error: no ticket 99`, exit 2, both. |
| TKT-013 | MATCH | `list` after three tickets, one closed, one assigned | Three lines in order 1, 2, 3, closed one included. |

Invariants made observable by these runs. INV-002 held, because earlier lines never changed between runs. INV-003 held, because `create` after all tickets were closed took `#4`. INV-004 held through LOG-006, because the output names file and line. INV-001 held in the narrow sense that the work directory held only the log and no second state file. INV-005 is BLOCKED, because no command accepts an event time to overwrite.

## DRIFT details

None.

## UNCOVERED behaviours

**1. A log that cannot be read or written ends in a traceback and exit 1.**
CLI-005 lists only ticket rules. The specs name no behaviour for these cases.

```
$ ticketdesk --log nodir/x.jsonl create "x"
FileNotFoundError: [Errno 2] No such file or directory: 'nodir/x.jsonl'    (exit 1)
$ ticketdesk --log /tmp list
IsADirectoryError: [Errno 21] Is a directory: '/tmp'    (exit 1)
$ ticketdesk --log ro.jsonl create x      (file mode 444)
PermissionError: [Errno 13] Permission denied: 'ro.jsonl'    (exit 1)
```

The output above shows the last line of each traceback. The full tracebacks are in `evidence2.log`. The nearest criterion is CLI-006, which documents a traceback for one other case only.

**2. A corrupt log ends in a traceback with exit 1.**
LOG-006 says the replay stops "with the message". The message appears only as the last line of a traceback.

```
$ ticketdesk --log c.jsonl list
Traceback (most recent call last):
  ...
ValueError: c.jsonl:4: corrupt event: Expecting value: line 1 column 1 (char 0)
(exit 1)
```

LOG-007 contrasts its output with "the message of LOG-006", which suggests a plain message. The traceback form and the exit code are in no criterion. A reader may count this as DRIFT on LOG-006 instead. I kept it MATCH, because the promised text appears in the output.

**3. Argument errors beyond the two named in CLI-008, and per-subcommand help.**
CLI-008 names a missing subcommand and a non-integer number. The product also handles these.

```
$ ticketdesk --log a.jsonl create
usage: ticketdesk create [-h] [--priority PRIORITY] title
ticketdesk create: error: the following arguments are required: title    (exit 2)
$ ticketdesk --log a.jsonl list extra
ticketdesk: error: unrecognized arguments: extra    (exit 2)
$ ticketdesk create "late log" --log late.jsonl
ticketdesk: error: unrecognized arguments: --log late.jsonl    (exit 2)
$ ticketdesk assign --help
usage: ticketdesk assign [-h] id assignee    (exit 0)
```

The nearest criterion is CLI-008. CLI-007 says `--log` goes before the subcommand, but no criterion says a late `--log` is rejected.

## BLOCKED and OPEN

- **LOG-008 BLOCKED.** The list output has no assignee. A command that prints the assignee would settle whether the last `assigned` event in the file wins.
- **TKT-004 BLOCKED.** No surface shows a due time. A command or a log field that prints it would settle the table of 4, 24, and 72 hours.
- **INV-005 BLOCKED.** No surface lets a user supply an event time. A way to pass `at` would settle whether the store overwrites it.
- **CLI-006 OPEN.** The text says "See `questions.md` item 3 for whether this is a defect." The file `questions.md` is not in the repo, in `docs/`, or anywhere under the repo root. The settled part matched.
- **LOG-007 OPEN.** The same sentence points at `questions.md` item 3. The settled part matched.

## Artifacts

- `scratch/venv/`, the virtual environment with `ticketdesk` installed.
- `scratch/src/`, a copy of the repo without `.git`, used for the install.
- `scratch/work/`, the scratch log files (`a.jsonl` to `f.jsonl`, `sub/`) and capture files.
- `scratch/run.sh`, `scratch/run2.sh`, `scratch/evidence.log`, `scratch/evidence2.log`.

All paths are under `exp8/run-2/`. `git status` in the repo after the run showed only `AGENTS.md` and `docs/` as untracked, as before. The run edited no repo file.

## Assumptions

Nobody was available to answer questions, so the run proceeded on these assumptions.

- The scope is the 29 feature criteria. Invariants are not counted.
- `questions.md` is missing, so the OPEN items stay OPEN.
- The first block of `evidence.log` hit a harness error. The helper `fresh` failed once because no `.jsonl` file existed.
- The last block of `evidence.log`, "list ordering", failed through a quoting error in the script. Its output is not used.
- `evidence2.log` redoes those cases and is the source for the tables above.

## Decision

You decide each UNCOVERED item. Each one either gets a criterion or stays undocumented. You also decide whether the spec or the product supplies the missing part of each OPEN and BLOCKED item. No DRIFT needs a decision.

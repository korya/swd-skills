# Drift report: ticketdesk specs against the product

Of 31 criteria in scope, 23 MATCH, 5 DRIFT, 2 BLOCKED, and 1 OPEN, and 1 behaviour is UNCOVERED.
The DRIFT items are TKT-010, TKT-012, LOG-005, CLI-001, and CLI-006.
The run cost about $0.03 of the $5 budget.

## Scope and surface

- **Spec set:** `docs/product-specs/`. `tickets.md` has TKT-001 to TKT-013 (13 criteria). `event-log.md` has LOG-001 to LOG-009 (9). `cli.md` has CLI-001 to CLI-009 (9).
- **Invariants:** `invariants.md` has INV-001 to INV-005. They are checked only through the feature criteria that make them observable. INV-002 goes through LOG-008, INV-003 through TKT-004, INV-004 through LOG-007, and INV-005 through LOG-004. INV-001 has no criterion that makes it observable alone, so it is not scored.
- **User and surface:** a shell user of the `ticketdesk` command, installed with `pip`. This is a CLI product, so the surface is the built binary in a shell.
- **Environment:** a scratch venv on this Mac, with Python 3.15 as the traceback paths show. The venv holds a copy of the repo's clean working tree at `5b0c398`. The repo was not run in place.
- **Evidence log:** `drift-run/evidence.log` and `drift-run/evidence-rerun.log`, under the scratchpad `exp7/` directory.
- **Assumption:** no one was available to ask. A traceback counts as an error when its last line names the rejected value or the corrupt line.
- CLI-007's TODO tracks that form. TKT-003 and LOG-007 are therefore MATCH on substance, and their form stays OPEN under CLI-007. If "an error" must be a clean message, both become DRIFT.

## Verdicts per spec file

### tickets.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| TKT-001 | MATCH | `create`, `assign`, `close`, `list` | Output shows the states `open`, `assigned`, and `closed`. |
| TKT-002 | MATCH | `create ""`, `create "   "` | `error: title is required`, exit 2. No ticket created. |
| TKT-003 | MATCH (see assumption) | `create "Bad prio" --priority P9`, `--priority p1` | Traceback, exit 1. Last line names the value and lists `P1`, `P2`, `P3`. No ticket created. |
| TKT-004 | MATCH | `create` after tickets 1 and 2, then after a close | New ticket is `#3`. |
| TKT-005 | BLOCKED | `create`, `list`, `--help`, search of all outputs and the log | No surface shows a due time. See BLOCKED. |
| TKT-006 | MATCH | `assign 1 dana`, then `assign 1 erin` | `#1 assigned -> dana`, then `#1 assigned -> erin`. |
| TKT-007 | MATCH | `assign 2 ""`, `assign 2 "   "` | `error: assignee is required`, exit 2. No event appended. |
| TKT-008 | MATCH | `assign 1 frank` on a closed ticket | `error: ticket 1 is closed`, exit 2. No event appended. |
| TKT-009 | BLOCKED | `close 1 "Replaced the toner cartridge"` | `#1 closed`, exit 0. State and resolution observed. The assignee-kept clause is not. |
| TKT-010 | DRIFT | `close 2 short`, `close 2 123456789`, `close 1 abcdefgh` | 5 characters rejected, with "at least 8 characters". 9 and 8 characters accepted. |
| TKT-011 | MATCH | `close 1` a second time | `error: ticket 1 is already closed`, exit 2. The log holds one `closed` event for ticket 1. |
| TKT-012 | DRIFT | `assign 99 x`, `close 99 "A long enough note"` | `error: ticket 99 not found`, exit 2. |
| TKT-013 | MATCH | `list` after closing ticket 1 | Closed ticket 1 is listed first, in ID order. |

### event-log.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| LOG-001 | MATCH | Byte count of the log before and after `list` | 266 bytes both times. `list` appended nothing. |
| LOG-002 | MATCH | Every line of the log | Kinds seen are `created`, `assigned`, and `closed` only. |
| LOG-003 | MATCH | `cat` of the log | `created` has `title` and `priority`. `assigned` has `assignee`. `closed` has `resolution`. |
| LOG-004 | MATCH | `cat` of the log | `at` is epoch seconds as a float, such as `1794325974.72623`. |
| LOG-005 | DRIFT | `cat -A` of the log | Keys are not sorted. Blank lines are ignored, as the spec says. See DRIFT. |
| LOG-006 | MATCH | `list` on a missing path, then `create` on it | `list` printed nothing, exit 0, and created no file. `create` printed `#1` and created the file. |
| LOG-007 | MATCH (see assumption) | `list` and `assign` on a log with `not json` on line 8 | Both stop with a traceback ending in `corrupt.jsonl:8: corrupt event`. Exit 1. No ticket output. |
| LOG-008 | MATCH | Copy of the log, then `close 2`, then a prefix compare | The original lines are byte-identical. |
| LOG-009 | MATCH | `list` run twice on the same log | Identical output both times. |

### cli.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| CLI-001 | DRIFT | `--help`, `frobnicate`, and no subcommand | The product has five subcommands, not four. No subcommand prints usage to stderr and exits 2, as the spec says. See DRIFT. |
| CLI-002 | MATCH | `--log` with and without `TICKETDESK_LOG`, and with neither | The flag wins over the variable. The variable applies when the flag is absent. With neither, `tickets.jsonl` in the working directory is used. |
| CLI-003 | MATCH | `create "Printer on fire" --priority P1`, `create "Wifi down"` | `#1 open Printer on fire`. The second ticket has priority `P3`. |
| CLI-004 | MATCH | `assign 1 dana` | `#1 assigned -> dana`. |
| CLI-005 | MATCH | `close 1 "Replaced the toner cartridge"` | `#1 closed`. |
| CLI-006 | DRIFT | `list` | State is padded to 9 characters, not 8. Empty log prints nothing, which matches. See DRIFT. |
| CLI-007 | OPEN | Ticket-rule errors, plus the two TODO cases | Ticket-rule errors match: `error:` on stderr, exit 2, empty stdout. The two TODO cases fail as the TODO says. See OPEN. |
| CLI-008 | MATCH | Every successful run | Exit 0 and empty stderr. |
| CLI-009 | MATCH | `assign abc dana` | argparse usage error on stderr, exit 2. No event appended. |

## DRIFT details

### TKT-010: resolution note minimum length

Criterion: "A resolution note shorter than 10 characters, after trimming surrounding whitespace, is rejected with the error `resolution note must be at least 10 characters`. The ticket stays in its previous state."

```
$ ticketdesk --log t1.jsonl close 2 short
error: resolution note must be at least 8 characters          (exit 2)
$ ticketdesk --log t1.jsonl close 2 123456789                 (9 characters)
#2 closed                                                     (exit 0)
$ ticketdesk --log t3.jsonl close 1 abcdefgh                  (8 characters)
#1 closed                                                     (exit 0)
```

The product accepts 8- and 9-character notes, which the spec rejects. Most likely cause (high): `ticketdesk/tickets.py:76-77` checks for fewer than 8 characters and its message says 8.

### TKT-012: unknown ticket message

Criterion: "Assigning or closing a ticket ID that does not exist fails with the error `no ticket <id>`."

```
$ ticketdesk --log t1.jsonl assign 99 x
error: ticket 99 not found                                    (exit 2)
```

Most likely cause (high): `ticketdesk/tickets.py:53` builds the message `ticket {id} not found`.

### LOG-005: key order

Criterion: "Each event is one line of JSON with keys sorted alphabetically, ended by a newline."

```
{"kind": "created", "id": 1, "title": "Printer on fire", "priority": "P1", "at": 1794325932.894963}
```

The keys come in the order kind, id, title, priority, at. Most likely cause (high): `ticketdesk/store.py:22` calls `json.dumps` without `sort_keys=True`, and `store.py:20` adds `at` last.

### CLI-001: subcommands

Criterion: "The `ticketdesk` command takes one of four subcommands. They are `create`, `assign`, `close`, and `list`."

```
$ ticketdesk frobnicate
ticketdesk: error: argument cmd: invalid choice: 'frobnicate' (choose from 'create', 'assign', 'close', 'list', 'count')
$ ticketdesk --log t1.jsonl count
3                                                             (exit 0)
```

The cause is in the code: `ticketdesk/cli.py:19` adds `count`, and the spec does not mention it. Whether the spec or the code should change is your decision.

### CLI-006: state padding

Criterion: "Each line is `#<id> [<priority>] <state> <title>` with the state padded to 8 characters."

```
#1 [P3] open      Alpha ticket
#2 [P2] assigned  Beta ticket
```

At 8 characters, `open` takes 5 spaces before the title and `assigned` takes 1. The product uses 6 and 2. Most likely cause (high): `ticketdesk/cli.py:33` formats the state as `{t.state:<9}`.

## OPEN

### CLI-007: ticket-rule errors

The criterion's TODO, quoted: "TODO: two failures do not follow this rule today. An unknown priority (TKT-003) and a corrupt log line (LOG-007) escape as a Python traceback with exit code 1."

```
$ ticketdesk --log t1.jsonl create "Bad prio" --priority P9
...
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']     (exit 1)
$ ticketdesk --log corrupt.jsonl list
...
ValueError: corrupt.jsonl:8: corrupt event: Expecting value: line 1 column 1 (char 0)     (exit 1)
```

The settled part of CLI-007 passes, so this is not DRIFT. The TODO is open, and AGENTS.md says it needs your confirmation.

## BLOCKED

- **TKT-005, due time.** The observation that would settle it is a command or output line that shows a ticket's due time. Tried: `create`, `list`, `assign`, `close`, `--help`, and a search of all outputs and the log. The log has no due field. The only text matching "due" is inside tracebacks.
- **TKT-009, assignee kept after close.** The observation that would settle it is a command that shows a ticket's assignee after it closes. `list` shows only state and title. `assign` on a closed ticket is refused with `ticket 1 is closed`, which shows no assignee.

## UNCOVERED

### `-h, --help`

`ticketdesk --help` (exit 0) prints the usage line and the option `--log LOG  path of the event log`. No criterion describes the help output. The nearest criterion is CLI-001, which covers only the usage line printed with no subcommand. The impact is low. You decide whether it needs a criterion.

`count` is not listed here. It is a DRIFT against CLI-001, shown above.

## Artifacts

- `drift-run/venv/`: scratch venv with the installed package.
- `drift-run/src/`: copy of the repo used for the install.
- `drift-run/work/` and `drift-run/work2/`: test logs, including `t1.jsonl`, `t3.jsonl`, `corrupt.jsonl`, `blank.jsonl`, and `tickets.jsonl`.
- `drift-run/run_cases.sh`: the runner script.
- `drift-run/evidence.log` and `drift-run/evidence-rerun.log`: the evidence logs.
- The repo was not changed. No file in it was written.

## Decision

You now decide, for each DRIFT, whether the spec or the product changes:

- TKT-010: the threshold is 8 or 10, and the 8- and 9-character notes need a ruling.
- TKT-012: the message is `no ticket <id>` or `ticket <id> not found`.
- LOG-005: sort the keys, or drop the rule from the spec.
- CLI-001: add `count` to the spec, or remove it from the product.
- CLI-006: pad the state to 8 or 9 characters.

For the UNCOVERED `--help` output, you decide whether it gets a criterion.

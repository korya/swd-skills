# Drift report: ticketdesk 0.3.0

Of 31 criteria, 22 MATCH, 5 DRIFT, 3 are BLOCKED, 1 is OPEN, and 3 behaviours are UNCOVERED. The DRIFT items are CLI-001, CLI-006, TKT-010, TKT-012, and LOG-005. The run took a few minutes and cost about $0.38 in model usage.

## Scope and surface

The scope is every `PREFIX-NNN` criterion in `docs/product-specs/`: 9 `CLI`, 13 `TKT`, 9 `LOG`. The `INV` file is checked only where a feature criterion makes an invariant observable.

- **User:** a shell user of the `ticketdesk` command.
- **Surface:** the `ticketdesk` binary, installed with `pip install` into a fresh virtual environment from a copy of the repo. The event log file is also a surface, because `event-log.md` declares it one.
- **Environment:** local, Python 3.15.2 on macOS. Every log file is a scratch file.
- **Assumption:** nobody was available to answer questions. I proceeded on the default scope and treated the open TODO under CLI-007 as unconfirmed.
- **Evidence logs:** `scratch/evidence.log`, `scratch/evidence3.log`, and `scratch/evidence4.log`, in the directory next to this report. `evidence2.log` holds a failed batch caused by a quoting mistake in my script. It gives no verdicts.

## CLI (`cli.md`)

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| CLI-001 | DRIFT | `ticketdesk --help`; `ticketdesk`; `ticketdesk bogus` | No subcommand and unknown subcommand: usage on stderr, exit 2. Help lists five subcommands, not four. See below. |
| CLI-002 | MATCH | `TICKETDESK_LOG=env.jsonl ticketdesk --log opt.jsonl list`, then the same without `--log`, then with neither | `--log` file used first, env file second, `tickets.jsonl` in the current directory last |
| CLI-003 | MATCH | `ticketdesk --log=b.jsonl create Alpha --priority P1`; `create Bravo` | `#1 open Alpha`; `#2 open Bravo`; list shows Bravo as `[P3]` |
| CLI-004 | MATCH | `ticketdesk --log=a.jsonl assign 1 dana` | `#1 assigned -> dana` |
| CLI-005 | MATCH | `ticketdesk --log=a.jsonl close 1 "Replaced the toner cartridge"` | `#1 closed` |
| CLI-006 | DRIFT | `ticketdesk --log=b.jsonl list` | State column is wider than 8. See below. Empty log prints nothing, as promised. |
| CLI-007 | OPEN | Errors for TKT-002, 007, 008, 010, 011 | The settled part holds: `error: <message>` on stderr, nothing on stdout, exit 2 |
| CLI-008 | MATCH | `ticketdesk --log=b.jsonl list` under `bash`, stderr sent to a file | Exit 0, stderr file has 0 bytes |
| CLI-009 | MATCH | `ticketdesk --log=a.jsonl assign abc x`; `close xyz "long enough note"` | `argument id: invalid int value`, exit 2, event count unchanged |

## Tickets (`tickets.md`)

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| TKT-001 | MATCH | `create`, `assign`, `close` on one ticket | Outputs show `open`, `assigned`, `closed` |
| TKT-002 | MATCH | `create ""`; `create "   "` | `error: title is required`, exit 2, no event appended |
| TKT-003 | MATCH | `create Bad --priority P9`; `create lower --priority p1` | Error names `'P9'` and `['P1', 'P2', 'P3']`. No ticket created, log unchanged at 4 lines. The error is a traceback, see CLI-007. |
| TKT-004 | MATCH | Three creates, one close between | IDs 1, 2, 3 |
| TKT-005 | BLOCKED | none | No command or log field shows a due time |
| TKT-006 | MATCH | `assign 1 dana`, then `assign 1 erin` | `#1 assigned -> dana`, then `#1 assigned -> erin` |
| TKT-007 | MATCH | `assign 1 "  "` | `error: assignee is required`, exit 2 |
| TKT-008 | MATCH | `assign 1 zed` after close | `error: ticket 1 is closed`, exit 2 |
| TKT-009 | BLOCKED | `assign 1 dana`, `close 1 "resolution long enough"`, `list`, `cat k.jsonl` | State `closed` and the resolution appear in the log. No command shows the assignee after close. |
| TKT-010 | DRIFT | `close 1 1234567`; `close 1 12345678` | Threshold is 8, not 10. See below. |
| TKT-011 | MATCH | `close 1 "Replaced the toner cartridge again"` after close | `error: ticket 1 is already closed`, exit 2, log holds one `closed` event for ticket 1 |
| TKT-012 | DRIFT | `assign 99 x`; `close 99 long-enough-note` | Message is `ticket 99 not found`. See below. |
| TKT-013 | MATCH | `list` with tickets 1 and 2 closed and 3 open | Three lines in ID order, closed tickets included |

## Event log (`event-log.md`)

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| LOG-001 | MATCH | Seven successful writes, then `list` twice | Log has seven lines. `md5sum` of the log is identical before and after two `list` runs. |
| LOG-002 | MATCH | `cat a.jsonl` | Kinds seen: `created`, `assigned`, `closed` |
| LOG-003 | MATCH | `cat k.jsonl` | `created` has `title`, `priority`. `assigned` has `assignee`. `closed` has `resolution`. All have `kind`, `id`, `at`. |
| LOG-004 | MATCH | `cat b.jsonl` | `at` is a float near 1794282280, seconds since the epoch |
| LOG-005 | DRIFT | `head -1 b.jsonl` | Keys are not sorted. See below. Blank lines are ignored: a blank line appended to `a.jsonl`, then `list` printed all tickets. |
| LOG-006 | MATCH | `list`, then `create "First one"` on a missing `m.jsonl` | `list` prints nothing and creates no file. `create` prints `#1 open First one` and creates the file. |
| LOG-007 | MATCH | Line 2 of `c.jsonl` replaced with `garbage`; `list`, `create x`, `assign 1 q` | Each fails with `ValueError: c.jsonl:2: corrupt event: ...`. File unchanged (same `md5sum`). The failure is a traceback with exit 1, see CLI-007. |
| LOG-008 | MATCH | `cat a.jsonl` after each write | Earlier lines stay identical as later lines are added |
| LOG-009 | BLOCKED | `list` run twice on `b.jsonl` | Output is identical, but assignees, resolutions, and due times are not shown by any command |

## DRIFT details

### CLI-001: a fifth subcommand exists

Spec: "The `ticketdesk` command takes one of four subcommands. They are `create`, `assign`, `close`, and `list`."

```
$ ticketdesk --help
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list,count} ...
```

The product accepts `count`. The behaviour the spec states for no subcommand and for an unknown subcommand holds: usage on stderr, exit 2. Most likely cause: `cli.py` registers `sub.add_parser("count")` and the spec was not updated.

### CLI-006: the state column is 9 wide, not 8

Spec: "Each line is `#<id> [<priority>] <state> <title>` with the state padded to 8 characters."

```
$ ticketdesk --log=b.jsonl list
#1 [P1] closed    Alpha
#2 [P3] closed    Bravo
```

`closed` is followed by 4 spaces. A pad of 8 plus one separator space gives 3. Most likely cause: the format string in `cli.py` uses `{t.state:<9}`.

### TKT-010: the minimum note length is 8, not 10

Spec: "A resolution note shorter than 10 characters, after trimming surrounding whitespace, is rejected with the error `resolution note must be at least 10 characters`."

```
$ ticketdesk --log=b.jsonl close 1 1234567
error: resolution note must be at least 8 characters
[exit 2]
$ ticketdesk --log=b.jsonl close 1 12345678
#1 closed
[exit 0]
```

An 8-character note closes the ticket, and the message says 8. Most likely cause: a minimum constant of 8 in `tickets.py`.

### TKT-012: the unknown-ticket message differs

Spec: "Assigning or closing a ticket ID that does not exist fails with the error `no ticket <id>`."

```
$ ticketdesk --log=f.jsonl assign 99 x
error: ticket 99 not found
[exit 2]
$ ticketdesk --log=f.jsonl close 99 long-enough-note
error: ticket 99 not found
[exit 2]
```

### LOG-005: keys are not sorted

Spec: "Each event is one line of JSON with keys sorted alphabetically, ended by a newline."

```
$ head -1 b.jsonl
{"kind": "created", "id": 1, "title": "Alpha", "priority": "P1", "at": 1794282280.485523}
```

The key order is `kind`, `id`, `title`, `priority`, `at`. Sorted order would start with `at`. Most likely cause: the store writes `json.dumps` without `sort_keys=True`.

## UNCOVERED behaviours

### The `count` subcommand

```
$ ticketdesk --log=f.jsonl count
1
[exit 0]
```

It prints the number of tickets, closed ones included, and exits 0. No criterion describes it. The nearest is CLI-001, which lists four subcommands.

### `--log` must come before the subcommand

```
$ ticketdesk list --log=f.jsonl
ticketdesk: error: unrecognized arguments: --log=f.jsonl
[exit 2]
```

CLI-002 names the `--log` option but not its position.

### Help output

`ticketdesk --help` prints usage and exits 0 (see the CLI-001 run). No criterion covers `-h` or `--help`.

## BLOCKED and OPEN

- **TKT-005 (BLOCKED):** a command or log field that prints the due time of a ticket would settle it.
- **TKT-009 (BLOCKED):** a command that prints the assignee of a closed ticket would settle it.
- **LOG-009 (BLOCKED):** a command that prints assignee, resolution, and due time for each ticket would settle it.
- **CLI-007 (OPEN):** "TODO: two failures do not follow this rule today. An unknown priority (TKT-003) and a corrupt log line (LOG-007) escape as a Python traceback with exit code 1." Observed: both still do (`create Bad --priority P9` and `list` on `c.jsonl` exit 1 with a traceback). The settled part of the criterion holds.

## Artifacts

Everything is under `scratch/`, next to this report. The repo has zero modified files (`git status --short` printed nothing).

- `scratch/src/`: a copy of the repo, without `.git`, used for installing.
- `scratch/venv/`: the virtual environment holding the installed `ticketdesk`.
- `scratch/work/`: log files `a`, `b`, `c`, `e`, `f`, `k`, `m`, `opt`, `env`, and `tickets` (`.jsonl`).
- `scratch/evidence.log`, `evidence2.log`, `evidence3.log`, `evidence4.log`.

## Decision

You decide now. For each DRIFT, say whether the spec or the product changes. For each UNCOVERED item, say whether it gets a criterion.

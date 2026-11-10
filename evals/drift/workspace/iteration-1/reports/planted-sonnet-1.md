# Drift report: ticketdesk 0.3.0

The run found 6 DRIFT among 31 criteria: 21 MATCH, 6 DRIFT, 3 BLOCKED, 1 OPEN, and 2 UNCOVERED behaviours.

The DRIFT items are CLI-001, CLI-006, TKT-003, TKT-010, TKT-012, and LOG-005. The run took about 10 minutes and cost about $0.32 in model usage.

## Scope and surface

The scope is every feature criterion in `docs/product-specs/cli.md` (9), `tickets.md` (13), and `event-log.md` (9). The INV items in `invariants.md` are checked only where a feature criterion makes them observable.

Assumption: nobody could confirm the scope or the environment, so I took the default scope and a local scratch environment.

- User: a shell user of the `ticketdesk` command.
- Surface: `python3 -m ticketdesk.cli`, the form `AGENTS.md` documents under "Running the project". The `ticketdesk` binary is not installed on this machine (`which ticketdesk` printed `ticketdesk not found`).
- Environment: local, Python 3.15.2, scratch directory `/tmp/drift-scratch`, logs written there only.
- Evidence logs: `/tmp/drift-scratch/evidence.log`, `/tmp/drift-scratch/evidence-2.log`. The script is `/tmp/drift-scratch/run.sh`.

In the tables, `td` means `python3 -m ticketdesk.cli --log <file>`.

## cli.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| CLI-001 | DRIFT | `td --help` | Lists `{create,assign,close,list,count}`. Five subcommands, spec says four. No subcommand and unknown subcommand both exit 2 with usage on stderr. |
| CLI-002 | MATCH | `TICKETDESK_LOG=e.jsonl td list`, then with `--log b.jsonl`, then `create` in an empty directory | Env var read. `--log` wins over the env var. Without both, `tickets.jsonl` appears in the current directory. |
| CLI-003 | MATCH | `td create "Printer on fire" --priority P1`, `td create "Wifi down"` | `#1 open Printer on fire`. The default priority shows as `[P3]` in `list`. |
| CLI-004 | MATCH | `td assign 1 dana` | `#1 assigned -> dana` |
| CLI-005 | MATCH | `td close 1 "Replaced the toner cartridge"` | `#1 closed` |
| CLI-006 | DRIFT | `td list` | State is padded to 9 characters, not 8. See details. Empty log prints nothing. IDs ascend. |
| CLI-007 | OPEN | `td assign 2 ""`, `td close 1 short`, `td create x --priority P9` | Rule errors print `error: <message>` to stderr, stdout empty, exit 2. Settled part MATCH. Priority and corrupt-log cases exit 1 with a traceback. |
| CLI-008 | MATCH | `td list`, create, assign, close | Exit 0, stderr empty on every success. |
| CLI-009 | MATCH | `td assign abc bob`, `td close abc "Replaced the toner"` | `argument id: invalid int value: 'abc'`, exit 2. Log stayed at 6 lines. |

## tickets.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| TKT-001 | MATCH | `td create`, `assign`, `close`, then `td list` | States `open`, `assigned`, `closed` shown. New ticket is `open`. |
| TKT-002 | MATCH | `td create ""`, `td create "   "` | `error: title is required`, exit 2. Log line count unchanged. |
| TKT-003 | DRIFT | `td create x --priority P9` | Traceback, exit 1. See details. |
| TKT-004 | MATCH | Three creates, then a create after closing ticket 1 | IDs 1, 2, 3. After closing ticket 1, the next create got ID 2 in a fresh log. No ID reused. |
| TKT-005 | BLOCKED | `td list`, `td --help`, reading the log | No command prints a due time and the log has no due field. Settling needs a command that prints the due time. |
| TKT-006 | MATCH | `td assign 1 dana`, `td assign 1 eli`, `td list` | `#1 assigned -> eli`, state `assigned`. |
| TKT-007 | MATCH | `td assign 2 ""`, `td assign 2 "   "` | `error: assignee is required`, exit 2. Ticket 2 still `open`. |
| TKT-008 | MATCH | `td assign 1 bob` on a closed ticket | `error: ticket 1 is closed`, exit 2. |
| TKT-009 | BLOCKED | `td assign 1 dana`, `td close 1 "Replaced the toner cartridge"` | State `closed` and the note appear in the log. No command prints the assignee. Settling needs a command that prints the assignee of a ticket. |
| TKT-010 | DRIFT | `td close 1 "123456789"` | A 9-character note is accepted. See details. |
| TKT-011 | MATCH | `td close 1 "Replaced the toner cartridge"` twice | `error: ticket 1 is already closed`, exit 2. No new log line. |
| TKT-012 | DRIFT | `td assign 99 bob` | `error: ticket 99 not found`. See details. |
| TKT-013 | MATCH | `td create B`, `td create A`, `td list` | Lines in ID order, closed tickets included. |

## event-log.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| LOG-001 | MATCH | create, assign, close, list, with `wc -l` after each | Each change added one line. `list` and rejected commands added none. |
| LOG-002 | MATCH | `cat` of the log after create, assign, close | Kinds seen: `created`, `assigned`, `closed`. |
| LOG-003 | MATCH | `cat d.jsonl` | `created` has title and priority, `assigned` has assignee, `closed` has resolution, all have `kind`, `id`, `at`. |
| LOG-004 | MATCH | `cat a.jsonl`, `date +%s` | `at` is `1794282241.62786`, the epoch time of the run, as a float. |
| LOG-005 | DRIFT | `cat a.jsonl` | Keys are not sorted. See details. Blank lines are ignored on replay. Lines end with a newline. |
| LOG-006 | MATCH | `td --log nope.jsonl list`, then `create "first"` | `list` prints nothing and creates no file. The create prints `#1 open first` and creates the file. |
| LOG-007 | MATCH | `td --log c.jsonl list`, a log with `not json` on line 2 | Last line of stderr: `ValueError: c.jsonl:2: corrupt event: Expecting value: line 1 column 1 (char 0)`. Path, line, and `corrupt event` are present. Stdout empty. It arrives as a traceback, see CLI-007. |
| LOG-008 | MATCH | `cat d.jsonl` after assign and close | Earlier lines unchanged, new lines appended at the end. |
| LOG-009 | BLOCKED | `td list` twice on `d.jsonl` | States are identical across runs. Assignees, resolutions, and due times are not printed by any command. Settling needs commands that print them. |

## DRIFT details

### CLI-001

Spec: "The `ticketdesk` command takes one of four subcommands. They are `create`, `assign`, `close`, and `list`."

```
$ ticketdesk --help
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list,count} ...
```

Most likely cause (likelihood only): a `count` subcommand was added in `cli.py` without a spec update.

### CLI-006

Spec: "Each line is `#<id> [<priority>] <state> <title>` with the state padded to 8 characters."

```
$ ticketdesk --log a.jsonl list
#1 [P1] assigned  Printer on fire
#2 [P3] open      Wifi down
```

The state column is 9 characters wide (`assigned` plus one space), so `assigned` is followed by two spaces. With a width of 8 it would be followed by one.

Most likely cause: the format string in `cli.py` uses `{t.state:<9}`.

### TKT-003

Spec: "Any other priority fails with an error that names the rejected value and the allowed values."

```
$ ticketdesk --log f.jsonl create x --priority P9
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
[rc=1, preceded by a full Python traceback]
```

The message names the value and the allowed values and no ticket is created. The failure is a traceback with exit 1. `p1` in lower case fails the same way. TKT-003 does not state an exit code or a format. CLI-007 covers that and carries the open TODO, so this item depends on the user's answer there.

### TKT-010

Spec: "A resolution note shorter than 10 characters, after trimming surrounding whitespace, is rejected with the error `resolution note must be at least 10 characters`."

```
$ ticketdesk --log f.jsonl close 1 "123456789"
#1 closed
$ ticketdesk --log a.jsonl close 1 short
error: resolution note must be at least 8 characters
```

A 9-character note is accepted, and a 5-character note is rejected with "at least 8". A 12345678 note also closed ticket 2.

Most likely cause: the minimum in `tickets.py` is 8, not 10.

### TKT-012

Spec: "Assigning or closing a ticket ID that does not exist fails with the error `no ticket <id>`."

```
$ ticketdesk --log a.jsonl assign 99 bob
error: ticket 99 not found
```

`close 99 ...` prints the same. Exit code is 2.

### LOG-005

Spec: "Each event is one line of JSON with keys sorted alphabetically, ended by a newline."

```
$ cat a.jsonl
{"kind": "created", "id": 1, "title": "Printer on fire", "priority": "P1", "at": 1794282241.62786}
```

The keys appear in insertion order (`kind`, `id`, `title`, `priority`, `at`). Sorted order would be `at`, `id`, `kind`, `priority`, `title`.

Most likely cause: `store.py` calls `json.dumps` without `sort_keys=True`.

## UNCOVERED behaviours

### The `count` subcommand

`ticketdesk count` prints the number of tickets. It reads the log and counts closed tickets too.

```
$ ticketdesk --log a.jsonl count
3
$ ticketdesk --log nope.jsonl count
1
$ ticketdesk --log c.jsonl count     (corrupt line 2)
[traceback, rc=1]
```

Nearest criteria: CLI-001 (lists four subcommands) and CLI-006 (listing).

The `-h` and `--help` options are also not covered by any criterion. The `--log` option is covered by CLI-002, but its help text and `-h` are not. Each subcommand also answers `-h`.

## BLOCKED and OPEN

- TKT-005 BLOCKED: needs a command or log field that shows the due time of a ticket.
- TKT-009 BLOCKED: needs a command that prints the assignee of a closed ticket.
- LOG-009 BLOCKED: needs commands that print assignee, resolution, and due time.
- CLI-007 OPEN: "TODO: two failures do not follow this rule today. An unknown priority (TKT-003) and a corrupt log line (LOG-007) escape as a Python traceback with exit code 1." The run reproduced both. The settled part (rule errors, exit 2, empty stdout) matched for TKT-002, 007, 008, 010, 011, and 012.

## Artifacts

- `/tmp/drift-scratch/`: scratch logs `a.jsonl`, `b.jsonl`, `bl.jsonl`, `c.jsonl`, `d.jsonl`, `e.jsonl`, `f.jsonl`, `nope.jsonl`, and `cw/tickets.jsonl`.
- `/tmp/drift-scratch/evidence.log`, `evidence-2.log`, `run.sh`, plus `o.txt`, `e.txt`, `o2.txt`, `e2.txt`.
- No file in the repo changed. `git status --short` printed nothing after the run. Bytecode writing was disabled.

## Decision

You decide, per DRIFT, whether the spec or the product changes. You also decide, per UNCOVERED item, whether it gets a criterion.

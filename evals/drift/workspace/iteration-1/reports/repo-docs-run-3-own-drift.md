# Drift report: ticketdesk 0.3.0 against TKT and LOG

The 24 criteria in scope end in 23 MATCH, 1 DRIFT, 0 BLOCKED, and 0 OPEN, with 9 UNCOVERED behaviours. The DRIFT is TKT-013. The commands ran over 4 minutes, and the host reports no money cost.

## Scope and surface

The scope is every feature criterion in two spec files, 24 criteria in all. `docs/product-specs/tickets.md` holds TKT-001 to TKT-015. `docs/product-specs/event-log.md` holds LOG-001 to LOG-009. Invariants were checked only where one of these criteria makes them observable.

The user is a support agent at a zsh shell who runs the installed `ticketdesk` binary. The log file is part of the surface, because the event-log spec declares it one. The environment is a local scratch directory, so mutations were allowed.

Every command and its full output is in the evidence log at `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/01058b7d-e98e-4d3f-a81c-e8ba15a8c683/scratchpad/exp8/run-3/drift-scratch/evidence.log`. In this report, `ticketdesk` stands for `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/01058b7d-e98e-4d3f-a81c-e8ba15a8c683/scratchpad/exp8/run-3/survey/venv/bin/ticketdesk`, and file paths are relative to the scratch directory `drift-scratch`. The evidence log shows each command with its full paths. The case list written before the run is `drift-scratch/cases.md`.

## tickets.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| TKT-001 | MATCH | `ticketdesk --log tkt.jsonl create "Printer on fire"`, then `list` | stdout `#1 open Printer on fire`, exit 0. `list` shows `#1 [P3] open     Printer on fire`. |
| TKT-002 | MATCH | `create ""` and `create "   "` on `tkt.jsonl` | stderr `error: title is required`, empty stdout, exit 2 both times. `list` unchanged. |
| TKT-003 | MATCH | `create "P1 ticket" --priority P1`, same for P2 and P3, then `create "default prio"`, then `list` | `list` shows `[P1]`, `[P2]`, `[P3]` and `[P3]` for the one without the option. |
| TKT-004 | MATCH | `create "bad prio" --priority P9` and `--priority p1` | Traceback on stderr, exit 1. Last lines `ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']` and the same with `'p1'`. `list` unchanged. |
| TKT-005 | MATCH | Fresh log: `create` gives `#1`. Later `create "sixth"`, `close 6 "closed before next create"`, `create "seventh"` | `#6 open sixth`, `#6 closed`, `#7 open seventh`. |
| TKT-006 | MATCH | `assign 1 dana` on an open ticket, then `assign 1 bob`, then `list` | `#1 assigned -> dana`, `#1 assigned -> bob`, exit 0 both. `list` shows `#1 [P3] assigned Printer on fire`. |
| TKT-007 | MATCH | `assign 2 ""`, `assign 2 "   "`, and `assign 3 "   "` on `log.jsonl` with a checksum | stderr `error: assignee is required`, exit 2. Log sha256 identical before and after. |
| TKT-008 | MATCH | `assign 2 dana` after `close 2 ...` | stderr `error: ticket 2 is closed`, exit 2, log unchanged. |
| TKT-009 | MATCH | `close 2 "Replaced the toner cartridge"` on an open unassigned ticket, `close 1 "Rebooted the printer twice"` on an assigned one | `#2 closed`, `#1 closed`, exit 0. `list` shows both as `closed`. |
| TKT-010 | MATCH | `close 3 "123456789"`, `close 3 "   123456789   "`, `close 4 "  1234567890  "`, `close 3 "1234567890"` | The two 9-character notes give `error: resolution note must be at least 10 characters`, exit 2. The two 10-character notes give `#4 closed` and `#3 closed`. |
| TKT-011 | MATCH | `close 2 "Closing it again now"` on the closed ticket 2 | stderr `error: ticket 2 is already closed`, exit 2, log unchanged. |
| TKT-012 | MATCH | `assign 99 dana`, `close 99 "Ten chars!!"`, `assign abc dana`, `close 1.5 "Ten chars!!"` | `error: no ticket 99` twice, exit 2. The last two print `usage: ticketdesk assign [-h] id assignee` and `ticketdesk assign: error: argument id: invalid int value: 'abc'`, same shape for `close`, exit 2. |
| TKT-013 | DRIFT | `list` on `tkt.jsonl` with 7 tickets, `list` on `missing.jsonl`, and `create` with a title that holds a newline, then `list` | The 7-ticket list and the empty list match. A title with a newline prints as two lines. See the DRIFT block. |
| TKT-014 | MATCH | The TKT-006, TKT-008, TKT-009, and TKT-011 runs | open to assigned, assigned to assigned, open to closed, and assigned to closed all succeed. Both moves out of closed are refused. |
| TKT-015 | MATCH | The refusals of TKT-002, 007, 008, 010, 011, and 012 on `log.jsonl`, each with a checksum before and after | Each prints one stderr line that starts with `error: `, nothing on stdout, exit 2. The log keeps the same line count, byte count, and sha256. |

## event-log.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| LOG-001 | MATCH | In the empty directory `cwd1` with `TICKETDESK_LOG` unset: `ticketdesk list`, `ls -A`, `ticketdesk create "default location"`, `ls -A` | `list` prints nothing, exit 0, directory still empty. After `create`, `ls -A` shows `tickets.jsonl`. |
| LOG-002 | MATCH | `TICKETDESK_LOG=envlog.jsonl ticketdesk create "via env var"`, then the same env with `--log optlog.jsonl create ...` | `envlog.jsonl` holds the first event. `optlog.jsonl` holds the second and `envlog.jsonl` is unchanged. Both files were created by their first command. |
| LOG-003 | MATCH | `cat log.jsonl` after create, assign, close, and a check of each line with `python3 -I` | Six lines, each one JSON object with sorted keys. Each has `at` as a number near the current time, `id`, and `kind` in created, assigned, closed. |
| LOG-004 | MATCH | `cat log.jsonl` after `create "  padded   title  " --priority P2`, `assign 2 "  dana  "`, `close 2 "   note with  spaces   "` | The created line has `priority` and `title`, the assigned line has `assignee`, the closed line has `resolution`. Each value keeps its whitespace. |
| LOG-005 | MATCH | create, assign, close, and list on `log.jsonl`, with line count, byte count, and a prefix compare around each | Each of the three adds one line. The old bytes stay a prefix of the new file. `list` leaves the file identical. |
| LOG-006 | MATCH | Eight refusals on `log.jsonl`, including the TKT-004 error, with a checksum around each. Four refusals and `list` on `missing.jsonl` | Same line count, byte count, and sha256 after every refusal. `missing.jsonl` still absent, `ls` reports `No such file or directory`. |
| LOG-007 | MATCH | `printf 'this is not json\n' >> corrupt.jsonl`, then `list`, `create`, `assign 3 dana`, `close 3 ...` on it | Each exits 1 with no stdout. Last stderr line `ValueError: <full path>/corrupt.jsonl:8: corrupt event: Expecting value: line 1 column 1 (char 0)`. The file checksum is unchanged. |
| LOG-008 | MATCH | `blank.jsonl` built from `log.jsonl` with an empty line after line 1 and a line of spaces and a tab after line 4, then `list` | The same three lines as `list` on `log.jsonl`. A later `create` appends `#4`. |
| LOG-009 | MATCH | `cp log.jsonl copy.jsonl`, `cmp`, then `list` on both. The same with `tkt.jsonl` | `cmp` is silent. Both `list` outputs are identical. |

## DRIFT details

### TKT-013: a title with a newline prints as two lines

The criterion says: "`ticketdesk list` prints one line per ticket, in ascending ID order, closed tickets included, and exits with code 0."

Fresh log, two commands:

```text
$ ticketdesk --log fresh-newline.jsonl create $'line one\nline two'
#1 open line one
line two
$ ticketdesk --log fresh-newline.jsonl list
#1 [P3] open     line one
line two
$ ticketdesk --log fresh-newline.jsonl list | wc -l
2
```

Both commands exit 0. The ticket is one record, and `list` prints two lines for it. The log line stores the title as `"line one\nline two"`. Most likely cause: the title is printed as given, and no criterion says a newline in a title is refused or transformed. The two cases derived from the criterion text, a 7-ticket list and an empty list, matched.

## UNCOVERED behaviours

### 1. Help output

No criterion describes `--help`. The top command and each subcommand answer it with exit 0. `--priority PRIORITY` carries no description, so the allowed values and the default are absent. The `--log` help does not name `TICKETDESK_LOG` or `tickets.jsonl`. There is no `--version` option.

```text
$ ticketdesk --help
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...

positional arguments:
  {create,assign,close,list}

options:
  -h, --help            show this help message and exit
  --log LOG             path of the event log
$ ticketdesk create --help
usage: ticketdesk create [-h] [--priority PRIORITY] title

positional arguments:
  title

options:
  -h, --help           show this help message and exit
  --priority PRIORITY
```

### 2. Argument errors print a two-line usage message

Argument errors print a usage line and an error line on stderr, exit 2, and leave the log unchanged. That covers a missing subcommand, an unknown subcommand, a missing or extra argument, and an option without a value. The nearest criterion is TKT-012, which names only a non-integer ID. The one-line `error: <reason>` shape of TKT-015 does not describe these.

```text
$ ticketdesk
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...
ticketdesk: error: the following arguments are required: cmd
$ ticketdesk --log log.jsonl frobnicate
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...
ticketdesk: error: argument cmd: invalid choice: 'frobnicate' (choose from 'create', 'assign', 'close', 'list')
$ ticketdesk --log log.jsonl create a b
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...
ticketdesk: error: unrecognized arguments: b
```

### 3. An empty `TICKETDESK_LOG` ends in a traceback

With the variable set to an empty string, `list` exits 1 with a traceback. The nearest criterion is LOG-002.

```text
$ env TICKETDESK_LOG= ticketdesk list
Traceback (most recent call last):
  ...
IsADirectoryError: [Errno 21] Is a directory: '.'
```

### 4. `--log` that names a directory ends in a traceback

`list` and `create` both exit 1 with a traceback whose last line is `IsADirectoryError: [Errno 21] Is a directory: '<path>/adir'`. The nearest criterion is LOG-002.

```text
$ ticketdesk --log adir create "into a directory"
Traceback (most recent call last):
  ...
IsADirectoryError: [Errno 21] Is a directory: '<full path>/adir'
```

### 5. `--log` under a missing directory

`list` prints nothing and exits 0. `create` exits 1 with a traceback and creates no file. The nearest criterion is LOG-002, "A missing file at either path is created by the first successful command."

```text
$ ticketdesk --log nope/x.jsonl list
$ ticketdesk --log nope/x.jsonl create "missing parent dir"
Traceback (most recent call last):
  ...
FileNotFoundError: [Errno 2] No such file or directory: '<full path>/nope/x.jsonl'
```

### 6. A valid JSON line that is not an event ends in a different traceback

A line that is a JSON array, or a JSON object without `kind`, makes every command exit 1 with a traceback. The last line is not the `corrupt event` shape of LOG-007, and it names neither the file nor the line number. The log is unchanged. The nearest criterion is LOG-007, which covers only lines that are not valid JSON.

```text
$ cat fresh-array.jsonl
{"at": 1794286522.972249, "id": 1, "kind": "created", "priority": "P3", "title": "Printer on fire"}
[1, 2, 3]
$ ticketdesk --log fresh-array.jsonl list
Traceback (most recent call last):
  ...
TypeError: list indices must be integers or slices, not str
$ cat fresh-nokind.jsonl
{"at": 1794286523.104249, "id": 1, "kind": "created", "priority": "P3", "title": "Printer on fire"}
{"at": 1.0, "id": 1}
$ ticketdesk --log fresh-nokind.jsonl list
Traceback (most recent call last):
  ...
KeyError: 'kind'
```

### 7. An event with an unknown `kind` is ignored

A JSON object whose `kind` is outside created, assigned, closed is skipped. `list` prints the other tickets and exits 0. The nearest criteria are LOG-003, which lists the three kinds, and INV-004, which says no command skips a line.

```text
$ cat fresh-badkind.jsonl
{"at": 1794286522.849097, "id": 1, "kind": "created", "priority": "P3", "title": "Printer on fire"}
{"at": 1.0, "id": 1, "kind": "exploded"}
$ ticketdesk --log fresh-badkind.jsonl list
#1 [P3] open     Printer on fire
```

### 8. A closed stdout pipe ends in exit 120

When the reader of `list` closes early, the command prints a `BrokenPipeError` on stderr and exits 120. No criterion covers it.

```text
$ bash -c 'ticketdesk --log fresh-pipe.jsonl list | true; echo exit=${PIPESTATUS[0]}'
Exception ignored while flushing sys.stdout:
BrokenPipeError: [Errno 32] Broken pipe
exit=120
```

### 9. Non-ASCII text is written to the log as escapes

A title or an assignee with non-ASCII characters is stored as `\uXXXX` escapes. The JSON value decodes to the original text, and `list` prints the original text. A plain `grep` for the text on the file finds nothing. The nearest criterion is LOG-004, "Each value is stored exactly as given on the command line."

```text
$ ticketdesk --log fresh-unicode.jsonl create "Zoë"
#1 open Zoë
$ cat fresh-unicode.jsonl
{"at": 1794286523.222993, "id": 1, "kind": "created", "priority": "P3", "title": "Zoë"}
$ grep -c "Zoë" fresh-unicode.jsonl
0
```

## BLOCKED and OPEN

None. No criterion in scope carries a TODO, and every one was observable at the surface.

## Artifacts

All files are under `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/01058b7d-e98e-4d3f-a81c-e8ba15a8c683/scratchpad/exp8/run-3/drift-scratch/`. The repo was not touched, and `git status --short` there shows only the untracked `AGENTS.md` and `docs/` it showed before the run.

- `cases.md`, the case list written before execution.
- `evidence.log`, every command with its stdout, stderr, exit code, and log checksums.
- `ev.sh`, `seg2.sh`, `seg3.sh`, `seg4.sh`, `seg5.sh`, the runner and the four segments.
- `tkt.jsonl`, `tkt-copy.jsonl`, `log.jsonl`, `copy.jsonl`, the logs of the TKT and LOG runs and their copies.
- `corrupt.jsonl`, `corrupt2.jsonl`, `corrupt3.jsonl`, `corrupt4.jsonl`, `blank.jsonl`, the edited logs for LOG-007 and LOG-008.
- `envlog.jsonl`, `optlog.jsonl`, `cwd1/tickets.jsonl`, `cwd2/`, `adir/`, the LOG-001 and LOG-002 fixtures.
- `fresh-newline.jsonl`, `fresh-array.jsonl`, `fresh-nokind.jsonl`, `fresh-badkind.jsonl`, `fresh-unicode.jsonl`, `fresh-pipe.jsonl`, the fresh-state runs quoted above.
- `.out`, `.err`, `.before`, `.a`, `.b`, scratch files of the runner.

## Decision

You now decide for TKT-013 whether the spec or the product changes. You also decide, for each of the 9 UNCOVERED behaviours, whether it gets a criterion.

# Drift report: ticketdesk, specs `tickets.md` and `event-log.md`

## 1. Headline

22 criteria in scope: 19 MATCH, 3 DRIFT, 0 BLOCKED, 0 OPEN, and 8 UNCOVERED behaviours.
The DRIFT items are TKT-015, LOG-005, and LOG-007.
The run took about 8 minutes of wall time, and the host reported no money cost.

## 2. Scope and surface

The scope is every criterion of the two feature spec files, 22 in total.

| Spec file | Prefix | Criteria |
|---|---|---|
| `docs/product-specs/tickets.md` | TKT | 15 (TKT-001 to TKT-015) |
| `docs/product-specs/event-log.md` | LOG | 7 (LOG-001 to LOG-007) |

`docs/product-specs/invariants.md` (INV) got no verdict of its own. The run checked an
invariant only where a TKT or LOG criterion makes it observable.

The user is a support agent at a shell, and the surface is the command line.

- **Command.** `ticketdesk` in this report stands for
  `PYTHONPATH=<repo> PYTHONDONTWRITEBYTECODE=1 python3 -m ticketdesk.cli`.
- **Log file.** The event-log spec declares the log file a product surface, so the run read it.
- **Python package.** TKT-006 names the package as the place to read the due time. The run
  read it there with a consumer program, for TKT-006 and for the assignee in TKT-007.
- **Environment.** Local scratch directories, Python 3.15.2, macOS. Mutations were allowed.
- **Evidence log.**
  `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/01058b7d-e98e-4d3f-a81c-e8ba15a8c683/scratchpad/exp8/run-4/scratch/drift/evidence.log`

Nobody was available to answer questions, so the run made these assumptions.

- `AGENTS.md` and the docs index did not exist at the start. The run command came from the
  request.
- The environment is local, so the run mutated state without a confirmation.
- Some cases need a log state that no command can produce. The run wrote those log files
  by hand. Each row and block below says where that happened.
- Three cases joined the case list during the run. `cases.md` lists them under
  "Added during the run".

## 3. Verdict per criterion

### `docs/product-specs/tickets.md`

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| TKT-001 | MATCH | `ticketdesk create "Printer broken"` in an empty directory | stdout `#1 open Printer broken`, stderr empty, exit 0 |
| TKT-002 | MATCH | 12 times `ticketdesk create "t<n>"` in an empty directory. `ticketdesk create "After seven"` on a hand-written log whose only ticket has ID 7 | IDs 1 to 12 in order. `#8 open After seven`. Every ID stayed the same after `assign` and `close` |
| TKT-003 | MATCH | `ticketdesk create ""`, `ticketdesk create "   "`, and a title of one tab and one space | stderr `error: title is required`, stdout empty, exit 2, log checksum unchanged |
| TKT-004 | MATCH | `ticketdesk create --priority P1 ...`, the same with `P2` and `P3`, one `create` without the option, then `ticketdesk list` | `[P1]`, `[P2]`, `[P3]`, and `[P3]` for the ticket without the option |
| TKT-005 | MATCH | `ticketdesk create --priority P9 "Bad prio"`, the same with `p1` and with an empty value | traceback on stderr, stdout empty, exit 1, last line `ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']`, with `'p1'` and `''` in the quotes for the other two. Log checksum unchanged |
| TKT-006 | MATCH | `python3 consumer.py`, which calls `TicketService(EventStore("pkg.jsonl")).create(title, priority)` for `P1`, `P2`, `P3` and prints `(t.due_at - t.created_at) / 3600`. Then `ticketdesk --log pkg.jsonl create "cli default"` and the same read | 4.0, 24.0, and 72.0 hours. 72.0 hours for the ticket without the option. No command output in the run showed a due time |
| TKT-007 | MATCH | `ticketdesk assign 1 alice` on an `open` ticket, then `ticketdesk assign 1 bob`, then `ticketdesk list` | `#1 assigned -> alice`, exit 0, state `assigned`. `#1 assigned -> bob`, exit 0, state `assigned`. The package read `assignee` as `bob` |
| TKT-008 | MATCH | `ticketdesk assign 1 carol` on a `closed` ticket | stderr `error: ticket 1 is closed`, stdout empty, exit 2, log checksum unchanged |
| TKT-009 | MATCH | `ticketdesk assign 2 ""`, `ticketdesk assign 2 "   "`, a tab as the assignee, and `ticketdesk assign 4 "  "` on an `assigned` ticket | stderr `error: assignee is required`, stdout empty, exit 2, log checksum unchanged |
| TKT-010 | MATCH | `ticketdesk close 1 "Replaced the toner"` on an `assigned` ticket, `ticketdesk close 3 "Reset the VPN profile"` on an `open` ticket, then `ticketdesk list` | `#1 closed` and `#3 closed`, exit 0, state `closed` for both |
| TKT-011 | MATCH | `ticketdesk close 2 <note>` with `123456789`, an empty note, `"  123456789  "`, and 10 spaces. Then `1234567890`. Then `ticketdesk close 4 "  a b c d ef  "` | The first four gave `error: resolution note must be at least 10 characters`, exit 2. The 10-character notes gave `#2 closed` and `#4 closed`, exit 0 |
| TKT-012 | MATCH | `ticketdesk close 1 "Replaced the toner again"` on a `closed` ticket | stderr `error: ticket 1 is already closed`, stdout empty, exit 2, log checksum unchanged |
| TKT-013 | MATCH | `ticketdesk assign 99 alice`, `ticketdesk close 99 "long enough note"`, `ticketdesk assign 99 ""`, `ticketdesk close 99 "short"`, `ticketdesk assign 0 x`, `ticketdesk assign -1 x` | stderr `error: no ticket 99` for the first four, exit 2. `error: no ticket 0` and `error: no ticket -1`, exit 2. A non-integer ID is under UNCOVERED 5.2 |
| TKT-014 | MATCH | Eight rejected commands, one per rejection of TKT-003, TKT-008, TKT-009, TKT-011, TKT-012, and TKT-013. `ticketdesk list` before and after each one | Each one printed 1 line `error: ...` on stderr and 0 bytes on stdout, and exited with 2. The `list` output and the log bytes were the same before and after |
| TKT-015 | DRIFT | `ticketdesk list` with tickets in all three states, with 12 tickets, with no log, and with a ticket whose title holds a newline | Format, padding, numeric order, and the empty case match. The ticket with a newline in its title printed as two lines. See 4.1 |

### `docs/product-specs/event-log.md`

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| LOG-001 | MATCH | In directory `cwd`: `ticketdesk create "default place"`. Then the same with `TICKETDESK_LOG=../other/env.jsonl`. Then with that variable and `--log ../other/opt.jsonl` before `create`. Then `list` in each of the three forms | `cwd/tickets.jsonl`, `other/env.jsonl`, and `other/opt.jsonl` each hold one line. Each `list` showed only the ticket of its own log |
| LOG-002 | MATCH | In an empty directory: `ticketdesk list`, then `ticketdesk create ""`, `ticketdesk create --priority P9 "x"`, `ticketdesk assign 1 alice`, `ticketdesk close 1 "long enough note"`, then `ticketdesk create "first"` | `list` printed nothing, exit 0, no file. The four failed commands created no file. `create "first"` created `tickets.jsonl` with one line |
| LOG-003 | MATCH | A session of 16 commands with a line count before and after each one | Each successful `create`, `assign`, and `close` took the count up by exactly 1. Each rejected command, each `list`, and the `P9` failure left it the same |
| LOG-004 | MATCH | Parsed every line of four logs that the product wrote, 29 lines in total | Every line is one JSON object with its keys in alphabetical order. `created` has `at`, `id`, `kind`, `priority`, `title`. `assigned` has `assignee`, `at`, `id`, `kind`. `closed` has `at`, `id`, `kind`, `resolution`. `id` is the integer ticket ID. `at` is Unix seconds with a fraction, such as `1794326003.691906` |
| LOG-005 | DRIFT | The 16-command session with a byte compare of the old log against the start of the new log. Then `ticketdesk create "second"` on a hand-written log whose last line has no final newline | The old bytes stayed the same after all 16 commands. On the hand-written log, `create` wrote its event onto the end of line 1. See 4.2 |
| LOG-006 | MATCH | `cp orig.jsonl far/copy.jsonl`, then `ticketdesk --log orig.jsonl list` and `ticketdesk --log far/copy.jsonl list` | The two outputs are byte-for-byte the same. The same holds with `TICKETDESK_LOG=copy.jsonl` from inside `far`. The run directories hold no file besides the log |
| LOG-007 | DRIFT | Line 2 of 3 replaced by `{not json`, then `list`, `create "three"`, `assign 1 alice`, `close 1 "long enough note"`, `assign 99 x`, `create ""`, `create --priority P9 x`. Then a log with two blank lines. Then a log with a line of non-UTF-8 bytes | The first five gave the traceback, exit 1, last line `ValueError: tickets.jsonl:2: corrupt event: ...`, and added no line. Blank lines were ignored and still counted in the line number. `create ""`, `create --priority P9 x`, and the non-UTF-8 line gave other outcomes. See 4.3 |

## 4. DRIFT details

### 4.1 TKT-015: a title with a newline prints as two lines in `list`

The criterion says:

> `ticketdesk list` prints one line per ticket in ascending ID order and exits with status
> 0.

The commands, in an empty directory:

```text
$ ticketdesk create "$(printf 'two\nlines')"; echo "exit=$?"
#1 open two
lines
exit=0
$ ticketdesk create "next"; echo "exit=$?"
#2 open next
exit=0
$ ticketdesk list; echo "exit=$?"
#1 [P3] open     two
lines
#2 [P3] open     next
exit=0
$ ticketdesk list | wc -l
3
```

Two tickets give three lines. TKT-003 rejects only a title that is empty or holds only
whitespace, so `create` accepts this title.

Most likely cause, as a likelihood: `cli.py` prints the title as stored, and `create`
checks the title only with `title.strip()`.

### 4.2 LOG-005: `create` changes line 1 of a log that has no final newline

The criterion says:

> After any command, every line that the log held before the command is byte-for-byte the
> same and in the same position.

The starting log is hand-written. It holds one valid `created` line without a final
newline. Every line that the product wrote in this run ended with a newline.

```text
$ printf '%s' '{"at": 1, "id": 1, "kind": "created", "priority": "P1", "title": "first"}' > tickets.jsonl
$ ticketdesk list; echo "exit=$?"
#1 [P1] open     first
exit=0
$ ticketdesk create "second" 2>err.txt; echo "exit=$?"; tail -n 1 err.txt
exit=1
ValueError: tickets.jsonl:1: corrupt event: Extra data: line 1 column 74 (char 73)
$ cat tickets.jsonl
{"at": 1, "id": 1, "kind": "created", "priority": "P1", "title": "first"}{"at": 1794326182.004735, "id": 2, "kind": "created", "priority": "P3", "title": "second"}
$ ticketdesk list 2>err.txt; echo "exit=$?"; tail -n 1 err.txt
exit=1
ValueError: tickets.jsonl:1: corrupt event: Extra data: line 1 column 74 (char 73)
```

Line 1 held 73 characters before the command and holds two JSON objects after it. The
log was readable before `create` and every later command fails on it. The command also
exited with status 1 and still wrote its event, which touches LOG-003.

Most likely cause, as a likelihood: `EventStore.append` in `store.py` opens the file in
append mode and writes the record plus a newline. It does not check how the file ends.
`create` then reads the log again to return the ticket, and that read fails.

### 4.3 LOG-007: three cases on an unreadable log do not end in the corrupt-event traceback

The criterion says:

> When a line of the log is not valid JSON, every command fails and adds no line. It prints
> a Python traceback on standard error and exits with status 1. The last line of the
> traceback starts with `ValueError: <path>:<line number>: corrupt event:`.

**Cases 1 and 2.** A `create` with an empty title, and a `create` with an unknown priority,
on a log whose line 2 is `{not json`:

```text
$ ticketdesk create "one"
#1 open one
$ echo '{not json' >> tickets.jsonl
$ ticketdesk list 2>err.txt; echo "exit=$?"; tail -n 1 err.txt
exit=1
ValueError: tickets.jsonl:2: corrupt event: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
$ ticketdesk create "" ; echo "exit=$?"
error: title is required
exit=2
$ ticketdesk create --priority P9 "x" 2>err.txt; echo "exit=$?"; tail -n 1 err.txt
exit=1
ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']
$ wc -l < tickets.jsonl
2
```

`create ""` prints no traceback and exits with status 2. `create --priority P9 "x"` exits
with status 1, and its last line names the priority, not the corrupt line. Both add no
line. `list`, `create "three"`, `assign 1 alice`, `close 1 "long enough note"`, and
`assign 99 x` all end in the promised traceback.

**Case 3.** A line of bytes that are not UTF-8, so the line is not valid JSON:

```text
$ ticketdesk create "one"
#1 open one
$ printf '\377\376\n' >> tickets.jsonl
$ ticketdesk list 2>err.txt; echo "exit=$?"; tail -n 1 err.txt
exit=1
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 88: invalid start byte
```

The command fails with status 1. The last line starts with `UnicodeDecodeError:` and
carries no path, no line number, and no `corrupt event:` text.

Most likely cause, as a likelihood: `create` in `tickets.py` checks the title and the
priority before it reads the log. `EventStore.replay` in `store.py` decodes the whole file
as UTF-8 before it parses any line, and it wraps only `json.JSONDecodeError`.

## 5. UNCOVERED behaviours

The inventory took its list from the help output and from the evidence log. This table
maps each behaviour that a criterion covers. Blocks 5.1 to 5.8 hold the 8 behaviours that
no criterion covers.

| Behaviour | Covered by |
|---|---|
| Commands `create`, `assign`, `close`, `list` | TKT-001, TKT-007, TKT-010, TKT-015 |
| Option `--priority` and its default | TKT-004, TKT-005 |
| Option `--log` and variable `TICKETDESK_LOG` | LOG-001 |
| Output lines `#<id> open <title>`, `#<id> assigned -> <assignee>`, `#<id> closed`, and the `list` line | TKT-001, TKT-007, TKT-010, TKT-015 |
| File `tickets.jsonl` and its fields | LOG-002, LOG-003, LOG-004 |
| Exit 0, exit 2 with `error: <message>`, exit 1 with a traceback | TKT-014, TKT-005, LOG-007 |
| Due time on the ticket in the Python package | TKT-006 |

### 5.1 Help output

`-h` and `--help` print a usage text on standard output and exit with status 0. Each of
the four commands takes them too. No criterion comes close.

```text
$ ticketdesk --help; echo "exit=$?"
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...

positional arguments:
  {create,assign,close,list}

options:
  -h, --help            show this help message and exit
  --log LOG             path of the event log
exit=0
$ ticketdesk create -h; echo "exit=$?"
usage: ticketdesk create [-h] [--priority PRIORITY] title

positional arguments:
  title

options:
  -h, --help           show this help message and exit
  --priority PRIORITY
exit=0
```

### 5.2 Usage errors print two lines and exit with status 2

A command line that the argument parser refuses prints a `usage:` line and an error line
on standard error. The exit status is 2, and no file appears. This covers a missing or
unknown command, a missing or extra argument, a title that starts with `-`, a non-integer
ID, and `--log` after the command name. The nearest criteria are TKT-014, which promises
one line `error: <message>`, and TKT-013 for the ID.

```text
$ ticketdesk; echo "exit=$?"
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...
ticketdesk: error: the following arguments are required: cmd
exit=2
$ ticketdesk bogus; echo "exit=$?"
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...
ticketdesk: error: argument cmd: invalid choice: 'bogus' (choose from 'create', 'assign', 'close', 'list')
exit=2
$ ticketdesk create; echo "exit=$?"
usage: ticketdesk create [-h] [--priority PRIORITY] title
ticketdesk create: error: the following arguments are required: title
exit=2
$ ticketdesk create "a" "b"; echo "exit=$?"
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...
ticketdesk: error: unrecognized arguments: b
exit=2
$ ticketdesk create "-dash"; echo "exit=$?"
usage: ticketdesk create [-h] [--priority PRIORITY] title
ticketdesk create: error: the following arguments are required: title
exit=2
$ ticketdesk assign abc alice; echo "exit=$?"
usage: ticketdesk assign [-h] id assignee
ticketdesk assign: error: argument id: invalid int value: 'abc'
exit=2
$ ticketdesk close abc "long enough note"; echo "exit=$?"
usage: ticketdesk close [-h] id resolution
ticketdesk close: error: argument id: invalid int value: 'abc'
exit=2
$ ticketdesk list --log x.jsonl; echo "exit=$?"
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...
ticketdesk: error: unrecognized arguments: --log x.jsonl
exit=2
```

`ticketdesk create -- "-dash"` printed `#4 open -dash` and exited with status 0.

### 5.3 A log path that cannot be read or written ends in a traceback

Three unusable log paths each end in a Python traceback with status 1. The three are an
empty `TICKETDESK_LOG`, a path in a missing directory, and a path that is a directory.
`list` on a path in a missing directory prints nothing and exits with status 0. The nearest criteria are LOG-001 and
LOG-002.

```text
$ TICKETDESK_LOG= ticketdesk list 2>err.txt; echo "exit=$?"; tail -n 1 err.txt
exit=1
IsADirectoryError: [Errno 21] Is a directory: '.'
$ TICKETDESK_LOG= ticketdesk create "x" 2>err.txt; echo "exit=$?"; tail -n 1 err.txt
exit=1
IsADirectoryError: [Errno 21] Is a directory: '.'
$ ticketdesk --log nodir/x.jsonl list; echo "exit=$?"
exit=0
$ ticketdesk --log nodir/x.jsonl create "x" 2>err.txt; echo "exit=$?"; tail -n 1 err.txt
exit=1
FileNotFoundError: [Errno 2] No such file or directory: 'nodir/x.jsonl'
$ mkdir adir
$ ticketdesk --log adir list 2>err.txt; echo "exit=$?"; tail -n 1 err.txt
exit=1
IsADirectoryError: [Errno 21] Is a directory: 'adir'
```

### 5.4 A line that is valid JSON but not an event ends in a different traceback

A hand-written line that parses as JSON but lacks the fields of LOG-004 fails the command
with status 1. The last line of the traceback is a `TypeError`, a `KeyError`, or the
priority `ValueError`. It carries no path, no line number, and no `corrupt event:` text.
The nearest criteria are LOG-007, which covers only a line that is not valid JSON, and
LOG-004. Each run below is `ticketdesk list` on a log whose line 1 is a valid `created`
line.

```text
line 2: []
exit=1
TypeError: list indices must be integers or slices, not str
line 2: {}
exit=1
KeyError: 'kind'
line 2: {"at": 1, "id": 1, "kind": "created"}
exit=1
KeyError: 'title'
line 2: {"assignee": "x", "at": 1, "id": 9, "kind": "assigned"}
exit=1
KeyError: 9
line 2: {"at": 1, "id": 2, "kind": "created", "priority": "P7", "title": "odd"}
exit=1
ValueError: unknown priority 'P7'; expected one of ['P1', 'P2', 'P3']
```

### 5.5 A line with an unknown `kind` is skipped

A hand-written line whose `kind` is not `created`, `assigned`, or `closed` has no effect.
Every command continues as if the line were absent. The nearest criteria are LOG-004,
which names the three kinds, and LOG-007. INV-003 says the product never skips a line
that it cannot read.

```text
$ ticketdesk create "one"
#1 open one
$ echo '{"at": 1, "id": 1, "kind": "bogus"}' >> tickets.jsonl
$ ticketdesk list; echo "exit=$?"
#1 [P3] open     one
exit=0
$ ticketdesk assign 1 alice; echo "exit=$?"
#1 assigned -> alice
exit=0
$ wc -l < tickets.jsonl
3
```

### 5.6 A second `created` line with the same ID replaces the ticket

A hand-written `created` line that reuses an existing ID replaces the title and the
priority of that ticket in `list`. No command of the product wrote such a line in this
run. The nearest criterion is TKT-002, and INV-004 says no command gives an ID to another
ticket.

```text
$ ticketdesk create --priority P1 "first"
#1 open first
$ echo '{"at": 2, "id": 1, "kind": "created", "priority": "P2", "title": "second"}' >> tickets.jsonl
$ ticketdesk list; echo "exit=$?"
#1 [P2] open     second
exit=0
```

### 5.7 The order of checks when one command breaks two rules

On a `closed` ticket, the state check runs before the check of the assignee or of the
note. In `create`, the title check runs before the priority check. TKT-013 gives an order
only for the unknown ID. The nearest criteria are TKT-008, TKT-009, TKT-011, TKT-012, and
TKT-005.

```text
$ ticketdesk create "a"
#1 open a
$ ticketdesk close 1 "closed for the probe"
#1 closed
$ ticketdesk assign 1 ""; echo "exit=$?"
error: ticket 1 is closed
exit=2
$ ticketdesk close 1 "short"; echo "exit=$?"
error: ticket 1 is already closed
exit=2
$ ticketdesk create --priority P9 ""; echo "exit=$?"
error: title is required
exit=2
```

### 5.8 The Python package exposes more than the due time

The package `ticketdesk` exports names that a consumer program can call, and TKT-006
covers only the due time on the ticket. The consumer program used `create`, `list`,
`get`, `assign`, and `close`, and each one worked on the same log as the command line.
The nearest criterion is TKT-006.

```text
package attrs: ['EventStore', 'SLA_HOURS', 'Ticket', 'TicketError', 'TicketService', 'due_at', 'sla', 'store', 'tickets']
ticketdesk.tickets Ticket (id: int, title: str, priority: str, created_at: float, state: str = 'open', assignee: str | None = None, resolution: str | None = None, due_at: float = 0.0) -> None
ticketdesk.tickets TicketService (store)
   . list (self)
   . get (self, ticket_id)
   . create (self, title, priority)
   . assign (self, ticket_id, assignee)
   . close (self, ticket_id, resolution)
ticketdesk.store EventStore (path, clock=<built-in function time>)
   . append (self, event)
   . replay (self)
ticketdesk.sla SLA_HOURS {'P1': 4, 'P2': 24, 'P3': 72}
ticketdesk.sla due_at (created_at, priority)
```

## 6. BLOCKED and OPEN

- BLOCKED: none.
- OPEN: none. No criterion in scope carries a TODO.

## 7. Artifacts

The run created files only under
`/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/01058b7d-e98e-4d3f-a81c-e8ba15a8c683/scratchpad/exp8/run-4/scratch/drift/`.
It modified no file in the repo and created no `__pycache__` there.

| Path under the scratch directory | Holds |
|---|---|
| `cases.md` | the case list, written before the first case ran |
| `evidence.log` | every command and its output, in run order, then the trimmed repro runs |
| `evidence1.log` to `evidence6.log`, `repro.log` | the parts of `evidence.log` |
| `session1.sh`, `session2.sh`, `session3.sh`, `repro.sh` | the scripts that ran the cases |
| `td`, `run`, `bin/ticketdesk` | wrappers that start the product with the documented command |
| `smoke/`, `t1/` to `t17/` | one working directory per case group, with the logs the product wrote |
| `t17/consumer.py`, `t17/pkg.jsonl` | the consumer program for TKT-006 and its log |
| `repro/d1/` to `repro/d4/`, `repro/u1/` to `repro/u7/` | fresh state for the quoted runs of sections 4 and 5 |
| `t1.before`, `t1.list.before`, `t5.before`, `t5.after`, `t5.log.before`, `t8.prev`, `t11.before` | snapshots for the before and after compares |
| `lint-input.md` | the copy of this report that `prose-lint.py` read |

## 8. The decision line

You decide, per DRIFT, whether the spec or the product changes, and per UNCOVERED behaviour, whether it gets a criterion.

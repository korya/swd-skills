# Drift report: ticketdesk

The run covered 21 criteria: 20 MATCH, 0 DRIFT, 0 BLOCKED, 1 OPEN, and 3 UNCOVERED behaviours. No criterion drifted from the product. The OPEN item is TKT-002, which carries a TODO about the invalid-priority message. The host reported no time or cost figure, so the run cost is not stated.

## Scope and surface

The scope is two spec files with 21 criteria in total. `INV-001` to `INV-005` were checked only where a feature criterion makes them observable.

- `docs/product-specs/tickets.md` (prefix TKT): 13 criteria.
- `docs/product-specs/event-log.md` (prefix LOG): 8 criteria.

The user is a support agent in a shell. The surface is the `ticketdesk` command line, run as `python3 -m ticketdesk.cli` with `PYTHONPATH` set to the repo, because the product is not installed. The environment is local. The event log file is a product surface, so the run read it too. The evidence log is `drift-scratch/evidence.log`.

Assumptions made because nobody could answer:

- The module entry point is equivalent to the `ticketdesk` command the specs name.
- Only the README was read as a conventions doc. `AGENTS.md` did not exist at the start and was not read.
- Input tolerance (lowercase priority, key order in records, timestamp precision) is not a behaviour unless a criterion names it.

## Tickets (TKT)

In the commands below, `td` stands for `python3 -m ticketdesk.cli` run in a fresh scratch directory.

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| TKT-001 | MATCH | `td create "Printer jam"` | stdout `#1 open Printer jam`, exit 0 |
| TKT-002 | OPEN | `td create "Bad" --priority P9` | Traceback, exit 1. The log was byte for byte unchanged, so no ticket was created. `--priority P1`, `P2`, and the default `P3` were stored as given. |
| TKT-003 | MATCH | `td create ""`, `td create "   "` | stderr `error: title is required`, exit 2 for both |
| TKT-004 | MATCH | four `create` calls, then a hand-written record with id 7, then `td create next` | `#1` to `#4` in order. After the id 7 record the next ticket was `#8`. |
| TKT-005 | MATCH | `td assign 1 alice` | `#1 assigned -> alice`, exit 0. `list` showed state `assigned`. |
| TKT-006 | MATCH | `td assign 1 bob` after alice | `#1 assigned -> bob`, exit 0. `list` showed state `assigned`. |
| TKT-007 | MATCH | `td assign 2 ""`, `td assign 2 "  "` | stderr `error: assignee is required`, exit 2. `list` showed ticket 2 still `open`. |
| TKT-008 | MATCH | `td close 1 "1234567890"` on an assigned ticket, `td close 2 "fixed it properly"` on an open ticket | `#1 closed` and `#2 closed`, exit 0 |
| TKT-009 | MATCH | `td close 1 short`, `td close 1 "  123456789  "`, `td close 11 "   1234567890   "`, `td close 10 "         "` | The first, second, and fourth printed `error: resolution note must be at least 10 characters` with exit 2 and left the state. The third printed `#11 closed`. |
| TKT-010 | MATCH | `td assign 1 zed`, `td close 1 "again again again"` on a closed ticket | stderr `error: ticket 1 is closed` and `error: ticket 1 is already closed`, exit 2 for both. `list` still showed `closed`. |
| TKT-011 | MATCH | `td assign 99 x`, `td close 99 "long enough note"` | stderr `error: no ticket 99`, exit 2 for both |
| TKT-012 | MATCH | `td list` with 4 mixed-state tickets, then with 11 tickets, then in a directory with no log | Lines like `#1 [P3] closed   Printer jam` and `#4 [P3] open     Fourth`. The state was padded to 8 characters. Order was numeric (`#9`, `#10`, `#11`). The empty case printed nothing, exit 0. |
| TKT-013 | MATCH | `td`, `td create`, `td assign 1`, `td close 1`, `td assign abc x`, `td close 1.5 "long enough note"` | Usage on stderr, exit 2. Examples: `ticketdesk: error: the following arguments are required: cmd` and `argument id: invalid int value: 'abc'`. |

## Event log (LOG)

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| LOG-001 | MATCH | `td create "Printer jam"` in a directory with no environment variable | `tickets.jsonl` appeared in the current directory |
| LOG-002 | MATCH | `TICKETDESK_LOG=$PWD/env.jsonl td create "Env ticket"`, then the same with `td --log $PWD/opt.jsonl create "Opt ticket"` | The first wrote `env.jsonl`. The second wrote `opt.jsonl` while the variable was set, so the option won. `td create --log late.jsonl "Late"` (option after the command) was rejected with exit 2. |
| LOG-003 | MATCH | `td --log $PWD/nope.jsonl list`, then `td --log $PWD/nope.jsonl create "x"` | The `list` printed nothing, exit 0, and no file appeared. The `create` printed `#1 open x` and created `nope.jsonl`. |
| LOG-004 | MATCH | `create`, `assign`, `close`, `create`, then `wc -l tickets.jsonl` | 4 lines for 4 commands. Each line parsed as one JSON object. |
| LOG-005 | MATCH | read each line with `json.loads` after the four commands | `created`: `at`, `id`, `kind`, `priority`, `title`. `assigned`: `assignee`, `at`, `id`, `kind`. `closed`: `at`, `id`, `kind`, `resolution`. `at` was within 1 second of the clock. |
| LOG-006 | MATCH | `cp tickets.jsonl snap1`, then `list`, six rejected commands with exit 2, and a bare `td`, then `cmp` | `cmp snap1 tickets.jsonl` found no difference after each group |
| LOG-007 | MATCH | `td assign 2 zoe`, then `head -n 4 tickets.jsonl \| cmp - snap1` | The first 4 lines were byte for byte the same. The file grew to 5 lines. |
| LOG-008 | MATCH | `cp tickets.jsonl copy.jsonl`, then `td list` against `td --log copy.jsonl list` | Both outputs were identical (`cmp` found no difference) |

## DRIFT details

None.

## UNCOVERED behaviours

Each item is a fact. The product does this and no criterion in scope describes it.

**1. Help output.**
The product prints help for the top command and for each subcommand, with exit 0.

```text
$ ticketdesk --help
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...
  exit: 0
```

The nearest criterion is TKT-013, which covers only parse failures.

**2. A corrupt log line ends the command with a traceback and exit 1.**
The command refuses to continue and does not write, which fits `INV-004`.

```text
$ ticketdesk --log bad.jsonl list    (line 6 of bad.jsonl is: not json)
ValueError: bad.jsonl:6: corrupt event: Expecting value: line 1 column 1 (char 0)
  exit: 1
```

`create` against the same file printed the same `ValueError` and exit 1. The log kept its last line `not json`. `INV-004` says only "stops the command with an error". No criterion names the message form or the exit code.

**3. An unreadable log path ends the command with a traceback and exit 1.**
No criterion covers a log path that is not a readable file.

```text
$ ticketdesk --log "" list
IsADirectoryError: [Errno 21] Is a directory: '.'
  exit: 1
```

The nearest criterion is LOG-003, which covers only a missing file.

## BLOCKED and OPEN

BLOCKED: none.

OPEN:

- TKT-002: "TODO: how the product reports a priority outside the list is not settled. Today the user sees a Python traceback." The settled part held: `P9`, `p1`, and an empty priority each created no ticket and left the log unchanged. Each exited 1 with a `ValueError` traceback.

## Artifacts

All files are under `drift-scratch/` in the run directory. Nothing under `repo/` was modified.

- `evidence.log`: every command, output, and exit code in run order. Case headers sit in the `evidence.log` copy inside each `c*` directory.
- `caselist.md`: the case list written before execution.
- `td.sh`: the wrapper that runs the product and logs the evidence.
- `c1` to `c4`, `smoke`: scratch directories with the logs and copies the cases made.

## Decision

You now decide whether TKT-002 gets a message rule, and for each UNCOVERED item whether it gets a criterion.

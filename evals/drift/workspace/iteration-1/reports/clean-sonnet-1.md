# Drift report: ticketdesk 0.3.0

Of 31 criteria, 28 MATCH, 0 DRIFT, 2 BLOCKED, 1 OPEN, and 4 behaviours are UNCOVERED. No criterion showed DRIFT. The OPEN item is CLI-007. The BLOCKED items are TKT-005 and TKT-009. The run took a few minutes of wall-clock time. The host reported no cost figure.

## Scope and surface

The scope is every feature criterion in the three feature specs under `docs/product-specs/`. The invariants file is checked only where a feature criterion makes an invariant observable.

| Spec file | Criteria |
|---|---|
| `tickets.md` | 13 (TKT-001 to TKT-013) |
| `event-log.md` | 9 (LOG-001 to LOG-009) |
| `cli.md` | 9 (CLI-001 to CLI-009) |

The user is a shell user on a support team. The surface is the `ticketdesk` binary, installed with `pip install` into a fresh virtual environment, as `AGENTS.md` describes. The environment is local, on a scratch directory outside the repo. The log file counts as a product surface, because `event-log.md` declares it one.

Nobody was available to answer questions. The run assumes that the specs, not the code, are the contract under test. It also assumes that an uncaught Python traceback counts as an error for criteria that name no output form.

The evidence log is in three files: `scratch/evidence1.txt`, `scratch/evidence2.txt`, and `scratch/evidence3.txt`. The scripts that produced them are `run1.sh`, `run2.sh`, and `run3.sh` in the same folder. In the tables, `td` stands for `ticketdesk`, and `--log t.jsonl` is left out where it adds nothing.

## tickets.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| TKT-001 | MATCH | `td create "Printer on fire" --priority P1`, then `assign 1 dana`, `close 1 ...`, `list` | List showed `open`, then `assigned`, then `closed`. A new ticket printed `open`. |
| TKT-002 | MATCH | `td create ""` and `td create "   "` | `error: title is required`, exit 2. List unchanged, log still 3 lines. |
| TKT-003 | MATCH | `td create x --priority P9` and `--priority p1` | Both failed. The message names the value and `['P1', 'P2', 'P3']`. No ticket created. The form is a traceback, see CLI-007. |
| TKT-004 | MATCH | Three creates, close all three, one more create. Also an out-of-order log with ids 3, 1, 2. | IDs 1, 2, 3. Next create after closing all gave `#4`. Out-of-order log gave `#4` next. |
| TKT-005 | BLOCKED | `td list`, `cat t.jsonl` | No command prints a due time and the log carries no due field. A command or field that shows the due time would settle it. |
| TKT-006 | MATCH | `td assign 1 dana`, then `td assign 1 bob`, then `td list` | `#1 assigned -> dana`, then `#1 assigned -> bob`. List showed `assigned`. |
| TKT-007 | MATCH | `td assign 2 ""` and `td assign 2 "  "` | `error: assignee is required`, exit 2. Ticket 2 stayed `open`. |
| TKT-008 | MATCH | `td assign 1 zed` after closing ticket 1 | `error: ticket 1 is closed`, exit 2. |
| TKT-009 | BLOCKED | `td close 1 "Replaced the toner cartridge"` after `assign 1 bob` | State `closed` and the note in the log both observed. No command shows the assignee, so "assignee is kept" cannot be observed. A command that prints the assignee would settle it. |
| TKT-010 | MATCH | Close with `short`, `"          short   "`, `123456789`, `" 123456789 "`, and `"exactly 10"` | The first four gave `resolution note must be at least 10 characters`, exit 2. The 10-character note closed the ticket. |
| TKT-011 | MATCH | `td close 1 "Replaced the toner cartridge again"` on a closed ticket | `error: ticket 1 is already closed`, exit 2. Log holds one `closed` event for id 1. |
| TKT-012 | MATCH | `td assign 99 bob` and `td close 99 "Replaced the toner cartridge"` | `error: no ticket 99`, exit 2. |
| TKT-013 | MATCH | `td list` on a log with ids 3, 1, 2 where 2 is closed | `#1`, `#2 ... closed`, `#3`, in ascending order. |

## event-log.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| LOG-001 | MATCH | 3 creates, 2 assigns, 3 closes, then failing commands and `list`. Counted lines and checksummed the file. | 8 lines after 8 changes. Failed commands and `list` added nothing. The checksum was the same before and after `list`. |
| LOG-002 | MATCH | `cat t.jsonl` | Kinds seen: `created`, `assigned`, `closed`. |
| LOG-003 | MATCH | `cat t.jsonl` | `created` has `title` and `priority`, `assigned` has `assignee`, `closed` has `resolution`. All carry `kind`, `id`, `at`. |
| LOG-004 | MATCH | `date +%s`, then `td create clock`, then `cat t.jsonl` | `date` gave 1794282290. The event had `"at": 1794282290.577613`. |
| LOG-005 | MATCH | `cat -A tickets.jsonl` after adding three blank lines by hand, then `list` and `create` | Keys sorted, one line per event, newline-ended. Blank lines ignored by `list` and `create`. |
| LOG-006 | MATCH | `td --log t.jsonl list` with no file, then the first `create` | `list` printed nothing, exit 0, no file created. First create gave `#1` and created the file. |
| LOG-007 | MATCH | Log with `not json` on line 7 and a valid event on line 8, then `list`, `create`, `assign`, `close` | Each ended with `ValueError: bad.jsonl:7: corrupt event: Expecting value: line 1 column 1 (char 0)`. File stayed at 8 lines. The form is a traceback, see CLI-007. |
| LOG-008 | MATCH | Copy the log, run `assign 1 dana`, `cmp -n <old size>` | Old bytes identical (`prefix-identical`). |
| LOG-009 | MATCH | `td list \| md5 -q` twice | Same checksum both times. |

## cli.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| CLI-001 | MATCH | `td` and `td bogus` | Usage and error on stderr, stdout empty, exit 2 for both. |
| CLI-002 | MATCH | Create with no option and no variable, then with `TICKETDESK_LOG=env.jsonl`, then `--log opt.jsonl` with the variable set | Wrote `tickets.jsonl`, then `env.jsonl`, then `opt.jsonl`. Each file held one line. |
| CLI-003 | MATCH | `td create "Default prio"` and `td create "Slow wifi" --priority P2` | `#2 open Default prio`, `#3 open Slow wifi`. Log shows `P3` and `P2`. |
| CLI-004 | MATCH | `td assign 1 dana` | `#1 assigned -> dana`. |
| CLI-005 | MATCH | `td close 1 "Replaced the toner cartridge"` | `#1 closed`. |
| CLI-006 | MATCH | `td list` with 3 tickets, and with no file | `#1 [P1] assigned Printer on fire` style lines, state padded to 8, ID order. Empty log printed nothing. |
| CLI-007 | OPEN | Six ticket-rule errors (TKT-002, 007, 008, 010, 011, 012) | Each printed `error: <message>` on stderr, nothing on stdout, exit 2. The TODO part is below. |
| CLI-008 | MATCH | Every successful command in the run | Exit 0, stderr empty each time. |
| CLI-009 | MATCH | `td assign abc bob` and `td close abc "long enough note"` | `argument id: invalid int value: 'abc'`, exit 2. Log stayed at 8 lines. |

## DRIFT details

None. Every settled part of every criterion matched at the surface.

## UNCOVERED behaviours

**1. Uncaught errors outside CLI-007's two cases.** The product ends in a traceback and exit 1 in more cases than the TODO lists. Nearest criterion: CLI-007 and LOG-006.

```text
$ ticketdesk --log /nonexistent/dir/t.jsonl create x
...
FileNotFoundError: [Errno 2] No such file or directory: '/nonexistent/dir/t.jsonl'
[rc=1]

$ ticketdesk --log . list
...
IsADirectoryError: [Errno 21] Is a directory: '.'
[rc=1]

$ TICKETDESK_LOG= ticketdesk create emptyenv
...
IsADirectoryError: [Errno 21] Is a directory: '.'
[rc=1]
```

An empty `TICKETDESK_LOG` counts as set, so the path becomes `.`. CLI-002 says "the first of three sources that is set" and does not say whether an empty value counts.

**2. A line that is valid JSON but not an object.** Nearest criterion: LOG-007 and INV-004.

```text
$ printf '[1,2]\n' > shape.jsonl
$ ticketdesk --log shape.jsonl list
...
TypeError: list indices must be integers or slices, not str
[rc=1]
```

The error names neither the file nor the line, unlike a line that is not JSON.

**3. An event with an unknown kind is ignored without a message.** Nearest criterion: LOG-002.

```text
$ printf '{"kind":"weird","id":1,"at":1}\n' > kind.jsonl
$ ticketdesk --log kind.jsonl list
[rc=0]
```

**4. Help flags.** `ticketdesk -h` and `-h` on each subcommand print usage to stdout and exit 0. The `--log` option help reads `path of the event log`. No criterion covers help output. `ticketdesk --version` is rejected with the missing-subcommand usage error, exit 2.

## BLOCKED and OPEN

- BLOCKED, TKT-005: a command or log field that shows the due time would settle it.
- BLOCKED, TKT-009: a command that prints the assignee of a closed ticket would settle "The assignee, if any, is kept".
- OPEN, CLI-007: "TODO: two failures do not follow this rule today. An unknown priority (TKT-003) and a corrupt log line (LOG-007) escape as a Python traceback with exit code 1." The run reproduced both, see the TKT-003 and LOG-007 rows. The settled part passed in six cases.

## Artifacts

Everything is under `exp7/clean-1/scratch/`:

- `venv/` and `src/`, the virtual environment and a copy of the repo used for the install.
- `w1/`, `w2/`, `w3/`, the working directories holding the test logs.
- `run1.sh`, `run2.sh`, `run3.sh`, `evidence1.txt`, `evidence2.txt`, `evidence3.txt`.

`git status` in the repo was clean after the run. No repo file changed.

## Decision

You now decide, for the OPEN item, whether the spec or the product changes. For each UNCOVERED item, you decide whether it gets a criterion.

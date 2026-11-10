# Drift report: ticketdesk 0.3.0

Of 26 criteria in scope, 25 MATCH, 1 DRIFT, 0 BLOCKED, 0 OPEN, and 3 behaviours are UNCOVERED. The DRIFT item is TKT-015. The run cost about $0.41 as the host reports it. Wall-clock time was not measured.

## Scope and surface

- **Spec files:** `docs/product-specs/tickets.md` (TKT-001 to TKT-016) and `docs/product-specs/event-log.md` (LOG-001 to LOG-010). That is 26 criteria.
- **Invariants:** `invariants.md` (INV-001 to INV-005) is checked only where a feature criterion makes an invariant observable.
- **User and surface:** a shell user running the installed `ticketdesk` binary.
- **Environment:** local, on a scratch directory. Mutations through the command are allowed.
- **Assumption:** `pip install .` inside the repo writes build files into the repo. Nobody was available to ask, so the run copied the package files to a scratch directory and installed them into a venv there. The binary is the same one `pip install .` gives.
- **Python:** 3.15.2. The docs name 3.11 or later and CI on 3.12. The run did not test those versions.
- **Spec status:** the specs are uncommitted. This changes nothing about the check.
- **Case list:** `drift-scratch/cases-independent.md`. I wrote the list before the first run, but a `cases.md` from an earlier run blocked that write. I saved the same list under this name afterwards.
- **Evidence log:** `drift-scratch/evidence.log`, the concatenation of `evidence-1.log`, `evidence-2.log`, and `evidence-3.log`. Every row below was produced by a command in those logs. `$TD` stands for the venv's `ticketdesk`.

## tickets.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| TKT-001 | MATCH | `$TD create "Printer on fire"`, then `$TD list` | `#1 open Printer on fire`, exit 0. List shows `#1 [P3] open     Printer on fire`. |
| TKT-002 | MATCH | `$TD create ""` and `$TD create "   "` | `error: title is required` on stderr, exit 2. `list` prints nothing. |
| TKT-003 | MATCH | `create a --priority P1`, `P2`, `P3`, and `create d` | List shows `[P1]`, `[P2]`, `[P3]`, and `[P3]` for the default. |
| TKT-004 | MATCH | `create x --priority P9` and `--priority p1` | Both exit 1. Last stderr line is `ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']` (and `'p1'`). `list` prints nothing. |
| TKT-005 | MATCH | Create a, b, c. `close 3 "long enough note"`. Create d. | The new ticket is `#4`. |
| TKT-006 | MATCH | `create a`, `assign 1 dana`, `assign 1 bob`, `list` | `#1 assigned -> dana`, then `#1 assigned -> bob`, exit 0. List shows `assigned`. |
| TKT-007 | MATCH | `assign 1 ""` and `assign 1 "  "` | `error: assignee is required`, exit 2. Log stays at 1 line. |
| TKT-008 | MATCH | Create, close, then `assign 1 dana` | `error: ticket 1 is closed`, exit 2. Log stays at 2 lines. |
| TKT-009 | MATCH | `close 1 "long enough note"` on an open ticket. Then assign and close ticket 2. | `#1 closed` and `#2 closed`, exit 0. |
| TKT-010 | MATCH | `close 1` with `123456789`, `"  123456789  "`, `"      1234567"`, then `1234567890` | The first three print `error: resolution note must be at least 10 characters`, exit 2. The 10-character note prints `#1 closed`. |
| TKT-011 | MATCH | Close ticket 1 twice | Second call prints `error: ticket 1 is already closed`, exit 2. Log stays at 2 lines. |
| TKT-012 | MATCH | `assign 9 x`, `close 9 ...`, `assign abc x`, `assign 1.5 x`, no command, `frobnicate`, missing and extra arguments, `create a --priority` | `error: no ticket 9` for unknown IDs. All parser refusals print a `usage:` line and an error line, exit 2. Log stays at 1 line. |
| TKT-013 | MATCH | Four tickets in mixed states, one title with a newline, then `list` | Ascending order, closed included. `#2 [P3] closed   Laptop slow`. The newline title spans two lines. Empty log prints nothing. |
| TKT-014 | MATCH | Runs of TKT-006, TKT-008, TKT-009, TKT-011 | open to assigned, assigned to assigned, open to closed, and assigned to closed succeed. Any move out of `closed` is refused. |
| TKT-015 | DRIFT | See DRIFT details | Parser refusals print two lines on stderr, not one `error: <reason>` line. |
| TKT-016 | MATCH | `--help`, each command's `--help`, `--version`, `-V` | Usage on stdout, exit 0, names `--log` and the four commands. `create --help` names `--priority`. `--version` and `-V` are refused with exit 2. |

## event-log.md

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| LOG-001 | MATCH | `list` in an empty directory, then `create a`, then `ls -A` | `list` prints nothing, exit 0, no file. After `create` the directory holds `tickets.jsonl`. |
| LOG-002 | MATCH | `--log sub/x.jsonl create a`. With `TICKETDESK_LOG` set, `create b`, then `--log flag.jsonl create c`. | `sub/x.jsonl` is created. `create b` writes `env.jsonl`. `--log` wins and writes `flag.jsonl`. |
| LOG-003 | MATCH | `create`, `assign`, `close`, then `cat tickets.jsonl` | One JSON object per line, keys in alphabetical order, each with `at`, `id`, `kind`. |
| LOG-004 | MATCH | `create "  Zoë  " --priority P2`, `assign 1 " Zoë "`, `close 1 "  résumé note ok  "`, `cat`, `list`, `grep -c Zoë` | Log has `priority`, `title`, `assignee`, `resolution`. Whitespace is kept. `Zoë` is escaped. `list` prints `Zoë`. `grep` finds 0 lines. |
| LOG-005 | MATCH | Two creates, copy the log, `assign 1 x`, compare the first bytes, then `list` | The log grows from 2 to 3 lines. The first bytes equal the copy. `list` leaves the file unchanged. |
| LOG-006 | MATCH | `create x --priority P9`, `create ""`, `create a`, then `close 1 short`, `close 9 ...`, `frobnicate`, `--priority p1` | No file exists after the first two. After the later refusals `cmp` shows the log unchanged. |
| LOG-007 | MATCH | Append `not json`, then `list`, `create b`, `assign 1 x`. Then append `[1,2]`, and use a log of `{"id":1,"at":1}`. | Exit 1 each time. Last line is `ValueError: tickets.jsonl:2: corrupt event: Expecting value: line 1 column 1 (char 0)`. Log stays at 2 lines. Array gives `TypeError`, no-`kind` object gives `KeyError: 'kind'`, with no file or line. |
| LOG-008 | MATCH | Append an empty line and a whitespace line, `create b`, `list` | `list` shows tickets 1 and 2. |
| LOG-009 | MATCH | Build a log, copy it to `c/copy.jsonl`, run `list` on both | Both print the same two lines. |
| LOG-010 | MATCH | `--log d` (a directory) with `list`, `create`, `assign`. `TICKETDESK_LOG=""`. `--log nodir/x.jsonl` with `create` and `list`. | Directory and empty variable: exit 1, last line `IsADirectoryError`. Missing directory: `create` exits 1 with `FileNotFoundError` and creates no file. `list` prints nothing, exit 0. |

## DRIFT details

### TKT-015: Refusals share one shape

Spec text: "Every refusal of a ticket rule has the same shape. That covers TKT-002, TKT-007, TKT-008, TKT-010, TKT-011, and TKT-012. The command prints one line `error: <reason>` on stderr and nothing on stdout."

TKT-012 covers parser refusals. Those print a `usage:` line and an error line, which TKT-012 also says. The two criteria disagree with each other, and the product follows TKT-012.

Command and output:

```
$ ticketdesk assign abc x
--stdout:
--stderr:
  usage: ticketdesk assign [-h] id assignee
  ticketdesk assign: error: argument id: invalid int value: 'abc'
--rc=2
```

The same command with an unknown ID, `ticketdesk assign 9 x`, does match the shape: one line `error: no ticket 9`, exit 2.

Most likely cause: `argparse` prints its own usage and error text before any ticket rule runs. This is a likelihood, not a verified fact.

## UNCOVERED behaviours

### Order of refusal checks

When one command breaks two rules, the product reports one of them. No criterion says which.

```
$ ticketdesk close 1 short        (ticket 1 is closed)
  error: ticket 1 is already closed          rc=2
$ ticketdesk assign 1 ""          (ticket 1 is closed)
  error: ticket 1 is closed                  rc=2
$ ticketdesk close 9 short
  error: no ticket 9                         rc=2
$ ticketdesk create "" --priority P9
  error: title is required                   rc=2
```

A corrupt log plus an empty title reports `error: title is required` with exit 2. A corrupt log plus `close 1 short` gives the exit 1 traceback. Nearest criteria: TKT-015 and LOG-007.

### An event with an unknown kind is ignored

```
$ cat e1.jsonl
{"at":1,"id":1,"kind":"reopened"}
$ ticketdesk --log e1.jsonl list
--stdout:
--stderr:
--rc=0
```

LOG-003 limits `kind` to three values. LOG-007 stops every command for a JSON line that "is not an event", with two examples. This case is neither. Nearest criteria: LOG-003 and LOG-007.

### An event for a ticket that was never created crashes

```
$ cat e2.jsonl
{"at":1,"id":5,"kind":"assigned","assignee":"x"}
$ ticketdesk --log e2.jsonl list
(traceback)
KeyError: 5
--rc=1
```

The traceback names neither the file nor the line. LOG-007 says that for its examples, but this event is well formed and refers to no ticket. Nearest criterion: LOG-007.

## BLOCKED and OPEN

- **BLOCKED:** none.
- **OPEN:** none. No criterion carries a TODO.

## Artifacts

All under `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/01058b7d-e98e-4d3f-a81c-e8ba15a8c683/scratchpad/exp8/run-3/drift-scratch/`:

- `src/`: copy of the package and `pyproject.toml`.
- `venv/`: the install.
- `work/`: one fresh directory per case, with its log file.
- `cases-independent.md`, `lib.sh`, `run1.sh`, `run2.sh`, `run3.sh`: case list and scripts.
- `evidence-1.log`, `evidence-2.log`, `evidence-3.log`, `evidence.log`: raw output.

No file in the repo changed.

The scratch directory already held files from an earlier run, such as `cases.md`, `ev.sh`, and `seg2.sh` to `seg5.sh`. I did not edit them. I did overwrite the earlier `evidence.log` with my concatenated log, without reading it first. That earlier content is lost. My `rm -rf` of `work/<case>` directories only touched names my own scripts use.

## Decision

You now decide whether the spec or the product changes for TKT-015. You also decide per UNCOVERED item whether it gets a criterion.

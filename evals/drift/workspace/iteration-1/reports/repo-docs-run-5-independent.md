# Drift report: ticketdesk 0.3.0

The run covered 22 criteria: 21 MATCH, 0 DRIFT, 0 BLOCKED, 1 OPEN, and 4 UNCOVERED behaviours. No criterion drifted. The OPEN item is TKT-002, whose own text carries a TODO. The run took about 10 minutes and the host reported no money cost beyond the session budget.

## Scope and surface

The scope is every feature criterion in `docs/product-specs/tickets.md` (TKT-001 to TKT-014) and `docs/product-specs/event-log.md` (LOG-001 to LOG-008). The invariants in `invariants.md` were checked only where a feature criterion makes them observable. The specs are uncommitted, and that changed nothing about the check.

The user is a support agent in a shell. The surface is the `ticketdesk` binary, installed the way `pyproject.toml` declares it. I installed a copy of the repo into a fresh virtual environment outside the repo. The environment is local. The log file is a declared product surface, so I read it too.

Assumption: nobody could answer questions, so I treated `ticketdesk` as the invocation form. The specs name the commands in that form.

Evidence logs:
- `drift-work/evidence.log` holds the main run. Each command shows stdout, stderr, and exit code.
- `drift-work/evidence2.log` holds the stream checks and the log-damage probes.

Numbers in quoted logs differ between runs because the log stores the clock time.

## Tickets (`tickets.md`)

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| TKT-001 | MATCH | `ticketdesk create "Printer on fire"` | stdout `#1 open Printer on fire`, exit 0 |
| TKT-002 | OPEN | `ticketdesk create Mouse --priority P2`, `create x --priority P9`, `create x --priority p1` | P1, P2 and omitted (P3) listed as `[P1]`, `[P2]`, `[P3]`. P9 and p1 exit 1 with a Python traceback. No log file was created (`ls` showed none). The settled part holds. |
| TKT-003 | MATCH | `ticketdesk create ""` and `create "   "` | stderr `error: title is required`, exit 2, stdout empty |
| TKT-004 | MATCH | create A, B, C, close 3, create D, list | numbers 1, 2, 3, then `#4 open D` after ticket 3 closed |
| TKT-005 | MATCH | `ticketdesk assign 1 dana` | stdout `#1 assigned -> dana`, exit 0 |
| TKT-006 | MATCH | `ticketdesk assign 1 bob` after dana | stdout `#1 assigned -> bob`, exit 0, list shows `assigned` |
| TKT-007 | MATCH | `ticketdesk assign 1 ""` and `assign 1 "  "` | stderr `error: assignee is required`, exit 2 |
| TKT-008 | MATCH | `ticketdesk close 1 1234567890`, and `close 2 "straight from open"` | stdout `#1 closed` from state `assigned`, `#2 closed` from state `open`, exit 0 |
| TKT-009 | MATCH | `close 1 short`, `close 1 "   short    "`, `close 1 123456789`, `close 1 1234567890` | first three: stderr `error: resolution note must be at least 10 characters`, exit 2, state unchanged. Ten characters: accepted. |
| TKT-010 | MATCH | `assign 1 eve`, then `close 1 "another long note"` on a closed ticket | stderr `error: ticket 1 is closed` and `error: ticket 1 is already closed`, both exit 2, list shows `closed` |
| TKT-011 | MATCH | `ticketdesk assign 99 x` and `close 99 "long enough note"` | stderr `error: no ticket 99`, exit 2 |
| TKT-012 | MATCH | create three tickets with P1, P3, P2, then `list` | `#1 [P1] open     Printer on fire`, one line per ticket in ascending order, exit 0. Empty log prints nothing. |
| TKT-013 | MATCH | no command, `create`, `assign`, `assign abc dana`, `close 1`, `close x "..."`, `bogus`, `list extra` | usage on stderr, exit 2 each time |
| TKT-014 | MATCH | `--help`, `-h`, `create --help`, `assign -h`, `close --help`, `list --help` | usage on stdout, stderr empty, exit 0, no log file created |

## Event log (`event-log.md`)

| ID | Verdict | Command run | Observed |
|---|---|---|---|
| LOG-001 | MATCH | `ticketdesk create "Printer on fire"` in an empty directory | `tickets.jsonl` created in the current directory |
| LOG-002 | MATCH | `TICKETDESK_LOG=env.jsonl ticketdesk create B`, then `--log opt.jsonl create C` | with the variable set, `env.jsonl` was written. With `--log` also given, `opt.jsonl` was written and `env.jsonl` kept only B. After the command, `create D --log z.jsonl` exits 2 (`unrecognized arguments`), which matches "before the command". |
| LOG-003 | MATCH | `ticketdesk --log nope.jsonl list` | no output, exit 0, `nope.jsonl` not created. First `create` created the file. |
| LOG-004 | MATCH | create, assign, close on one ticket | `wc -l` shows 3 lines, each one JSON object |
| LOG-005 | MATCH | `cat tickets.jsonl` after create, assign, close | `{"at": 1794327365.78..., "id": 1, "kind": "created", "priority": "P3", "title": "A"}`, plus `assignee` and `resolution` on the other kinds. `at` matched `date +%s` to the second. |
| LOG-006 | MATCH | `list`, then `close 1 short`, `assign 9 x`, `create ""`, `create x --priority P9`, `assign 1 y`, `close 1 "twice twice twice"`, `create`, each followed by `cmp` | file identical to its copy after all of them |
| LOG-007 | MATCH | `create E` after a 3-line log, then `head -n 3 \| cmp` against the saved copy | first 3 lines identical, file has 4 lines |
| LOG-008 | MATCH | `cp tickets.jsonl copy.jsonl`, then `--log copy.jsonl list` against the original | `cmp` found the outputs identical |

## DRIFT details

None.

## UNCOVERED behaviours

**1. A corrupt record ends the command with a Python traceback and exit code 1.** INV-004 says a corrupt line "stops the command with an error". No criterion names the message, the stream, or the exit code. Specs name only exit codes 0 and 2.

```
$ printf 'garbage\n' >> tickets.jsonl
$ ticketdesk list
...
ValueError: tickets.jsonl:2: corrupt event: Expecting value: line 1 column 1 (char 0)
[exit 1]
```

`create` and `assign` fail the same way, and the log stayed byte for byte the same. Nearest criterion: INV-004, which is not tied to any feature criterion.

**2. A blank line in the log is skipped without an error.** A log holding an empty line, one valid `created` record, and another empty line lists that ticket and exits 0. A later `create` keeps the blank lines.

```
$ printf '\n{"kind":"created","id":1,"title":"T","priority":"P1","at":1}\n\n' > b.jsonl
$ ticketdesk --log b.jsonl list
#1 [P1] open     T
[exit 0]
```

Nearest criterion: INV-004 says the product "never skips the line". It speaks of a line that is not valid JSON, and an empty line may not count as a record.

**3. A log that parses but has the wrong shape ends in a traceback.** Exit code is 1 for each case.

```
$ echo '{}' > s.jsonl && ticketdesk --log s.jsonl list      -> KeyError: 'kind'
$ echo '[1]' > s2.jsonl && ticketdesk --log s2.jsonl list   -> TypeError: list indices must be integers or slices, not str
$ ticketdesk --log s3.jsonl list   (assigned record for ticket 7, no created record)  -> KeyError: 7
```

Nearest criterion: INV-004 covers invalid JSON only.

**4. A log path that cannot be used ends in a traceback.** Exit code is 1 for each case.

```
$ ticketdesk --log nodir/x.jsonl create A    -> FileNotFoundError: [Errno 2] No such file or directory: 'nodir/x.jsonl'
$ ticketdesk --log d list    (d is a directory)  -> IsADirectoryError: [Errno 21] Is a directory: 'd'
$ TICKETDESK_LOG= ticketdesk create A        -> IsADirectoryError: [Errno 21] Is a directory: '.'
```

Nearest criteria: LOG-002 and LOG-003 cover a named file that exists or is missing. They do not cover a missing parent directory, a directory, or an empty variable.

Input tolerance and the hidden due time are not reported as UNCOVERED. A title with surrounding spaces is stored as typed, which is input tolerance. The ticket due time is computed in the product but no command shows it, and the `tickets.md` non-goals cover that.

## BLOCKED and OPEN

BLOCKED: none.

OPEN: TKT-002 carries the TODO "how the product reports a priority outside the list is not settled. Today the user sees a Python traceback." The settled part, that no ticket is created, held. Lowercase `p1` is treated as outside the list.

## Artifacts

All under `drift-work/` next to this report. The repo has no changes (`git status` shows only the `AGENTS.md` and `docs/` that were untracked before the run).

- `venv/`: virtual environment with `ticketdesk` installed from a copy in `src/`.
- `run.sh`, `run2.sh`: case scripts.
- `evidence.log`, `evidence2.log`: command output.
- `w/`, `w2/`, `w3/`: scratch directories holding the log files the cases wrote.

## Decision

You decide what happens next. There are no DRIFT items to settle. For each UNCOVERED item 1 to 4, you decide whether it gets a criterion. You also decide how TKT-002 settles its TODO.

# Drift report: ticketdesk specs against the product

Of 31 feature criteria, 22 match the product, 5 drift, 3 are blocked, and 1 is open. The product also does three things that no criterion describes. The DRIFT items are TKT-010, TKT-012, LOG-005, CLI-001, and CLI-006. The run cost about $0.10 of the $5 budget and changed no repo file.

## Scope and surface

- **Spec set:** `docs/product-specs/` holds 31 feature criteria: TKT (13), LOG (9), and CLI (9). The invariants INV-001 to INV-005 are checked only through the feature criteria that cite them.
- **User and surface:** a shell user runs the `ticketdesk` binary. The README has no install section, so the `pyproject.toml` entry point is the install path.
- **Source under test:** a git archive of `HEAD` (commit 5b0c398), copied outside the repo. The binary was installed with pip into a scratch venv.
- **Environment:** local scratch only. Every write went to a scratch log file. No external service was called.
- **Evidence log:** `drift-work/evidence.log`, 983 lines. Each command appears with its stdout, stderr, and exit code, copied verbatim.

No one could be asked, so these assumptions drive the verdicts:

- A criterion with a clause that cannot be observed is BLOCKED, never MATCH.
- A traceback that carries the words the criterion requires counts as an error. This applies to TKT-003 and LOG-007 and is the one judgement call in this report.
- "State padded to 8 characters" means an 8-character field, followed by the single space of the template.

## Verdicts by spec file

### tickets.md (TKT)

| ID | Verdict | Command run (case in evidence.log) | Observed |
|----|---------|------------------------------------|----------|
| TKT-001 | MATCH | `create`, `assign`, `close`, `list` (create) | New tickets show `open`. Later states show `assigned` and `closed`. |
| TKT-002 | MATCH | `create ""`, `create "   "` (title-required) | `error: title is required`, exit 2. No log file written. |
| TKT-003 | MATCH | `create ... --priority P9`, `--priority p1` (priority) | Exit 1 with a traceback. The last line names the value and the allowed values. No event written. See the note below. |
| TKT-004 | MATCH | three creates, `close 1`, `create d` (ids) | IDs 1, 2, 3, then 4 after closing ticket 1. |
| TKT-005 | BLOCKED | `create ... --priority P1`, `list` (create) | No command prints a due time. |
| TKT-006 | MATCH | `assign 1 dana`, `assign 1 erin` (assign) | `#1 assigned -> dana`, then `#1 assigned -> erin`. |
| TKT-007 | MATCH | `assign 1 ""`, `assign 1 "   "` (assign-empty) | `error: assignee is required`, exit 2. Log stays at one line. |
| TKT-008 | MATCH | `close 1`, then `assign 1 dana` (assign-closed) | `error: ticket 1 is closed`, exit 2. List still shows `closed`. |
| TKT-009 | BLOCKED | `assign 1 dana`, `close 1 ...` (close) | Closing works: `#1 closed`, exit 0. The kept assignee is not printed by any command. |
| TKT-010 | DRIFT | `close 1` with 7, 8, 9, 10 characters (res-7, res-8, res-9, res-10, res-trim) | 7 characters rejected with `at least 8 characters`. 8 and 9 characters accepted. The spec says 10. |
| TKT-011 | MATCH | `close 1` twice (close-twice) | `error: ticket 1 is already closed`, exit 2. The log holds one closed event, with the first note. |
| TKT-012 | DRIFT | `assign 99 bob`, `close 99 ...` (unknown-ticket) | `error: ticket 99 not found`, exit 2. The spec says `no ticket 99`. |
| TKT-013 | MATCH | creates, `close 1`, `create`, `list` (ids) | Lines #1 to #4 in ID order. The closed ticket is included. |

### event-log.md (LOG)

| ID | Verdict | Command run (case in evidence.log) | Observed |
|----|---------|------------------------------------|----------|
| LOG-001 | MATCH | `wc -l` after create, list, assign, close, rejected assign (log-appends) | Line counts 1, 1, 2, 3, 3. `list` appends nothing. |
| LOG-002 | MATCH | log file after create, assign, close (log-appends) | Only `created`, `assigned`, and `closed` appear. |
| LOG-003 | MATCH | same log file (log-appends) | `created` has title and priority. `assigned` has assignee. `closed` has resolution. Every event has kind, id, and at. |
| LOG-004 | MATCH | `date +%s` before and after, plus the `at` values (log-appends) | `at` is a float such as 1794325997.224993, inside the run window. |
| LOG-005 | DRIFT | log file after create, and after a blank-line append (create, blank-lines) | Keys appear as kind, id, title, priority, at. They are not sorted. Blank lines are ignored: MATCH. Each line ends with a newline. |
| LOG-006 | MATCH | `list` and `test -e` on a missing log, then `create` (missing-log, empty-existing) | `list` prints nothing and creates no file. The first create prints `#1 open First ticket` and creates the file. |
| LOG-007 | MATCH | corrupt line appended, then `list`, `create`, `assign`, `close` (corrupt) | Each command exits 1 with a traceback ending in `t.jsonl:2: corrupt event: ...`. Stdout is empty. See the note below. |
| LOG-008 | MATCH | snapshot of line 1, then assign and close, then diff (append-only) | Line 1 is unchanged. |
| LOG-009 | BLOCKED | create, assign, close, two lists, and a list of a copied log (replay) | The visible states match across runs and copies. Due times, assignees, and resolutions are not printed. |

### cli.md (CLI)

| ID | Verdict | Command run (case in evidence.log) | Observed |
|----|---------|------------------------------------|----------|
| CLI-001 | DRIFT | no arguments, `bogus`, `count`, `--help` (subcommands) | No arguments and `bogus` exit 2 with usage. `count` exists, exits 0, and prints `2`. The help lists five subcommands. |
| CLI-002 | MATCH | env var only, flag over env, neither (log-path) | The env var is used. `--log` wins over the env var. Without either, `tickets.jsonl` in the working directory is used. |
| CLI-003 | MATCH | `create` with P1, with no priority, with P2 (create) | `#1 open Printer on fire`. The default priority shows as `[P3]`. |
| CLI-004 | MATCH | `assign 1 dana` (assign) | `#1 assigned -> dana`. |
| CLI-005 | MATCH | `close 1 ...` (close) | `#1 closed`. |
| CLI-006 | DRIFT | `list` of open, assigned, and closed tickets (list-format); `list` on an empty log (empty-existing) | `#2 [P3] assigned  assigned one` has two spaces before the title. The spec implies one. Empty output: MATCH. |
| CLI-007 | OPEN | rule-error runs in the cases listed for TKT-002, 007, 008, 011, 012 and exit-codes | Settled part MATCH: `error:` on stderr, exit 2, stdout empty. The TODO is quoted under BLOCKED and OPEN. |
| CLI-008 | MATCH | successful create, assign, close, and list (exit-codes, create) | Exit 0 and empty stderr each time. |
| CLI-009 | MATCH | `assign abc bob`, `close abc ...` (bad-id) | Usage error on stderr, exit 2. The log stays at one line. |

TKT-003 and LOG-007 are MATCH because the promised content appears. The error reaches the user as a traceback, which the CLI-007 TODO already records. If you read "fails with an error" as a clean CLI error, both become DRIFT.

## DRIFT details

### TKT-010: Resolution note minimum length

The spec says: "A resolution note shorter than 10 characters, after trimming surrounding whitespace, is rejected with the error `resolution note must be at least 10 characters`."

```
$ ticketdesk --log t.jsonl close 1 12345678      # 8 characters
#1 closed                                        # exit 0
$ ticketdesk --log t.jsonl close 1 1234567       # 7 characters
error: resolution note must be at least 8 characters   # exit 2
```

Most likely cause (high): commit 5b0c398 changed `< 10` to `< 8` in `ticketdesk/tickets.py`, and changed the message to match. The spec files were last changed in fb600c5, before that commit.

### TKT-012: Unknown ticket

The spec says: "fails with the error `no ticket <id>`."

```
$ ticketdesk --log t.jsonl assign 99 bob
error: ticket 99 not found        # exit 2
```

Most likely cause (high): commit 5b0c398 changed the message in `ticketdesk/tickets.py`.

### LOG-005: Line format

The spec says: "Each event is one line of JSON with keys sorted alphabetically, ended by a newline."

```
$ ticketdesk --log t.jsonl create "Printer on fire" --priority P1
$ cat t.jsonl
{"kind": "created", "id": 1, "title": "Printer on fire", "priority": "P1", "at": 1794325995.197546}
```

Most likely cause (high): commit 5b0c398 removed `sort_keys=True` from `json.dumps` in `ticketdesk/store.py`.

### CLI-001: Subcommands

The spec says: "The `ticketdesk` command takes one of four subcommands. They are `create`, `assign`, `close`, and `list`."

```
$ ticketdesk --log t.jsonl count
2                                 # exit 0
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list,count} ...
```

Most likely cause (high): commit 5b0c398 added the `count` subparser and its branch in `ticketdesk/cli.py`.

### CLI-006: List format

The spec says: "with the state padded to 8 characters."

```
#1 [P3] open      open one
#2 [P3] assigned  assigned one
#3 [P3] closed    closed one
```

The spec implies one space after `open`, and one after `assigned`. The output has six and two. Most likely cause (high): commit 5b0c398 changed `{t.state:<8}` to `{t.state:<9}` in `ticketdesk/cli.py`.

The likely causes are readings of the git diff. None is confirmed by a run of the old code.

## UNCOVERED behaviours

### U1: `count` subcommand

`ticketdesk --log t.jsonl count` prints the number of tickets and exits 0. Nearest criterion: CLI-001, which lists four subcommands and is already DRIFT.

### U2: Unwritable log directory

`ticketdesk --log <scratch>/no-such-dir/t.jsonl create x` prints a Python traceback that ends in `FileNotFoundError`, and exits 1. Nearest criteria: CLI-002 chooses the path but says nothing about a missing directory. CLI-007 covers rule errors only.

### U3: Help output

`ticketdesk --help` prints the usage line with `{create,assign,close,list,count}` and the option `--log LOG  path of the event log`. Nearest criterion: CLI-001.

## BLOCKED and OPEN

- **BLOCKED TKT-005:** needs a command or output line that shows the due time.
- **BLOCKED TKT-009:** needs a command that prints a ticket's assignee after it closes.
- **BLOCKED LOG-009:** needs a command that prints due times, assignees, and resolutions.
- **OPEN CLI-007:** the TODO reads: "Confirm with the user whether CLI-007 should cover them, then fix either the code or this spec." The full TODO names TKT-003 and LOG-007. Its settled part is MATCH.

## Artifacts

- `drift-work/` in the scratch area, outside the repo: `src/` (git archive of `HEAD`), `venv/` (installed package), `cases/` (one log per case), `evidence.log`, and `run-cases.sh`.
- `drift-report.md`, this file.
- Repo: no file changed. `git status` was clean before and after the run.

## Decision

You now decide, for each DRIFT, whether the spec or the product changes. For each UNCOVERED item, you decide whether it gets a criterion. You also decide whether CLI-007 covers the traceback cases, which settles TKT-003 and LOG-007.

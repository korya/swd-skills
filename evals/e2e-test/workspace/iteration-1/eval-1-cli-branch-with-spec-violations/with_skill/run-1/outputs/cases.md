# Case list (contract, written before execution)

Scope: branch feature/cli-tidy vs main (PR.md: list output, resolution minimum, assign on closed, --help description),
specs CLI-001..009, TKT-001..013, LOG-001..009, INV-001..005, and the blast radius (every subcommand shares the log path and the replayed store).
Surface: shell user running `python3 -m ticketdesk.cli` from the repo root, as AGENTS.md documents. Environment: local dev, log under OUTPUT_DIR. Depth: comprehensive.

| # | Case | Spec/ref |
|---|---|---|
| 1 | `--help` exits 0, lists the four subcommands, `--log`, and the new description line, spelled correctly | CLI-001, PR |
| 2 | No subcommand: usage on stderr, nothing on stdout, exit 2 | CLI-001 |
| 3 | Unknown subcommand: usage on stderr, exit 2 | CLI-001 |
| 4 | `list` on a missing log prints nothing, exit 0, creates no file | LOG-006, CLI-006 |
| 5 | First `create` without `--priority` prints `#1 open <title>`, exit 0, empty stderr, creates the file | CLI-003, CLI-008, LOG-006 |
| 6 | Second `create --priority P1` prints `#2 open ...`; IDs rise by one | CLI-003, TKT-004 |
| 7 | `create ""` and `create "   "`: `error: title is required`, exit 2, empty stdout, no event appended | TKT-002, CLI-007, LOG-001 |
| 8 | `create --priority P9`: error names the value and the allowed values, exit 2, no ticket | TKT-003, CLI-007 (open TODO) |
| 9 | `create --priority p1` (lowercase) is rejected like any other value | TKT-003 |
| 10 | `list` line format `#<id> [<priority>] <state> <title>`, state padded to 8 | CLI-006 |
| 11 | `list` order: ID ascending, closed tickets included | TKT-013 |
| 12 | `assign 1 dana` on an open ticket prints `#1 assigned -> dana`, exit 0; `list` shows `assigned` | CLI-004, TKT-006 |
| 13 | Reassigning an assigned ticket replaces the assignee (visible in the log's latest `assigned` event) | TKT-006 |
| 14 | `assign 1 ""` and `assign 1 "  "`: `error: assignee is required`, exit 2, no event appended | TKT-007, CLI-007 |
| 15 | `assign 99 dana`: `error: no ticket 99`, exit 2 | TKT-012 |
| 16 | `assign abc dana`: usage error on stderr, exit 2, no event appended | CLI-009 |
| 17 | `assign 1` with the assignee missing: usage error, exit 2 | CLI-001 |
| 18 | `close 2 "Replaced the toner cartridge"` on an open ticket prints `#2 closed`, exit 0; `list` shows `closed` | CLI-005, TKT-009 |
| 19 | Closing an assigned ticket keeps the assignee (log keeps the assigned event, state closed) | TKT-009 |
| 20 | `close` with a 9-character note (`duplicate`) is rejected with `resolution note must be at least 10 characters`; ticket state unchanged | TKT-010 |
| 21 | `close` with an 8-character note is rejected with the same message | TKT-010 |
| 22 | `close` with a 10-character note is accepted | TKT-010 |
| 23 | `close` with a note that is 10+ characters only because of surrounding whitespace is rejected | TKT-010 |
| 24 | Closing a closed ticket: `error: ticket <id> is already closed`, exit 2; resolution unchanged | TKT-011 |
| 25 | Assigning a closed ticket: `error: ticket <id> is closed`, exit 2; ticket unchanged, state stays `closed` | TKT-008, TKT-001 |
| 26 | `close 99 "Long enough note"`: `error: no ticket 99`, exit 2 | TKT-012 |
| 27 | `close abc "Long enough note"`: usage error, exit 2 | CLI-009 |
| 28 | `TICKETDESK_LOG` is used when `--log` is absent | CLI-002 |
| 29 | `--log` wins over `TICKETDESK_LOG` | CLI-002 |
| 30 | Without either, `tickets.jsonl` in the current directory is used | CLI-002 |
| 31 | Log lines: one JSON object per line, keys sorted, `kind`/`id`/`at` on every event, extra fields per kind, `at` is epoch seconds | LOG-002, LOG-003, LOG-004, LOG-005 |
| 32 | `list` appends nothing; each create/assign/close appends exactly one line | LOG-001 |
| 33 | Appending leaves existing lines byte-for-byte unchanged | LOG-008, INV-002 |
| 34 | Blank lines in the log are ignored on replay | LOG-005 |
| 35 | A corrupt line stops every operation with an error naming the path, line number, and `corrupt event`; later lines are not read | LOG-007, INV-004 (open TODO) |
| 36 | Creating after a close continues the ID sequence; closed IDs are not reused | INV-003, TKT-004 |
| 37 | Title with spaces and non-ASCII characters is stored and listed verbatim | CLI-003, CLI-006 |
| 38 | `list | head -1` in a pipe exits cleanly with no traceback | shell contract |
| 39 | `create --help`, `assign --help`, `close --help` describe their arguments | shell contract |
| 40 | Success commands write nothing to stderr (checked across 5, 6, 12, 18) | CLI-008 |

Not derivable at the surface: TKT-005 due time (no command shows it; the log stores only priority).

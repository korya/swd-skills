# Drift actions

One line per DRIFT, BLOCKED, OPEN, and UNCOVERED item in `drift-report.md`, with what was
done about it. Every action changed spec text only. No code or test changed.

| Item | Verdict | Action |
|---|---|---|
| TKT-013 | DRIFT | Fixed the text: "one line per ticket" became "one entry per ticket", and the criterion now says the title is printed as given, so a title with a newline spans more lines. Question 7 asks whether a newline in a title should be refused instead. |
| (none) | BLOCKED | No BLOCKED item in the report. |
| (none) | OPEN | No OPEN item in the report. |
| 1. Help output | UNCOVERED | Added TKT-016: `--help` on the top command and on each command prints the usage and exits 0, and there is no `--version`. The missing description of `--priority` and the silent `TICKETDESK_LOG` go to question 8 as a UX gap, not a contract. |
| 2. Argument errors print a two-line usage message | UNCOVERED | Extended TKT-012 to cover a missing or unknown command, a missing or extra argument, and an option without a value: usage line plus error line on stderr, exit 2, nothing written. |
| 3. Empty `TICKETDESK_LOG` ends in a traceback | UNCOVERED | Added LOG-010, which names the empty variable as a path to the current directory and records the `IsADirectoryError` exit 1. Question 9 asks whether the crash is intended. |
| 4. `--log` naming a directory ends in a traceback | UNCOVERED | Covered by the new LOG-010. Question 9. |
| 5. `--log` under a missing directory | UNCOVERED | Covered by the new LOG-010 (`create` exits 1 with `FileNotFoundError`, `list` prints nothing and exits 0) and LOG-002 now says the file is created only when its directory exists. Question 9. |
| 6. A valid JSON line that is not an event | UNCOVERED | Extended LOG-007: such a line also stops every command with exit 1, and the traceback names neither the file nor the line. Question 10 asks whether it should get the `corrupt event` message. |
| 7. An event with an unknown `kind` is ignored | UNCOVERED | No criterion added. The behaviour contradicts the intent of INV-004 (no command skips a line), so blessing it in a spec is the user's call. Listed as question 11. |
| 8. A closed stdout pipe ends in exit 120 | UNCOVERED | No criterion added. Listed as question 12, since the exit code and the `BrokenPipeError` message are interpreter behaviour the team may or may not want to promise. |
| 9. Non-ASCII text is written as escapes | UNCOVERED | Fixed LOG-004: values keep their whitespace, and a non-ASCII character is stored as a `\uXXXX` escape, so a plain text search of the file finds nothing while `list` prints the original. |

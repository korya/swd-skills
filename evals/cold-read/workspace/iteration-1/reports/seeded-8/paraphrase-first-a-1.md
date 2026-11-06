PARAPHRASE

The document proposes "overdue" as a flag computed when tickets are read. It adds no new state and no new event, and it stores nothing in the log. `ticketdesk list` would show `OVERDUE` in the state column for tickets that are not closed and are past their due time. A new `ticketdesk overdue` subcommand would print only those tickets in the same line format, sorted by due time and then by ID. The work is gated on the user signing off six spec edits. It then covers service code, CLI wiring, the first CLI test suite, and doc updates.

According to the document alone, the system works as follows. `TicketService` replays the log to build tickets, each with a creation time and a due time. The CLI has four subcommands, and `list` is the final `else` branch. The store and `sla.py` hold the log and the hours per priority. Tests use `pytest` and a fake `Clock`, and there are 7 passing tests and no CLI tests.

FINDINGS

- Severity: Blocker
  Where: Plan step 2, `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`
  What: The plan adds a second hours table, and its P3 value is wrong. The spec says 72 hours, and `sla.py` already holds the table and `due_at`. Tickets also already carry `due_at`. A P3 ticket would be flagged overdue 24 hours early, and the table would drift from TKT-005.
  Evidence: `sla.py:3` has `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`. TKT-005 says P3 is 72 hours. `tickets.py:36` has `t.due_at = due_at(...)`. A1 in the plan notes that tickets carry their due time, yet step 2 does not use it.

- Severity: Blocker
  Where: Plan step 2, `Ticket.is_overdue`, `now >= created_at + ...`
  What: The code uses `>=`, so a ticket is overdue at the due time exactly. TKT-014 as drafted, open question 3, and the A6 test all say it is not overdue at that moment.
  Evidence: Step 1 says "At the due time exactly, it is not overdue." Step 2 has `now >= self.created_at + ...`. The test plan expects "not overdue ... at the due time exactly". Following the plan as written would fail its own boundary test.

- Severity: Blocker
  Where: Plan step 2, `TicketService.overdue`, `key=lambda t: (t.created_at, t.id)`
  What: The sort is by creation time, but the request and TKT-015 require ascending due time. Because the hours differ by priority, the two orders differ. A P3 ticket created at hour 0 is due at hour 72. A P1 ticket created at hour 10 is due at hour 14, so it is due first.
  Evidence: The plan's own TKT-015 says "sorted by due time ascending". A4 and the P1-before-P3 test describe due-time order. Creation order would return the P3 ticket first, which fails that test. The correct key is `t.due_at`.

- Severity: Blocker
  Where: Plan step 1, "`cli.md` CLI-009 (new)", and the plan's reference to "next free number"
  What: CLI-009 already exists as "Ticket ID is an integer". The plan would reuse an ID that is already taken. docs/README.md says IDs are stable and a new spec takes the next free number, so the new spec should be CLI-010. The same wrong ID appears in step 8, the test plan, and the "Reflected in plan" list.
  Evidence: `docs/product-specs/cli.md:58` is `### CLI-009: Ticket ID is an integer`. `docs/README.md:27-28`: "A new spec gets the next free number."

- Severity: Major
  Where: Plan step 5, A5, and the conventions list. The plan names `pytest`, `tmp_path`, and `make lint && pytest -q`.
  What: The project uses `unittest`, and `pytest` is not installed. The Makefile runs `unittest discover`. Step 7 would fail, and `tmp_path` is unavailable. `tests/test_cli.py` should use `unittest` and `tempfile`, as `tests/test_tickets.py` does.
  Evidence: `Makefile:3` is `python3 -m unittest discover -s tests -q`. `import pytest` gives `ModuleNotFoundError`. AGENTS.md says "Tests | `unittest`, `make test`". The plan's convention entry cites "AGENTS.md:22-23, Makefile:1-5: the suite runs under `pytest`". Those lines say the opposite.

- Severity: Major
  Where: Plan step 3, last bullet
  What: The plan says a missing subcommand currently falls into the `list` branch because the subparsers are not marked required. They are marked required. The stated reason for changing `else:` to `elif` is false. The change is still reasonable for other reasons.
  Evidence: `cli.py:14` has `sub = parser.add_subparsers(dest="cmd", required=True)`.

- Severity: Major
  Where: Assumptions table A3, A4, A5, A6, A8, and the sources `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py`
  What: The evidence for these "confirmed" results cannot be checked. The scratch scripts are not in the repo. There is no `scratch/` directory, and git status shows only `plan.md` as untracked. A4 also uses a P3 ticket "created 80 h ago", which would not be overdue under the 48-hour table in step 2 but is overdue under the real 72 hours.
  Evidence: `ls scratch` gives "No such file or directory".

- Severity: Minor
  Where: Plan step 6, line citations AGENTS.md:102/114/116 and architecture.md:94-96/103
  What: The AGENTS.md lines match: `make test` says "7 unittest cases", and "Done" and "Not covered" are at 114 and 116. The architecture.md citations are not what the plan says. The sentence "The CLI is not covered by tests today" is near line 103, and the layout is near 92-98. I did not verify every line number.
  Evidence: `docs/architecture.md` shows the layout and the sentence in that region. I only spot-checked the numbers.

- Severity: Minor
  Where: Plan step 1, LOG-001 row, and the "six spec changes" in the Headline
  What: The count works out to six rows, so the count is fine. The sign-off needs more, because step 6 adds architecture.md and AGENTS.md edits and architecture.md:12 needs `overdue` added, so the ask is more than six changes. It also leaves out the CLI-007 TODO, which AGENTS.md lists as an open conflict.
  Evidence: Headline: "your sign-off on six spec changes". Step 6 lists further doc edits.

MISSING DECISIONS

- The plan never says what `ticketdesk overdue` prints for the `OVERDUE` label's underlying state. It does list this as open question 2, so that one is not hidden.
- It does not say whether `now` is passed to `list()` for filtering or only for labels.
- It does not say what happens to the 4→5 subcommand count in the README.md, which the plan never mentions.
- It does not say which of the plan's own assumptions the user should rule on first. The "blocking" gate (question 5) is stated, but the three code blockers above need fixing before any sign-off.

Note: the tests and lint pass on HEAD (7 tests OK). I changed nothing.
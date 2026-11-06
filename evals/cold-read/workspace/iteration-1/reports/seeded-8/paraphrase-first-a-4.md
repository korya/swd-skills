PARAPHRASE

The plan adds overdue as a flag computed when tickets are read. It is never a new state or a logged event. A ticket is overdue if it isn't closed and the current time is later than its due time. `ticketdesk list` would show `OVERDUE` in place of the state column for those rows. A new `ticketdesk overdue` subcommand would print only overdue tickets, sorted by due time and then by ID. The work needs sign-off on six spec changes first. It then adds a rule in `tickets.py`, wires `cli.py`, adds unit tests and the first CLI subprocess tests, and updates the docs.

According to the document alone, the system has a CLI that calls `TicketService`, which replays an append-only log into tickets. Each ticket carries a creation time, a priority and a due time from an SLA table. The tests use a fake `Clock` and run under pytest. The CLI has no tests. `list` prints in ID order with a state padded to 8 characters, and the subparsers are not marked required.

FINDINGS

- Severity: Blocker
  Where: Step 2, `Ticket.is_overdue` and `OVERDUE_HOURS`
  What: The plan adds a second hours table with P3 = 48. The spec and the code say P3 = 72. The plan's formula also uses `>=`, which makes a ticket overdue at the exact due time. Its own TKT-014, tests and open question 3 say a ticket is not overdue at that moment. A ticket would be flagged 24 h early for P3, and the boundary test would fail.
  Evidence: sla.py:3 `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`, and TKT-005 gives P3 = 72. The plan says `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}` and `now >= self.created_at + ...`. TKT-014 in the plan says "At the due time exactly, it is not overdue."
  The plan's own A1 says `due_at` is already on every ticket, so the rule should be `now > self.due_at` with no second table. Step 2's "reuses" claim and the "Duplicate logic: no overdue code exists" sweep both miss this duplication.

- Severity: Blocker
  Where: Step 2, `TicketService.overdue` sort key
  What: The sort key is `(t.created_at, t.id)`. The request and TKT-015 say "oldest due first", which is sorted by due time. With mixed priorities the two orders differ.
  Evidence: The plan's `key=lambda t: (t.created_at, t.id)` against its TKT-015, "sorted by due time ascending". The plan's own test, "returns a P1 ticket created later before a P3 ticket created earlier", requires `due_at`. Sorting by `created_at` puts the P3 ticket first.

- Severity: Major
  Where: Step 1 table, `CLI-009 (new)`, and the Conventions entry for docs/README.md:27-28
  What: CLI-009 already exists as "Ticket ID is an integer". The plan reuses the ID, which breaks the stable-ID rule. The next free number is CLI-010. The same collision affects the step 8 commit citations, the test plan and the Test plan's "(CLI-009)" references.
  Evidence: cli.md:58 `### CLI-009: Ticket ID is an integer`. docs/README.md:27-28: "Never renumber... A new spec gets the next free number."

- Severity: Major
  Where: Step 3, last bullet, and the A7 assumption
  What: The plan says the subparsers are not marked required and that a missing subcommand falls into the `list` branch. The code already has `required=True`. The `else:`-to-`elif` change is therefore not for that reason. If it is made, any unmatched `cmd` silently does nothing.
  Evidence: cli.py:14 `sub = parser.add_subparsers(dest="cmd", required=True)`. The plan says "Today a missing subcommand also reaches that branch, because the subparsers are not marked required."

- Severity: Major
  Where: Steps 5 and 7, "Project conventions" first bullet, and the pytest `tmp_path` fixture
  What: The project runs tests with `unittest`, and pytest is not a declared dependency. It isn't installed on this machine. The plan's pytest claims contradict AGENTS.md. `tmp_path` and `pytest -q` also break the "no dependencies" rule, and CI runs `make test`. A pytest-style `tests/test_cli.py` would not be collected or run by `make test` or CI.
  Evidence: Makefile:3 `python3 -m unittest discover -s tests -q`. AGENTS.md:22 "Tests | `unittest`, `make test`". `python3 -m pytest --version` gives "No module named pytest". The plan's convention bullet says "the suite runs under `pytest`".

- Severity: Major
  Where: Assumptions table A3 to A8, Baseline, and the scratch-script references
  What: The evidence files can't be found. `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py` don't exist in the repo, and nothing is committed. The experiments E1 to E5 and the Python 3.12.16 rerun can't be checked. `plan.md` is the only untracked file.
  Evidence: `ls scratch` gives "No such file or directory". `git status` shows only `?? plan.md`.

- Severity: Major
  Where: Step 1 and Plan step 8 versus "six spec changes"
  What: The plan's list of spec changes does not touch TKT-013 and LOG-009, but it says they "hold". The list also leaves out the "four subcommands" wording in architecture.md:12 and the CLI-006 line shape for `create`. The Headline says six changes and the table has six rows, so that part is consistent. However, step 6 says "update the test count" without giving a number, and the plan doesn't say that the count is "7 unittest cases" at AGENTS.md:102.
  Evidence: AGENTS.md:102 `make test  # 7 unittest cases`. Plan step 6 gives no new count.

- Severity: Minor
  Where: Step 6, architecture.md:94-96/103, and the line-number citations
  What: Several cited lines are off or imprecise. The "not covered by tests" sentence is at architecture.md:101, not 103. The 8-character claim for the arrow label is at architecture.md:12. The architecture.md:44 citation for "no data migration" is correct.
  Evidence: architecture.md contains "The CLI is not covered by tests today." about 7 lines below the tree's `test_store.py` line.

- Severity: Minor
  Where: Step 3, `_line(t, now)`
  What: `create` and `assign` print their own lines, so `OVERDUE` never appears there. The plan doesn't say whether that is deliberate.
  Evidence: cli.py:23 and cli.py:25 print `t.state` directly.

DECISIONS LEFT TO THE NEXT READER

- Which `now` clock the CLI uses, and whether it should come from the store clock (INV-005 says time comes from the store's clock, never the caller). Step 3 uses `time.time()` in the CLI, which the plan does not reconcile with that.
- How `overdue` handles a ticket past its due time on a corrupt log. The plan says it inherits the traceback and defers to CLI-007.
- Whether `overdue` should show the underlying state. The plan marks it open question 2 and picks "reuse CLI-006".

I did not run the plan's code or tests, because the plan's changes don't exist yet.
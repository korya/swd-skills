PARAPHRASE

The plan adds "overdue" as a flag computed at read time. It is not a new state and not a new event. The service gets a rule that a ticket is overdue when it isn't closed and now is past its due time. `ticketdesk list` shows `OVERDUE` in place of the state for those rows. A new `ticketdesk overdue` command prints only overdue tickets in the `list` line format, sorted by due time and then ID. Work is gated on the user signing off six spec changes. After that come the service rule, the CLI wiring, unit tests, the first CLI test suite, doc updates, and three commits.

According to the document, the system is a layered CLI (`cli.py`, `tickets.py`, `store.py`) over an append-only JSON-lines log. Tickets are rebuilt by replaying the log. Each replayed ticket carries its creation time, priority and due time. The specs define due times by priority, the 8-character state column, and four subcommands. The suite is described as running under pytest, and the CLI is untested.

FINDINGS

- Severity: Blocker
  Where: Step 2, `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`
  What: The plan adds a second SLA table, and its P3 value is wrong. The spec says 72 hours, so P3 tickets between 48 and 72 hours old would show as overdue early. The ticket already carries `due_at` from `sla.py`, so no table is needed.
  Evidence: `sla.py:3` has `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`. TKT-005 says P3 is 72. `tickets.py:36` sets `t.due_at`. The plan itself says "the SLA table stays untouched" and A1 says every ticket "already carries its due time".

- Severity: Blocker
  Where: Step 2, `TicketService.overdue` sort key
  What: The key is `(t.created_at, t.id)`, which is creation order. TKT-015 and the request ask for due-time order. With mixed priorities these differ, so "oldest due first" is wrong. It also contradicts the plan's own test, which expects a later-created P1 before an earlier-created P3.
  Evidence: Plan line 40, `key=lambda t: (t.created_at, t.id)`. Plan line 31 (TKT-015) says "sorted by due time". Test plan line 118 expects the P1 created later to come first.

- Severity: Blocker
  Where: Step 2, `now >= ...`, against TKT-014 and the test plan
  What: The rule uses `>=`, so a ticket at its due time exactly is overdue. TKT-014 (line 30), open question 3 and the boundary test all say it is not overdue at that moment. An implementation that follows the code makes the boundary test fail.
  Evidence: Plan line 39 `now >= self.created_at + ...`. Plan line 30: "At the due time exactly, it is not overdue." Plan line 114.

- Severity: Blocker
  Where: Step 1, CLI-009 (new)
  What: CLI-009 already exists as "Ticket ID is an integer". The plan treats it as a free ID and would overwrite or duplicate it. IDs are stable and unique, and the next free CLI number is CLI-010. The step 5 and step 8 references to CLI-009 are wrong for the same reason.
  Evidence: `docs/product-specs/cli.md:58-61` has `### CLI-009: Ticket ID is an integer`. `docs/README.md:27-28` says a new spec gets the next free number. Plan line 34.

- Severity: Major
  Where: A4 and Test plan line 118, example E3
  What: The recomputed example does not give the claimed order. A P3 ticket created 80 h ago is due 8 h ago. A P1 ticket created 6 h ago is due 2 h ago. Oldest due first is `[1, 2]`, which is also ID order. The plan claims `[2, 1]`, and the same is true with its 48 h figure. So A4 is false as stated, and the proof test cannot distinguish due-time order from ID order. A pair that does differ is a P3 created 10 h ago (due in 62 h) and a P1 created 1 h ago (due in 3 h) to the extent both are overdue at a later "now", or simply a P1 created after a P2 where the P1 is due sooner.
  Evidence: Computed with the 72 h spec value: due = T−8 h for ticket 1 and T−2 h for ticket 2, so ticket 1 sorts first. Plan line 72.

- Severity: Major
  Where: Step 5, Step 7, Conventions (line 90), and Counterfactual
  What: The project does not use pytest. `make test` runs `unittest discover`, the stack table lists `unittest`, and pytest isn't installed or declared (dependencies: none). Step 5 relies on the pytest `tmp_path` fixture, and step 7 runs `pytest -q`. Neither `make test` nor CI would run or support these tests. The convention line misquotes AGENTS.md.
  Evidence: `Makefile:3` is `python3 -m unittest discover -s tests -q`. `AGENTS.md:22` says "Tests | `unittest`, `make test`". `python3 -m pytest` returns "No module named pytest". Plan lines 51, 58, 90.

- Severity: Major
  Where: Assumptions A3, A5, A6, A7, A8 and the E1–E5 evidence
  What: The evidence cannot be found. `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py` are cited as the proof, but no `scratch/` directory exists in the repo. The reviewer cannot confirm the results, and A4's result already fails recomputation.
  Evidence: `ls scratch` returns "No such file or directory". `git status` shows only `plan.md` untracked.

- Severity: Minor
  Where: Step 3, last bullet
  What: The plan says a missing subcommand today reaches the `list` branch because subparsers aren't required. They are required. Missing subcommands already exit 2 through argparse, so the stated reason for changing `else:` is false. The change is still harmless, but the justification is wrong.
  Evidence: `cli.py:14` has `add_subparsers(dest="cmd", required=True)`. CLI-001 says a missing subcommand exits 2.

- Severity: Minor
  Where: Step 3 and Step 1 CLI-006, plus the state-column claim
  What: A new `import time` plus `time.time()` in the CLI duplicates how the store gets timestamps. The store takes an injectable `clock`, which is how the tests are written. The CLI gets a second, uninjectable clock. This is acceptable but it should be a conscious choice. Passing the clock to the service would keep `now` inside the service layer.
  Evidence: `tests/test_tickets.py:20` uses `EventStore(..., clock=Clock())`. Plan line 9.

- Severity: Minor
  Where: Step 8, commit split
  What: The first commit includes "the specs", but the spec changes for CLI-001, CLI-006, CLI-009 and LOG-001 are listed in the second commit. The specs would land before the code they describe, or the commits cite IDs that don't yet exist. One logical change per commit is also muddied by mixing the `list` label change with the new subcommand and the first CLI suite.
  Evidence: Plan lines 61–63 against `docs/guidelines.md:82-87`.

- Severity: Minor
  Where: Step 6 and AGENTS.md line references
  What: The step says to update the AGENTS.md test count at line 102. That line only says "7 unittest cases" in a comment. The new suite would be pytest-based, so "unittest cases" would be false, which ties back to the pytest finding. The Out-of-scope CLI-007 note also says `overdue` "inherits" the traceback, but no test or spec change records that for overdue.
  Evidence: `AGENTS.md:102` reads `make test  # 7 unittest cases`.
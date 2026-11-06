PARAPHRASE

The plan proposes that "overdue" is a flag worked out when tickets are read. It is not a new state or a log event. `ticketdesk list` would show `OVERDUE` in place of the state for tickets that are not closed and are past due. A new `ticketdesk overdue` command would print only those tickets, ordered by due time and then by ID, in the same line format as `list`. The rule lives in `tickets.py`, the CLI reads the clock once per command, and it needs sign-off on six spec changes before any code is written.

According to the document alone, the existing system is a CLI that calls a service, which replays an append-only log through a store. Tickets have states `open`, `assigned` and `closed`, and each ticket already carries a creation time, a priority and a due time. `list` prints in ID order with the state padded to 8 characters. The CLI has no tests. Tests use a fake clock, run under pytest, and CI runs on Python 3.12. The plan treats specs and docs as needing user confirmation to change.

I could not paraphrase the scratch-script evidence (E1 to E5). It cites `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py`, which I only reach in step 2.

FINDINGS

- Severity: Blocker
  Where: Step 2, `OVERDUE_HOURS`, and the A1 row.
  What: The plan adds a second SLA table with `"P3": 48`. The real P3 SLA is 72 hours. Because `Ticket.due_at` already exists, the table is a duplicate of `SLA_HOURS` and its only value that differs from the real one is wrong. P3 tickets would turn overdue 24 hours early, and the table would have to be kept in sync with `sla.py` by hand.
  Evidence: plan.md:38 `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`. `ticketdesk/sla.py:3` `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`, and tickets.md:44 `| P3 | 72 |`. plan.md:69 (A1) itself says tickets.py:35-36 sets `t.due_at`. The fix is to use `t.due_at`.

- Severity: Blocker
  Where: Step 2, `Ticket.is_overdue`, against TKT-014 in the step 1 table and the Test plan.
  What: The code uses `>=`, so a ticket is overdue at its due time exactly. The plan's own spec says it is not overdue then, and the test plan checks for that.
  Evidence: plan.md:39 `now >= self.created_at + ...`. plan.md:30 "At the due time exactly, it is not overdue." plan.md:114 "not overdue ... at the due time exactly".

- Severity: Blocker
  Where: Step 2, `TicketService.overdue`.
  What: The sort key is `(t.created_at, t.id)`, which is creation order, not due-time order. The request and TKT-015 want oldest due first. For example, a P1 created 6 h ago and a P3 created 80 h ago would come back as `[1, 2]` and not `[2, 1]`. That contradicts the plan's own test (A4/E3) and its success criterion.
  Evidence: plan.md:40 `key=lambda t: (t.created_at, t.id)`. plan.md:31 "sorted by due time". plan.md:118 expects the P1 ticket created later to come before the P3 ticket created earlier. plan.md:171 "The P1-before-P3 test returns ID order".

- Severity: Major
  Where: Step 1, the CLI-009 (new) row, and the "next free number" convention.
  What: `CLI-009` already exists in `cli.md` as "Ticket ID is an integer". The plan would reuse an ID, which breaks "IDs are stable ... never renumber". The next free number is CLI-010. The `CLI-009` references in step 8 and in the test plan would then cite the wrong spec.
  Evidence: docs/product-specs/cli.md:58 `### CLI-009: Ticket ID is an integer`. docs/README.md:27-28 "A new spec gets the next free number." plan.md:34 "`cli.md` CLI-009 (new)". plan.md:98 "step 1 adds ... CLI-009".

- Severity: Major
  Where: Step 3, last bullet, and the A7 row.
  What: The plan says the subparsers are not marked required and that a missing subcommand reaches the `list` branch. They are required (`required=True`), so a missing command exits 2 in argparse. Changing `else:` to `elif` is harmless but is justified by a false premise, and the `else:` branch is not a missing-command path.
  Evidence: ticketdesk/cli.py:14 `sub = parser.add_subparsers(dest="cmd", required=True)`. plan.md:47 "because the subparsers are not marked required."

- Severity: Major
  Where: Step 5, step 7, the Conventions section, and the test plan.
  What: The plan uses pytest (`tmp_path`, `pytest -q`) for a project whose stack is unittest and stdlib-only, with CI running `make test`. pytest is not installed here, and the CI workflow never installs it. The new `tests/test_cli.py` would fail in CI. The plan also lists "the suite runs under `pytest`" as a convention it follows, which is wrong.
  Evidence: AGENTS.md:22 "Tests | `unittest`, `make test`". Makefile:3 `python3 -m unittest discover`. ci.yml:11-12 `make lint`, `make test`. `import pytest` gives `ModuleNotFoundError`. plan.md:90 "the suite runs under `pytest`". plan.md:58 "`make lint && pytest -q`". plan.md:51 "pytest `tmp_path` fixture".

- Severity: Major
  Where: Assumptions table (A3, A4, A5, A6, A7, A8), the Falsifier, and the Counterfactual.
  What: The evidence for A3 to A8 comes from `scratch/` scripts, and `scratch/` does not exist in the repo or in git status. The "confirmed" results cannot be checked. They also did not catch the sort, boundary or P3 errors above. A8's claim that the scripts ran on Python 3.12.16 cannot be checked either.
  Evidence: `ls scratch` gives "No such file or directory". `git status` shows only `?? plan.md`. plan.md:71 and plan.md:74 cite `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py`.

- Severity: Minor
  Where: Step 6, the AGENTS.md and architecture.md updates, and step 1's LOG-001 row.
  What: The plan does not update the "Not covered by tests: the CLI" TODO in guidelines.md:10-11, which also needs user confirmation. Its AGENTS.md line citations are accurate (102, 114, 116).
  Evidence: docs/guidelines.md:10-11 "The CLI has no tests today."

- Severity: Minor
  Where: Headline and Open question 5.
  What: The plan counts six spec changes but gives no recommendation on the choice it flags as "the blocking decision". Open question 1 also leaves the user to choose between replacing the state and adding a marker. The plan's own risk section says replacing the state hides `open` versus `assigned`.
  Evidence: plan.md:11 "The main trade-off is that `list` hides whether an overdue ticket is `open` or `assigned`".

Checked and correct: baseline (`make test` ran 7 tests, OK), HEAD `ddc05e2`, CLI-001 "four subcommands", CLI-006 and LOG-001 wording, LOG-002, LOG-009, TKT-013, the `cli.py:18` and `cli.py:29` and `cli.py:30` line cites, the `Clock` class at tests/test_tickets.py:8-14, the `tickets.py:35-36` cites, and architecture.md:7, 12, 44, 62-63, 94-96, 103.

What the plan leaves to the next reader without saying so:
- Whether to add the `overdue` command to `README.md`. Its content was not checked.
- Whether tickets with an unknown priority, such as one in a hand-written log, should be handled. The plan would raise a `KeyError` in `is_overdue`.
- Whether `list` should read through `Ticket.due_at` or the new table. The plan does both.
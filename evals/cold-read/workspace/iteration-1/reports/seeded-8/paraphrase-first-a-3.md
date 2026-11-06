PARAPHRASE

The plan adds "overdue" as a flag computed when tickets are read, not as a new state or event. A ticket is overdue if it isn't closed and the current time is past its due time. `ticketdesk list` would show `OVERDUE` in the state column for those tickets. A new `ticketdesk overdue` subcommand would print only those tickets, in the same line format, sorted by due time and then by ID. The work is gated on the user signing off on six spec changes. It then covers the service rule, CLI wiring, unit and subprocess tests, doc updates and three commits.

According to the document alone, the system is a four-command argparse CLI (create, assign, close, list) over a `TicketService` that replays an append-only log. Each ticket carries a creation time, a priority and a precomputed `due_at` (tickets.py:35-36). Specs have stable IDs, doc changes need user confirmation, and the existing tests use a fake `Clock`. The document says tests run under pytest, and that the subparsers are not marked required.

FINDINGS

- Severity: Blocker
  Where: Step 2 (`OVERDUE_HOURS`, `is_overdue`), and the CLI-006/TKT-014 table row
  What: The plan defines a second hours table with P3 = 48. The real due time is 72 hours (TKT-005), and every ticket already carries `due_at`. P3 tickets would show OVERDUE 24 hours early, and the rule contradicts TKT-005, which the plan itself cites.
  Evidence: plan.md:38 `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`. sla.py:3 `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`. tickets.md:44 `| P3 | 72 |`. Plan A1 says "Every replayed ticket already carries its due time."

- Severity: Blocker
  Where: Step 2, `is_overdue`, against TKT-014 and the test plan
  What: The code uses `now >= ...`. The spec text in the same plan says a ticket at the due time exactly is not overdue, and the boundary test expects the same.
  Evidence: plan.md:39 `now >= self.created_at + ...`. plan.md:30 "At the due time exactly, it is not overdue." plan.md:114 "not overdue ... at the due time exactly".

- Severity: Blocker
  Where: Step 2, `TicketService.overdue` sort key
  What: The sort key is `t.created_at`, not due time. Tickets of different priorities would come out in the wrong order, which fails "oldest due first". It also contradicts the plan's own test and TKT-015.
  Evidence: plan.md:40 `key=lambda t: (t.created_at, t.id)`. plan.md:31 "sorted by due time ascending". plan.md:118 "returns a P1 ticket created later before a P3 ticket created earlier". The key would return the P3 ticket first. The fix is `t.due_at`.

- Severity: Blocker
  Where: Step 1, row `cli.md` CLI-009 (new), and the Step 8 and Test plan citations of CLI-009
  What: CLI-009 already exists ("Ticket ID is an integer"), so the "next free number" is CLI-010. As written, the plan would duplicate a stable ID, and its tests and commits would cite the wrong spec.
  Evidence: cli.md:58 `### CLI-009: Ticket ID is an integer`. docs/README.md:27-28 "A new spec gets the next free number." plan.md:34 `CLI-009 (new)`.

- Severity: Major
  Where: Step 5, Step 7, "Project conventions" first bullet, and A8
  What: The plan uses pytest (`tmp_path`, `pytest -q`) and says the suite runs under pytest. The project uses `unittest`, CI and `make test` run `unittest discover`, and pytest isn't installed. It also breaks the no-dependencies rule. The plan's own step 4 test file is `unittest`-style.
  Evidence: AGENTS.md:22 "Tests | `unittest`, `make test`". Makefile: `python3 -m unittest discover -s tests -q`. `python3 -m pytest` → "No module named pytest". plan.md:90 "the suite runs under `pytest`". CI runs only `make lint` and `make test`, so `tests/test_cli.py` written with `tmp_path` would error under CI.

- Severity: Major
  Where: Step 3, last bullet
  What: The plan claims a missing subcommand reaches the `else:` branch because the subparsers aren't marked required. They are marked required, so that rationale is false. The plan's own A7 says no command exits 2.
  Evidence: cli.py:14 `add_subparsers(dest="cmd", required=True)`. plan.md:47 "the subparsers are not marked required". plan.md:75 "no command both exited 2".

- Severity: Major
  Where: Assumptions validated (A3–A8), and Steps 7 and 8
  What: The evidence for these rows is not reproducible. `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py` don't exist in the repo or in git (only `plan.md` is untracked). The E1–E5 results can't be checked.
  Evidence: `ls scratch` → "No such file or directory". `git status` → `?? plan.md` only. plan.md:71, 74.

- Severity: Major
  Where: Step 1 table, `cli.md` CLI-006 and the `list` change
  What: `list` is told to take the "current time" and be tested by subprocess. The plan passes `now` as a parameter, while the existing `Ticket` has no clock and `TicketService` has none. Also, CLI-006's line format and the `OVERDUE` label are specced, but INV/TKT-001 compatibility is asserted only for the stored state. Step 3 puts the "OVERDUE" label choice in the CLI by calling `t.is_overdue(now)` for every row. That is acceptable, but `list` and `overdue` both read `time.time()` in the CLI while INV-005 says time "comes from the store's clock, never from the caller". The plan doesn't address this. A reader could take it as an invariant conflict that needs surfacing, since AGENTS.md says to confirm any invariant break.
  Evidence: invariants.md:36-37 "The time comes from the store's clock, never from the caller." plan.md:9 "reads the current time once per command with `time.time()`".

- Severity: Minor
  Where: Step 6, "Baseline" and Test plan counts
  What: The plan says to update "the test count" at AGENTS.md:102. The doc quotes "7 unittest cases" and never records what the new count should be, and the plan doesn't say what number to use. Small, but unspecified.
  Evidence: AGENTS.md "make test  # 7 unittest cases".

- Severity: Minor
  Where: Open questions 2 and 1
  What: Question 2 admits that `overdue` lines all say `OVERDUE` and carry no extra information. The request doesn't say which format to use, so this is left to the next reader as an assumption. The plan also answers questions 3 and 4 inside TKT-014 and the code before the user has answered them.
  Evidence: plan.md:177, 178-179 against plan.md:30.

Decisions left unstated: how the CLI should get the clock, since INV-005 only covers the store; whether `OVERDUE` should hide the `open`/`assigned` distinction (question 1, flagged); and what happens when `overdue` meets an unknown priority, which is only noted as a CLI-007 inheritance.
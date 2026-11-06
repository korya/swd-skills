PARAPHRASE

The document proposes that "overdue" be a flag computed when tickets are read, not a new state or log event. `ticketdesk list` would print `OVERDUE` in the state column of past-due, unclosed tickets. A new `ticketdesk overdue` subcommand would print only those tickets, sorted by due time and then by ID. The work is: add the rule to `Ticket`/`TicketService`, wire the CLI, add unit tests and the first CLI subprocess tests, update the specs and docs after the user signs off, then commit in three pieces.

According to the document, the existing system works like this. Tickets are rebuilt by replaying an append-only log, and each replayed ticket carries a creation time, a priority and a due time (TKT-005). The CLI has four subcommands. The `list` branch is the final `else:`, and the line format is `#id [prio] state(8) title`. The service holds the rules and the store only appends and replays. Tests use a fake `Clock`, the suite runs under `pytest`, and the CLI has no tests.

FINDINGS

- Severity: Blocker
  Where: Plan step 2, `OVERDUE_HOURS`, `is_overdue`, and `overdue()` sort key
  What: The plan builds a second SLA table with `P3: 48`, but the real P3 SLA is 72 hours. It also ignores the existing `Ticket.due_at` field. As written, P3 tickets would show OVERDUE 24 hours early, and TKT-005 would be duplicated and wrong. The plan's own A1 says the due time is already carried.
  Evidence: `ticketdesk/sla.py:3` has `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`. `tickets.py:36` sets `t.due_at`. The plan at `plan.md:38` has `"P3": 48`. Its "Out of scope" section says the SLA table stays untouched, yet the plan adds a duplicate.

- Severity: Blocker
  Where: Plan step 2, `is_overdue` (`>=`) and `overdue()` sort key (`t.created_at`)
  What: The code contradicts the plan's own spec, tests and request. TKT-014 and the tests say a ticket at its due time exactly is not overdue, but the code uses `now >= ...`, which makes it overdue. The sort key is `created_at`, not the due time. That is wrong across priorities. A P3 created 80h ago and a P1 created 6h ago sort by creation as `[1,2]`, but the plan's own A4 says due-time order is `[2,1]`. The request asked for "oldest due first".
  Evidence: `plan.md:30` ("later than"), `plan.md:114`, `plan.md:39` (`>=`) and `plan.md:40` (`key=(t.created_at, t.id)`). The fix is to use `now > t.due_at` and `key=(t.due_at, t.id)`.

- Severity: Blocker
  Where: Step 1 table, new `CLI-009`
  What: `CLI-009` already exists, as "Ticket ID is an integer". The next free CLI ID is `CLI-010`. The plan claims to follow the "next free number" rule, then collides with an existing ID. The collision is repeated in the test plan, the commit plan and the CLI-006 line-format references.
  Evidence: `docs/product-specs/cli.md:58` has `### CLI-009: Ticket ID is an integer`. `docs/README.md:27-28`: "A new spec gets the next free number".

- Severity: Major
  Where: Steps 5, 7, "Project conventions", Test plan
  What: The plan assumes `pytest`, including the `tmp_path` fixture and `pytest -q`. The project uses `unittest` only, and `make test` runs `unittest discover`. pytest isn't installed here, and CI doesn't install it either. The plan also says the project has no dependencies beyond the standard library. The CLI tests would not run in CI, or would force a new dependency. They should use `unittest` plus `tempfile`. Step 7 should run `make test`.
  Evidence: `Makefile:3` has `python3 -m unittest discover -s tests -q`. `AGENTS.md:22` says `unittest`. `python3 -c "import pytest"` gives ModuleNotFoundError. `ci.yml` runs `make lint` and `make test`. The convention row at `plan.md:90` ("the suite runs under pytest") misquotes `AGENTS.md:22-23`.

- Severity: Major
  Where: Assumptions table A3-A8, "Baseline"
  What: The cited evidence cannot be checked. `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py` don't exist in the repo, and there is no `scratch/` directory. E1 to E5 and the 3.12.16 rerun are unsupported, so "confirmed" is unverified. The baseline (lint passes, 7 tests OK) does reproduce.
  Evidence: `ls scratch` gives "No such file or directory". `git status` shows only `plan.md` as untracked.

- Severity: Minor
  Where: Step 3, last bullet
  What: The claim "the subparsers are not marked required" is false. `required=True` is already set, so a missing subcommand exits 2 before the `else` branch. The `elif` change is still harmless, but the stated rationale is wrong. It is also needed, since the final `else` would otherwise catch `overdue`.
  Evidence: `cli.py:14` has `add_subparsers(dest="cmd", required=True)`.

- Severity: Minor
  Where: Step 3, `_line(t, now)` and `OVERDUE` padding
  What: The format string is `{label:<8}`, and `OVERDUE` is 7 characters. This is fine, but the plan's wording is loose. The CLI also still calls `time.time()` while the store takes an injectable clock. The plan doesn't say how the CLI tests get a "now" seam beyond hand-written past `at` values, which is acceptable. It never mentions that `list` would then call `is_overdue` in the CLI per ticket, even though the service could expose the flag. This is a design nit only.
  Evidence: `cli.py:30`, `plan.md:45`.

- Severity: Minor
  Where: Step 6
  What: The test count and line references in `AGENTS.md:102/114/116` and `architecture.md` weren't rechecked against the plan. The "7 unittest cases" figure in `AGENTS.md:102` will also need the new count, which the plan only mentions in passing. Low risk.
  Evidence: `AGENTS.md:102`.
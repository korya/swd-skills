PARAPHRASE

The plan makes "overdue" a value computed when a ticket is read. It is not a new state or a logged event. A ticket is overdue when it is not closed and the current time is past its due time. `ticketdesk list` would show `OVERDUE` in the state column for such tickets. A new `ticketdesk overdue` subcommand would list only those tickets, sorted by due time and then by ID. The work is gated on the user signing off six spec changes. After that come a service rule, CLI wiring, unit tests, a first CLI test suite, doc updates and three commits.

According to the document, the service replays an append-only log into tickets. Each ticket carries a creation time, a priority and a due time. The CLI has four subcommands and a `list` line format with the state padded to 8 characters. Specs have stable IDs such as TKT, CLI and LOG, and the tests are run under pytest. The CLI is untested, the CLI-007 TODO is open, and the existing `Clock` test helper advances on every call.

FINDINGS

- Severity: Blocker
  Where: Step 2 (`OVERDUE_HOURS`, `is_overdue`), TKT-014 row.
  What: The plan adds a second hours table with P3 = 48. The project's table says 72. The rule also recomputes the due time instead of using the existing `t.due_at`, so P3 tickets would show OVERDUE 24 hours early. The plan's own A1 says `due_at` is already on every ticket.
  Evidence: `ticketdesk/sla.py:3` has `{"P1": 4, "P2": 24, "P3": 72}`. TKT-005 (`docs/product-specs/tickets.md:44`) says P3 is 72. `ticketdesk/tickets.py:36` sets `t.due_at`.

- Severity: Blocker
  Where: Step 2, `TicketService.overdue` sort key.
  What: The sort key is `(t.created_at, t.id)`. The request and TKT-015 say oldest due first, so the key must be `due_at`. Creation order is not due order across priorities. The test "P1 created later before P3 created earlier" only passes under a due-time sort, so the code and the test contradict each other.
  Evidence: Plan line 40 against plan lines 31 and 118.

- Severity: Blocker
  Where: Step 2 code (`now >= created_at + ...`) against TKT-014, open question 3 and the boundary test.
  What: The code uses `>=`, which makes a ticket overdue at its due time exactly. TKT-014, question 3 and the test plan all say it is not overdue at that moment. The unit test would fail against the plan's own code.
  Evidence: Plan lines 30, 39, 114 and 178.

- Severity: Blocker
  Where: Assumption A4 (E3) and the test case at line 118.
  What: The worked example gives the wrong order. A P3 ticket created 80 hours ago is due 72 hours after creation, which was 8 hours ago. A P1 ticket created 6 hours ago is due 4 hours after creation, which was 2 hours ago. By due time that gives `[1, 2]`, the same as ID order, not `[2, 1]`. The example does not show that `overdue` needs its own sort, and "confirmed" is false.
  Evidence: Recomputed from `sla.py:3`. The plan says `[2, 1]` by due time.

- Severity: Blocker
  Where: Step 1, CLI-009 (new).
  What: CLI-009 already exists as "Ticket ID is an integer", so the plan would produce a duplicate ID. The next free CLI number is CLI-010. Steps 5 and 8 and the test plan also cite CLI-009.
  Evidence: `docs/product-specs/cli.md:58` (CLI-009). `docs/README.md:27-28` says IDs are never reused.

- Severity: Major
  Where: Steps 5 and 7, the Conventions section, and the "pytest" claims.
  What: The project runs `unittest` through `make test`, and pytest is not installed or declared. The plan's `tmp_path` fixture and `pytest -q` do not work here. The convention line "the suite runs under pytest" misquotes AGENTS.md. The CI-facing `make test` would not collect pytest-style tests either.
  Evidence: `AGENTS.md:22` says "Tests | `unittest`, `make test`". `Makefile:3` runs `python3 -m unittest discover`. `python3 -c "import pytest"` gives `ModuleNotFoundError`. AGENTS.md:25 says no dependencies.

- Severity: Major
  Where: Assumptions table (A3, A5, A6, A7, A8) and the "Verified" claims.
  What: The cited evidence cannot be checked. `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py` do not exist in the repo, and there is no `scratch/` directory. The runs on Python 3.12.16 and the results E1 to E5 are unsupported. E3 is demonstrably wrong (see above).
  Evidence: `ls scratch` gives "No such file or directory". `git status` shows only `plan.md` untracked.

- Severity: Minor
  Where: Step 3, last bullet.
  What: The claim that a missing subcommand falls into the `list` branch because subparsers are not required is false. They are required, so argparse exits 2 first. The `else:` to `elif` change is still harmless, but its stated reason is wrong.
  Evidence: `ticketdesk/cli.py:14` has `required=True`.

- Severity: Minor
  Where: Steps 1 and 8, commit grouping against step 0.
  What: Commit 1 mixes the spec edits with code, and step 6 puts the architecture and AGENTS.md updates in a third commit. The doc and spec changes need sign-off, and guidelines.md:85-86 asks for one logical change per commit. The grouping is workable but not clean. Separately, the spec-change count of "six" matches the table, but the AGENTS.md test-count update stays unspecified if tests are not run under the same runner.
  Evidence: `docs/guidelines.md:85-86`.

Baseline check: `make test` runs 7 tests and passes, as the plan says.
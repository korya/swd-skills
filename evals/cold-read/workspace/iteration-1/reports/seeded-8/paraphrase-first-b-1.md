PARAPHRASE

The plan adds "overdue" as a flag computed when tickets are read. It is not a new state or a stored event. A ticket counts as overdue if it isn't closed and the current time is later than its due time. `list` would show `OVERDUE` in place of the state column for those tickets. A new `overdue` subcommand would print only overdue tickets, sorted by due time and then by ID. The work goes in this order: get sign-off on six spec edits, add the rule to the service, wire the CLI, add unit tests and a new subprocess CLI suite, update docs, then commit in three pieces.

According to the plan, the service replays the event log into tickets. Each ticket carries a creation time, a priority and a due time. The CLI parses one command, calls the service and prints one line per ticket. The product specs fix the event kinds, the states and the `list` format. Docs may only change with user sign-off. Tests use a fake clock, and the CLI currently has no tests. I can't tell what `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py` contain, because the plan only quotes their results.

FINDINGS

- Severity: Blocker
  Where: Step 2, `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`
  What: The plan introduces a second SLA table, and its P3 value (48) is wrong. TKT-005 and `sla.py` say 72. The table also duplicates a rule the code already has. `Ticket.due_at` is already computed on replay, so the plan's own A1 makes the table redundant. P3 tickets would show OVERDUE 24 hours early.
  Evidence: `ticketdesk/sla.py:3` has `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`. `docs/product-specs/tickets.md` TKT-005 lists P3 as 72. `tickets.py:36` sets `t.due_at`.

- Severity: Blocker
  Where: Step 2, `is_overdue` uses `now >= created_at + …`
  What: The comparison contradicts the plan's own TKT-014 and its unit test. TKT-014 says that at the due time exactly a ticket is not overdue, so the check must be `now > due_at`. With `>=`, the boundary test in the test plan would fail.
  Evidence: plan.md:30 and plan.md:114 say "not overdue at the due time". plan.md:39 uses `>=`.

- Severity: Blocker
  Where: Step 2, `TicketService.overdue` sort key `(t.created_at, t.id)`; test plan line 118
  What: The request asks for "oldest due first", but the sort is by creation time. Creation order differs from due order when priorities differ. For example, a P3 created 75 hours ago is due 3 hours ago. A P1 created 10 hours ago is due 6 hours ago. The P1 should come first, but this key puts the P3 first. The test case "P1 created later before P3 created earlier" would fail against the plan's own code, because the code sorts the earlier-created ticket first. The plan should sort on `t.due_at`.
  Evidence: plan.md:40 against plan.md:31 and plan.md:118. TKT-015 as written in plan.md:31 says "sorted by due time".

- Severity: Blocker
  Where: Step 1, new spec `CLI-009`
  What: `CLI-009` already exists as "Ticket ID is an integer". The plan says "next free number", but the new spec would collide with an existing, stable ID. The next free number is CLI-010. Steps 1 and 8 and the tests all cite CLI-009.
  Evidence: `docs/product-specs/cli.md` has `### CLI-009: Ticket ID is an integer`. `docs/README.md:25-28` says IDs are never reused.

- Severity: Major
  Where: Assumptions A3 to A8, "Baseline"
  What: The evidence cited for the assumptions can't be checked. `scratch/` does not exist in the repo. The A3 example output, `'#1 [P1] OVERDUE  title'`, has two spaces after OVERDUE. The CLI-006 format pads the state to 8 characters and adds one more space. "OVERDUE" is 7 characters, so it gives 1 pad plus 1 separator, which is also two spaces. So the example is plausible but unverifiable. A4's numbers are also wrong. By due time a P3 created 80 hours ago (72-hour SLA) sorts before the P1 created 6 hours ago, giving `[1, 2]`, which matches ID order. A4 claims `[2, 1]`, so it doesn't show the sort differs from ID order.
  Evidence: `ls scratch` fails. A4 at plan.md:72, computed with the 72-hour P3 from `sla.py:3`.

- Severity: Major
  Where: Steps 4, 5 and 7, and the Conventions table row on pytest
  What: The project uses `unittest`, not pytest. The plan has `tests/test_cli.py` use the pytest `tmp_path` fixture and has step 7 run `pytest -q`. The plan's "Conventions" cites AGENTS.md:22-23 as saying the suite runs under pytest, but that line says `unittest`. pytest isn't installed here, and CI runs `make test` (unittest). The new suite would not run in CI, or would need a new dependency. This breaks the "no dependencies" rule.
  Evidence: `AGENTS.md:22` has "Tests | `unittest`". `Makefile:3` runs `python3 -m unittest discover`. `python3 -c "import pytest"` gives ModuleNotFoundError. `ci.yml` runs `make lint` and `make test`.

- Severity: Major
  Where: Step 3, last bullet
  What: The claim that the subparsers aren't marked required is false. They already use `required=True`. A missing subcommand exits 2 via argparse and never reaches the `else:` branch. Changing `else:` to `elif` is still harmless, but the stated reason is wrong. The plan then also never handles the case where nothing matches.
  Evidence: `cli.py:14` has `add_subparsers(dest="cmd", required=True)`.

- Severity: Minor
  Where: Step 1 and open question 5, "six spec changes"; also the decision to treat `OVERDUE` as hiding `open` and `assigned`
  What: The plan makes `list` hide `open` against `assigned` for overdue rows. It doesn't mention that this loses information scripts and agents might rely on. It lists this as only an open question, though the request ("show as OVERDUE") is a reasonable reading. Nothing wrong with this, but the "six spec changes" gate does depend on the `CLI-009` collision above being fixed first.
  Evidence: plan.md:176 and plan.md:11.

- Severity: Minor
  Where: Step 6 line references
  What: The plan cites `AGENTS.md:102`, `:114` and `:116`, and architecture lines 12, 94-96 and 103. The ones I checked match: 102, 116 and architecture.md:103. I didn't check the rest. The plan also tells the author to update the test count, but doesn't say what it becomes.
  Evidence: `AGENTS.md:102` and `:116`, `docs/architecture.md:103`.

I did not rerun the plan's end-to-end script, since it needs the unmodified feature. The existing suite passes with `make test` (7 tests).
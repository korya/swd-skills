PARAPHRASE
The plan makes "overdue" a flag computed when tickets are read, not a new state or event. A ticket counts as overdue when it isn't closed and the current time is past its due time. `ticketdesk list` would show `OVERDUE` in the state column for those tickets. A new `ticketdesk overdue` command would list only them, sorted by due time and then by ID. The plan puts the rule in `tickets.py`, has the CLI pick the label, adds unit tests and the first CLI test suite, and asks for sign-off on the spec and doc changes before any code work.

According to the plan, the system is a layered CLI (cli → TicketService → EventStore) over an append-only JSON-lines log. State is rebuilt by replay, and each ticket already carries a creation time, a priority and a due time. Specs have stable IDs (TKT, CLI, LOG, INV). Doc changes need user confirmation. The tests use a fake `Clock`, and there are 7 of them. There is no CLI test suite, and CLI-007 is an open TODO.

FINDINGS

- Severity: Blocker
  Where: Step 2, `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`
  What: The plan invents a second SLA table, and its P3 value is wrong. The real P3 target is 72 hours. With 48, P3 tickets would show OVERDUE 24 hours early. The second table also duplicates `SLA_HOURS` in `sla.py`, and the plan's own TKT-014 says to use the due time from TKT-005.
  Evidence: `ticketdesk/sla.py:3` has `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`. `docs/product-specs/tickets.md` TKT-005 says P3 is 72. `Ticket.due_at` already exists (`tickets.py:21`, set at `tickets.py:36`), and the plan's A1 confirms it. The rule should be `now > self.due_at`.

- Severity: Blocker
  Where: Step 2, `TicketService.overdue` sort key `(t.created_at, t.id)`
  What: The sort key is creation time, not due time. TKT-015 and the request say "oldest due first". Because the P1, P2 and P3 windows differ, creation order and due order diverge. The test plan's "P1 created later before P3 created earlier" case would fail against this key.
  Evidence: The key at plan.md:40 uses `t.created_at`, while TKT-015 (plan.md:31) says due time. The key should be `(t.due_at, t.id)`.

- Severity: Blocker
  Where: Step 2 `is_overdue`, `>=`
  What: The code uses `now >= created_at + …`, but TKT-014, open question 3 and the unit tests say a ticket is not overdue at the exact due time. The implementation contradicts the plan's own spec, and the boundary test would fail.
  Evidence: plan.md:39 (`now >=`) against plan.md:30 ("At the due time exactly, it is not overdue") and plan.md:114.

- Severity: Major
  Where: Step 1 table, `cli.md` CLI-009 (new)
  What: CLI-009 already exists as "Ticket ID is an integer". The plan treats it as free, so it would reuse the ID and break "IDs are stable". The next free CLI number is CLI-010. The "Reflected in plan" line and steps 5 and 8 repeat the wrong ID.
  Evidence: `docs/product-specs/cli.md` has `### CLI-009: Ticket ID is an integer`. The existing "next free number" rule is at `docs/README.md:27-28`.

- Severity: Major
  Where: Plan steps 5 and 7, and the conventions list ("suite runs under `pytest`")
  What: The project uses `unittest`, not pytest. `make test` runs `python3 -m unittest discover`, so a `tmp_path`-based `tests/test_cli.py` would not run under `make test` or CI. CI never runs `pytest -q`. The plan's convention citation misquotes AGENTS.md. The assumptions section also cites a "baseline" of `make test`, which is unittest, so the plan contradicts itself.
  Evidence: `Makefile:3` runs `python3 -m unittest discover -s tests -q`. `ci.yml` runs `make lint` and `make test`. AGENTS.md's tech stack says "Tests | `unittest`". No pytest reference exists in the repo. Tests should use `tempfile.TemporaryDirectory` like `tests/test_tickets.py:19`.

- Severity: Major
  Where: A3–A8 evidence, `scratch/exp1_crafted_log.py`, `scratch/exp2_clock_and_argparse.py`
  What: The cited experiment scripts don't exist, so the "confirmed" results can't be checked. The Python 3.12.16 rerun is also unverifiable.
  Evidence: `ls scratch` returns "No such file or directory". `git status` shows only `plan.md` untracked.

- Severity: Major
  Where: A4 (E3 example) and the P1-before-P3 test
  What: The numbers don't show what the plan claims. With the real 72 h P3 target, a P3 created 80 h ago is due 8 h ago, and a P1 created 6 h ago is due 2 h ago. Due-time order is therefore `[1, 2]`, the same as ID order, not `[2, 1]`. Using 48 h gives the same `[1, 2]`. The need for a separate sort is not demonstrated, and the test built on it would not distinguish the two orders. A working example is P1 (ID 1) created 5 h ago, due 1 h ago, with P3 (ID 2) created 75 h ago, due 3 h ago. That gives `[2, 1]` by due time.
  Evidence: `sla.py:3`, plus recomputing the plan's own numbers.

- Severity: Minor
  Where: Step 3, last bullet
  What: The claim that "a missing subcommand also reaches that branch, because the subparsers are not marked required" is false today. `required=True` is already set, and a missing command exits 2 in argparse. The `else` → `elif` change is still reasonable as defensive code, but the stated reason is wrong.
  Evidence: `cli.py:14` has `add_subparsers(dest="cmd", required=True)`.

- Severity: Minor
  Where: Step 1, CLI-006 and `_line` in step 3
  What: The `_line` helper changes the `list` line shape for non-overdue rows too. CLI-006 pads the state to 8 characters. `OVERDUE` is 7, so it fits, but `assigned` is 8 and the plan never states this. Open question 2 (every `overdue` line says OVERDUE) and the risk that scripts grep for `open` or `assigned` are both noted. What is not noted is that `overdue` shows `OVERDUE` in the state column, so it loses the open/assigned distinction entirely.
  Evidence: `cli.py:30` and CLI-006.

- Severity: Minor
  Where: Step 5, `make lint` and compileall, test counts
  What: The plan updates AGENTS.md ("7 unittest cases") and `architecture.md` lines by number but never says what the new count is. Step 6's line references (AGENTS.md:102/114/116, architecture.md:94-96/103) were not shown to match. I only partly checked them: architecture.md does say "The CLI is not covered by tests today", and the layout is nearby.
  Evidence: `docs/architecture.md`, tree section, and AGENTS.md's "Running the project".

- Severity: Minor
  Where: Step 1, LOG-001 edit
  What: The plan rewrites LOG-001 to say overdue listing appends nothing. That is only needed if `overdue` is a "listing". Since TKT-015 already calls it "Listing overdue tickets", this is consistent. The six-change count is fine. However, `invariants.md` and CLI-001 ("four subcommands") are touched, and INV-002 is cited only in tests. This is mild, and no further action is needed beyond confirming that CLI-001's edit and the architecture arrow edit are consistent.
  Evidence: `docs/product-specs/event-log.md:14-15`, `cli.md` CLI-001.

I did not run `make test`. I read the code and the specs.
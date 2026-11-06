FINDINGS

- Severity: Blocker
  Where: Step 2, `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`
  What: The plan adds a second SLA table, and its P3 value is wrong. The spec and code say P3 is 72 hours, not 48. A P3 ticket would show OVERDUE 24 hours early. The table also duplicates `sla.py`, which exists to keep this table in one place. `Ticket.due_at` is already computed on replay, so `is_overdue` can use `now > self.due_at` and needs no table.
  Evidence: `ticketdesk/sla.py:3` has `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`. TKT-005 in `docs/product-specs/tickets.md:44` says P3 is 72. `docs/architecture.md` says `sla.py` keeps the table "in one place". `tickets.py:36` sets `t.due_at`. The plan's own A1 says every ticket already carries its due time.

- Severity: Blocker
  Where: Step 2, `is_overdue` uses `now >= ...`
  What: The code contradicts the plan's own rule. TKT-014 (new), the "Test plan" and open question 3 all say a ticket is not overdue at the due time exactly. `>=` makes it overdue at that instant. The planned boundary test would fail against the planned code.
  Evidence: Plan line 30, "At the due time exactly, it is not overdue". Plan line 114, "not overdue ... at the due time exactly". Plan line 39, `now >= self.created_at + ...`.

- Severity: Blocker
  Where: Step 2, `overdue()` sort key `(t.created_at, t.id)`
  What: The request asks for oldest due first, but this sorts by creation time. A P1 created at t=0 is due at 4 h. A P3 created at t=−10 h is due at 62 h. Sorting by creation puts the P3 first, which is the wrong order. The key should be `t.due_at`. This contradicts the plan's own TKT-015 text, which says "sorted by due time", and the test plan.
  Evidence: Plan line 40 against plan lines 31 and 119. `tickets.py:21` has the `due_at` field.

- Severity: Major
  Where: A4, and the test "P1 ticket created later before P3 ticket created earlier"
  What: The worked example is wrong. P3 created 80 h ago (ID 1) is due at −8 h with the 72 h SLA, or −32 h with the plan's 48. P1 created 6 h ago (ID 2) is due at −2 h. Due order is [1, 2], which equals ID order. The example does not show that `overdue` needs its own sort, and the planned test would fail or pass for the wrong reason. A valid example needs a later-created ticket with an earlier due time. For instance, a P3 created 100 h ago and a P1 created 5 h ago are due at −28 h and −1 h, which is still [1, 2]. One that works is a P3 created 10 h ago, due in 62 h, and a P1 created 20 h ago, due at −16 h. That puts the later ID first.
  Evidence: Plan line 72. SLA from `sla.py:3`.

- Severity: Major
  Where: Step 1, `CLI-009 (new)`
  What: CLI-009 already exists ("Ticket ID is an integer"). The plan's own convention says IDs are never reused and a new spec takes the next free number, which is CLI-010. The plan's tests also cite CLI-009 for the overdue behavior, so the references are ambiguous.
  Evidence: `docs/product-specs/cli.md:58`, `### CLI-009: Ticket ID is an integer`. `docs/README.md:27-28`. Plan lines 34, 98, 128 and 129.

- Severity: Major
  Where: Plan steps 5 and 7, "Project conventions" bullet 1, Counterfactual
  What: The plan assumes pytest, but the project uses `unittest` and has no dependencies. `make test` runs `python3 -m unittest discover`. `pytest` is not installed here (`ModuleNotFoundError`). The `tmp_path` fixture is pytest-only, and step 7 runs `pytest -q`. CI runs only `make lint` and `make test`. As written, the new CLI suite would not run in CI. The conventions bullet states the opposite of what AGENTS.md says.
  Evidence: `Makefile:3`. AGENTS.md:22 (`Tests | unittest, make test`). `docs/architecture.md:80`. `ci.yml:11-12`. The plan's claim at line 90, "the suite runs under `pytest`".

- Severity: Major
  Where: Assumptions table A3 to A8, and "Assumptions validated"
  What: The evidence cites `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py`. Neither exists in the repo, and there is no `scratch/` directory. The reviewer cannot reproduce E1 to E5. The 3.12.16 rerun claim in A8 is also unverifiable. A4's result is already shown wrong above, so these "confirmed" labels cannot be trusted.
  Evidence: `ls scratch` returns "No such file or directory". `git status` shows only `plan.md` untracked.

- Severity: Minor
  Where: Step 3, last bullet
  What: The stated rationale is false. The subparsers are already `required=True`, so a missing subcommand exits 2 in argparse and never reaches the `else:` branch. Changing `else:` to `elif args.cmd == "list":` is still harmless, but the justification is wrong.
  Evidence: `cli.py:14`, `required=True`. CLI-001 says no subcommand exits 2.

- Severity: Minor
  Where: Step 6, and the AGENTS.md references
  What: Step 6 removes the line "Not covered by tests: the CLI" and the matching statement in architecture.md, which is right only if `tests/test_cli.py` actually runs under `make test`. See the pytest finding. The 7-test count in AGENTS.md:102 also changes only if the new suites are unittest.
  Evidence: `AGENTS.md:102,114,116`. `docs/architecture.md:103`.

- Severity: Minor
  Where: Step 8, commit split
  What: The first commit is described as "the specs and the service rule", which would include the CLI spec edits (CLI-001, CLI-006, CLI-009). The second commit then cites those same CLI IDs. The split is inconsistent with step 1, which updates all specs in one pass.
  Evidence: Plan lines 26 to 35 and 60 to 63.

- Severity: Minor
  Where: Step 3, `time.time()` in the CLI
  What: The CLI reads the wall clock directly. The project routes time through an injectable clock owned by the store (INV-005, architecture.md:50). Reading it in the CLI is defensible for "now", but the plan does not acknowledge the deviation or say why the service or store does not own it. This is also why CLI tests need hand-written logs.
  Evidence: `docs/product-specs/invariants.md:34-37`. `docs/architecture.md:50`.

- Severity: Minor
  Where: Open question 2, and the CLI-009 `overdue` format
  What: Every line of `overdue` output would read `OVERDUE`, which adds nothing. This is flagged in the plan, but the recommended default is the least useful option. Keeping the real state, or showing lateness, may serve the request better.
  Evidence: Plan lines 177 and 34.

PARAPHRASE

The plan proposes treating "overdue" as a flag computed at read time from the ticket's creation time and priority, not as a new state or log event. `ticketdesk list` would show `OVERDUE` in the state column for open or assigned tickets past their due time. A new `ticketdesk overdue` subcommand would print only those tickets, in the same line format, sorted by creation time and then by ID. The work is gated on user sign-off for six spec changes and followed by service and CLI tests, doc updates and three commits.

According to the document alone, the system is an append-only event log replayed on every command. The service derives tickets, the CLI only formats them, and `sla.py` holds the hours per priority. The document says every ticket already carries its due time, the CLI has no tests, and the suite runs under pytest. It also says the CLI would fall through to `list` on a missing subcommand, and that the P3 target is 48 hours. The code contradicts those last three claims: the suite uses `unittest`, the subparsers are already required, and P3 is 72 hours.
FINDINGS

- Severity: Blocker
  Where: Step 1 table (CLI-009 new), step 8, Test plan, and the Approach.
  What: The spec ID `CLI-009` is already taken. It is "Ticket ID is an integer". The plan calls it "new" and says it takes "the next free number". The next free CLI number is CLI-010. Its own docs/README.md:27-28 rule says to use the next free number and never renumber. The plan also never says to re-cite CLI-009 as the overdue spec in tests and commits, so traceability would be wrong.
  Evidence: docs/product-specs/cli.md:58-61 reads `### CLI-009: Ticket ID is an integer`. Plan line 34 reads "`cli.md` CLI-009 (new)".

- Severity: Blocker
  Where: Step 2, `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`, and `Ticket.is_overdue`.
  What: There are three problems.
  1. The duplicate hours table has P3 at 48. The real SLA is 72, so P3 tickets would show OVERDUE 24 hours early.
  2. It contradicts TKT-005 and the plan's own claim that the rule uses "its due time (TKT-005)".
  3. `Ticket` already carries `due_at`, set at tickets.py:36. The plan should compare `now > self.due_at` and add no second table. A duplicate table is the kind of drift the project avoids by keeping the hours in sla.py.
  Evidence: sla.py:3 has `"P3": 72`. tickets.md:44 says P3 is 72. Plan line 38 says 48. tickets.py:21 and 36 hold `due_at`.

- Severity: Blocker
  Where: Step 2 `is_overdue` versus TKT-014 and the Test plan.
  What: The code uses `now >= created_at + hours*3600`. The spec text, open question 3, and the boundary test all say a ticket is not overdue at the exact due time. Under `>=` it is overdue at exactly that time. The unit test "not overdue at the due time exactly" would fail against the plan's own code. It should be `>`.
  Evidence: Plan line 39 `now >= ...`. Plan line 30 "At the due time exactly, it is not overdue". Plan line 114.

- Severity: Major
  Where: Steps 5 and 7, "Project conventions" (first bullet), and A1-A8.
  What: The plan says the suite runs under `pytest`. It adds a `tests/test_cli.py` that uses the pytest `tmp_path` fixture. It runs `make lint && pytest -q`. The project uses `unittest` only, run through `make test` (`unittest discover`). There is no pytest dependency. The tech stack says "None" for dependencies. Adding it breaks that rule, and CI runs only `make test`, so `tmp_path` tests would error. The plan misquotes AGENTS.md:22-23, which says `unittest`. The plan should use `tempfile` and `unittest`, like the existing tests, and run `make lint && make test`.
  Evidence: AGENTS.md tech stack row "Tests | `unittest`, `make test`". Makefile:3. ci.yml:12. A grep for "pytest" outside plan.md finds nothing. Plan lines 51, 58 and 90.

- Severity: Major
  Where: Assumptions table (A3, A4, A5, A6, A8) and the "scratch/..." citations.
  What: The plan cites `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py` as evidence, with experiments E1-E5 and a Python 3.12.16 rerun. No `scratch/` directory exists in the repo or in git. These results cannot be checked. A3 and A4 are labelled "Plausible" yet marked "confirmed". The baseline claim of 7 passing tests on 265e7de does hold when I run it.
  Evidence: `ls scratch` gives "No such file or directory". `git ls-files` lists no scratch files.

- Severity: Major
  Where: Step 3, the `elif args.cmd == "list":` change, and the claim about missing subcommands.
  What: The plan says "Today a missing subcommand also reaches that branch, because the subparsers are not marked required." That is false. `required=True` is set, so a missing command exits 2. The reasoning for the change is wrong. The change is still harmless, but it is a drive-by edit. A7 is also stated as if the behavior might change.
  Evidence: cli.py:14 `add_subparsers(dest="cmd", required=True)`.

- Severity: Major
  Where: Step 1, the LOG-001 change and "six spec changes".
  What: The plan rewrites LOG-001 to "Listing tickets, overdue tickets included, appends nothing." This is vague, and it edits an invariant-adjacent spec when nothing is needed. The count says six changes, but the table has six rows and counts the CLI-001 edit. CLI-001's usage line, "four subcommands", is edited correctly. The plan also changes CLI-006 to show `OVERDUE` in the state column. That stops being "the state" and breaks the `#<id> [<priority>] <state> <title>` contract. It is flagged as a risk, but the plan does not say which line it passes as the format. It also leaves unmentioned that CLI-006 says "with the state padded to 8 characters", and `OVERDUE` is 7 characters. It fits, so this is minor.
  Evidence: event-log.md:14-15. cli.md:41-43.

- Severity: Major
  Where: Step 3 and "Approach" (`time.time()` in the CLI).
  What: The CLI reads the clock itself with `time.time()`. The project injects a clock into the store (`EventStore(path, clock=...)`), and the service holds the rules. The plan adds a second, un-injectable time source, which is why the CLI test needs hand-written past `at` logs. A better fit is for the service to take a clock, or for `svc.list()` and `svc.overdue()` to take `now`. The plan chose this but did not weigh the alternative of making the store's clock reachable. The service is called as `svc.overdue(now)`, so the unit tests do work. The cost is real but limited.
  Evidence: tests/test_tickets.py:8-21 and store.py:20 `self.clock()`.

- Severity: Minor
  Where: Step 3 ordering and Headline.
  What: The plan sorts `overdue` by `created_at` then ID in step 2. That equals due-time order only if all priorities share one SLA. It does not. The step 2 code `key=lambda t: (t.created_at, t.id)` contradicts TKT-015 ("sorted by due time"), and it contradicts test A4/E3, where a P1 ticket created later must come before a P3 ticket created earlier. With `created_at` as the key, the P3 ticket (ID 1) would sort first, so the E3 test would fail. It must be `(t.due_at, t.id)`. This is arguably a Blocker, because it makes the "oldest due first" request wrong.
  Evidence: Plan line 40 versus plan lines 31, 72 and 118.

- Severity: Minor
  Where: Step 6 and Step 8.
  What: Line numbers cited in AGENTS.md (102, 114, 116) are approximate. The step 6 text says "update the test count". It does not state a number. The e2e script has the `Old P3` ticket expecting `#2 [P3] OVERDUE  Old P3`. It also expects `list` to show `#1 open`, which is padded to 8 characters, `#1 [P1] open     Fresh P1`. The e2e example `close 2 "Replaced the toner cartridge"` is fine (over 10 characters).
  Evidence: AGENTS.md "make test # 7 unittest cases".

- Severity: Minor
  Where: Step 8, the three-commit split.
  What: Commit 1 bundles the spec edits with service code, and commit 2 holds CLI-001/CLI-006 spec edits with the CLI code. But step 1 says the specs are written as one step after sign-off. The spec changes for CLI sit in the commit that implements them, so the split does not match the steps. guidelines.md asks for "one logical change per commit", which this roughly meets. There is also no instruction to add a `Co-Authored-By` line, but that comes from the harness, not the plan.
  Evidence: Plan lines 60-63.

- Severity: Minor
  Where: Open questions 1 and 2, and the Counterfactual verdict.
  What: Question 2 shows that on the `overdue` command every line says `OVERDUE`, so the output carries no extra information. The plan still assumes it and calls the verdict "Confirmed with gaps". The user asked for `overdue` to list tickets oldest due first. With no due time and no state shown, the order cannot be verified from the output. This is the plan's own admitted weakness, so the author should raise it as a recommendation rather than an assumption.
  Evidence: Plan lines 176-177.
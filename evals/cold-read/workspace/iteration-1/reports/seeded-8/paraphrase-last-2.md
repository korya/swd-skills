FINDINGS

- Severity: Blocker
  Where: Plan step 2 (`OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`) and `is_overdue`.
  What: The plan adds a second hours table with P3 = 48. TKT-005 and `sla.py` say P3 = 72. The rule also recomputes the due time as `created_at + hours*3600` and ignores `Ticket.due_at`. Every P3 ticket would show OVERDUE 24 hours early, and a future SLA change would need edits in two places.
  Evidence: `ticketdesk/sla.py:3` has `{"P1": 4, "P2": 24, "P3": 72}`, and `docs/product-specs/tickets.md:44` has "`P3` | 72". `tickets.py:36` already sets `t.due_at`. The plan's A1 says every ticket "already carries its due time", then does not use it. `architecture.md:54-56` says the SLA table is the one place for hours. The plan's own "Duplicate logic" sweep claims the hours table sits "next to the rule", which contradicts this.

- Severity: Blocker
  Where: Plan step 2, `TicketService.overdue`, the `key=(t.created_at, t.id)` sort.
  What: The request and TKT-015 say oldest due first, sorted by due time. The code sorts by creation time. The test plan's P1-before-P3 case (E3) fails under this sort, because the P3 ticket was created earlier and so sorts first.
  Evidence: Plan line 31 says "sorted by due time ascending". Plan lines 72 and 118 say the P1 ticket created 6 h ago comes before the P3 ticket created 80 h ago. Plan line 40 uses `t.created_at`. The key should be `(t.due_at, t.id)`.

- Severity: Blocker
  Where: Plan step 2 `is_overdue` (`now >= ...`) against TKT-014 (step 1 table), the test plan, and open question 3.
  What: The code uses `>=`, so a ticket at its due time exactly is overdue. The proposed spec, the boundary test, and the stated assumption all say it is not overdue at the exact due time. The "request" says "pass their due time", which also means strictly later.
  Evidence: Plan line 39 has `now >= ...`. Plan lines 30, 114, and 178 say "later than" and "not overdue ... at the due time exactly". The code should be `now > t.due_at`.

- Severity: Blocker
  Where: Plan steps 1, 5, 7, 8, and the Conventions section. It calls the suite `pytest` and uses `tmp_path`.
  What: The project uses `unittest`, and pytest is not installed or declared. `pytest -q` in step 7 fails. `tests/test_cli.py` with `tmp_path` would not run under `make test`, so CI would not run it either. This breaks the "no dependencies" rule.
  Evidence: `Makefile:3` runs `python3 -m unittest discover`. `AGENTS.md:22` and `architecture.md:80` say `unittest`. `AGENTS.md:25` says no dependencies. `python3 -c "import pytest"` gives `ModuleNotFoundError`. The plan's convention line 90 says "the suite runs under `pytest`" and cites AGENTS.md:22-23. Those lines say the opposite.

- Severity: Major
  Where: Step 1 table, "`cli.md` CLI-009 (new)", and step 8.
  What: CLI-009 already exists ("Ticket ID is an integer"). The next free number is CLI-010. Reusing 009 breaks the stable-ID rule, and the test cases and commit messages that cite CLI-009 would point at the wrong spec.
  Evidence: `docs/product-specs/cli.md:58`. `docs/README.md:27-28` says IDs are never renumbered and a new spec takes the next free number. The plan's own convention line 98 claims to follow this rule.

- Severity: Major
  Where: Plan step 3, `now = time.time()` in the CLI.
  What: This breaks the project's clock design. Timestamps come from the store's injectable clock "never from the caller". The CLI reading the wall clock directly creates a second time source. It also forces the CLI tests to forge past `at` values by hand, which the plan admits is the "only seam". The service already holds the store with its `clock`, so `overdue()` could read the time from there. The plan never weighs this against the existing pattern.
  Evidence: `architecture.md:49-50` and `architecture.md:68-69`. `INV-005` at `invariants.md:34-37`. `store.py:15-16` has `clock=time.time`.

- Severity: Major
  Where: Step 3, the `_line` helper; the A3 evidence; the "Counterfactual" table.
  What: The plan puts the `OVERDUE` label choice in the CLI, but the "overdue" decision comes from the service, so the CLI formats it per row. That is acceptable. The real problem is that `list` has no `now`: `svc.list()` stays unchanged, so the CLI works out "overdue" per row. It also makes `overdue` output the same format as `list`, so every line says `OVERDUE`. The plan flags this as open question 2 but still writes it into CLI-009 as settled.
  Evidence: Plan lines 34, 45, 177.

- Severity: Major
  Where: "Assumptions validated" A3–A8, "Baseline", and the cited scratch files.
  What: The evidence cites `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py`. Neither exists in the repo, so a reader cannot rerun them. A8 claims a run on "Python 3.12.16", which I cannot confirm. The A1 to A7 results, including the A4 ordering claim, can't be checked, and the sort bug above suggests the experiments did not exercise the code as written.
  Evidence: `ls scratch` gives "No such file or directory". `git status` shows only `plan.md` as untracked.

- Severity: Minor
  Where: Step 3, "Today a missing subcommand also reaches that branch, because the subparsers are not marked required."
  What: This is false. The subparsers are `required=True`, so a missing command exits 2 in argparse. The `else:` to `elif` change is still reasonable, but the stated reason is wrong.
  Evidence: `cli.py:14`: `sub = parser.add_subparsers(dest="cmd", required=True)`.

- Severity: Minor
  Where: Step 6 line refs `architecture.md:94-96` and `:103`; step 6 `AGENTS.md` refs; the Conventions block `AGENTS.md:25`, `architecture.md:76`; "Callers" sweep (`cli.py:29`).
  What: The line numbers mostly match, but the architecture ref `architecture.md:12` is the arrow label, which is right. Step 6 omits `guidelines.md:10-11` ("The CLI has no tests today", a TODO), which would also go stale. Step 6 also omits the `cli.py` box description in `architecture.md`. Smaller: step 6 lists "7 unittest cases" at AGENTS.md:102 as the count to update, but it does not say what the new count is.
  Evidence: `docs/guidelines.md:10-11`.

- Severity: Minor
  Where: Step 1 and open question 5. Both say "six spec changes".
  What: The table has six rows, which matches. But two of them (TKT-014 and TKT-015) and the CLI-006 edit change a user-visible contract (the `list` format). Question 6 is left at "no known consumer exists". The headline calls the spec sign-off blocking, yet the plan does not also ask about the CLI-007 TODO as a conflict, only as out of scope. That is acceptable, but the plan should say that the new `overdue` command inherits the traceback behaviour and so adds one more path that violates CLI-007.
  Evidence: `cli.md:50-52`.

- Severity: Minor
  Where: Step 5 and the e2e script.
  What: The e2e script appends an event with `id` 2 and `at` 100 hours ago after an event at "now", so the log is no longer time-ordered. The script is also fragile: it hand-writes a log line, which `LOG-004` and `INV-005` say should come only from the store. This is fine as a test device, but the plan should say so.
  Evidence: `event-log.md:33-34`.

PARAPHRASE

The plan proposes that overdue is a flag derived at read time rather than a new state or event. A ticket is overdue if it is not closed and the current time is strictly after its due time. `ticketdesk list` would replace the state column with `OVERDUE` for those tickets. A new `ticketdesk overdue` subcommand would print only those tickets in the same line format, sorted by due time and then by ID. Specs are updated first, after the user signs off. The work is a service rule, a CLI change, and a new CLI test suite.

According to the plan alone, the system is a three-layer CLI. The CLI parses a command and prints lines. The service replays an append-only log to derive tickets, and the store only appends and replays events. Each ticket already carries a creation time, a priority, and a due time. Tests inject a fake clock and run under pytest, and the CLI has no tests. Part of the plan I could not follow: it says the rule lives in the service and the CLI only picks the label, yet the code in step 2 uses a hand-copied hours table with different numbers than the SLA table the plan itself cites in A1. I can't tell which due time it intends.
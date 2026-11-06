PARAPHRASE

The plan adds overdue as a flag computed when tickets are read. It is not a new state or event, and the log, store and SLA table stay as they are. The service gets an `is_overdue(now)` rule and an `overdue(now)` query. The CLI reads `time.time()` once per command. `list` shows `OVERDUE` in the state column for overdue rows, and a new `ticketdesk overdue` prints only those rows, ordered by due time and then by ID. Work is gated on the user signing off six spec changes. Then come the code, unit tests, the first CLI tests, doc updates, and three commits.

According to the plan alone, the system is a CLI layer over a service over an append-only event store. The service replays the log into tickets that carry creation time, priority and due time. The CLI has four subcommands, and `list` prints `#id [prio] state title` in ID order. Tests run under pytest, the CLI has no tests, and every doc change needs user confirmation.

FINDINGS

- Severity: Blocker
  Where: Step 2, `OVERDUE_HOURS` and `is_overdue`
  What: The plan creates a second SLA table with P3 set to 48, but the spec and `sla.py` say 72. The rule also uses `>=`, while TKT-014 in the plan and the test plan say "later than", so the due time exactly is not overdue. A P3 ticket would go overdue 24h early, and every ticket would go overdue at the boundary.
  Evidence: Plan line 38 `{"P1": 4, "P2": 24, "P3": 48}` and line 39 `now >= self.created_at + ...`. `sla.py:3` has `"P3": 72`. `tickets.md:44` has P3 at 72. Plan line 30 says "At the due time exactly, it is not overdue." The plan's own claims "SLA table stay untouched" and "Step 2 keeps the hours table next to the rule" conflict with TKT-005, which says to use `t.due_at`, already set at `tickets.py:36`.

- Severity: Blocker
  Where: Step 2, `TicketService.overdue` sort key
  What: The sort key is `(t.created_at, t.id)`, which is creation order, not due order. The request and TKT-015 say oldest due first. The A4/E3 example and the P1-before-P3 test cannot pass with this key.
  Evidence: Plan line 40 `key=lambda t: (t.created_at, t.id)`. Plan line 31 says "sorted by due time ascending". Plan line 118 expects the P1 ticket created later to come first. A4 (line 72) says `[2, 1]` by due time. With the real SLA, the P3 ticket created 80h ago is due 72−80 = 8h ago and the P1 ticket created 6h ago is due 2h ago, so due order is `[1, 2]`. A4's example doesn't show what it claims.

- Severity: Blocker
  Where: Step 1, the new `CLI-009`
  What: CLI-009 already exists as "Ticket ID is an integer", so the plan's "next free number" claim is false. It would create a duplicate ID, and the plan cites CLI-009 in tests and commits. The next free number is CLI-010.
  Evidence: `cli.md:58` has `### CLI-009: Ticket ID is an integer`. Plan line 34 `cli.md CLI-009 (new)`. Plan line 98 cites `docs/README.md:27-28` as the next-free-number rule.

- Severity: Major
  Where: Step 5, step 7, and the conventions list (line 90)
  What: The plan assumes pytest, but the project uses `unittest` and `make test` runs `unittest discover`. pytest isn't installed or declared, so adding a dependency conflicts with the no-dependencies rule. A `tmp_path` test would fail under `make test`, which CI runs.
  Evidence: Plan line 51 "pytest `tmp_path` fixture" and line 58 "`pytest -q`". Line 90 says "the suite runs under `pytest`" and cites AGENTS.md:22-23, which says "Tests | `unittest`, `make test`". `Makefile:3` is `python3 -m unittest discover`. `python3 -m pytest` returns "No module named pytest".

- Severity: Major
  Where: Step 3, last bullet
  What: The reason given for changing `else:` is false. The subparsers are already `required=True`, so a missing subcommand exits 2 and never reaches that branch.
  Evidence: Plan line 47 "the subparsers are not marked required". `cli.py:14` has `required=True`. Running `python3 -m ticketdesk.cli` printed "error: the following arguments are required: cmd". The `elif` change is still harmless, but its stated justification is invented.

- Severity: Major
  Where: Assumptions validated, A3 to A8, and the "scratch" references
  What: The cited experiments can't be reproduced. The `scratch/` scripts exist neither in the working tree nor in git, so every "confirmed" result that rests on E1 to E5 is unverifiable. At least E3/A4 is contradicted by the evidence above, and A4 is marked "confirmed".
  Evidence: Plan lines 71, 74 cite `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py`. `ls scratch` returns "No such file". `git status` shows only `plan.md` and `__pycache__` untracked.

- Severity: Minor
  Where: Step 3, `now = time.time()` in the CLI
  What: The plan doesn't address INV-005 or the architecture rule that time comes from the store's clock, never the caller. The plan neither reuses `store.clock` nor says why a CLI-side clock is acceptable. The reader has to decide this.
  Evidence: `invariants.md:36-37` "The time comes from the store's clock, never from the caller". `architecture.md:68-69` "Timestamps and due times are floats from the store's clock, never from the caller".

- Severity: Minor
  Where: Scope, steps 3, 5 and 6
  What: The request asked for neither the CLI test suite, nor the `else`→`elif` change, nor the architecture and AGENTS.md rewrites. They enlarge the change and the sign-off. They also bundle a refactor with a feature, which `guidelines.md:86` says to commit separately.
  Evidence: The request names only the `OVERDUE` display and the `overdue` subcommand. `guidelines.md:86` "Do not bundle a feature with unrelated cleanup."

- Severity: Minor
  Where: Open questions 1 to 4 and 6
  What: The plan makes the decisions itself and records them as assumptions. They are `OVERDUE` replacing the state, the line format, closed tickets never overdue, and the boundary. It does flag them as questions, but step 1's spec text already hard-codes them. Q3 is also resolved the opposite way in the code (`>=`).
  Evidence: Plan lines 176 to 179 against line 39.

Verified correct: the `make test` baseline of 7 tests passes, and the cited line numbers for `cli.py`, `tickets.py`, `sla.py`, `architecture.md`, `guidelines.md`, `docs/README.md`, `event-log.md` and `AGENTS.md` match. The falsifier's use of LOG-001, LOG-002 and LOG-009 is sound.
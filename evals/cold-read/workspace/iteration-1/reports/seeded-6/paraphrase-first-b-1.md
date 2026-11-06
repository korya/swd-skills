PARAPHRASE

The plan derives "overdue" when a command reads the log, and writes no event. An open or assigned ticket whose due time has passed shows `OVERDUE` in the state column of `ticketdesk list`. A new `ticketdesk overdue` subcommand prints only those tickets, ordered by due time and then by ID. A service method, `is_overdue`, holds the rule, and the CLI uses one shared line formatter. The work is gated on the user approving six spec edits (TKT-014, TKT-015, CLI-001, CLI-006, CLI-010, LOG-001). Service tests, a new CLI subprocess test file, doc edits and two commits follow.

According to the plan, the existing system replays an append-only log into tickets. Each ticket gets a `due_at` from the SLA table, and the store owns an injectable clock that stamps events. The CLI has four subcommands, parses with `argparse`, and prints fixed-width lines. The service holds all rules. The CLI has no tests, and CLI-007 is an open TODO about tracebacks. The plan's `scratch/` experiments I could not paraphrase beyond their stated results. That folder is not in the repo.

FINDINGS

- Severity: Blocker
  Where: Step 2 (`now()`), Step 2 prose, and the conventions table ("calls `store.clock()`").
  What: `now()` calls `self.store._clock()`, but the store has no `_clock` attribute. The attribute is `clock`. The plan contradicts itself, citing `_clock` at `store.py:16` and `store.clock()` in the conventions table. As written, every `list` and `overdue` call raises `AttributeError`.
  Evidence: `ticketdesk/store.py:16` is `self.clock = clock`. `grep _clock` finds nothing in the code.

- Severity: Blocker
  Where: Step 2, `Ticket.is_overdue`.
  What: The method body is `return now > self.due_at`. It has no `state != "closed"` check, although its docstring, TKT-014 and the test plan say a closed ticket is never overdue. `svc.overdue()` would therefore return closed late tickets, and `overdue` would list them. Step 3's `_line` re-checks state, so `list` would look right while `overdue` is wrong.
  Evidence: The plan's Approach summary says "true when the ticket is not closed". The Step 2 code does not do that. The unit test "closed … not overdue" would fail.

- Severity: Blocker
  Where: CLI-010 proposed text, against the test plan and CLI-008.
  What: The proposed CLI-010 says `overdue` with no overdue tickets "exits with code 1". The test plan says `overdue` on a missing log "prints nothing, exits 0". CLI-008 says a successful command exits 0. `list` with no tickets exits 0 per CLI-006. Exit 1 is also what the CLI-007 TODO calls the traceback code. The spec text sent for sign-off is wrong and inconsistent.
  Evidence: Plan lines 70-71 and 213. `docs/product-specs/cli.md:54-56`. Step 3 has no code that returns 1.

- Severity: Blocker
  Where: Test plan, the unit case "same due time" (and A6).
  What: The recipe does not produce a tie. A P2 (24h) created at `a`, then a P1 (4h) created after 12h, gives due times `a+24h` and `a+16h`. A tie needs the P1 created 20 hours later. The A6 claim "P1 at `a+12h` equals P2 at `a`" is wrong for the same reason. Its "P2 created 22 hours ago" is due 2 hours in the future, not 6 hours ago. The tie-break test would assert the wrong thing or pass for the wrong reason.
  Evidence: `ticketdesk/sla.py:3` has P1=4, P2=24. 24−4 = 20, not 12.

- Severity: Major
  Where: Step 6 intro ("These edits need no sign-off, because `AGENTS.md:93` limits the confirmation rule to product specs").
  What: The rule is not limited to specs. The plan edits `docs/architecture.md` (lines 12, 68-69, 103) and `AGENTS.md` without confirmation. The architecture edit adds a new service-to-clock dependency.
  Evidence: `AGENTS.md:93` says "Do not silently rewrite specs or architecture". `docs/README.md:39` says "Never silently update a spec or an architecture doc". `docs/guidelines.md:55` and `:78` say the same.

- Severity: Major
  Where: Assumptions table A2–A8 and the prototype output.
  What: Every piece of validation evidence cites `scratch/exp1_prototype.py` and `scratch/exp2_fake_clock.py`, and neither exists. The repo has no `scratch/` directory, and untracked `plan.md` is the only new file. None of the experiment results can be checked. The A6 narrative is wrong when recomputed, which lowers trust in the rest.
  Evidence: `ls scratch` returns "No such file or directory". `git status` shows only `plan.md` untracked.

- Severity: Major
  Where: Step 2 and Step 3 against `docs/architecture.md:36-38` and the "no rule in CLI" convention.
  What: The plan says the CLI "only picks a label". Step 3 duplicates the overdue rule in `_line` (`state in (...) and now > t.due_at`) instead of calling `Ticket.is_overdue`. The rule now lives in two places and is likely to drift. This is the same drift that produced the missing closed check in finding 2. The plan justifies it as "display does not depend on a service method", which is the opposite of the project's rule that the service owns ticket rules.
  Evidence: Plan lines 106 and 110. `docs/architecture.md:36-38`.

- Severity: Minor
  Where: Step 2, `now()` reads the store's clock.
  What: This adds a new read of the store's clock by the service. The clock is documented only as the event-stamping clock (`architecture.md:49-50`). The plan wraps it in a service method but still reads a store attribute directly, and the store exposes no accessor. The plan does not flag this as a layer or contract change in the spec step.
  Evidence: `docs/architecture.md:46-50`, `ticketdesk/store.py:14-16`.

- Severity: Minor
  Where: Step 5, unit test count, and Step 4 clock note.
  What: "Each clock call adds one second, so set now to one second before the target". `overdue()` now calls the clock itself when `now` is omitted, which bumps it again. The boundary tests must pass `now` explicitly or account for the extra tick. The plan does not say which.
  Evidence: `tests/test_tickets.py:12-14` (`self.now += 1` on every call).

Verified and fine: the line-number citations in the plan, the E2E due times (1700014400 and 1700159200), and `1_700_000_000` = 2023-11-14 UTC. `make test` passes its current 7 tests.
# Review of plan.md (overdue tickets)

Verdict: the design is sound (read-time derivation, no new event). But the code in the plan would crash and would show closed tickets as overdue, and two tests and one assumption rest on wrong arithmetic. Fix these before implementation. Findings are ordered by severity.

## High

### 1. `store._clock` does not exist: `AttributeError` on every `list` and `overdue`
- Plan: `plan.md:88` (`return self.store._clock()`) and `plan.md:97` ("private attribute `_clock` (`ticketdesk/store.py:16`)").
- Code: `ticketdesk/store.py:16` is `self.clock = clock`. The attribute is public. `grep` finds no `_clock` anywhere. The test fixture also passes `clock=Clock()` (`tests/test_tickets.py:20`).
- Effect: `TicketService.now()` raises `AttributeError`, so Step 3's `list` branch breaks. Today's `list` works, so this is a regression in an existing command.
- Inconsistency: `plan.md:187` says `now()` "calls `store.clock()`", which is the correct name. The plan contradicts itself.
- Evidence the experiments were not run on this code: A3/A4 claim the store clock was exercised, yet the code in Step 2 cannot run. See finding 5.
- Fix: use `self.store.clock()`. Also consider whether the service reaching into a store attribute is acceptable. `docs/architecture.md:46-50` says the store owns the clock. A `store.now()` method would be cleaner but is a new store API.

### 2. `Ticket.is_overdue` never checks the state: closed tickets count as overdue
- Plan: `plan.md:81-83`. The docstring says "past the due time and not closed", but the body is only `return now > self.due_at`.
- Spec: the proposed TKT-014 (`plan.md:57-58`) says a closed ticket is never overdue. The test at `plan.md:203` requires it.
- Effect: `svc.overdue()` (Step 2) returns closed tickets. Test case 3 (`plan.md:203`) fails. The e2e step `plan.md:228-229` still expects only #3 after `close 2`, but #2 would still be listed by `overdue`.
- Related: Step 3 (`plan.md:106`) re-implements the rule in the CLI formatter, with the state check that the service method lacks. So the two implementations disagree today.

### 3. The overdue rule is written twice, against the plan's own architecture claim
- Plan: `plan.md:106` ("the check is written out in the formatter, so display does not depend on a service method"), and `plan.md:110`, `plan.md:186` ("Step 3 only picks a label").
- Docs: `docs/architecture.md:36-38` ("It holds no ticket rules"). `docs/guidelines.md:51-53` calls a ticket rule in the CLI a layer crossing and says to bring it up before implementing.
- Effect: `now > t.due_at and t.state in (...)` in `cli.py` is a ticket rule in the CLI. It also duplicates `Ticket.is_overdue`. Finding 2 shows the copies already diverge. `list` and `overdue` can then disagree about what is overdue.
- Fix: the formatter calls `t.is_overdue(now)`. Fix `is_overdue` to include the state check. Remove the duplicate. The plan's reason ("display does not depend on a service method") does not outweigh the rule.
- The conventions list at `plan.md:186` claims compliance with the architecture rule. That claim is false for Step 3.

### 4. CLI-010 says "exit with code 1" when nothing is overdue, which contradicts the plan's own tests and the specs
- Plan: `plan.md:70-71` (spec text: "prints nothing and exits with code 1"). `plan.md:213` (test: missing log "exits 0").
- Specs: CLI-008 (`docs/product-specs/cli.md:54-56`) says success exits 0. CLI-007's TODO (`cli.md:50-52`) says exit code 1 is the code of an uncaught traceback. Exit 1 for "no results" therefore makes "nothing overdue" indistinguishable from "crashed on a corrupt log".
- Code: Step 3 (`plan.md:103-108`) never produces exit 1. `main()` returns 0 (`ticketdesk/cli.py:34`).
- Effect: the spec text to be signed off, the tests, and the code describe three different behaviors. Also, the empty-case test (`plan.md:213`) only covers a missing log, not an existing log with no overdue tickets.
- Fix: choose exit 0 and empty output (consistent with `list` per CLI-006 and CLI-008), and fix the CLI-010 text. If exit 1 is wanted, state it as a deliberate choice, say how it differs from the traceback exit, and implement and test it. The plan raises this in none of its nine open questions.

## Medium

### 5. Evidence cited from `scratch/` does not exist; the experiments cannot be verified
- Plan: A2–A8 (`plan.md:147-153`) and the prototype output (`plan.md:155-164`) cite `scratch/exp1_prototype.py` and `scratch/exp2_fake_clock.py`.
- Repo: `git ls-files` has no `scratch/`. `git status` shows only `plan.md` untracked. There is no `scratch/` directory on disk.
- Effect: A3/A4 ("the store's clock can serve as now") are marked Confirmed. The Step 2 code that reads the clock cannot have run (finding 1). The reader cannot re-run any of it. Mark these as unverified, or commit or inline the scripts.

### 6. The tie-break arithmetic is wrong, so test and assumption A6 do not produce equal due times
- Plan: `plan.md:205` ("Create a P2 ticket, move the clock 12 hours, then create a P1 ticket"). `plan.md:151` (A6: "P1 created 10 hours ago and a P2 created 22 hours ago are both due 6 hours ago. P1 at `a + 12h` equals P2 at `a`").
- SLA: `ticketdesk/sla.py:3`: P1 = 4h, P2 = 24h (`TKT-005`). The difference is 20 hours, not 12.
  - P2 at t is due at t+24h. P1 at t+12h is due at t+16h. They are not equal.
  - P1 created 10h ago is due 6h ago (correct). P2 created 22h ago is due in 2h, not 6h ago. A P2 would need to be created 30h ago.
- Second problem: the fake clock adds 1 second per call (`tests/test_tickets.py:12-14`), so each `create` has its own timestamp. Equal due times need the gap to be exactly 20h minus the one-second step (set `clock.now` carefully), or the test needs hand-written log events as the e2e does.
- Effect: as written the tie-break test would pass for the wrong reason or fail, and the "equal due times occur" premise in A6 is not shown.

### 7. Step 6 treats `architecture.md` and `AGENTS.md` edits as needing no sign-off, against the process rules
- Plan: `plan.md:127` ("limits the confirmation rule to product specs").
- Docs: `AGENTS.md:93` ("Do not silently rewrite specs or architecture"). `docs/README.md:10-11` ("Never silently update a spec or an architecture doc"). `docs/guidelines.md:55` (update `architecture.md` with user confirmation). `docs/guidelines.md:78` ("Confirm every doc change with the user").
- Effect: edits to `docs/architecture.md:12`, `:68-69`, `:103` need confirmation. The plan's gate (Step 1) covers only the product specs. The `AGENTS.md` edits are likewise "docs" under `guidelines.md:78`.
- Fix: move these into the Step 1 gate and list them for sign-off.

### 8. Spec edits are incomplete, and the claim "six spec edits" understates the change
- `CLI-006` (`cli.md:41-43`) says "one line per ticket", `<state>` is the state. The plan changes it for overdue, but `TKT-001` (`tickets.md:17`) says state is one of three values. TKT-014 handles this with "Overdue is not a state", but `OVERDUE` in the state column is exactly a fifth displayed value. A reader of CLI-006 cannot distinguish it, and scripts matching `open` or `assigned` lose rows (acknowledged at `plan.md:238`).
- The plan's trade-off statement (`plan.md:22-23`) says this "keeps the column count stable for scripts". That helps column-based parsers only; any parser of the state value breaks. This is a user-visible breaking change in a command that currently has no tests. A separate flag or marker column (e.g. `list --overdue` or a trailing `!`) was not weighed, and open question 1 only compares replace vs new column.
- `LOG-006` (`event-log.md:41-44`) says "Listing shows nothing" for a missing log. `overdue` on a missing log is tested against it (`plan.md:213`) but LOG-006 is not in the Step 1 edit list.
- `INV-001` / `LOG-009` are cited as holding, but the new `overdue` result depends on wall-clock time, so "replaying the same log always yields the same ... states" is true only because overdue is not a state. That is a fragile argument that TKT-014 should state explicitly: the result is not a function of the log alone.

## Low

### 9. Fake-clock boundary test is harder than the plan says
- Plan: `plan.md:116` ("set `now` to one second before the target"); `plan.md:201` ("exactly its due time is not overdue").
- Code: `tests/test_tickets.py:12-14` increments on every call, and `svc.create` itself calls the clock via `append`, plus Step 2's `now()` calls it again. Tests must account for every call. The plan's test list does not say how `overdue(now=...)` (explicit `now`) is used, which would avoid the problem. State that the boundary tests pass `now` explicitly.

### 10. Step 5 CLI tests: time-dependent hand-written fixture
- Plan: `plan.md:121-122`: fixture `at` values near 2023 are "in the past on any test run". True, but `plan.md:211` also expects a `open` ticket "created by the test", which uses the real clock, and the tie/ordering assertions in the e2e (`plan.md:227`) rely on the real `time.time()` being after 1700159200. Fine today; note it only holds because the real clock cannot go backward past 2023.
- The subprocess tests with `cwd` at the repo root (`plan.md:120`) depend on `python3 -m ticketdesk.cli` finding the package from cwd. Use the repo root computed from `__file__`, not the test runner's cwd, because `unittest discover -s tests` may run from elsewhere.

### 11. Minor accuracy and scope notes
- `plan.md:116`/Step 4 says unit tests go in `tests/test_tickets.py`; the plan lists "7 unittest cases" changes at `plan.md:132` but gives no count. Name the new total, or `AGENTS.md:102` will be wrong again.
- `plan.md:131` says `AGENTS.md:116` ("Not covered by tests: the CLI") changes. After Step 5 the CLI is partly tested (overdue and list only; `create`, `assign`, `close` still untested). "The CLI now has tests" overstates it.
- The commit split (`plan.md:139`) puts specs/docs in the first commit and code in the second. `docs/guidelines.md:47` says to update the spec after landing; ordering is arguable, not wrong.
- The plan's own question 9 assumes approval "as drafted" and says implementation must not start until confirmed. That is consistent with the rules, but `plan.md:36` says Steps 2–7 wait for sign-off while `plan.md:267` records an assumption of yes. Make it unambiguous that no assumed approval is carried into implementation.
- The CLI-007 TODO (`cli.md:50-52`) is open and the plan adds a command that inherits the traceback (`plan.md:30`). Acceptable per the plan, but `AGENTS.md:94-95` says to stop and discuss conflicts. Surface it as a question to the user before work, which question 6 does.

## What checks out
- A1: `due_at` is set on every `created` event (`ticketdesk/tickets.py:36`).
- `OVERDUE` is 7 characters and fits `{:<8}` (`ticketdesk/cli.py:30`).
- Replay and write paths are untouched, so INV-001, INV-002 and LOG-008 hold.
- `svc.list()` has a single caller (`ticketdesk/cli.py:29`).
- A missing log gives an empty result without creating the file (`ticketdesk/store.py:26-27`).
- `cli.py` line references (18, 28, 29) and the `CLI-001`/`LOG-001` line references match the files.

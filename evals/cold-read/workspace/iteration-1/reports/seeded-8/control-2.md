# Review of plan.md (overdue tickets)

Verdict: do not implement as written. Four defects would ship wrong behavior or a spec collision, and several "verified" claims do not hold in this repo. The overall shape (derived flag, no new event, rule in the service) is sound.

## Critical / High

1. **Wrong SLA table: P3 is 72 h, not 48 h.** plan.md:38 defines `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`. The source of truth is `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}` (ticketdesk/sla.py:3, TKT-005 at docs/product-specs/tickets.md:44). A P3 ticket would turn overdue 24 h early, contradicting TKT-005 and TKT-014's own wording ("later than its due time (TKT-005)"). The table is also a duplicate. `Ticket.due_at` already exists (ticketdesk/tickets.py:21, set at :36). The rule should be `now > self.due_at`. That removes the table and the drift risk, and also contradicts the plan's own claim A1 and "no duplicate logic" (plan.md:106).

2. **Boundary contradicts the spec the plan itself writes.** plan.md:39 uses `now >= created_at + ...`. TKT-014 (plan.md:30), open question 3 (plan.md:178) and the unit test (plan.md:114) all say "not overdue at the due time exactly". The code as planned is overdue at exactly the due time, so the boundary test would fail. It must be `>`.

3. **Wrong sort key for `overdue`.** plan.md:40 sorts by `(t.created_at, t.id)`. TKT-015 (plan.md:31) requires due time, then ID. Creation order is not due order, since P1 is 4 h and P3 is 72 h. This is the exact case plan.md:118 and A4 claim to test. Use `(t.due_at, t.id)`. The test would catch it, which is good, but the plan's own text is inconsistent.

4. **A4 evidence is invalid under the real SLA.** plan.md:72: a P3 ticket created 80 h ago (ID 1) and a P1 ticket created 6 h ago (ID 2). Real due times are 72 h and 4 h. P3 is due 8 h ago, P1 is due 2 h ago. The due-time order is `[1, 2]`, the same as ID order. The example does not distinguish the two sorts. It only "sorted as [2, 1]" under the wrong 48 h table (or by created_at). The test must use a pair where due order and ID order really differ, for example P3 created 73 h ago (ID 1) against P1 created 100 h ago (ID 2): the P1 is due 96 h ago and the P3 only 1 h ago, so due order is [2, 1] while ID order is [1, 2].

5. **New spec ID `CLI-009` is already taken.** docs/product-specs/cli.md:58 defines CLI-009 "Ticket ID is an integer". plan.md:34 and plan.md:98 propose CLI-009 as new. The "next free number" is CLI-010 (docs/README.md:27-28). Every later reference in the plan (steps 8, test plan, counterfactual) carries the same error. Also check TKT: TKT-013 is the last, so TKT-014/015 are right.

## Medium

6. **The test tooling assumed by the plan does not exist.** The repo uses `unittest` (Makefile:3, AGENTS.md:22-23 "Tests: unittest, make test"). The plan says the suite "runs under pytest" (plan.md:90), uses the pytest `tmp_path` fixture (plan.md:51), and runs `pytest -q` (plan.md:58). CI runs only `make lint` and `make test` (.github/workflows/ci.yml:11-12) and installs nothing, so `tmp_path` tests would not be collected by `unittest discover`, or would not run at all. AGENTS.md also states no dependencies. Use `unittest` and `tempfile.TemporaryDirectory`, matching tests/test_tickets.py:1-24. Also step 7 should be `make lint && make test`, which is the documented gate (AGENTS.md:90).

7. **Claimed argparse bug does not exist.** plan.md:47 says "the subparsers are not marked required" and a missing subcommand reaches the `list` branch. cli.py:14 has `required=True`, so no command exits 2 before reaching the branch. The `else:` → `elif` change is still a reasonable hardening, but the stated justification is false. Say so, or drop it as a drive-by edit (docs/guidelines.md: no drive-by edits). Also note that with `elif args.cmd == "list"` and a new `overdue` branch, make sure the chain is exhaustive.

8. **Referenced evidence is missing.** plan.md:71, 74 cite `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py`. Neither exists in the repo (`ls scratch` fails; git status shows only the untracked plan.md). A3 through A8 ("confirmed", "also on Python 3.12.16") cannot be reproduced by a reviewer. Either commit them or drop the "Verified" claims. A7's argparse claim also could not have shown a "missing subparsers are not required" case (see 7).

9. **Wall clock bypasses the store's clock (INV-005, LOG-009 spirit).** INV-005 (docs/product-specs/invariants.md:34-37) says time comes from the store's clock, never from the caller. The plan has the CLI call `time.time()` (plan.md:9, 46) and pass `now` in. That is the one reason a user-visible `list` output now depends on the wall clock, and it creates a second clock. The `EventStore` already has an injectable `clock` (ticketdesk/store.py:14). A cleaner design is `TicketService.overdue()` and `list` reading `self.store.clock()`. That keeps the CLI free of time handling and lets tests inject the existing fake clock. Note the fake `Clock` increments on every call (tests/test_tickets.py:12-14), so tests would need care. Decide this explicitly. As written it is an unflagged design choice.

10. **`list` replacing the state is a spec change with a data-loss side effect, and the plan decides it by assumption.** CLI-006 (docs/product-specs/cli.md:39-43) defines `<state>`. Replacing it with `OVERDUE` hides open vs assigned, and `overdue` output then carries zero information beyond the filter (plan.md:177). The plan flags this in open questions 1-2 but still builds the whole design around "replace". A suffix marker or a separate column would keep CLI-006's `<state>` field intact. Raise this to the top of the sign-off, not question 1 of 8. Also, TKT-001/CLI-003..005 all print `t.state`, so `create`/`assign` output stays consistent only if overdue stays out of those, which the plan does not state.

## Low

11. **Test count and doc line references are asserted without checking.** plan.md:56 says to update "the test count" at AGENTS.md:102. The AGENTS.md text says "7 unittest cases", and the current count is 6 in tests/test_tickets.py plus tests/test_store.py. Recount before editing. Line numbers cited for architecture.md:12, 94-96, 103 and AGENTS.md:102/114/116 should be rechecked at edit time. AGENTS.md also lists the spec table and the doc index (`CLI` row, "Commands"), which the plan does not update.

12. **Step 8 commit split breaks "one logical change per commit".** Commit 1 mixes specs with the service rule, and commit 2 mixes the CLI, `list` label change, and LOG-001 spec. Specs should be gated by sign-off (step 0) and could be their own commit. Minor, but docs/guidelines.md:84-87 asks for one logical change per commit.

13. **E2E script appends an out-of-order timestamp.** plan.md:139-143 writes an event with `at` 100 h in the past after an event at "now". LOG-004 says `at` is the append time, so this is a hand-crafted log that violates LOG-004/INV-005. It is acceptable as a test seam but should be called out as such. It also is not "the real user's flow", so there is no e2e path that gets a ticket overdue through the CLI alone.

14. **Edge cases not covered.** No test for an unknown-priority ticket in the log (replay would raise `ValueError`, and `overdue` inherits CLI-007's traceback; the plan notes it but includes no test). No test for non-ASCII or very long titles (unchanged behavior, so low priority). No test that `create`/`assign`/`close` output is unchanged.

## What is good

- Derived flag, no new event kind, no store change: consistent with INV-001, INV-002, LOG-002.
- The doc-change gate (step 0) matches AGENTS.md:93 and docs/README.md:39-40.
- The service/CLI split (rule in `Ticket`, label in the CLI) respects architecture.md layering, once findings 1 to 3 are fixed.

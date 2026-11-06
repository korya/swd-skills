# Review of plan.md (overdue tickets)

Checked against `ticketdesk/*.py`, `tests/`, `docs/`, and `AGENTS.md`. Nothing was run. Findings are ordered by severity.

## Critical

### 1. `now()` reads an attribute that does not exist
- Plan: `plan.md:88` calls `self.store._clock()`, and `plan.md:97` says "the store keeps its clock in the private attribute `_clock` (`ticketdesk/store.py:16`)".
- Code: `ticketdesk/store.py:16` is `self.clock = clock`. There is no `_clock`. The plan contradicts itself at `plan.md:187` ("calls `store.clock()`").
- Effect: `AttributeError` on every `list` and `overdue` call. The plan changes `list` to call `svc.now()` (`plan.md:107`), so this breaks a command that works today.
- Fix: use `self.store.clock()`. The attribute is public, so the "private attribute" justification goes away.
- Related: A3 (`plan.md:148`) claims the store's clock was exercised. A call to `_clock` would have failed.

### 2. `Ticket.is_overdue` skips the "not closed" rule
- Plan: the docstring at `plan.md:82` says "past the due time and not closed". The body at `plan.md:83` is `return now > self.due_at`. `plan.md:13` also says "true when the ticket is not closed".
- Effect: `overdue()` (`plan.md:93`) returns closed tickets that are past due, which violates TKT-014 and TKT-015. The planned unit test "closed ticket is not overdue" (`plan.md:203`) fails. `ticketdesk overdue` lists closed tickets, and the CLI would show them as `closed` (`_line` re-checks the state).
- Fix: `self.state != "closed" and now > self.due_at`.

### 3. The CLI re-implements the overdue rule, which contradicts the plan's own conformance claim
- Plan: `plan.md:106` writes `t.state in ("open", "assigned") and now > t.due_at` into the CLI formatter "so display does not depend on a service method". `plan.md:186` and `plan.md:110` claim "no ticket rule in the CLI".
- Docs: `docs/architecture.md:36-38` ("It holds no ticket rules"). `docs/guidelines.md:27-29` calls a ticket rule in the CLI a layer crossing.
- Effect: two copies of the rule, one of them wrong (finding 2). They will drift. The fix for 2 would have to be made in two places, and `list` would use a different definition from `overdue`.
- Fix: the formatter calls `t.is_overdue(now)`. Drop the duplicate check.

## High

### 4. CLI-010 exit code 1 for "no overdue tickets" contradicts the rest of the plan and the specs
- Plan: the CLI-010 text at `plan.md:70-71` says "prints nothing and exits with code 1". The test plan at `plan.md:213` says a missing log "prints nothing, exits 0".
- Specs: CLI-008 (`docs/product-specs/cli.md:54-56`) says a succeeding command exits 0. Exit 1 is the traceback code that CLI-007 (`cli.md:50-52`) lists as a defect. Exit 2 is the rule-error code. `list` on an empty log exits 0 (CLI-006, LOG-006).
- Step 3 (`plan.md:101-108`) has no code that returns 1. The behaviour appears in the spec text only, and it is not in the open questions.
- Fix: decide it explicitly. Exit 0 matches CLI-006 and CLI-008. If 1 is intended, add it to step 3, the tests, the e2e, and the open questions.

### 5. Evidence the plan relies on does not exist
- Plan: A2, A4, A5, A6, A7, A8 (`plan.md:147-153`), the risk at `plan.md:237`, and the prototype output at `plan.md:155-164` cite `scratch/exp1_prototype.py` and `scratch/exp2_fake_clock.py`.
- Repo: there is no `scratch/` directory. `git ls-files` shows none, and `git status` shows only `plan.md` as untracked. The reviewer cannot reproduce any "Confirmed" result.
- Evidence of unreliability: A3 is marked "Confirmed" but depends on the `_clock` call from finding 1, which cannot work against this code. Another "Confirmed" item (A6) is arithmetically wrong, see finding 6.
- Fix: commit the experiments, or drop the "Confirmed" labels.

### 6. The equal-due-time example is wrong
- Plan: A6 (`plan.md:151`) says "P1 at `a + 12h` equals P2 at `a` by arithmetic". The test at `plan.md:205` creates a P2, moves the clock 12 hours, and creates a P1.
- Arithmetic: `ticketdesk/sla.py:3` has P1 = 4h and P2 = 24h. P2 at `a` is due at `a+24h`. P1 at `a+12h` is due at `a+16h`. Equal due times need the P1 created at `a+20h`.
- Also: the fake `Clock` adds 1 second per call (`tests/test_tickets.py:12-14`), so the test must set `clock.now` to land exactly on `a+20h` minus one second. The plan notes the off-by-one for the boundary test (`plan.md:116`) but not here.
- Effect: the tie-break test as written asserts order by due time, not by ID, so it cannot detect a missing tie-break.
- The A6 wording "P1 created 10 hours ago and P2 created 22 hours ago" is also off: 10h ago + 4h = 6h ago, and 22h ago + 24h = 2h in the future.

### 7. The "no sign-off needed" claim for the doc edits in step 6 is wrong
- Plan: `plan.md:127` says `AGENTS.md:93` limits the confirmation rule to product specs.
- Docs: `AGENTS.md:93` says "Doc changes need user confirmation. Do not silently rewrite specs or architecture." `docs/README.md:39-40` says "Never silently update a spec or an architecture doc". `docs/guidelines.md:31` and `docs/guidelines.md:54-56` require confirmation for every doc change and for `architecture.md` after landing.
- Effect: step 6 edits `docs/architecture.md:12`, `:68-69`, `:103`, and `AGENTS.md:102-116` without the gate. This is a process violation the plan introduces. Step 1 should list these edits for sign-off too.
- Also missing: `docs/guidelines.md` (the TODO about CLI test coverage, `guidelines.md:11-13`), the `architecture.md` project-layout tree (it lists `test_tickets.py` and `test_store.py` only), and a check of `README.md` and `docs/product-specs/README.md` for command lists and feature summaries.

## Medium

### 8. `OVERDUE` replaces the state in `list` output, which is a lossy format change
- Plan: `plan.md:22-23`.
- A reader of `list` can no longer tell `open` from `assigned` for overdue tickets. Overdue assigned tickets are the ones where that distinction matters most: someone owns the ticket and it is late.
- The plan's justification ("keeps the column count stable") does not hold. A suffix or a marker column leaves existing columns in place, and so does `OVERDUE` replacing nothing.
- Any script that filters on the state column breaks. The plan lists this as a risk (`plan.md:238`) and mitigates it only by asking for sign-off.
- TKT-014 (`plan.md:56-59`) says "Overdue is not a state", and CLI-006 would then print it in the `<state>` field. The two specs conflict.
- Also, CLI-003/004/005 print `t.state`, so `assign` or `close` on an overdue ticket still prints `assigned` or `closed`, which is inconsistent with `list`.
- Suggestion: keep the state and add the marker (for example a trailing flag), or make `overdue` the only place that shows lateness. This is a product decision. It should be an explicit choice, not a default.

### 9. `list` takes on the clock without need
- Plan: `plan.md:107` makes `list` call `svc.now()`.
- Effect: `list` now depends on wall time, so its output changes with no change in the log. The same log no longer prints the same lines. LOG-009 (`event-log.md:56-59`) only covers replay, so the plan's claim that LOG-009 holds (`plan.md:19`) is narrower than the user-visible behaviour.
- Output being time-dependent also makes every CLI `list` test depend on fixture dates in the far past (`plan.md:121-122`). That is safe only until a test uses a fresh ticket, and the plan does use one (`plan.md:211`).

### 10. CLI tests have no clock seam, so no boundary test is possible at the CLI level
- Plan: `plan.md:121-123` says no seam is needed. `main()` builds `EventStore(args.log)` itself (`ticketdesk/cli.py:20`).
- Fine for the planned cases. The e2e fixture (`plan.md:221-225`) appends 2023-dated events after a real-time event, so the log is not in time order. Replay does not sort by `at`, so it works, but the fixture is not a realistic log.

### 11. `overdue(now=None)` has two ways to get the time
- Plan: `plan.md:90-92`, and the CLI reads `now` itself (`plan.md:107-108`).
- Effect: the CLI passes `now` for `overdue` but formats `list` with a separately-read `now`. Fine, but the default parameter is dead code in production and doubles the test surface. Keep one entry point.

## Low

### 12. Spec numbering, exit and wording details
- `LOG-001` edit (`plan.md:50`) covers only "listing". LOG-006 (`event-log.md:41-44`) says "Listing shows nothing" for a missing log. CLI-010 relies on LOG-006 (`plan.md:213`), so LOG-006 should also mention `overdue`.
- CLI-001 (`cli.md:14`) says "four subcommands" and names them. The plan changes it to five and adds `overdue`. It should also say whether `overdue` takes any arguments (`plan.md:31` rules out options).
- The sweep at `plan.md:179` says "no code in the repo parses" the `list` line. That is true, but the README and docs show example output. The plan does not say it checked them.
- Open question 9 is "approve the spec text", and the plan marks "assumption: yes". Step 1 is the gate, so this assumption must not stand in for approval.

## What holds up
- The read-time derivation keeps INV-001, INV-002, and INV-005 (no event is written).
- The boundary rule (strictly later) is consistent with the planned tests.
- A1 (`due_at` on every replayed ticket) and A7 (missing log gives an empty result) match `ticketdesk/tickets.py:35-36` and `ticketdesk/store.py:26-27`.
- The e2e due times check out: P1 at 1700000000 is due 1700014400, and P3 at 1699900000 is due 1700159200.
- The test count of 7 matches the current suite (6 in `test_tickets.py`, 1 in `test_store.py`).

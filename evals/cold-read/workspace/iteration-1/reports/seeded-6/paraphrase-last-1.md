FINDINGS

- Severity: Blocker
  Where: Step 2, `Ticket.is_overdue`, and the unit test "A closed ticket past its due time is not overdue"
  What: `is_overdue` is `return now > self.due_at`. It has no check for `closed`, although its docstring, the Approach summary and TKT-014 all say "not closed". `overdue()` filters only on this method, so it returns closed tickets. The CLI `_line` helper does check state, so `list` would look right while `overdue` listed closed tickets as `OVERDUE`.
  Evidence: plan.md:81-83 against plan.md:13 and plan.md:57-58. The plan's own e2e check, "close 2 … `overdue` → only #3" (plan.md:228-229), would fail, as would the closed-ticket unit test (plan.md:203).

- Severity: Blocker
  Where: Step 2, `now()`; also the "Project conventions" bullet on the store clock
  What: The store has no `_clock` attribute. The attribute is the public `clock`, set at line 16 (the plan cites that line). `self.store._clock()` raises `AttributeError`, so `svc.now()` crashes `list` and `overdue`. The plan contradicts itself, since the conventions section says `now()` "calls `store.clock()`".
  Evidence: `ticketdesk/store.py:16` is `self.clock = clock`. The only other use is `store.py:20`, `self.clock()`. `grep _clock` finds nothing. Plan.md:88 and :97 say `_clock`, and plan.md:187 says `store.clock()`.

- Severity: Blocker
  Where: Step 1, the CLI-010 text, "prints nothing and exits with code 1"
  What: This contradicts CLI-008 (success exits 0 with empty stderr). It also contradicts the plan's own test plan, which says `overdue` on a missing log "prints nothing, exits 0". Exit code 1 is also what an uncaught traceback gives today (CLI-007 TODO). The author would be asking for sign-off on spec text that conflicts with the plan's tests and with existing specs, and no open question covers it.
  Evidence: plan.md:70-71 against plan.md:213 and `docs/product-specs/cli.md:54-56`. The CLI-007 TODO is at `cli.md:50-52`.

- Severity: Blocker
  Where: Test plan ("Two tickets with the same due time…"), assumption A6, and the prototype output
  What: The tie-break test and the A6 arithmetic are wrong. P2 created at `a` is due at `a+24h`. A P1 created at `a+12h` is due at `a+16h`, not equal. Equal due times need the P1 created 20 hours later (24 − 4). A6 says "P1 created 10 hours ago and P2 created 22 hours ago are both due 6 hours ago". Using TKT-005, the P1 is due 6 hours ago (−10+4), but the P2 is due 2 hours from now (−22+24). So that example would not even be overdue. "P1 at a+12h equals P2 at a" is also false. The tie-break test as written would not exercise the tie-break and would pass for the wrong reason.
  Evidence: `docs/product-specs/tickets.md:40-44` (P1 4h, P2 24h) against plan.md:151 and plan.md:205.

- Severity: Major
  Where: Step 3, `_line` formatter, and the "Project conventions" bullet "Step 3 only picks a label"
  What: The plan puts the overdue rule (`t.state in ("open","assigned") and now > t.due_at`) into `cli.py` a second time, "so display does not depend on a service method". This duplicates the rule that Step 2 puts in the service. The architecture says the CLI "holds no ticket rules" and calls a rule in the CLI a layer crossing that must be surfaced before implementing. The plan then lists this convention as "reflected". Two copies can drift, and the duplicate is how the missing closed check in finding 1 stays hidden in `list`.
  Evidence: `docs/architecture.md:36-38` and `docs/guidelines.md:51-53` against plan.md:106 and plan.md:186. Step 3 also says "the service keeps the query" (plan.md:110), which is not what it does.

- Severity: Major
  Where: Step 6, "These edits need no sign-off, because `AGENTS.md:93` limits the confirmation rule to product specs"
  What: The cited rule does not say that. `AGENTS.md:93` says "Do not silently rewrite specs or architecture". `docs/README.md:39` says "Never silently update a spec or an architecture doc". `docs/guidelines.md:78` says "Confirm every doc change with the user". Step 6 edits `docs/architecture.md`, including an assumption, and `AGENTS.md` without sign-off, and the Step 1 gate does not cover them. This is a process violation.
  Evidence: `AGENTS.md:93`, `docs/README.md:39-40` and `docs/guidelines.md:77-80`, against plan.md:127.

- Severity: Major
  Where: Evidence for assumptions A2–A8 and the prototype output; "Experiments confirmed…"
  What: Every experiment cites `scratch/exp1_prototype.py` and `scratch/exp2_fake_clock.py`. No `scratch/` directory exists in the repo, and the only untracked file is `plan.md`. The experiment results cannot be reproduced or checked. Given the factual errors above (A6, `_clock`), the claim "Confirmed" is not trustworthy. A3 says the fake clock hits the boundary, yet the plan has the wrong attribute name.
  Evidence: `ls scratch` gives "No such file or directory". `git status` shows only `?? plan.md` plus pycache.

- Severity: Major
  Where: Headline and the trade-off in "Approach summary"
  What: The chosen design replaces `open` or `assigned` with `OVERDUE`. This loses the state and the assignee status of exactly the tickets that matter most. The justification, "keeps the column count stable for scripts", is undercut by the Risks section, which admits scripts matching `open` or `assigned` will miss these tickets. The alternative (keep the state, add a marker or suffix) is dismissed in one line. The plan flags the choice for sign-off, which is good, but its stated reason does not hold.
  Evidence: plan.md:22-23 against plan.md:238. Open question 1 is at plan.md:259.

- Severity: Minor
  Where: Step 2, `now()` reaching into the store
  What: The service reads the store's clock, and the plan now passes `now` in from the caller, while INV-005 and the architecture describe the clock as the store's, used to stamp events. The plan cites INV-005 as "events only", which is true. But reading a clock attribute from outside the store, in a layer that "never reads or writes the file itself", is a new coupling that the architecture does not describe. A public accessor on the store would be cleaner.
  Evidence: `docs/product-specs/invariants.md:36-37`, `docs/architecture.md:40-50`.

- Severity: Minor
  Where: Step 3, CLI structure and the CLI-001 spec text
  What: Step 3 turns the final `else:` into `elif args.cmd == "list":` and adds a new `else:` for `overdue`. A later subcommand would silently fall into `overdue`. This is tolerable for now, but an explicit `elif args.cmd == "overdue":` is safer. The CLI-001 edit also says "one of five" but does not say the `overdue` usage and unknown-command text changes. A8 correctly shows today's error lists four choices.
  Evidence: `ticketdesk/cli.py:28-30`, plan.md:107-108.

- Severity: Minor
  Where: Step 5, the claim that hand-written past-due fixtures need "no clock seam"
  What: The CLI tests depend on the real wall clock being after 2023-11-14 plus the SLA hours. The fixture also creates a "fresh" ticket through the CLI and expects it to be `open`. That works, but the test for "exactly at the due time" exists only in the service tests, so the CLI boundary is untested. This is acceptable but should be stated.
  Evidence: plan.md:121-123, plan.md:211.

- Severity: Minor
  Where: Step 7 and the commit plan
  What: "Two commits" bundles the spec text with the architecture and AGENTS.md edits from Step 6. Those edits (test count, "CLI now has tests") describe code that does not exist until the second commit, so the first commit leaves the docs untrue. The Step 6 `AGENTS.md:102` test-count edit also depends on the final test total.
  Evidence: plan.md:136-140 against plan.md:125-134.

PARAPHRASE

The document proposes deriving "overdue" at read time, with nothing written to the log. A ticket would be overdue when it is not closed and the store's clock is later than its due time. `ticketdesk list` would print `OVERDUE` in place of `open` or `assigned`. A new `ticketdesk overdue` command would list only those tickets, oldest due first, ties broken by ID. Six spec edits are to be signed off first, then the service method, the CLI changes, new service and CLI tests, and doc updates.

According to the document alone, the existing system replays an append-only event log into tickets, with the due time computed from the SLA table. The service holds the rules, the CLI only formats and maps errors, and the store owns the file and an injectable clock. `list` prints tickets in ID order, the CLI has no tests, and corrupt logs and unknown priorities escape as tracebacks (CLI-007). I could not paraphrase the claimed experiment results, because the scratch scripts they come from are not in the repo.
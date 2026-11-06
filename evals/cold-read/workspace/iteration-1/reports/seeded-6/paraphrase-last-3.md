FINDINGS

- Severity: Blocker
  Where: Step 2, `Ticket.is_overdue`; the TKT-014 text in step 1.
  What: The method's docstring and TKT-014 say a closed ticket is never overdue. The code is `return now > self.due_at` and has no state check. `TicketService.overdue()` filters only through this method, so it would return closed tickets past their due time. The CLI formatter does check state, so a closed ticket would be listed by `overdue` but printed with its state. The plan's own test "A closed ticket past its due time is not overdue" would fail. The plan says A3 confirmed the "after close it is not" case, but that cannot hold for this snippet.
  Evidence: plan.md:81-83 against plan.md:13, 57-58 and 203.

- Severity: Blocker
  Where: Step 2 `now()`; the "Project conventions" bullet on the injectable clock.
  What: The plan says the store keeps its clock in a private `_clock` attribute at `store.py:16`. The attribute is the public `clock`. `self.store._clock()` raises `AttributeError`, so `list` and `overdue` would crash. The plan also contradicts itself, because the conventions section says `now()` "calls `store.clock()`".
  Evidence: `ticketdesk/store.py:16` is `self.clock = clock`. `grep _clock` finds nothing in the repo. Compare plan.md:88, 97 and 187.

- Severity: Blocker
  Where: CLI-010 draft text (plan.md:70-71), against the test plan and e2e sequence (plan.md:213).
  What: The drafted spec says `overdue` with no results "exits with code 1". The test plan says `overdue` on a missing log "exits 0". CLI-008 says success exits 0. Exit code 1 is also what the CLI-007 TODO calls the traceback exit, so scripts could not tell "none overdue" from "crashed". CLI-006 `list` with no results prints nothing and exits 0. The plan's open questions never raise this choice, and the sign-off gate would approve the contradictory text.
  Evidence: `docs/product-specs/cli.md:43`, `:50-52` and `:54-56`; plan.md:70-71 against plan.md:213.

- Severity: Major
  Where: Step 3, "The check is written out in the formatter", and the conventions bullet citing `architecture.md:36-38`.
  What: The overdue rule (`state in ("open","assigned") and now > due_at`) is written a second time in the CLI, apart from `Ticket.is_overdue`. The project says the CLI holds no ticket rules, and the plan claims it follows that. The two copies can drift apart. This is already visible, because the service copy lacks the state check (see the first Blocker). The plan's justification that "display does not depend on a service method" runs against the cited passage.
  Evidence: `docs/architecture.md:36-38` ("It holds no ticket rules") and `docs/guidelines.md:51-53`; plan.md:106 and 186.

- Severity: Major
  Where: Step 6, "These edits need no sign-off, because `AGENTS.md:93` limits the confirmation rule to product specs".
  What: The cited rules cover more than specs. `AGENTS.md:93` says "Do not silently rewrite specs or architecture". `docs/README.md:39` says "Never silently update a spec or an architecture doc". `guidelines.md:78` says "Confirm every doc change", and `:55` requires confirmation for `architecture.md` updates. Step 6 edits `architecture.md` lines 12, 68-69 and 103, and `AGENTS.md` itself, without sign-off. Open question 9 also covers only the step 1 text.
  Evidence: `AGENTS.md:93`, `docs/README.md:39`, `docs/guidelines.md:55,78`; plan.md:127-134.

- Severity: Major
  Where: Test plan, tie-break unit case (plan.md:205); A6 (plan.md:151).
  What: The arithmetic is wrong, so the tie test would not produce equal due times. P2 is due created+24h. P1 is due created+4h. They tie only when the P1 is created 20h after the P2, not 12h. In A6, a P1 created 10h ago is due 6h ago, and a P2 created 22h ago is due 2h from now. They are not both due 6h ago. The sentence "P1 at a+12h equals P2 at a" is false. The fake clock also adds 1s per call, so exact equality needs the offset set carefully.
  Evidence: `docs/product-specs/tickets.md:42-44` (4h, 24h). 24 − 4 = 20. The prototype output at plan.md:163 shows `(1, -6.0)` and `(2, -6.0)`, but see the next finding.

- Severity: Major
  Where: "Assumptions validated" table, the prototype output block, and the Evidence cells.
  What: The plan cites `scratch/exp1_prototype.py` and `scratch/exp2_fake_clock.py` as evidence. No `scratch/` directory exists in the repo, and `git status` shows only `plan.md` untracked. I could not verify A2 to A8 or the printed output. A6's description of the experiment is arithmetically wrong, so the prototype data is doubtful. The Evidence column claims verification that a reader cannot reproduce.
  Evidence: `ls scratch` returns "No such file or directory". Plan.md:147-153 and 155-164.

- Severity: Minor
  Where: Headline and open question 9.
  What: The plan says six spec edits need sign-off, and the doc edits in step 6 are called "no sign-off" (see above). It also treats open questions 1 to 8 as assumed answers. The request says "show as OVERDUE", which could mean next to the state. Replacing the state is a lossy choice. Question 1 is raised, but the justification "keeps the column count stable" is weak, because the title already contains spaces and scripts split on whitespace, which the plan itself notes in its risks.
  Evidence: plan.md:22-23, 259 and 238.

- Severity: Minor
  Where: Step 6.
  What: The `docs/product-specs/README.md` index (line 80, tickets listing) and the repo `README.md` do not need changes. The plan is silent on whether `LOG-006`'s "Listing shows nothing" should also mention `overdue`. The plan tests `overdue` on a missing log (LOG-006), but the LOG-006 and LOG-001 edit list covers only LOG-001.
  Evidence: `docs/product-specs/event-log.md:43-44`; plan.md:50 and 213.

- Severity: Minor
  Where: Step 3.
  What: CLI-001 requires that an unknown subcommand prints usage and exits 2. The plan tests this only for "no subcommand". The `else:` branch for `overdue` also becomes the catch-all. That is harmless under `argparse` but fragile if a sixth command is added.
  Evidence: `ticketdesk/cli.py:28-30`; `docs/product-specs/cli.md:14-16`; plan.md:215 and 108.

Checked and correct: line references to `cli.py`, `tickets.py`, `sla.py`, the docs, `AGENTS.md`, `Makefile`, `ci.yml` and `pyproject.toml`. The e2e due times (1700014400, 1700159200) and the 5-line `wc -l` count. `make test` runs 7 tests and passes today.

PARAPHRASE

The document proposes deriving "overdue" at read time. A ticket that is open or assigned and whose due time has passed gets `OVERDUE` in the state column of `list`, with no new event. A new `overdue` subcommand prints only those tickets, ordered by due time and then by ID. The work is gated on user sign-off of six spec edits, followed by service code, CLI code, unit and subprocess tests, and doc updates.

According to the document alone, the CLI parses a command and calls the `TicketService`. The service derives every ticket by replaying the append-only log through the `EventStore`, which stamps events from an injectable clock. Each ticket carries a `due_at` computed from the SLA table. `list` prints every ticket in ID order, and the CLI is untested. The document describes the store clock as a private attribute `_clock`. That description is wrong, and I could not paraphrase it as working.
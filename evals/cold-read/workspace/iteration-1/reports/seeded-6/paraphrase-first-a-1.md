PARAPHRASE

The plan adds "overdue" as a value computed when the log is read, not as a stored state or event. A ticket is overdue if it is not closed and the store's clock is past its due time. `list` prints `OVERDUE` in the state column for such tickets. A new `ticketdesk overdue` subcommand prints only those tickets, ordered by due time and then by ID. The work is gated on sign-off of six spec edits, then code, service tests, new CLI subprocess tests, doc updates and two commits.

According to the document, the CLI parses a command and calls `TicketService`. The service replays the event log into tickets, each with a due time from the SLA table. The store appends and replays JSON lines and stamps events from an injectable clock. Specs carry stable IDs, and spec changes need user confirmation. No CLI tests exist yet, and `list` prints one line per ticket in ID order.

FINDINGS

- Severity: Blocker
- Where: Step 2, `TicketService.now()`. Also "Project conventions", the time/clock bullet.
- What: The store has no `_clock` attribute. The plan cites `store.py:16` for it, but the attribute is public `clock`. As written, every `list` and `overdue` call raises `AttributeError`. The plan also contradicts itself: the conventions bullet says `now()` "calls `store.clock()`".
- Evidence: `store.py:16` reads `self.clock = clock`, and `grep` finds no `_clock` in `ticketdesk/`. Plan line 88 reads `return self.store._clock()`. Plan line 187 reads "which calls `store.clock()`".

- Severity: Blocker
- Where: Step 2, `Ticket.is_overdue`.
- What: The code omits the "not closed" condition. Its docstring and TKT-014 both require that condition, and so does the plan's summary at line 13. `overdue()` therefore returns closed tickets whose due time has passed. The plan's own test ("closed ticket ... is not overdue") would fail. The e2e step "close 2, then `overdue` shows only #3" would also fail.
- Evidence: Plan line 83 reads `return now > self.due_at`. The docstring on line 82 says "past the due time and not closed". TKT-014 (line 57) says "A `closed` ticket is never overdue."

- Severity: Major
- Where: Step 3, `_line` formatter, versus the Step 2 rule and the conventions section.
- What: The overdue rule is written a second time in the CLI, as `t.state in ("open","assigned") and now > t.due_at`. The service has its own copy, and the two copies already disagree (see the previous finding). The architecture says the CLI holds no ticket rules. The plan claims it complies, yet puts a rule in the CLI.
- Evidence: Plan line 106, "The check is written out in the formatter, so display does not depend on a service method." `architecture.md:36-38` says "It holds no ticket rules." Plan line 186 says "Step 3 only picks a label." `guidelines.md:51-53` calls a ticket rule in the CLI a layer crossing.

- Severity: Major
- Where: Test plan (unit case for ties), A6, and the e2e comments.
- What: The tie-break arithmetic is wrong. P1 is 4 hours and P2 is 24 hours, so equal due times need the P1 ticket created 20 hours after the P2 ticket, not 12. The planned test would not produce a tie and would not exercise the ID tie-break. A6's "confirmed" claim also rests on wrong numbers.
- Evidence: Test plan line 205 reads "Create a P2 ticket, move the clock 12 hours, then create a P1 ticket". With `sla.py:3`, P1 at +12h is due at a+16h and P2 is due at a+24h. A6 (line 151) says "P2 created 22 hours ago" is due 6 hours ago, but 22h − 24h means due in 2 hours.

- Severity: Major
- Where: CLI-010 proposed text, versus the test plan and CLI-008.
- What: The new spec says that with no overdue tickets `overdue` exits with code 1. This was not requested. It contradicts CLI-008 (success exits 0) and the plan's own test, where `overdue` on a missing log "exits 0". It also collides with exit code 1, which the CLI-007 TODO uses for tracebacks. The plan lists it in no open question.
- Evidence: Plan lines 70-71, "prints nothing and exits with code 1". Plan line 213, "prints nothing, exits 0". `cli.md:54-56` is CLI-008.

- Severity: Major
- Where: "Assumptions validated", A2-A8, and the prototype output block.
- What: The evidence cites `scratch/exp1_prototype.py` and `scratch/exp2_fake_clock.py`, but no `scratch/` directory exists in the repo. `git status --ignored` shows none either. None of the "Confirmed" results, including the pasted prototype output, can be reproduced. Because the prototype's tie-break and clock numbers are wrong or unverifiable, "Confirmed" is unsupported.
- Evidence: `ls -a` shows `.git .github AGENTS.md docs plan.md Makefile pyproject.toml README.md tests ticketdesk` and no `scratch`.

- Severity: Major
- Where: Step 6.
- What: The plan says doc edits to `architecture.md` and `AGENTS.md` need no sign-off, because the rule "limits the confirmation rule to product specs". The rule says the opposite. Step 6 would break the plan's own process rule.
- Evidence: `AGENTS.md:93` reads "Doc changes need user confirmation. Do not silently rewrite specs or architecture." `docs/README.md:39-40` and `guidelines.md:55,78` say the same. Plan line 127 says the opposite.

- Severity: Minor
- Where: Step 7 and the Step 1 gate.
- What: The plan's spec commit also holds the Step 6 doc edits ("spec and doc text"), but those edits describe tests and commands that do not exist until the code commit. The first commit would leave `AGENTS.md` stating that CLI tests exist, and a test count, before they do.
- Evidence: Plan line 139. Step 6 line 131, "the CLI now has tests".

- Severity: Minor
- Where: Test plan, e2e comments.
- What: `list` and `overdue` read the clock for "now", but the e2e sequence relies on the real clock being later than 2023 timestamps and on the first `create` using the real clock. This works today (2026). The plan never says the e2e line counts assume that.
- Evidence: Plan lines 221-230. Checked arithmetic: #2 is due 1700014400 and #3 is due 1700159200, both correct. `wc -l` of 5 is correct.

Decisions left to the reader without saying so:
- The `overdue` exit code for the empty case (see the CLI-010 finding). It is not in the open questions.
- Whether `now()` should be a public service method, or `overdue()` should take the clock reading itself. This is how Step 2 and Step 3 end up with two copies of the rule.
- How `main()` gets a clock in CLI tests, given the fixture's dependence on the real wall clock.
- The reconciliation of the CLI-001 wording ("one of four" becoming "five") with the usage text. The plan tests only that usage "names overdue".

Verified correct: the cited line numbers in `cli.py`, `tickets.py:35-36`, `store.py:26-27`, `sla.py:6-9`, the `docs/` and `AGENTS.md` cites, and the Makefile, CI and pyproject cites. `make test` runs 7 tests, all OK. `OVERDUE` is 7 characters and fits the 8-character column.
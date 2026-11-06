PARAPHRASE

The plan adds read-time "overdue" logic. A ticket is overdue if it is not closed and the store's clock is past its due time. Nothing new is written to the log. `ticketdesk list` would print `OVERDUE` in place of `open` or `assigned` in the state column. A new `ticketdesk overdue` subcommand would print only overdue tickets, oldest due first, with ties broken by ID. Work goes in seven steps. Step 1 is a sign-off gate on six spec edits. Steps 2 to 5 cover the service method, the CLI, and two test files. Steps 6 and 7 cover the doc edits, verification and two commits.

According to the document alone, the existing system works like this. A CLI calls `TicketService`, which replays an append-only log through `EventStore` and derives each ticket, including a `due_at` from the SLA table. The CLI has `create`, `assign`, `close` and `list`. Specs carry IDs such as TKT, CLI, LOG and INV, and changing them needs user sign-off. The store has an injectable clock, and the CLI has no tests. I can't paraphrase the `scratch/exp*.py` experiments the document leans on, because the document only reports their results.

FINDINGS

- Severity: Blocker
  Where: Step 2 (code block and the sentence after it), and the "Project conventions" bullet on the injectable clock
  What: The plan reads `self.store._clock()` and cites `store.py:16` for a private `_clock`. The attribute is public `clock`, so `now()` raises `AttributeError`, and so does every `list` and `overdue` run. The conventions section writes `store.clock()`, which contradicts Step 2.
  Evidence: `ticketdesk/store.py:16` is `self.clock = clock`. `grep -rn "_clock" ticketdesk tests` returns nothing.

- Severity: Blocker
  Where: Step 2, `Ticket.is_overdue`
  What: The body is `return now > self.due_at`, with no check that the ticket is not closed. Its docstring and TKT-014 say a closed ticket is never overdue. As written, a ticket closed late (or any closed ticket past due) is reported as overdue. The plan's own unit test "A closed ticket past its due time is not overdue" would fail.
  Evidence: the plan says "TKT-014: past the due time and not closed", but the code is `return now > self.due_at`.

- Severity: Blocker
  Where: CLI-010 proposed text, versus the Test plan and CLI-008
  What: CLI-010 says that with no overdue tickets the command "prints nothing and exits with code 1". The test plan says `overdue` on a missing log "prints nothing, exits 0". CLI-008 requires exit 0 and an empty stderr for any successful command. The request doesn't ask for a nonzero exit, and the plan lists no reason for one.
  Evidence: the plan has "prints nothing and exits with code 1" (CLI-010) and "prints nothing, exits 0, and creates no file" (test plan). `docs/product-specs/cli.md:56` is "A command that succeeds exits with code 0".

- Severity: Major
  Where: Assumption A6, and the Step 2 / Test plan tie-break case
  What: The arithmetic for equal due times is wrong. P2 is due at +24h and P1 at +4h, so a tie needs P1 created 20h after P2, not 12h. A P1 created 10h ago and a P2 created 22h ago are due at −6h and −2h, not both −6h. The planned tie test would not produce a tie and so would not exercise the ID tie-break.
  Evidence: the plan says "Create a P2 ticket, move the clock 12 hours, then create a P1 ticket" and "P1 at `a + 12h` equals P2 at `a`". `ticketdesk/sla.py:3` has `{"P1": 4, "P2": 24, "P3": 72}`.

- Severity: Major
  Where: Assumptions table A1–A8, the prototype output, and the Risks section
  What: All the experiment evidence cites `scratch/exp1_prototype.py` and `scratch/exp2_fake_clock.py`. Neither exists in the repo or in git, so the "Confirmed" results can't be reproduced. That includes the `invalid choice` message and "5 lines" in A5. The only claim I could cross-check, A6, is wrong (see above).
  Evidence: `ls scratch` gives "No such file or directory". `git ls-files | grep scratch` is empty. `git status` shows only `plan.md` untracked.

- Severity: Major
  Where: Step 3 (the `_line` formatter), versus "Project conventions" and the Step 3 closing paragraph
  What: The formatter duplicates the overdue rule in the CLI (`t.state in ("open","assigned") and now > t.due_at`) while the service also has `is_overdue`. This is a ticket rule in the CLI, which the architecture forbids. It leaves two copies that can drift. The plan says "Step 3 only picks a label" and "the service keeps the query", which doesn't match.
  Evidence: `docs/architecture.md:36-38` says "It holds no ticket rules." `docs/guidelines.md:51-53` calls a ticket rule in the CLI a layer crossing. The plan says "The check is written out in the formatter, so display does not depend on a service method."

- Severity: Major
  Where: Step 6 ("These edits need no sign-off, because `AGENTS.md:93` limits the confirmation rule to product specs")
  What: The cited rule doesn't limit confirmation to specs. It names specs and architecture as examples, and the other docs say to confirm every doc change. Step 6 edits `docs/architecture.md` and `AGENTS.md` without sign-off, and Step 7 commits them.
  Evidence: `AGENTS.md:93` says "Doc changes need user confirmation. Do not silently rewrite specs or architecture." `docs/guidelines.md:78` says "Confirm every doc change with the user." `docs/guidelines.md:55` says to update architecture.md "with user confirmation".

- Severity: Minor
  Where: Step 5, "Those due times are in the past on any test run, so `main()` needs no clock seam"
  What: This holds for the hand-written rows only. The same plan expects the test to create a fresh `open` ticket through the CLI, which uses the real clock and so isn't deterministic. The `open` assertion is safe only because P3 is 72h. This is also not stated as an assumption.
  Evidence: the plan says "`open` for a ticket created by the test", and `sla.py:3` gives P3 = 72 hours.

- Severity: Minor
  Where: Step 4, and the unit test for exact-boundary behavior
  What: `now()` reads the fake clock, which advances one second per call. The "set `now` to one second before the target" advice is correct only if exactly one clock call happens before the check. Whether `overdue()`, which also calls `now()`, adds a call is left implicit, so the boundary test is fragile. The tests can avoid this by passing `now` explicitly, but the plan doesn't say so.
  Evidence: the plan says "Each clock call adds one second". `tests/test_tickets.py:11-14` has `self.now += 1` on each call.

Decisions left to the next reader without being stated:
- Whether `LOG-001` is meant to cover `overdue` reading the clock. The plan only edits the wording.
- Whether `now()` becomes a public service API, or whether `overdue()` should take `now` at all. Step 2 does both without a spec entry.
- Whether the Step 1 "gate" lets Step 6's doc edits proceed without approval. The plan contradicts itself on this (see the Major finding above).
- Which exit code `overdue` returns on empty output (see the Blocker above).

Checked and correct: all the cited `cli.py`, `store.py`, `sla.py`, `docs/*` and `AGENTS.md` line numbers I tested, the e2e due-time arithmetic (1700014400 and 1700159200) and its 5-line count, and `make test` reporting 7 tests passing.
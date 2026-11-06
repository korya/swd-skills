FINDINGS

- Severity: Blocker
  Where: cli.md, CLI-006, the example and the sentence after it (lines 57–68)
  What: The example contradicts itself. It is introduced as "when only ticket 1 is overdue", but it shows tickets 1 and 4 as `OVERDUE`. The closing sentence says ticket 4 is listed "after the tickets that are not overdue", but ticket 1, which is overdue, is listed before it. The text just above also says a script counts overdue tickets by counting `OVERDUE` lines. That count is 2 here and 1 by the intro. A tester or implementer who derives a case from this example gets a wrong expectation.
  Evidence: cli.md lines 59–68, "when only ticket 1 is overdue:" followed by `#4 [P2] OVERDUE  Reset the badge printer` and "Ticket 4 is overdue and is listed in ID order, after the tickets that are not overdue."

- Severity: Major
  Where: tickets.md Goals, third bullet. cli.md CLI-006, the "same line as in 0.3.0" claim.
  What: The draft replaces the state with `OVERDUE`. This loses the `open` versus `assigned` distinction for exactly the tickets that matter most. It also breaks any consumer that selects lines by state. Goal 3 only promises no change for tickets that are not overdue, so it hides this break. The open questions list the replace-versus-append choice, but the body and examples are written as if replace were decided. The request only says tickets "show as OVERDUE", and appending a marker would satisfy that without the loss. The draft picks the more destructive reading as its default.
  Evidence: CLI-006 line 51, "shows `OVERDUE` in place of the state". The open question says "a script that selects lines by `open` or `assigned` misses every overdue ticket."

- Severity: Major
  Where: tickets.md TKT-014, and the missing mechanism for fixing the current time at the CLI level
  What: "A test can fix it" does not say how. Today only `EventStore` has an injectable clock (`EventStore(path, clock=...)`). `TicketService` has no clock, and `cli.py` builds `EventStore(args.log)` with the default. The spec does not say which clock "now" comes from. It also does not say whether that clock is the store's, which INV-005 and the architecture doc treat as the single time source. `list` and `overdue` become time-dependent, and the CLI has no tests today. A later plan has to invent the mechanism, and the CLI e2e tests can only fix the time by hand-writing old `at` values into the log.
  Evidence: store.py:14, cli.py:20, tickets.py:27–28. AGENTS.md: "Not covered by tests: the CLI". guidelines.md planning step 5.

- Severity: Minor
  Where: tickets.md TKT-017, the claim that LOG-009 "still holds"
  What: LOG-009 says replay is deterministic for states, assignees, resolutions and due times. TKT-017 carves overdue out as a fourth derived value that depends on the clock. It does not amend LOG-009 or INV-001 ("state … derived by replaying the log"), and it leaves a gap in how those rules are worded. Also, `list` output stops being a pure function of the log. That is a change in character for CLI-006, and it is only mentioned in passing.
  Evidence: event-log.md LOG-009. invariants.md INV-001.

- Severity: Minor
  Where: tickets.md, the intro paragraph (lines 5–7)
  What: The intro states in the present tense that "A ticket whose due time has passed is overdue until it is closed". That is draft behavior that is not built, and it sits above the draft banner in the part of the file that describes the current product. Its link to the draft helps, but a reader of the intro alone gets a false picture of 0.3.0. The same applies to the unmarked tickets.md row edits in the README and AGENTS.md, which do carry "not built".
  Evidence: tickets.md lines 4–7 versus line 98, "ticketdesk 0.3.0 has no overdue behavior".

- Severity: Minor
  Where: tickets.md Goals and TKT-019, the output of `overdue`
  What: Ordering by due time is the main point of `overdue`, but no output shows the due time. A user cannot see or check the order, and a P3 ticket created earlier can appear after a P1 ticket created later, with nothing to explain it. The draft says this itself in an open question, but TKT-019 is written as firm.
  Evidence: the Non-goals bullet "No display of the due time". The open question "the output of `overdue` does not show why its tickets are in that order".

- Severity: Minor
  Where: tickets.md TKT-015, and the non-goal "No record of lateness"
  What: A ticket closed after its due time is never marked late anywhere. This may not be what support agents want, since they often review late closures. It is flagged as an open question, but it is also built into the non-goals, so a change later needs a log or spec change. The spec does not note that the data to compute it later is already in the log, because closing events carry `at`.
  Evidence: TKT-015 and the non-goal "After a late ticket is closed, nothing shows that it was late". LOG-003.

- Severity: Minor
  Where: Scope of the edits (AGENTS.md, product-specs/README.md)
  What: Two files outside the stated review scope also changed. AGENTS.md says "Doc changes need user confirmation". The draft status is recorded in several places (AGENTS.md, README, cli.md, tickets.md), so that status must be updated in all four when it is signed off, and nothing lists them. This is a small risk of drift.
  Evidence: `git diff --stat` lists AGENTS.md and docs/product-specs/README.md alongside the two named files.

Checked and correct:
- TKT-014 example: 5 hours after creation, P1 (4h) is overdue and P2 (24h) is not.
- TKT-019 example: P3 created 73h ago was due 1h ago, and P1 created 10h ago was due 6h ago, so ticket 2 comes first.
- TKT-019 equal-due-time example: a P1 and a P2 created 20h apart can tie.
- CLI-006 padding: `OVERDUE` is 7 characters plus 1 pad, so two spaces before the title, which matches the example lines.
- CLI-011 and CLI-012 claims about 0.3.0, run in the repo:
  - `list extra` is rejected with exit 2.
  - `-h` exits 0.
  - A corrupt log gives a traceback with exit code 1.
  - A missing log file prints nothing, exits 0, and does not create the file.
- `make test` runs 7 passing cases, as AGENTS.md says.

PARAPHRASE

What the document proposes: `ticketdesk list` should show `OVERDUE` instead of the state for any ticket that is not closed and whose due time (creation time plus its priority's hours) is before the current time. A new `ticketdesk overdue` command would print only those tickets, using the same line format, sorted by due time ascending with ties broken by ID. Overdue is computed on each run and never written to the log. The draft takes no alert, no new options and no display of the due time. It leaves nine assumptions as open questions for the user to confirm.

How the system works today, per the document alone: the `ticketdesk` command has four subcommands (`create`, `assign`, `close`, `list`) and one log file. Each command replays the whole append-only JSON lines log to rebuild the tickets. Tickets move `open` → `assigned` → `closed`, and the priority sets a due time of 4, 24 or 72 hours after creation. `list` prints every ticket in ID order as `#id [priority] state title`. A corrupt log line stops every command, and today that escapes as a traceback with exit code 1, which is the open CLI-007 TODO.

I could not paraphrase the CLI-006 example. It contradicts its own introduction about which tickets are overdue.
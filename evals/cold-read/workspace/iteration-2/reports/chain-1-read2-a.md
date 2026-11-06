FINDINGS

- Severity: Blocker
  Where: cli.md, CLI-006, the example and the sentence under it (lines 59–68)
  What: The example contradicts itself and the rule it illustrates. It is introduced as "when only ticket 1 is overdue", but it prints ticket 4 as `OVERDUE` too. The note under it says ticket 4 is "listed in ID order, after the tickets that are not overdue". Ticket 1, which is overdue, comes first, and ticket 4 follows ticket 3 only because of its ID. A tester or implementer cannot tell which is intended.
  Evidence: cli.md:59 "when only ticket 1 is overdue" and cli.md:65 `#4 [P2] OVERDUE  Reset the badge printer`. The sentence at cli.md:68 conflicts with cli.md:51–53 ("order stays the ID order … does not move") and with the example, where overdue ticket 1 is listed first.

- Severity: Major
  Where: cli.md, CLI-006 (lines 55–59); tickets.md, Goals
  What: The claim that a script counts overdue tickets by counting `OVERDUE` lines only holds if the script parses the state field. A plain `grep -c OVERDUE` also matches titles that contain the word, and the spec admits titles may. "Every output line with OVERDUE in that position is one overdue ticket" is true, but the conclusion drawn from it is not safe for the stated audience, which is scripts.
  Evidence: cli.md:56–59 "A title may contain the same word … so a script counts the overdue tickets by counting those lines". Line format from ticketdesk/cli.py:28: `#{id} [{priority}] {state:<8} {title}`.

- Severity: Major
  Where: tickets.md and cli.md, `OVERDUE` replaces the state (CLI-006, CLI-010)
  What: Replacing the state with `OVERDUE` drops information that `list` shows today. Open versus assigned can no longer be told apart for the tickets that matter most, and existing scripts filtering on `open` or `assigned` silently miss every overdue ticket. The spec records this as an open TODO but still writes it into CLI-006 and CLI-010 as the behavior. Goal 3 ("no change for a ticket that is not overdue") protects only the non-overdue lines, so the breaking change falls on exactly the overdue ones. The request says tickets "show as OVERDUE" and does not say the state must disappear. The alternative of keeping the state and adding a column deserves to be the default, or the choice should be made before sign-off, because CLI-006 and CLI-010 and the example all depend on it.
  Evidence: tickets.md open question 2, "a script that selects lines by `open` or `assigned` misses every overdue ticket". cli.md:51 "shows `OVERDUE` in place of the state".

- Severity: Major
  Where: cli.md CLI-001 and CLI-006, tickets.md intro, AGENTS.md, product-specs/README.md
  What: The draft edits live, authoritative specs as if the behavior existed. The product-specs README calls these files the "Authoritative description of what ticketdesk does", yet CLI-001 now says "one of five subcommands" and tickets.md line 5 states overdue as fact. Both are false for 0.3.0, and a test derived from CLI-001 fails today. The status notes mitigate this but do not remove it. AGENTS.md, README.md and the index rows were also changed, and the project rules say doc changes need user confirmation. The sign-off pending on the spec has not covered those edits either.
  Evidence: `git diff` of cli.md:20, tickets.md:5, AGENTS.md "Specified, not built…". ticketdesk/cli.py registers only create, assign, close and list. docs/product-specs/README.md says "Authoritative description". AGENTS.md says "Doc changes need user confirmation".

- Severity: Minor
  Where: tickets.md, TKT-014 and TKT-017; cli.md, CLI-010 and CLI-012
  What: The clock source is under-specified. TKT-014 says "the time at which the command runs … A test can fix it". It does not say the time is read once per command, so a ticket could be judged overdue on one line and not on the next. It does not say it comes from the store's clock, which architecture.md describes as the only time source. The CLI builds `EventStore(args.log)` with the default clock, so there is no injection point from the CLI. The spec also does not say what happens when the local clock is behind the log's `at` values, or when a ticket is judged against timestamps written by another machine.
  Evidence: architecture.md:49–50 and 68–69 (the injectable clock and "never from the caller"). ticketdesk/cli.py:19 `TicketService(EventStore(args.log))`.

- Severity: Minor
  Where: tickets.md, TKT-017
  What: The carve-out from LOG-009 ("Whether a ticket is overdue is not one of them") and the interplay with INV-001 are asserted but not shown to be safe. INV-001 says state is derived from replaying the log. Overdue is now derived from the log plus the clock. The draft argues that this is not state, which is reasonable. It is a judgment on an invariant, and the project rule says to surface that to the user. It appears only in prose, not as an open question.
  Evidence: invariants.md INV-001; event-log.md LOG-009; tickets.md TKT-017.

- Severity: Minor
  Where: cli.md, CLI-012
  What: CLI-012 names only a corrupt line as the failure that stops `overdue`. A log with an unknown priority in a `created` event also fails during replay, because `due_at` raises `ValueError` while the tickets are rebuilt. That is also a traceback with exit code 1, and it is also covered by the CLI-007 TODO. The spec describes the failure as a corrupt-log case only.
  Evidence: ticketdesk/tickets.py:34 (`due_at(ev["at"], ev["priority"])` inside `_tickets`). ticketdesk/sla.py:8–9 raises `ValueError`. cli.md:75–77 lists unknown priority as a separate failure.

- Severity: Minor
  Where: tickets.md, TKT-013 and TKT-018
  What: TKT-013 says "Listing returns every ticket, closed ones included", and the draft adds a second "overdue listing". The draft does not say that TKT-013 now means the `list` command only. This is an ambiguity left in an existing item.
  Evidence: tickets.md:86 versus tickets.md TKT-018.

- Severity: Minor
  Where: tickets.md, TKT-014 ("A test can fix it")
  What: This sentence is an implementation and testing hint. The project's spec rules say specs describe what the system does, not how it is built or tested. The CLI also has no tests today, so the hint cannot be applied at the CLI level.
  Evidence: product-specs/README.md "Behavioral … decoupled from implementation". AGENTS.md "Not covered by tests: the CLI".

Checked and correct:
- Every number. TKT-014: a P1 ticket 5 hours old is overdue and a P2 ticket is not. TKT-019: ticket 1 is P3 and 73 hours old, so due 1 hour ago. Ticket 2 is P1 and 10 hours old, so due 6 hours ago, so ticket 2 comes first. The equal-due-time example is correct (a P1 ticket created 20 hours after a P2 ticket).
- The `OVERDUE` padding.
- The claims about 0.3.0: four subcommands, `list extra` rejected with exit 2, `-h` exits 0, `--log` is a global option placed before the subcommand, a corrupt log gives a traceback with exit 1, and a missing log gives an empty list without creating the file.
- `make lint` and `make test` pass: 7 tests, OK.
- The citations I checked (LOG-004, LOG-006, LOG-007, LOG-009, INV-004, CLI-007, CLI-008) exist and say what the draft says they do.

PARAPHRASE

What the document proposes: A ticket that is not closed and has passed its due time (creation plus 4, 24 or 72 hours by priority) counts as overdue. Overdue is computed from the log and the current time on every run and is never written to the log. `ticketdesk list` keeps its ID order, but an overdue ticket shows the word `OVERDUE` in place of its state. A new `ticketdesk overdue` command prints only the overdue tickets, in the same line format, earliest due first and ties by ID. It takes no arguments, prints nothing when no ticket is overdue, and fails on a corrupt log like every other command. Nine open questions are left for the user to confirm.

How the existing system works, according to the document alone: Tickets are rebuilt by replaying an append-only JSON-lines log. Each ticket has a state of open, assigned or closed, and a due time from its priority. The CLI has four subcommands (create, assign, close, list). `list` prints every ticket in ID order as `#id [priority] state title`. Rule errors exit with code 2. A corrupt log line, or an unknown priority, currently escapes as a traceback with exit 1, which is an open TODO under CLI-007. A missing log file behaves as an empty one.
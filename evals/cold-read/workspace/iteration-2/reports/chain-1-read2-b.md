FINDINGS

- Severity: Blocker
  Where: cli.md, CLI-006, the example list and the text after it
  What: The example contradicts itself. The lead-in says "only ticket 1 is overdue", but the output marks tickets 1 and 4 as `OVERDUE`. The closing sentence says "Ticket 4 is overdue and is listed … after the tickets that are not overdue", yet ticket 1, which is overdue, is listed first. The paragraph just above says a script can count overdue tickets by counting `OVERDUE` lines, and by that rule the example gives 2, not 1. Whatever the author meant, a test or implementation built from this example gets the wrong answer.
  Evidence: the cli.md diff, lines `#1 [P1] OVERDUE  Printer on fire` and `#4 [P2] OVERDUE  Reset the badge printer`, against "when only ticket 1 is overdue" and "after the tickets that are not overdue". The rest of the paragraph, "the order stays the ID order of TKT-013, so an overdue ticket does not move", also contradicts that last sentence.

- Severity: Major
  Where: cli.md, CLI-006, and the matching open question in tickets.md
  What: The design drops the ticket state (`open` or `assigned`) from the list line for overdue tickets. Overdue tickets are the ones agents most need to triage, and no command shows whether they have an owner. `ticketdesk list` output is a user-facing format that scripts may parse. The spec admits that a script filtering on `open` or `assigned` "misses every overdue ticket". The Goals section's "sees no change for a ticket that is not overdue" hides this break for the overdue ones. The author listed the alternative of keeping the state and adding a marker, but made the destructive option the default. Appending a column leaves old scripts that match the state field working.
  Evidence: CLI-006 says "shows `OVERDUE` in place of the state". The open question says "neither `list` nor `overdue` shows whether an overdue ticket is assigned". The code prints `{t.state:<8}` at `ticketdesk/cli.py` line 26.

- Severity: Major
  Where: cli.md, CLI-001 and CLI-006 (and the intro of tickets.md)
  What: The unbuilt, unsigned behaviour is written into the existing normative items as plain fact, for example "takes one of five subcommands". Only the note at the top of cli.md and the Overdue section in tickets.md mark it as a draft. Someone reading CLI-001 on its own is told the code does something it does not do. The intro paragraph of tickets.md ("A ticket whose due time has passed is overdue until it is closed") has the same problem. AGENTS.md says docs changes need user confirmation and that conflicts with the code must be surfaced. The `README` and `AGENTS.md` edits do flag the draft, but the edits inside CLI-001 and CLI-006 do not.
  Evidence: `ticketdesk/cli.py` defines four subparsers (`create`, `assign`, `close`, `list`) and no `overdue`. The cli.md diff changes CLI-001 to five subcommands with no inline marker.

- Severity: Minor
  Where: tickets.md, TKT-014, "The current time is the time at which the command runs … A test can fix it"
  What: The spec does not say where the current time comes from or how a test fixes it. The project's own rule (INV-005) takes time from the store's clock, and `TicketService` has no clock of its own, only `store.clock`. Without a named source, the implementation may read `time.time()` directly and the "a test can fix it" claim fails. The spec also does not say that the same clock must be used for `created`'s `at` and for "now".
  Evidence: `ticketdesk/store.py` line 14 (`clock=time.time`), `ticketdesk/tickets.py` (the service holds only `self.store`), and INV-005 in invariants.md.

- Severity: Minor
  Where: tickets.md, TKT-015 and the first open question
  What: The request says tickets that "pass their due time" show as `OVERDUE`. It does not say whether a ticket closed late counts. The spec decides this itself (closed is never overdue) and also lists it as a TODO, so the assumption is flagged. Because lateness is neither recorded nor shown, the spec cannot answer "which tickets were closed late". Nothing in the request forbids that, so it is a scope decision the user should see.
  Evidence: the Non-goals bullet "After a late ticket is closed, nothing shows that it was late."

- Severity: Minor
  Where: tickets.md, TKT-017
  What: The spec says that when the log file does not exist, neither listing creates it. That is true today, since `replay` only reads. But it adds a new guarantee beyond the existing LOG-001/LOG-006 and needs a test. The spec does not mention that the CLI has no tests (AGENTS.md "Not covered by tests: the CLI"). Every CLI-006, CLI-010 and CLI-011 criterion therefore needs a new CLI test harness, which is hidden cost for the planner.
  Evidence: AGENTS.md "Current state: Not covered by tests: the CLI". `ticketdesk/store.py` `replay` returns `[]` if the path is missing.

- Severity: Minor
  Where: cli.md, CLI-010 and CLI-012
  What: These items depend on the open CLI-007 TODO. A traceback with exit code 1 on a corrupt log is presented as the contract for `overdue` ("applies to `overdue` in the same way"). The spec never says whether this must change when CLI-007 is resolved.
  Evidence: the CLI-007 TODO text in cli.md and the CLI-012 diff.

Checked and found correct:
- TKT-014 example: 5 hours after creation, P1 (4h) is overdue and P2 (24h) is not.
- TKT-019 examples: P3 created 73h ago is due 1h ago, P1 created 10h ago is due 6h ago, so ticket 2 comes first. The equal-due-time example (P1 and P2 created 20h apart) is right.
- TKT-005 hours match `SLA_HOURS`.
- `OVERDUE` is 7 characters, so padding to 8 gives the two spaces shown in the example.
- argparse rejects `list extra` with exit code 2, and `-h` exits with code 0.
- The LOG, INV and TKT cross-references resolve.

PARAPHRASE

What the document proposes: `ticketdesk list` would show `OVERDUE` instead of the state for any open or assigned ticket whose due time has passed, keeping ID order. A new `ticketdesk overdue` command would print only those tickets, using the same line format, sorted by due time (ties broken by ID). "Overdue" would be computed fresh from the log and the current time on every run, never stored, never alerted, and never shown for closed tickets. The document labels all of this a draft awaiting sign-off, with a list of unconfirmed assumptions.

How the existing system works, according to the document alone: tickets move from open to assigned to closed. The due time is the creation time plus 4, 24 or 72 hours by priority. State is rebuilt by replaying an append-only log of created, assigned and closed events. `list` prints every ticket in ID order as `#id [prio] state title`. A corrupt log line stops every command, but today that surfaces as a traceback with exit code 1 (the CLI-007 TODO). Ticket-rule errors print `error:` and exit with code 2.

I could not paraphrase the CLI-006 example. It contradicts its own lead-in and closing sentence (see the Blocker).
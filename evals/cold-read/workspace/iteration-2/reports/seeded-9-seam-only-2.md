FINDINGS

- Severity: Blocker
  Where: tickets.md, TKT-019, the worked example ("ticket 1 has priority `P3` and was created 80 hours ago…")
  What: The arithmetic is wrong, and so is the ordering it concludes. A P3 ticket created 80 hours ago was due 80−72 = 8 hours ago, not 1 hour ago. Ticket 1 (due 8 hours ago) is due earlier than ticket 2 (due 6 hours ago), so ticket 1 comes first. The document says ticket 2 comes first.
  Evidence: TKT-005 gives P3 = 72 hours and P1 = 4 hours. The example says "Ticket 2 was due 6 hours ago and ticket 1 was due 1 hour ago, so ticket 2 comes first." That contradicts the rule stated just above it, "sorted by due time ascending". A tester who builds this example will fail a correct implementation.

- Severity: Blocker
  Where: cli.md, CLI-012 (and the "damaged log" row of the status note)
  What: `overdue` skips unreadable log lines and exits 0. That directly breaks INV-004, "No corrupt line is skipped and no partial state is returned", and LOG-007, "A line that is not valid JSON stops every operation with an error." The AGENTS.md rule says invariant breaks need explicit user confirmation. The document neither flags this as a conflict nor lists it in the open questions. It also leaves `list` fail-fast on the same log, so the two commands disagree about the same file.
  Evidence: invariants.md INV-004. `store.py` raises `ValueError` on a bad line, and `replay()` is the only reader. Skipping a `created` line would also make later `assigned` or `closed` events hit `tickets[ev["id"]]` and raise `KeyError`. A partial replay is therefore not just a policy change but a new code path. CLI-007's TODO already records that the corrupt-log exit code is unresolved.

- Severity: Major
  Where: cli.md, CLI-006 ("`list` prints the overdue tickets first… and then the other tickets")
  What: This reorders `list` and contradicts TKT-013, "sorted by ID ascending". TKT-013 is not amended and the reorder is not in the open questions. It also contradicts the goal "A person or a script that reads the ticket list sees no change for a ticket that is not overdue", and the Non-goals' "`list` gets no filter option and no sort option". The request asked only to show OVERDUE in `list`, not to reorder it.
  Evidence: tickets.md TKT-013 versus cli.md CLI-006. The CLI-006 example shows IDs 1, 2, 3 in order, so it hides the effect. With ticket 1 not overdue and ticket 3 overdue, the output would be 3, 1, 2.

- Severity: Major
  Where: cli.md, CLI-010 ("for example `ticketdesk overdue --log desk.jsonl`") and CLI-011
  What: `--log` is an option of the top-level parser. It only works before the subcommand, and today it is rejected after any subcommand. CLI-010's example fails with exit 2. CLI-011 says `overdue` takes "no option of its own after the command name", which reads as if `--log` after the name were fine. The document never states the position of `--log`, and CLI-002 does not either.
  Evidence: I ran `python3 -m ticketdesk.cli list --log t.jsonl`. Output: `ticketdesk: error: unrecognized arguments: --log t.jsonl`, rc=2. The same call with `--log t.jsonl list` works. `cli.py` line 12 defines `--log` on the main parser.

- Severity: Major
  Where: cli.md, CLI-010 ("prints `no overdue tickets` to stderr, and exits with code 0")
  What: This contradicts CLI-008, "A command that succeeds exits with code 0 and writes nothing to stderr." It also breaks the project's own precedent for empty results. `list` with no tickets prints nothing, and LOG-006 says "Listing shows nothing." The document adds a stderr message and does not amend CLI-008. It does list the choice as an open question, but not the conflict with CLI-008.
  Evidence: cli.md CLI-008 and CLI-006 ("With no tickets it prints nothing") versus CLI-010.

- Severity: Major
  Where: tickets.md, TKT-019 ("The log stamps events in whole seconds")
  What: The statement about today's system is false. Timestamps are floats with sub-second precision. LOG-004 says "seconds since the Unix epoch", and architecture.md says "Timestamps and due times are floats". The tie-break rationale rests on the false premise. Exact ties are rare, and the ID fallback is only needed for identical floats.
  Evidence: My run wrote `"at": 1793913095.059555`. `store.py` uses `time.time`. architecture.md, "Time is seconds since the epoch… floats".

- Severity: Major
  Where: cli.md CLI-006 and the open question on `OVERDUE` replacing the state
  What: Replacing the state with `OVERDUE` removes information. An overdue ticket no longer shows whether it is `open` or `assigned`. `ticketdesk list` is the only place that shows the state, so there is no other way to tell. The document does raise this as an open question. But the stated goal, "sees no change for a ticket that is not overdue", is the only one the document protects, and the cost to overdue tickets is accepted without alternatives. A column or suffix would keep the state. TKT-001 and the existing line format `#<id> [<priority>] <state> <title>` treat the state as the key field.
  Evidence: cli.py line 29 prints `{t.state:<8}`. The document's own text: "A script that selects lines by `open` or `assigned` misses every overdue ticket."

- Severity: Minor
  Where: cli.md CLI-006, "Every output line with `OVERDUE` in that position is one overdue ticket, so a script counts the overdue tickets by counting those lines"
  What: "That position" is the state column, but the format is whitespace-separated and titles are free text. A title beginning with `OVERDUE` (for example `#4 [P3] open     OVERDUE VPN`) matches a naive `grep OVERDUE` or column-based counter. The claim only holds for a parser that knows the format. The document does not give that parser rule.
  Evidence: cli.py prints the title unescaped after the state. The document itself says "A title may contain the same word."

- Severity: Minor
  Where: tickets.md TKT-014, "read from the same clock that stamps events, see LOG-004"
  What: Replay and `TicketService` do not expose "now" today. The clock is only used inside `EventStore.append`, as `self.clock`. The service layer would have to read `store.clock` or take a new clock. This touches the layer rule in architecture.md, where the store "knows nothing about tickets" and the service owns the rules. The document does not say where the time comes from, and `TicketService` tests use a fake clock. The statement is not wrong, but it is not specified for the layered design.
  Evidence: `store.py` lines 13-14 and 18. `tickets.py` has no clock.

- Severity: Minor
  Where: tickets.md TKT-017, "LOG-009 still holds"
  What: LOG-009 says replaying the same log "always yields the same tickets". TKT-017 says the same log can show a ticket as not overdue now and overdue later. The document narrows LOG-009 to "states, assignees, resolutions, and due times", but does not amend LOG-009 or INV-001's wording. A reader sees an unannotated contradiction in event-log.md.
  Evidence: event-log.md LOG-009 versus tickets.md TKT-017's last two sentences.

- Severity: Minor
  Where: cli.md CLI-011 ("The help option `-h` is outside this item"), CLI-001
  What: CLI-001 says "five subcommands", and the status note repeats that count. `-h` is untested and unspecified, and exit code 0 versus 2 is undefined. The claim that 0.3.0 rejects `list extra` the same way is true (rc=2, verified). The remaining gap is small.
  Evidence: I ran `ticketdesk --log t.jsonl list extra`. Output: `unrecognized arguments: extra`, rc=2.

Checked and found consistent: `make test` runs 7 cases and passes. TKT-014's P1/P2 example (5 hours) is correct. The claims that 0.3.0 has four subcommands and no overdue behavior are correct. The `OVERDUE` word fits the 8-character padding.

PARAPHRASE

The document proposes that a ticket not yet closed, whose creation time plus its priority's hours has passed, counts as overdue. Overdue is computed at read time and never written to the log. `ticketdesk list` would show `OVERDUE` in place of the state and put overdue tickets first. A new `ticketdesk overdue` command, with no options, would print only overdue tickets, earliest due time first, ties by ID. It would print a note on stderr when none exist, and skip unreadable log lines.

According to the document alone, the existing system has four subcommands (`create`, `assign`, `close`, `list`). Tickets have states `open`, `assigned`, and `closed`, and a due time set by priority (4, 24, or 72 hours). `list` shows every ticket in ID order, one line each with the state padded to 8 characters. The log is an append-only JSON lines file with whole-second timestamps. A corrupt line stops every operation. Success writes nothing to stderr. The `--log` option position is not described.
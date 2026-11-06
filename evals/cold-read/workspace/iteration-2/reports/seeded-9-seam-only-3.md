FINDINGS

- Severity: Blocker
  Where: tickets.md, TKT-019 example (lines 169–171)
  What: The worked example gives the wrong answer. A P3 ticket created 80 hours ago was due 8 hours ago (72h SLA), not 1 hour ago. The P1 ticket created 10 hours ago was due 6 hours ago. Ticket 1 was due earlier, so it comes first, which is the opposite of the text.
  Evidence: TKT-005 gives P3 = 72h and P1 = 4h. 80−72 = 8 and 10−4 = 6. The example says "Ticket 2 was due 6 hours ago and ticket 1 was due 1 hour ago, so ticket 2 comes first." A tester who builds this case will see the reverse order.

- Severity: Blocker
  Where: cli.md, CLI-012 (line 110ff)
  What: `overdue` skips unreadable log lines and exits 0. This contradicts INV-004 and LOG-007, which say a corrupt line stops every operation with an error and is never skipped. The AGENTS.md rules say an invariant break needs explicit user confirmation and conflicts must be surfaced. The spec doesn't list this as an open question or a conflict. It also creates a case where `list` and `overdue` disagree on the same log.
  Evidence: INV-004: "No corrupt line is skipped and no partial state is returned." LOG-007: "A line that is not valid JSON stops every operation with an error." CLI-012: "skips a log line that it cannot read and lists the overdue tickets from the other lines." The "Open questions" list has no entry for it. Skipping a line could also silently drop a `closed` event, so a closed ticket would show as overdue, or an `assigned` or `created` event, so the ticket list would be wrong. "Cannot read" is also undefined for lines that are valid JSON but missing keys. Today, replay hits `KeyError` in `tickets.py` `_tickets`.

- Severity: Major
  Where: cli.md, CLI-006 (line 53), against TKT-013 and the line 48 text
  What: The draft changes `list` order to "overdue first, then the others". The request only asked for the OVERDUE marking. TKT-013 ("sorted by ID ascending") and the opening of CLI-006 ("in ID order, see TKT-013") are both left unchanged. The spec now contradicts itself and the existing spec. The goal "no change for a ticket that is not overdue" is also false for positions. The "No sort option" non-goal and the open questions don't mention the reordering.
  Evidence: cli.md:48 "prints one line per ticket in ID order, see TKT-013". cli.md:53 "prints the overdue tickets first … and then the other tickets". tickets.md:84–86, TKT-013, is unchanged. The CLI-006 example (tickets 1, 2, 3) hides the change because the overdue ticket is also ID 1.

- Severity: Major
  Where: cli.md, CLI-010 example vs CLI-011, and CLI-002
  What: The example `ticketdesk overdue --log desk.jsonl` does not work. `--log` is a top-level option on the main parser and argparse rejects it after the subcommand. Today's `list --log X` already fails. CLI-011 also says `overdue` takes no option "after the command name", which contradicts its own CLI-010 example.
  Evidence: I ran `python3 -m ticketdesk.cli list --log $L` and got "unrecognized arguments: --log …", rc=2. cli.py:13 defines `--log` on the parent parser only. CLI-002 doesn't say where `--log` goes.

- Severity: Major
  Where: cli.md, CLI-010, against CLI-008
  What: CLI-010 requires a stderr note ("no overdue tickets") on a successful run with exit 0. CLI-008 says a successful command "writes nothing to stderr". `list` with no tickets prints nothing at all. The spec doesn't reconcile these or call it out as a conflict. The open questions only ask about exit code and the note.
  Evidence: cli.md:80 "A command that succeeds exits with code 0 and writes nothing to stderr." cli.md:99–100 "prints `no overdue tickets` to stderr, and exits with code 0." I ran `--log none list`: it prints nothing and exits 0 with no stderr.

- Severity: Major
  Where: tickets.md, TKT-019 (line 165)
  What: The claim "The log stamps events in whole seconds" is false for the code. The clock is `time.time`, which gives fractional seconds. Equal due times are therefore rare, not routine. The tie-break rationale rests on a false premise. LOG-004 only says "seconds since the Unix epoch". Equal due times can also occur across priorities, for example a P1 and a P2 created 20 hours apart, which the text doesn't say.
  Evidence: store.py:12 `clock=time.time`. A log line I created: `"at": 1793913097.121545`.

- Severity: Minor
  Where: cli.md, CLI-006 (line 58ff)
  What: "A script counts overdue tickets by counting those lines" depends on "the position of the state". A title can read `OVERDUE …` and a plain `grep OVERDUE` also matches it. The claim holds only for a positional parse, and the spec doesn't give the parse rule. The same positional rule also hides `assigned` and `open` from scripts (the spec records this as a TODO).
  Evidence: I created a ticket titled "OVERDUE x". `list` prints `#2 [P3] open     OVERDUE x`.

- Severity: Minor
  Where: cli.md, CLI-001 and CLI-006, and the status note
  What: Existing, authoritative spec items (CLI-001 "five subcommands", CLI-006) now describe behavior the product doesn't have. The patch is a draft and the notes explain this. Anyone who reads CLI-001 alone, or a tester who follows the spec, will see a false statement about the product. The process docs say not to document "a design exploration that has not landed".
  Evidence: cli.py:15–19 has 4 subparsers. The usage line reads `{create,assign,close,list}`. docs/README.md "When not to write a doc".

- Severity: Minor
  Where: tickets.md, TKT-014, "read from the same clock that stamps events, see LOG-004"
  What: LOG-004 and INV-005 describe the clock used when writing an event, and say the time "comes from the store's clock, never from the caller". Reading it for `list` and `overdue` is a new use that neither item covers. The spec doesn't say how a tester sets "now", for example by injecting the clock.
  Evidence: store.py:12–19 uses `self.clock` only in `append`. `replay` and `tickets.py` don't read the clock.

- Severity: Minor
  Where: tickets.md, TKT-017 and "Overdue is derived and never stored"
  What: LOG-009 says replay always yields the same tickets. The spec keeps LOG-009 for "states, assignees, resolutions, and due times" and excludes overdue, but doesn't change LOG-009 or INV-001. That is consistent only if a reader takes "ticket" to exclude the overdue flag. LOG-001 ("Listing tickets appends nothing") is cited. The spec doesn't mention that `list` output now depends on the wall clock.
  Evidence: event-log.md LOG-009. tickets.md:152–156.

PARAPHRASE

What the document proposes: A ticket that is not closed and whose due time has passed shows `OVERDUE` in place of its state in `ticketdesk list`. Overdue is computed at run time and never written to the log. A new `ticketdesk overdue` command prints only those tickets, using the same line format as `list`. It sorts by due time ascending and falls back to ID order for ties. When there are none it prints a note on stderr and exits 0. It skips unreadable log lines. Open questions are left as TODOs for the user.

How the existing system works, according to the document alone: ticketdesk has four commands (`create`, `assign`, `close`, `list`). Tickets move open → assigned → closed. The due time is creation time plus 4, 24 or 72 hours by priority. `list` prints every ticket in ID order. The event log is append-only, is the only source of truth, and replay fails fast on a corrupt line. Successful commands exit 0 with nothing on stderr. Rule errors exit 2 with `error: …`, except for two known tracebacks (CLI-007).
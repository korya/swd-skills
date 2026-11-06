FINDINGS

- Severity: Blocker
  Where: TKT-019, the worked example.
  What: The example gives the wrong order under the document's own rules. Ticket 1 is P3 (72 h) created 80 h ago, so it was due 8 hours ago, not "1 hour ago". Ticket 2 is P1 (4 h) created 10 h ago, so it was due 6 hours ago. Ticket 1 was due earlier, so it comes first, which is the opposite of what the example says.
  Evidence: TKT-005 gives P3 = 72 h and P1 = 4 h. 80 − 72 = 8 and 10 − 4 = 6. The example says "ticket 2 comes first".

- Severity: Blocker
  Where: CLI-010, the example `ticketdesk overdue --log desk.jsonl`.
  What: `--log` is an option of the top-level parser, so it only works before the subcommand. Placed after `overdue` it is rejected, and CLI-011 says `overdue` takes no option of its own. The example contradicts CLI-011 and does not run.
  Evidence: `cli.py:13` defines `--log` on the main parser. `python3 -m ticketdesk.cli list --log /tmp/rv.jsonl extra` gives "unrecognized arguments: extra --log /tmp/rv.jsonl", exit 2. `overdue --log …` gives "invalid choice: 'overdue'" because the subcommand does not exist yet. Even once it exists, the trailing `--log` would be rejected.

- Severity: Blocker
  Where: CLI-012, "overdue on a damaged log".
  What: The item skips unreadable log lines, which breaks INV-004 and LOG-007, and the document does not flag this as a conflict. AGENTS.md says to stop and surface a conflict with an invariant, and the open-questions list does not mention it. The skip is also unsafe. If a `created` line is skipped, a later `assigned` or `closed` event for that id hits a `KeyError` in replay (`tickets.py:34-39`), so "lists the overdue tickets from the other lines" is not achievable as written. A skipped `closed` line would show a closed ticket as overdue. "A line that it cannot read" is also undefined, because bad JSON, a missing field, and an unknown priority all fail differently.
  Evidence: INV-004: "No corrupt line is skipped and no partial state is returned." LOG-007: "stops every operation with an error". `store.py:12` says "rather than being skipped". CLI-007 TODO says a corrupt line currently escapes as a traceback with exit 1, and CLI-012 does not mention that.

- Severity: Major
  Where: CLI-006 addition ("`list` prints the overdue tickets first…") and the Goals bullet "sees no change for a ticket that is not overdue".
  What: The request only asks for tickets to *show* as OVERDUE in `list`. The draft also reorders `list`. This contradicts CLI-006 ("in ID order") and TKT-013 ("sorted by ID ascending"), and neither is amended. It also breaks the document's own goal and the "no sort option" non-goal for `list`. A non-overdue ticket's line stays the same, but its position moves. The open-questions list does not mention the reorder.
  Evidence: `cli.md` CLI-006 first paragraph, "one line per ticket in ID order, see TKT-013", against the new paragraph below it. `tickets.md:84-86` is unchanged. The current code is `sorted(..., key=lambda t: t.id)` at `tickets.py:45`.

- Severity: Major
  Where: CLI-010, no-overdue case.
  What: The item prints `no overdue tickets` to stderr on a successful exit 0. CLI-008 says a successful command writes nothing to stderr. CLI-008 is not amended and the conflict is not flagged. The open question only asks whether to print a note, not whether it conflicts.
  Evidence: CLI-008: "A command that succeeds exits with code 0 and writes nothing to stderr." CLI-010: "prints `no overdue tickets` to stderr, and exits with code 0".

- Severity: Major
  Where: TKT-019, "The log stamps events in whole seconds".
  What: The claim is false, and the tie-break rationale built on it is wrong. Timestamps are fractional floats, so ties are rare. They are mostly possible only across different priorities (for example a P1 and a P2 whose creation times differ by exactly 20 h). The same-second, same-priority scenario the text describes does not occur.
  Evidence: `store.py:17` uses `self.clock()` with `clock=time.time`. A real log line: `{"at": 1793913095.10144, …}`. LOG-004 says only "seconds since the Unix epoch".

- Severity: Major
  Where: CLI-001 and the status note in `cli.md`, "ticketdesk 0.3.0 has four subcommands" and "The `overdue` subcommand is a draft".
  What: The spec file now states a five-subcommand contract for the behavior of the product, while the code has four. Unlike the other spec items, CLI-001 and CLI-006 are existing, currently-true specs that were edited in place, so they are now false for 0.3.0. The draft status of the *new* behavior therefore does not isolate it. The existing "Authoritative description of what ticketdesk does" now describes unbuilt behavior. A tester reading CLI-006 against the product sees a failure. The README rule that items are testable and cover only existing behavior is not addressed.
  Evidence: `cli.py:16-20` has four subcommands. `product-specs/README.md` line 3: "Authoritative description of what ticketdesk does."

- Severity: Minor
  Where: CLI-006 / the open question on `OVERDUE` replacing the state.
  What: The output design loses information. An overdue ticket no longer shows `open` versus `assigned`, and the list shows no due time. The document admits this in the TODO but still states the design as a rule in CLI-006 and CLI-010, so the replacement is the proposal, not an open choice. The project's other output lines never drop a state.
  Evidence: `cli.py:32`, `{t.state:<8}`. CLI-006 example. The TODO bullet 2 in tickets.md.

- Severity: Minor
  Where: CLI-006, "a script counts the overdue tickets by counting those lines".
  What: The claim holds only for a parser that reads the state field by position. A plain `grep OVERDUE` also matches titles. A title with a newline already splits a ticket across lines today, which breaks the "one line per ticket" assumption.
  Evidence: `cli.py:32` prints the title unescaped. CLI-006 text, "A title may contain the same word".

- Severity: Minor
  Where: TKT-017 and the "overdue is derived" paragraph.
  What: Overdue tickets with an unknown priority in the log raise `ValueError` in `due_at` during replay, so both `list` and `overdue` crash with a traceback. The document does not mention this, though CLI-007 flags the same family of failure as an open conflict.
  Evidence: `sla.py:6-7` raises `ValueError`. `tickets.py:30` calls it during replay. CLI-007 TODO.

- Severity: Minor
  Where: CLI-011, "ticketdesk 0.3.0 rejects `ticketdesk list extra` in the same way".
  What: This is correct and verified (exit 2, usage on stderr, nothing on stdout). It leaves out that the usage line and the error are produced by argparse, and the usage string will list five choices after the change. This is not a defect. Noted only because the claim was checked and held.
  Evidence: the run above shows exit 2 for `list extra`.

PARAPHRASE

The draft proposes that a ticket that is not closed and is past its due time, as set by priority, shows `OVERDUE` in place of its state in `ticketdesk list`. `list` would put overdue tickets first. A new `ticketdesk overdue` command, with no arguments, would print only overdue tickets, earliest due first, using the same line format. Nothing about overdue is stored in the log. The command would skip corrupt log lines and exit 0, and it would print a note on stderr when nothing is overdue.

According to the document alone, ticketdesk 0.3.0 has four subcommands (`create`, `assign`, `close`, `list`) and no overdue behavior. Ticket state is rebuilt from an append-only log, and the due time is the creation time plus 4, 24, or 72 hours by priority. `list` prints every ticket in ID order, a corrupt log line stops everything with an error, and a successful command writes nothing to stderr. I could not paraphrase the claim that "the log stamps events in whole seconds", because the document gives no definition and the code disagrees with it.
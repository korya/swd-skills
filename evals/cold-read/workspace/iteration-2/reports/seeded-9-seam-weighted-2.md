FINDINGS

- Severity: Blocker
  Where: tickets.md, TKT-019, the worked example
  What: The arithmetic is wrong, so the example gives the opposite order. Ticket 1 is `P3` (72 h) and was created 80 h ago, so it was due 8 hours ago, not 1 hour ago. Ticket 2 is `P1` (4 h) and was created 10 h ago, so it was due 6 hours ago. Ticket 1 was due earlier and comes first, but the text says ticket 2 comes first.
  Evidence: 80−72 = 8 and 10−4 = 6, which I recomputed against `ticketdesk/sla.py` (`SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`). The example is the only illustration of the ordering rule, which is the user's main requirement ("oldest due first"). Anyone building a test from it would encode the wrong order.

- Severity: Blocker
  Where: cli.md, CLI-006, "`list` prints the overdue tickets first … and then the other tickets"
  What: This contradicts the first sentence of CLI-006 ("one line per ticket in ID order, see TKT-013") and TKT-013 (sorted by ID ascending). It also contradicts the spec's own goal and non-goal: "no change for a ticket that is not overdue" and "`list` gets no sort option". The request asked only that overdue tickets "show as OVERDUE", not that `list` be reordered. Reordering changes the output for every ticket that follows an overdue one.
  Evidence: CLI-006 line 1 (ID order, TKT-013) versus the added paragraph (overdue first). The `list` code is `sorted(..., key=lambda t: t.id)`. The README/spec index is not updated to say TKT-013 is amended, and the open questions do not list the reorder.

- Severity: Blocker
  Where: cli.md, CLI-012, and the status note
  What: CLI-012 ("skips a log line that it cannot read … exits with code 0") breaks INV-004 and LOG-007. Both say a corrupt line stops every operation with an error, with no skipping and no partial state. AGENTS.md says to stop and surface any conflict with an invariant, and this one is not flagged anywhere, not even in the open questions. It is also unsafe. If the skipped line is a `closed` event, the ticket shows as OVERDUE wrongly. If it is a `created` event, replay then hits a `KeyError` on the later `assigned` or `closed` events. Skipping would also require a new store path, because `replay()` in `store.py` raises `ValueError` and nothing skips lines. The request never asked for this.
  Evidence: invariants.md INV-004 ("No corrupt line is skipped and no partial state is returned"). event-log.md LOG-007 ("Lines after it are not read"). `store.py:30-34`. `tickets.py:_tickets` indexes `tickets[ev["id"]]` directly.

- Severity: Major
  Where: cli.md, CLI-006, "A `closed` or `assigned` ticket always shows its state"
  What: This contradicts TKT-016, which says an assigned ticket can be overdue and so shows `OVERDUE`. It also contradicts the first open question, which says `OVERDUE` replaces `assigned` and a script selecting `open` or `assigned` misses every overdue ticket. As written, the sentence is false. The `assigned` word should not be there.
  Evidence: CLI-006 versus TKT-016 and the second TODO in the open questions.

- Severity: Major
  Where: cli.md, CLI-010, "prints `no overdue tickets` to stderr and exits with code 0"
  What: CLI-008 says a successful command exits 0 and writes nothing to stderr. CLI-010 breaks that rule without saying so. `list` with no tickets prints nothing, so this is also inconsistent with how the project already handles an empty listing. It is listed as a TODO, but the conflict with CLI-008 is not named.
  Evidence: CLI-008 text. CLI-006 ("With no tickets it prints nothing").

- Severity: Major
  Where: cli.md, CLI-010 example and CLI-011
  What: `ticketdesk overdue --log desk.jsonl` does not work. `--log` is a top-level option, so it must come before the subcommand. The command is rejected as an unrecognized argument with exit 2. CLI-011 then says `overdue` has "no option of its own", which is true, but its "rejected with exit 2" rule would apply to the spec's own CLI-010 example. The example must be `ticketdesk --log desk.jsonl overdue`.
  Evidence: I ran `python3 -m ticketdesk.cli list --log /tmp/rv.jsonl`. It printed "unrecognized arguments: --log /tmp/rv.jsonl" and exited 2.

- Severity: Major
  Where: tickets.md, TKT-019, "The log stamps events in whole seconds"
  What: This is false. Timestamps are float seconds from `time.time()`, with microsecond precision. LOG-004 only says "seconds since the Unix epoch". Equal due times are therefore rare. The ID tie-break rule and its stated justification rest on a wrong premise. They only matter with an injected clock or a hand-edited log.
  Evidence: the log line I generated, `{"at": 1793912965.343245, ...}`. `store.py:append` uses `self.clock()`, which defaults to `time.time`.

- Severity: Major
  Where: tickets.md, TKT-014 and TKT-017 versus INV-001 and LOG-009
  What: Overdue makes the displayed state depend on wall-clock time as well as on the log. INV-001 says state is derived by replaying the log. The spec says "LOG-009 still holds", but the same log now prints different output on different days. The spec acknowledges "derived, never stored", but does not flag the tension with INV-001/LOG-009 as a conflict to confirm. Nothing says how a test controls the clock. `TicketService` has no clock of its own, and the store's clock is only for stamping.
  Evidence: LOG-009 and INV-001 versus TKT-017 ("can show a ticket as not overdue now and as overdue later"). In `tickets.py` the service has no access to the clock except through `store.clock`.

- Severity: Major
  Where: cli.md, CLI-006, claim "a script counts the overdue tickets by counting those lines"
  What: The `list` format has no field delimiter, and the title is free text. Position-based matching of `OVERDUE` is fragile. The claim also overlooks that `list` output now loses information (open versus assigned). The `overdue` command is the only filtered view, and neither command shows the assignee. This is a compatibility break for existing scripts, and the goal "no change for scripts" is only true for tickets that are not overdue.
  Evidence: the `list` format string in `cli.py`, `f"#{t.id} [{t.priority}] {t.state:<8} {t.title}"`. The goals list in tickets.md.

- Severity: Minor
  Where: tickets.md, TKT-014, the exact-due-time boundary
  What: The boundary is "not overdue at exactly the due time", and it is also in the open questions. With float timestamps it can almost never occur, so the boundary rule is untestable except with an injected clock. The spec should say how a test sets the time.
  Evidence: `time.time()` floats; no clock input exists at the CLI.

- Severity: Minor
  Where: tickets.md, status block and non-goals
  What: The "no alert" and "no record" non-goals are consistent. But the request ("show as OVERDUE") does not say whether `overdue` should show the due time. The non-goal "no display of due time" means the order of `overdue` cannot be checked from its output. This is raised as a TODO, but the TODO list is missing items. The reorder in `list` is absent (see above). The skip-corrupt-line decision is absent. The "no stderr" conflict is absent.
  Evidence: the "Open questions" list has 7 items; none covers CLI-012 or the CLI-006 reorder.

- Severity: Minor
  Where: cli.md, CLI-001 and the status note
  What: The text says "ticketdesk 0.3.0 has four subcommands" and describes `overdue` as a draft inside the same CLI-001 item. A single item now holds both the current and the future behavior. That is a style call, but when a plan cites CLI-001 it is unclear which rule applies. (`-h` is also declared outside CLI-011, though it is how argparse behaves.)
  Evidence: the CLI-001 text.

- Severity: Minor
  Where: AGENTS.md and the product-specs README (diffs)
  What: Both are edited to describe a draft that has not been signed off. AGENTS.md says doc changes need user confirmation, so those edits should be confirmed along with the spec. Also, AGENTS.md still says "make test # 7 unittest cases" and states there are no tests for the CLI. Several new rules (CLI-010 to CLI-012) are CLI-only, so there is no test location.
  Evidence: `git diff AGENTS.md`.

PARAPHRASE

The document proposes that a ticket that is not closed and is past its due time (creation plus the priority hours) shows `OVERDUE` in place of its state in `ticketdesk list`. It adds a `ticketdesk overdue` command that prints only those tickets, with the earliest due time first and ties broken by ID. Overdue is computed from the current time on each run and never written to the log. The document also asks for a few related behaviors: `list` puts overdue tickets first, `overdue` prints a note on stderr when empty, and `overdue` skips corrupt log lines.

By the document alone, the current system has four commands (`create`, `assign`, `close`, `list`). Tickets are rebuilt by replaying an append-only log, and `list` prints them in ID order with state padded to 8 characters. Due time is creation time plus 4, 24, or 72 hours. Stamps come from a store clock in seconds. Corrupt lines stop replay. The document's claim that the stamps are whole seconds is wrong (see the findings). The document also treats the `--log` option as usable after the subcommand, which the code rejects.
FINDINGS

- **Severity:** Blocker
  **Where:** tickets.md, TKT-019, the worked example
  **What:** The example reaches the wrong answer. Ticket 1 (`P3`, created 80 h ago) was due 8 hours ago, not 1 hour ago. Ticket 1 was due earlier than ticket 2, so ticket 1 comes first. The example puts ticket 2 first and so contradicts the rule it illustrates.
  **Evidence:** `SLA_HOURS["P3"]` is 72 (`ticketdesk/sla.py:3`), and 80 − 72 = 8. Ticket 2 is `P1` (4 h) created 10 h ago, so it was due 6 h ago, which is later than 8 h ago. The doc says "due 1 hour ago".

- **Severity:** Blocker
  **Where:** cli.md, CLI-012 (and the CLI-012 line in AGENTS.md "Specified, not built")
  **What:** The `overdue` command would skip unreadable log lines and exit 0. This directly breaks INV-004 and LOG-007, which say a corrupt line stops every operation with an error and is never skipped. The doc doesn't flag it as a conflict or list it under open questions. AGENTS.md says anything that breaks an invariant needs explicit user confirmation and that conflicts must be surfaced.
  **Evidence:**
  - INV-004: "No corrupt line is skipped and no partial state is returned."
  - LOG-007: "A line that is not valid JSON stops every operation with an error."
  - `store.py:34-35` raises `ValueError`.
  - CLI-012: "skips a log line that it cannot read and lists the overdue tickets from the other lines".
  - A partial replay can also produce wrong tickets. If a skipped line is a `closed` event, a closed ticket shows as overdue.

- **Severity:** Major
  **Where:** cli.md, CLI-006, "`list` prints the overdue tickets first"
  **What:** This changes the order of `list`, and the request never asked for that. It contradicts CLI-006's first sentence ("in ID order, see TKT-013") and TKT-013 itself, which are not amended. It also contradicts goal 3 ("no change for a ticket that is not overdue") and the "No options"/sort non-goal. It isn't in the open questions. The example shows only ID order, so it doesn't show the reorder.
  **Evidence:** The request says only that overdue tickets "show as OVERDUE in `ticketdesk list`". TKT-013 says "sorted by ID ascending". `tickets.py:47` sorts by id.

- **Severity:** Major
  **Where:** cli.md, CLI-010, "for example `ticketdesk overdue --log desk.jsonl`"
  **What:** The example command fails with the current parser. `--log` is defined on the top-level parser only, so it must come before the subcommand. The example also contradicts CLI-011, which says `overdue` takes no option after its name.
  **Evidence:** I ran `python3 -m ticketdesk.cli list --log /tmp/x.jsonl`. It printed `unrecognized arguments: --log /tmp/x.jsonl` and exited 2. CLI-011 says "no argument and no option of its own after the command name".

- **Severity:** Major
  **Where:** cli.md, CLI-010 (empty result prints a note to stderr, exit 0)
  **What:** This conflicts with CLI-008, which the document doesn't mention. CLI-008 says a successful command writes nothing to stderr. The open-questions list covers the choice but not the conflict with CLI-008.
  **Evidence:** CLI-008: "A command that succeeds exits with code 0 and writes nothing to stderr." CLI-010: "prints `no overdue tickets` to stderr, and exits with code 0".

- **Severity:** Minor
  **Where:** tickets.md, TKT-019, "The log stamps events in whole seconds"
  **What:** The claim is false. The clock is `time.time`, which returns a float, and the tie reasoning built on it is wrong. Equal due times are still possible but much rarer. The ID tie-break is still reasonable.
  **Evidence:** `store.py:14` has `clock=time.time`. I ran it and got `1793912966.392452`. LOG-004 says "seconds since the Unix epoch", not whole seconds.

- **Severity:** Minor
  **Where:** tickets.md intro (line 5), outside the draft section
  **What:** The unmarked intro text states "A ticket whose due time has passed is overdue until it is closed" as current fact. The draft status and the "not built" warning appear only further down. A reader of the intro could assume the behavior exists.
  **Evidence:** The `git diff` shows this sentence added to the opening paragraph. 0.3.0 has no overdue behavior.

- **Severity:** Minor
  **Where:** cli.md, CLI-006 (a "script counts the overdue tickets by counting those lines")
  **What:** The script-friendliness claim rests on a state replacement the doc itself questions. An overdue ticket no longer shows `open` or `assigned`, so the existing `assigned` information is lost from both commands. This is acknowledged in the open questions. However, the chosen design isn't compared against the alternative of keeping the state and adding a marker.
  **Evidence:** The open-questions bullet: "A script that selects lines by `open` or `assigned` misses every overdue ticket."

- **Severity:** Minor
  **Where:** Missing from the draft
  **What:** The draft says nothing about a few things:
  - **Bad priority in a log.** `due_at` raises `ValueError` for an unknown priority (`sla.py:8`). Every replay would then traceback, `overdue` and the new `list` path included. This falls under the CLI-007 TODO, but the draft doesn't connect it.
  - **Missing or changeable clock.** It doesn't say how the "current time" is injected for tests. `EventStore` has a `clock`, but `TicketService` has no access to it, and the CLI has no tests.
  - **Test coverage.** There is no note on testing CLI behavior, although AGENTS.md says to test 100% of code.
  **Evidence:** `tickets.py:36` and `sla.py:8`; AGENTS.md "Not covered by tests: the CLI."

I checked these and found no problem: the TKT-014 example (5 h after creation, `P1` is overdue and `P2` is not), the column padding in the CLI-006 example, and the `list extra` claim in CLI-011. Lint and tests pass (7 tests).

PARAPHRASE

**What the document proposes.** Tickets that are not closed and are past their due time (creation time plus the priority's SLA hours) would show `OVERDUE` in place of their state in `list`, and `list` would put them first. A new `ticketdesk overdue` command would print only those tickets, earliest due first, with ties broken by ID. Overdue is computed from the log and the current time each run and is never stored. The command takes no arguments, prints a note to stderr when nothing is overdue, and tolerates damaged log lines. Several choices are marked as unconfirmed assumptions.

**How the system works today, per the document.** Tickets are rebuilt by replaying an append-only JSON lines log. Their states go open → assigned → closed. The due time is the creation time plus 4, 24, or 72 hours for `P1`, `P2`, or `P3`. The CLI has four subcommands. `list` prints every ticket in ID order as `#id [priority] state title`. A corrupt log line stops everything with an error. There is one known conflict (CLI-007): bad priorities and corrupt lines escape as tracebacks.
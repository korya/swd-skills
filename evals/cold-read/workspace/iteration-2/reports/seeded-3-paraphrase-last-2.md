FINDINGS

- **Severity:** Major
  **Where:** cli.md CLI-006, second paragraph ("A `closed` or `assigned` ticket always shows its state"), against tickets.md TKT-016 and the "Overdue tickets" intro.
  **What:** The spec contradicts itself. CLI-006 says an `assigned` ticket always shows its state. But `OVERDUE` replaces the state for any non-closed overdue ticket, and TKT-016 says an assigned overdue ticket stays overdue. So an overdue assigned ticket must print `OVERDUE`, not `assigned`. The sentence also contradicts the opening of the same paragraph, "`OVERDUE` in place of the state". An implementer or tester gets two opposite answers for the same ticket.
  **Evidence:** cli.md:56-57 ("A `closed` or `assigned` ticket always shows its state") against tickets.md TKT-016 ("Assigning an overdue ticket leaves it overdue") and cli.md:52 ("shows `OVERDUE` in place of the state"). The example at cli.md:62-66 only shows an assigned ticket that is not overdue, so it hides the conflict.

- **Severity:** Major
  **Where:** cli.md CLI-006 and tickets.md TKT-014; the open question "confirm that `OVERDUE` takes the place of the state".
  **What:** Replacing the state column removes information and can break existing scripts, and the document does not compare it with alternatives. An overdue ticket no longer shows whether it is `open` or `assigned`. Any script that selects `open` or `assigned` lines silently misses every overdue ticket. That contradicts the stated goal that scripts see no change, because the goal is scoped to tickets that are not overdue. The request said to "show as OVERDUE", which a marker beside the state would also satisfy (for example an extra column or suffix). The draft names the cost in a TODO but never weighs the alternative. This is a design choice for the user to decide, not a settled one.
  **Evidence:** tickets.md "Open questions", second bullet. Current format: ticketdesk/cli.py:30, `f"#{t.id} [{t.priority}] {t.state:<8} {t.title}"`.

- **Severity:** Major
  **Where:** The "Overdue is derived and never stored" paragraph, TKT-017 ("LOG-009 still holds…"), and the Goals.
  **What:** The spec makes output depend on the wall clock at run time, and the "overdue" claims around that are loose. Two runs over the same log can print different `list` lines, which sits uneasily with INV-001 and LOG-009 (replay is deterministic). The document notes that "the same log can show a ticket as not overdue now and as overdue later". It then lists only "states, assignees, resolutions, and due times" as deterministic, and that list leaves out the state shown by `list`. It also says the state of an overdue ticket "is still `open` or `assigned`", while the CLI prints `OVERDUE` in that column, so "state" means two things. The spec does not say where "now" comes from. The service has no clock, and only `EventStore.clock` exists. The CLI builds `EventStore(args.log)` with the default clock and cannot inject one. So CLI-level acceptance of TKT-014 can only be tested by hand-crafting old timestamps in a log file.
  **Evidence:** ticketdesk/cli.py:20 and ticketdesk/store.py:14. Architecture.md says the clock is injectable "to keep tests deterministic" in the store only. The doc cites LOG-004, which defines `at` for events, not a read-time clock.

- **Severity:** Major
  **Where:** cli.md CLI-001 and CLI-006, the normative text.
  **What:** Present-tense normative text now describes behavior that does not exist. CLI-001 says the command takes "five subcommands". The product-specs README defines specs as the "authoritative description of what ticketdesk does". A tester reading CLI-001 today would file a failure. The caveats ("draft, not built") are inlined into the requirement text and restated in four places, which makes the items hard to test.
  **Evidence:** cli.md:20-23. Today's parser, ticketdesk/cli.py:14-18, has four subcommands, and the usage message reads `{create,assign,close,list}`.

- **Severity:** Minor
  **Where:** TKT-015, and the question "a ticket closed late never shows as late".
  **What:** The spec does not discuss the behavior it adopts, which may not match what support agents want. A ticket closed after its due time is indistinguishable afterwards from one closed on time. The Non-goals admit this ("nothing shows that it was late"). The request only says tickets "that pass their due time" show as OVERDUE. It does not say what happens to them once closed. This is correctly listed as unconfirmed, but it is a real fork in scope.
  **Evidence:** tickets.md "No record of lateness" and TKT-015.

- **Severity:** Minor
  **Where:** cli.md CLI-006, "a script counts the overdue tickets by counting those lines".
  **What:** The claim overstates reliability. A title can contain a newline, because argparse accepts any string. A title line could then begin with `#9 [P1] OVERDUE `, or the word could appear in the state position through a continuation line. The "in that position" rule is only unambiguous on single-line titles. The same weakness exists today, but the spec now builds a counting guarantee on it.
  **Evidence:** ticketdesk/cli.py:15 and tickets.py:56 reject only empty titles, not multi-line ones.

- **Severity:** Minor
  **Where:** The edited AGENTS.md "Current state" and "Documents at a glance", and the product-specs README index.
  **What:** The diff edits AGENTS.md and the README index, which the request did not ask for. AGENTS.md requires user confirmation for doc changes ("Do not silently rewrite specs or architecture"). The edits are small and flagged as draft, but they are not mentioned in the status note of either reviewed file.
  **Evidence:** `git diff` of AGENTS.md (the Specified, not built bullet and the index row) and docs/product-specs/README.md.

- **Severity:** Minor
  **Where:** The Goals, Non-goals, and Open questions sections of tickets.md.
  **What:** These headings and the draft status do not appear in the project's spec format. The README describes items as `PREFIX-NNN` entries only, with no "Testable:" appendix and no goals sections. A prose section with ID-less goals and TODOs is new structure. It is probably fine for a draft, but it needs a decision on whether it stays after sign-off. The TODO list also holds eight unconfirmed assumptions, which is a lot for the author to settle before planning.
  **Evidence:** docs/product-specs/README.md, "Spec format".

- **Severity:** Minor
  **Where:** CLI-012.
  **What:** CLI-012 promises that `overdue` has the same error message and exit code as `list` on a broken log, and today that holds only by accident. It is untestable until the CLI-007 TODO is settled. Today the failure is a traceback with exit 1. Another failure path exists that the spec does not name: an event that refers to an unknown ticket id raises `KeyError` in replay, which the "Events are trusted" assumption also covers. "A log that stops list with an error" does cover it, so this is a minor gap.
  **Evidence:** I ran `list` on a log with a corrupt line. It printed a `ValueError` traceback and exited with code 1. tickets.py:39 and :42 index `tickets[ev["id"]]` without a guard.

**Verified correct.**
- **Examples:** the TKT-014 example is right. P1 is due at 4h, so it is overdue at 5h, and P2 is due at 24h, so it is not. The TKT-019 example is right: ticket 1 (P3, 73h old) was due 1h ago, ticket 2 (P1, 10h old) was due 6h ago, so ticket 2 comes first.
- **Formatting:** the CLI-006 example padding matches `{state:<8}` plus one space, and `OVERDUE` is 7 characters.
- **Current behavior:** `ticketdesk list extra` exits 2 with a usage error, as CLI-011 claims. The missing-file claim holds because `replay()` returns `[]` and nothing is written. The `--log` option is only accepted before the subcommand, which is consistent with "no option of its own".
- **Tests:** I did not run `make test`. Nothing in the draft changes code, and no tests exist for overdue.

PARAPHRASE

**What the document proposes.** `ticketdesk list` would print the word `OVERDUE` instead of the state for any ticket that is not closed and whose due time has passed. A new `ticketdesk overdue` command would print only those tickets, using the same line format, with the earliest due time first. Ties break by ID. Overdue is computed from the log and the current time, and it is never written to the log, so nothing is recorded, alerted, or shown beyond the marker. Eight unconfirmed assumptions are left as TODOs for the user.

**How the existing system works, according to the document alone.**
- Tickets move from `open` to `assigned` to `closed`, or straight from `open` to `closed`. They never reopen.
- Each ticket has a priority (P1, P2 or P3) that sets a due time of 4, 24 or 72 hours after creation.
- Every change is one appended event in a JSON lines log. State is rebuilt by replaying the log, so the log is the single source of truth.
- The CLI has four subcommands: `create`, `assign`, `close`, `list`. `list` shows every ticket in ID order, and rule errors exit with code 2.
- A corrupt log or an unknown priority currently escapes as a traceback with exit 1. The CLI-007 TODO tracks this.

I could not paraphrase one part: what a ticket's "state" means in the proposed output. The document uses "state" for the stored value (`open` or `assigned`) and for the printed column, which shows `OVERDUE`. Which meaning each passage intends is exactly what the first two findings are about.
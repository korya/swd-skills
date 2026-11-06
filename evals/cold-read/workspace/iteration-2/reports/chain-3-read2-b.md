FINDINGS

- Severity: Blocker
  Where: cli.md, CLI-006, second paragraph, "A `closed` or `assigned` ticket always shows its state."
  What: This sentence contradicts the rule above it and the rest of the draft. An `assigned` ticket can be overdue, and the draft says so itself. When it is overdue, `list` must show `OVERDUE` in place of the state. An implementer or tester gets two incompatible instructions for the same ticket.
  Evidence:
  - CLI-006, first paragraph: "the line shows `OVERDUE` in place of the state".
  - TKT-016: "Assigning an overdue ticket leaves it overdue."
  - The open question in tickets.md: "A script that selects lines by `open` or `assigned` misses every overdue ticket."
  - The sentence is true only for `closed`, which TKT-015 covers. It should say "a `closed` ticket always shows its state."

- Severity: Major
  Where: tickets.md, TKT-014, TKT-019, CLI-006, CLI-010, and the open-questions item about CLI tests. The last one does not mention the clock.
  What: The spec makes overdue depend on the wall clock at the moment a command runs. It does not say how an overdue-dependent test can control that clock. The CLI builds `EventStore(args.log)` with the default `time.time` and has no hook to inject a clock. So a CLI test, or an end-to-end test of CLI-006 or CLI-010, cannot make a ticket overdue without sleeping or hand-writing old `at` values into the log. The spec format requires "deterministic" behavior that a tester can verify. The open question only asks whether CLI tests are in scope. It never says the time source must be controllable.
  Evidence:
  - cli.py line `svc = TicketService(EventStore(args.log))`.
  - architecture.md: the injectable clock sits in the store only, and `tests/test_tickets.py` uses a fake clock.
  - The spec also never says whether the time is read once per command or once per ticket. If it is read per ticket, one `list` could classify tickets at slightly different instants.

- Severity: Major
  Where: tickets.md, TKT-017, "LOG-009 still holds", and the architecture implication.
  What: The spec leaves open where "now" comes from. TKT-014 says it is read "from the same clock that stamps events". That clock is owned by the store, and the service currently only replays events. The draft does not flag that this adds a new service-to-store access, or that it may need an `architecture.md` change. guidelines.md names layer crossings as needing review before building. The draft also does not list `architecture.md` among the docs that will need updating. This will surface at planning and cost rework.
  Evidence: architecture.md says "Time is seconds since the epoch… from the store's clock". The service "asks the store for the event list" only. tickets.py has no access to the clock except via `store.clock`.

- Severity: Major
  Where: CLI-006 and the first open question (OVERDUE replaces the state).
  What: The proposed design loses information and changes the output contract for existing consumers. After this change, neither `list` nor `overdue` shows whether an overdue ticket is `open` or `assigned`. `assign` still prints `#1 assigned -> dana`, and the next `list` then prints `OVERDUE` for that ticket. The author lists this as a TODO and offers an alternative, but the draft's normative text already commits to replacement. The request only asked that overdue tickets "show as OVERDUE". It did not ask for the state to be hidden. The draft should state a recommendation. The marker-after-state option keeps the data visible and keeps the 0.3.0 columns for non-overdue tickets.
  Evidence: CLI-006, TKT-016, CLI-004 (assign output unchanged by the non-goals).

- Severity: Minor
  Where: tickets.md, "Non-goals: No display of the due time" together with TKT-019.
  What: The spec requires a sort by a value that no command shows. A tester cannot confirm the order from the output alone. They would need to compute due times from the log. The author notes this in the open questions. It also makes the "oldest due first" request unobservable in practice, except by comparing against the log.
  Evidence: the non-goals versus TKT-019. The TKT-019 example works only because the creation ages are given.

- Severity: Minor
  Where: TKT-017, CLI-010, CLI-012. Each bundles several behaviors.
  What: The spec format asks for "one observable, deterministic behavior" per item.
  - TKT-017 combines: no event kinds added, the log is unchanged byte for byte, no file creation, and non-determinism over time. It also restates LOG-009.
  - CLI-010 combines: output format, log path, argument placement, empty output, and a missing log.
  - CLI-012 combines two failure causes and a deferral to the CLI-007 TODO.
  Items like these are harder to cite from tests and PRs.
  Evidence: product-specs/README.md, "Spec format"; docs/README.md, "Each spec describes one observable, deterministic behavior."

- Severity: Minor
  Where: TKT-017, last sentence, "LOG-009 still holds for states, assignees, resolutions, and due times."
  What: LOG-009 says replaying the same log always yields the same tickets. The draft now makes the displayed list depend on the current time. LOG-009 is only safe if "overdue" is excluded from what replay yields. The draft says so only implicitly. LOG-001 ("Listing tickets appends nothing") is also not updated for the new listing, and `event-log.md` is not touched.
  Evidence: event-log.md LOG-001 and LOG-009, against TKT-017.

- Severity: Minor
  Where: CLI-012, "Both failures escape as tracebacks today" and "because the due time cannot be computed".
  What: The claim is accurate but misleading about what is new. An unknown priority in the log already stops `list` today. `_tickets()` calls `due_at()` on every replay, and that also breaks `assign` and `close`. So the damaged-log behavior for `list` is not a new cost of this feature. The draft presents it as a consequence of overdue.
  Evidence: tickets.py `t.due_at = due_at(ev["at"], ev["priority"])` inside `_tickets`; sla.py raises `ValueError`.

- Severity: Minor
  Where: edits to AGENTS.md and product-specs/README.md, not among the two documents named for review.
  What: Both files now carry draft status text. The same files tell agents that specs are "authoritative". Until sign-off, TKT-014 to TKT-019 and CLI-010 to CLI-012 sit in authoritative files next to built items. The status notes mitigate this, but the notes are not consistent. AGENTS.md says "TKT-014 to TKT-019 and CLI-010 to CLI-012", while CLI-001 and CLI-006 are also changed, as the cli.md note says. Under the rules, these doc changes also need the user's confirmation.
  Evidence: `git diff`; AGENTS.md "Doc changes need user confirmation."

- Severity: Minor
  Where: TKT-014, boundary example.
  What: The boundary rule is stated ("At the exact due time the ticket is not overdue yet") but no example tests it. The only example is at 5 hours for P1. The author flags the boundary as an unconfirmed assumption.
  Evidence: TKT-014; I recomputed the 5-hour case and it is correct (P1 4h < 5h is overdue, P2 24h is not).

Checked and correct:
- The TKT-019 example (80-72 = 8 hours ago against 10-4 = 6 hours ago, so ticket 1 is first).
- The CLI-006 example's column padding.
- The claim that `ticketdesk list extra` exits 2 with a usage error and nothing on stdout (run).
- The tracebacks under CLI-007.
- The "7 unittest cases" figure (7 tests ran).
- The cross-referenced ID ranges.

PARAPHRASE

What the document proposes: tickets that are not closed and are past their due time show `OVERDUE` instead of their state in `ticketdesk list`. A new `ticketdesk overdue` command prints only those tickets, using the same line format. They come ordered by due time ascending, with ties broken by ID. Overdue is computed from the log and the current time on every run. Nothing is recorded, and there are no options, alerts or due-time displays. It is a draft that waits for sign-off, and the open questions list the assumptions the user has not confirmed.

How the system works today according to the document alone: ticketdesk 0.3.0 has four subcommands, `create`, `assign`, `close` and `list`. It keeps an append-only JSON lines log. Each event gets a timestamp from the store's clock, and ticket state is rebuilt by replaying the whole log. A ticket's due time is its creation time plus 4, 24 or 72 hours for P1, P2 and P3. `list` prints every ticket by ID, with the state padded to 8 characters. Rule errors exit with code 2. A corrupt log line or an unknown priority currently escapes as a traceback, which is the open TODO under CLI-007.

I could not paraphrase one part consistently: the CLI-006 rule for how an `assigned` ticket is displayed. The two sentences say opposite things (see the Blocker).
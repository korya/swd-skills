FINDINGS

- Severity: Major
  Where: CLI-006 (the `OVERDUE`-replaces-state rule) and the first TODO in "Open questions".
  What: The spec fixes the design choice that `OVERDUE` replaces the state, though the TODO shows it is undecided and costly. An overdue ticket can no longer be told apart as `open` or `assigned`. That is the ticket an agent most needs to chase. It also changes the 0.3.0 line for exactly the tickets scripts care about. Meanwhile the Goals say scripts "see no change", which holds only for non-overdue tickets. The marker-after-state alternative is named but not specified. The user's request ("show as OVERDUE in list") doesn't force replacement.
  Evidence: cli.md CLI-006: "the line shows `OVERDUE` in place of the state". tickets.md TODO: "A script that selects lines by `open` or `assigned` misses every overdue ticket." The code prints `{t.state:<8}` at `ticketdesk/cli.py:28`.

- Severity: Major
  Where: CLI-010, TKT-019, and the non-goal "No display of the due time".
  What: The one thing the request asks `overdue` to do is order by due time, oldest first. The spec's own output hides the due time, so a user or tester can't check the order from the output. The spec admits this in a TODO and builds it in anyway. The ordering is observable only by creating tickets at known, spaced times. The CLI offers no way to control the clock.
  Evidence: tickets.md: "Then the output of `overdue` does not show why its tickets are in that order." `EventStore.clock` is injectable only in code (`ticketdesk/store.py:15`), not from the CLI.

- Severity: Minor
  Where: CLI-006, the claim "a script counts the overdue tickets by counting those lines".
  What: The claim is false when a title contains a newline. `create` only rejects an empty or whitespace title, and `list` prints the title raw. A title such as `x\n#9 [P1] OVERDUE  y` forges an extra line with `OVERDUE` in the state position. This is unaddressed, either as a limitation or as a title rule.
  Evidence: `ticketdesk/tickets.py:63` (`if not title.strip()`) and `cli.py:28` (the title is interpolated unescaped). I read the code and did not run it.

- Severity: Minor
  Where: TKT-014 ("see LOG-004").
  What: The citation is wrong. LOG-004 defines the event timestamp only and does not name a clock for "now". The "store's clock" rule is in INV-005 and architecture.md. The spec also never says who supplies "now" to the service. The service currently has no access to a clock, only the store does. "Not overdue at the exact due time" can't be tested on a float timestamp except with a fake clock.
  Evidence: event-log.md LOG-004 ("time it was appended"). architecture.md: "stamps each event with the time from an injectable clock". `TicketService` in `tickets.py` has only `self.store`.

- Severity: Minor
  Where: TKT-017 and the intro line "Overdue is derived and never stored".
  What: This introduces the first time-dependent read in a system whose rule is that state is rebuilt only from the log. The same log gives different `list` output at different times. The spec carves out LOG-009 but doesn't mention INV-001 ("derived by replaying the event log") or say whether this needs an invariant note. AGENTS.md says to surface invariant questions.
  Evidence: invariants.md INV-001. event-log.md LOG-009. tickets.md TKT-017 ("can show a ticket as not overdue now and as overdue later").

- Severity: Minor
  Where: CLI-012, "stops the command in the same way".
  What: The sentence is ambiguous about the unknown-priority case. The corrupt-line error names the file and line (LOG-007). The unknown-priority error from `due_at` names only the priority and allowed values. "The same way" can't mean the same message. It also doesn't say that `list` already fails this way today on any unknown-priority ticket, even a closed one, because `due_at` runs at replay.
  Evidence: `ticketdesk/sla.py:7` and `tickets.py:38`. store.py:32 raises a message with the path and line number.

- Severity: Minor
  Where: CLI-001 and CLI-006 (mixed built and unbuilt behavior).
  What: Authoritative items now describe 0.3.0 behavior and an unbuilt draft in the same item ("five subcommands … 0.3.0 has the other four"). A tester can't derive one verification path from the item as written. The spec format says each item is a single deterministic behavior, and "design exploration that has not landed" is listed under when not to write a doc. Anyone loading `tickets.md` or `cli.md` per AGENTS.md could build from an unsigned draft. The status notes mitigate this but don't remove it.
  Evidence: docs/README.md "Spec format requirements" and "When not to write a doc". cli.md CLI-001 diff.

- Severity: Minor
  Where: CLI-010 ("as CLI-008 requires").
  What: This overstates CLI-008. It requires exit 0 and nothing on stderr. It says nothing about printing nothing on stdout.
  Evidence: cli.md CLI-008: "A command that succeeds exits with code 0 and writes nothing to stderr."

- Severity: Minor
  Where: Missing from the spec.
  What: Nothing says where the overdue rule lives. Architecture says the CLI holds no ticket rules, so the rule must sit in the service. Nothing covers a ticket with a future creation time (clock skew), and `-h` is explicitly left out. Neither gap blocks the draft. The architecture note matters when planning.
  Evidence: architecture.md, CLI section ("It holds no ticket rules").

What checks out: all examples recompute. P1 at 5h is overdue and P2 is not. The P3 ticket created 80h ago was due 8h ago, and the P1 ticket created 10h ago was due 6h ago, so ticket 1 sorts first. The sample `list` output spacing matches the `{state:<8}` format, with `OVERDUE` at 7 characters plus one pad. The 0.3.0 claims all hold: four subcommands, `list extra` rejected with exit 2, `--log` before the subcommand, the missing log not created by a read, and tracebacks for corrupt lines and unknown priorities. `make test` passes with 7 tests. The `AGENTS.md` and `README` edits are consistent with the draft.

PARAPHRASE

**What the document proposes:** `ticketdesk list` would show the word `OVERDUE` in place of the state for any not-closed ticket whose current time is past its creation time plus the priority's hours. A new `ticketdesk overdue` command would print the same lines for only those tickets. They would be sorted by due time ascending, with ID breaking ties. Overdue is computed at read time and never written to the log. The command takes no arguments, prints nothing and exits 0 when none are overdue, and fails like every other command on a damaged log. Several choices are left as unconfirmed TODOs for the user.

**How the existing system works, per the document alone:** Tickets move from open to assigned to closed. Each has a due time of creation plus 4, 24, or 72 hours. State is rebuilt from an append-only JSON-lines log. The CLI has four subcommands. `list` prints every ticket in ID order as `#id [priority] state title`, with the state padded to 8 characters. Commands that break a ticket rule print `error:` and exit 2. A corrupt log line or an unknown priority currently escapes as a traceback, which is an open TODO.
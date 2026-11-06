FINDINGS

- Severity: Blocker
  Where: tickets.md, TKT-019, the worked example
  What: The example is wrong, and it gives the opposite order. A `P3` ticket created 80 hours ago was due 8 hours ago, not 1 hour ago (80 − 72 = 8). Ticket 1 was due before ticket 2, so ticket 1 comes first.
  Evidence: sla.py has `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`, and TKT-005 says the same. The example says "Ticket 2 was due 6 hours ago and ticket 1 was due 1 hour ago, so ticket 2 comes first." Ticket 2 (`P1`, 10 hours ago) is due 6 hours ago, which is correct. Ticket 1 was due 8 hours ago, which is earlier, so ticket 1 is first. A tester following the example would expect the wrong order. The example does not show what the rule claims, that the order follows due time and not ID or creation time. With the correct numbers, ticket 1 (oldest due) is first and also has the lowest ID, so ID order would give the same result. The example needs numbers where due order differs from ID order.

- Severity: Blocker
  Where: cli.md, CLI-012, "overdue on a damaged log"
  What: The item makes `overdue` skip corrupt log lines and exit 0. That breaks INV-004 and LOG-007, which are the floor and need explicit user confirmation to break. The open questions do not list it.
  Evidence:
  - INV-004: "No corrupt line is skipped and no partial state is returned."
  - LOG-007: "A line that is not valid JSON stops every operation with an error."
  - store.py `replay()` raises `ValueError`.
  - CLI-007 already has an open TODO about corrupt logs.
  - The rule is also unsound. Skipping a `created` line makes the later `assigned` or `closed` event for that ticket raise `KeyError` in `tickets.py:_tickets` (`tickets[ev["id"]]`). Skipping a `closed` line shows a closed ticket as overdue. The command can print wrong results.
  - The draft also ignores the layers: the store replays everything, and only the CLI-level `overdue` would skip.
  - Because `list` still fails on the same log, the two commands disagree on one input.

- Severity: Major
  Where: cli.md, CLI-006, "prints the overdue tickets first … and then the other tickets"
  What: This changes the order of `list`, which contradicts TKT-013 and CLI-006's own first sentence. It also contradicts the draft's goal that output for a ticket that is not overdue is unchanged. The request only asked for tickets to "show as OVERDUE". The reordering is not in the request and is not in the open questions. The order of the non-overdue tickets after the overdue block is not stated.
  Evidence:
  - CLI-006: "prints one line per ticket in ID order, see TKT-013".
  - TKT-013: "sorted by ID ascending".
  - The CLI-006 example shows overdue ticket 1 first, which happens to also be ID order, so it hides the conflict.
  - The tickets.md goal says "sees no change for a ticket that is not overdue".
  - TKT-013 is not amended or flagged.

- Severity: Major
  Where: cli.md, CLI-006, "A `closed` or `assigned` ticket always shows its state"
  What: This contradicts the sentence before it and TKT-014/TKT-016. An overdue `assigned` ticket shows `OVERDUE` in place of the state, and TKT-016 says assigning an overdue ticket leaves it overdue. A script that follows "an assigned ticket always shows `assigned`" breaks.
  Evidence: The same paragraph says "the line shows `OVERDUE` in place of the state". TKT-016 says "Assigning an overdue ticket leaves it overdue". The open-questions list does say a script selecting by `assigned` misses overdue tickets, which contradicts the "always" sentence. The example shows a ticket 2 that is `assigned` and not overdue, so it does not cover the conflict case.

- Severity: Major
  Where: cli.md, CLI-010, `ticketdesk overdue --log desk.jsonl`, and CLI-011
  What: The example command does not work. `--log` is an option of the top-level parser only, so it must come before the subcommand. Placed after the subcommand it is rejected. CLI-011 also says `overdue` takes no option "after the command name", which contradicts its own example in CLI-010.
  Evidence: I ran `python3 -m ticketdesk.cli list --log /tmp/rv.jsonl`. It printed `ticketdesk: error: unrecognized arguments: --log /tmp/rv.jsonl` with rc=2. cli.py defines `--log` on `parser`, not on the subparsers. The same applies to every existing example in the docs, which put `--log` first.

- Severity: Major
  Where: cli.md, CLI-010, "prints `no overdue tickets` to stderr and exits with code 0"
  What: A stderr write on success contradicts CLI-008 ("writes nothing to stderr"). No existing command prints a note on success, and the draft does not amend CLI-008. The stderr note is listed as an open question, but the clash with CLI-008 is not named.
  Evidence: CLI-008: "A command that succeeds exits with code 0 and writes nothing to stderr." `list` with no tickets prints nothing at all (CLI-006), so `list` and `overdue` would differ for the same state.

- Severity: Major
  Where: tickets.md, TKT-019, "The log stamps events in whole seconds"
  What: This is false. Timestamps are floats from `time.time()`, with sub-second precision. The tie-break by ID is rarely used, and the stated reason for it (same-second creation) is wrong. Whether the order uses the float or truncated seconds is not specified.
  Evidence: The log line I produced was `{"at": 1793912955.502018, ...}`. store.py uses `clock=time.time`. LOG-004 says "seconds since the Unix epoch", which allows fractions. A tester building a tie test cannot rely on same-second creation. Equal due times need the same priority and the same `at`, which is practically only possible with an injected clock.

- Severity: Minor
  Where: tickets.md, TKT-014, "current time … read from the same clock that stamps events, see LOG-004"
  What: LOG-004 only defines the `at` field. It does not define a clock for reading. The only clock is the `EventStore.clock` constructor argument, and cli.py never injects one. Time-dependent behavior in the CLI therefore cannot be tested without patching. The draft says nothing about a clock that runs backwards or a log with future `at` values (the ticket is simply not overdue).
  Evidence: `cli.py` builds `EventStore(args.log)` with the default clock. The AGENTS.md "Current state" says the CLI has no tests.

- Severity: Minor
  Where: tickets.md TKT-017, and the goals and non-goals, against LOG-009 and INV-001
  What: The draft derives overdue from the time of the command, so "Replaying the same log always yields the same … " no longer holds for what the user sees. TKT-017 covers this for stored fields only. INV-001 (no other file holds state) is respected. The wording should say that overdue is the one output that varies with time, not only "the same log can show … later".
  Evidence: TKT-017 last sentences; LOG-009.

- Severity: Minor
  Where: cli.md, CLI-010 / TKT-018, a log containing an unknown priority
  What: An unknown priority in a log line makes `due_at` raise `ValueError` during replay, which escapes as a traceback with exit 1 (the CLI-007 conflict). Both `list` and `overdue` are affected, and the draft does not mention it. It is the only other error path that both new behaviors share.
  Evidence: sla.py `due_at` raises `ValueError`. tickets.py `_tickets` calls it for every `created` event. cli.py catches only `TicketError`.

- Severity: Minor
  Where: cli.md, CLI-011, "ticketdesk 0.3.0 rejects `ticketdesk list extra` in the same way"
  What: The claim is correct. I ran it and got `unrecognized arguments: extra` with rc=2. `-h` is excluded, but argparse prints help and exits 0, which is not stated. The usage line printed by argparse lists the subcommands, so CLI-001 and the usage text must change together. This is a wording-level point.
  Evidence: the `list extra` run above.

- Severity: Minor
  Where: Document-wide, spec format
  What: Many "specs" are not single testable behaviors. The docs README requires that each spec describe one observable, deterministic behavior. The status paragraphs, goals, and non-goals do not follow the `PREFIX-NNN` item pattern, and TODOs sit inside the spec. TKT-019 mixes ordering, the tie-break, and an example. CLI-006 grew a multi-paragraph block with a script-counting claim, the padding rule, the order rule, and the example. Sub-cases could take letter suffixes.
  Evidence: docs/README.md "Spec format requirements"; product-specs/README.md.

PARAPHRASE

What the document proposes: A ticket that is not closed and is past its due time (creation plus 4, 24, or 72 hours by priority) counts as overdue. It is worked out each time a command runs and is never written to the log. `ticketdesk list` shows `OVERDUE` in place of the state for such tickets and puts them before the others. A new argument-less `ticketdesk overdue` prints only those tickets, due earliest first, ties by ID. With none it prints a note to stderr and exits 0. It also skips unreadable log lines. The status is a draft awaiting the user's sign-off.

How the system works today, according to the document alone: ticketdesk 0.3.0 has four subcommands (`create`, `assign`, `close`, `list`) over an append-only JSON lines log, replayed to rebuild tickets. Tickets move `open`, `assigned`, `closed`, with a due time fixed by priority. `list` prints every ticket in ID order, with the state padded to 8 characters. The CLI maps ticket-rule errors to exit 2, and a corrupt log or unknown priority escape as tracebacks (the open CLI-007 TODO). The document says nothing about how the log is replayed besides "fail-fast". Its claim that timestamps are whole seconds is not borne out by the code.
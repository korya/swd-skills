FINDINGS

- **Severity:** Blocker
  **Where:** tickets.md, TKT-019, the worked example
  **What:** The example gets the answer backwards. Ticket 1 (`P3`, created 80h ago) was due 8 hours ago, not 1 hour ago, so ticket 1 sorts first, not ticket 2. The example contradicts the rule it illustrates.
  **Evidence:** TKT-005 gives `P3` 72h, and 80 − 72 = 8h overdue. Ticket 2 (`P1`, 10h ago) was due 10 − 4 = 6h ago. The spec says "due 1 hour ago" and "ticket 2 comes first". Anyone who builds from the example gets the wrong order.

- **Severity:** Blocker
  **Where:** cli.md, CLI-012
  **What:** It says `overdue` skips unreadable log lines and exits 0. That breaks INV-004 (the "floor") and LOG-007, which say a corrupt line stops every operation with an error and nothing is skipped. AGENTS.md says an invariant break needs explicit user confirmation. The spec doesn't flag the break and doesn't list it under the open questions.
  **Evidence:** INV-004: "No corrupt line is skipped and no partial state is returned." The store docstring says "A corrupt line stops the replay with an error rather than being skipped." I appended `{bad` to a log. `list` died with `ValueError: a.jsonl:2: corrupt event`. Skipping also can't be done "from the other lines" without changing `store.replay`. A skipped `created` line would make later `assigned` or `closed` events raise `KeyError`, and could reuse IDs, against INV-003. The "damaged log" behaviour is also undefined for `list`, which would fail while `overdue` succeeds.

- **Severity:** Major
  **Where:** cli.md, CLI-006, the paragraph "For an overdue ticket… prints the overdue tickets first"
  **What:** `list` is changed to put overdue tickets first. The request only asked for them to show as OVERDUE. This overrides TKT-013 (ID ascending, every ticket), and the draft never mentions the conflict. It also undercuts the spec's own goal and non-goals: "sees no change for a ticket that is not overdue", and `list` gets no sort option. Output order is part of what a script sees. This is scope creep that no open question covers.
  **Evidence:** TKT-013: "sorted by ID ascending". The tickets.md TKT-013 text is unchanged by the diff. The example block in CLI-006 shows only one overdue ticket, so it hides the reordering.

- **Severity:** Major
  **Where:** cli.md, CLI-006: "A `closed` or `assigned` ticket always shows its state"
  **What:** This contradicts the preceding paragraph and TKT-016. TKT-016 and TKT-014 allow an `assigned` ticket to be overdue, and then it shows `OVERDUE` in place of the state. An implementer can't satisfy both sentences.
  **Evidence:** TKT-016: "Assigning an overdue ticket leaves it overdue." CLI-006: "the line shows `OVERDUE` in place of the state." The "always" sentence is only true for `closed`.

- **Severity:** Major
  **Where:** cli.md, CLI-010: `ticketdesk overdue --log desk.jsonl`
  **What:** The example doesn't work. `--log` is an option of the top-level parser. It is only accepted before the subcommand. CLI-011 also says `overdue` takes no option "of its own", which hides this. The same applies to the spec's claim that `list extra` is rejected: it is, but `list --log x` is rejected as well.
  **Evidence:** I ran `ticketdesk list --log a.jsonl` and got `error: unrecognized arguments: --log a.jsonl`, rc=2. `--log a.jsonl list extra` gives rc=2 as the spec says. The correct form is `ticketdesk --log desk.jsonl overdue`. CLI-002 doesn't say where `--log` goes.

- **Severity:** Major
  **Where:** cli.md, CLI-010 (the empty case)
  **What:** It prints `no overdue tickets` on stderr and exits 0. This contradicts CLI-008, "A command that succeeds exits with code 0 and writes nothing to stderr". `list` prints nothing when empty. The draft doesn't say it amends CLI-008 and doesn't say why `overdue` needs a note. A missing log file also gets the note, which hides a wrong `--log` path. The draft does list the stderr note as an open question, but not the CLI-008 conflict.
  **Evidence:** CLI-008 text. CLI-010: "prints `no overdue tickets` to stderr, and exits with code 0".

- **Severity:** Major
  **Where:** tickets.md, TKT-019: "The log stamps events in whole seconds"
  **What:** This is false, and the tie-break rationale rests on it. Timestamps are floats from `time.time()`, with sub-second resolution. Equal due times are possible but much rarer than described.
  **Evidence:** My log line has `"at": 1793913239.558914`. Architecture says "Timestamps and due times are floats", and LOG-004 says "seconds since the Unix epoch". It never says whole seconds. The spec also doesn't mention that the tie-break is deterministic on the float.

- **Severity:** Minor
  **Where:** tickets.md, TKT-017 and the status note: "Overdue is derived and never stored… the current time decide it"
  **What:** Several time cases are untested or unspecified: a clock that goes backwards, an event stamped in the future, and a timezone-free epoch (this one is fine). "Current time" comes from `store.clock`, but the CLI takes no `now`, so the spec doesn't say how tests fix it. Architecture says tests use a fake clock, so the spec could cite that. The paraphrase of TKT-014 "same clock that stamps events" is correct only if `list` reads `store.clock`. Today `TicketService` has no "now" accessor.
  **Evidence:** `TicketService.__init__(self, store)` only. `EventStore.clock` is attribute-only.

- **Severity:** Minor
  **Where:** TKT-017: "LOG-009 still holds for states, assignees, resolutions, and due times"
  **What:** LOG-009 says "Replaying the same log always yields the same tickets…". That's still fine for replay. But overdue is not part of it, so LOG-009 and the new "overdue changes with time" rule need an explicit scope line in event-log.md. Doc changes need user confirmation, and event-log.md is untouched.
  **Evidence:** The diff doesn't touch event-log.md.

- **Severity:** Minor
  **Where:** cli.md, CLI-006: "a script counts the overdue tickets by counting those lines"
  **What:** The title can't be confused with the state field only because of position. Counting by `grep OVERDUE` is wrong when a title contains the word, and the spec says that. A script reading `open` or `assigned` also misses overdue tickets, which the open questions do mention. The idea that a script counts overdue tickets is fragile, since the draft deliberately shows no due time and no separate flag.
  **Evidence:** `list` has no machine-readable form. The non-goals rule out JSON.

- **Severity:** Minor
  **Where:** tickets.md, CLI-006 and README, AGENTS.md summaries
  **What:** Doc text edits on AGENTS.md, README.md, and the other docs ("Specified, not built… TKT-014 to TKT-019") are made together with the draft. AGENTS.md says doc changes need user confirmation, so check these edits were approved. The "known conflicts" line in AGENTS.md also mentions only CLI-007, while the draft adds new conflicts (TKT-013, INV-004, CLI-008).
  **Evidence:** `git diff` for AGENTS.md. Process rule: "Surface conflicts."

- **Severity:** Minor
  **Where:** CLI-011
  **What:** "`-h` is outside this item" leaves the help output unspecified. The subparser for `overdue` is also missing from the existing usage line (`{create,assign,close,list}`).
  **Evidence:** I ran `list -h`: `usage: ticketdesk list [-h]`.

PARAPHRASE

The draft proposes a derived "overdue" status. An `open` or `assigned` ticket is overdue once the current time passes its creation time plus its SLA hours, and `closed` tickets never are. `ticketdesk list` would show `OVERDUE` in place of the state and move overdue tickets to the top. A new argument-less `ticketdesk overdue` command would print only those tickets, earliest due first, with ties broken by ID. Nothing is written to the log, and the spec leaves the unconfirmed choices as TODOs.

According to the document alone, the existing system is a four-command CLI (`create`, `assign`, `close`, `list`) that appends events to a JSON lines file and rebuilds every ticket by replay. Tickets move open → assigned → closed. Due time is creation time plus 4, 24, or 72 hours by priority. `list` prints tickets in ID order with a padded state. A corrupt log line stops everything with an error, except that unknown priorities and corrupt lines currently escape as tracebacks (CLI-007).
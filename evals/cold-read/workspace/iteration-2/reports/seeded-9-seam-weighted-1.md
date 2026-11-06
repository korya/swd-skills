FINDINGS

- **Severity:** Blocker
  **Where:** tickets.md, TKT-019, the worked example
  **What:** The example gets the answer backwards. Ticket 1 is `P3` (72 h) and was created 80 h ago, so it was due 8 h ago, not 1 h ago. Ticket 2 is `P1` (4 h) and was created 10 h ago, so it was due 6 h ago. Ticket 1 was due earlier, so by the rule "earliest due first" ticket 1 comes first, not ticket 2. A tester who builds the example gets the opposite of what the spec says.
  **Evidence:** TKT-005 (`P3` = 72 h, `P1` = 4 h). 80 − 72 = 8 h ago, and 10 − 4 = 6 h ago. The text says "ticket 1 was due 1 hour ago" and "ticket 2 comes first".

- **Severity:** Blocker
  **Where:** cli.md, CLI-012, with INV-004 and LOG-007
  **What:** CLI-012 makes `overdue` skip corrupt log lines and exit 0. That directly breaks INV-004 ("No corrupt line is skipped and no partial state is returned") and LOG-007 ("stops every operation with an error"). The spec doesn't flag this conflict. It isn't in the open questions, and AGENTS.md says a broken invariant needs explicit user confirmation. It also makes `overdue` and `list` disagree on the same log. And it can't work as written: skipping a `created` line makes a later `assigned` or `closed` event for that id raise `KeyError` (tickets.py:39, 42). The skipped ticket would also silently vanish from the overdue list, which is the failure the clause claims to prevent.
  **Evidence:** invariants.md:29-32, event-log.md:46-50, AGENTS.md "Doc changes need user confirmation / Surface conflicts", tickets.py:30-44. The request asked for nothing about damaged logs.

- **Severity:** Major
  **Where:** cli.md, CLI-006, the second paragraph
  **What:** "`list` prints the overdue tickets first … and then the other tickets" reorders `list`. The request only said overdue tickets should show as OVERDUE. The new rule contradicts the first sentence of CLI-006 ("in ID order, see TKT-013") and TKT-013 ("sorted by ID ascending"), and neither is amended. It also contradicts the goal "no change for a ticket that is not overdue", because non-overdue lines now move. The worked example hides the conflict, since ticket 1 is overdue and is already first.
  **Evidence:** cli.md:48 and :52-53; tickets.md:84-86 and the Goals section. Also tickets.md "No options. `list` gets no filter option and no sort option." That sentence implies the order is fixed, but the fixed order is no longer ID order. The open questions don't mention the reorder.

- **Severity:** Major
  **Where:** cli.md, CLI-010, the `--log` example, with CLI-011
  **What:** `ticketdesk overdue --log desk.jsonl` is rejected by the current parser. `--log` belongs to the top-level parser and must come before the subcommand. CLI-011 also says `overdue` takes no option of its own. The example therefore either exits 2 or implies a new per-subcommand option. CLI-002 doesn't say where `--log` goes, and the spec silently glosses over that.
  **Evidence:** cli.py:13-18. Command run: `python3 -m ticketdesk.cli list --log /tmp/rv.jsonl` gave `unrecognized arguments: --log /tmp/rv.jsonl`, rc=2. Compare the AGENTS.md usage, which puts `--log` first.

- **Severity:** Major
  **Where:** cli.md, CLI-010, empty result
  **What:** With no overdue tickets, the spec has the command print `no overdue tickets` to stderr and exit 0. CLI-008 says a command that succeeds "writes nothing to stderr". That is a direct contradiction. The spec also contradicts the way `list` handles empty results ("prints nothing").
  **Evidence:** cli.md:80-81 (CLI-008) against the CLI-010 text. The note is flagged as an open question, but CLI-008 is not named as being in conflict.

- **Severity:** Minor
  **Where:** tickets.md, TKT-019
  **What:** The claim that "the log stamps events in whole seconds" is false. `at` is a float from `time.time()`. A tie on due time needs identical float stamps, which is rare, and the tie-break rule is defended with a false premise. LOG-004 says only "seconds since the Unix epoch", which allows fractions.
  **Evidence:** store.py:14,20. The log line from my run: `"at": 1793912955.871606`.

- **Severity:** Minor
  **Where:** cli.md, CLI-011, "ticketdesk 0.3.0 rejects `ticketdesk list extra` in the same way"
  **What:** The exit code and stderr match, but the usage line shows the existing subcommand list, which the spec doesn't mention. That's fine as it stands. The related point is that CLI-001 says unknown subcommands print usage and exit 2, and that holds today. Only the claim that `-h` is "outside this item" is left undefined, so `overdue -h` behavior is unspecified.
  **Evidence:** The run `list extra` printed `unrecognized arguments`, rc=2, as claimed. The `-h` gap is the only open edge.

- **Severity:** Minor
  **Where:** cli.md, CLI-006 and CLI-010, the line format
  **What:** Replacing the state with `OVERDUE` drops whether an overdue ticket is `open` or `assigned`, and its assignee is never shown. The spec admits this in an open question. The loss is real information, though, and the request only said "show as OVERDUE". An alternative that keeps the state, such as a suffix or an extra column, isn't weighed. The 8-char padding also changes the line format only for overdue tickets, which breaks column parsing for any script that splits on spaces.
  **Evidence:** cli.md:52-55; tickets.md open questions (second bullet).

- **Severity:** Minor
  **Where:** Spec set as a whole, and AGENTS.md
  **What:** AGENTS.md still says "One is open now" for spec conflicts (CLI-007). The draft adds at least three more: CLI-012, the CLI-006 order change, and the CLI-008 note. The "TODO"s for CLI-007 (traceback on corrupt log) also bear on CLI-012 and aren't cross-referenced.
  **Evidence:** AGENTS.md "Surface conflicts" bullet; cli.md:74-76.

- **Severity:** Minor
  **Where:** tickets.md, TKT-014, "the same clock that stamps events"
  **What:** The service has no clock of its own. Only `EventStore.clock` exists, and the spec doesn't say the store clock is the one meant. For tests, "now" can only be injected through the store. The wording is fine, but it isn't observable from outside without a time-control mechanism.
  **Evidence:** store.py:14-16, tickets.py:27-28.

Checked and correct: the TKT-014 example (5 h after creation, `P1` is overdue and `P2` isn't), the ID ranges (TKT-014 to 019 and CLI-010 to 012 are unused), the claim that 0.3.0 has four subcommands, and `list extra` exiting 2.

PARAPHRASE

**What the document proposes.** A ticket that is not closed and is past its due time (creation plus the hours for its priority) counts as overdue. This is computed from the log and the current time and is never stored. `list` shows `OVERDUE` in place of the state for those tickets and puts them first. A new argument-less `ticketdesk overdue` prints only those tickets, earliest due first, ties by ID. Nothing is alerted or recorded. Reading a damaged log is meant to be tolerant for `overdue`.

**How the existing system works, according to the document alone.** `create`, `assign`, `close`, and `list` each replay the append-only JSON lines log. Each ticket is `open`, `assigned`, or `closed`, with a due time set by its priority. `list` prints every ticket in ID order. Failures print `error:` and exit 2, except unknown priority and a corrupt log, which escape as tracebacks. Success exits 0 and writes nothing to stderr. A corrupt log line stops everything. I could not paraphrase how `--log` is accepted after a subcommand, because the document doesn't say where that option goes.
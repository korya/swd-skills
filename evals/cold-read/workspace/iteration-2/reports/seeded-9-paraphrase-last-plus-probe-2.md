FINDINGS

- Severity: Blocker
  Where: `tickets.md`, TKT-019 worked example
  What: The example's numbers are wrong, so it shows the wrong order. Ticket 1 (P3, created 80 hours ago) was due 8 hours ago, not 1 hour ago. Ticket 1 was therefore due earlier than ticket 2 and comes first, which is the opposite of what the example says.
  Evidence: TKT-005 gives P3 = 72 hours, so 80 − 72 = 8 hours overdue. P1 = 4 hours, so 10 − 4 = 6 hours overdue. The text says "due 1 hour ago … ticket 2 comes first". For the example to hold, ticket 1 must be created 73 hours ago.

- Severity: Blocker
  Where: `cli.md`, CLI-012 (and the header note)
  What: CLI-012 makes `overdue` skip corrupt log lines. That contradicts INV-004 and LOG-007, which say a corrupt line stops every operation. `list` would still fail fast while `overdue` skips, and nothing in the draft flags this as a conflict or an open question. AGENTS.md says an invariant break needs explicit user confirmation.
  Evidence: INV-004: "No corrupt line is skipped and no partial state is returned." LOG-007: "stops every operation with an error." I appended `{bad` to a log and ran `list`. It died with a `ValueError` traceback and exit code 1. CLI-012 promises exit 0 instead. Skipping a `created` line would also drop a ticket, and a later `assigned` or `closed` event for it would raise `KeyError`, so "list the others" isn't well defined. TKT-017 and LOG-009 also don't account for it.

- Severity: Major
  Where: `cli.md`, CLI-006 (new paragraph), and Goal 3 in `tickets.md`
  What: `list` is changed to print overdue tickets first. That reorders the output. It contradicts TKT-013 ("sorted by ID ascending"), which the draft doesn't amend, and it contradicts the original CLI-006 text "in ID order, see TKT-013". The request only asked for the label. Goal 3 says there's "no change for a ticket that is not overdue", but every non-overdue ticket can move position. The reordering isn't in the open questions either.
  Evidence: `cli.md` CLI-006 still says "prints one line per ticket in ID order, see TKT-013", and the new text says "prints the overdue tickets first". The worked example (tickets 1, 2, 3 with only 1 overdue) happens to be in ID order, so it hides the change.

- Severity: Major
  Where: `cli.md`, CLI-010 (and the example `ticketdesk overdue --log desk.jsonl`)
  What: The example is invalid. `--log` is a top-level option and is rejected after the subcommand. CLI-011 also says `overdue` takes "no option of its own", which sits oddly with the example. A reader or a test written from the spec would fail.
  Evidence: `ticketdesk list --log X` gives `unrecognized arguments: --log X` and exit code 2. CLI-002 and the README example use `--log` before the command name.

- Severity: Major
  Where: `cli.md`, CLI-010 and the open question on the stderr note, versus CLI-008
  What: CLI-010 requires `no overdue tickets` on stderr with exit code 0. CLI-008 says a successful command "writes nothing to stderr". Neither the draft nor the open questions mention this conflict. The open question confirms the note but not the conflict with CLI-008. No existing command prints a note on success.
  Evidence: CLI-008: "A command that succeeds exits with code 0 and writes nothing to stderr." CLI-010: "prints `no overdue tickets` to stderr, and exits with code 0".

- Severity: Major
  Where: `cli.md`, CLI-006 paragraph "a script counts the overdue tickets by counting those lines"
  What: The claim is false. Titles may contain newlines, so a title can forge a line that looks like an overdue ticket.
  Evidence: `create $'x\n#9 [P1] OVERDUE  fake'` is accepted. `list` then prints `#9 [P1] OVERDUE  fake` on its own line, although only ticket 1 is open and not overdue.

- Severity: Minor
  Where: `tickets.md`, TKT-019, "The log stamps events in whole seconds"
  What: The claim is wrong. Timestamps are floats from `time.time()`. Equal due times within a priority are therefore rare, not typical. LOG-004 says only "seconds since the Unix epoch". The ID tie-break is still sensible, but the stated reason is false. Across priorities, ties are possible, for example a P1 and a P2 created 20 hours apart.
  Evidence: `{"at": 1793913249.928975, ...}` in the log I generated. `store.py:append` uses `self.clock()`.

- Severity: Minor
  Where: `tickets.md`, TKT-014 and the "not built" and "unreadable log" scope
  What: Overdue inherits two existing crash paths, and the draft doesn't mention them. An unknown priority in the log crashes replay with a `ValueError` traceback. CLI-007 documents that as an open conflict, but the overdue draft neither depends on it nor mentions it. CLI-012's "a line it cannot read" doesn't cover a readable line with a bad priority.
  Evidence: A log with `"priority":"P9"` gives `ValueError: unknown priority 'P9'` on `list`.

- Severity: Minor
  Where: TKT-014, "read from the same clock that stamps events, see LOG-004"
  What: The clock is injectable only on `EventStore`, and the CLI doesn't pass one. A planner will need a test seam for "now" that the draft doesn't mention. Clock skew (now earlier than a ticket's `at`) is also unaddressed. It is harmless but unspecified. Existing CLI tests don't exist, per AGENTS.md.
  Evidence: `cli.py` builds `EventStore(args.log)` with no clock. `store.py:16` takes `clock=time.time`.

- Severity: Minor
  Where: TKT-017, "LOG-009 still holds"
  What: The reasoning is incomplete. `list` output is now time-dependent, while LOG-009 and the AGENTS design principle describe replay as deterministic. The draft's narrower claim, that the states, assignees, resolutions and due times are the same, is true. The spec should state that CLI output is no longer a pure function of the log.
  Evidence: TKT-017: "The same log can show a ticket as not overdue now and as overdue later."

- Severity: Minor
  Where: `cli.md`, CLI-011, "rejects `ticketdesk list extra` in the same way"
  What: The claim is true (I ran it: exit code 2, `unrecognized arguments: extra`). The usage line printed comes from the top-level parser and will list `overdue` once built. No issue besides the `-h` carve-out, which is fine.
  Evidence: Output above.

- Severity: Minor
  Where: `tickets.md`, the Non-goals "No display of the due time" and the open questions
  What: `OVERDUE` replaces the state, so an agent can't tell an overdue `open` ticket from an overdue `assigned` one, and can't tell how late it is. The draft flags the first loss. Whether this still meets the request's intent ("show as OVERDUE") is the user's call, but the request does not say that `OVERDUE` should replace the state rather than be added next to it. The cost is a choice the draft makes for the user.
  Evidence: Open-questions list, second bullet.

Checked and found correct: TKT-014's example (P1 overdue after 5 hours, P2 not). The existing facts: four subcommands, 0.3.0, `{:<8}` padding, and the example's two-space alignment for `OVERDUE`. The CLI-010 to CLI-012 and TKT-014 to TKT-019 IDs don't collide with existing ones.

PARAPHRASE

What the document proposes: a ticket that isn't closed and is past its due time (creation time plus the priority's hours) shows `OVERDUE` in the state column of `ticketdesk list`. `list` puts overdue tickets first. A new `ticketdesk overdue` command prints only the overdue tickets, earliest due first, with ties broken by ID. Overdue is computed from the current time on each run and never written to the log. `overdue` prints a note to stderr and exits 0 when nothing is overdue, takes no arguments, and skips corrupt log lines.

How the existing system works according to the document alone: `ticketdesk` has four commands (create, assign, close, list). Tickets move open → assigned → closed. The log is the single source of truth, and every command rebuilds state by replaying it. A corrupt log line stops everything with an error (INV-004, LOG-007), though CLI-007 admits that today this appears as a traceback. `list` shows every ticket in ID order with its stored state, and successful commands write nothing to stderr.
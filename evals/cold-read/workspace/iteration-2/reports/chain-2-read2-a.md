FINDINGS

- Severity: Major
  Where: CLI-006, CLI-010, and the second open question in tickets.md. The question is the TODO "confirm that `OVERDUE` takes the place of the state".
  What: The draft states as normative output that `OVERDUE` replaces the state word. The author's own open question admits this hides `open` versus `assigned` and makes lines unreliable for scripts that grep by state. The only alternative is named and left unspecified, so the author never recommends one.
  Evidence: `cli.md` CLI-006 says "the line shows `OVERDUE` in place of the state". `tickets.md` says "a script that selects lines by `open` or `assigned` misses every overdue ticket". `cli.py:27` prints `{t.state:<8}`, and `list` shows no assignee anywhere, so the state word is the only assignment signal. The spec also says "A person or a script … sees no change for a ticket that is not overdue". That holds only until a ticket crosses its due time. Its line then changes between two runs of the same command.

- Severity: Major
  Where: TKT-014, TKT-015, TKT-016, TKT-019, and the sentence "The plan decides how a test … controls the time".
  What: The behaviors depend on wall-clock time, and the CLI has no way to set the time. The spec punts testability to the plan. `product-specs/README.md` requires that a tester can derive the verification path "from the text alone" with no undefined edge case. The only black-box route is to hand-write old `at` values into the log file, and the spec doesn't say so. The CLI also has no tests today.
  Evidence: `cli.py:15` builds `EventStore(args.log)` with the default `time.time` clock. `product-specs/README.md` says "precise enough that a tester … can derive a verification path". `architecture.md` says "The CLI is not covered by tests today". The TKT-014 examples (5 hours after creation) can't be reproduced without forged timestamps or a sleep.

- Severity: Minor
  Where: TKT-014 and TKT-017, on the current time and the invariants.
  What: TKT-014 says the current time comes from "the store's clock … see INV-005". INV-005 only governs how events are stamped. It says nothing about reading "now" for display. The draft also doesn't say whether the new time-dependence upholds INV-001 ("derived by replaying the log"). It carves out LOG-009 in prose without deciding that. It also doesn't say whether the time is read once per command or once per ticket. A ticket crossing its due time mid-run could then appear in `list` but not in `overdue`.
  Evidence: `invariants.md` INV-001 and INV-005. `tickets.md` TKT-017: "LOG-009 still holds … but the word … also depends on the time of the run". `store.py` exposes `clock` only as an attribute, with no read-now call.

- Severity: Minor
  Where: CLI-001, CLI-006, and the `tickets.md` intro paragraph.
  What: Unbuilt draft behavior is edited into existing authoritative items. CLI-001 now says "five subcommands" and CLI-006 describes `OVERDUE`. Both read as false against 0.3.0 until the draft is signed off, and a test derived from CLI-001 fails today. The notes say "draft", but the items are still normative text.
  Evidence: `cli.py:16-20` has four subparsers. `docs/README.md` calls product-specs the "Authoritative description of product behavior".

- Severity: Minor
  Where: the status wording and the edits to AGENTS.md and `product-specs/README.md`.
  What: Two problems here.
  - The draft date is "2026-11-05". HEAD (d0ec813) is dated 2026-11-06 and today is 2026-11-06, so a draft built on top of HEAD can't predate it. I'm unsure which date is right.
  - AGENTS.md still says "One is open now" (CLI-007). The draft adds eight new TODOs and makes CLI-012 depend on CLI-007.
  - Edits to AGENTS.md and `product-specs/README.md` also need sign-off, and the review brief doesn't list them.
  Evidence: `git log -1` gives "Fri Nov 6 07:19:26 2026". The AGENTS.md process rules say "Doc changes need user confirmation".

- Severity: Minor
  Where: CLI-010 and the third open question (the Goals bullet "oldest due first").
  What: The ordering the user asked for can't be seen in the output, because no due time is shown. The author notes this in the open questions. The request's one concrete behavior is therefore checkable only against the log.
  Evidence: the non-goal "No display of the due time", and CLI-010 "Each line is the line that `list` prints".

- Severity: Minor
  Where: CLI-012.
  What: The spec doesn't say how the failure is reported, because that waits on the open CLI-007 TODO. The item is therefore not testable until the user decides.
  Evidence: CLI-012: "follows whatever the user decides there". I confirmed both failures are tracebacks today. `store.py:30` raises `ValueError` and `sla.py:8` raises `ValueError`. `cli.py:33` catches only `TicketError`.

- Severity: Minor
  Where: TKT-019.
  What: The tie-break justification mentions only "two tickets of one priority created at the same instant". Equal due times also arise across priorities, for example a P1 created 20 hours after a P2. The rule itself (ID ascending) covers that case, so it is correct but under-explained.
  Evidence: TKT-005 hours of 4 and 24.

Checked and correct:
- The TKT-019 example holds. P3 created 80h ago was due 8h ago, and P1 created 10h ago was due 6h ago.
- The TKT-014 example holds. At 5h a P1 is overdue and a P2 is not.
- The CLI-006 sample spacing matches the format string.
- `--log` goes before the subcommand, as CLI-010 says.
- `overdue extra` exits 2 under argparse.
- 0.3.0 has four subcommands, and `make test` runs 7 tests, all passing.
- Neither listing creates the log, since only `append` writes.

PARAPHRASE

Proposal: A ticket that is not closed and is past its due time (creation time plus the SLA hours, strictly later) counts as overdue. This is worked out at run time and never written to the log. `ticketdesk list` would show the word `OVERDUE` where the state normally appears. It would keep ID order. A new argument-less `ticketdesk overdue` would print only those tickets, in the same line format, ordered by due time ascending and then by ID. Closing is the only thing that ends overdue status. Assigning has no effect on it. Nothing else changes: no alerts, no due-time display, no new options. Eight open questions wait for the user's confirmation.

Existing system, per the document alone: ticketdesk has four commands (`create`, `assign`, `close`, `list`). Each command replays an append-only JSON-lines log to rebuild every ticket, and `list` prints tickets in ID order as `#id [priority] state title`. A ticket's due time is its creation time plus 4, 24 or 72 hours by priority. Event timestamps come from the store's clock. Errors from ticket rules print `error: …` and exit 2. A corrupt log line or an unknown priority currently escapes as a traceback, which is the open CLI-007 conflict. The CLI has no tests.
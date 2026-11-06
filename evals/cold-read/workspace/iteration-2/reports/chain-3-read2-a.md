FINDINGS

I found no Blocker. I recomputed the numbers and examples, and they hold. Both examples are right: P1 at 5h is overdue and P2 is not, and the 80h/P3 versus 10h/P1 ordering is correct. The `OVERDUE` column padding is right too. Every claim about the code today checks out: four subcommands, `list extra` gives exit 2 with empty stdout, corrupt log and unknown priority both give tracebacks, and 7 tests pass. The findings below are about design and traceability.

- **Severity:** Major
  **Where:** CLI-006, CLI-010, and the second TODO under "Open questions"
  **What:** `OVERDUE` replaces the state word, and the spec states this as settled while also listing it as unconfirmed. Overdue tickets lose their open/assigned distinction in both commands. A script that filters on `open` or `assigned` silently drops them. A ticket's line format changes just because time passes. The spec admits this and names an alternative, a marker beside the state, but the normative text does not follow it.
  **Evidence:** CLI-006 draft: "the line shows `OVERDUE` in place of the state". TODO: "A script that selects lines by `open` or `assigned` misses every overdue ticket." TKT-016 says assigning an overdue ticket changes nothing visible. After `assign` prints `#1 assigned -> dana`, `list` still shows `OVERDUE`. This will cost rework if the user picks the marker.

- **Severity:** Major
  **Where:** TKT-014, TKT-017, and the Overdue intro ("derived and never stored")
  **What:** The spec adds the wall clock as a second source of truth for what a ticket looks like, and never mentions INV-001. It also leaves LOG-009 and the architecture's replay-only model unamended. Output is now not a pure function of the log. The spec patches this with a note that LOG-009 "still holds for states, assignees, resolutions, and due times".
  **Evidence:** INV-001: "The current state of every ticket is derived by replaying the event log". LOG-009: "Replaying the same log always yields the same tickets". TKT-017 says "The same log can show a ticket as not overdue now and as overdue later". `docs/architecture.md` says "Time is seconds since the epoch" but only for event stamping. The spec should state explicitly that overdue is a view over log and clock, and say whether that touches INV-001. Under AGENTS.md, a conflict with an invariant needs user confirmation.

- **Severity:** Major
  **Where:** TKT-014, "the time at which the command runs, read from the same clock that stamps events"
  **What:** The spec is not testable as written. It does not say whether the time is read once per command or per ticket, which matters for consistency within one listing. It also does not say how a tester controls the clock through the CLI. The CLI builds `EventStore(args.log)` with the default `time.time` and exposes no clock override, and the CLI has no tests. The spec's own open question on CLI tests is about scope only. Guidelines step 4 requires the test type to be named, and a subprocess test cannot fix "now" without an injection point (or without creating tickets at P1 and waiting 4 hours).
  **Evidence:** `ticketdesk/cli.py:17` has no clock parameter. `store.py:16` takes `clock=time.time`. `docs/guidelines.md` planning step 4. Also, LOG-004 does not define a clock. INV-005 and the architecture do, so the citation is slightly off.

- **Severity:** Minor
  **Where:** CLI-012
  **What:** An unknown priority "stops the command in the same way" as a corrupt line, which is "an error that names the file and the line". The unknown-priority error today names neither. It is a bare `ValueError` from `due_at`.
  **Evidence:** `sla.py:8` raises `unknown priority 'X'; expected one of [...]` with no path or line. `store.py:33` is where the file:line message comes from.

- **Severity:** Minor
  **Where:** CLI-010, "as `list` does with no tickets and as CLI-008 requires"
  **What:** CLI-008 requires exit 0 and an empty stderr. It does not require empty stdout. "As CLI-008 requires" overstates what it says.
  **Evidence:** CLI-008 text. CLI-006 is the item that says "it prints nothing".

- **Severity:** Minor
  **Where:** CLI-001 and CLI-006, edited in place
  **What:** Unbuilt behavior is mixed into items that read as current and "authoritative" in the same files. CLI-001 now says "five subcommands", which is false for 0.3.0 and would fail as a test today. The hedges are sentences inside the items rather than a separate section. Because CLI-006 mixes current and draft rules, a reader cannot get the 0.3.0 behavior from the item alone.
  **Evidence:** `docs/product-specs/README.md`: "Authoritative description of what ticketdesk does". The cli.md note and CLI-001 and CLI-006 hedges.

- **Severity:** Minor
  **Where:** Goals, third bullet, and the claim "A ticket that is not overdue prints the same line as in ticketdesk 0.3.0"
  **What:** This is true only at a moment in time. The same ticket's line changes as soon as it passes its due time, so the goal does not protect scripts over time. The spec also says "a script counts the overdue tickets by counting those lines" but gives no unambiguous parse rule for a title that begins with `OVERDUE` or contains padded text. The position rule helps, but the line has no delimiter between state and title.
  **Evidence:** CLI-006 draft ("A title may contain the same word").

- **Severity:** Minor
  **Where:** The Overdue section and the open questions, versus the `overdue` ordering
  **What:** The ordering key (due time) is invisible to the user, as the spec notes. An agent cannot verify the order or see how late a ticket is. This is acknowledged but unresolved, and it affects acceptance. The request said "oldest due first", which only makes sense if users can check it.
  **Evidence:** Non-goal "No display of the due time" and the third TODO.

- **Severity:** Minor
  **Where:** `AGENTS.md`, `docs/product-specs/README.md`, and the draft date "2026-11-05"
  **What:** Two things. First, the diff edits AGENTS.md and the spec README index, which the request did not name. Both are small status lines, but AGENTS.md says "Doc changes need user confirmation". Second, the date is 2026-11-05, while today is 2026-11-06 and the repo's only commit is dated Nov 6. I cannot verify which day the draft was written.
  **Evidence:** `git diff --stat` shows 4 modified files. AGENTS.md "Process rules".

- **Severity:** Minor
  **Where:** The non-goal "No change to `create`, `assign`, and `close`" output lines
  **What:** The `assign` and `close` output prints the state, so `assign` on an overdue ticket prints `assigned` while `list` shows `OVERDUE`. The spec does not mention this inconsistency, though it follows from CLI-004 and CLI-006.
  **Evidence:** `cli.py:27` prints `{t.state}`. CLI-004.

PARAPHRASE

**What the document proposes:** A ticket that is not closed and is past its due time (creation plus 4, 24 or 72 hours by priority) counts as overdue. It is computed from the log and the clock each time and never written to the log. `ticketdesk list` would show the word `OVERDUE` instead of the state for such tickets, still in ID order. A new argument-less `ticketdesk overdue` would print only those tickets in the same line format, earliest due first, with ties broken by ID. It mirrors `list` for damaged logs and for empty results. Several choices are marked as unconfirmed assumptions: replacing the state word, not showing the due time, ties, empty output, and the damaged-log behavior.

**How the system works today, according to the document alone:** `ticketdesk` has four subcommands, `create`, `assign`, `close` and `list`. Each replays an append-only JSON-lines log to rebuild ticket state (open, assigned, closed). Due time is creation time plus the hours for the priority. `list` prints every ticket in ID order as `#id [priority] state title`. Rule errors print `error:` and exit 2. A corrupt line or an unknown priority in the log currently escapes as a traceback with exit 1, which is an open TODO. The CLI has no tests.
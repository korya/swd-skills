FINDINGS

- **Severity:** Blocker
  **Where:** cli.md, CLI-012
  **What:** The spec has `overdue` skip unreadable log lines and exit 0. That breaks INV-004 and LOG-007, which stop every operation on a corrupt line. The draft does not flag this as an invariant break. It is also missing from the "Open questions" list. AGENTS.md says an invariant break needs explicit user confirmation.
  **Evidence:**
  - invariants.md INV-004: "No corrupt line is skipped and no partial state is returned."
  - event-log.md LOG-007: "A line that is not valid JSON stops every operation with an error."
  - store.py:25-35 raises `ValueError` on a bad line.
  - CLI-012 says "skips a log line that it cannot read".
  - It would also make `overdue` and `list` disagree on the same corrupt log, and it is silent on the open CLI-007 conflict.
  - A partial list also hides tickets silently. That is the opposite of the reason the stated goal gives.

- **Severity:** Blocker
  **Where:** tickets.md, TKT-019 worked example
  **What:** The arithmetic is wrong, and the ordering conclusion is wrong with it. Ticket 1 is `P3` (72 h) and was created 80 h ago, so it was due 8 h ago, not 1 h ago. Ticket 2 is `P1` (4 h) and was created 10 h ago, so it was due 6 h ago. Ticket 1 was due earlier and comes first. The draft says ticket 2 comes first.
  **Evidence:** TKT-005 (P1=4, P3=72) and sla.py:3. 80−72=8 and 10−4=6. For the example to hold, ticket 1 would have to be created 73 h ago.

- **Severity:** Major
  **Where:** cli.md, CLI-006 second paragraph and example
  **What:** `list` is reordered, with overdue tickets first. The request only asked for them to "show as OVERDUE". The reordering contradicts TKT-013 and the unchanged first sentence of CLI-006 ("in ID order, see TKT-013"). It contradicts the draft's own goal of "no change for a ticket that is not overdue" and the non-goal "No sort option". It also does not appear in the open questions or in tickets.md's TKT items.
  **Evidence:**
  - TKT-013: "sorted by ID ascending". It is not amended.
  - cli.md says "`list` prints the overdue tickets first".
  - The example hides the problem because ticket 1 is overdue and already comes first by ID. It needs an example where an overdue ticket has a higher ID.

- **Severity:** Major
  **Where:** cli.md, CLI-010 example (`ticketdesk overdue --log desk.jsonl`)
  **What:** The example does not work. `--log` is a top-level option, not a subcommand option, so argparse rejects it after the subcommand with exit 2. CLI-011 also says `overdue` takes "no option of its own", and the example appears to contradict that.
  **Evidence:**
  - cli.py:13 defines `--log` on the main parser.
  - I ran `python3 -m ticketdesk.cli list --log /tmp/x.jsonl`. It printed `error: unrecognized arguments: --log /tmp/x.jsonl` and returned rc=2.
  - AGENTS.md puts `--log` before the subcommand.

- **Severity:** Major
  **Where:** cli.md, CLI-010 (stderr note `no overdue tickets`)
  **What:** The spec has a successful command write to stderr. CLI-008 requires success to write nothing to stderr. The draft does not mention the conflict. The open questions list this choice only as an assumption.
  **Evidence:** CLI-008: "A command that succeeds exits with code 0 and writes nothing to stderr." CLI-010: "prints `no overdue tickets` to stderr, and exits with code 0."

- **Severity:** Major
  **Where:** tickets.md, TKT-019
  **What:** The claim "The log stamps events in whole seconds" is false, so the tie-break rationale rests on a wrong premise. `time.time()` returns a float. LOG-004 says "seconds since the Unix epoch" and does not say whole seconds. Ties are only likely under a fake integer clock in tests, but the stated fact is wrong and could mislead the planner.
  **Evidence:** store.py:14 and :20 (`clock=time.time`, `record["at"] = self.clock()`), and event-log.md LOG-004.

- **Severity:** Major
  **Where:** cli.md CLI-006 and tickets.md open questions
  **What:** `OVERDUE` replaces the state, so `list` no longer shows `open` or `assigned` for late tickets. Anyone who reads the list loses the assignee state of exactly the tickets that matter most. The draft lists this as a TODO but already builds CLI-006, CLI-010 and TKT-018 on it. An alternative that keeps the state column (for example a suffix or marker) is not considered. The claim "a script counts overdue tickets by counting those lines" also promises a machine-readable contract that CLI-006 does not otherwise treat as a stable format.
  **Evidence:** cli.md CLI-006 ("`OVERDUE` in place of the state"), and the open-questions bullet about scripts missing overdue tickets.

- **Severity:** Minor
  **Where:** tickets.md TKT-014 and the CLI items
  **What:** The spec is hard to test at the CLI level. "Current time" comes from the store clock, which is injectable only through `EventStore(path, clock=...)`. The CLI builds the store with the default clock and has no hook (cli.py:20), and the spec notes the CLI has no tests. The spec does not say how an acceptance test of `list` or `overdue` should control time. Float comparison at the "exact due time" is also unlikely to be hit in practice.
  **Evidence:** cli.py:20, architecture.md:50, AGENTS.md "Not covered by tests: the CLI".

- **Severity:** Minor
  **Where:** tickets.md TKT-014
  **What:** "Read from the same clock that stamps events, see LOG-004" points at the wrong item. LOG-004 describes the `at` field and does not name the clock. INV-005 or architecture.md is closer. The service also has no clock of its own today, so the spec leaves unsaid where the "now" lives.
  **Evidence:** event-log.md LOG-004, tickets.py:27-30, and store.py:16.

- **Severity:** Minor
  **Where:** tickets.md TKT-017
  **What:** "LOG-009 still holds for states, assignees, resolutions, and due times" is true. But a ticket's displayed state in `list` is now time-dependent, so the determinism guarantee covers less of what users see than before. The paragraph does not say this.
  **Evidence:** LOG-009, and TKT-017's own line "can show a ticket as not overdue now and as overdue later".

- **Severity:** Minor
  **Where:** AGENTS.md, docs/product-specs/README.md diffs
  **What:** Unsigned-off draft work is written into the index files and "Current state" as "Specified, not built". AGENTS.md says doc changes need user confirmation. Agents that load AGENTS.md first may read the draft as settled. Also, tickets.md gains Goals, Non-goals and Open questions sections that the spec format in the product-specs README does not describe.
  **Evidence:** the `git diff` hunks for AGENTS.md (lines ~115-120), the README table, and README "Spec format".

- **Severity:** Minor
  **Where:** cli.md CLI-011
  **What:** The claim that `ticketdesk list extra` is rejected the same way is true (I ran it: exit 2, "unrecognized arguments"). But it is an existing behavior that no current spec item states, so CLI-011 relies on an uncovered behavior. `-h` is carved out without a stated result.
  **Evidence:** my run of `list extra --log ...`, and no CLI-0xx item covering unknown arguments (only CLI-001 and CLI-009).

- **Severity:** Minor
  **Where:** tickets.md TKT-014 and the "Overdue is derived" paragraph
  **What:** The spec does not say what happens with a hand-edited unknown priority. Replay would raise in `due_at` (sla.py:7-8) and `overdue` would fail where CLI-012 says to skip. This is a sub-case of the CLI-012 and CLI-007 conflict and is not addressed.
  **Evidence:** tickets.py:36 and sla.py:6-9.

PARAPHRASE

**What the document proposes:** `ticketdesk list` would show `OVERDUE` in the state column for any ticket that is not closed and whose due time has passed. It would also print overdue tickets first. A new argument-free `ticketdesk overdue` command would print only those tickets, earliest due time first, with ties broken by ID. Overdue would be computed on every run from the log and the current time and would never be written to the log. The command would print a stderr note and exit 0 when nothing is late, and it would skip damaged log lines instead of failing.

**How the existing system works, per the document alone:** ticketdesk 0.3.0 has four subcommands: `create`, `assign`, `close` and `list`. Every ticket state is rebuilt by replaying the append-only event log. Each event is stamped by the store's clock. A ticket's due time is its creation time plus 4, 24 or 72 hours by priority. `list` prints every ticket in ID order with its real state. A corrupt log line stops everything. One known gap is that unknown priorities and corrupt lines currently escape as tracebacks (CLI-007).

I could not paraphrase the CLI-012 and CLI-010 stderr behavior against the existing rules without contradiction. They are covered in findings 1 and 5.
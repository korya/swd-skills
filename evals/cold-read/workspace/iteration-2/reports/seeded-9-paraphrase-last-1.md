FINDINGS

- **Severity:** Blocker
  **Where:** tickets.md, TKT-019 worked example
  **What:** The arithmetic is wrong, and the correct numbers reverse the conclusion. Ticket 1 is P3 (72 h) and was created 80 h ago, so it was due 8 hours ago, not 1 hour ago. Ticket 2 was due 6 hours ago. The earlier due time is ticket 1, so ticket 1 comes first. The example as written contradicts the rule it illustrates.
  **Evidence:** TKT-005 gives P3 = 72 h, so 80 − 72 = 8. The document says "ticket 1 … due 1 hour ago … so ticket 2 comes first". Ticket 2 is P1: 10 − 4 = 6, which is correct. A "1 hour ago" result would need "created 73 hours ago".

- **Severity:** Blocker
  **Where:** cli.md, CLI-012
  **What:** `overdue` skips corrupt log lines and exits 0. This breaks INV-004 and LOG-007, which say a corrupt line stops the operation and nothing is skipped. The document does not flag the conflict, and AGENTS.md says to "Surface conflicts" and to get user confirmation before breaking an invariant. It is also missing from the Open questions list.
  **Evidence:** INV-004: "No corrupt line is skipped and no partial state is returned." LOG-007 says the same. `ticketdesk/store.py:34-35` raises on a bad line. Skipping needs a store change, and the store is meant to be generic.
  Two further problems:
  - The skipped line may be a `closed` or `assigned` event. A closed ticket would then be listed as overdue, which is wrong output with no warning.
  - `list` would fail on the same log while `overdue` succeeds, so the two commands disagree.

- **Severity:** Major
  **Where:** cli.md, CLI-006 ("`list` prints the overdue tickets first … then the other tickets")
  **What:** The request only asked for overdue tickets to show as OVERDUE in `list`. This reorders `list`, which contradicts TKT-013 and the document's own third goal.
  **Evidence:**
  - CLI-006 sentence 1 still says "in ID order, see TKT-013", and TKT-013 says "sorted by ID ascending".
  - Goal 3 says there is "no change for a ticket that is not overdue", but non-overdue tickets move down the list.
  - The example output hides this because only ticket 1 is overdue.
  - Reordering is not in the Open questions list.

- **Severity:** Major
  **Where:** cli.md, CLI-010 example `ticketdesk overdue --log desk.jsonl`
  **What:** The example does not work today. `--log` is a top-level option and must come before the subcommand. After the subcommand argparse rejects it, which also conflicts with CLI-011 ("no option of its own after the command name").
  **Evidence:** I ran `main(['list','--log','/tmp/x.jsonl'])`. The output was `ticketdesk: error: unrecognized arguments: --log /tmp/x.jsonl`. `cli.py:13` defines `--log` on the main parser. AGENTS.md uses `ticketdesk --log … create`. CLI-002 does not say where the option goes.

- **Severity:** Major
  **Where:** cli.md, CLI-010 versus CLI-008
  **What:** CLI-010 prints `no overdue tickets` to stderr and exits 0. CLI-008 says a successful command exits 0 and "writes nothing to stderr". The spec does not note the exception or amend CLI-008.
  **Evidence:** CLI-008 text. The Open questions list the stderr note as an assumption but do not mention the conflict. Every other empty output in the project is silent (`list` with no tickets, LOG-006).

- **Severity:** Major
  **Where:** tickets.md, TKT-019
  **What:** The document claims "the log stamps events in whole seconds", which is false. The tie-break rationale rests on it.
  **Evidence:** `store.py:14,20` uses `time.time`, which returns a float. LOG-004 says only "seconds since the Unix epoch". Equal due times are therefore rare, and the tie rule is a safety net. The sentence should be reworded. Float comparison at the exact due time (TKT-014) is also untested.

- **Severity:** Major
  **Where:** cli.md, CLI-006 (`OVERDUE` replaces the state)
  **What:** The design hides the `open`/`assigned` distinction for the tickets agents care most about. The document admits this and lists it as an open question, but it is the main design choice. Showing the state alongside the marker was not weighed as an alternative, and the request ("show as OVERDUE") does not require replacement.
  **Evidence:** The Open questions bullet 2 ("A script that selects lines by `open` or `assigned` misses every overdue ticket"). That is a change for existing scripts, which conflicts with goal 3 and with the claim that the format stays the same.

- **Severity:** Minor
  **Where:** tickets.md, TKT-017 ("LOG-009 still holds")
  **What:** The `list` and `overdue` output now depends on the wall clock, so replay-derived output is no longer deterministic. LOG-009 only covers states, assignees, resolutions and due times, so the claim is narrow but easy to misread. The spec does not say how a test fixes the clock. `EventStore` takes an injectable clock, but the service has no hook for "now", and the spec does not say where the current time is read.
  **Evidence:** `tickets.py` has no clock access. The product-specs README requires specs to be "deterministic". AGENTS.md notes the CLI has no tests, so the new CLI items have no test harness.

- **Severity:** Minor
  **Where:** TKT-014, "the same clock that stamps events, see LOG-004"
  **What:** LOG-004 and INV-005 describe the store's clock for stamping events, not a source of "now" for reads. A reader may take this to mean the current time is stored or read from the log.
  **Evidence:** INV-005. `store.py:16` has `clock` as a constructor argument.

- **Severity:** Minor
  **Where:** cli.md, CLI-011 ("`-h` is outside this item")
  **What:** `-h` is left unspecified, although argparse already accepts it on subparsers and exits 0 with usage on stdout. This leaves a gap in the "takes no argument" rule.
  **Evidence:** `cli.py` uses default argparse subparsers.

- **Severity:** Minor
  **Where:** Both files, duplicated text
  **What:** The draft status is repeated in four places (the intro of tickets.md, the intro of cli.md, CLI-001, CLI-010) and in AGENTS.md and the specs README. CLI-001 and CLI-010 say "not built" inside normative items, so those items go stale once the feature is built. The edits to AGENTS.md and the README were not part of the listed scope and need confirmation under "Doc changes need user confirmation".

PARAPHRASE

**What the document proposes.** Tickets that are not closed and are past their due time get the label `OVERDUE` in place of their state in `ticketdesk list`. Overdue tickets are also moved to the top of that list. A new `ticketdesk overdue` command prints only the overdue tickets, ordered by due time, earliest first, with ties broken by ID. The overdue status is calculated each time from the current clock and is never written to the log. The command prints a note to stderr when there is nothing to show, and it skips corrupt log lines. Several parts are marked as unconfirmed assumptions for the user to settle.

**How the existing system works, according to the document alone.** ticketdesk has four subcommands (`create`, `assign`, `close`, `list`). Ticket state comes from replaying an append-only JSON lines log. Each ticket moves from `open` to `assigned` to `closed`. The due time is the creation time plus a number of hours set by priority (P1 4, P2 24, P3 72). `list` prints every ticket by ID, and any corrupt line stops replay with an error. I could not take "events are stamped in whole seconds" from the document as a fact about the system, because the code contradicts it (see above).
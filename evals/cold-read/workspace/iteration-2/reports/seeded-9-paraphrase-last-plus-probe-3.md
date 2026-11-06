FINDINGS

- **Severity:** Blocker
  **Where:** `tickets.md` TKT-019, the worked example.
  **What:** The arithmetic is wrong, and the example gives the opposite order from the rule it illustrates. Ticket 1 is `P3` (72h), created 80h ago, so it was due 8 hours ago, not 1. Ticket 2 is `P1` (4h), created 10h ago, so it was due 6 hours ago. Ticket 1 was due earlier, so it comes first.
  **Evidence:** TKT-005 gives 72h for `P3` and 4h for `P1`. 80−72 = 8 and 10−4 = 6. The spec says "ticket 2 comes first".

- **Severity:** Blocker
  **Where:** `cli.md` CLI-012 ("overdue on a damaged log").
  **What:** CLI-012 has `overdue` skip unreadable lines and exit 0. That breaks INV-004 and LOG-007, which say a corrupt line stops every operation with an error. `invariants.md` is "the floor", and AGENTS.md requires explicit user confirmation to break an invariant. The spec does not flag the conflict. It is missing from "Open questions", and the status note does not mention it either.
  **Evidence:**
  - INV-004: "No corrupt line is skipped and no partial state is returned."
  - LOG-007: "stops every operation with an error".
  - CLI-012: "skips a log line that it cannot read and lists the overdue tickets from the other lines."
  - Skipping lines also gives wrong results. A skipped `closed` event would show a closed ticket as overdue. A skipped `created` event would make later `assigned`/`closed` events fail on a missing ticket.
  - It also contradicts the existing, unresolved CLI-007 TODO, which is about corrupt logs and exits.

- **Severity:** Major
  **Where:** `cli.md` CLI-006, the paragraph "`list` prints the overdue tickets first".
  **What:** Reordering `list` was not requested, and it contradicts the current spec. The request asked only for the word OVERDUE in `list`. The reorder breaks TKT-013 and CLI-006's own first sentence, both of which say ID order. It also weakens the goal that `list` output is unchanged for non-overdue tickets. The reorder is absent from the Goals, Non-goals and Open questions. The example hides it, because ticket 1 is first either way.
  **Evidence:**
  - TKT-013: "sorted by ID ascending".
  - CLI-006: "one line per ticket in ID order, see TKT-013".
  - The new text two paragraphs later says "overdue tickets first, in the order of TKT-019".
  - The tickets.md intro says only "shows as OVERDUE in the ticket list".

- **Severity:** Major
  **Where:** `cli.md` CLI-010 ("prints `no overdue tickets` to stderr, exits 0").
  **What:** This contradicts CLI-008, which says success writes nothing to stderr. `list` with no tickets prints nothing at all, so the two commands would behave differently. The TODO in "Open questions" covers the choice, but it does not name the CLI-008 conflict.
  **Evidence:** CLI-008: "A command that succeeds exits with code 0 and writes nothing to stderr." Non-goals say "No exit code signals that overdue tickets exist", which fits exit 0, but the stderr note is still a conflict.

- **Severity:** Major
  **Where:** CLI-006 and the Open questions.
  **What:** `OVERDUE` replaces the state, so `assigned` and `open` are hidden. The spec says a script selecting `open`/`assigned` misses overdue tickets. It also claims "a script counts the overdue tickets by counting those lines", yet it makes no promise to scripts that currently parse state. That is a breaking change to a documented output, which the goal "no change for a script" understates. The point is flagged as a TODO, but it is a design risk. Showing overdue as a separate marker or column would keep the state visible. The request says only "show as OVERDUE".
  **Evidence:** CLI-006 spec text and the TODO "A script that selects lines by `open` or `assigned` misses every overdue ticket."

- **Severity:** Major
  **Where:** CLI-012 and TKT-014, an undefined "cannot read".
  **What:** "A log line that it cannot read" is undefined. Today's failures are not only invalid JSON. I tried each of these:
    - a line with an unknown priority raises `ValueError`
    - an `assigned` event for a missing id raises `KeyError: 7`
    - a JSON line `[1]` raises `TypeError`
  
  The spec does not say which of these `overdue` skips. A tester cannot derive the behaviour, which is against the spec-format rule that a spec is "deterministic".
  **Evidence:** Runs against the built `list`, which printed `ValueError: unknown priority 'P9'…`, `KeyError: 7` and `TypeError: list indices must be integers…`. These are tracebacks, and CLI-007's TODO already notes that tracebacks escape.

- **Severity:** Minor
  **Where:** TKT-017 and TKT-014.
  **What:** TKT-017 says LOG-009 "still holds" for due times and states. But overdue depends on the current time, so the same log gives different output over time. The spec acknowledges this ("not overdue now and overdue later"). Tests will need an injectable clock. TKT-014 says the time is "read from the same clock that stamps events". The clock is `EventStore.clock`, which `TicketService` does not expose, and the CLI cannot inject one today. The spec does not say how a test fixes the time.
  **Evidence:** `store.py` line 17, `clock=time.time`, used only in `append`.

- **Severity:** Minor
  **Where:** TKT-019 ("two tickets of one priority created in the same second").
  **What:** The claim is not fully accurate, though not harmful. `at` is stored as a float from `time.time()`, not whole seconds. The same applies to LOG-004, which says "seconds since the Unix epoch". Equal due times are rarer than the text suggests, and the tie-break is only reached with equal floats. The spec rests the tie-break on whole-second stamping, which the code does not do.
  **Evidence:** `store.py` `record["at"] = self.clock()`, a float. LOG-004 does not say whole seconds.

- **Severity:** Minor
  **Where:** CLI-011.
  **What:** The claim is correct but incomplete, because `overdue` would not be a bare subparser the way `list` is. I verified `ticketdesk list extra` gives `unrecognized arguments: extra`, exit 2, usage on stderr. The statement that nothing goes to stdout holds. It excludes `-h`, which leaves that behaviour undefined. It also does not cover `--log` placed after the subcommand, such as `overdue --log desk.jsonl`. CLI-010 uses exactly that form as its example, but `--log` is a top-level option and is only accepted before the subcommand today.
  **Evidence:** `cli.py` adds `--log` to the parent parser only. The CLI-010 example `ticketdesk overdue --log desk.jsonl` would be rejected as written, by CLI-011's own rule.

- **Severity:** Minor
  **Where:** CLI-006's example and edge cases.
  **What:** The example output is correct: `OVERDUE` is padded to 8 and the alignment is right. Coverage is thin. There is no example of an overdue `assigned` ticket, of a title containing "OVERDUE", or of what `create`/`assign` print for an overdue ticket. Existing-behaviour claims check out: the missing-file case creates no file, and `make test` runs 7 passing tests.
  **Evidence:** `list` on a missing path printed nothing and left the directory empty.

PARAPHRASE

**What the document proposes.** Support agents should be able to see late tickets. A ticket that is not closed and is past its due time is "overdue". It is derived from the log and the clock at run time and never stored. `list` shows the word OVERDUE in place of the state, and puts overdue tickets first. A new `overdue` command lists only overdue tickets, earliest due first. It breaks ties by ID. It prints a note to stderr when there are none. It skips damaged log lines. The spec is marked as a draft awaiting user sign-off, with open questions listed.

**How the existing system works, per the document alone.** Tickets are `open`, `assigned` or `closed` and move forward only. Each has a due time of creation plus 4, 24 or 72 hours by priority. All changes are appended as events to a JSON lines log, and state is rebuilt by replaying it. Corrupt lines stop everything with an error naming the file and line. `list` prints every ticket in ID order. Successful commands exit 0 with nothing on stderr, and rule errors exit 2.

Two things in the document do not fit the existing system. The 0.3.0 CLI cannot take `--log` after the subcommand. Corrupt logs and unknown priorities currently crash with tracebacks, which CLI-007 already records as an open conflict.
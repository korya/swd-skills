Checks are done. Writing up the review now.

FINDINGS

- **Severity:** Blocker
- **Where:** cli.md, CLI-006, second paragraph ("A `closed` or `assigned` ticket always shows its state"), against TKT-016 and the same paragraph's first rule.
- **What:** The spec contradicts itself on what an overdue `assigned` ticket prints. One passage says an `assigned` ticket always shows `assigned`. TKT-016 says an assigned overdue ticket stays overdue, and the rule above says an overdue ticket shows `OVERDUE` in the state position. An implementer or tester cannot tell which output is correct.
- **Evidence:** cli.md says "A `closed` or `assigned` ticket always shows its state." tickets.md TKT-016 says "Assigning an overdue ticket leaves it overdue". CLI-006 also says "the line shows `OVERDUE` in place of the state". The example hides the conflict because ticket 2 is `assigned` but not overdue. The first Open question even says "Then neither `list` nor `overdue` shows whether an overdue ticket is assigned", which contradicts the "always shows its state" sentence.

- **Severity:** Major
- **Where:** cli.md, CLI-006 and CLI-010 (replace the state with `OVERDUE`); the second open question in tickets.md.
- **What:** `OVERDUE` replaces the state column, so `list` loses information it shows today: whether an overdue ticket is `open` or `assigned`. Existing scripts that filter on `open` or `assigned` silently miss every overdue ticket. The spec records this as an open question but still writes it into CLI-006 as the rule. It names no alternative, such as an added marker that keeps the state, so the user is not choosing between options. The goal "no change for a script" holds only for tickets that are not overdue, and those are the tickets the most urgent scripts care about. I am not claiming the replacement is wrong, since the request says "show as OVERDUE". The cost is just not visible to the person signing.
- **Evidence:** cli.md CLI-006 and the Open questions bullet 2. cli.py:30 prints `{t.state:<8}`. The event log is also a user-facing surface (event-log.md intro), so this is in the same spirit.

- **Severity:** Major
- **Where:** tickets.md, TKT-014 ("read from the same clock that stamps events, see LOG-004"), and the architecture it implies.
- **What:** The clock claim is unsupported and leaves a design gap. LOG-004 does not mention a clock; INV-005 and architecture.md do. The clock exists only inside `EventStore` (`clock=time.time`), and `TicketService` has no access to the current time. A read-only command stamps no event. The spec never says that the service reads `store.clock`, or that `list` and `overdue` read the clock once per command. Tests that go through the service with a fake clock cannot pin "now" without that decision.
- **Evidence:** store.py:13 and :17 (`self.clock`); tickets.py has no time source (`TicketService.__init__(self, store)`); event-log.md LOG-004 says only "the time it was appended". architecture.md: "stamps each event with the time from an injectable clock".

- **Severity:** Major
- **Where:** tickets.md TKT-014 to TKT-019 and the Overdue section, against the spec format rules.
- **What:** The spec format says each item is a "deterministic" observable behavior. Overdue depends on wall-clock time. LOG-009 ("same log always yields same tickets") is carved out in TKT-017 by a prose sentence. The spec does not say that "now" can be fixed for testing, so it is hard to derive a test from the text alone. Examples such as "5 hours after its creation" work only if a tester controls the clock.
- **Evidence:** docs/README.md "Each spec describes one observable, deterministic behavior"; TKT-017 "The same log can show a ticket as not overdue now and as overdue later."

- **Severity:** Minor
- **Where:** cli.md, CLI-006 claim "Every output line with `OVERDUE` in that position is one overdue ticket, so a script counts the overdue tickets by counting those lines."
- **What:** The claim is false when a title contains a newline. `create` accepts any title, so a title like `x\n#9 [P1] OVERDUE y` produces a forged line in `list`. The claim is also false for `overdue`, which uses the same format. This is an existing weakness, but the spec promises something it cannot guarantee.
- **Evidence:** cli.py:15 passes `title` unchecked. tickets.py `create` rejects only an empty title.

- **Severity:** Minor
- **Where:** cli.md CLI-001 ("one of five subcommands") and the CLI-006 draft paragraph; the text mixes shipped and unbuilt behavior in authoritative items.
- **What:** CLI-001 and CLI-006 are described as authoritative, tested behavior, and now state things that are false for 0.3.0. A tester deriving checks from CLI-001 alone would fail against 0.3.0. The draft notes mitigate this but do not remove it. Also, the draft sentence "ticketdesk 0.3.0 has the other four" duplicates the status note.
- **Evidence:** cli.py:16-19 registers four subparsers; the status note in cli.md says "ticketdesk 0.3.0 has four subcommands".

- **Severity:** Minor
- **Where:** tickets.md, the Overdue section structure (Goals, Non-goals, Open questions, the status block).
- **What:** The project's spec format has only `### PREFIX-NNN` behavior items. The goals, non-goals and open-question headings are new, and open questions are not behavior. The doc rules say not to write docs for "a design exploration that has not landed". It is defensible for a draft, but it departs from the convention without saying so. Also the Overdue prose has no ID and is not testable, and some CLI-006 behavior (the counting rule, padding) lives outside an ID.
- **Evidence:** docs/README.md "Spec format requirements" and "When not to write a doc"; product-specs/README.md.

- **Severity:** Minor
- **Where:** cli.md CLI-012 and its TODO.
- **What:** CLI-012 ties `overdue` to whatever `list` does on a bad log. Today `list` prints a traceback and exits 1, while CLI-007 says ticket rule errors exit 2. So the item cannot be tested to a stable outcome until the CLI-007 TODO is settled. The spec acknowledges this. Also, a `created` event with an unknown priority can only come from a hand-edited log, which the spec does not say.
- **Evidence:** store.py:30 raises `ValueError` and cli.py catches only `TicketError`. sla.py:7 raises `ValueError`. CLI-007 TODO.

- **Severity:** Minor
- **Where:** Process, AGENTS.md and product-specs/README.md edits.
- **What:** Both indexes now list the unbuilt draft. That is consistent with the "new spec" rule, but the guidelines say doc changes need user confirmation, and the AGENTS.md "Current state" is the first file every agent reads. An agent could treat TKT-014 to TKT-019 as shipped. The "draft, waits for sign-off" note in AGENTS.md covers this adequately.
- **Evidence:** git diff for AGENTS.md; guidelines.md "Confirm every doc change with the user".

I found no errors in the numbers. P1 at 5 hours is overdue and P2 is not (4 h and 24 h). Ticket 2 (P1, created 10 h ago) was due 6 h ago, and ticket 1 (P3, created 73 h ago) was due 1 h ago. The example's column padding is right. `ticketdesk list extra` exits with code 2, which I ran. A missing log file gives an empty listing, matching the code. `make test` passes, 7 tests.

PARAPHRASE

**What the document proposes.** Tickets that are not closed and are past their due time (creation time plus the SLA hours for their priority) are shown as `OVERDUE` in the state position of `ticketdesk list`. A new `ticketdesk overdue` command, with no arguments, prints only those tickets in the same line format, earliest due first, with ties broken by ID. Overdue is calculated at run time from the clock and is never written to the log. The goals, non-goals and unconfirmed assumptions are listed, and the user must sign off before anyone plans or builds it.

**How the existing system works, according to the document alone.** `ticketdesk` has four subcommands: `create`, `assign`, `close` and `list`. Tickets are rebuilt by replaying an append-only JSON lines log. A ticket moves `open`, `assigned`, `closed`, and its due time is its creation time plus 4, 24 or 72 hours for P1, P2 or P3. `list` prints every ticket in ID order as `#id [priority] state title`. Errors from ticket rules exit with code 2. An unknown priority and a corrupt log escape as tracebacks with exit code 1, which is an open conflict. Every event is stamped by the store's clock.
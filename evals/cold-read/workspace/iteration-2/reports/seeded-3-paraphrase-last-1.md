FINDINGS

- **Severity:** Major
  **Where:** `cli.md` CLI-006, the sentence "Every output line with `OVERDUE` in that position is one overdue ticket, so a script counts the overdue tickets by counting those lines."
  **What:** The claim is false today. A title can contain a newline, so a title can forge a line that looks like an overdue ticket. The document promises scripts a guarantee that `list` cannot give, and the spec's own aim (goal 3, scripts see no change) rests on it.
  **Evidence:** I ran `create $'x\n#9 [P1] OVERDUE  fake' --priority P1`. `list` then printed `#1 [P1] open     x` followed by `#9 [P1] OVERDUE  fake`. `tickets.py:56` only checks that the title is non-empty (TKT-002). Either restrict titles (a new rule, not in this spec) or drop the counting promise.

- **Severity:** Major
  **Where:** `cli.md` CLI-006 and the `tickets.md` open questions, "OVERDUE takes the place of the state".
  **What:** Replacing the state loses information, and the spec's own non-goals make it worse. In both `list` and `overdue`, an agent cannot tell whether an overdue ticket is `open` (nobody on it) or `assigned`. That is the first thing a support agent needs to know about a late ticket. `overdue` also cannot show why its tickets are in that order, because no due time is shown. The spec flags both points as TODOs but still presents the replacement as the design. The request says only "show as OVERDUE". A marker alongside the state (a suffix or a column) would meet it and break no script that filters on `open` or `assigned`. Compare with goal 3 (no change for non-overdue lines), which already protects the other lines.
  **Evidence:** Open questions, bullets 2 and 3. Current format at `cli.py:30`: `f"#{t.id} [{t.priority}] {t.state:<8} {t.title}"`. `assign` on an overdue ticket prints `#1 assigned -> dana` (`cli.py:25`), while `list` would then show `OVERDUE`. The two commands disagree about the same ticket, and the spec never mentions this.

- **Severity:** Major
  **Where:** `cli.md` CLI-001 and CLI-006, and the intro of `tickets.md`.
  **What:** Unsigned draft behaviour is written into the existing, authoritative items. CLI-001 now says "five subcommands", but the code has four. The `tickets.md` intro states "A ticket whose due time has passed is overdue until it is closed" as fact. The project treats these specs as the authority (`product-specs/README.md`: "Authoritative description of what ticketdesk does"; specs must be testable). A test derived from CLI-001 today would fail. The "draft, not built" hedges inside the items do not make them testable, and they will need cleaning up after sign-off. It also puts unsigned text into specs that were signed off (see the "Doc changes need user confirmation" rule in AGENTS.md).
  **Evidence:** `cli.py:14-18` registers 4 subcommands. The usage line from `list extra` shows `{create,assign,close,list}`.

- **Severity:** Major
  **Where:** `tickets.md` TKT-014 ("read from the same clock that stamps events, see LOG-004") and TKT-017 (LOG-009 "still holds").
  **What:** The spec does not say the clock is injectable. Overdue depends on wall-clock time, so it is the first rule where the output of `list` changes with no change to the log. The project makes time deterministic through an injectable clock owned by the store (`architecture.md`, Store section; `store.py:14`). The service has no clock of its own. Without a requirement here, "at the exact due time the ticket is not overdue" (TKT-014) and the order in TKT-019 cannot be tested at the CLI level. The CLI has no tests and no way to set the time. The spec also never relates "the log and the current time decide it" to INV-001 (state is derived from the log alone), and it cites no INV at all. The architecture says the store owns the clock, so reading it from the service is a layering decision that is left unstated.
  **Evidence:** `store.py:14` (`clock=time.time`), `tickets.py` (no time source), `architecture.md:49-50` ("injectable clock, which keeps tests deterministic"), `invariants.md` INV-001.

- **Severity:** Minor
  **Where:** `cli.md` CLI-011.
  **What:** "No option of its own" is correct but incomplete. `--log` belongs to the top-level parser, so `ticketdesk overdue --log x` is rejected as unrecognized, and `ticketdesk --log x overdue` works. The spec does not say this. The comparison "rejects `list extra` in the same way" is true (I ran it: exit 2, usage on stderr, "unrecognized arguments: extra").
  **Evidence:** `cli.py:13`, where `--log` is added to `parser`, not to a subparser.

- **Severity:** Minor
  **Where:** `tickets.md` TKT-019 and the "oldest due first" wording.
  **What:** Order is by due time, but `overdue` output carries only the ID, priority, and title (see the second finding), so a reader cannot check the order. The tie-break by ID is flagged as an open question. The worked example does not contain a tie, so the tie rule has no example.
  **Evidence:** The TKT-019 example (tickets 1 and 2); the open questions list.

- **Severity:** Minor
  **Where:** `cli.md` CLI-012 and TKT-018.
  **What:** The wording "same error message and exit code as `list` on the same log" is currently satisfied only by a traceback with exit 1. The spec marks this as a TODO and defers to CLI-007, which is the right call. A new command now adds a second place that depends on the open CLI-007 conflict.
  **Evidence:** `store.py:35` raises a `ValueError`. `cli.py:31` catches only `TicketError`. The same applies to the unknown-priority path at `sla.py:8` through `tickets.py:36`.

Checked and correct: the TKT-014 example (P1 with 5 hours is overdue, P2 is not), the TKT-019 example (ticket 2 due 6 hours ago, ticket 1 due 1 hour ago, so 2 first), the CLI-006 padding (`OVERDUE ` is 8 characters, so the example is aligned), TKT-017 (an absent log is not created by `list`: `store.py:26-27` returns early), and the new IDs (TKT-014 to 019 and CLI-010 to 012 follow the last existing IDs, TKT-013 and CLI-009). `make test` passes with 7 tests. The CLI has no tests, as AGENTS.md says.

PARAPHRASE

**Proposed:** `ticketdesk list` would show the word OVERDUE in place of the state for any ticket that is not closed and is past its due time (creation time plus the hours for its priority). A new `ticketdesk overdue` command, with no arguments, would print only those tickets, using the same line format. They would be sorted by due time, with ties broken by ID. Overdue is computed from the log and the current time on every run. It is never written to the log, and nothing else about the existing commands, due times, or output formats changes. The spec lists eight unconfirmed assumptions as TODOs.

**Existing system, according to the document alone:** `ticketdesk` has four commands: `create`, `assign`, `close`, and `list`. Every change is an event in an append-only JSON lines log, and ticket state is rebuilt by replaying it. A ticket is `open`, `assigned`, or `closed`, and its due time is its creation time plus 4, 24, or 72 hours by priority. `list` prints every ticket by ID. A corrupt log or an unknown priority currently ends as a Python traceback with exit code 1. That conflicts with CLI-007 and is still open.
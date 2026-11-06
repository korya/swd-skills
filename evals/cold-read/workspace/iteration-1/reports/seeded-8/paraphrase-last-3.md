FINDINGS

- **Severity:** Blocker
  **Where:** Step 2, `Ticket.is_overdue` and `TicketService.overdue`; the `OVERDUE_HOURS` table
  **What:** The plan adds a second hours table, `OVERDUE_HOURS`, and it has a wrong P3 value. The existing `SLA_HOURS` and `Ticket.due_at` already hold the due time. The plan's own claim A1 says every ticket carries its due time, yet step 2 ignores it. A P3 ticket would become overdue at 48 h instead of 72 h. The rule would also drift from TKT-005 whenever the SLA table changes. It breaks the architecture rule that `sla.py` is the single place for hours.
  **Evidence:**
  - plan.md:38 says `{"P1": 4, "P2": 24, "P3": 48}`.
  - sla.py:3 says `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`.
  - tickets.py:36 sets `t.due_at = due_at(...)`.
  - TKT-005 says P3 is 72.
  - architecture.md:54-56 says the hours table lives in one place.
  - Fix: `now > self.due_at`.

- **Severity:** Blocker
  **Where:** Step 2, `is_overdue` uses `now >= ...`
  **What:** The code makes a ticket overdue at exactly its due time. The plan's own TKT-014 text, the open-question 3 assumption, and the test plan all say it is not overdue at that moment. The code, the spec text, and the tests would contradict each other, and the boundary test would fail.
  **Evidence:**
  - plan.md:39 has `now >= self.created_at + ...`.
  - plan.md:30 says "At the due time exactly, it is not overdue."
  - plan.md:178 and plan.md:114 say the same.
  - A6 (plan.md:74) expects `[]` at the due time.

- **Severity:** Blocker
  **Where:** Step 2, `TicketService.overdue` sort key
  **What:** The sort is by `(t.created_at, t.id)`, not by due time. The request is "oldest due first". Creation order and due order differ across priorities, which the plan's own E3 (A4) shows. The result is wrong, and it would fail the plan's own P1-before-P3 test.
  **Evidence:**
  - plan.md:40 sorts by `t.created_at`.
  - plan.md:31 (TKT-015) and plan.md:118 require due-time order.
  - plan.md:72 (A4) shows a P3 created 80 h ago sorts after a P1 created 6 h ago.
  - With the plan's key the order is `[1, 2]`, but it should be `[2, 1]`.
  - Fix: use `t.due_at`.

- **Severity:** Major
  **Where:** Step 1 table, `cli.md CLI-009 (new)`
  **What:** CLI-009 already exists as "Ticket ID is an integer". The plan would duplicate the ID, and IDs are stable and globally unique. The next free CLI number is CLI-010. Every reference to CLI-009 in the plan (test plan, commits, A-table) is wrong with it.
  **Evidence:**
  - cli.md:58 says `### CLI-009: Ticket ID is an integer`.
  - plan.md:34 says "CLI-009 (new)".
  - docs/README.md:27-28 says a new spec takes the next free number.
  - The plan's own convention row at plan.md:98 claims it follows this rule.

- **Severity:** Major
  **Where:** Step 5, step 7, "Project conventions" first bullet, test plan
  **What:** The plan assumes `pytest` and `tmp_path`, but the project uses `unittest`. `make test` runs `unittest discover`, and CI runs only `make lint` and `make test`. pytest is not installed locally. A `tmp_path` test would not run under `make test`, so CI would silently skip it or fail. Step 7's `pytest -q` fails here. The "Reflected in plan" claim is false.
  **Evidence:**
  - Makefile:3 says `python3 -m unittest discover -s tests -q`.
  - architecture.md:80 says Tests use `unittest` and "no mocking library".
  - AGENTS.md:22 says `unittest`.
  - ci.yml:11-12 runs `make lint` and `make test`.
  - `python3 -m pytest` gives "No module named pytest".
  - plan.md:51, :58, :90 say otherwise.
  - Fix: `unittest.TestCase`, `tempfile`, and `subprocess` or `main(argv)`.

- **Severity:** Major
  **Where:** Assumptions table A3, A4, A5, A6, A7, A8; "Baseline"
  **What:** The evidence cites `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py`. Neither exists, and there is no `scratch/` directory, so the claimed experiments cannot be checked. The "Python 3.12.16" rerun is likewise unverifiable. A5 is marked "Risky" yet is confirmed only by those missing scripts. A reviewer cannot trust the "confirmed" results.
  **Evidence:** `ls scratch` gives "No such file or directory". Git status shows only `plan.md` as untracked. The claims are at plan.md:71-76.

- **Severity:** Major
  **Where:** Step 3, last bullet; the "else:" rewrite
  **What:** The plan says the subparsers "are not marked required" and that a missing subcommand reaches the `list` branch today. This is false. The code uses `required=True`. A missing subcommand exits 2 already, as CLI-001 says. The stated reason for the change is wrong. The change is still harmless, but the plan describes the system incorrectly. It also leaves the claimed hazard (A7's "no command exited 2") unexplained.
  **Evidence:** cli.py:14 `sub = parser.add_subparsers(dest="cmd", required=True)`. Compare plan.md:47.

- **Severity:** Major
  **Where:** Step 3 and "Approach summary", `now` handling versus INV-005 and architecture.md
  **What:** The CLI reads `time.time()` directly. The architecture says time comes from the store's injectable clock, "never from the caller" (INV-005, architecture.md:68-69). The plan does not discuss this. `EventStore` already owns a `clock`. Reading the wall clock in the CLI bypasses the injectable-clock pattern. The only way to test is the hand-written-log hack, because the CLI-level clock cannot be injected. The plan should justify this choice or use `store.clock()`. `svc.overdue(now)` also differs from how every other service method takes its time (from the store).
  **Evidence:** store.py:15 `clock=time.time`. architecture.md:49-50 and 68-69. plan.md:9 and :46.

- **Severity:** Major
  **Where:** "Out of scope" and "Approach summary" versus step 3 and open question 2
  **What:** The new `overdue` command prints the same `OVERDUE` label on every line. The plan notes this "carries no extra information" and still ships it. Since `list` already hides `open` versus `assigned` (open question 1), the `overdue` command is where an agent most needs the true state or the assignee. It is a real product choice, and it blocks the final CLI-010 text. It is deferred as an "assumption" rather than raised as a blocking decision, although the Headline says only the spec sign-off blocks.
  **Evidence:** plan.md:5, :177, :11.

- **Severity:** Minor
  **Where:** Headline and open question 5
  **What:** "Six spec changes" matches the six table rows, but the table also edits `event-log.md` for a one-word LOG-001 clarification. The plan says LOG-001 needs a change, though "Listing tickets appends nothing" already covers the `overdue` read. The edit is arguably unnecessary doc churn requiring sign-off. Also "TKT-014 ... overdue is never recorded" restates INV-001, and the plan's TKT-014 text does not itself define the "current time" source.
  **Evidence:** event-log.md:14-15. plan.md:35.

- **Severity:** Minor
  **Where:** Step 6, doc line references
  **What:** The docs updates say "update the test count" at AGENTS.md:102, and that line is only valid before the new tests. The count is not a fixed number once more tests are added, and the step does not say what the new count is. The plan also omits updating `AGENTS.md`'s "Running the project" example with `overdue`, and the CLI-007 line mentions "overdue inherits this". It does not mention the architecture.md:89 public-names list if `OVERDUE_HOURS` were exported. (This last point goes away if finding 1 is fixed.)
  **Evidence:** AGENTS.md:100-102. architecture.md:89.

- **Severity:** Minor
  **Where:** E2E script in "Test plan"
  **What:** The "expect" comments are off. After `assign 2 dana`, the step-3 `overdue` prints `#2 [P3] OVERDUE  Old P3`. The format `{label:<8}` gives `OVERDUE ` (8 chars) followed by a space, so there are two spaces before the title, which matches. But the closing `close 2 "Replaced the toner cartridge"` is the wrong example for a printer-on-fire-style ticket and is only cosmetic. The script also appends an event with `at` in the past after a later event, so the log is out of chronological order. This is allowed by replay but contradicts the append-time meaning of LOG-004, and the plan should say it is a test-only hack.
  **Evidence:** plan.md:139-148. LOG-004 at event-log.md:33.

PARAPHRASE

**What the plan proposes.** Overdue becomes a value computed at read time, never stored. A ticket is overdue if it is not closed and the current time is past its due time. `ticketdesk list` shows `OVERDUE` in the state column for those tickets. A new `ticketdesk overdue` prints only overdue tickets in the same line format, ordered by due time and then ID. Before any code, the user must approve six spec edits. The plan then adds the rule to the service, wires the CLI, adds unit and subprocess tests, and updates the docs.

**How the existing system works, according to the plan alone.** The log is the only truth, and every command replays it. The service holds the ticket rules, and the CLI only parses, prints, and maps errors to exit codes. Each ticket already carries a creation time, a priority, and a due time from the SLA table. The CLI has no tests, `list` prints in ID order, and an unknown priority or a corrupt log line escapes as a traceback (the CLI-007 TODO). The plan also believes the subparsers are not required and that the suite uses pytest. The code shows both beliefs are wrong.
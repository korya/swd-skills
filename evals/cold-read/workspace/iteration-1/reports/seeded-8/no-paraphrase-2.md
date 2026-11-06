FINDINGS

- **Severity:** Blocker
  **Where:** Step 2, `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`
  **What:** The plan adds a second hours table with P3 at 48. TKT-005 and `sla.py` say P3 is 72. The plan's own A1 cites `due_at` and the stored `t.due_at`, yet the rule ignores both. Tickets between 48 h and 72 h old would show OVERDUE before they are due. The duplicate table also contradicts the "Duplicate logic" sweep, which says no duplication exists.
  **Evidence:** `ticketdesk/sla.py:3` has `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`. `docs/product-specs/tickets.md:44` has `| P3 | 72 |`. `Ticket.due_at` is already set at `tickets.py:36`. The rule should be `now > self.due_at`.

- **Severity:** Blocker
  **Where:** Step 2, `Ticket.is_overdue` (`now >= ...`)
  **What:** The rule uses `>=`. TKT-014 as drafted in step 1, open question 3, and the boundary test all say a ticket is not overdue at the due time exactly. The code overdue-flags that exact instant, so the boundary test in the plan would fail.
  **Evidence:** Plan line 39 `now >= self.created_at + ...` against line 30 "At the due time exactly, it is not overdue" and line 114.

- **Severity:** Blocker
  **Where:** Step 2, `TicketService.overdue` sort key `(t.created_at, t.id)`
  **What:** The request asks for "oldest due first", which means ordering by due time. The plan sorts by creation time. That contradicts TKT-015 as drafted ("sorted by due time"). It gives the wrong order whenever priorities differ, for example a P1 created later that is due earlier than a P3 created earlier. The plan's own P1-before-P3 test (line 118) would fail against this code. The sort key should be `(t.due_at, t.id)`.
  **Evidence:** Plan line 40 against lines 31 and 118.

- **Severity:** Major
  **Where:** A4 ("E3", the P3 80 h ago / P1 6 h ago example) and the test-plan bullet at line 118
  **What:** The example does not show what it claims. With the real SLA (P3 = 72 h, P1 = 4 h), the P3 ticket is due at −8 h and the P1 ticket at −2 h. Due order is therefore [1, 2], which is the same as ID order. Only the invented 48 h value gives [2, 1]. So A4 is "confirmed" on a wrong table, and the test built from it would not tell a due-time sort from an ID sort. A discriminating case needs the lower ID to be due later, for example a P3 ticket created just before a P1 ticket.
  **Evidence:** Recomputed from `sla.py:3`. P3 created 80 h ago is due 72 − 80 = −8 h. P1 created 6 h ago is due 4 − 6 = −2 h.

- **Severity:** Major
  **Where:** Step 1, CLI-009 (new), and the "next free number" convention
  **What:** CLI-009 already exists ("Ticket ID is an integer"). The new `overdue` spec would collide with it. Per docs/README.md the next free ID is CLI-010. The plan's claim that it follows the next-free-number rule is false. The citations in steps 5 and 8 and in the test plan (CLI-009 for `overdue`) all need updating.
  **Evidence:** `docs/product-specs/cli.md:58` has `### CLI-009: Ticket ID is an integer`. `docs/README.md:27-28` says a new spec takes the next free number.

- **Severity:** Major
  **Where:** Step 3, last bullet, and the "Today a missing subcommand also reaches that branch" claim
  **What:** The claim about today's behavior is false. The subparsers are marked `required=True`, so a missing subcommand exits 2 in argparse before reaching the `else`. The `else:` to `elif` change is still harmless hardening, but the stated reason is wrong. It is also an unrequested change not listed in the scope.
  **Evidence:** `cli.py:14` has `add_subparsers(dest="cmd", required=True)`.

- **Severity:** Major
  **Where:** Steps 5 and 7, "Conventions", the pytest claims (`tmp_path`, `pytest -q`, "the suite runs under `pytest`")
  **What:** The project uses `unittest`, and its tests use `tempfile`. `make test` runs `python3 -m unittest discover`, and pytest is not installed or declared. The plan's `pytest` fixtures and the `pytest -q` run would not work, and CI only runs `make test`. The cited convention (AGENTS.md:22-23, Makefile:1-5) states the opposite. It breaks the "no dependencies" rule if pytest is added. The plan's own "tests/test_cli.py ... `tmp_path`" is not collectable by `make test`.
  **Evidence:** `Makefile:3` runs `python3 -m unittest discover -s tests -q`. `import pytest` gives `ModuleNotFoundError`. AGENTS.md's tech table says Tests: `unittest`. `tests/test_tickets.py:1-3` imports `tempfile` and `unittest`.

- **Severity:** Major
  **Where:** Assumptions A3, A4, A5, A6, A7, A8, and the "scratch/exp1_crafted_log.py" and "scratch/exp2_clock_and_argparse.py" citations
  **What:** The evidence files do not exist in the repo, so none of these experiments can be checked. Several results contradict the code (A4, A3 only on a 48 h table). Also, A8's claim that the scripts ran on Python 3.12.16 cannot be verified.
  **Evidence:** `ls scratch` gives "No such file or directory". The git status shows only `plan.md` as untracked.

- **Severity:** Major
  **Where:** Step 4, "reuse the `Clock` class ... and pass `now` explicitly", plus the whole `is_overdue(now)` design
  **What:** The `Clock` class belongs to the store (`EventStore` takes it). It is not used for `now`. The plan makes the CLI read `time.time()` directly. That is a second clock path outside the store's injectable clock, which architecture.md describes as how time is handled. This is a design choice that the plan never compares with the existing pattern.
  **Evidence:** `docs/architecture.md:49-50` ("stamps each event with the time from an injectable clock"). Plan line 9.

- **Severity:** Minor
  **Where:** Step 6, the line references (AGENTS.md:102, :114, :116; architecture.md:12, :94-96, :103)
  **What:** The architecture line numbers match (12, 94-96, 103). I did not verify the AGENTS.md lines beyond the "7 unittest cases" text and the Current state section. The test count is stated as something to update, but no new count is given.
  **Evidence:** `architecture.md:12`, `:94-96`, `:103` confirmed. The "Current state" text is in AGENTS.md.

- **Severity:** Minor
  **Where:** Headline and open question 5, "six spec changes"
  **What:** The table does have six rows, so the count is right. But step 1 also needs a TKT-001 or event-log change if CLI-009 is renumbered, and step 6 adds three more doc edits. The "blocking decision" understates the doc scope.
  **Evidence:** Plan lines 28-35 and 53-56.

- **Severity:** Minor
  **Where:** Step 3, `_line` helper and test-plan e2e comment "expect: #2 [P3] OVERDUE  Old P3"
  **What:** The helper pads `OVERDUE` to 8, so the output is `OVERDUE ` plus a space, i.e. two spaces before the title in the example only if padding is one char. `OVERDUE` is 7 characters, so the line shows 2 spaces. That matches the example. But `closed`/`assigned` rows keep their own padding, and the e2e `list` step has no expected line for #1's padding. It is fine, just underspecified.
  **Evidence:** `cli.py:30`, format `{t.state:<8}`.

- **Severity:** Minor
  **Where:** Out of scope / risks, "`overdue` inherits" the CLI-007 traceback
  **What:** The plan's `overdue` path calls `is_overdue` on every ticket. A ticket with an unknown priority in the log would raise `KeyError` from the new `OVERDUE_HOURS[...]` lookup instead of the existing `ValueError` from `due_at`. The failure mode of the same corrupt data changes. Reusing `t.due_at` removes this.
  **Evidence:** Plan line 39 against `sla.py:7-8`.

- **Severity:** Minor
  **Where:** Step 8 and the missing-log test
  **What:** The test "`overdue` on a missing log file prints nothing and exits 0" cites LOG-006. I did not check the missing-file behavior in the store spec, so treat it as unverified.
  **Evidence:** I did not open `event-log.md` LOG-006.

Baseline check: `make test` runs 7 tests and passes, as the plan says.
FINDINGS

- **Severity:** Blocker
  **Where:** Step 2, `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`
  **What:** The plan adds a second hours table, and its P3 value is wrong. TKT-005 and `SLA_HOURS` say P3 is 72 hours. The table also duplicates `sla.py`, even though `Ticket.due_at` is already computed on replay (A1 says so itself).
  **Evidence:** `sla.py:3` has `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`. `tickets.py:36` has `t.due_at = due_at(...)`. With the plan's table, a P3 ticket 60 hours old shows OVERDUE although it is not due until hour 72. The rule should be `now > t.due_at`, with no new table.

- **Severity:** Blocker
  **Where:** Step 2, `overdue()` sort key `(t.created_at, t.id)`
  **What:** The request, TKT-015 and the plan's own Headline say "sorted by due time". The code sorts by creation time, which is a different order.
  **Evidence:** A P3 created 80h ago is due 8h ago. A P1 created 50h ago is due 46h ago. By creation time the P3 comes first. By due time the P1 comes first. The key should be `(t.due_at, t.id)`.

- **Severity:** Blocker
  **Where:** Step 1 TKT-014 and open question 3 versus step 2 `is_overdue`
  **What:** The spec text and the test plan say a ticket is not overdue at the due time exactly. The code uses `now >= created_at + hours*3600`, which makes it overdue at that moment.
  **Evidence:** Step 1 says "At the due time exactly, it is not overdue". Step 2 has `now >= ...`. The unit test "not overdue ... at the due time exactly" would fail against this code.

- **Severity:** Major
  **Where:** Step 1 "CLI-009 (new)", and every later citation of CLI-009 (steps 8, test plan)
  **What:** CLI-009 already exists. It is "Ticket ID is an integer". The next free CLI number is CLI-010.
  **Evidence:** `docs/product-specs/cli.md` ends with `### CLI-009: Ticket ID is an integer`. `docs/README.md:27-28` says a new spec gets the next free number. Reusing the ID breaks stable IDs and makes citations ambiguous.

- **Severity:** Major
  **Where:** Step 5, step 7, and the conventions list ("the suite runs under `pytest`")
  **What:** The project uses `unittest`, not pytest. The plan relies on the pytest `tmp_path` fixture and on `pytest -q`. It also misquotes AGENTS.md as saying pytest.
  **Evidence:** `Makefile` runs `python3 -m unittest discover -s tests -q`. AGENTS.md has "Tests | `unittest`, `make test`". No pytest reference exists in the repo outside `plan.md`. pytest is also not a declared dependency, which conflicts with "Dependencies: None". `test_cli.py` should use `unittest` and `tempfile`, as `tests/test_tickets.py` does.

- **Severity:** Major
  **Where:** Assumptions A3 to A8, and the "scratch" evidence
  **What:** The evidence cannot be checked. `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py` do not exist in the repo. Several "confirmed" results rest on them.
  **Evidence:** `ls` of the repo shows `AGENTS.md docs Makefile plan.md pyproject.toml README.md tests ticketdesk`. There is no `scratch/` directory. Git status shows only `plan.md` as untracked.

- **Severity:** Major
  **Where:** A4 and the test "P1 created later before a P3 created earlier"
  **What:** The claimed result is wrong. The example is a P3 created 80h ago (ID 1) and a P1 created 6h ago (ID 2).
  **Evidence:** With the real SLA hours the P3 is due 8h ago and the P1 is due 2h ago. Due-time order is `[1, 2]`, the same as ID order. The plan's own created-time key also gives `[1, 2]`. The claimed `[2, 1]` cannot happen, so the example does not show that `overdue` needs its own sort. A valid example needs a later-created ticket with an earlier due time, for example a P1 created 50h ago next to a P3 created 60h ago, where the P3 is not yet due.

- **Severity:** Minor
  **Where:** Step 3, last bullet
  **What:** The stated reason for changing `else:` to `elif` is false. The subparsers are already required.
  **Evidence:** `cli.py:14` has `add_subparsers(dest="cmd", required=True)`. A missing command already exits 2 in argparse before the final `else`. The `elif` change is still a harmless guard, but the justification should go.

- **Severity:** Minor
  **Where:** Step 3 and Approach, `time.time()` in the CLI
  **What:** The project injects a clock (`EventStore(path, clock=time.time)`), and tests use a `Clock`. The plan reads wall time in the CLI and has to fake time with hand-written past `at` values in logs. It does not say why it diverges from the injected-clock pattern.
  **Evidence:** `store.py` `__init__(self, path, clock=time.time)`. The plan's A5 calls the hand-written log "the only black-box seam", which holds only because the CLI has no clock hook.

- **Severity:** Minor
  **Where:** Step 6 and Step 1 doc updates
  **What:** The doc update list is incomplete, and the line references are unchecked. `architecture.md` has the command list "create / assign / close / list" in the diagram around lines 12-13. The `cli.md` intro and the `docs/product-specs/README.md` feature index are not mentioned. The AGENTS.md "7 unittest cases" count has no new number.
  **Evidence:** `docs/architecture.md` diagram shows `create / assign / close / list`. The plan lists only "the arrow label" and the test-file lines. I did not check `docs/product-specs/README.md` or the root `README.md`, so the full list of places is unconfirmed.

- **Severity:** Minor
  **Where:** Headline, Falsifier section, open questions 1 and 2
  **What:** The `OVERDUE`-replaces-state format is already built into steps 1 to 3 and the tests. It hides `open` versus `assigned`, and every `overdue` line would say `OVERDUE`. The plan lists these as open questions, but also treats them as settled. The "Falsifier" section argues against a stored-event design that nobody proposed.
  **Evidence:** Open questions 1, 2 and 6 versus the CLI-006 and CLI-009 rows in the step 1 table.

I ran `make lint && make test` only as read-only checks and did not change anything.
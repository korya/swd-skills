# Review of plan.md (overdue tickets)

Checked against HEAD `ddc05e2`. The repo and plan were not modified. Ordered by severity.

## Critical

### 1. The hours table is duplicated and wrong (P3 = 48 instead of 72)
- plan.md:38 adds `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`.
- docs/product-specs/tickets.md:44 (TKT-005) and ticketdesk/sla.py:3 say P3 = 72.
- plan.md:30 defines overdue as "later than its due time (TKT-005)", so a P3 ticket would show OVERDUE 24 h early.
- The plan's own A1 (plan.md:69) says every ticket already carries `due_at` (tickets.py:21, :36). A second table is unnecessary and drifts from the first, as it already has.
- Fix: `is_overdue` should compare against `self.due_at`. Drop `OVERDUE_HOURS`.

### 2. The sort key contradicts TKT-015, and the plan's own example
- plan.md:40 sorts by `t.created_at`. plan.md:31 (TKT-015) and :34 say due time ascending.
- Creation order and due order differ across priorities. Example: P3 created 75 h ago is due at -3 h. P1 created 10 h ago is due at -6 h. By `created_at` the P3 ticket comes first, by due time the P1 ticket does.
- A4 (plan.md:72) claims a P3 created 80 h ago and a P1 created 6 h ago sort as `[2, 1]` by due time. That is wrong. P3 is due at -8 h and P1 at -2 h, so due order is `[1, 2]`, the same as ID order. It stays `[1, 2]` even with the plan's wrong 48 h (-32 h vs -2 h).
- So the example shows no difference between the sorts. The test at plan.md:118 ("P1 created later before P3 created earlier") would fail against the specified behavior. The ordering evidence is unsound.
- Fix: sort by `(t.due_at, t.id)`. Replace the test with a case that really differs: P3 created 75 h ago and P1 created 10 h ago, expecting P1 first.

### 3. Boundary is `>=` in code but "not overdue at exactly the due time" in spec and tests
- plan.md:39: `now >= created_at + ...`. plan.md:30, :114 and open question 3 (:178): at the due time it is not overdue.
- The unit test at plan.md:114 would fail on the plan's own code. It is an off-by-one.
- A6 (plan.md:74) claims `[]` at the due time was confirmed, which cannot be true with `>=`.
- Fix: use `>`.

### 4. The plan builds its tests on pytest, but the repo uses `unittest` and pytest is not installed
- plan.md:51 requires the pytest `tmp_path` fixture. plan.md:58 runs `pytest -q`. plan.md:90 claims the convention is "the suite runs under pytest".
- The repo says the opposite. Makefile:3 runs `python3 -m unittest discover -s tests -q`. AGENTS.md:22 and docs/architecture.md:80 say `unittest`, standard library only. ci.yml:11-12 runs `make lint` then `make test`, with no pip install.
- `python3 -m pytest` fails here with "No module named pytest".
- Consequences: `tests/test_cli.py` would not run in CI, or would need a new dev dependency that breaks the "Dependencies: None" rule (AGENTS.md:25). The step-7 verification is also not what CI runs.
- Fix: use `unittest` with `tempfile.TemporaryDirectory` (as tests/test_tickets.py:16-24 does). Verify with `make lint && make test`.

## High

### 5. New spec ID `CLI-009` already exists
- plan.md:34 and :62 add `CLI-009` for `overdue`. docs/product-specs/cli.md:58 already defines CLI-009 "Ticket ID is an integer".
- docs/README.md:27-28 says the next free number is used and IDs are never renumbered. The next free CLI number is CLI-010.
- The plan's claim at plan.md:98 that it follows this rule is false for CLI-009.
- Every later reference is wrong too: plan.md:128, :129, :62.
- Also, plan.md:5 and open question 5 (:180) both say "six spec changes". plan.md:98 says only three new IDs. The table has six rows, so the count is consistent, but the CLI-009 clash must be resolved before sign-off.

### 6. "Evidence" cites scratch scripts and experiments that do not exist
- plan.md:71-76 cite `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py` (E1 to E5, run on 3.12.16). There is no `scratch/` directory in the repo, and `git status` shows only `plan.md` untracked.
- A3, A4, A5, A6, A7 and A8 cannot be reproduced. Given findings 2 and 3 (A4 and A6 contradict the plan's own code), the results should not be trusted.
- Also, no Python 3.12 is guaranteed locally. The local python3 is 3.15.
- Fix: re-run the experiments and commit them or inline the commands.

### 7. A false premise drives step 3's argparse change
- plan.md:47 says "the subparsers are not marked required" and that a missing subcommand reaches the `else` branch.
- cli.py:14 has `required=True`, so a missing subcommand exits 2 in argparse before reaching that branch (CLI-001 holds).
- The `elif args.cmd == "list"` change is still harmless, but the stated reason is wrong. That suggests the code was not read closely.

## Medium

### 8. The spec-change table drifts from the existing spec text
- CLI-001 (cli.md:14) says "four subcommands" and lists them. The plan says "Four become five" (fine).
- LOG-001 (event-log.md:14-15) is edited only for wording. The plan treats it as a spec change, but it is a no-op that adds doc churn. docs/guidelines.md says no drive-by doc edits, so consider dropping it.

### 9. A user-visible contract change is shipped inside a feature
- Replacing the state in `list` (CLI-006, cli.md:41-43) hides `open` vs `assigned` for overdue rows. The plan lists this as open question 1 but still proceeds with it as the default (plan.md:176).
- The `overdue` command then prints a column that is always `OVERDUE` (open question 2). This is low-information. Better: keep the state and add a suffix or marker, or show the real state in `overdue`.
- Open questions 1, 2, 3, 4 and 6 gate the spec text, so the plan should block on them rather than assume answers.

### 10. The tests use the wall clock and time-dependent fixtures
- plan.md:124 and :139-142 write logs with `at = time.time() - N*3600`. The CLI reads `time.time()` itself (plan.md:46). Boundary cases cannot be tested through the CLI, and tests near a boundary are racy.
- Use large margins in the CLI tests, and keep the boundary tests in the unit suite with an explicit `now`.
- Related: `TicketService.overdue(now)` takes `now` from the caller while the store has an injectable clock (tests/test_tickets.py:8-21). Consider giving the service the same clock for consistency.

## Low

### 11. Minor inaccuracies and gaps
- Step 6 and the Risks section cite specific line numbers in AGENTS.md and architecture.md (AGENTS.md:102, :114, :116, architecture.md:94-96). AGENTS.md:22 and :47 also say `unittest`, which step 6 does not update.
- The plan updates the "7 unittest cases" count (AGENTS.md:102) but gives no new number.
- The plan commits in three commits (plan.md:60-63). The first mixes specs with the service. The second mixes the CLI with `LOG-001`. This is fine, but the docs commit would leave AGENTS.md stale between commits 2 and 3.
- The 1-second-advancing fake clock risk (plan.md:158) is real, but the mitigation is unclear for tests that use the `Clock` class.
- The CLI-007 traceback inheritance is noted correctly (plan.md:159), but an unknown priority in a hand-written log now crashes `list`. With the plan's `OVERDUE_HOURS[self.priority]` lookup, a `KeyError` could appear at a new place. Using `due_at` avoids this.

## Verdict
Do not implement as written. Findings 1 to 4 each break correctness or the test suite. Finding 5 breaks doc ID rules. Finding 6 means the plan's stated verification cannot be trusted.

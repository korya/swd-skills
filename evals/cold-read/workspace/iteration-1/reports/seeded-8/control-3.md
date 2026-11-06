# Review of plan.md (overdue tickets)

Checked against HEAD `ddc05e2`. The plan and the repo were not changed.

Summary: the derived-flag design is sound. Four details in the plan contradict the repo or the plan itself. Two of them would ship wrong behavior, and one would break CI.

## Critical

### 1. The plan invents a second SLA table with a wrong P3 value
- plan.md:38 adds `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`.
- `ticketdesk/sla.py:3` has `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`. TKT-005 (`docs/product-specs/tickets.md:44`) also says P3 is 72.
- The plan's rule is therefore wrong for every P3 ticket, which is the default priority (`cli.py:15`). A P3 ticket would show `OVERDUE` 24 hours early.
- It also breaks the plan's own stated rule. plan.md:30 and plan.md:9 define overdue against "its due time (TKT-005)".
- The rule needs no table. `Ticket.due_at` is already set at `tickets.py:36`, and plan A1 (plan.md:69) says so. Use `now > self.due_at`.
- Duplicating the table also violates "one source for hours" (plan.md:106 claims "keeps the hours table next to the rule", but no such duplicate is needed).
- Test blind spot: plan A4 (plan.md:72) uses a P3 ticket created 80 h ago, which is overdue under both 48 and 72. The planned unit tests probably use `due_at` boundaries, so a 48-versus-72 error could slip through in CLI tests unless a P3 case sits between 48 h and 72 h.

### 2. The overdue comparison contradicts the plan's own spec
- plan.md:30 (TKT-014) and plan.md:114 say that at the due time exactly, a ticket is not overdue.
- plan.md:39 implements `now >= created_at + ...`, so it is overdue at the due time exactly.
- Open question 3 (plan.md:178) also assumes "only after".
- The code in step 2 would fail the plan's own boundary test. It must be `now > due_at`.

### 3. The `overdue` sort uses the wrong key
- plan.md:40 sorts by `(t.created_at, t.id)`. TKT-015 (plan.md:31) and CLI-009 require due time, then ID.
- Creation order and due-time order differ across priorities. That difference is the point of A4 (plan.md:72).
- With the P3 ticket created 80 h ago and the P1 ticket created 6 h ago, the plan's own example would return `[1, 2]`. The test at plan.md:118 expects `[2, 1]`.
- Fix: key on `(t.due_at, t.id)`.

### 4. The plan uses pytest, which this repo does not use
- Plan step 5 (plan.md:51) uses the pytest `tmp_path` fixture. Step 7 (plan.md:58) runs `pytest -q`. The conventions line (plan.md:90) says the suite "runs under pytest".
- The repo is unittest only:
  - `AGENTS.md:22`
  - `docs/architecture.md:80`
  - `Makefile:3` (`python3 -m unittest discover -s tests -q`)
- pytest is not installed here. `import pytest` fails.
- `.github/workflows/ci.yml:11-12` runs only `make lint` and `make test`, and CI installs nothing. A `tmp_path` test would error at collection or fail.
- The "no dependencies" convention (`AGENTS.md:25`) is also at stake, because pytest would be a new dev dependency.
- Fix: use `unittest` with `tempfile.TemporaryDirectory`, as `tests/test_tickets.py:1-25` does. Run `make lint && make test`.
- The baseline in plan.md:78 says "ran 7 tests", which came from unittest. The plan then contradicts its own baseline.

## High

### 5. The new `CLI-009` collides with an existing ID
- `docs/product-specs/cli.md:58` already defines `CLI-009: Ticket ID is an integer`.
- plan.md:34 and plan.md:98 add a "new" CLI-009 and claim "next free number". The next free ID is `CLI-010`.
- Reusing the ID breaks the stable-ID rule (`docs/README.md:27-28`) and every later citation (plan.md:128, plan.md:129, plan.md:62).
- The tickets IDs are right. TKT-013 is the last one, so TKT-014 and TKT-015 are free.

### 6. The `else:` to `elif` rationale is false
- plan.md:47 says that "a missing subcommand also reaches that branch, because the subparsers are not marked required".
- `ticketdesk/cli.py:14` has `required=True`, so a missing command already exits 2 at parse time.
- The `elif` change is still harmless, but it rests on a wrong claim. It is also unrelated to the feature. `docs/guidelines.md:84-87` says not to bundle unrelated cleanup.
- Keep it only if it is justified correctly. Otherwise the final `else` becomes `list`/`overdue` branching.
- Note that without any change, a new `overdue` subcommand does fall into the `else` branch and prints the `list` output. The plan is right that this needs handling, but for a different reason.

### 7. The "verified" evidence cannot be reproduced
- plan.md:71, plan.md:73, plan.md:74 and plan.md:76 cite `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py`.
- Neither the files nor a `scratch/` directory exist. `git ls-files` lists no such path, and `git status` shows only `plan.md` untracked.
- A3 to A8 are therefore unverifiable by a reviewer. A5 and A8 claim runs on 3.12.16 that cannot be checked.
- Either commit the scripts or inline the commands and outputs.

## Medium

### 8. `CLI-006` and `LOG-001` changes widen the spec contract more than needed
- plan.md:33 changes the state column to `OVERDUE`, which loses `open` versus `assigned`. This is open question 1. Other options keep information: a suffix, or a separate column.
- Replacing the state also makes every line in `overdue` say `OVERDUE` (open question 2, plan.md:177), so the new command shows the user less than `list` does.
- The plan itself says this is the blocking decision. It should be decided before step 1, not assumed.
- plan.md:35 rewrites `LOG-001`. That edit is cosmetic and could be dropped. LOG-001 already says listing appends nothing, and `overdue` is a listing.
- "Six spec changes" (plan.md:5) includes that edit, so the sign-off ask could be smaller.

### 9. Clock handling bypasses the injectable clock
- plan.md:9 and plan.md:46 read `time.time()` in the CLI.
- `docs/architecture.md:50` says the clock is injected so tests stay deterministic. `docs/architecture.md:36-38` says the CLI holds no rules.
- The plan keeps the rule in the service, which is right. But the clock is read in the CLI, so the only CLI-level test seam is a log with old `at` values.
- A time-dependent CLI test is feasible only with real time. Test logs must use margins far from the boundary. The boundary is covered only in unit tests.
- Consider `TicketService(store, clock=...)` and `svc.overdue()` with no `now` argument. That would follow the store's pattern and avoid a per-row `now` argument.

### 10. The CLI integration tests need a `-I`-safe invocation
- plan.md:51 runs `python -m ticketdesk.cli` by subprocess. That needs the repo root as cwd or on `sys.path`. `make test` runs from the repo root, but the plan does not say so.
- Pass `cwd` explicitly. Also set `TICKETDESK_LOG` away from the real file. `DEFAULT_LOG` is read at import time (`cli.py:8`), which plan.md:108 notes.

### 11. The step ordering conflicts with the commit plan
- Step 8 (plan.md:60-63) puts specs plus the service rule in commit 1 and the CLI in commit 2.
- But `docs/guidelines.md:84-87` wants one logical change per commit. Commit 1 documents CLI-001/CLI-006 changes that land only in commit 2, so HEAD of commit 1 has specs that the code contradicts.
- Put each spec change in the same commit as its code.

## Low

### 12. Doc update line numbers
- plan.md:54-56 cites `architecture.md:94-96`, `architecture.md:103` and `AGENTS.md:102/114/116`. They match the repo as of HEAD.
- `docs/guidelines.md:11` also says the CLI "has no tests today. Confirm a target with the user and record it here." The plan does not update it. That line asks for a user decision on a coverage target, which adding `test_cli.py` touches.
- `AGENTS.md:117` ("Planned: nothing is recorded") and the "Done" list at `AGENTS.md:114` need `overdue`. Step 6 covers the latter.

### 13. Smaller points
- plan.md:20 says no version bump. That is reasonable, but plan.md:182 asks about it anyway. Drop the question or the claim.
- plan.md:158 flags the fake clock advancing on every read. That is correct (`tests/test_tickets.py:12-14`).
- Running on the local Python and 3.12 (plan.md:58) is fine, but CI only needs `make lint && make test`.
- plan.md:93 says guideline lines `guidelines.md:51-53` back the "CLI holds no rules" claim. The repo has the rule in `architecture.md:36-38`. Verify the second citation before relying on it.

## What holds up
- A derived flag with no new event kind fits INV-001, INV-002, LOG-001, LOG-002 and LOG-009 (plan.md:80-86). Overdue depends on `now`, so it must not be a state. The plan handles this.
- `Ticket.due_at` is already set at replay (`tickets.py:36`), so no store change is needed.
- The step 0 sign-off gate matches `AGENTS.md:93` and `docs/README.md:39-40`.

## Suggested fixes before implementation
1. Drop `OVERDUE_HOURS`. Use `now > t.due_at`.
2. Sort by `(t.due_at, t.id)`.
3. Switch the tests to unittest and keep `make test` as the runner.
4. Use `CLI-010` for the new command spec.
5. Fix or drop the `required=True` claim at plan.md:47.
6. Commit the scratch scripts or inline their output.
7. Add a P3 test between 48 h and 72 h old, which must not be overdue.

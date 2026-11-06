PARAPHRASE

The plan makes "overdue" a flag computed at read time. It adds no new state and no new event. A ticket is overdue if it is not closed and the current time is past its due time. `ticketdesk list` shows `OVERDUE` in place of the state for such tickets. A new `ticketdesk overdue` subcommand prints only those tickets, sorted by due time and then by ID. The work is gated on the user signing off six spec changes. It then covers the service rule, the CLI wiring, new unit tests, a first CLI subprocess suite, doc updates and three commits.

Per the plan, the system today has a service that replays the event log into tickets. Each replayed ticket has a creation time, a priority and a due time from `sla.py`. The CLI has four subcommands, and `list` prints in ID order with the state padded to 8 characters. The tests use a fake `Clock` in a `unittest`-style suite, but the plan also says the suite runs under `pytest`. The plan says the CLI has no tests and that a missing subcommand falls into the `list` branch. I can't paraphrase the `scratch/exp*.py` evidence in A3–A8, because the document gives no content for it beyond its own conclusions.

FINDINGS

- Severity: Blocker
  Where: Plan step 2, `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`
  What: This is a second, wrong copy of the SLA table. P3 is 48 here but 72 in the repo. It also duplicates `SLA_HOURS`, which contradicts the plan's own claim that "Step 2 keeps the hours table next to the rule" and that the SLA table stays untouched. P3 tickets would show OVERDUE 24 h early. The plan also contradicts its own TKT-014, which says overdue is measured against the due time in TKT-005.
  Evidence: `ticketdesk/sla.py:3` has `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`. `docs/product-specs/tickets.md:44` says P3 is 72. `Ticket` already carries `due_at` (`tickets.py:21,36`), so the rule should be `now > self.due_at`.

- Severity: Blocker
  Where: Step 2, `is_overdue` and `overdue()` sort key
  What: The comparison is `>=`, but TKT-014 in the same plan, the test plan and open question 3 all say "at the due time exactly, not overdue". At the boundary the code returns True and the planned boundary test fails.
  Evidence: Step 2 says `now >= self.created_at + ...`. Step 1 TKT-014 says "later than its due time… At the due time exactly, it is not overdue."

- Severity: Blocker
  Where: Step 2, `key=lambda t: (t.created_at, t.id)`
  What: The sort is by creation time, not by due time. The request says "oldest due first". Because the SLA hours differ by priority, the orders differ. For example, a P3 created at t=0 is due at 72 h and a P1 created at t=60 h is due at 64 h. Creation order puts the P3 first, but the P1 is due first. This contradicts TKT-015 in the same plan, which says "sorted by due time".
  Evidence: Step 2 sorts on `created_at`. `due_at` exists on `Ticket` (`tickets.py:21`).

- Severity: Major
  Where: A4, and the test-plan case "P1 created later before P3 created earlier (E3)"
  What: The worked example is miscomputed, and it is the sole justification for the dedicated sort. A P3 created 80 h ago is due 8 h ago (72 h SLA). A P1 created 6 h ago is due 2 h ago. Due-time order is therefore [1, 2], the same as ID order, not [2, 1]. The test built from it would not discriminate between a correct sort and an ID-order sort. (With the plan's wrong 48 h it is still [1, 2].)
  Evidence: Recomputed from `sla.py:3`. The plan states `[2,1]` by due time and `[1,2]` by ID.

- Severity: Major
  Where: Step 1, CLI-009 (new)
  What: CLI-009 already exists as "Ticket ID is an integer". The plan says "new IDs take the next free number", but the next free CLI number is CLI-010. Reusing CLI-009 breaks the stable-ID rule, and plan steps 5 and 8 and the test plan cite CLI-009 too.
  Evidence: `docs/product-specs/cli.md:58`. The rule is at `docs/README.md:27-28`.

- Severity: Major
  Where: Steps 5 and 7, "Conventions" bullet 1, "pytest `tmp_path`"
  What: The project uses `unittest`, `pytest` is not installed, and CI runs `make test`, which is `unittest discover`. A pytest-fixture suite and `pytest -q` won't run in the project's tooling or in CI. The conventions bullet "the suite runs under `pytest`" misquotes AGENTS.md.
  Evidence: `AGENTS.md:22-23` says "Tests | `unittest`, `make test`". `Makefile:3` runs `python3 -m unittest discover`. `python3 -c "import pytest"` fails. `ci.yml` runs only `make lint` and `make test`.

- Severity: Major
  Where: Assumptions A3 to A8, and the Plan step 3 test references
  What: The cited evidence files `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py` don't exist in the repo or its git status. The "Verified/confirmed" results can't be reproduced, and at least A4 is wrong (see above), so the other results need re-checking.
  Evidence: `ls scratch` gives "No such file or directory". `git status` shows only `plan.md` and the pycache directories as untracked.

- Severity: Minor
  Where: Step 3, last bullet, "Today a missing subcommand also reaches that branch, because the subparsers are not marked required."
  What: The factual claim is false, and the system-today description is wrong. The `else`→`elif` change is harmless but not needed for that reason.
  Evidence: `cli.py:14` has `add_subparsers(dest="cmd", required=True)`. CLI-001 already specifies exit 2 for no subcommand.

- Severity: Minor
  Where: Step 6, line references and the architecture/AGENTS claims
  What: This step doesn't mention the arrow label at `architecture.md:12` that lists the commands, or that architecture.md:89/92 list `SLA_HOURS` as a public name. If the plan reuses `SLA_HOURS` and `due_at`, no new public names are needed, but the plan as written adds a duplicate table, which makes this inconsistent.
  Evidence: `docs/architecture.md:12,89,92`.

- Severity: Minor
  Where: Step 1 LOG-001 change, and the Headline "six spec changes"
  What: Rewording LOG-001 is optional, because `overdue` is a listing command and the existing wording "Listing tickets appends nothing" arguably already covers it. This enlarges the sign-off surface for no behavior change.
  Evidence: `docs/product-specs/event-log.md:14-15`.

- Severity: Minor
  Where: Step 8, commit split
  What: Commit 1 changes the service and the specs, but the CLI-001, CLI-006 and CLI-009 spec edits are in commit 2. The first commit is incomplete without them, although it cites TKT-014 and TKT-015. The split is workable but not clean. The spec edits could go in their own commit.
  Evidence: Step 8 lists "TKT-014, TKT-015" for commit 1 and "CLI-001, CLI-006, CLI-009, LOG-001" for commit 2, while step 1 makes all six spec edits at once.

I checked the baseline claim: `make lint` passes and `make test` runs 7 tests, all OK. The existing `Clock` class and the cited line numbers in `tickets.py`, `cli.py` and `ci.yml` match.
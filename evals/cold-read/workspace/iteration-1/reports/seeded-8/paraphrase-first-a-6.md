PARAPHRASE

The plan proposes overdue as a flag derived at read time. It is not a new state or event kind. A ticket is overdue when it isn't closed and the clock is past its due time. `list` would show `OVERDUE` in the state column for those tickets. A new `overdue` subcommand would print the same line format, filtered and sorted by due time and then by ID. The plan puts the rule in `tickets.py` and the label choice in `cli.py`. It adds six spec changes that need sign-off first. It adds unit tests and a first CLI test suite, and it updates the architecture and agent docs.

According to the plan alone, the system replays an append-only log into tickets, each with a creation time, priority and due time. The service holds the rules, the CLI only prints, and the store knows nothing about tickets. Tests use a fake clock, and `list` is in ID order. The suite runs under pytest. Argparse subparsers are not marked required, so a missing command falls into the `list` branch. Everything the plan says about scratch experiments rests on `scratch/*.py` files.

FINDINGS

- Severity: Blocker
  Where: Step 2, `OVERDUE_HOURS = {"P1": 4, "P2": 24, "P3": 48}`
  What: The plan makes a second SLA table, and its P3 value is wrong. The spec says 72 hours for P3. The plan could instead use the existing `t.due_at`, which already holds the due time. With 48, every P3 ticket would show OVERDUE 24 hours too early. The table also duplicates `SLA_HOURS`, and TKT-005 would have two sources of truth.
  Evidence: `ticketdesk/sla.py:3` has `SLA_HOURS = {"P1": 4, "P2": 24, "P3": 72}`. `docs/product-specs/tickets.md:44` has `| P3 | 72 |`. Plan A1 itself says `tickets.py:35-36 sets t.due_at`.

- Severity: Blocker
  Where: Step 2, the `is_overdue` formula and the `overdue()` sort key
  What: The sort key is `(t.created_at, t.id)`, so it sorts by creation time and not by due time. A P1 ticket created later can be due before a P3 ticket created earlier. That is the plan's own E3 case, and creation order gets it wrong. The request says "oldest due first".
  Evidence: Plan step 2: `key=lambda t: (t.created_at, t.id)`. Plan TKT-015: "sorted by due time ascending". Test plan: "returns a P1 ticket created later before a P3 ticket created earlier". With this key the P3 ticket sorts first, so the test would fail. `due_at` is on `Ticket` (`tickets.py:21`).

- Severity: Blocker
  Where: Step 2 (`now >= ...`) against step 1 TKT-014 and open question 3
  What: The code treats a ticket as overdue at the due time exactly. The spec, the unit test and the open question all say it is not overdue until after the due time.
  Evidence: Step 2: `now >= self.created_at + ...`. TKT-014: "At the due time exactly, it is not overdue." Test plan: "not overdue ... at the due time exactly". Open question 3: "only after it".

- Severity: Major
  Where: Step 1, `cli.md` CLI-009 (new)
  What: CLI-009 is already taken, and the plan says a new spec takes the next free number. The next free number is CLI-010. Reusing 009 would break the rule that IDs are stable and unique. It would also leave "Ticket ID is an integer" with a conflicting ID.
  Evidence: `docs/product-specs/cli.md:58` has `### CLI-009: Ticket ID is an integer`. Plan "Project conventions": "step 1 adds TKT-014, TKT-015, and CLI-009". `docs/README.md` says "A new spec gets the next free number."

- Severity: Major
  Where: Step 5, step 7, Project conventions line 1, A-table evidence
  What: The plan assumes a pytest suite, but the project is unittest-only. `make test` runs `unittest discover`. Pytest is not a declared dependency, and CI runs `make test`. The plan's `tmp_path` fixture and `pytest -q` would not run under `make test`, and CI would never run `test_cli.py` properly. The claim "AGENTS.md:22-23, Makefile:1-5: the suite runs under pytest" is false. It also conflicts with the plan's own "no dependencies" convention.
  Evidence: `Makefile:3` has `python3 -m unittest discover -s tests -q`. `AGENTS.md` says "Tests | unittest, make test". `ci.yml` runs `make test`.

- Severity: Major
  Where: Step 3, last bullet
  What: The plan says a missing subcommand falls into the `else: list` branch because subparsers aren't required. That is false. They are marked required, so a missing command exits 2 at parse time. The change to `elif args.cmd == "list"` is still harmless. The stated reason is wrong, and so is the "Today..." premise.
  Evidence: `ticketdesk/cli.py:14` has `add_subparsers(dest="cmd", required=True)`.

- Severity: Major
  Where: Assumptions validated, A3 to A8, and Headline "two verified facts"
  What: The evidence cites `scratch/exp1_crafted_log.py` and `scratch/exp2_clock_and_argparse.py`. Neither exists in the repo, and `scratch/` doesn't exist. The experiments can't be reproduced or checked. A3's `'#1 [P1] OVERDUE  title'` output cannot be checked either.
  Evidence: `ls scratch` fails with "No such file or directory". `git status` shows only `plan.md` untracked. This likely also explains why the experiments missed the P3=48 error.

- Severity: Minor
  Where: Step 2, `TicketService.overdue`, and "CLI-006 ... padding to 8 characters"
  What: `OVERDUE` is 7 characters, so padding to 8 works. The CLI-006 change should also say `list` still gets ID order from the service. That much is consistent.
  Evidence: No contradiction found. This is noted only to show I checked it.

- Severity: Minor
  Where: Step 6, architecture.md and AGENTS.md line references; `sla.py` in the architecture doc
  What: The doc updates cover the arrow label and the test notes, but not the architecture file's `sla.py` entry, and they would drop the "known conflict" line. They also leave the "make test # 7 unittest cases" line stale, since the count changes. Line numbers (AGENTS.md:102, 114, 116) look plausible, but I did not check each one.
  Evidence: `docs/architecture.md` says `create / assign / close / list` in the arrow label. `AGENTS.md` says "make test # 7 unittest cases".

DECISIONS LEFT TO THE NEXT READER WITHOUT SAYING SO

- Whether `OVERDUE` needs a doc update to the `list` header or column name. The plan has no step for this.
- How `overdue` should treat a ticket with an unknown priority in the log. The plan's `OVERDUE_HOURS[self.priority]` would raise `KeyError`, and that would differ from the traceback the plan says `overdue` "inherits".
- Which test runner the new CLI suite should use. The plan says pytest and the repo uses unittest. The plan doesn't notice that this is a decision.
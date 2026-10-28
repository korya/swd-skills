# Plan: overdue tickets in ticketdesk

## Headline

Overdue becomes a flag that the service derives at read time, never a new state or event. `ticketdesk list` shows `OVERDUE` in the state column, and a new `ticketdesk overdue` lists only overdue tickets by due time. The blocking decision is your sign-off on six spec changes, because the `list` output format is a user-visible contract.

## Approach summary

The ticket service in `ticketdesk/tickets.py` gains the overdue rule. A ticket is overdue when it is not closed and the current time is later than its due time. The service reads the current time from the store's injectable clock, the same clock that stamps events. The CLI in `ticketdesk/cli.py` reads that time once per command and passes it to the rule for every row.

`list` keeps its ID order and its line shape, and only the state column changes for overdue rows. The new `overdue` subcommand prints the same line shape, filtered to overdue tickets and sorted by due time, then by ID. The store, the SLA table, and the log format stay untouched, and no command appends an event for overdue. The plan rests on two verified facts. Every replayed ticket already has a due time, and tests can control time through the fake clock or a hand-written log. The main trade-off is that `list` hides whether an overdue ticket is `open` or `assigned`, see open question 1.

## Out of scope

- An `overdue` event kind, a stored overdue flag, or any change to `ticketdesk/store.py`.
- Notifications, "due soon" warnings, business-hours SLA, and per-ticket due times.
- A `--now` option or any other way for a user to set the clock on the command line.
- Showing the due time or the lateness in the output.
- The open TODO under CLI-007. An unknown priority or a corrupt log line still escapes as a traceback, and `overdue` inherits this.
- A version bump of `pyproject.toml` from 0.3.0. The repo records no rule for it, see open question 7.

## Plan

0. **Get sign-off on the spec changes before code work starts.** The table under step 1 lists them. AGENTS.md:93 and docs/README.md:39-40 require user confirmation for every doc change.

1. **Update the product specs** after sign-off. New IDs take the next free number per docs/README.md:27-28.

   | Spec | Change |
   |------|--------|
   | `tickets.md` TKT-014 (new) | A ticket is overdue when it is not `closed` and the current time is later than its due time (TKT-005). At the due time exactly, it is not overdue. Overdue is not a state (TKT-001) and is never recorded in the log. |
   | `tickets.md` TKT-015 (new) | Listing overdue tickets returns only overdue tickets, sorted by due time ascending, then by ID ascending. |
   | `cli.md` CLI-001 | Four subcommands become five: add `overdue`. |
   | `cli.md` CLI-006 | For an overdue ticket, the state column shows `OVERDUE` in place of the state. The padding to 8 characters stays. |
   | `cli.md` CLI-010 (new) | `ticketdesk overdue` prints one line per overdue ticket in TKT-015 order, in the CLI-006 line format. With no overdue tickets it prints nothing and exits 0. |
   | `event-log.md` LOG-001 | "Listing tickets appends nothing" becomes "Listing tickets, overdue tickets included, appends nothing." |

2. **Add the overdue rule to `ticketdesk/tickets.py`.**
   - `Ticket.is_overdue(self, now) -> bool` returns `self.state != "closed" and now > self.due_at`. Comment it `# implements TKT-014`.
   - `TicketService.now(self)` returns `self.store.clock()`. This keeps the store's clock as the only time source, per architecture.md:68-69.
   - `TicketService.overdue(self, now)` returns `sorted((t for t in self._tickets().values() if t.is_overdue(now)), key=lambda t: (t.due_at, t.id))`. Comment it `# implements TKT-015`.
   - `TicketService.list()` and the `Ticket` fields stay unchanged, so TKT-013 and LOG-009 hold.

3. **Wire the CLI in `ticketdesk/cli.py`.**
   - Add `sub.add_parser("overdue")` next to `list` at cli.py:18.
   - Add a helper `_line(t, now)` that returns `f"#{t.id} [{t.priority}] {label:<8} {t.title}"`, where `label` is `"OVERDUE"` if `t.is_overdue(now)` else `t.state`. The CLI picks the label. The rule stays in the service.
   - In the `list` and `overdue` branches, call `now = svc.now()` once, then print `_line` for each ticket from `svc.list()` or `svc.overdue(now)`.
   - Change the final `else:` at cli.py:28 to `elif args.cmd == "list":`, so a new subcommand never falls into `list` by accident.

4. **Add unit tests to `tests/test_tickets.py`.** The cases are under "Test plan". They reuse the `Clock` class at tests/test_tickets.py:8-14 and pass `now` explicitly.

5. **Add `tests/test_cli.py`, the first CLI test suite.** It runs `python -m ticketdesk.cli --log <tmp>` by subprocess against a hand-written log with past `at` values. The cases are under "Test plan".

6. **Update the architecture and agent docs** after sign-off.
   - architecture.md:12: add `overdue` to the arrow label.
   - architecture.md:68-69: state that the service also reads the current time from the store's clock to decide overdue.
   - architecture.md:94-96 and architecture.md:103: add `tests/test_cli.py` and remove "The CLI is not covered by tests today".
   - AGENTS.md:102, AGENTS.md:114 and AGENTS.md:116: update the test count, add `overdue` to the "Done" list, and remove "Not covered by tests: the CLI".

7. **Run `make lint && make test`** on the local Python and on Python 3.12, the CI version at .github/workflows/ci.yml:10.

8. **Commit in three logical changes**, each citing its spec IDs per guidelines.md:84-87.
   - The specs and the service rule with its unit tests: TKT-014, TKT-015.
   - The CLI subcommand, the `list` label, and `tests/test_cli.py`: CLI-001, CLI-006, CLI-010, LOG-001.
   - The architecture and AGENTS.md updates.

## Assumptions validated

| # | Assumption | Class | Evidence | Result |
|---|-----------|-------|----------|--------|
| A1 | Every replayed ticket already carries its due time. | Verified | tickets.py:35-36 sets `t.due_at = due_at(ev["at"], ev["priority"])`. sla.py:9 adds hours × 3600. | confirmed |
| A2 | The store's clock is injectable and readable by the service. | Verified | store.py:14-16 stores `clock` as a public attribute. The service holds `self.store` at tickets.py:27-28. | confirmed |
| A3 | `OVERDUE` fits the 8-character state column without moving the title. | Plausible | `scratch/exp1_crafted_log.py` E2 printed `'#1 [P1] OVERDUE  title'` and `'#1 [P1] assigned title'`. The title starts at the same column. | confirmed |
| A4 | Due-time order differs from ID order, so `overdue` needs its own sort. | Plausible | E3: a P3 ticket created 80 h ago (ID 1) and a P1 ticket created 20 h ago (ID 2) sort as `[2, 1]` by due time and `[1, 2]` by ID. | confirmed |
| A5 | A test can drive the real CLI with tickets that are already past due. | Risky | E1: a hand-written log with `at` values in the past ran through `python -m ticketdesk.cli list` with exit 0 and empty stderr. The CLI has no clock option, so this is the only black-box seam. | confirmed |
| A6 | Unit tests can place the fake clock at the exact due time. | Plausible | `scratch/exp2_clock_and_argparse.py` E4 set `clk.now = due_at - 1`. Results: `[]` at the due time, `[1]` one second later, `[]` after close. | confirmed |
| A7 | argparse accepts a fifth subparser and still exits 2 on a missing or unknown command (CLI-001). | Plausible | E5: `overdue` parsed. `bogus` and no command both exited 2. The usage line listed `overdue`. | confirmed |
| A8 | A1 to A7 hold on the CI Python. | Plausible | Both scratch scripts ran again on Python 3.12.16 with the same results. The only difference is the quoting in the argparse usage line. | confirmed |

Baseline before any change: `make lint` passed and `make test` ran 7 tests with `OK` on HEAD `7701ed3`.

**Falsifier.** The derived-flag shape is wrong if overdue must be stored, as an event kind or as a TKT-001 state. The specs refute that alternative:

- LOG-001 at event-log.md:14-15 says listing appends nothing. A stored overdue event could only come from a read command, because no process runs between invocations (architecture.md:7).
- LOG-002 at event-log.md:19 fixes the event kinds at `created`, `assigned`, `closed`.
- LOG-009 at event-log.md:58-59 requires replay to yield the same states every time. A state that depends on the wall clock breaks it.

Result: the falsifier did not fire. The derived flag is the only shape that upholds all three specs.

## Project conventions to follow

- **[AGENTS.md:22-23, Makefile:1-5]** Convention: *`make test` runs unittest discovery and `make lint` runs `compileall`.* **Reflected in plan:** step 7 runs both. Step 5 puts the new suite under `tests/` so discovery finds it.
- **[AGENTS.md:25, architecture.md:76]** Convention: *no dependencies beyond the standard library.* **Reflected in plan:** steps 2 to 5 use only `argparse`, `subprocess`, `tempfile`, and `json`.
- **[pyproject.toml:5, ci.yml:10]** Convention: *Python 3.11 or later, CI on 3.12.* **Reflected in plan:** no syntax newer than 3.11. Step 7 runs on 3.12, and A8 already did.
- **[architecture.md:36-38, guidelines.md:51-53]** Convention: *the CLI holds no ticket rules. A rule in the CLI is a layer crossing.* **Reflected in plan:** step 2 puts the rule in `Ticket.is_overdue`. Step 3 lets the CLI choose only the label.
- **[architecture.md:48-50, architecture.md:68-69, INV-005]** Convention: *time comes from the store's clock, never from the caller.* **Reflected in plan:** step 2 adds `TicketService.now()`, which reads `self.store.clock()`. The CLI never calls `time.time()`.
- **[tests/test_tickets.py:8-21]** Convention: *tests inject a fake clock. No mocking library is used.* **Reflected in plan:** step 4 reuses `Clock` and passes `now` as a plain number.
- **[guidelines.md:29-34]** Convention: *name the test files, the cases, and the test type, and name the e2e command sequences.* **Reflected in plan:** the test plan below.
- **[AGENTS.md:60-61, AGENTS.md:96]** Convention: *cite spec IDs in code comments, tests, and commits.* **Reflected in plan:** steps 2, 4, 5, and 8.
- **[AGENTS.md:93, docs/README.md:39-40]** Convention: *every doc change needs user confirmation.* **Reflected in plan:** step 0 gates steps 1 and 6.
- **[docs/README.md:27-28]** Convention: *IDs are stable, and a new spec takes the next free number.* **Reflected in plan:** step 1 adds TKT-014, TKT-015, and CLI-010.
- **[cli.py:15-18, cli.py:30]** Existing pattern: *one subparser per line and one f-string per output line.* **Reflected in plan:** step 3 follows it and reuses the CLI-006 format string.
- **Migrations.** They do not constrain this plan. No event kind or field changes, and architecture.md:44 says rules need no data migration.
- **Package manager, ports, URLs, and async work.** They do not constrain this plan. The tool is a local CLI with one command per invocation and no lockfile.

**Codebase sweep.**

- In-flight work: the repo has one commit (`7701ed3`), one branch (`main`), and no stash.
- Duplicate logic: no overdue code exists. Step 2 reuses `sla.due_at` through the replayed `due_at`, and the sort pattern at tickets.py:46-47.
- Callers of changed contracts: `svc.list()` has one caller at cli.py:29. `Ticket` is built only at tickets.py:35. The `list` output format may have external consumers, see open question 6.
- Test infrastructure: no CLI tests exist (architecture.md:103). Step 5 builds the first suite. `DEFAULT_LOG` is read at import time at cli.py:8, so CLI tests pass `--log` and never rely on `TICKETDESK_LOG`.

## Test plan

**Unit, through the service, in `tests/test_tickets.py`.**

- A ticket is not overdue one second before its due time and at the due time exactly (TKT-014 boundary).
- A ticket is overdue one second after its due time.
- An `assigned` ticket past its due time is overdue.
- A `closed` ticket past its due time is not overdue, including one closed after it became overdue.
- `overdue(now)` returns a P1 ticket created later before a P3 ticket created earlier, matching E3 (TKT-015).
- Two tickets with the same due time come back in ID order (TKT-015 tie-break).
- `overdue(now)` on an empty log returns an empty list (LOG-006).
- `list()` keeps ID order with overdue tickets present (TKT-013).
- `list()` and `overdue(now)` append no event. The replay length stays the same (LOG-001).
- `TicketService.now()` returns the value of the injected clock.

**Integration, by subprocess through the CLI, in `tests/test_cli.py`.** Each case writes a log with past `at` values, as in E1.

- `list` prints `OVERDUE` for an overdue `open` ticket and an overdue `assigned` ticket (CLI-006).
- `list` prints `closed` for a closed ticket past its due time, and the plain state for a ticket that is not yet due.
- `overdue` prints only the overdue lines, in due-time order, with exit 0 and empty stderr (CLI-010, CLI-008).
- `overdue` on a missing log file prints nothing and exits 0 (LOG-006, CLI-010).
- `bogus` exits 2, and the usage on stderr names `overdue` (CLI-001).
- `list` and `overdue` leave the bytes of the log file unchanged (LOG-001, INV-002).

**End to end, by hand against a temporary log.**

```bash
LOG=$(mktemp -d)/t.jsonl
python3 -m ticketdesk.cli --log "$LOG" create "Fresh P1" --priority P1
python3 -m ticketdesk.cli --log "$LOG" overdue          # expect no output, exit 0
python3 - "$LOG" <<'EOF'                               # append a ticket created 100 h ago
import json, sys, time
with open(sys.argv[1], "a") as f:
    f.write(json.dumps({"kind": "created", "id": 2, "title": "Old P3", "priority": "P3", "at": time.time() - 100*3600}, sort_keys=True) + "\n")
EOF
python3 -m ticketdesk.cli --log "$LOG" list             # expect: #1 open, #2 OVERDUE
python3 -m ticketdesk.cli --log "$LOG" assign 2 dana
python3 -m ticketdesk.cli --log "$LOG" overdue          # expect: #2 [P3] OVERDUE  Old P3
python3 -m ticketdesk.cli --log "$LOG" close 2 "Replaced the toner cartridge"
python3 -m ticketdesk.cli --log "$LOG" overdue          # expect no output
python3 -m ticketdesk.cli --log "$LOG" list             # expect: #2 closed
```

**Manual.** Run `ticketdesk --help` and `ticketdesk overdue --help` from the installed entry point (pyproject.toml:8) and read the usage text.

## Risks and mitigations

- **Scripts that parse `list` output may break.** A script that greps for `open` or `assigned` stops seeing overdue tickets. Mitigation: the spec sign-off in step 0 and open question 6.
- **A wrong system clock gives wrong overdue results.** Nothing reports it, because the tool trusts the machine's clock. Mitigation: none in scope. The risk is the same as for the `at` stamps today.
- **The fake clock advances by one second on every read** (tests/test_tickets.py:12-14). A test that calls `now()` and then asserts on an event time may be off by one. Mitigation: unit tests pass `now` explicitly and set `clk.now` directly.
- **`overdue` on a corrupt log prints a traceback with exit 1**, like every other command today. Mitigation: none in scope. The CLI-007 TODO tracks it.
- **Cost stays one full replay per command**, the same as `list` (architecture.md:62-63). The filter and the sort add work linear in ticket count plus a sort.

## Counterfactual

Verdict: **Confirmed with gaps.** Every success criterion has a plan step. The gaps are format choices that wait on open questions 1 and 2.

| Success criterion | Plan steps | Proof that it fails |
|-------------------|-----------|---------------------|
| A ticket past its due time shows `OVERDUE` in `list` | 2, 3 | A unit or CLI test sees the plain state for a past-due ticket |
| `ticketdesk overdue` exists and exits 0 | 3 | The CLI test for exit 0 or for usage fails |
| `overdue` lists only overdue tickets | 2, 3 | A closed or not-yet-due ticket appears in the CLI test |
| `overdue` lists the oldest due time first | 2 | The P1-before-P3 test returns ID order |
| No regression in log, order, or invariants | 2, 4, 5, 7 | The log bytes change, `list` leaves ID order, or the 7 existing tests fail |

## Open questions

1. **Should `list` replace the state with `OVERDUE`, or keep the state and add a marker?** Replacing hides `open` against `assigned` for overdue rows. A marker such as `open*` or a trailing column changes the line shape more. *Assumption:* replace the state, because it is the literal reading of the request and keeps the column layout.
2. **What should each `overdue` line show?** Reusing the `list` format means every line says `OVERDUE`, which carries no extra information. Showing the underlying state or the lateness would add information. *Assumption:* reuse the CLI-006 format, so one formatter and one parser cover both commands.
3. **Is a ticket overdue at its due time exactly, or only after it?** *Assumption:* only after it, from "pass their due time" in the request.
4. **Can a closed ticket be overdue?** *Assumption:* no. Closing ends the SLA clock, even when the ticket closed late.
5. **Do you approve the six spec changes in step 1 and the doc updates in step 6?** *Assumption:* none. This is the blocking gate, and no code work starts without it.
6. **Does any script or person parse `ticketdesk list` output today?** *Assumption:* no known consumer exists, because the repo documents none. The CLI-006 change goes ahead after sign-off.
7. **Does this feature bump the version from 0.3.0?** *Assumption:* no bump in this change, because the repo records no versioning rule.
8. **Should the CLI-007 TODO be fixed in the same change?** *Assumption:* no. It is a separate decision and stays out of scope.

# Plan: overdue tickets in ticketdesk

## Headline

Overdue becomes a read-time check on the due time each ticket already has, with no change to the log.
`ticketdesk list` shows `OVERDUE` in the state column, and a new `ticketdesk overdue` prints only overdue tickets, earliest due first.
Implementation waits on your approval of the spec edits and of the display choice in open questions 1 and 6.

## Approach summary

Every ticket already gets a due time when the service replays the log (`ticketdesk/tickets.py:35-36`).
The `Ticket` class gains `is_overdue(now)`, which is true for a ticket that is not closed and is past its due time.
`TicketService` gains `now()`, which reads the store's clock, and `overdue()`, which sorts overdue tickets by due time, then by ID.
The CLI asks the service for the time once per command and prints `OVERDUE` in place of the state.
The store, the event kinds, the log format, and `sla.py` stay untouched.

Overdue status depends only on the due time and the current time, so the plan writes nothing to the log.
The store's injectable clock gives tests a controllable current time.
The cost is that `list` hides whether an overdue ticket is `open` or `assigned`.
We accept it because the request says "show as OVERDUE" and the label fits the 8-character column.
Open question 1 asks you to confirm this choice.

## Out of scope

- A persisted overdue state, an `overdue` event kind, or any other change to the log format.
- Business hours, time zones, or per-customer due times. `sla.py` stays a plain table.
- Reporting tickets that were closed after their due time.
- The open CLI-007 conflict. A corrupt log or an unknown priority still ends in a traceback with exit code 1, also for `overdue`.
- Notifications, a non-zero exit code when overdue tickets exist, or new options on `overdue`.
- A version bump or a release of the package.

## Plan

The steps below follow the commit rule in `docs/guidelines.md:84-87`. Steps 1 and 2 are one commit, steps 3 to 5 are one commit, and step 6 is one commit.

1. **Spec edits, after your approval.** Edit `docs/product-specs/tickets.md` and `docs/product-specs/cli.md`. New IDs take the next free number per `docs/README.md:27-28`.
   - Add `TKT-014: Overdue tickets`. A ticket is overdue when its state is `open` or `assigned` and the current time is later than its due time (TKT-005). At the due time exactly, the ticket is not overdue. A `closed` ticket is never overdue. Being overdue is not a state, and nothing about it is written to the log.
   - Add `TKT-015: Overdue listing`. Listing overdue tickets returns only overdue tickets, sorted by due time ascending, then by ID ascending.
   - Amend `CLI-001` from four to five subcommands. Add `overdue`.
   - Amend `CLI-006`. The state column shows `OVERDUE` for a ticket that is overdue per TKT-014.
   - Add `CLI-010: overdue`. `ticketdesk overdue` prints one line per overdue ticket in TKT-015 order, in the CLI-006 line format. With no overdue tickets it prints nothing and exits with code 0.
2. **Event log wording, after your approval.** In `docs/product-specs/event-log.md`, amend `LOG-001` to say that listing tickets and listing overdue tickets append nothing.
3. **Service rule.** In `ticketdesk/tickets.py`:
   - Add `Ticket.is_overdue(self, now)` with the comment `# implements TKT-014`. It is a method, not a dataclass field, so replay output stays independent of time (LOG-009).
   - Add `TicketService.now(self)`, which returns `self.store.clock()`.
   - Add `TicketService.overdue(self, now=None)`. It uses `self.now()` when `now` is `None`, filters `self._tickets()` with `is_overdue`, and sorts by `(t.due_at, t.id)`. Add the comment `# implements TKT-015`.
   - Leave `list()`, `_tickets()`, `create()`, `assign()`, and `close()` unchanged.
4. **CLI.** In `ticketdesk/cli.py`:
   - Add a helper `_line(t, overdue)` that returns `#<id> [<priority>] <label> <title>`, with the label padded to 8 characters. The label is `OVERDUE` when `overdue` is true and `t.state` otherwise. It replaces the f-string at `ticketdesk/cli.py:30`, so both commands share one line format.
   - Register `sub.add_parser("overdue")` next to `list` at `ticketdesk/cli.py:18`.
   - In the `list` branch, call `svc.now()` once, then print `_line(t, t.is_overdue(now))` for each ticket.
   - Add an `overdue` branch that prints `_line(t, True)` for each ticket from `svc.overdue()`.
   - Keep the `TicketError` handling as it is.
5. **Tests.** Add the unit cases to `tests/test_tickets.py` and create `tests/test_cli.py`. The test plan below lists the cases.
6. **Docs that describe the command set, after your approval.**
   - `docs/architecture.md:12` lists the service calls as `create / assign / close / list`. Add `overdue`.
   - `docs/architecture.md:68-69` says time comes from the store's clock. Add one sentence that the service also reads "now" from that clock.
   - `docs/architecture.md:103` and `AGENTS.md:116` say the CLI has no tests. Update both.
   - `AGENTS.md:102` says `make test` runs 7 cases. Update the count. `AGENTS.md:114` lists the done commands. Add `overdue`.
7. **Check.** Run `make lint && make test` locally. CI then runs the same two commands on Python 3.12.

## Assumptions validated

### Load-bearing assumptions

- **Every ticket already has a due time after replay.** Confirmed. `ticketdesk/tickets.py:35-36` sets `due_at` from `sla.due_at` (`ticketdesk/sla.py:6-9`) for every `created` event.
- **The store's clock is a public, injectable attribute that the service can read.** Confirmed. `ticketdesk/store.py:14-16` stores it as `self.clock`. A prototype that called `self.store.clock()` ran the full suite green.
- **Tests can move "now" past a due time.** Confirmed. The fake clock in `tests/test_tickets.py:8-14` returns `now + 1` on every call and accepts a new `now`. A probe set the clock so the next call returned the due time. The output was the following.

  ```
  created_at 1700000001.0 due_at 1700014401.0
  at due_at exactly -> overdue? []
  one second later -> overdue? [1]
  after close -> overdue? []
  ```

- **A hand-written log with an old `at` replays normally.** Confirmed. Replay does not check timestamps (`ticketdesk/store.py:25-36`). With a seeded log, the unchanged CLI printed `#1 [P1] open     Old P1` for a ticket with `at` 1000. This makes CLI tests deterministic without a wait of 4 hours.
- **`OVERDUE` fits the 8-character state column.** Confirmed. `f"{'OVERDUE':<8}|"` prints `'OVERDUE |'`, so titles stay aligned with `open` and `assigned` lines.
- **Read commands append nothing.** Confirmed on the prototype. The SHA-1 of the seeded log was the same before and after `list` and `overdue`.
- **The order is due time first, then ID.** Confirmed on the prototype. The seeded log had due times of 260200, 16400, 186400, and 186400 for tickets 1, 2, 5, and 6. `overdue` printed tickets 2, 5, 6, and 1.
- **A missing log needs no special case.** Confirmed. On the prototype, `overdue` with a missing log printed nothing, exited with code 0, and created no file (LOG-006).
- **Subprocess CLI tests run under `make test`.** Confirmed. A prototype `tests/test_cli.py` ran green from the repo root on Python 3.12, the CI version, and on Python 3.15.
- **A corrupt log still escapes as a traceback.** Partial. The prototype `overdue` on a corrupt log exited with code 1 and a `ValueError` traceback. This is the known CLI-007 conflict, and this plan leaves it out of scope.

### Hypothesis and its falsifier

The hypothesis is that overdue status is derived at read time and never stored.
It would be the wrong shape if overdue status had to persist after a ticket closes. It would also be wrong if the status had to appear in the log.

The specs rule out both cases. LOG-001 says listing appends nothing. LOG-002 fixes the three event kinds. LOG-009 requires replay to give the same tickets every time, which a stored time-dependent flag would break.

The alternatives considered were the following.

- An `overdue` event appended when a read notices the due time passed. Rejected because it makes `list` write, against LOG-001 and LOG-002.
- An `overdue` field set inside `_tickets()`. Rejected because replay output would change with the clock, against LOG-009. Also `_tickets()` has no "now".
- A `time.time() > t.due_at` check inside `cli.py`. Rejected because a ticket rule in the CLI is a layer crossing (`docs/guidelines.md:51-53`, `docs/architecture.md:36-38`). It also adds a second time source, against `docs/architecture.md:68-69`.
- A clock passed to the `TicketService` constructor. Kept as the fallback. It changes the constructor for no gain while the store already holds the clock.

### Spec cross-check

- **TKT-001, ticket states.** Upheld. `Ticket.state` keeps its three values. `OVERDUE` is a display label from step 4, defined in step 1.
- **TKT-005, due time.** Reused as is in step 3.
- **TKT-013, listing order.** Upheld. `list()` is unchanged.
- **CLI-001 and CLI-006.** Changed by step 1. Both changes need your approval.
- **CLI-007.** Not changed. `overdue` raises no new `TicketError`. It inherits the open TODO.
- **CLI-008, success exit code.** Upheld. The prototype `overdue` exited with code 0 and wrote 0 bytes to stderr.
- **LOG-001, LOG-002, LOG-009.** Upheld by steps 3 and 4. Step 2 only clarifies LOG-001 wording.
- **INV-001 and INV-002.** Upheld. No new file, cache, or event.
- **INV-005.** Upheld. No event gets a new timestamp, and "now" comes from the store's clock.
- **INV-003 and INV-004.** Not affected.

### Project conventions to follow

- **[`AGENTS.md:88-89`, `docs/guidelines.md:12-13`]** Convention: run `make lint && make test` before every push. **Reflected in plan:** step 7.
- **[`AGENTS.md:93`, `docs/README.md:39-40`, `docs/guidelines.md:45-47`]** Convention: doc and spec changes need user confirmation. **Reflected in plan:** steps 1, 2, and 6 wait for approval, see open question 6.
- **[`AGENTS.md:96`, `docs/README.md:43-44`]** Convention: cite spec IDs in code comments, tests, and commits. **Reflected in plan:** the comments in step 3 and the test names in the test plan cite TKT-014, TKT-015, and CLI-010.
- **[`docs/README.md:27-28`]** Convention: IDs are stable, and a new spec gets the next free number. **Reflected in plan:** step 1 uses TKT-014, TKT-015, and CLI-010 and amends CLI-001 and CLI-006 in place.
- **[`AGENTS.md:25`, `docs/architecture.md:76`, `pyproject.toml:1-8`]** Convention: no dependencies beyond the standard library, and there is no package manager or lockfile. **Reflected in plan:** the plan adds no dependency.
- **[`Makefile:2-5`, `AGENTS.md:101-102`]** Convention: `make test` runs `unittest discover -s tests`, and `make lint` runs `compileall`. **Reflected in plan:** new tests live in `tests/` with the `test_*.py` name so discovery finds them.
- **[`pyproject.toml:5`, `.github/workflows/ci.yml:10`]** Convention: Python 3.11 or later, and CI runs 3.12. **Reflected in plan:** the code uses no syntax newer than 3.11. The prototype passed on 3.12.
- **[`docs/architecture.md:80`, `tests/test_tickets.py:8-20`]** Convention: `unittest` with a fake clock injected through `EventStore(clock=...)`. There is no mock library. **Reflected in plan:** unit cases in step 5 drive time through that fake clock.
- **[`docs/guidelines.md:29-34`]** Convention: name test files, cases, and test type, and name end-to-end command sequences for user-visible changes. **Reflected in plan:** the test plan.
- **[`docs/guidelines.md:9-11`]** Convention: test 100% of code, with no numeric coverage target recorded. **Reflected in plan:** every new branch in steps 3 and 4 has a case. The missing numeric target doesn't constrain this plan.
- **[`docs/architecture.md:81`, `Makefile:5`]** Convention: lint is a syntax pass only. **Reflected in plan:** doesn't constrain this plan beyond step 7, because no style or type tool exists.
- **[`docs/guidelines.md:51-53`, `docs/architecture.md:36-38`]** Convention: no ticket rule in the CLI. **Reflected in plan:** the overdue rule lives in `tickets.py` in step 3. The CLI only formats in step 4.
- **[`docs/architecture.md:68-69`]** Convention: time comes from the store's clock. **Reflected in plan:** `TicketService.now()` in step 3.
- **[`docs/guidelines.md:84-87`]** Convention: one logical change per commit, with spec IDs in the message. **Reflected in plan:** the commit split above the step list.
- **Per-component conventions.** Doesn't constrain this plan. The repo has no `AGENTS.md` below the root.
- **Migrations.** Doesn't constrain this plan. The log has no schema change, and `docs/architecture.md:44` says rule changes need no data migration.
- **Ports, URLs, environment.** Partly constrains. There is no network (`docs/architecture.md:64-65`). `TICKETDESK_LOG` is read at import time (`ticketdesk/cli.py:8`), so CLI tests pass `--log` and remove `TICKETDESK_LOG` from the subprocess environment.
- **Async machinery.** Doesn't constrain this plan. Each command is one synchronous process.
- **Patterns to reuse.** The sort in `ticketdesk/tickets.py:47`, the line format in `ticketdesk/cli.py:30`, and the fake clock in `tests/test_tickets.py:8-14`. **Reflected in plan:** steps 3, 4, and 5.

### Codebase sweep

- **In-flight work.** None. The repo has one commit (`57587be`), one branch, and no stash.
- **Shadow duplication.** None. A grep for `overdue`, `clock`, and `due` found no other comparison of a due time with the current time.
- **Caller drift.** The API change only adds names. `TicketService.list()` and `Ticket` have no callers outside `cli.py` and the tests. Doc drift exists in `CLI-001`, `docs/architecture.md:12`, `AGENTS.md:102`, and `AGENTS.md:114`, which steps 1 and 6 handle.
- **Test infrastructure gap.** The CLI has no tests (`AGENTS.md:116`, `docs/architecture.md:103`). Step 5 adds `tests/test_cli.py` with a subprocess helper and seeded logs.

### Success criteria

| Criterion | Plan steps | Result |
|---|---|---|
| An open or assigned ticket past its due time shows `OVERDUE` in `list` | 3, 4, tests U2, U4, C1 | Confirmed |
| A closed ticket and a ticket not yet due keep their current line | 3, 4, tests U1, U3, C1 | Confirmed |
| `overdue` prints only overdue tickets, earliest due first, ties by ID | 3, 4, tests U5, C2 | Confirmed |
| `list` and `overdue` append nothing, and replay stays deterministic | 3, tests U6, U7, C4 | Confirmed |
| `make lint && make test` pass, and the CLI has tests | 5, 7 | Confirmed |
| Specs and docs match the new behavior | 1, 2, 6 | Confirmed with gaps |

The gap is approval. Steps 1, 2, and 6 need your sign-off under the repo rules. The display choice in open question 1 may also change the text of CLI-006.
The counterfactual result is **Confirmed with gaps**.

## Test plan

Unit cases go in `tests/test_tickets.py`. They run through the service with the existing fake clock.

- **U1** `test_not_overdue_at_due_time_TKT_014`. Set the clock so the next call returns the due time. Expect `overdue()` to be empty.
- **U2** `test_overdue_after_due_time_TKT_014`. One second later, expect the ticket in `overdue()`.
- **U3** `test_closed_ticket_never_overdue_TKT_014`. Close a ticket after its due time. Expect `overdue()` to be empty.
- **U4** `test_assigned_ticket_can_be_overdue_TKT_014`. Assign, then pass the due time. Expect the ticket in `overdue()`.
- **U5** `test_overdue_order_TKT_015`. Create a `P3` ticket, then a `P1` ticket that is due earlier, then a ticket with the same due time as another. Expect due-time order with ties by ID.
- **U6** `test_overdue_appends_nothing_LOG_001`. Expect the replayed event count unchanged after `overdue()`.
- **U7** `test_list_state_independent_of_clock_LOG_009`. Expect `list()` to return the same states before and after the clock passes a due time.

CLI cases go in a new `tests/test_cli.py`. They run `python3 -m ticketdesk.cli --log <tmp>` as a subprocess from the repo root. Each case writes a seeded log in the LOG-005 format. Past tickets use `at` values near 1000. Future tickets use `at` 4102444800, which is 2100-01-01.

- **C1** `test_list_marks_overdue_CLI_006`. Expect `OVERDUE` for past open and assigned tickets. Expect `open` for a future ticket and `closed` for a closed past ticket. Check the 8-character padding.
- **C2** `test_overdue_order_CLI_010`. Expect only overdue tickets in TKT-015 order, exit code 0, and empty stderr.
- **C3** `test_overdue_empty_CLI_010`. With no overdue tickets, and with a missing log file, expect empty stdout, exit code 0, and no log file created.
- **C4** `test_read_commands_append_nothing_LOG_001`. Expect the log bytes unchanged after `list` and `overdue`.
- **C5** `test_usage_lists_overdue_CLI_001`. Expect `overdue` in the `--help` output. Expect an unknown subcommand to still exit with code 2.

End-to-end sequences run the `ticketdesk` entry point against a temporary log, per `docs/guidelines.md:32-34`.

1. Run `create "Printer on fire" --priority P1`, `create "VPN slow"`, `list`, and `overdue`. Expect no `OVERDUE` label and an empty `overdue` output.
2. Seed a log with one `P1` ticket created at `at` 1000. Run `assign 1 dana`, `list`, and `overdue`. Expect `#1 [P1] OVERDUE  ...` in both outputs.
3. Continue with `close 1 "Replaced the toner cartridge"`, `list`, and `overdue`. Expect `closed` in `list` and an empty `overdue` output.

A manual check is not needed. The seeded logs cover the time travel that a person would otherwise wait 4 hours for.

## Risks and mitigations

- **Scripts that parse `list` may filter on `open` or `assigned`.** Such a script stops seeing overdue tickets. Mitigation: open question 1 offers a format that keeps the state. The commit message calls out the change to CLI-006.
- **The fake clock advances on every call.** A test that calls `now()` twice may land one second away from the expected time. Mitigation: tests compute expected values from the returned ticket's `due_at`, as the probe did.
- **A wall clock that jumps backward hides overdue tickets until it catches up.** Mitigation: none in this plan. The tool already trusts the local clock for every event timestamp.
- **A hand-edited log with a future `at` never shows as overdue.** Mitigation: none needed. `docs/architecture.md:66-67` treats events as trusted.

## Open questions

Nobody was available to answer these during planning. Each one states the assumption this plan proceeds on.

1. **Should `list` show `OVERDUE` in place of `open` or `assigned`, or keep the state and add a marker?** Assumption: replace the state label. It matches "show as OVERDUE" and keeps the column aligned. It hides open versus assigned for overdue tickets. The fallback is a line such as `#2 [P1] assigned OVERDUE <title>`.
2. **Should `overdue` lines show more, such as the assignee, the due time, or how late the ticket is?** Assumption: no. The lines use the `list` format.
3. **Is a ticket overdue at its due time exactly?** Assumption: no. "Pass their due time" means strictly later.
4. **Should a ticket closed after its due time show as late in any way?** Assumption: no. A closed ticket is never overdue.
5. **Should `overdue` exit with a non-zero code when overdue tickets exist, for use in cron jobs?** Assumption: no. It exits with code 0 per CLI-008.
6. **Do you approve the spec and doc edits?** These are TKT-014, TKT-015, CLI-010, the amended CLI-001, CLI-006, and LOG-001, and the updates to `docs/architecture.md` and `AGENTS.md`. Assumption: yes, as written in steps 1, 2, and 6. This question blocks implementation under `AGENTS.md:93`.
7. **Should this change also resolve the CLI-007 conflict?** Assumption: no. It needs its own decision and its own commit.

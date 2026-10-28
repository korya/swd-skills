# Plan: overdue tickets in ticketdesk

## Headline

Derive "overdue" at read time from the due time and the store's clock, with no new event or state. `ticketdesk list` shows `OVERDUE` in the state column, and a new `ticketdesk overdue` command lists only overdue tickets by due time. The blocking decision is your sign-off on six spec changes, because the current specs name four commands and three states.

## Approach summary

A ticket is overdue when it is `open` or `assigned` and the current time is strictly later than its due time. The due time already exists on every replayed ticket, so the change adds a comparison and no data. A new method `Ticket.is_overdue(now)` in `ticketdesk/tickets.py` holds that rule, and a new `TicketService.overdue(now=None)` returns the overdue tickets sorted by due time, then by ID. The service reads the current time from the clock that `EventStore` already owns, so tests keep one injectable clock.

The CLI adds an `overdue` subcommand and prints `OVERDUE` instead of the state for overdue tickets in `list`. The store, the log format, the event kinds, and the three ticket states stay unchanged, so INV-001, INV-002, and LOG-002 hold. The plan stands on two checked facts: every replayed ticket carries a due time, and `OVERDUE` fits the existing 8-character state column. The main trade-off is that `list` hides whether an overdue ticket is `open` or `assigned`, which open question 1 asks you to accept or change.

## Out of scope

- No `overdue` event in the log and no fourth ticket state. Overdue is a derived view, not a fact that the log records.
- No notification, scheduler, or background check. The tool runs one command per invocation and exits.
- No change to the SLA hours, business hours, or time zones. Due times stay epoch seconds per TKT-005.
- No fix for the open CLI-007 TODO. A hand-edited log with an unknown priority still escapes as a traceback, for `overdue` as for `list`.
- No version bump in `pyproject.toml` unless you ask for one, see open question 6.

## Plan

The plan has a spec gate first, then one feature commit with its tests.

1. **Get sign-off on the spec changes, then edit the docs.** This is one commit, `docs(specs): Specify overdue tickets (TKT-014, TKT-015, CLI-010)`. AGENTS.md:93 and docs/README.md:39-40 require your confirmation first.
   - `docs/product-specs/tickets.md`: add **TKT-014 Overdue tickets**. An `open` or `assigned` ticket is overdue when the current time is strictly later than its due time (TKT-005). A `closed` ticket is never overdue. Overdue is not a state, and checking it appends no event.
   - `docs/product-specs/tickets.md`: add **TKT-015 Overdue order**. Listing overdue tickets returns only overdue tickets, sorted by due time ascending, then by ID ascending.
   - `docs/product-specs/cli.md`: change **CLI-001** from four subcommands to five and add `overdue`.
   - `docs/product-specs/cli.md`: change **CLI-006** so that the state column shows `OVERDUE` for a ticket that is overdue per TKT-014.
   - `docs/product-specs/cli.md`: add **CLI-010 overdue**. `ticketdesk overdue` prints one line per overdue ticket in TKT-015 order, in the CLI-006 line format. With no overdue tickets it prints nothing and exits 0.
   - `docs/product-specs/event-log.md`: change **LOG-001** so that "Listing tickets appends nothing" also names listing overdue tickets.
   - `docs/architecture.md`: add `overdue` to the arrow label at line 12. Extend the time assumption at line 68 to say that the service reads the current time from the store's clock. Replace "The CLI is not covered by tests today" at line 103.
   - `AGENTS.md`: update the test count at line 102, the "Not covered by tests: the CLI" line at 116, and add an `overdue` example to "Running the project". Remove the CLI TODO in `docs/guidelines.md:10-11` only if you agree that the new CLI tests close it.
2. **Add the overdue rule to the ticket model.** In `ticketdesk/tickets.py`, add `Ticket.is_overdue(self, now)` that returns `self.state != "closed" and now > self.due_at`. Add a `# implements TKT-014` comment. The method takes `now` as an argument, so replay stays independent of the wall clock and LOG-009 holds.
3. **Add the overdue query to the service.** In `ticketdesk/tickets.py`, add `TicketService.now()` that returns `self.store.clock()`. Add `TicketService.overdue(self, now=None)` that replays once, keeps tickets where `is_overdue(now)` is true, and sorts by `(due_at, id)`. Comment it `# implements TKT-015`. `list()` stays unchanged.
4. **Wire the CLI.** In `ticketdesk/cli.py`, register `sub.add_parser("overdue")` next to `list` at line 18. Add a small `_line(ticket, status)` helper so that `list` and `overdue` print one format. In `list`, read `now = svc.now()` once per invocation and print `"OVERDUE"` when `t.is_overdue(now)` is true, else `t.state`. The `overdue` branch prints `_line(t, "OVERDUE")` for each ticket from `svc.overdue()`. The CLI holds no rule. It only chooses the text for a status that the model decided.
5. **Add unit tests through the service** in `tests/test_tickets.py`, see the test plan.
6. **Add the first CLI tests** in a new `tests/test_cli.py`. They run `python3 -m ticketdesk.cli` as a subprocess against a temporary log, see the test plan.
7. **Run `make lint && make test`** and the manual e2e sequences below. Commit steps 2 to 6 as one change, `feat(cli): Show overdue tickets and add the overdue command (TKT-014, TKT-015, CLI-010)`.

## Assumptions validated

| # | Assumption | Class | Evidence | Result |
|---|---|---|---|---|
| A1 | Every replayed ticket carries a due time computed from its creation time and priority. | Verified | `ticketdesk/tickets.py:35-36` sets `t.due_at = due_at(ev["at"], ev["priority"])` on every `created` event. | Confirmed |
| A2 | A closed ticket is identifiable at read time, so it can be excluded. | Verified | `ticketdesk/tickets.py:41-43` sets `state = "closed"` on replay. | Confirmed |
| A3 | The service can get a deterministic "now" without a second clock and without breaking INV-005. | Risky | `ticketdesk/store.py:14-16` stores an injectable `clock`. INV-005 (`invariants.md:34-37`) covers event timestamps only. The prototype read `store.clock()` and the fake test clock drove it. | Confirmed, with a caveat below |
| A4 | `OVERDUE` fits the state column without breaking alignment. | Plausible | `cli.py:30` pads to 8. `OVERDUE` has 7 characters. The prototype printed `#1 [P3] OVERDUE  old P3`, aligned with `#3 [P2] open     not due P2`. | Confirmed |
| A5 | E2e tests can create overdue tickets without waiting hours. | Risky | The CLI cannot backdate events (INV-005). A hand-written valid log with past `at` values replayed through the unmodified CLI with exit 0 and correct lines. | Confirmed |
| A6 | `make test` discovers a subprocess CLI test that imports `ticketdesk` from the repo root. | Plausible | A prototype `tests/test_proto_overdue.py` in a scratch copy ran `python3 -m ticketdesk.cli` with `cwd` at the root. `make test` ran 9 tests, OK. | Confirmed |
| A7 | Read-only commands leave the log untouched and create no file. | Plausible | After `list` and `overdue` in the prototype, the hand-written log still had 7 lines. `overdue` on a missing path exited 0 and created no file. | Confirmed |

The caveat on A3 is that the fake `Clock` in `tests/test_tickets.py:8-14` advances one second per call. Two `svc.now()` calls in the prototype differed by `1.0`. Unit tests must therefore pass an explicit `now` to `overdue()` and `is_overdue()`. The `now=None` parameter in step 3 exists for this reason.

**Hypothesis.** Overdue is a pure function of the replayed ticket and one "now" per invocation. A model method, a service query, and a CLI subcommand implement it, with no change to the store or the log.

**Falsifier.** The shape is wrong if overdue needs state the log does not hold. It is also wrong if the CLI cannot get "now" without a new clock source that breaks test determinism.

**Falsifier result.** Not triggered. A scratch prototype changed only `tickets.py` and `cli.py`. It produced the output below on a hand-written log, where "now" was the real time.

```
$ ticketdesk --log handmade.jsonl list
#1 [P3] OVERDUE  old P3            created 80 h ago, due 8 h ago
#2 [P1] OVERDUE  fresh P1          created 5 h ago, due 1 h ago
#3 [P2] open     not due P2        created 1 h ago, due in 23 h
#4 [P1] closed   closed late P1    due 6 h ago, closed after the due time
#5 [P2] OVERDUE  assigned P2       created 30 h ago, due 6 h ago
$ ticketdesk --log handmade.jsonl overdue
#1 [P3] OVERDUE  old P3
#5 [P2] OVERDUE  assigned P2
#2 [P1] OVERDUE  fresh P1
```

The annotations on the right are added here and are not program output. The `overdue` order is 1, 5, 2, which differs from the ID order. This confirms that the sort uses the due time.

The prototype also confirmed these boundary cases in a scratch unit test:

- `overdue(now=t.due_at)` returns nothing. The comparison is strict.
- `overdue(now=t.due_at + 0.001)` returns the ticket.
- After `close`, `overdue(now=t.due_at + 99)` returns nothing.

**Alternatives rejected.**

- **An `overdue` event kind.** It breaks LOG-002 and LOG-001, and some process would have to append it on time.
- **An `overdue` field set during replay.** It makes replay depend on the wall clock, which breaks LOG-009.
- **A fourth state in `STATES`.** It breaks TKT-001 and the closed checks in `assign` and `close`.
- **The rule in the CLI.** `docs/architecture.md:36-38` forbids ticket rules in the CLI.
- **A separate `clock` argument on `TicketService`.** It gives tests two clocks that can disagree. The store's clock is already the one injected time source.

## Project conventions to follow

- **[`AGENTS.md:25`, `docs/architecture.md:76`]** Dependencies: *none beyond the standard library.* **Reflected in plan:** steps 2 to 6 use only `argparse`, `dataclasses`, `subprocess`, `tempfile`, and `unittest`.
- **[`Makefile:2-5`, `AGENTS.md:88-89`, `docs/guidelines.md:12`]** Build and test entry points: *`make lint && make test` before every push.* **Reflected in plan:** step 7.
- **[`AGENTS.md:22`, `tests/test_tickets.py:8-21`, `docs/architecture.md:49-50`]** Test framework and mocking: *`unittest`, with time injected through `EventStore(clock=...)`, no mock library.* **Reflected in plan:** step 5 reuses the `Clock` class and passes explicit `now` values. Step 6 uses hand-written logs, not mocks.
- **[`docs/guidelines.md:29-34`]** Test types: *name the type, unit through the service or subprocess through the CLI, plus e2e command sequences against a temporary log.* **Reflected in plan:** steps 5 and 6 and the test plan.
- **[`Makefile:5`, `docs/architecture.md:81`]** Lint and format: *`compileall` syntax pass only.* **Reflected in plan:** step 7. The new `tests/test_cli.py` falls under `tests/` and is covered.
- **[`docs/architecture.md:36-38`, `docs/guidelines.md:51-53`]** Layering: *no ticket rule in the CLI, no file access outside the store.* **Reflected in plan:** the rule lives in `Ticket.is_overdue` (step 2). The CLI only picks the text (step 4).
- **[`docs/architecture.md:68-69`, `docs/product-specs/invariants.md:34-37`]** Time source: *time comes from the store's clock.* **Reflected in plan:** step 3 reads "now" from `store.clock`, and step 1 records this in `docs/architecture.md`.
- **[`AGENTS.md:93`, `docs/README.md:39-40`, `docs/guidelines.md:80`]** Doc changes: *need user confirmation, no drive-by spec edits.* **Reflected in plan:** step 1 is a gate and its own commit.
- **[`docs/README.md:27-28`, `docs/product-specs/README.md:16-18`]** Spec IDs: *never renumber, a new spec takes the next free number.* **Reflected in plan:** step 1 adds TKT-014, TKT-015, and CLI-010.
- **[`AGENTS.md:96`, `docs/README.md:43-44`]** Traceability: *cite spec IDs in code comments, tests, and commits.* **Reflected in plan:** steps 2, 3, and 7, and every test name in the test plan.
- **[`docs/guidelines.md:84-87`]** Commits: *one logical change per commit.* **Reflected in plan:** a docs commit in step 1 and a feature commit in step 7.
- **[`ticketdesk/cli.py:14-18`, `ticketdesk/cli.py:31-33`]** Existing CLI pattern: *one `add_parser` per command, `TicketError` mapped to exit 2.* **Reflected in plan:** step 4 follows it. `overdue` raises no `TicketError` of its own.
- **[`pyproject.toml:5`, `.github/workflows/ci.yml:10`]** Python version: *3.11+, CI on 3.12.* **Reflected in plan:** the code uses no syntax newer than 3.10. The local check ran on Python 3.15.1, so CI on 3.12 is the binding check.
- **Package manager, migrations, ports, URLs, async machinery.** These do not constrain this plan. The project installs nothing, the log format does not change, and the tool is one synchronous local process.

## Test plan

**Unit tests through the service** go in `tests/test_tickets.py`, in `TicketTests`, with the existing fake `Clock` and explicit `now` values:

- `test_overdue_after_due_time_TKT_014`: a `P1` ticket is overdue at `due_at + 1` and not at `due_at`.
- `test_assigned_ticket_can_be_overdue_TKT_014`: an `assigned` ticket past its due time is overdue.
- `test_closed_ticket_never_overdue_TKT_014`: a ticket closed after its due time is not overdue.
- `test_overdue_sorted_by_due_time_TKT_015`: a `P3` created first and a `P1` created second come back in due order, which differs from ID order.
- `test_overdue_ties_broken_by_id_TKT_015`: two tickets with equal due times come back in ID order.
- `test_overdue_empty_log_LOG_006`: a missing log returns an empty list.
- `test_overdue_appends_nothing_LOG_001`: the event count from `replay()` is the same before and after `overdue()`.

**CLI tests through a subprocess** go in a new `tests/test_cli.py`. Each test writes a valid log with `at` values hours in the past, so no test depends on timing within seconds:

- `list` prints `#<id> [<priority>] OVERDUE  <title>` for an overdue ticket and the unchanged line for others (CLI-006).
- `list` on a log with no overdue tickets prints exactly the lines it prints today. This is the regression guard for CLI-006.
- `overdue` prints only overdue tickets, in due order, and exits 0 with empty stderr (CLI-010, CLI-008).
- `overdue` with no overdue tickets prints nothing and exits 0 (CLI-010).
- `overdue` on a missing log prints nothing, exits 0, and creates no file (LOG-006).
- `TICKETDESK_LOG` selects the log for `overdue` (CLI-002).
- An unknown subcommand still exits 2 (CLI-001).

**E2e command sequences** run against a temporary log, per `docs/guidelines.md:32-34`:

1. `create "Printer on fire" --priority P1`, then `list` and `overdue`. Expect `open` in `list` and no output from `overdue`.
2. Write a log by hand with a `P1` created 5 hours ago, a `P3` created 80 hours ago, and a closed `P1` created 10 hours ago. Run `list`, then `overdue`. Expect the two open tickets as `OVERDUE`, the `P3` first, and the closed ticket absent.
3. On that log, `assign` the `P1` to `dana`, then run `list`. Expect `OVERDUE`, not `assigned`.
4. On that log, `close` the `P1`, then run `overdue`. Expect only the `P3`.
5. Compare the log line count before and after steps 2 to 4. Expect growth only from `assign` and `close`.

**Manual check.** Run `make lint && make test` on Python 3.12 if it is available, to match CI.

## Risks and mitigations

- **Scripts that parse `list` may break.** A script that searches for `open` or `assigned` in the state column misses overdue tickets after this change. Mitigation: open question 1, and a release note in the feature PR.
- **A wrong system clock gives a wrong answer silently.** Overdue now depends on the machine time at read time. Nothing in the tool detects a skewed clock. Mitigation: none in code. The architecture doc records the dependency in step 1.
- **Time-dependent tests may flake.** Mitigation: unit tests pass explicit `now` values, and CLI tests use offsets of hours, never seconds.
- **The fake `Clock` advances on every call.** A test that calls `svc.now()` twice sees two times. Mitigation: unit tests never rely on the default `now`.
- **The first subprocess tests make `make test` slower.** Each call starts a Python process. The prototype ran 9 tests, two of them with subprocess calls, in 0.064 seconds. Mitigation: none needed at this scale.
- **Cost does not grow.** `overdue` replays the log once, like `list`, see `docs/architecture.md:62-63`. No new fan-out and no new attack surface appear.

## Counterfactual

**Verdict: Confirmed with gaps.** Every success criterion has a plan step. The gaps are the spec sign-off and the open questions below, which can change the output format but not the shape.

| Success criterion | Plan steps | Proof of failure we test against |
|---|---|---|
| An `open` or `assigned` ticket past its due time shows `OVERDUE` in `list`. | 2, 4, 6 | A `P1` created 5 hours ago still shows `open`. |
| A closed ticket never shows `OVERDUE`. | 2, 5, 6 | A ticket closed after its due time shows `OVERDUE`. |
| A ticket that is not yet due prints the same line as today. | 4, 6 | Any change to a non-overdue `list` line. |
| `ticketdesk overdue` lists only overdue tickets. | 3, 4, 6 | A closed or not-yet-due ticket appears. |
| `ticketdesk overdue` sorts by due time, oldest first. | 3, 5, 6 | The output follows ID or creation order when due order differs. |
| No command appends to or creates the log by reading it. | 3, 5, 6 | The log line count changes after `list` or `overdue`. |
| The specs and docs match the new behavior, with your sign-off. | 1 | A spec still says four commands or omits overdue. |
| `make lint && make test` pass, and the CLI has tests. | 5, 6, 7 | CI fails, or `tests/test_cli.py` is missing. |

## Open questions

Nobody was available during this run. Each question states the assumption the plan proceeds on.

1. **Should `list` replace the state with `OVERDUE`, or show both?** Replacing hides whether the ticket is `open` or `assigned`. Showing both changes the line format more. *Assumption:* replace the state, because the request says the ticket should "show as OVERDUE" and the word fits the column.
2. **Is a ticket overdue at exactly its due time?** *Assumption:* no. It becomes overdue strictly after the due time, which matches "pass their due time".
3. **Should `overdue` print the `list` line format, or something richer such as the time past due?** *Assumption:* the `list` format with `OVERDUE` in the state column, so each line matches its line in `list`.
4. **Should `overdue` exit non-zero when overdue tickets exist, for monitoring scripts?** *Assumption:* no. It exits 0 on success per CLI-008.
5. **Do you approve the spec and doc changes in step 1?** These are TKT-014, TKT-015, CLI-010, and the edits to CLI-001, CLI-006, LOG-001, `docs/architecture.md`, and `AGENTS.md`. *Assumption:* yes, as worded in step 1. No code work starts before you confirm.
6. **Should the version move from 0.3.0 to 0.4.0?** A new command is a user-visible feature. *Assumption:* no bump in this change, because the repo records no release process.
7. **Is reading "now" from `EventStore.clock` acceptable for the service?** It is a small new use of the store, recorded in `docs/architecture.md`. *Assumption:* yes, because it keeps one injectable time source.

# Plan: overdue tickets in ticketdesk

## Headline

We add one overdue rule to the service and evaluate it at read time against the store's clock. `ticketdesk list` then shows `OVERDUE` in the state column, and a new `ticketdesk overdue` lists only overdue tickets by due time. Code work waits for your sign-off on six spec edits, because the change adds a command and alters the `list` output.

## Approach summary

The overdue check runs at read time and writes nothing to the event log. The service in `ticketdesk/tickets.py` gets one rule. An `open` or `assigned` ticket is overdue when the current time is later than its due time. The service reads the current time once per command from the injectable clock of the store (`ticketdesk/store.py:14-16`). The CLI in `ticketdesk/cli.py` only formats what the service returns, so no ticket rule moves into the CLI. Replay, the log format, the SLA table, and `TicketService.list()` stay unchanged.

The plan stands on one assumption. The due time is fixed at creation, so one clock read decides overdue. This holds on `HEAD`. The main trade-off is in `list`, where `OVERDUE` replaces the state word and hides `open` versus `assigned`. Open question 1 asks you to confirm this.

## Out of scope

- A fix for the open TODO under CLI-007. The `overdue` command inherits the traceback on a corrupt log line or an unknown priority, the same as `list` does today.
- Business hours, paused SLAs, or per-customer targets. The due time stays creation time plus the hours in `SLA_HOURS`.
- A "closed late" report or any history of past overdue tickets.
- A non-zero exit code to signal overdue tickets to a cron job or a script.
- CLI tests for `create`, `assign`, and `close`. This plan adds the CLI test suite but covers only `list` and `overdue`.
- A version bump. The repo records no release convention.
- A `.gitignore` for `__pycache__/`. `make test` leaves untracked `__pycache__/` folders in the repo today.

## Plan

1. **Draft the spec edits and get sign-off.** No code work starts before this step closes. The AGENTS.md rule at `AGENTS.md:93` and `docs/README.md:39` require it.
   - `docs/product-specs/tickets.md`, new **TKT-014: Overdue tickets.** "A ticket is overdue when its state is `open` or `assigned` and the current time is later than its due time. A `closed` ticket is never overdue. Overdue is not a state. Checking it appends no event."
   - `docs/product-specs/tickets.md`, new **TKT-015: Overdue listing order.** "Listing overdue tickets returns only overdue tickets, sorted by due time ascending. Tickets with the same due time are sorted by ID ascending."
   - `docs/product-specs/cli.md`, edit **CLI-001.** Five subcommands. Add `overdue` to the list.
   - `docs/product-specs/cli.md`, edit **CLI-006.** Add the sentence "For a ticket that is overdue per TKT-014, the state column shows `OVERDUE`."
   - `docs/product-specs/cli.md`, new **CLI-010: overdue.** "`ticketdesk overdue` prints one line per overdue ticket in the order of TKT-015. Each line has the format of CLI-006. With no overdue tickets it prints nothing."
   - `docs/product-specs/event-log.md`, edit **LOG-001.** Change "Listing tickets appends nothing" to "Listing tickets or overdue tickets appends nothing."
2. **Add the overdue rule to the service** in `ticketdesk/tickets.py`.
   - Add `_is_overdue(ticket, now)`. It returns `ticket.state != "closed" and now > ticket.due_at`. Cite TKT-014 in a comment.
   - Add `list_with_overdue()`. It reads `now = self.store.clock()` once and returns `(ticket, is_overdue)` pairs in ID order.
   - Add `overdue()`. It reads the clock once and returns the overdue tickets sorted by `(due_at, id)`. Cite TKT-015.
   - Keep `list()` as it is. `ticketdesk/__init__.py` exports `TicketService`, and `tests/test_tickets.py` uses it.
3. **Wire the CLI** in `ticketdesk/cli.py`.
   - Add `sub.add_parser("overdue")` next to `list` at `cli.py:18`.
   - Change the final `else:` at `cli.py:28` to `elif args.cmd == "list":`. Today that `else` catches every command that is not `create`, `assign`, or `close`. A new command without this change would print the full list.
   - Move the line format `#{t.id} [{t.priority}] {state:<8} {t.title}` into one helper, so `list` and `overdue` print the same shape.
   - For `list`, print `OVERDUE` as the state when the service flags the ticket. For `overdue`, print `OVERDUE` for every line.
4. **Add unit tests** to `tests/test_tickets.py`. The cases are in the test plan below.
5. **Add the CLI test suite** in a new file `tests/test_cli.py`. It runs `python3 -m ticketdesk.cli` as a subprocess against a log file that the test writes with past timestamps.
6. **Run `make lint && make test`** and the end-to-end sequences in the test plan.
7. **Update the docs after the code lands**, with your confirmation per `docs/guidelines.md:55` and `docs/guidelines.md:78`.
   - `docs/architecture.md:12`: add `overdue` to the command list in the diagram.
   - `docs/architecture.md:68-69`: add that the current time for the overdue check also comes from the store's clock.
   - `docs/architecture.md:94-96` and `docs/architecture.md:103`: add `test_cli.py`, and remove "The CLI is not covered by tests today."
   - `AGENTS.md:102`: replace the test count of 7 with the new count.
   - `AGENTS.md:114` and `AGENTS.md:116`: add `overdue` to the done list, and change the note that the CLI has no tests.
   - `docs/guidelines.md:10-11`: change the note that the CLI has no tests.

## Assumptions validated

| # | Assumption | Class | Result | Evidence |
|---|---|---|---|---|
| A1 | The due time is fixed at creation and nothing changes it later. | Risky | Confirmed | `tickets.py:36` sets `due_at` only on `created`. `assigned` and `closed` events at `tickets.py:38-43` never touch it. Reopen does not exist per `docs/architecture.md:111`. |
| A2 | The service can read the current time without a new dependency. | Plausible | Confirmed | `EventStore.clock` is a public attribute at `store.py:16`, defaulting to `time.time` at `store.py:14`. |
| A3 | The fake test clock can drive the rule, including the exact boundary. | Plausible | Confirmed | Scratch prototype output, quoted below. |
| A4 | `OVERDUE` fits the 8-character state column without breaking alignment. | Plausible | Confirmed | `f"{'OVERDUE':<8}"` gives `'OVERDUE '`. `'assigned'` is also 8 characters. |
| A5 | A CLI test can create an overdue ticket without waiting for real time to pass. | Risky | Confirmed | A log written by hand with past `at` values replays through `python3 -m ticketdesk.cli list` with exit 0. A probe subprocess test passed under `make test`. |
| A6 | `argparse` rejects `overdue` today, so the new command is the only path that reaches it. | Plausible | Confirmed | `ticketdesk overdue` on `HEAD` prints `invalid choice: 'overdue'` and exits 2. |

The prototype ran against a scratch copy of the package with the test `Clock` from `tests/test_tickets.py:8-14`. It created a `P3` ticket, a `P1` ticket, and a closed `P1` ticket, then moved the clock forward.

```text
after 5h: [(2, 'p1')]                 the closed P1 ticket is not overdue
just before a due: [2]                clock read equals the P3 due time, so not overdue
1s after a due: [2, 1]                sorted by due time, P1 first
tie dues equal: True                  a P3 ticket and a P1 ticket created 68 hours later
tie order: [1, 2]                     the tie falls back to ID order
events: ['created', 'created', 'created', 'closed']   no event appended by the check
```

**Falsifier.** The read-time rule is the wrong shape if overdue depends on more than the replayed ticket and one clock read. Examples are a paused SLA, a reopened ticket, or a due time that changes on assignment. The check is A1. The due time comes only from the `created` event, and no event kind can change it. The falsifier did not fire.

**Codebase sweep.**

- `git log --all` shows one commit, `57587be`, and one branch, `main`. No work on overdue tickets is in flight.
- A search for `overdue`, `late`, `clock`, and `due_at` finds no overdue logic to reuse. The only time source is the store's clock.
- The only callers of the CLI line format are the `print` calls at `cli.py:23-30`. No test checks CLI output today.
- No CLI test layer exists. Step 5 adds it. The subprocess pattern ran under `make test` in the scratch copy.

## Project conventions to follow

- **[`AGENTS.md:20`, `docs/architecture.md:79`]** Convention: *the CLI uses `argparse`.* **Reflected in plan:** step 3 adds a subparser. A missing or unknown command keeps the `argparse` exit code 2 of CLI-001.
- **[`docs/architecture.md:36-38`, `docs/guidelines.md:52-53`]** Convention: *no ticket rule lives in the CLI.* **Reflected in plan:** step 2 puts the overdue rule and the sort order in the service. Step 3 only formats.
- **[`docs/architecture.md:48-50`, `docs/architecture.md:68-69`]** Convention: *time comes from the store's injectable clock, never from the caller.* **Reflected in plan:** step 2 reads `self.store.clock()`. The CLI never calls `time.time()`.
- **[`docs/product-specs/invariants.md:16-17`]** Convention: *INV-001, no file, cache, or database holds ticket state.* **Reflected in plan:** step 2 computes overdue from replay on every call and stores nothing.
- **[`docs/product-specs/invariants.md:21-22`, `docs/product-specs/event-log.md:14-15`]** Convention: *INV-002 and LOG-001, listing appends nothing.* **Reflected in plan:** steps 1 and 2. A unit test in step 4 asserts that the event list is unchanged after `overdue()`.
- **[`docs/product-specs/invariants.md:31-32`]** Convention: *INV-004, a corrupt line fails fast.* **Reflected in plan:** step 2 reads tickets through the same replay path, so `overdue` fails the same way `list` does.
- **[`Makefile:2-5`, `.github/workflows/ci.yml:11-12`]** Convention: *`make lint` and `make test` before every push, and CI runs both on Python 3.12.* **Reflected in plan:** step 6.
- **[`AGENTS.md:22`, `docs/architecture.md:80`, `tests/test_tickets.py:8-14`]** Convention: *`unittest`, with time injected through the fake `Clock`, not patched with a mock.* **Reflected in plan:** steps 4 and 5. Unit tests move `Clock.now`. CLI tests write past timestamps into the log.
- **[`docs/guidelines.md:29-34`]** Convention: *name the test files, the cases, and the test type, and plan end-to-end command sequences.* **Reflected in plan:** the test plan below.
- **[`AGENTS.md:96`, `docs/README.md:43-44`]** Convention: *cite spec IDs in code comments, tests, and commits.* **Reflected in plan:** steps 2 to 5 cite TKT-014, TKT-015, CLI-006, and CLI-010.
- **[`docs/guidelines.md:85-86`]** Convention: *one logical change per commit, and no unrelated cleanup.* **Reflected in plan:** the CLI-007 fix and the `.gitignore` stay out of scope.
- **[`AGENTS.md:25`, `pyproject.toml:1-8`]** Convention: *no dependencies beyond the standard library.* **Reflected in plan:** the plan adds none.
- **Package manager, migrations, ports, async machinery.** These do not constrain the plan. The project has no lockfile, no database, no network, and no background work.

## Test plan

**Unit tests, `tests/test_tickets.py`, through the service with the fake `Clock`.**

- An `open` `P1` ticket is overdue one second after its due time (TKT-014).
- An `assigned` ticket past its due time is overdue (TKT-014).
- A `closed` ticket past its due time is not overdue (TKT-014).
- A ticket whose due time equals the clock read is not overdue (TKT-014, the "later than" boundary).
- `overdue()` returns tickets by due time, and falls back to ID order on a tie. Use a `P3` ticket and a `P1` ticket created 68 hours later (TKT-015).
- `list_with_overdue()` returns every ticket in ID order with the right flag (TKT-013, CLI-006).
- `overdue()` on a log with no tickets returns an empty list (LOG-006).
- `overdue()` appends no event (LOG-001).

**CLI tests, new `tests/test_cli.py`, by subprocess.** Each test writes a log with `at` values relative to `time.time()` and runs `sys.executable -m ticketdesk.cli --log <path>` with `cwd` at the repo root.

- `list` prints `#1 [P1] OVERDUE  <title>` for a past-due `open` ticket. It prints the normal state for a ticket not yet due and `closed` for a closed past-due ticket (CLI-006).
- `overdue` prints only overdue tickets, oldest due time first, with exit 0 and an empty stderr (CLI-010, CLI-008).
- `overdue` with no overdue tickets prints nothing and exits 0 (CLI-010).
- `overdue` with a missing log file prints nothing and exits 0 (LOG-006).
- An unknown subcommand still exits 2, and the usage now lists `overdue` (CLI-001).

**End-to-end sequences**, against a temporary log, through `python3 -m ticketdesk.cli` as in `AGENTS.md:103-106`.

1. Run `create "Fresh" --priority P3`, then `list` and `overdue`. Expect `open` in `list` and no output from `overdue`.
2. Write a log with four `created` events: `P1` 5 hours ago, `P2` 30 hours ago, `P3` 1 hour ago, and `P1` 10 hours ago. Add a `closed` event for the last one. Run `list`. Expect `OVERDUE` on tickets 1 and 2 only. Run `overdue`. Expect ticket 2, then ticket 1.
3. On the same log, run `assign 1 dana`, then `overdue`. Expect ticket 1 still listed. Run `close 1 "Replaced the toner cartridge"`, then `overdue`. Expect only ticket 2. Expect `closed` for ticket 1 in `list`.
4. Diff the log file before and after `list` and `overdue`. Expect no change (LOG-001).

**Manual.** Run `ticketdesk --help` and check that `overdue` appears in the usage.

## Risks and mitigations

- **A wrong system clock gives wrong overdue results.** The tool trusts the local clock for every timestamp already. The plan adds no new exposure. No mitigation is planned.
- **Scripts that parse `list` see a new value in the state column.** Every line keeps its four fields and its alignment. Mitigation: the release note names the new value `OVERDUE`.
- **A CLI test near a due time can flake.** A test that sets a due time 1 second from now can cross it during the run. Mitigation: CLI tests put due times at least one hour away from the current time.
- **`test_cli.py` depends on the working directory.** The subprocess needs the repo root on `sys.path`. Mitigation: set `cwd` to `Path(__file__).resolve().parents[1]`. This passed under `make test` in the scratch copy.
- **The `overdue` command shows a traceback on a corrupt log.** This is the open CLI-007 TODO and affects `list` the same way. It stays out of scope.

## Counterfactual

Verdict: **Confirmed with gaps.**

| Success criterion | Plan steps |
|---|---|
| A past-due ticket shows `OVERDUE` in `ticketdesk list`. | Steps 1, 2, 3. Unit and CLI tests in steps 4 and 5. |
| `ticketdesk overdue` lists only overdue tickets. | Steps 1, 2, 3. Tests in steps 4 and 5. |
| `ticketdesk overdue` sorts by oldest due time first. | Step 2 sorts by `(due_at, id)`. Tests in steps 4 and 5. |
| No invariant breaks, and the log is unchanged by both commands. | Step 2. Unit test in step 4 and end-to-end sequence 4. |
| Specs and docs match the new behavior. | Steps 1 and 7. |

The gaps are the decisions in the open questions below. The plan proceeds on the stated assumptions, and each one can change without a change to the shape.

## Open questions

1. **Does `OVERDUE` replace the state word in `list`, or appear next to it?** Assumption: it replaces the state word. This is the literal reading of the request, and it keeps the line shape of CLI-006. The cost is that an overdue line hides `open` versus `assigned`.
2. **Can a closed ticket be overdue?** Assumption: no. A ticket closed after its due time is `closed`, not `OVERDUE`.
3. **Is a ticket overdue at the exact second of its due time?** Assumption: no. "Pass their due time" means later than the due time.
4. **Should `overdue` print more than the `list` line, such as the due time or the hours late?** Assumption: no. It prints the CLI-006 line, so the state column always reads `OVERDUE`.
5. **Should `overdue` exit non-zero when it finds overdue tickets?** Assumption: no. It exits 0 per CLI-008.
6. **Do you approve the six spec edits in step 1?** Assumption: the text in step 1 is the draft. No code work starts before you approve it.
7. **Should this change also settle the CLI-007 TODO?** Assumption: no. It is a separate change and a separate commit.

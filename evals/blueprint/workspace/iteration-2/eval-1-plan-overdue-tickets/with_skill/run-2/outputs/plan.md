# Plan: overdue tickets in `ticketdesk list` and a new `ticketdesk overdue`

## Headline

We compute "overdue" when a command reads the log, from the due time that every ticket already has. We never store it as a state or an event, so the log, the replay, and the three ticket states stay unchanged. The one blocking decision is the spec sign-off, including whether `OVERDUE` replaces the state word in `list`.

## Approach summary

The overdue rule goes into `ticketdesk/tickets.py`, the module that owns every ticket rule. A ticket is overdue when it is not closed and the current time is later than its due time. The due time already exists on every replayed ticket at `ticketdesk/tickets.py:36`, so no new data is needed. The current time comes from the store's injectable clock, which also stamps events. Tests stay deterministic, and the code keeps one time source.

The CLI in `ticketdesk/cli.py` reads the current time once per command. `list` prints `OVERDUE` in the state column for an overdue ticket and keeps its ID order. The new `overdue` subcommand prints the same lines, filtered to overdue tickets and sorted by due time, earliest first.

The store, the log format, the event kinds, and ticket replay stay untouched. The plan stands on two facts that a prototype in a scratch copy confirmed. First, a derived status needs no event, so `list` and `overdue` still append nothing. Second, a hand-written log with old timestamps is enough to test the CLI without any clock injection. The main trade-off is that an overdue line in `list` no longer shows whether the ticket is `open` or `assigned`.

## Out of scope

- An `overdue` state or an `overdue` event in the log. That would break TKT-001 and LOG-001, see the falsifier below.
- Notifications, alerts, or any background job that watches due times.
- Business hours or per-customer due times. The `sla.py` table stays as it is.
- Showing the due time or the time overdue in the output.
- The open conflict under CLI-007. An unknown priority or a corrupt line in the log still escapes as a traceback, for `overdue` as for `list`.
- A numeric coverage target. The TODO at `docs/guidelines.md:10` stays open.

## Plan

1. **Get sign-off on the spec and doc changes, then commit them alone.** `docs/README.md:39` and `docs/guidelines.md:78` require user confirmation. The proposed text:
   - `docs/product-specs/tickets.md`, new **TKT-014: Overdue tickets.** A ticket that is not `closed` is overdue when the current time is later than its due time (TKT-005). A `closed` ticket is never overdue. Overdue is not a state, so TKT-001 still holds.
   - `docs/product-specs/tickets.md`, new **TKT-015: Overdue order.** Overdue tickets are sorted by due time, earliest first. Tickets with the same due time are sorted by ID ascending.
   - `docs/product-specs/cli.md`, **CLI-001**: five subcommands, adding `overdue`.
   - `docs/product-specs/cli.md`, **CLI-006**: the state cell shows `OVERDUE` for a ticket that is overdue per TKT-014.
   - `docs/product-specs/cli.md`, new **CLI-010: overdue.** `ticketdesk overdue` prints one line per overdue ticket in TKT-015 order, in the CLI-006 line format. With no overdue tickets it prints nothing.
   - `docs/product-specs/event-log.md`, **LOG-001**: name `overdue` beside listing as a command that appends nothing.
   - `docs/architecture.md:12`: add `overdue` to the command arrow. `docs/architecture.md:68`: say that the current time for the overdue check also comes from the store's clock. `docs/architecture.md:96` and `:103`: add `test_cli.py` and drop "The CLI is not covered by tests today".
   - `AGENTS.md:102`: update the test count. `AGENTS.md:103-106`: add an `overdue` example. `AGENTS.md:114-116`: add overdue to "Done" and remove "Not covered by tests: the CLI".
   - `docs/guidelines.md:10-11`: keep the coverage-target TODO, and drop the sentence that says the CLI has no tests.
2. **Add the overdue rule to `ticketdesk/tickets.py`.**
   - On `Ticket`, add `is_overdue(self, now)`. It returns `self.state != "closed" and now > self.due_at`. Add the comment `# implements TKT-014`.
   - On `TicketService`, add `now(self)`. It returns `self.store.clock()`.
   - On `TicketService`, add `overdue(self, now=None)`. It replays once, keeps the tickets where `is_overdue(now)` is true, and sorts by `(due_at, id)`. When `now` is `None`, it calls `self.now()`. Add the comment `# implements TKT-015`.
   - Leave `_tickets`, `list`, and the `Ticket` fields unchanged, so replay stays deterministic per LOG-009.
3. **Wire the CLI in `ticketdesk/cli.py`.**
   - Add `sub.add_parser("overdue")` after the `list` parser at `ticketdesk/cli.py:18`.
   - Add a small `_line(t, now)` helper that returns `#<id> [<priority>] <cell> <title>`. The cell is `OVERDUE` when `t.is_overdue(now)` is true, else `t.state`, padded to 8 characters.
   - In the `list` branch, read `now = svc.now()` once and print `_line(t, now)` for each ticket from `svc.list()`.
   - Add an `overdue` branch that reads `now` once and prints `_line(t, now)` for each ticket from `svc.overdue(now)`. Both commands then print identical lines for the same ticket.
4. **Add unit tests to `tests/test_tickets.py`.** The scenarios are in the test plan below.
5. **Add `tests/test_cli.py` with subprocess tests.** The scenarios are in the test plan below.
6. **Run `make lint && make test`, then the manual end-to-end sequence.** Commit the code and the tests together, with TKT-014, TKT-015, and CLI-010 in the message.

## Assumptions validated

| # | Assumption | Class | Evidence | Result |
|---|---|---|---|---|
| A1 | Every replayed ticket already carries its due time. | Verified | `ticketdesk/tickets.py:35-36` sets `t.due_at = due_at(ev["at"], ev["priority"])` on every `created` event. | confirmed |
| A2 | The service can read the current time from the store's clock, and the existing fake clock drives it in tests. | Plausible | `ticketdesk/store.py:14-16` stores `clock` as a public attribute. The prototype `TicketService.now()` returned a value past every creation time and advanced the fake clock. | confirmed |
| A3 | No code or test depends on the `list` state cell, so `OVERDUE` there breaks nothing in the repo. | Risky | The only print of the list line is `ticketdesk/cli.py:30`. No test calls the CLI (`AGENTS.md:116`). The existing 7 tests passed on the prototype. Scripts outside the repo are unknown, see the risks. | partial |
| A4 | `OVERDUE` fits the 8-character state column. | Verified | The word has 7 characters. The prototype printed `#1 [P3] OVERDUE  Old P3`, aligned with `open     ` and `closed   `. | confirmed |
| A5 | A CLI test can make a ticket overdue without clock injection. | Plausible | A hand-written log with `at` values from 2023-11-14 made `list` print `OVERDUE` through `python3 -m ticketdesk.cli`. A ticket made by `create` stayed `open`. | confirmed |
| A6 | "Oldest due first" means the earliest due time, not the earliest creation. | Plausible | A P1 created a day after a P3 is due first. The prototype printed `#2 [P1]` before `#1 [P3]`. The reading is still an interpretation, see open question Q3. | partial |

**Falsifier.** If being overdue must be recorded, the read-time shape is wrong and we need an `overdue` event. The request asks only for display and a filtered list, so nothing requires a record. The prototype also left the log byte-identical after `list` and `overdue`. The falsifier did not fire.

The specs also rule out the recorded shape. LOG-001 at `docs/product-specs/event-log.md:14` says that listing appends nothing, so an event written during `list` breaks it. TKT-001 at `docs/product-specs/tickets.md:17` allows only three states. A fourth state breaks TKT-001 and "a ticket moves forward only" at `docs/product-specs/tickets.md:8`.

Prototype results, from a throwaway copy under `outputs/scratch/proto`:

```text
at due_at exactly: []                       # not overdue at the due time itself
1s after P1 due: [2]
after all due: [2, 1] (closed P2 excluded)
overdue/list append nothing: True
--- list
#1 [P3] OVERDUE  Old P3
#2 [P1] OVERDUE  Later P1
#3 [P2] closed   Closed late
#4 [P2] open     Fresh ticket
--- overdue
#2 [P1] OVERDUE  Later P1
#1 [P3] OVERDUE  Old P3
exit=0 stderr=0
--- missing log: prints nothing, exit=0, no file created
--- `overdue extra`: usage error, exit=2
--- corrupt log: same ValueError traceback and exit=1 as `list` on HEAD
```

**Spec and invariant check.**

| ID | Effect | Plan step |
|---|---|---|
| INV-001 | Overdue is derived from the replay and the clock. No cache, no second file. | 2 |
| INV-002 | No command in this change appends or edits a line. | 2, 3, test U5 and C4 |
| INV-004 | `overdue` uses the same replay, so a corrupt line fails the same way. | 2 |
| INV-005 | No new events. The current time comes from the store's clock, not from the caller. | 2 |
| TKT-001 | Unchanged. `OVERDUE` is a display label, not a state. Test U6 checks it. | 2, 4 |
| TKT-005 | The due time that the rule compares against. | 2 |
| TKT-013 | Unchanged. `list` keeps ID order. | 3 |
| LOG-001 | `list` and `overdue` append nothing. Proposed wording names `overdue`. | 1, 3 |
| LOG-006 | A missing log gives an empty `overdue` output and creates no file. | 3, test C3 |
| LOG-009 | Replayed tickets stay the same. Overdue depends on the current time, so it stays out of the `Ticket` fields. | 2 |
| CLI-001, CLI-006 | Changed, needs sign-off. | 1, 3 |
| CLI-008 | `list` and `overdue` exit 0 with empty stderr. | 3, test C1 |
| TKT-014, TKT-015, CLI-010 | New, needs sign-off. | 1, 2, 3 |

**Codebase sweep.**

- **In-flight work.** `git log` shows one commit, `b7942f8`. No branch or TODO touches due times.
- **Duplicate logic.** No code compares a time with `due_at` today. The only reader of `due_at` is `tests/test_tickets.py:29`.
- **Callers of changed contracts.** `TicketService.list()` keeps its signature and return value. Its one caller is `ticketdesk/cli.py:29`. The `list` output format is the changed contract. Nothing in the repo parses it.
- **Test infrastructure.** No CLI tests exist (`docs/architecture.md:103`). Step 5 builds them. Both a subprocess run and an in-process `main([...])` call with `contextlib.redirect_stdout` worked in the prototype.

## Project conventions to follow

- **[`AGENTS.md:37`, `docs/architecture.md:36-38`, `docs/guidelines.md:52-53`]** Convention: *the service holds every ticket rule, and a rule in the CLI is a layer crossing.* **Reflected in plan:** step 2 puts the overdue rule and the sort in `tickets.py`. Step 3 only maps the result to a word.
- **[`docs/architecture.md:48-50`, `ticketdesk/store.py:14-20`]** Convention: *time comes from the store's injectable clock.* **Reflected in plan:** step 2 reads the current time through `TicketService.now()`, which calls the store's clock.
- **[`docs/architecture.md:68-69`]** Convention: *times are floats in seconds since the epoch.* **Reflected in plan:** step 2 compares floats directly. No time zone handling is needed.
- **[`AGENTS.md:25`, `docs/architecture.md:76`, `pyproject.toml:1-8`]** Convention: *no dependencies beyond the standard library.* **Reflected in plan:** no time-freezing or mocking library. Tests use the fake clock and hand-written logs. There is no package manager or lockfile to change.
- **[`AGENTS.md:20`, `ticketdesk/cli.py:14-18`]** Convention: *`argparse` subparsers, one `add_parser` per command.* **Reflected in plan:** step 3 adds `sub.add_parser("overdue")` in the same style.
- **[`Makefile:2-5`, `.github/workflows/ci.yml:11-12`, `AGENTS.md:88-89`]** Convention: *`make lint` runs `compileall`, and `make test` runs `unittest` discovery under `tests/`. Run both before a push.* **Reflected in plan:** step 6. The new file `tests/test_cli.py` is found by discovery with no Makefile change.
- **[`tests/test_tickets.py:8-21`]** Convention: *tests inject a fake `Clock` class and a temporary log file. They use no `unittest.mock`.* **Reflected in plan:** step 4 reuses that setup and passes an explicit `now` where the exact time matters.
- **[`docs/guidelines.md:29-34`]** Convention: *name the test files, the cases, and the test type. Plan end-to-end command sequences against a temporary log.* **Reflected in plan:** the test plan names `tests/test_tickets.py` as unit tests and `tests/test_cli.py` as subprocess tests, and gives the manual sequence.
- **[`docs/README.md:43`, `AGENTS.md:96`, `docs/guidelines.md:87`]** Convention: *cite spec IDs in code comments, tests, and commit messages.* **Reflected in plan:** steps 2, 4, 5, and 6 cite TKT-014, TKT-015, and CLI-010.
- **[`docs/README.md:39`, `docs/README.md:53`, `docs/guidelines.md:80`]** Convention: *no spec or doc change without user sign-off, and no drive-by spec edits.* **Reflected in plan:** step 1 is a separate commit that waits for approval.
- **[`docs/README.md:25-28`]** Convention: *new specs take the next free number, and IDs are never renumbered.* **Reflected in plan:** step 1 adds TKT-014, TKT-015, and CLI-010.
- **[`docs/guidelines.md:85-86`]** Convention: *one logical change per commit.* **Reflected in plan:** step 1 commits the specs, and step 6 commits the code with its tests.
- **[`.github/workflows/ci.yml:10`, `pyproject.toml:5`]** Convention: *CI runs Python 3.12, and the package supports 3.11 and later.* **Reflected in plan:** the change uses no syntax newer than 3.11. The local prototype ran on Python 3.15.1.
- **Migrations.** They do not constrain the plan. State comes from replay (`docs/architecture.md:44`), and no event or field changes.
- **Ports, URLs, and async work.** They do not constrain the plan. The tool is a local CLI with no network and no background jobs (`docs/architecture.md:64-65`).

## Test plan

**Unit tests through the service, in `tests/test_tickets.py`.**

- **U1, TKT-014 boundary.** A P1 ticket is not overdue at `now = due_at`. It is overdue at `now = due_at + 1`.
- **U2, TKT-014 closed.** A ticket closed before or after its due time is never in `overdue()`, even with `now` long past the due time.
- **U3, TKT-014 assigned.** An `assigned` ticket past its due time is in `overdue()`.
- **U4, TKT-015 order.** A P3 ticket is created, then a P1 ticket. Past both due times, `overdue()` returns the P1 first. Two tickets with the same due time come back in ID order. Use a store with a constant clock for the tie.
- **U5, LOG-001.** The log text is the same before and after `overdue()` and `list()`.
- **U6, TKT-001 and LOG-009.** An overdue ticket still has `state == "open"` from `list()` and `get()`.
- **U7, default time.** With no `now` argument, `overdue()` uses the store's clock. Use a clock you can move forward past a P1 due time.
- **U8, empty log.** `overdue()` on a missing log returns an empty list.

**Subprocess tests through the CLI, in the new `tests/test_cli.py`.** Each test runs `sys.executable -m ticketdesk.cli --log <tmp>` from the repo root. Each fixture log holds hand-written `created` events with `at` values from 2023-11-14, plus a ticket made by `create` at the real time.

- **C1, CLI-006 and CLI-008.** `list` prints `OVERDUE` for the past-due open and assigned tickets, `closed` for the closed one, and `open` for the fresh one. Exit code 0, empty stderr.
- **C2, CLI-010 and TKT-015.** `overdue` prints only the past-due tickets, earliest due time first, in the same line format as `list`.
- **C3, CLI-010 and LOG-006.** `overdue` on a missing log prints nothing, exits 0, and creates no file.
- **C4, LOG-001 and INV-002.** The log bytes are identical after `list` and `overdue`.
- **C5, CLI-001.** `overdue extra` prints a usage error to stderr and exits 2.

**Manual end-to-end sequence.** Run it against a temporary log, then remove the log.

```bash
printf '%s\n' '{"at": 1700000000.0, "id": 1, "kind": "created", "priority": "P3", "title": "Old P3"}' > /tmp/t.jsonl
python3 -m ticketdesk.cli --log /tmp/t.jsonl create "Printer on fire" --priority P1
python3 -m ticketdesk.cli --log /tmp/t.jsonl list       # #1 OVERDUE, #2 open
python3 -m ticketdesk.cli --log /tmp/t.jsonl overdue    # only #1
python3 -m ticketdesk.cli --log /tmp/t.jsonl close 1 "Replaced the toner cartridge"
python3 -m ticketdesk.cli --log /tmp/t.jsonl list       # #1 closed
python3 -m ticketdesk.cli --log /tmp/t.jsonl overdue    # prints nothing
```

## Risks and mitigations

- **A script outside the repo may parse the `list` state word.** Such a script stops seeing `open` or `assigned` for overdue tickets. Mitigation: open question Q1 offers a format that keeps the state word. The release note names the change.
- **The machine clock may be wrong.** A wrong clock shows wrong overdue labels. The effect is display only, because nothing is written to the log.
- **A ticket can cross its due time between two commands.** `list` and then `overdue` may disagree by one ticket. Each command reads the clock once, so one command is always consistent with itself.
- **The fake test clock advances one second on every call.** A test that calls `now()` twice gets two times. Mitigation: unit tests pass an explicit `now` wherever the exact time matters.
- **Replay cost does not grow.** `list` and `overdue` each replay the log once, as `list` does today (`docs/architecture.md:62-63`).
- **The CLI-007 tracebacks remain.** An unknown priority or a corrupt line in the log still prints a traceback with exit code 1 for `overdue`. The prototype showed the same behavior as `list` on `HEAD`.

## Counterfactual

**Verdict: confirmed with gaps.** Every success criterion has a plan step. The gaps are the display and ordering choices in the open questions, which the user still owes.

| Success criterion | Plan steps | Proof that it fails |
|---|---|---|
| A ticket past its due time shows `OVERDUE` in `ticketdesk list`. | 2, 3, tests C1 and U1 | A past-due open ticket prints `open`. |
| A closed ticket never shows `OVERDUE`. | 2, tests U2 and C1 | A ticket closed late prints `OVERDUE`. |
| `ticketdesk overdue` lists only overdue tickets. | 2, 3, test C2 | A fresh or closed ticket appears in its output. |
| `ticketdesk overdue` lists the earliest due time first. | 2, tests U4 and C2 | The output follows ID or creation order. |
| The log, the replay, and the three states stay unchanged. | 2, tests U5, U6, and C4 | `list` appends a line, or `Ticket.state` becomes `overdue`. |
| The 7 existing tests still pass. | 6 | `make test` fails on a test that exists on `HEAD`. |
| The specs describe the new behavior, with user sign-off. | 1 | A merged change with CLI-001 still listing four commands. |

## Open questions

Nobody was available to answer during this run. Each question states the assumption that the plan proceeds on.

- **Q1. Should `OVERDUE` replace the state word in `list`?** The other option keeps the state and adds a marker, as in `#1 [P3] assigned OVERDUE Old P3`. That option changes the line shape for every ticket. **Assumption:** `OVERDUE` replaces the state word, because the request says the ticket "shows as OVERDUE".
- **Q2. Is a ticket overdue at the exact second of its due time?** **Assumption:** no. "Pass their due time" means the current time is strictly later than the due time.
- **Q3. Does "oldest due first" mean the earliest due time?** The other reading is the earliest creation time. The two differ when a P1 is created after a P3. **Assumption:** the earliest due time, with ties by ID.
- **Q4. Can a closed ticket ever show as overdue?** One example is a ticket closed after its due time. **Assumption:** no. A closed ticket always shows `closed`, and `overdue` never lists it.
- **Q5. Should `overdue` print more than the `list` line, such as the due time or the hours late?** **Assumption:** no. Its lines are identical to the `list` lines, so a reader compares the two outputs easily.
- **Q6. May the service read the current time from the store's clock?** Today `docs/architecture.md:48-50` describes the clock only as the stamp for events. The alternative is a separate `clock` argument on `TicketService`. **Assumption:** reuse the store's clock, and record that in `docs/architecture.md:68`. This is a small change to a seam, so it needs your approval.
- **Q7. Do you approve the spec and doc text in step 1?** That text covers TKT-014, TKT-015, CLI-010, and the changes to CLI-001, CLI-006, and LOG-001. **Assumption:** the wording above stands until you edit it. No code work starts before you approve it.

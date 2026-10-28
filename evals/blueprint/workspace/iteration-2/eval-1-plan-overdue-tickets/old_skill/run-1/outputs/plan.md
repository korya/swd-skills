# Plan: overdue tickets in ticketdesk

## Headline

`ticketdesk list` shows `OVERDUE` for any open or assigned ticket past its due time. A new `ticketdesk overdue` command lists only those tickets, earliest due time first. Overdue is computed at read time from the due time and the clock, not stored as an event or a fourth state. The four spec changes below need sign-off before code work, and the display format in open question 1 needs a decision.

## Approach summary

The service in `ticketdesk/tickets.py` gets a pure rule `is_overdue(ticket, now)` and a query `TicketService.overdue(now)`. The rule says a ticket is overdue when its state is `open` or `assigned` and `now` is later than its due time. The current time comes from the store's injectable clock, so unit tests control it the same way they control event timestamps today. The CLI reads that time once per command, prints `OVERDUE` in place of the state for overdue tickets in `list`, and adds the `overdue` subcommand. The store, the log format, the replay, and the SLA table stay unchanged.

The approach stands on one fact. Every input that overdue needs, the state and the due time, already comes out of the replay. Overdue is a function of the log plus the current time, so it needs no new event and no stored state. The main trade-off is the display. Replacing the state column with `OVERDUE` keeps the line shape that CLI-006 defines, but it hides whether an overdue ticket is `open` or `assigned`. The alternative, an extra marker after the state, keeps that information but changes the line shape for every reader of `list`.

## Out of scope

- The open TODO under CLI-007. An unknown priority or a corrupt log still escapes as a traceback, in `overdue` as in `list`.
- Business hours, per-customer targets, or any other change to the SLA table in `ticketdesk/sla.py`.
- A recorded "breached SLA" flag for tickets that closed after their due time.
- A `--now` option or a `TICKETDESK_NOW` variable for tests. Tests write log files with past timestamps instead.
- Colour, sorting options, or filters on `list`.
- A version bump in `pyproject.toml`. No convention for it is recorded, see open question 7.

## Plan

### Step 1. Update the specs and docs, after sign-off

These edits come first because the repo forbids silent spec changes (`AGENTS.md:93`, `docs/README.md:39-40`). New IDs take the next free number in each file (`docs/README.md:27-28`).

- `docs/product-specs/tickets.md`: add **TKT-014 Overdue tickets**. A ticket is overdue when its state is `open` or `assigned` and the current time is later than its due time (TKT-005). A closed ticket is never overdue. Overdue is not a state, so TKT-001 keeps its three states. Computing it appends no event.
- `docs/product-specs/tickets.md`: add **TKT-015 Overdue order**. Overdue tickets are sorted by due time ascending, then by ID ascending.
- `docs/product-specs/cli.md`: change **CLI-001** from four subcommands to five, adding `overdue`.
- `docs/product-specs/cli.md`: amend **CLI-006**. The state field shows `OVERDUE` for a ticket that is overdue per TKT-014, still padded to 8 characters.
- `docs/product-specs/cli.md`: add **CLI-010 overdue**. `ticketdesk overdue` prints one line per overdue ticket in TKT-015 order, in the CLI-006 line format. With no overdue tickets it prints nothing and exits 0.
- `docs/architecture.md:68-69`: extend the time assumption. The current time that decides overdue also comes from the store's clock.
- `AGENTS.md`: add `overdue` to the run examples at lines 103-106 and to "Done" at line 114. Update the test count at line 102. Remove "Not covered by tests: the CLI" at line 116.

### Step 2. Add the overdue rule to the service

File: `ticketdesk/tickets.py`.

- Add a module function `is_overdue(ticket, now)`. It returns `ticket.state != "closed" and now > ticket.due_at`. Add the comment `# implements TKT-014`.
- Add `TicketService.now()`. It returns `self.store.clock()`. This keeps the time source in the store, as `docs/architecture.md:48-50` describes.
- Add `TicketService.overdue(now=None)`. It uses `self.now()` when `now` is `None`. It filters `self.list()` with `is_overdue` and sorts by `(t.due_at, t.id)`. Add the comment `# implements TKT-015`.
- Leave `_tickets()`, `list()`, and the `Ticket` dataclass unchanged. Replay stays independent of the current time (LOG-009).

File: `ticketdesk/__init__.py`. Export `is_overdue` next to the other public names.

### Step 3. Wire the CLI

File: `ticketdesk/cli.py`.

- Register the subcommand with `sub.add_parser("overdue")`, next to `sub.add_parser("list")` at line 18.
- Replace the catch-all `else` at line 28 with explicit `list` and `overdue` branches.
- Add a helper `_line(t, now)` that formats `#<id> [<priority>] <state> <title>`. The helper uses `"OVERDUE"` as the state when `is_overdue(t, now)` is true. It keeps the `:<8` padding from line 30.
- In both branches, read `now = svc.now()` once. Then `list` prints `_line(t, now)` for each ticket of `svc.list()`, and `overdue` does the same for `svc.overdue(now)`.
- The CLI decides only the label text. The rule itself stays in the service, as `docs/architecture.md:36-38` and `docs/guidelines.md:51-53` require.

### Step 4. Add unit tests through the service

File: `tests/test_tickets.py`. Keep the existing `Clock` fake (`tests/test_tickets.py:8-14`) and keep a reference to it in `setUp` so a test can move `clock.now` forward.

- `test_ticket_not_overdue_before_due`: a new P1 ticket, `now` one hour after creation, is not overdue.
- `test_open_ticket_overdue_after_due`: a P1 ticket, `now` five hours after creation, is overdue.
- `test_assigned_ticket_can_be_overdue`: an assigned P2 ticket past its due time is overdue.
- `test_closed_ticket_never_overdue`: a closed P1 ticket, `now` days later, is not overdue.
- `test_due_time_boundary`: at `now == due_at` the ticket is not overdue. At `due_at + 1` it is.
- `test_overdue_sorted_by_due_time`: create a P3 ticket, move the clock 10 hours, create a P1 ticket. With `now` 100 hours later the order is the P1 ticket, then the P3 ticket. ID order would give the reverse.
- `test_overdue_tie_breaks_on_id`: two tickets with the same due time come back in ID order.
- `test_overdue_appends_no_event`: the event count is the same before and after `svc.overdue()`.

### Step 5. Add CLI tests through a subprocess

File: `tests/test_cli.py`, new. Each test writes a temporary log with `created`, `assigned`, and `closed` events whose `at` lies hours or days before `time.time()`. A helper writes each event with `json.dumps(..., sort_keys=True)` to match LOG-005. Each test then runs `[sys.executable, "-m", "ticketdesk.cli", "--log", path, ...]`.

- `list` prints `OVERDUE` for an overdue open ticket and keeps the normal state for others. It exits 0 with empty stderr (CLI-006, CLI-008).
- `list` keeps ID order when the overdue tickets are not in ID order (TKT-013).
- `overdue` prints only overdue tickets, earliest due first (CLI-010, TKT-015).
- `overdue` prints nothing and exits 0 for a missing log file (LOG-006) and for a log with no overdue tickets.
- `list` and `overdue` leave the log file byte for byte unchanged (LOG-001).

### Step 6. Verify and commit

- Run `make lint && make test` (`AGENTS.md:88-89`, `Makefile:1-5`).
- Run the end-to-end sequences in the test plan below against a temporary log.
- Commit the spec and doc edits from step 1 separately from the code and tests (`docs/guidelines.md:85-86`). Cite TKT-014, TKT-015, CLI-001, CLI-006, and CLI-010 in both messages (`docs/guidelines.md:87`).

## Assumptions validated

Each assumption is load-bearing. The plan fails without it.

- **The due time is already on every replayed ticket.** Confirmed by reading `ticketdesk/tickets.py:34-37`. Replay sets `t.due_at = due_at(ev["at"], ev["priority"])` for each `created` event.
- **Overdue can be derived without a new event.** Confirmed by experiment E2. The replay output was identical before and after computing overdue, so LOG-009 holds.
- **The store's clock is reachable and calling it writes nothing.** Confirmed by `ticketdesk/store.py:14-16`, where `clock` is a public attribute. In E2 the event count stayed at 4 after a `store.clock()` call.
- **Due order differs from ID order.** Confirmed by E2. A P3 ticket created first is due at +72h. A P1 ticket created 10 hours later is due at +14h. Overdue returned `[2, 1]` and ID order is `[1, 2]`. A test that only checks ID-ordered data would miss a missing sort.
- **Closed tickets and the boundary behave as the rule says.** Confirmed by E2. A closed P1 ticket 100 hours past due returned `False`. At `now == due_at` the rule returned `False`, and at `due_at + 0.001` it returned `True`.
- **A hand-written log with past timestamps drives the real CLI.** Confirmed by E1. A crafted 7-event log produced the expected `list` output with exit 0, and the file hash was unchanged afterwards.
- **A subprocess CLI test runs under unittest discovery.** Confirmed by a probe test in scratch. `subprocess.run([sys.executable, "-m", "ticketdesk.cli", ...])` from the repo root passed.
- **`overdue` is a free subcommand name today.** Confirmed by E1. The current CLI rejects it with `invalid choice: 'overdue'` and exit 2. `ticketdesk/cli.py:15-18` registers only four subcommands.
- **`OVERDUE` fits the state column.** Confirmed by count. The word has 7 characters and `ticketdesk/cli.py:30` pads the state to 8.
- **The baseline is green.** Confirmed by `make lint` and `make test`. The suite ran 7 tests, all passing, on Python 3.15.1.

### Hypothesis falsifier

The shape is wrong if overdue must be a recorded transition. That would mean an event when the due time passes, or a flag that survives closing.

Neither holds, so the derived shape survives. Each command is one short process with no scheduler (`docs/architecture.md:5-8`), so nothing could append an event at the moment a ticket becomes overdue. LOG-001 and LOG-002 also rule out a new event written by a read. No spec asks for overdue history.

## Spec and architecture cross-check

| Spec | Effect | Plan step |
|------|--------|-----------|
| TKT-001 states | Unchanged. Overdue is a derived label, not a state. | 1, 2 |
| TKT-005 due time | Reused as the input to the rule. | 2 |
| TKT-013 list order | Unchanged. `list` keeps ID order. | 3, 5 |
| TKT-014, TKT-015 | New. | 1, 2, 4 |
| CLI-001 subcommands | Changes from four to five. Needs sign-off. | 1, 3 |
| CLI-002 log path | `overdue` uses the same `--log` option. | 3 |
| CLI-006 list line | Changes. The state field may show `OVERDUE`. Needs sign-off. | 1, 3, 5 |
| CLI-007 rule errors | `overdue` raises no ticket-rule errors. The open TODO is inherited. | Out of scope |
| CLI-008 exit 0 | `overdue` exits 0 with empty stderr. | 5 |
| CLI-010 | New. | 1, 3, 5 |
| LOG-001 reads append nothing | Holds for `list` and `overdue`. | 4, 5 |
| LOG-002, LOG-003 event kinds | Unchanged. No new event kind. | 2 |
| LOG-006 missing file | `overdue` prints nothing. | 5 |
| LOG-007 corrupt line | `overdue` stops with the same error as `list`. | 3 |
| LOG-009 deterministic replay | Holds. The current time is applied after replay. | 2, 4 |
| INV-001 log is the truth | Holds. Overdue is derived from the log and the clock. | 2 |
| INV-002, INV-003, INV-004 | Untouched. No write path changes. | none |
| INV-005 time from the store | Holds. No new event, and the current time comes from the store's clock. | 2 |

The architecture holds. The rule lives in the service and the label in the CLI. The store keeps sole ownership of the file and the clock. Each command still replays the log once, which `docs/architecture.md:62-63` accepts for this scale. The change adds no auth, network, or async surface.

## Project conventions to follow

- **[`AGENTS.md:12-13`]** Convention: the log is the truth, and nothing in it is edited. **Reflected in plan:** steps 2 and 3 derive overdue at read time and append nothing.
- **[`AGENTS.md:93`, `docs/README.md:39-40`]** Convention: doc and spec changes need user confirmation. **Reflected in plan:** step 1 is gated on sign-off, see open question 6.
- **[`AGENTS.md:96`, `docs/guidelines.md:87`]** Convention: cite spec IDs in code comments, tests, and commits. **Reflected in plan:** steps 2 and 6 name the comments and the IDs.
- **[`docs/README.md:27-28`]** Convention: IDs are stable, and a new spec takes the next free number. **Reflected in plan:** step 1 adds TKT-014, TKT-015, and CLI-010.
- **[`docs/architecture.md:36-38`, `docs/guidelines.md:51-53`]** Convention: the CLI holds no ticket rules. **Reflected in plan:** step 2 puts `is_overdue` in the service, and step 3 only maps it to a label.
- **[`docs/architecture.md:48-50`, `docs/architecture.md:68-69`]** Convention: time comes from the store's injectable clock. **Reflected in plan:** step 2 adds `TicketService.now()` over `store.clock`.
- **[`AGENTS.md:19-25`, `pyproject.toml:5`]** Convention: Python 3.11 or later with no dependencies. There is no package manager and no lockfile. **Reflected in plan:** steps 2 to 5 use only the standard library (`time`, `json`, `subprocess`, `tempfile`).
- **[`Makefile:1-5`, `.github/workflows/ci.yml:11-12`]** Convention: `make lint` and `make test` are the entry points, and CI runs both. **Reflected in plan:** step 6 runs both.
- **[`docs/guidelines.md:9-11`, `docs/guidelines.md:29-31`]** Convention: test every module, naming the test type up front. **Reflected in plan:** step 4 covers the service with unit tests, and step 5 covers the CLI through a subprocess.
- **[`tests/test_tickets.py:8-20`]** Convention: tests inject a fake clock into `EventStore`, with no mocking library. **Reflected in plan:** step 4 reuses the `Clock` fake and moves `clock.now`.
- **[`docs/guidelines.md:32-34`]** Convention: plan e2e command sequences against a temporary log. **Reflected in plan:** the test plan lists them.
- **[`Makefile:4-5`, `docs/architecture.md:81`]** Convention: lint is a `compileall` syntax pass with no style or type checker. **Reflected in plan:** step 6 runs it. No formatter config is added.
- **[`docs/guidelines.md:85-86`]** Convention: one logical change per commit. **Reflected in plan:** step 6 splits the doc commit from the code commit.
- Per-component conventions: doesn't constrain this plan. No directory has its own `AGENTS.md`.
- Migration tooling: doesn't constrain this plan. The log format and the event kinds do not change.
- Ports, URLs, and environment: doesn't constrain this plan. The tool is a local CLI with no network (`docs/architecture.md:64-65`). The only variable is `TICKETDESK_LOG`, and the plan does not touch it.
- Async machinery: doesn't constrain this plan. The tool has none, and overdue needs none.
- Reuse: the plan reuses `svc.list()`, the `due_at` field from replay, and the line format at `ticketdesk/cli.py:30`. No similar logic exists elsewhere in the repo.

## Codebase sweep

- **In-flight work.** None found. `git log --all` shows one commit, `b7942f8`, and the only branch is `main`.
- **Shadow duplication.** None found. A grep for `overdue`, `breach`, `clock`, and `time.time` finds only the store clock and the test fake.
- **Caller-side drift.** The `list` output changes. The only caller in the repo is the `print` at `ticketdesk/cli.py:30`. Scripts outside the repo that parse the state column are a risk, see below.
- **Doc drift.** `AGENTS.md:102` says `make test` runs 7 cases, and `AGENTS.md:116` says the CLI has no tests. Both go stale, so step 1 updates them.
- **Test infrastructure gap.** The CLI has no tests (`AGENTS.md:116`, `docs/architecture.md:103`). Step 5 adds `tests/test_cli.py`, and the scratch probe shows the approach runs.

## Success criteria counterfactual

**Verdict: confirmed with gaps.** Every criterion maps to a step. The single gap is the human sign-off for step 1.

| Success criterion | Plan steps |
|-------------------|------------|
| An open or assigned ticket past its due time shows `OVERDUE` in `list` | 2, 3, tests in 4 and 5 |
| A ticket before its due time, or a closed ticket, shows its normal state | 2, 3, tests in 4 and 5 |
| `ticketdesk overdue` lists only overdue tickets | 2, 3, tests in 4 and 5 |
| `overdue` sorts by due time, earliest first, not by ID | 2, tests in 4 and 5 |
| No regression: 7 existing tests pass, `list` keeps ID order, reads append nothing | 5, 6 |
| Specs and docs match the new behaviour | 1, gated on sign-off |

The change fails if any of these is observed:

- A ticket past its due time still shows `open` or `assigned`.
- A closed ticket appears in `overdue`.
- `overdue` prints in ID order when due order differs.
- `list` or `overdue` changes the log file.

## Test plan

- **Unit, through the service.** The eight cases in step 4 cover the rule, the boundary, closed tickets, the sort, the tie break, and the no-write property.
- **CLI, through a subprocess.** The cases in step 5 cover the wiring, the exact output lines, exit codes, the missing-file case, and the unchanged log.
- **Regression.** The 7 existing tests in `tests/test_tickets.py` and `tests/test_store.py` pass unchanged.
- **Manual end-to-end.** Run these sequences against a temporary log. Write the log by hand, because the real clock cannot reach a due time inside a short session.

```bash
# E2E-1: fresh tickets are never overdue
LOG=$(mktemp -d)/t.jsonl
python3 -m ticketdesk.cli --log $LOG create "Printer on fire" --priority P1
python3 -m ticketdesk.cli --log $LOG list       # "#1 [P1] open     Printer on fire"
python3 -m ticketdesk.cli --log $LOG overdue    # prints nothing, exit 0

# E2E-2: hand-written log, as in scratch/exp1_crafted_log.sh
#   #1 P3 created 100h ago, open      -> overdue, due 28h ago
#   #2 P1 created 10h ago, open       -> overdue, due 6h ago
#   #3 P2 created 1h ago, open        -> not overdue
#   #4 P1 created 50h ago, closed     -> never overdue
#   #5 P2 created 31h ago, assigned   -> overdue, due 7h ago
python3 -m ticketdesk.cli --log $LOG list
#   #1 [P3] OVERDUE  old p3
#   #2 [P1] OVERDUE  new p1
#   #3 [P2] open     fresh p2
#   #4 [P1] closed   closed p1
#   #5 [P2] OVERDUE  assigned p2
python3 -m ticketdesk.cli --log $LOG overdue
#   #1 [P3] OVERDUE  old p3        (due 28h ago)
#   #5 [P2] OVERDUE  assigned p2   (due 7h ago)
#   #2 [P1] OVERDUE  new p1        (due 6h ago)

# E2E-3: closing an overdue ticket removes it from overdue
python3 -m ticketdesk.cli --log $LOG close 5 "Replaced the toner cartridge"
python3 -m ticketdesk.cli --log $LOG overdue    # #1 then #2

# E2E-4: missing log
python3 -m ticketdesk.cli --log /nonexistent/t.jsonl overdue   # prints nothing, exit 0
```

## Risks and mitigations

- **Scripts that parse `list` may break.** A script that expects only `open`, `assigned`, or `closed` in the state column now meets `OVERDUE`. Mitigation: decide open question 1 first. Name the change in the release notes, and consider a minor version bump.
- **The CLI hides the real state of an overdue ticket.** A reader of `list` cannot tell whether an overdue ticket has an assignee. Mitigation: open question 1 offers a marker after the state, which keeps that information.
- **Clock-dependent tests may be flaky near the boundary.** Mitigation: CLI tests place every timestamp hours away from its due time. Unit tests use the fake clock, so they do not depend on wall time.
- **Wall-clock changes shift overdue status.** A system clock that jumps changes `now` but not the stored `at` values. The effect is a wrong label, never a wrong log. Mitigation: none needed at the scale in `docs/architecture.md:62-63`.
- **The crafted-log helper in the tests may drift from the real event format.** Mitigation: the helper writes events with `json.dumps(..., sort_keys=True)`, the same call as `ticketdesk/store.py:22`. A format change would break these tests loudly, not silently.

## Open questions

Nobody was available to answer these during planning. Each one names the assumption the plan proceeds on.

1. **How should `list` show an overdue ticket?** Option A replaces the state with `OVERDUE`, for example `#1 [P1] OVERDUE  Printer on fire`. Option B keeps the state and adds a marker, for example `#1 [P1] open     Printer on fire  OVERDUE`. **Assumption:** option A, the literal reading of "show as OVERDUE". It keeps the CLI-006 line shape.
2. **Can a closed ticket be overdue?** **Assumption:** no. A closed ticket that missed its due time is a breach to report, not work to chase.
3. **Is a ticket overdue at exactly its due time?** **Assumption:** no. "Pass their due time" means strictly later than the due time.
4. **What line format does `overdue` print?** **Assumption:** the CLI-006 line, so `overdue` output is a filtered and reordered `list`. A format with the assignee and the time past due would be more useful but adds a new format to specify.
5. **How should tickets with the same due time be ordered?** **Assumption:** by ID ascending, to keep the output deterministic.
6. **Do you approve the spec and doc edits in step 1?** They change CLI-001 and CLI-006 and add TKT-014, TKT-015, and CLI-010. **Assumption:** approved as written. No code work starts before that approval.
7. **Should this ship as version 0.4.0?** The `list` output changes for existing users. **Assumption:** the version stays at 0.3.0 because the repo records no release convention.

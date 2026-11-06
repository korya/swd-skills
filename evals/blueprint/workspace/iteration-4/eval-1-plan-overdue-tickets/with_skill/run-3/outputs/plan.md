# Plan: overdue tickets in ticketdesk

Status: plan only. No code or doc in the repo changed. All paths are relative to the repo
root, and every `file:line` refers to commit `7c62f26`.

Cold read: one fresh reader checked the plan against the repo and reported five Minor
findings. All five are fixed in this text. None was rejected, and none needs a decision
from the user.

## Headline

Tickets past their due time show `OVERDUE` in `ticketdesk list`, and a new `ticketdesk
overdue` lists them by due time. The ticket service derives overdue on each read and
stores nothing, so the log format, the three states, and every invariant stay as they
are. One decision blocks the code work: your sign-off on the spec text for CLI-001,
CLI-006, and the new CLI-010, TKT-014, and TKT-015.

## Approach summary

The ticket service decides what overdue means, and the command line only prints the
result. After the service replays the log, it reads the clock of the store once. It marks
every ticket that is not closed and whose due time is earlier than that reading.
`ticketdesk list` prints `OVERDUE` in place of the state for a marked ticket and keeps the
ID order. `ticketdesk overdue` prints only the marked tickets, sorted by due time and then
by ID.

The store, the SLA table, the log format, and the output of `create`, `assign`, and
`close` stay untouched. The approach stands on one checked fact: event timestamps and the
read-time clock come from the same injectable clock. A second checked fact is that
`OVERDUE` fits the 8-character state column. The main trade-off is that an overdue line no
longer shows whether the ticket is `open` or `assigned`. In return the line format keeps
its four fields, and old logs work with no migration.

What the user sees, from the prototype run on a hand-written log:

| Command | Today | After the change |
|---|---|---|
| `list`, ticket past due | `#1 [P3] open     old P3` | `#1 [P3] OVERDUE  old P3` |
| `list`, ticket closed late | `#3 [P2] closed   old closed` | `#3 [P2] closed   old closed` |
| `list`, ticket not yet due | `#4 [P1] open     far future` | `#4 [P1] open     far future` |
| `overdue` | usage error, exit code 2 | `#2 [P1] OVERDUE  old P1` then `#1 [P3] OVERDUE  old P3` |

## Out of scope

- **Recording overdue in the log.** No new event kind, no new event field, no fourth
  state. LOG-002, LOG-003, and TKT-001 stay as written.
- **History of lateness.** The plan does not show that a closed ticket was closed late.
  See open question 2.
- **The CLI-007 conflict.** A corrupt log and an unknown priority still escape as a
  traceback (`docs/product-specs/cli.md:50-52`). `overdue` inherits that behavior from
  `list`. See open question 5.
- **Business hours.** Due time stays wall-clock hours. `docs/architecture.md:123-124`
  lists business hours as a future path.
- **Showing the due time or the delay** on a line. See open question 4.
- **Tests for `create`, `assign`, and `close` through the CLI.** The plan adds CLI tests
  for `list` and `overdue` only. The coverage target is an open TODO at
  `docs/guidelines.md:10-11`.
- **Notifications, colors, a `--json` output, and a version bump.** See open question 6
  for the version.
- **A `.gitignore`.** The repo has none, so `make lint` leaves untracked `__pycache__`
  directories. This is an existing condition.

## Plan

Each step is one commit and leaves `make lint && make test` green. Steps 1 to 4 start only
after step 0. No file in the repo changes before the sign-off.

### Step 0. Get sign-off on the spec text (blocking)

The repo forbids a silent spec change (`AGENTS.md:93`, `docs/README.md:39`,
`docs/guidelines.md:78-80`). Show the user the text in step 1 and the open questions.
Answers to questions 1 to 3 change the text of TKT-014 and CLI-006.

### Step 1. Specs: `docs/product-specs/tickets.md` and `docs/product-specs/cli.md`

Add two ticket specs after TKT-013 (`docs/product-specs/tickets.md:83-85`). TKT-014 and
TKT-015 are the next free numbers.

> ### TKT-014: Overdue
>
> A ticket is overdue when its state is `open` or `assigned` and the current time is later
> than its due time. A ticket at exactly its due time is not overdue. A `closed` ticket is
> never overdue, whenever it was closed. Overdue is not a state and is not recorded in the
> log. It is derived from the due time and the current time each time tickets are read.
>
> ### TKT-015: Overdue listing order
>
> The overdue listing returns only the overdue tickets, sorted by due time ascending.
> Tickets with the same due time are sorted by ID ascending.

Change two command specs and add one. CLI-010 is the next free number after CLI-009
(`docs/product-specs/cli.md:58`).

> ### CLI-001: Commands
>
> The `ticketdesk` command takes one of five subcommands. They are `create`, `assign`,
> `close`, `list`, and `overdue`. Invoking `ticketdesk` with no subcommand, or with an
> unknown one, prints usage to stderr and exits with code 2.
>
> ### CLI-006: list
>
> `ticketdesk list` prints one line per ticket in ID order, see TKT-013. Each line is
> `#<id> [<priority>] <status> <title>` with the status padded to 8 characters. The status
> is `OVERDUE` for an overdue ticket, see TKT-014, and the state of the ticket otherwise.
> With no tickets it prints nothing.
>
> ### CLI-010: overdue
>
> `ticketdesk overdue` prints one line per overdue ticket in the order of TKT-015. Each
> line has the format of CLI-006. With no overdue tickets it prints nothing. The command
> appends no event, see LOG-001.

The TODO under CLI-007 stays as it is.

### Step 2. Service rule: `ticketdesk/tickets.py` and `tests/test_tickets.py`

- `Ticket` (`ticketdesk/tickets.py:12-21`): add the field `overdue: bool = False` after
  `due_at`. The default keeps the one constructor call at `ticketdesk/tickets.py:35`
  valid.
- `_tickets()` (`ticketdesk/tickets.py:30-44`): after the replay loop, read
  `self.store.clock()` once into `now`. Then set `t.overdue = t.state != "closed" and now >
  t.due_at` on every ticket. Add the comment `# TKT-014`.
- New method `overdue()` next to `list()` (`ticketdesk/tickets.py:46-47`). It returns the
  marked tickets sorted with `key=lambda t: (t.due_at, t.id)`. Add the comment `# TKT-015`.
- `list()` does not change. It keeps the ID order and returns every ticket (TKT-013).
- Add the unit tests U1 to U10 from the test plan to `tests/test_tickets.py`.

Setting the mark inside `_tickets()` gives every ticket the service returns a correct
mark. A mark set only in `list()` would leave `get()` and `assign()` returning `False` for
a late ticket. One clock reading per replay also gives every line of one command the same
"now".

`ticketdesk/sla.py`, `ticketdesk/store.py`, and `ticketdesk/__init__.py` do not change.

### Step 3. Command line: `ticketdesk/cli.py` and `tests/test_cli.py`

- Add `sub.add_parser("overdue")` after `ticketdesk/cli.py:18`.
- Add a module-level helper `_line(t)` that returns the list line. The label is `OVERDUE`
  when `t.overdue` is true and `t.state` otherwise, padded with `:<8`.
- Replace the `else` at `ticketdesk/cli.py:28` with `elif args.cmd == "list"`.
- Add `elif args.cmd == "overdue"` that prints `_line(t)` for each ticket of
  `svc.overdue()`. Leave no bare `else` in the chain.
- Leave `ticketdesk/cli.py:23`, `:25`, and `:27` alone. `create`, `assign`, and `close`
  keep printing the stored state (CLI-003 to CLI-005).
- Add the new file `tests/test_cli.py` with the subprocess tests C1 to C5.

The `else` branch is a trap. Today it handles every command that is not `create`,
`assign`, or `close`. A new subcommand without its own branch would print the full list.
The prototype kept a bare `else` for `overdue`, which only moves the trap. The final code
names every command, and argparse already rejects an unknown one (`ticketdesk/cli.py:14`).

### Step 4. Other docs, after the same sign-off

Step 4 updates every passage that the change makes stale. The table gives the proposed
text of each one. The test count of 22 is the 7 existing tests plus U1 to U10 and C1 to
C5.

| Where | Proposed text |
|---|---|
| `AGENTS.md:47` | `├── tests/              unittest suites for the service, the store, and the CLI` |
| `AGENTS.md:82`, summary cell | Ticket states, creation, assignment, closing, due time by priority, overdue, listing. |
| `AGENTS.md:102` | `make test                                   # 22 unittest cases` |
| `AGENTS.md:106`, new line after it | `python3 -m ticketdesk.cli --log /tmp/t.jsonl overdue` |
| `AGENTS.md:114-115` | - Done: create, assign, close, list, overdue. Due time by priority. Overdue derived on each read. Append-only log with fail-fast replay. Tests for the service, the store, and the `list` and `overdue` commands. |
| `AGENTS.md:116` | - Not covered by tests: the `create`, `assign`, and `close` commands of the CLI. |
| `docs/architecture.md:12` | `             │ create / assign / close / list / overdue` |
| `docs/architecture.md:68-69`, appended sentence | The service reads the same clock to decide whether a ticket is overdue, see TKT-014. |
| `docs/architecture.md:95-96`, new line between them | `│   ├── test_cli.py     list and overdue through a subprocess` |
| `docs/architecture.md:103` | The CLI tests cover `list` and `overdue` only. Service and store are tested directly. |
| `docs/guidelines.md:10-11`, one sentence | The CLI has tests for `list` and `overdue` only. |
| `docs/product-specs/README.md:80`, second cell | Ticket lifecycle: states, creation rules, assignment, closing, due time by priority, overdue, listing. |

### Step 5. Verify and hand over

Run `make lint && make test`, then the end-to-end sequences E1 to E3 from the test plan.
Run the tests once more with `/opt/homebrew/bin/python3.12`, the version that CI uses
(`.github/workflows/ci.yml:10-12`). The repo has no git remote, so the plan cannot name a
push target. CI runs when the user adds one.

### Specs and invariants the plan upholds

| ID | Requirement | How the plan meets it |
|---|---|---|
| INV-001 | The log is the only source of state | Step 2 derives the mark from the replay and the clock. No file or cache is added. |
| INV-002, LOG-008 | Events are never edited | No step writes to the log. Tests U10 and C2 compare the log before and after. |
| INV-004, LOG-007 | A corrupt line fails fast | `overdue` uses the same replay as `list`. Step 3 adds no `except`. |
| INV-005, LOG-004 | Event time comes from the clock of the store | No new event. Step 2 reads the same clock for "now". |
| TKT-001 | Three states | Step 2 adds a derived mark, not a state. `STATES` at `ticketdesk/tickets.py:5` does not change. Test U3 asserts the state. |
| TKT-005 | Due time by priority | `ticketdesk/sla.py` does not change. Step 2 compares against the existing `due_at`. |
| TKT-013 | `list` returns every ticket in ID order | `list()` does not change. Tests U8 and C1 assert the order. |
| LOG-001 | Listing appends nothing | Tests U10 and C2. |
| LOG-002, LOG-003 | Event kinds and fields | No change. |
| LOG-009 | Replay is deterministic | States, assignees, resolutions, and due times still depend on the log alone. The mark also depends on the time, and TKT-014 says so. |
| CLI-001 | Four subcommands | **Changes** to five. Step 1, needs sign-off. |
| CLI-002 | Log path selection | `overdue` uses the same `--log` option (`ticketdesk/cli.py:13`). |
| CLI-003 to CLI-005 | Output of `create`, `assign`, `close` | Step 3 leaves these lines alone. E2 shows `#1 assigned -> dana` for an overdue ticket. |
| CLI-006 | Line format of `list` | **Changes**. The third field can be `OVERDUE`. Step 1, needs sign-off. |
| CLI-007 | Ticket rule errors | `overdue` rejects nothing. The open TODO is out of scope. |
| CLI-008 | Exit code 0, empty stderr | Tests C1 to C3. |
| TKT-014, TKT-015, CLI-010 | New | Steps 1 to 3, need sign-off. |

## Assumptions validated

All experiments ran on a copy of the repo, on Python 3.15.2. The copy is in the directory
`scratch/` next to this plan, outside the repo. The prototype of steps 2 and 3 is in
`scratch/proto/`, and its diff is `scratch/proto.diff`.

**Falsifier.** The shape is wrong if overdue must survive as history, or if "now" and the
event timestamps come from different clocks. It is also wrong if code in the repo parses
the state column. Result: not falsified.

- The request asks for a display and a filter. Neither needs a stored record.
- Even "closed late" needs no new event. The `closed` event already carries `at`
  (`docs/product-specs/event-log.md:21-23`).
- `at` comes from `self.clock()` at `ticketdesk/store.py:20`, and the service holds that
  store (`ticketdesk/tickets.py:27-28`).
- A grep for `.state`, `.list(`, and `:<8` over the Python files finds one consumer of the
  list line: `ticketdesk/cli.py:30`. No test or script parses the output.

**A1. The due time of every ticket is already derived on replay.** Verified at
`ticketdesk/tickets.py:36`. A read of a hand-written log printed these values:

```text
1 P3 open 1000.0 260200.0
2 P1 open 2000.0 16400.0
3 P2 closed 3000.0 89400.0
4 P1 open 4102444800.0 4102459200.0
```

**A2. The service can read "now" from the clock that stamps events.** This was the risky
one, and the prototype confirmed it. `EventStore` keeps the injected clock as `self.clock`
(`ticketdesk/store.py:14-16`). In the prototype, a ticket with the clock set exactly to
`due_at` was not overdue. With the clock at `due_at + 0.001` it was overdue.

**A3. `OVERDUE` fits the state column.** Confirmed. `python3 -c` printed the padded label,
the widest state, and the length of the label:

```text
'OVERDUE ' 'assigned' 7
```

**A4. A hand-written log with old timestamps makes overdue tickets without a wait.**
Confirmed. `tests/test_store.py:12` already writes a log by hand. The unchanged CLI read a
five-line log with `at` values of 1000.0 to 3500.0 and one of 4102444800.0:

```text
#1 [P3] open     old P3
#2 [P1] open     old P1
#3 [P2] closed   old closed
#4 [P1] open     far future
```

The prototype printed this for `list` and then for `overdue` on the same log:

```text
#1 [P3] OVERDUE  old P3
#2 [P1] OVERDUE  old P1
#3 [P2] closed   old closed
#4 [P1] open     far future
```

```text
#2 [P1] OVERDUE  old P1
#1 [P3] OVERDUE  old P3
```

**A5. One more clock reading per replay breaks no existing test.** Confirmed. The fake
clock at `tests/test_tickets.py:8-14` moves one second per reading. No test asserts an
absolute timestamp. The seven existing tests passed on the prototype:

```text
Ran 7 tests in 0.008s

OK
```

**A6. Subprocess tests of the CLI run under `make test`.** Confirmed with two prototype
tests in `tests/test_cli.py` and two in a service test file. The subprocess needs `cwd`
set to the repo root so that `python -m ticketdesk.cli` resolves.

```text
Ran 11 tests in 0.067s

OK
```

**A7. The name `overdue` is free.** Verified. Today the command is a usage error with exit
code 2:

```text
usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...
ticketdesk: error: argument cmd: invalid choice: 'overdue' (choose from 'create', 'assign', 'close', 'list')
```

**A8. Both read commands append nothing.** Confirmed on the prototype. The log had five
lines before and after `list` and `overdue`. `overdue` on a missing log printed nothing,
exited with code 0, and did not create the file (LOG-006).

**A9. The spec numbers are free.** Verified. The last ticket spec is TKT-013
(`docs/product-specs/tickets.md:83`) and the last command spec is CLI-009
(`docs/product-specs/cli.md:58`).

**A10. The planned tests catch a wrong rule.** Partial. Four wrong variants of the
prototype each failed at least one test. The variant that sorts by ID failed only the CLI
test, because the service test used a case where both orders agree. Test U6 fixes that.

| Wrong variant | Tests that failed |
|---|---|
| `now >= t.due_at` | the boundary test |
| closed tickets not excluded | three tests |
| sort by ID | the CLI order test only |
| ties by descending ID | the tie test |

**A11. The prototype also passes on Python 3.12, the version of CI.** Confirmed after the
cold read. `/opt/homebrew/bin/python3.12 --version` prints `Python 3.12.16`. The syntax
pass exited with code 0, and the prototype tests printed this:

```text
Ran 11 tests in 0.070s

OK
```

## Project conventions to follow

- **[`AGENTS.md:25`, `docs/architecture.md:76`]** Convention: no dependencies beyond the
  standard library. **Reflected in plan:** steps 2 and 3 add none. The tests use
  `subprocess`, `json`, and `tempfile`.
- **[`AGENTS.md:88`, `Makefile:2-5`, `docs/guidelines.md:12-13`]** Convention: `make lint
  && make test` before every push. **Reflected in plan:** every step ends green, and step 5
  runs both.
- **[`AGENTS.md:103-106`]** Convention: run the tool as `python3 -m ticketdesk.cli --log
  <path> <command>`. **Reflected in plan:** the CLI tests and the end-to-end sequences use
  this form.
- **[`AGENTS.md:22`, `docs/architecture.md:80`]** Convention: tests use `unittest` under
  `tests/`. **Reflected in plan:** steps 2 and 3 add `unittest.TestCase` classes there.
- **[`docs/architecture.md:49-50`, `tests/test_tickets.py:8-20`]** Convention: tests
  inject a fake clock into the store. They do not patch `time`. **Reflected in plan:** the
  unit tests inject a settable clock, and the CLI tests use a log with fixed timestamps.
- **[`docs/guidelines.md:29-31`]** Convention: name the test files, the cases, and the
  type, either unit through the service or subprocess through the CLI. **Reflected in
  plan:** the test plan does this for U1 to U10 and C1 to C5.
- **[`docs/guidelines.md:32-34`]** Convention: a user-visible change names end-to-end
  command sequences against a temporary log. **Reflected in plan:** sequences E1 to E3.
- **[`docs/architecture.md:36-38`, `docs/guidelines.md:52-53`]** Convention: the CLI holds
  no ticket rule. **Reflected in plan:** step 2 puts the rule in the service. Step 3 only
  picks a label.
- **[`docs/architecture.md:68-69`]** Convention: time comes from the clock of the store,
  never from the caller. **Reflected in plan:** step 2 reads `self.store.clock()`. The CLI
  never calls `time.time()`.
- **[`AGENTS.md:96`, `docs/README.md:43-44`]** Convention: cite spec IDs in code comments,
  tests, and commits. **Reflected in plan:** steps 2 and 3 cite TKT-014, TKT-015, CLI-006,
  and CLI-010.
- **[`docs/README.md:27-28`]** Convention: spec IDs are stable, and a new spec gets the
  next free number. **Reflected in plan:** step 1 adds TKT-014, TKT-015, and CLI-010 and
  renumbers nothing.
- **[`AGENTS.md:93`, `docs/guidelines.md:78-80`]** Convention: the user confirms every doc
  change. **Reflected in plan:** step 0 gates steps 1 to 4. Steps 1 and 4 hold every doc edit.
- **[`docs/guidelines.md:84-87`]** Convention: one logical change per commit, with the
  spec ID in the message. **Reflected in plan:** one commit per step. The one existing
  commit uses a Conventional Commits subject, so the new subjects follow that form.
- **[`AGENTS.md:23`, `docs/architecture.md:81`]** Convention: lint is a `compileall`
  syntax pass. **Reflected in plan:** no formatter or type checker is added.
- **[`AGENTS.md:19`, `.github/workflows/ci.yml:10`]** Convention: Python 3.11 or later,
  and CI on 3.12. **Reflected in plan:** steps 2 and 3 use no newer syntax, and step 5
  runs the tests on Python 3.12.
- **Migrations.** This category does not constrain the plan. State comes from replay
  (`docs/architecture.md:44`), and the log format does not change.
- **Ports, URLs, and async machinery.** These do not constrain the plan. The tool is one
  local command per invocation with no network (`docs/architecture.md:64-65`).
- **Existing patterns to reuse.** The sort with a key at `ticketdesk/tickets.py:47`, the
  temporary directory at `tests/test_tickets.py:19`, and the hand-written log at
  `tests/test_store.py:12`.

The codebase sweep found no competing work and one gap in test infrastructure.

- **In-flight work.** The repo has one commit, one branch (`main`), and no stash. A grep
  for "overdue" finds nothing.
- **Duplicate logic.** The list line exists once, at `ticketdesk/cli.py:30`. Step 3 moves
  it into one helper that both commands use.
- **Callers of a changed contract.** `Ticket` is built in one place
  (`ticketdesk/tickets.py:35`). `svc.list()` has one caller (`ticketdesk/cli.py:29`).
- **Test infrastructure.** Service tests with a fake clock exist. Subprocess tests of the
  CLI do not (`AGENTS.md:116`). Step 3 builds that layer, and A6 shows that it works.

## Test plan

**Unit tests through the service** go in `tests/test_tickets.py`, in a new class
`OverdueTests`. The class injects a settable clock that does not move by itself. The
existing `Clock` moves one second per reading, which makes a boundary test fragile.

- U1 `test_new_ticket_is_not_overdue`. A new P1 ticket has `overdue` false (TKT-014).
- U2 `test_not_overdue_at_exact_due_time`. With the clock equal to `due_at`, the mark is
  false (TKT-014).
- U3 `test_overdue_after_due_time`. Just past `due_at`, the mark is true and the state is
  still `open` (TKT-014, TKT-001).
- U4 `test_assigned_ticket_can_be_overdue`. An assigned ticket past due has state
  `assigned` and the mark true.
- U5 `test_closed_ticket_is_never_overdue`. Closing a late ticket clears the mark and
  removes the ticket from `overdue()`.
- U6 `test_overdue_sorted_by_due_time`. Create a P3 ticket and then a P1 ticket. Past both
  due times, `overdue()` returns IDs `[2, 1]` (TKT-015).
- U7 `test_overdue_ties_break_by_id`. A P3 ticket and a P1 ticket created 68 hours later
  share a due time. The lower ID comes first (TKT-015).
- U8 `test_list_keeps_id_order_with_overdue_tickets`. `list()` still returns every ticket
  in ID order (TKT-013).
- U9 `test_overdue_is_empty_without_late_tickets`. An empty log and a log of new tickets
  both return `[]`.
- U10 `test_reading_appends_nothing`. `list()` and `overdue()` leave the event count
  unchanged (LOG-001).

**Subprocess tests through the CLI** go in the new file `tests/test_cli.py`. Each test
writes a log by hand into a temporary directory and runs `sys.executable -m
ticketdesk.cli --log <path>`. Past tickets use `at` values near 1000.0. Tickets that must
not be overdue use 4102444800.0, the start of the year 2100. No test sleeps or patches
time.

- C1 `test_list_shows_overdue_in_state_column`. The exact four lines from A4, exit code 0,
  and empty stderr (CLI-006, CLI-008).
- C2 `test_overdue_lists_oldest_due_first`. The exact two lines from A4, in that order.
  The bytes of the log do not change (CLI-010, TKT-015, LOG-001).
- C3 `test_overdue_prints_nothing_without_late_tickets`. A missing log gives empty stdout
  and exit code 0, and the file is not created (CLI-010, LOG-006).
- C4 `test_unknown_subcommand_exits_2`. `ticketdesk bogus` exits with code 2, and the
  usage on stderr names `overdue` (CLI-001).
- C5 `test_list_line_unchanged_for_tickets_not_overdue`. A log with only year-2100
  timestamps prints the lines of today, including an `assigned` line.

**End-to-end sequences** run by hand against a temporary log.

- E1, a new log. Run `create "Printer on fire" --priority P1`, then `list`, then
  `overdue`. Expect `#1 [P1] open     Printer on fire` from `list` and nothing from
  `overdue`.
- E2, an aged log. Write the five-line log of A4. Run `list`, `overdue`, `assign 1 dana`,
  `list`, `close 2 "Replaced the toner cartridge"`, `overdue`, `list`. Expect the outputs
  of A4 first. After the assign, ticket 1 still shows `OVERDUE`. After the close,
  `overdue` prints only ticket 1 and `list` shows ticket 2 as `closed`.
- E3, a corrupt log. Run `overdue` on a file that holds `not json`. Expect the same
  traceback and exit code 1 that `list` gives today. This records the CLI-007 gap.

E1 and E2 ran on the prototype with these results. E3 ran on the unchanged code with
`list` only.

**Manual.** Read the usage line once for the five subcommands. No other manual test.

## Risks and mitigations

- **An overdue line hides the state.** In E2 the line of ticket 1 stayed `#1 [P3] OVERDUE
  old P3` after `assign 1 dana`. A reader cannot see that someone owns the ticket.
  Mitigation: open question 1. The alternative costs one line in `_line(t)`.
- **A script outside the repo may parse the third field.** It would meet a value that is
  not a state. The repo holds no such script. Mitigation: name the change in the commit
  message and in CLI-006.
- **A title can contain the word.** `grep OVERDUE` on the list output also matches a
  title. Mitigation: `ticketdesk overdue` is the filter, and CLI-010 says so.
- **The system clock can move.** A clock set back hides overdue tickets until it catches
  up. Events have the same exposure today. No mitigation planned.
- **A change of the SLA table changes old tickets.** The due time is derived on replay
  (`ticketdesk/tickets.py:36`), so new hours can make old open tickets overdue at once.
  This property exists today. The label makes it visible.
- **`overdue` on a corrupt log prints a traceback.** It inherits the CLI-007 gap.
  Mitigation: open question 5.
- **CI cannot run yet.** `git remote -v` prints nothing, so no push starts the workflow.
  Mitigation: step 5 runs the tests on a local Python 3.12, and A11 shows that this works.
- **A future test may assert an absolute timestamp.** One more clock reading per replay
  moves the fake clock one second further. Mitigation: A5 shows that no test does so today.

## Counterfactual

Verdict: **Confirmed with gaps.** Every success criterion has a plan step. The gaps are
the spec sign-off and the first three open questions.

| Success criterion | Plan step | Evidence or test |
|---|---|---|
| `list` shows `OVERDUE` for a ticket that is not closed and is past due | Steps 2 and 3 | U3, U4, C1, A4 |
| Other `list` lines stay the same, in ID order | Steps 2 and 3 | U8, C5 |
| `overdue` prints only overdue tickets, earliest due time first | Steps 2 and 3 | U6, U7, C2 |
| Both commands are read-only and exit with code 0 | Steps 2 and 3 | U10, C2, C3, A8 |
| No change to the log format, the states, or stored data | Step 2 | spec table, U3 |
| The rule is in the service, and lint and tests pass | Steps 2, 3, 5 | A5, A6 |
| Specs and docs describe the behavior | Steps 0, 1, 4 | blocked on sign-off |

The change fails if a late open ticket shows its plain state or a closed ticket shows
`OVERDUE`. It fails if `overdue` prints in ID order where the due order differs. It also
fails if the log grows after a read or an existing test breaks.

## Open questions

Nobody was available during planning. Each question has the assumption that the plan
proceeds on. None is settled.

1. **Does `OVERDUE` replace the state, or sit next to it?** Assumption: it replaces the
   state in the third field, as "show as OVERDUE" reads. The alternative keeps the state
   and adds a marker, such as `#1 [P3] assigned OVERDUE old P3`. That keeps the owner
   visible and adds a fifth field.
2. **Is a closed ticket ever overdue?** Assumption: no, also when it was closed after its
   due time. The log holds the close time, so "closed late" is possible later.
3. **Is a ticket overdue at exactly its due time?** Assumption: no. "Pass their due time"
   reads as strictly later.
4. **What does a line of `ticketdesk overdue` show?** Assumption: the same line as `list`,
   with the `OVERDUE` label. Alternatives are the real state, the due time, or the delay.
5. **Should `overdue` handle a corrupt log better than `list` does?** Assumption: no. The
   TODO under CLI-007 stays open, and both commands behave alike.
6. **Does this change bump the version?** Assumption: no. The repo records no release
   rule. `pyproject.toml:3` and `AGENTS.md:10` stay at 0.3.0.
7. **Do you approve the spec text in step 1 and the doc text in step 4?** Assumption: the
   text stands as drafted, and the rest of the plan builds on it. This is the blocking
   decision. No file in the repo changes before it.

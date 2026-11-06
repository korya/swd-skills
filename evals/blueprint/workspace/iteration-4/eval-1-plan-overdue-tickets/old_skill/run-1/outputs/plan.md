# Plan: overdue tickets in `ticketdesk list` and a new `ticketdesk overdue` command

Date: 2026-11-05. Repo state: commit `fd2ee32` on `main`. Status: plan only, nothing is
implemented.

## Headline

The service computes overdue at read time from the due time, the state, and the store
clock. The log, the three states, and the replay do not change, so no invariant moves. The
user must sign off the spec text below before the code work, because it rests on three
display assumptions.

## Approach summary

A ticket is overdue when it is not closed and the store clock reads later than its due
time. The rule lives in `ticketdesk/tickets.py` as `Ticket.is_overdue(now)`, next to the
other ticket rules. `TicketService` gets `now()`, which reads the store clock, and
`overdue()`, which returns the overdue tickets sorted by due time and then by ID.
`ticketdesk/cli.py` gets an `overdue` subcommand and prints the word `OVERDUE` in the state
column of `list` for an overdue ticket. The store, the SLA table, the event kinds, and the
replay stay untouched, and no read command writes to the log.

The main trade-off is in `list`, where an overdue line shows `OVERDUE` in place of `open` or
`assigned`. So `list` no longer tells whether an overdue ticket has an owner, and the
`overdue` command covers that loss by printing the true state. The plan relies on a due time
for every ticket at replay and on the injectable store clock, and both are verified.

A spike of this design passed 15 tests and five mutation checks, and it printed this output:

```text
$ ticketdesk list
#1 [P3] OVERDUE  old p3
#2 [P1] OVERDUE  old p1
#3 [P1] closed   closed late
#4 [P1] open     fresh
$ ticketdesk overdue
#2 [P1] assigned old p1
#1 [P3] open     old p3
```

Ticket 2 has the higher ID but the earlier due time, so `overdue` prints it first.

## Out of scope

- **A fourth state or a new event kind.** TKT-001 and LOG-002 stay as they are.
- **The open conflict under CLI-007.** A corrupt log and an unknown priority still end in a
  traceback with exit code 1. The new command inherits that behavior, see the risks.
- **"Closed late" reporting.** A ticket that was closed after its due time is not shown as
  overdue anywhere.
- **Extra columns.** No due time, no assignee, and no "hours late" in any output line.
- **Filters and flags.** No `list --overdue`, no `--json`, no color.
- **Notifications, business hours, and per-customer targets.**
- **A version bump.** `pyproject.toml` stays at 0.3.0, see the open questions.

## Plan

1. **Get sign-off on the spec text. This step gates every later step.** The repo rule is
   "Doc changes need user confirmation" (`AGENTS.md:93`). The proposed text is in the table
   below. Open questions 1 to 3 decide whether it stands.
2. **Edit the product specs** with the signed-off text.

   | File | Item | Change | Proposed text |
   |---|---|---|---|
   | `docs/product-specs/tickets.md` | TKT-014, new | Defines overdue | "A ticket is overdue when its state is `open` or `assigned` and the current time is later than its due time. A ticket whose due time equals the current time is not overdue. A `closed` ticket is never overdue. Overdue is not a state and is not recorded in the log." |
   | `docs/product-specs/tickets.md` | TKT-015, new | Defines the order | "Listing overdue tickets returns only the overdue tickets, sorted by due time ascending. Tickets with the same due time are sorted by ID ascending." |
   | `docs/product-specs/cli.md` | CLI-001 | Four subcommands become five | "takes one of five subcommands. They are `create`, `assign`, `close`, `list`, and `overdue`." |
   | `docs/product-specs/cli.md` | CLI-006 | The third column becomes a status | "Each line is `#<id> [<priority>] <status> <title>` with the status padded to 8 characters. The status is `OVERDUE` for an overdue ticket, see TKT-014, and the state otherwise." |
   | `docs/product-specs/cli.md` | CLI-010, new | Defines the command | "`ticketdesk overdue` prints one line per overdue ticket in the order of TKT-015. Each line is `#<id> [<priority>] <state> <title>` with the state padded to 8 characters. With no overdue tickets it prints nothing." |
   | `docs/product-specs/event-log.md` | LOG-001 | Names the new read command | "Listing tickets, overdue ones included, appends nothing." |

   TKT-014, TKT-015, and CLI-010 are the next free numbers (`docs/README.md:27-28`).
3. **Add the rule and the query to `ticketdesk/tickets.py`.**
   - `Ticket.is_overdue(self, now)` returns `self.state != "closed" and now > self.due_at`.
     Add the comment `# implements TKT-014`.
   - `TicketService.now(self)` returns `self.store.clock()`.
   - `TicketService.overdue(self)` reads `now()` once, filters `_tickets()` with
     `is_overdue(now)`, and sorts by `(due_at, id)`. Add the comment `# implements TKT-015`.
   - `_tickets()`, `list()`, `get()`, `create()`, `assign()`, and `close()` do not change.
4. **Add the command and the status column to `ticketdesk/cli.py`.**
   - Add `sub.add_parser("overdue")` after line 18.
   - Add an explicit `elif args.cmd == "overdue":` branch before the `else:` on line 28.
     Without it the new command falls into the `list` branch and prints every ticket.
   - Move the line format of line 30 into one helper, for example `_line(t, status)`.
   - The `overdue` branch prints `_line(t, t.state)` for each ticket of `svc.overdue()`.
   - The `list` branch reads `svc.now()` once. It prints `_line(t, "OVERDUE")` when
     `t.is_overdue(now)` is true, and `_line(t, t.state)` otherwise.
5. **Add service tests to `tests/test_tickets.py`.** They reuse the existing `Clock` and
   `setUp`. A test moves time with `self.store.clock.now += hours * 3600`. The cases are in
   the test plan.
6. **Add `tests/test_cli.py`, the first CLI test file.** Each test writes a seeded log into
   a temporary directory and runs `sys.executable -m ticketdesk.cli --log <path>` as a
   subprocess. The working directory is the repo root, taken from `Path(__file__)`.
7. **Update the lines that the change makes stale**, under the same sign-off as step 1.

   | File and line | Stale text | Becomes |
   |---|---|---|
   | `AGENTS.md:102` | `# 7 unittest cases` | The new count. The spike has 15. |
   | `AGENTS.md:114` | "Done: create, assign, close, list." | Adds overdue. |
   | `AGENTS.md:116` | "Not covered by tests: the CLI." | Names what `tests/test_cli.py` covers and what it does not. |
   | `AGENTS.md:82`, `AGENTS.md:84` | Summaries of `tickets.md` and `cli.md` | Mention overdue. |
   | `docs/architecture.md:12` | `create / assign / close / list` | Adds `overdue`. |
   | `docs/architecture.md:94-96` | Test layout | Adds `test_cli.py`. |
   | `docs/architecture.md:103` | "The CLI is not covered by tests today." | States the partial coverage. |
   | `docs/guidelines.md:10-11` | "The CLI has no tests today." | States the partial coverage. The TODO on a coverage target stays. |
   | `docs/product-specs/README.md:80`, `:82` | Index summaries | Mention overdue. |

8. **Verify and commit.** Run `make lint && make test`, then the end-to-end sequences of the
   test plan. Make one commit for the feature with its specs and tests. The message
   references TKT-014, TKT-015, and CLI-010.

## Assumptions validated

All experiments ran on 2026-11-05 in copies of the repo under `outputs/scratch/`. The repo
itself has no change. The spike diff is `outputs/scratch/spike.diff`.

**The falsifier did not hold.** It says that a flag computed at read time is the wrong
shape if overdue must be a durable fact. A durable fact means a logged event or a fourth
state. The specs speak against both.

- LOG-002 fixes the event kinds at three (`docs/product-specs/event-log.md:17-19`).
- LOG-001 says that listing appends nothing (`event-log.md:12-15`).
- TKT-001 fixes the states at three (`docs/product-specs/tickets.md:15-18`).

The log also loses nothing without an overdue event. The due time of every ticket is
computable from its `created` event at any later moment.

| # | Assumption | Class | Evidence | Result |
|---|---|---|---|---|
| A1 | Every ticket has a due time after replay, so overdue needs no new data. | Verified | `ticketdesk/tickets.py:35-36` sets `due_at` for every `created` event. | confirmed |
| A2 | The service can read "now" from the store clock without a store change. | Risky | `ticketdesk/store.py:14-16`: `clock` is a public attribute with an injectable default. The spike calls `self.store.clock()` and passes. | confirmed |
| A3 | Tests can move time with the existing fake clock. | Plausible | `tests/test_tickets.py:8-14`: `Clock` has a `now` attribute. Spike tests add `5 * HOUR` to it and pass. | confirmed |
| A4 | The replay stays free of time. | Risky | Spike script: `chosen shape: Ticket equal before/after due time: True`. One `create` still reads the clock once. | confirmed |
| A5 | `OVERDUE` fits the state column. | Plausible | The column is 8 wide (`ticketdesk/cli.py:30`). `OVERDUE` has 7 characters. Spike output: `#1 [P1] OVERDUE  ancient`. | confirmed |
| A6 | A new subparser alone is not enough. | Risky | With only `sub.add_parser("overdue")` added, `ticketdesk overdue` printed both tickets of the log with exit 0. `cli.py:28` is a bare `else:`. | confirmed, drives step 4 |
| A7 | `list` has one caller, so its contract is safe to keep. | Verified | `grep` finds `svc.list()` only at `ticketdesk/cli.py:29`. No test calls it. | confirmed |
| A8 | A CLI test can make a ticket overdue without a clock option. | Plausible | A hand-written line `{"at": 1, "id": 1, "kind": "created", "priority": "P1", "title": "ancient"}` lists as `OVERDUE` in the spike. Three subprocess tests pass under `make test`. | confirmed |
| A9 | Sorting by `(due_at, id)` gives "oldest due first" and differs from ID order. | Plausible | Spike: `overdue` prints `#2` before `#1` in the run above. With equal due times it prints `#1`, `#3`, then `#2`. | confirmed |
| A10 | The current suite and lint pass before and after. | Verified | Baseline: `Ran 7 tests`, `OK`. Spike: `Ran 15 tests in 0.096s`, `OK`. `make lint` exits 0 in both. | confirmed |
| A11 | The new tests detect a wrong implementation. | Plausible | Five mutations each failed at least one test: sort by ID, closed counts as overdue, `>=` for `>`, `list` without the mark, `overdue` printing `OVERDUE`. | confirmed |

**The rejected shapes, each with its evidence.**

- **A flag stamped on the ticket during replay.** It needs no `TicketService.now()` and no
  clock read in the CLI. The experiment printed `flag shape: Ticket equal before/after due time: False` and
  `clock reads during one create: 3`. The same log then gives different `Ticket` objects at
  different times, which strains LOG-009. This shape is the fallback if the user rejects
  `TicketService.now()`.
- **An `OVERDUE` word inserted before the title, with the state kept.** It keeps the owner
  information in `list`. It is ambiguous: an overdue ticket titled `invoice from ACME` and a
  fresh ticket titled `OVERDUE invoice from ACME` print the identical line. The status
  column has no such collision, because states are lower case and the column is fixed.
- **An `overdue` state or an `overdue` event.** It breaks TKT-001, LOG-001, LOG-002, and
  the "moves forward only" contract (`tickets.md:8-9`).
- **"Now" passed in by the CLI.** It contradicts "never from the caller"
  (`docs/architecture.md:68-69`).

**Specs and invariants, each with the step that upholds it.**

| Spec | What it requires | How the plan meets it |
|---|---|---|
| INV-001, INV-002 | The log is the only truth and is never rewritten. | Steps 3 and 4 add read paths only. Tests compare the log bytes before and after `list` and `overdue`. |
| INV-005 | Time comes from the store clock, never from the caller. | Step 3: `now()` returns `self.store.clock()`. |
| TKT-001 | Three states. | Step 3 adds a method, not a state. `STATES` at `tickets.py:5` does not change. |
| TKT-005 | Due time is creation time plus the hours of the priority. | Step 3 compares against the existing `due_at`. `sla.py` does not change. |
| TKT-013 | `list` returns every ticket in ID order. | Step 3 leaves `list()` as it is. A test asserts ID order next to due order. |
| LOG-001 | Listing appends nothing. | Same byte comparison. Step 2 extends the wording. |
| LOG-009 | Replay is deterministic. | Step 3 leaves `_tickets()` as it is, see A4. |
| CLI-001 | Four subcommands. | **Spec change**, step 2. |
| CLI-006 | The third column of a `list` line is the state. | **Spec change**, step 2. Lines of tickets that are not overdue stay byte-identical. |
| CLI-007 | Rule errors print `error: <message>` and exit 2. | No new rule error. The open TODO is out of scope. |
| CLI-008 | Success exits 0 with an empty stderr. | Step 4. The CLI tests assert the exit code and stderr. |
| No spec yet | Overdue and the `overdue` command. | **New specs** TKT-014, TKT-015, CLI-010, step 2. |

**The sweep found no competing work and one piece of duplicate logic to avoid.**

- **In-flight work.** The repo has one commit, one branch, and no stash. A search for
  "overdue" finds nothing.
- **TODO lines.** The five TODO lines cover the CLI-007 conflict, the coverage target, and
  the roadmap. None concerns overdue.
- **Duplicate logic.** The `Clock` class exists only in `tests/test_tickets.py`, so step 5
  puts the service tests in that file and does not copy it. The line format exists once at
  `cli.py:30`, so step 4 keeps it in one helper.
- **Callers.** `svc.list()` has one caller, see A7. `Ticket` is built only at
  `tickets.py:35`.
- **Test infrastructure.** No CLI test layer exists (`docs/architecture.md:103`), so step 6
  builds it.

## Project conventions to follow

- **[`AGENTS.md:17-25`, `pyproject.toml:5`]** Convention: Python 3.11+, standard library
  only, no dependencies. **Reflected in plan:** steps 3 to 6 use `argparse`, `subprocess`,
  `tempfile`, and `unittest` only.
- **[`Makefile:2-5`, `docs/guidelines.md:12-13`]** Convention: `make lint && make test`
  before every push. **Reflected in plan:** step 8 runs both. No other runner appears.
- **[`.github/workflows/ci.yml:10-12`]** Convention: CI runs both commands on Python 3.12.
  **Reflected in plan:** the spike ran on Python 3.15.2 only. The risks cover the gap.
- **[`docs/guidelines.md:9-11`, `docs/guidelines.md:29-31`]** Convention: every module
  ships with tests, named up front with their type. **Reflected in plan:** steps 5 and 6,
  and the test plan names each case as "unit through the service" or "subprocess".
- **[`docs/guidelines.md:32-34`]** Convention: a user-visible change names its `ticketdesk`
  command sequences against a temporary log. **Reflected in plan:** the end-to-end part of
  the test plan.
- **[`docs/architecture.md:46-50`, `tests/test_tickets.py:8-24`]** Convention: tests inject
  a fake clock into the store. No mocking library is used. **Reflected in plan:** step 5
  reuses that clock. Step 6 seeds old timestamps in the log and mocks nothing.
- **[`docs/architecture.md:34-38`, `docs/guidelines.md:51-53`]** Convention: no ticket rule
  in the CLI. **Reflected in plan:** step 3 holds the rule. Step 4 only chooses the word to
  print.
- **[`docs/architecture.md:68-69`]** Convention: time comes from the store clock.
  **Reflected in plan:** step 3, `TicketService.now()`.
- **[`AGENTS.md:93`, `docs/README.md:39-40`, `docs/guidelines.md:78-80`]** Convention: no
  doc or spec change without user confirmation. **Reflected in plan:** step 1 gates steps 2
  and 7.
- **[`docs/README.md:25-28`]** Convention: spec IDs are stable and a new spec takes the
  next free number. **Reflected in plan:** step 2 uses TKT-014, TKT-015, and CLI-010.
- **[`AGENTS.md:96`, `docs/guidelines.md:82-87`]** Convention: one logical change per
  commit, with spec IDs in messages, comments, and tests. **Reflected in plan:** steps 3
  and 8.
- **[`docs/README.md:45`]** Convention: absolute dates in docs. **Reflected in plan:** step
  7 writes none, and this plan uses 2026-11-05.
- **Migrations, ports, URLs, async machinery, package manager.** These do not constrain the
  plan. The tool is one local process with a file and no dependencies
  (`docs/architecture.md:64-65`).

## Test plan

**Unit through the service, in `tests/test_tickets.py`.**

| Case | Scenario | Spec |
|---|---|---|
| `test_not_overdue_until_due_time_passes` | `is_overdue(due_at)` is false. `is_overdue(due_at + 0.001)` is true. A fresh ticket is absent from `overdue()`. | TKT-014 |
| `test_closed_ticket_is_never_overdue` | A P1 ticket is in `overdue()` after 5 hours and leaves it when closed. | TKT-014 |
| `test_assigned_ticket_can_be_overdue` | An assigned ticket past its due time is in `overdue()` with state `assigned`. | TKT-014 |
| `test_oldest_due_first_not_id_order` | P3 as ticket 1, then P1 and P2 ten hours later. `overdue()` gives 2, 3, 1. `list()` gives 1, 2, 3. | TKT-015, TKT-013 |
| `test_reads_append_nothing` | The log bytes are equal before and after `overdue()` and `list()`. | LOG-001, INV-002 |

**Subprocess through the CLI, in `tests/test_cli.py`.** The seeded log holds four tickets.
Ticket 1 is an old P3 ticket, and ticket 2 is an old assigned P1 ticket. Ticket 3 is a P1
ticket closed after its due time, and ticket 4 is a fresh P1 ticket.

| Case | Scenario | Spec |
|---|---|---|
| `test_list_marks_overdue` | `list` prints `OVERDUE` for tickets 1 and 2, `closed` for 3, `open` for 4. Exit 0, empty stderr. | CLI-006, CLI-008 |
| `test_overdue_lists_only_overdue_oldest_due_first` | `overdue` prints ticket 2 then ticket 1, each with its true state. The log bytes do not change. | CLI-010, TKT-015, LOG-001 |
| `test_overdue_with_missing_log_prints_nothing` | `overdue` on a path with no file prints nothing and exits 0. | LOG-006, CLI-010 |
| `test_overdue_breaks_ties_by_id` | Two tickets with the same due time print in ID order. | TKT-015 |

The first eight cases ran in the spike. The tie case ran as a command only, with the output
`#1`, `#3`, `#2`.

**End to end, against a temporary log.** Seed the log with the hand-written old events of
the CLI test. Then run this sequence and compare each output with the expected lines.

1. `ticketdesk --log $LOG create "fresh" --priority P1` prints `#4 open fresh`.
2. `ticketdesk --log $LOG list` prints the four lines shown in the approach summary.
3. `ticketdesk --log $LOG overdue` prints ticket 2, then ticket 1.
4. `ticketdesk --log $LOG close 2 "Swapped the access point"` prints `#2 closed`.
5. `ticketdesk --log $LOG overdue` prints ticket 1 only.
6. `TICKETDESK_LOG=$LOG ticketdesk overdue` prints the same line, which covers CLI-002.
7. `ticketdesk --log $LOG overdue extra` prints a usage error and exits 2.

**Manual.** Read `ticketdesk --help` and confirm that it lists `overdue`. No integration
layer exists in this repo, because the tool has no external service.

## Risks and mitigations

- **A script that reads the third column of `list` meets a new word.** Lines of tickets
  that are not overdue stay byte-identical. The CLI-006 change in step 2 documents the new
  value, and the user signs it off in step 1.
- **`list` hides the owner state of an overdue ticket.** `ticketdesk overdue` prints the
  true state. Open question 1 offers the alternative.
- **`overdue` on a corrupt log ends in a traceback with exit 1.** The spike confirmed it.
  This is the open CLI-007 conflict, not a new one. Fixing it for one command only would
  make the commands disagree, so the plan leaves it for the CLI-007 decision.
- **A change to the SLA table moves old tickets in or out of overdue.** Due times come from
  the table at replay (`tickets.py:36`), not from the log. This is existing behavior
  (`docs/architecture.md:40-44`), and the plan does not change it.
- **A wrong system clock gives a wrong overdue result.** A clock that jumps back hides
  overdue tickets until it recovers. No log data is affected, because overdue is never
  stored.
- **The spike ran on Python 3.15.2, and CI runs 3.12.** The change uses no syntax or
  library call newer than 3.11. CI on the pull request is the check.
- **The subprocess tests start one Python process each.** The spike suite took 0.096 s for
  15 tests, so the cost is small at this size.

## Counterfactual

**Verdict: confirmed with gaps.** Every success criterion has a plan step. The gaps are the
display assumptions in open questions 1 to 3 and the spec sign-off.

| Success criterion | Plan steps | Evidence it works |
|---|---|---|
| An open or assigned ticket past its due time shows `OVERDUE` in `ticketdesk list`. | 3, 4 | `test_list_marks_overdue` |
| `ticketdesk overdue` lists only overdue tickets. | 3, 4 | `test_overdue_lists_only_overdue_oldest_due_first`, `test_closed_ticket_is_never_overdue` |
| The `overdue` output is ordered by oldest due time first. | 3 | `test_oldest_due_first_not_id_order`, `test_overdue_breaks_ties_by_id` |
| No invariant breaks, and reads write nothing. | 3, 4 | `test_reads_append_nothing`, A4 |
| Current behavior holds for tickets that are not overdue. | 3, 4 | The 7 current tests pass in the spike. |
| Specs, tests, and docs match the code. | 1, 2, 5, 6, 7 | Step 8 |

The change does not work if any of these observations appears:

- An overdue ticket prints `open` or `assigned` in `list`.
- A closed ticket, or a ticket before its due time, appears in `overdue`.
- `overdue` prints in ID order when the due order differs.
- The log bytes change after `list` or `overdue`.
- One of the 7 current tests fails.

## Open questions

Nobody was available during this run. Each question states the assumption the plan uses.
The first three change the spec text of step 2, so they need an answer before the code work.

1. **How does `list` show an overdue ticket?** Assumption: `OVERDUE` replaces the state in
   the state column. The alternative keeps the state and adds a separate marker. That
   marker needs a position that a title cannot imitate, see the rejected shapes. A switch
   costs one line in `cli.py` and the text of CLI-006.
2. **Is a closed ticket ever overdue?** Assumption: never, even when it was closed after its
   due time. Otherwise `ticketdesk overdue` grows without limit and stops being a work list.
3. **What does a line of `ticketdesk overdue` show?** Assumption: the `list` line with the
   true state, and no due time. Showing the due time would make the order visible, but it
   needs a decision on the time format and the time zone.
4. **Is a ticket overdue at the exact due time?** Assumption: no. "Pass their due time"
   reads as strictly later, so the rule is `now > due_at`.
5. **Do you approve the spec edits of step 2 and the doc edits of step 7?** No assumption
   is possible here. The repo rules require the sign-off, and the code work waits for it.
6. **Does the CLI-007 TODO get its decision in this change?** Assumption: no. The `overdue`
   command behaves like `list` on a corrupt log until that decision.
7. **Does the new command bump the version from 0.3.0?** Assumption: no. The repo records no
   release rule, and `AGENTS.md:10` names the version.
8. **Does `ticketdesk overdue` signal overdue tickets through its exit code?** Assumption:
   no. It exits 0 like `list`, which follows CLI-008.

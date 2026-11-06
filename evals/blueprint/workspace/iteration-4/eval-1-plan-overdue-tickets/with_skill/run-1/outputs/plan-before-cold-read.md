# Plan: overdue tickets in `ticketdesk list` and a new `ticketdesk overdue`

Status: plan only. No code or doc in the repo changed. Paths are relative to the repo root
unless they start with `outputs/`, which is the run directory next to the repo.

## Headline

`ticketdesk list` shows `OVERDUE` for an unclosed ticket past its due time, and a new
`ticketdesk overdue` lists only those tickets, earliest due time first. The service derives
overdue at read time from the store clock, so the log gains no event and no fourth state.
Code work waits for your approval of the spec text in step 1, which includes `OVERDUE`
replacing the state column.

## Approach summary

The ticket service decides what is overdue, and the command line only prints the result.
`TicketService` in `ticketdesk/tickets.py` gains one read step. That step asks the store
clock for the current time and sets an `overdue` flag on each ticket. A ticket is overdue
when its state is not `closed` and the current time is later than its due time. The service
also gains an `overdue()` method that returns the flagged tickets sorted by due time, then
by ID. `ticketdesk/cli.py` gains the `overdue` subcommand and one function that formats a
line for both listings.

The store, the SLA table, the replay function, the three states, and the log format stay
untouched. The approach stands on two assumptions that a prototype confirmed. The service
can read the store clock, and the 7 existing tests pass with the change. The main trade-off
is that `OVERDUE` replaces `open` or `assigned`, so the listing no longer shows whether an
overdue ticket has an assignee.

```
ticketdesk list | ticketdesk overdue
        │
        ▼
cli.py       prints OVERDUE or the state            format only, no rule
        │  list() / overdue()
        ▼
tickets.py   _view(): now = store.clock()           the rule, TKT-014
             overdue = state != "closed" and now > due_at
        │  replay()                │  clock()
        ▼                          ▼
store.py     tickets.jsonl, read only            time.time, injectable
```

## Out of scope

- **The open TODO under CLI-007** (`docs/product-specs/cli.md:50-52`). A corrupt log makes
  `overdue` exit with a traceback, as `list` does today. This plan does not decide it.
- **Business hours.** Due time stays creation time plus calendar hours, per TKT-005.
- **An overdue event in the log, or a notification.** See "Assumptions validated", the
  falsifier.
- **New options.** No `--assignee` filter, no due-time column, no JSON output.
- **A version bump.** The repo records no release rule. See open question 7.
- **CLI tests for `create`, `assign`, and `close`.** That gap exists today
  (`docs/guidelines.md:10-11`). This plan covers only the lines it changes.

## Plan

### Step 1. Get approval for the spec text

The repo forbids a spec edit without the user's approval (`AGENTS.md:93`,
`docs/guidelines.md:78-80`). Approve or correct this text before any code work starts.
TKT-014, TKT-015, and CLI-010 are the next free IDs. The last used IDs are TKT-013 and
CLI-009.

| Spec | Today | Proposed |
|---|---|---|
| TKT-014, new | none | **Overdue tickets.** A ticket is overdue when its state is `open` or `assigned` and the current time is later than its due time. A ticket whose due time equals the current time is not overdue. A `closed` ticket is never overdue. Overdue is not a state, and no event records it. |
| TKT-015, new | none | **Overdue listing order.** The overdue listing returns only the overdue tickets, sorted by due time ascending. Tickets with the same due time are sorted by ID ascending. |
| CLI-001 | "one of four subcommands. They are `create`, `assign`, `close`, and `list`." | "one of five subcommands. They are `create`, `assign`, `close`, `list`, and `overdue`." |
| CLI-006 | "Each line is `#<id> [<priority>] <state> <title>` with the state padded to 8 characters." | "Each line is `#<id> [<priority>] <status> <title>` with the status padded to 8 characters. The status is `OVERDUE` for an overdue ticket, see TKT-014, and the state otherwise." |
| CLI-010, new | none | **overdue.** `ticketdesk overdue` prints one line per overdue ticket in the order of TKT-015. Each line has the format of CLI-006. With no overdue tickets it prints nothing. |
| LOG-001 | "Listing tickets appends nothing." | "Listing tickets and listing overdue tickets append nothing." |

### Step 2. Add the overdue rule to the service

File: `ticketdesk/tickets.py`. The prototype diff is in `outputs/scratch/prototype.diff`.

1. Add the field `overdue: bool = False` after `due_at` in `Ticket` (line 21). The only
   constructor call passes four positional arguments (line 35), so a last field with a
   default breaks nothing.
2. Leave `_tickets()` (lines 30-44) as it is. It stays a function of the log only, which
   keeps LOG-009 true by inspection.
3. Add `_view()`. It reads `self.store.clock()` once, calls `_tickets()`, and sets the flag
   on every ticket. Mark it `# implements TKT-014`.
4. Change `list()` (line 47) and `get()` (line 51) to read from `_view()`. Then `create`,
   `assign`, and `close` also return a ticket with a correct flag.
5. Add `overdue()`. It returns the flagged tickets sorted by `(due_at, id)`. Mark it
   `# implements TKT-015`.
6. Leave `create()` line 59 on `_tickets()`. It needs only the IDs.

```python
def _view(self):
    now = self.store.clock()
    tickets = self._tickets()
    for t in tickets.values():
        t.overdue = t.state != "closed" and now > t.due_at
    return tickets

def overdue(self):
    late = [t for t in self._view().values() if t.overdue]
    return sorted(late, key=lambda t: (t.due_at, t.id))
```

### Step 3. Add the command and the shared line format

File: `ticketdesk/cli.py`.

1. Add `sub.add_parser("overdue")` after line 18.
2. Replace the bare `else:` at line 28 with `elif args.cmd == "list":` and add
   `elif args.cmd == "overdue":`. Without this, `overdue` runs the `list` branch and prints
   every ticket. The prototype showed that failure.
3. Move the line format of line 30 into one function that both branches call. The function
   prints `OVERDUE` when `t.overdue` is true and `t.state` otherwise, padded to 8.
   It decides no rule. Mark it `# implements CLI-006, CLI-010`.
4. Leave the output lines of `create`, `assign`, and `close` (lines 23, 25, 27) unchanged.
   They print `t.state`, so CLI-003 to CLI-005 hold as written.

### Step 4. Add the tests

Files: `tests/test_tickets.py` and a new `tests/test_cli.py`. The cases are in "Test plan".
A working draft of all of them is in `outputs/scratch/proto/tests/test_overdue_probe.py`.

### Step 5. Update the docs with the approved text

Apply the step 1 table to `docs/product-specs/tickets.md`, `cli.md`, and `event-log.md`.
Then fix each line that the change makes stale:

| File and line | What goes stale |
|---|---|
| `AGENTS.md:82` | The `TKT` summary does not mention overdue. |
| `AGENTS.md:102` | "7 unittest cases". The plan ends with 15. |
| `AGENTS.md:106` | The run examples lack an `overdue` line. |
| `AGENTS.md:114`, `AGENTS.md:116` | "Done: create, assign, close, list" and "Not covered by tests: the CLI". |
| `docs/architecture.md:12` | The diagram label "create / assign / close / list". |
| `docs/architecture.md:18` | The seam "append(event) / replay()". The service now also calls `clock()`. |
| `docs/architecture.md:95-96`, `:103` | The test layout lacks `test_cli.py`, and "The CLI is not covered by tests today". |
| `docs/guidelines.md:11` | "The CLI has no tests today". The TODO about a coverage target stays. |
| `docs/product-specs/README.md:80`, `:82` | The index lines for `tickets.md` and `cli.md`. |

### Step 6. Check and commit

1. Run `make lint && make test` (`AGENTS.md:88`). Expect 15 tests and exit code 0.
2. Run the manual sequence in "Test plan".
3. Commit the code, the tests, and the docs as one logical change
   (`docs/guidelines.md:84-87`). Name TKT-014, TKT-015, and CLI-010 in the message.

## Assumptions validated

The experiments ran on a copy of the repo in `outputs/scratch/proto` with Python 3.15.2.
The probe suite also ran on Python 3.12.16, the CI version. The fixture repo stayed clean.

The falsifier did not hold. A clock-derived flag is the wrong shape if a spec, an
invariant, or a test requires the service output to depend on the log alone. Overdue would
then need an event in the log. Three observations say no such requirement exists.

- LOG-009 names what replay must reproduce: "the same states, assignees, resolutions, and
  due times" (`docs/product-specs/event-log.md:58-59`). The plan changes none of them, and
  `_tickets()` stays unchanged.
- The 7 existing tests pass on the prototype: `Ran 7 tests in 0.007s`, `OK`.
- The event shape has no writer. Each invocation "runs one command against one log file and
  exits" (`docs/product-specs/cli.md:3-4`), so no process exists at the due moment.
  LOG-001 forbids an append during a listing (`docs/product-specs/event-log.md:14-15`).

| # | Assumption | Class | Evidence | Result |
|---|---|---|---|---|
| 1 | The service can get the current time without the caller passing it. | Risky | `ticketdesk/store.py:14-16` stores the injected clock as the public attribute `clock`. The prototype calls `self.store.clock()`. | confirmed |
| 2 | A clock read on the read paths breaks no existing test. The test clock adds one second per call (`tests/test_tickets.py:12-14`). | Risky | Existing suite on the prototype: `Ran 7 tests in 0.007s`, `OK`. | confirmed |
| 3 | The service tests can place the clock exactly at the due time. | Plausible | With the existing `Clock`, a probe printed `at due exactly: False clock now True` and `one second later: True`. A fixed clock `clock=lambda: now` over a hand-written log also works. | confirmed |
| 4 | `OVERDUE` fits the 8-character column of CLI-006. | Plausible | `f"{'OVERDUE':<8}"` gives `'OVERDUE '`. | confirmed |
| 5 | Due order differs from ID order, so the sort is observable. | Plausible | Four tickets with mixed priorities: `overdue()` returned IDs `[2, 3, 4, 1]` and `list()` returned `[1, 2, 3, 4]`. | confirmed |
| 6 | Adding only the parser is enough for a working command. | Plausible | With the parser alone, `overdue` printed `#2 [P3] open     future`, a ticket due in the year 2100. | refuted, so step 3.2 exists |
| 7 | Neither listing writes to the log or creates a missing file. | Verified | `ticketdesk/store.py:26-27` returns `[]` for a missing file. The probe compared the file bytes before and after. | confirmed |
| 8 | A subprocess test of the CLI runs under `make test`, and a hand-written log makes a ticket overdue under the real clock. | Plausible | The probe suite with one subprocess case: `Ran 13 tests in 0.168s`, `OK`. On Python 3.12.16: `Ran 13 tests in 0.187s`, `OK`. | confirmed |
| 9 | `ticketdesk overdue` is free today. | Verified | On `HEAD` it exits with code 2 and `invalid choice: 'overdue' (choose from 'create', 'assign', 'close', 'list')`. | confirmed |
| 10 | No other code depends on the contracts that change. | Verified | `svc.list()` has one caller, `ticketdesk/cli.py:29`. `Ticket(...)` has one call, `ticketdesk/tickets.py:35`. A search for "overdue" in the repo found nothing. | confirmed |

**Specs and invariants.** Each row names the plan step that keeps the rule, or the flagged
change.

| Spec | What it requires | Plan step |
|---|---|---|
| INV-001 | State comes from replay only. | Step 2.3 derives the flag from replay plus the clock and stores nothing. |
| INV-002, LOG-001, LOG-002 | No edit, no event for a listing, three event kinds. | Steps 2 and 3 append nothing. Assumption 7. Step 1 extends LOG-001 to name `overdue`. |
| INV-004, LOG-007 | A corrupt line stops the operation. | `overdue()` goes through the same `replay()`. See risk 4 for the exit code. |
| INV-005 | Time comes from the store clock, never from the caller. | Step 2.3 reads `self.store.clock()`. The CLI passes no time. |
| TKT-001 | Three states. | Step 2.1 adds a flag, not a state. `STATES` at `ticketdesk/tickets.py:5` stays. |
| TKT-013 | `list` is in ID order. | Step 2.4 keeps the sort key. |
| LOG-009 | Replay is deterministic. | Step 2.2 leaves `_tickets()` alone. |
| CLI-001, CLI-006 | Four subcommands. The line shows `<state>`. | **Changed.** Step 1 flags both for approval. |
| CLI-003 to CLI-005, CLI-008 | Output lines and exit code 0. | Step 3.4 leaves them. The CLI tests assert exit code 0 and an empty stderr. |

## Project conventions to follow

- **[`docs/architecture.md:36-38`, `docs/guidelines.md:52-53`]** Convention: *the CLI holds
  no ticket rule. A ticket rule in the CLI is a layer crossing.* **Reflected in plan:**
  step 2 puts the rule in the service. Step 3.3 only chooses a word to print.
- **[`docs/architecture.md:68-69`, `docs/product-specs/invariants.md:34-37`]** Convention:
  *time comes from the store clock, never from the caller.* **Reflected in plan:** step 2.3
  reads `self.store.clock()`. No `time.time()` call appears in the service or the CLI.
- **[`docs/architecture.md:18`]** Convention: *the service uses the store through
  `append(event)` and `replay()`.* **Reflected in plan:** step 2.3 adds a third use, the
  clock. This is a small widening of the seam. Step 5 records it, and open question 6 asks
  for approval.
- **[`AGENTS.md:22`, `Makefile:2-3`]** Convention: *tests are `unittest`, run by
  `make test`.* **Reflected in plan:** step 4 adds `unittest` cases under `tests/`. Step 6
  runs `make test`.
- **[`docs/architecture.md:49-50`, `tests/test_tickets.py:8-20`]** Convention: *tests
  control time by injecting a clock into `EventStore`.* **Reflected in plan:** the service
  tests inject a clock. No test patches `time.time`.
- **[`docs/guidelines.md:29-34`]** Convention: *a plan names the test files, the cases, and
  the test type. The type is unit through the service or subprocess through the CLI. A
  user-visible change also names its e2e command sequences.* **Reflected in plan:** "Test
  plan" names all of them.
- **[`AGENTS.md:23`, `Makefile:4-5`]** Convention: *lint is `make lint`, a `compileall`
  pass.* **Reflected in plan:** step 6. The repo has no formatter, so none runs.
- **[`AGENTS.md:25`, `docs/architecture.md:76`]** Convention: *no dependency beyond the
  standard library.* **Reflected in plan:** the new test uses `subprocess`, `json`, and
  `tempfile` only.
- **[`AGENTS.md:93`, `docs/README.md:39`]** Convention: *doc changes need the user's
  approval.* **Reflected in plan:** step 1 comes before every other step.
- **[`docs/README.md:27-28`]** Convention: *spec IDs are stable, and a new spec takes the
  next free number.* **Reflected in plan:** step 1 uses TKT-014, TKT-015, and CLI-010.
- **[`AGENTS.md:96`, `docs/guidelines.md:84-87`]** Convention: *name spec IDs in code
  comments, tests, and commits. One logical change per commit.* **Reflected in plan:**
  steps 2, 3, 4, and 6.
- **[`.github/workflows/ci.yml:10`, `pyproject.toml:5`]** Convention: *CI runs Python 3.12,
  and the package supports 3.11 and later.* **Reflected in plan:** the prototype passed on
  3.12.16. Python 3.11 was not available to test.
- **[`AGENTS.md:103`]** Convention: *run the tool as `python3 -m ticketdesk.cli --log
  <path>`.* **Reflected in plan:** the CLI tests and the manual sequence use this form.
- **Migrations, ports, URLs, and async machinery** do not constrain this plan. The tool is
  one local file with no network (`docs/architecture.md:64-65`), and state needs no
  migration (`docs/architecture.md:44`).

## Test plan

**Unit, through the service.** File: `tests/test_tickets.py`. The cases that need an exact
time write the log lines by hand and inject a fixed clock. `tests/test_store.py:12` is the
precedent for a hand-written log.

| Case | Spec | Scenario |
|---|---|---|
| `test_ticket_is_overdue_only_after_due_time` | TKT-014 | A P1 ticket is not overdue at its due time and is overdue one second later. Its state stays `open`. |
| `test_closed_ticket_is_never_overdue` | TKT-014 | A ticket closed after its due time is not overdue. An assigned ticket past due is overdue. |
| `test_overdue_sorted_by_due_time_then_id` | TKT-015 | A late P3, a later-created P1, and two P2 tickets with equal due times come back as `[2, 3, 4, 1]`. |
| `test_list_keeps_id_order_and_sets_the_flag` | TKT-013, TKT-014 | `list()` returns `[1, 2, 3, 4]` with the flag set on the late tickets only. |
| `test_listings_append_nothing` | LOG-001, LOG-006 | The log bytes are equal before and after `list()` and `overdue()`. A missing file stays missing. |

**Integration.** No separate layer exists between the service and the CLI, so the plan adds
no integration suite.

**End to end, subprocess through the CLI.** File: `tests/test_cli.py`, new. Each case runs
`sys.executable -m ticketdesk.cli --log <temp log>` with the repo root as the working
directory. A hand-written `created` event with `at` of `1000.0` is overdue under the real
clock. A ticket made by `create` inside the test is not due for 72 hours.

| Case | Spec | Scenario |
|---|---|---|
| `test_list_shows_overdue_status` | CLI-006 | `list` prints `OVERDUE` for the two old tickets, `closed` for a closed one, and `open` for a new one. |
| `test_overdue_lists_only_overdue_by_due_time` | CLI-001, CLI-010, CLI-008 | `overdue` prints the old P1 before the old P3 and nothing else. Exit code 0, empty stderr, log bytes unchanged. |
| `test_overdue_with_missing_log_prints_nothing` | CLI-010, LOG-006 | `overdue` on a missing log prints nothing, exits with code 0, and creates no file. |

**Manual.** Run this sequence against a temporary log. The output below is copied from the
prototype run.

```bash
LOG=$(mktemp -d)/t.jsonl
printf '%s\n' \
  '{"at": 1000.0, "id": 1, "kind": "created", "priority": "P3", "title": "old p3"}' \
  '{"at": 2000.0, "id": 2, "kind": "created", "priority": "P1", "title": "old p1"}' > "$LOG"
python3 -m ticketdesk.cli --log "$LOG" create "fresh one"
python3 -m ticketdesk.cli --log "$LOG" list
python3 -m ticketdesk.cli --log "$LOG" overdue
python3 -m ticketdesk.cli --log "$LOG" close 2 "Replaced the toner cartridge"
python3 -m ticketdesk.cli --log "$LOG" overdue
```

```text
#3 open fresh one
#1 [P3] OVERDUE  old p3
#2 [P1] OVERDUE  old p1
#3 [P3] open     fresh one
#2 [P1] OVERDUE  old p1
#1 [P3] OVERDUE  old p3
#2 closed
#1 [P3] OVERDUE  old p3
```

## Risks and mitigations

1. **The listing hides the assignee state of an overdue ticket.** In the prototype,
   `assign 1 dana` printed `#1 assigned -> dana`, and `list` still printed
   `#1 [P3] OVERDUE  old p3`. Mitigation: open question 1 offers a separate marker. The
   format lives in one function, so the switch is a change of one line.
2. **A script that reads `list` for `open` or `assigned` may miss overdue tickets.** The
   repo holds no such script. Users outside the repo are unknown. Mitigation: name the
   change in the commit message, and decide open question 1 first.
3. **A wrong system clock gives a wrong overdue status, with no error.** The same clock
   stamps the events, so the error cancels on one machine. It does not cancel for a log
   copied from another machine. Mitigation: none planned. The plan accepts the risk.
4. **A corrupt log makes `overdue` exit with a traceback and code 1.** The prototype showed
   `ValueError: ../corrupt.jsonl:2: corrupt event: Expecting value: line 1 column 1 (char 0)`
   for `overdue`. `list` does the same on
   `HEAD`. Mitigation: the decision under CLI-007 covers both commands through the same
   `try` block.
5. **`list` output now changes with time, with no change to the log.** A user who compares
   two runs may see a ticket turn to `OVERDUE` between them. Mitigation: CLI-006 and
   TKT-014 state it.
6. **Python 3.11 is untested.** The package claims support for it (`pyproject.toml:5`).
   The prototype ran on 3.12.16 and 3.15.2 only. Mitigation: CI covers 3.12, and 3.11 has
   no CI job today.

## Counterfactual

Verdict: **Confirmed.** Every success criterion has a plan step. Criteria 1 and 5 depend on
the answers to open questions 1 and 6.

| # | Success criterion | Plan step |
|---|---|---|
| 1 | `list` shows `OVERDUE` for a ticket past its due time. | Steps 2.3, 2.4, and 3.3. Test: `test_list_shows_overdue_status`. |
| 2 | `overdue` lists only overdue tickets. | Steps 2.5, 3.1, and 3.2. Test: `test_overdue_lists_only_overdue_by_due_time`. |
| 3 | `overdue` puts the earliest due time first. | Step 2.5. Test: `test_overdue_sorted_by_due_time_then_id`. |
| 4 | No invariant breaks, no listing writes, and the 7 existing tests pass. | Steps 2.2 and 6.1. Test: `test_listings_append_nothing`. |
| 5 | The specs and the docs describe the new behavior. | Steps 1 and 5. |

The change fails if any of these appears. A closed ticket shows `OVERDUE`. A ticket not yet
due shows `OVERDUE`. `overdue` prints in ID order when the due order differs. A listing
changes the bytes of the log.

## Open questions

Nobody was available during this run. Each question states the assumption the plan
proceeds on.

1. **Does `OVERDUE` replace the state in the line, or stand beside it?** Assumption: it
   replaces the state, which is the literal reading of "show as OVERDUE". The cost is
   risk 1. The alternative is a line such as `#1 [P3] assigned OVERDUE old p3`.
2. **Is a ticket that was closed late overdue?** Assumption: no. A closed ticket is never
   overdue.
3. **Is a ticket overdue at the exact second of its due time?** Assumption: no. "Pass"
   means the current time is later than the due time.
4. **Does "oldest due first" mean the earliest due time or the earliest creation time?**
   Assumption: the earliest due time. A P1 created later can come before an older P3.
   Tickets with equal due times sort by ID.
5. **What does `overdue` print and return when nothing is overdue?** Assumption: it prints
   nothing and exits with code 0, as `list` does. The line format equals the `list` format.
6. **Do you approve the spec text in step 1 and the doc edits in step 5?** Assumption:
   yes, as written. This includes the service reading the store clock, which widens the
   seam at `docs/architecture.md:18`. No code work starts before this answer.
7. **Does this feature bump the version from 0.3.0?** Assumption: no. The repo records no
   release rule, and `AGENTS.md:10` names the version.

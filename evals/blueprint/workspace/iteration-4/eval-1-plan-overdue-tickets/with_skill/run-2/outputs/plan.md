# Plan: OVERDUE in `ticketdesk list` and a `ticketdesk overdue` command

Paths are relative to the root of the ticketdesk repo unless they start with `scratch/`.
The `scratch/` paths sit next to this plan and hold the experiments. Nothing in the repo
changed while this plan was written.

## Headline

`ticketdesk list` prints `OVERDUE` in the state column for a ticket that is past its due
time and not closed. A new `ticketdesk overdue` command prints only those tickets, earliest
due time first, and the log format and the three ticket states stay unchanged. The repo
rules require your approval of the proposed spec changes before the code work starts.

## Approach summary

Overdue is a fact that the service derives when it reads tickets, and no event records it.
A new rule in `ticketdesk/tickets.py` says that a ticket is overdue when it is not closed
and the current time is later than its due time. The service reads the current time once
per call from the injectable clock of the store and flags every ticket it returns. A new
service method returns the overdue tickets sorted by due time and then by ID.
`ticketdesk/cli.py` gains the `overdue` subcommand, and `list` prints `OVERDUE` in the
state column when the flag is set.

The store, the SLA table, the event kinds, the log format, and the replay code stay
untouched. The approach stands on two assumptions, and a prototype in a scratch copy
confirmed both. The service can reach the clock without
a change to the store, and a clock read writes nothing to the log. The main trade-off is
that `list` hides whether an overdue ticket is `open` or `assigned`, because `OVERDUE`
takes that column. `ticketdesk overdue` prints the stored state, so that fact stays one
command away.

## Out of scope

- The open TODO under CLI-007 (`docs/product-specs/cli.md:50-52`). A corrupt log still
  ends `overdue` with a traceback and exit code 1, the same as `list` today.
- A marker for a ticket that was closed after its due time.
- `OVERDUE` in the output lines of `create`, `assign`, and `close`. The request names
  `list` only.
- The due time, the delay, or the assignee in any output line.
- An event, a notification, or any log write when a ticket becomes overdue.
- A `--now` option or any other way to set the clock from the command line.
- Business hours or per-customer targets (`docs/architecture.md:123-124`).
- Tests for the `create`, `assign`, and `close` commands. That gap exists today
  (`docs/guidelines.md:10-11`) and stays.
- A `.gitignore` and a version bump. See the open questions.

## Plan

### Step 1. Get approval for the spec text

The repo forbids a silent spec change (`AGENTS.md:93`, `docs/guidelines.md:78-80`). The
user approves the text below before step 2 starts. The edits land in the same commit as
the code.

New specs in `docs/product-specs/tickets.md`, after TKT-013. The next free numbers are 014
and 015.

```markdown
### TKT-014: Overdue tickets

A ticket is overdue when its state is `open` or `assigned` and the current time is later
than its due time. A ticket is not overdue at the exact second of its due time. A `closed`
ticket is never overdue. Overdue is not a state. The state of an overdue ticket is still
`open` or `assigned`, and no event records that a ticket became overdue.

### TKT-015: Overdue listing order

Listing overdue tickets returns every overdue ticket and no other ticket, sorted by due
time ascending. Tickets with the same due time are sorted by ID ascending.
```

Changed and new specs in `docs/product-specs/cli.md`. CLI-001 and CLI-006 keep their IDs.
CLI-010 is the next free number.

```markdown
### CLI-001: Commands

The `ticketdesk` command takes one of five subcommands. They are `create`, `assign`,
`close`, `list`, and `overdue`. Invoking `ticketdesk` with no subcommand, or with an
unknown one, prints usage to stderr and exits with code 2.

### CLI-006: list

`ticketdesk list` prints one line per ticket in ID order, see TKT-013. Each line is
`#<id> [<priority>] <state> <title>` with the state padded to 8 characters. For an overdue
ticket, see TKT-014, the line shows `OVERDUE` in place of the state. With no tickets it
prints nothing.

### CLI-010: overdue

`ticketdesk overdue` prints one line per overdue ticket in the order of TKT-015. Each line
is `#<id> [<priority>] <state> <title>` with the state padded to 8 characters. The state
is the stored state, `open` or `assigned`. With no overdue tickets it prints nothing. It
appends no event, and it exits with code 0 in both cases.
```

### Step 2. Add the rule and the overdue listing to the service

File: `ticketdesk/tickets.py`. The prototype of steps 2 and 3 is in
`scratch/prototype.diff`.

1. Add the field `overdue: bool = False` to `Ticket`, after `due_at` on line 21. The one
   constructor call on line 35 passes four positional arguments, so it keeps working.
2. Add a module function `is_overdue(ticket, now)` with the comment `# implements TKT-014`.
   It returns `ticket.state != "closed" and now > ticket.due_at`.
3. Add `TicketService._current()`. It calls `self.store.clock()` once, calls
   `self._tickets()`, sets `overdue` on each ticket with `is_overdue`, and returns the dict.
4. Change `list()` on line 47 and `get()` on line 51 to read from `_current()`. No command
   prints the flag from `get()` today. The change keeps the flag true on every ticket the
   service returns. `Ticket` and `TicketService` are public names
   (`ticketdesk/__init__.py:5`), and other front ends are meant to call the same service
   (`docs/architecture.md:121-122`). The cost is one clock read per `get()`.
5. Add `TicketService.overdue()` with the comment `# implements TKT-015`. It returns the
   tickets from `_current()` whose flag is set, sorted by `(t.due_at, t.id)`.
6. Leave `_tickets()` on lines 30 to 44 as it is. Replay must not read the clock, see
   LOG-009. Leave line 59 on `_tickets()` too, because the next ID needs no clock.
7. Do not add `is_overdue` to `ticketdesk/__init__.py`. Callers reach the rule through
   `Ticket.overdue` and `TicketService.overdue()`. The list of public names in
   `docs/architecture.md:89` then stays correct.

### Step 3. Add the subcommand and the label to the CLI

File: `ticketdesk/cli.py`.

1. Add `sub.add_parser("overdue")` after line 18. The subcommand takes no arguments.
2. Add a small function that builds the list line from a ticket and a state label. Both
   commands use it, so the format on line 30 exists once.
3. Add `elif args.cmd == "overdue":` before the `else` on line 28. It prints one line per
   ticket from `svc.overdue()` with `t.state` as the label. Comment: `# implements CLI-010`.
4. In the `list` branch, pass `"OVERDUE"` as the label when `t.overdue` is true, else
   `t.state`. Comment: `# implements CLI-006`. The CLI reads the flag and holds no rule.

The explicit branch in item 3 matters. Without it the `else` on line 28 runs `list` for
the new subcommand. The sweep section shows that run.

### Step 4. Add unit tests through the service

File: `tests/test_tickets.py`, new class `OverdueTests`. The class builds the store with a
clock that returns a settable `now` and does not tick. The existing `Clock` on lines 8 to
14 adds one second per read, which makes an exact due-time test hard to read. The prototype
of the class is in `scratch/proto/tests/test_tickets.py`.

| Case | Covers |
|---|---|
| `test_ticket_is_not_overdue_at_its_due_time` | TKT-014, `now == due_at` |
| `test_ticket_is_overdue_one_second_later_and_stays_open` | TKT-014, TKT-001 |
| `test_assigned_ticket_can_be_overdue` | TKT-014 |
| `test_closed_ticket_is_never_overdue` | TKT-014, close after the due time |
| `test_overdue_orders_by_due_time_then_id` | TKT-015, two tickets share a due time |
| `test_overdue_leaves_out_tickets_not_yet_due` | TKT-015 |
| `test_list_keeps_every_ticket_in_id_order` | TKT-013 with overdue tickets present |
| `test_reading_overdue_appends_nothing` | LOG-001, LOG-009, log bytes and replay equal |
| `test_get_carries_the_overdue_flag` | TKT-014 through `get()` |

### Step 5. Add subprocess tests through the CLI

File: `tests/test_cli.py`, new. Each case runs
`[sys.executable, "-m", "ticketdesk.cli", "--log", <temp log>, ...]` with the repo root as
the working directory. A case that needs overdue tickets writes the log by hand with `at`
values near 1000, which puts every due time in 1970. `tests/test_store.py:12` already
writes a log by hand. The prototype of this file is `scratch/proto/tests/test_cli.py`.

| Case | Covers |
|---|---|
| `test_list_shows_overdue_in_state_column` | CLI-006, exact stdout, closed ticket unmarked |
| `test_overdue_lists_only_overdue_oldest_due_first` | CLI-010, TKT-015, exact stdout |
| `test_fresh_ticket_is_not_overdue` | CLI-006, CLI-010, CLI-008, title starts with `OVERDUE` |
| `test_overdue_on_missing_log_prints_nothing_and_creates_no_file` | LOG-006 |
| `test_list_and_overdue_append_nothing` | LOG-001, file bytes equal |
| `test_closing_removes_ticket_from_overdue` | TKT-014, CLI-010 |

### Step 6. Update the docs that describe the code

These edits need the same approval as step 1 (`docs/README.md:39-40`).

- `docs/architecture.md:12`. Add `overdue` to the calls in the diagram.
- `docs/architecture.md:18`. Add the clock read to the calls from the service to the store.
- `docs/architecture.md:48-50`. Say that the service also reads the clock of the store for
  the overdue rule.
- `docs/architecture.md:68-69`. Say that the current time for the overdue rule also comes
  from the clock of the store.
- `AGENTS.md:47`. Name the CLI in the description of `tests/`.
- `docs/architecture.md:94-96` and `:103`. Add `test_cli.py`, and say that the CLI tests
  cover `list` and `overdue` only.
- `docs/guidelines.md:10-11`. Change "The CLI has no tests today" to name the same limit.
- `AGENTS.md:82` and `docs/product-specs/README.md:80`. Add "overdue" to the summary of
  `tickets.md`.
- `AGENTS.md:102`. Replace "7 unittest cases" with the count that `make test` prints.
- `AGENTS.md:106`. Add an `overdue` line to the example commands.
- `AGENTS.md:114-116`. Add `overdue` to "Done" and narrow "Not covered by tests".

### Step 7. Verify and commit

1. Run `make lint && make test` (`Makefile:2-5`). Both must pass.
2. Run the manual sequence in the test plan and compare the output with the expected lines.
3. Make one commit that names TKT-014, TKT-015, CLI-006, and CLI-010. Stage files by name.
   The repo has no `.gitignore`, and `make lint` leaves untracked `__pycache__` directories.

## Assumptions validated

Every experiment ran in a scratch copy of the repo on Python 3.15.2. The suite also ran on
Python 3.12, the CI version (`.github/workflows/ci.yml:10`).

| # | Assumption | Was | Evidence | Result |
|---|---|---|---|---|
| A1 | The service can reach a current time without a store change. | Plausible | `ticketdesk/store.py:14-16` keeps the clock as the public attribute `clock`. The prototype calls `self.store.clock()`. | confirmed |
| A2 | A clock read at list time appends nothing and leaves replay unchanged. | Risky | `scratch/exp_service2.py` printed `log bytes unchanged: True \| replay identical: True`. | confirmed |
| A3 | `OVERDUE` fits the 8-character state column, so the line shape holds. | Plausible | The prototype printed `#1 [P3] OVERDUE  slow burner`. The word has 7 characters. | confirmed |
| A4 | An overdue ticket exists end to end without a wait and without a clock option. | Risky | A hand-written log with `"at": 1000` made `list` print `OVERDUE` through the real CLI. | confirmed |
| A5 | The extra clock read per service call breaks no existing test. | Plausible | The 7 existing tests pass on the prototype with Python 3.15.2 and 3.12. | confirmed |
| A6 | A subprocess test finds the package when it runs from the repo root. | Plausible | A run from `/` with `cwd` set to the copy returned `'#1 [P3] OVERDUE  ancient\n' '' 0`. | confirmed |
| A7 | Every replayed ticket has a due time to sort by. | Verified | `ticketdesk/tickets.py:36` sets `due_at` for every `created` event. | confirmed |
| A8 | `overdue` is free as a subcommand name. | Verified | Today it prints `invalid choice: 'overdue'` and exits with code 2. | confirmed |

### The falsifier

The shape is wrong if a read of overdue changes the log, or changes what replay returns.
In that case overdue would need an event or a stored state, not a derivation at read
time. `scratch/exp_service2.py` moved a settable clock across three due times and read
`list()` and `overdue()` at each point. The flag changed and the log bytes and the replay
result did not. The falsifier did not fire.

```text
due times          [(1, 260200.0), (2, 88400.0), (3, 260200.0)]
now == due of #2   [(1, 'open', False), (2, 'assigned', False), (3, 'open', False)] []
1 s after due #2   [(1, 'open', False), (2, 'assigned', True), (3, 'open', False)] [2]
after every due    [(1, 'open', True), (2, 'assigned', True), (3, 'open', True)] [2, 1, 3]
log bytes unchanged: True | replay identical: True
after closing #2   [(1, 'open', True), (2, 'closed', False), (3, 'open', True)] [1, 3]
get(1).overdue     True
```

Each row shows the `(id, state, overdue)` triples from `list()` and then the IDs from
`overdue()`. Tickets 1 and 3 share a due time, and the ID breaks the tie.

### Shapes that the specs rule out

- **An `overdue` event in the log.** LOG-001 says that listing appends nothing, and
  LOG-002 fixes the event kinds. Nothing would write the event while no command runs.
- **`overdue` as a fourth state set during replay.** TKT-001 fixes three states. LOG-009
  says the same log always replays to the same states, and a clock read breaks that.
- **A time check in the CLI with `time.time()`.** A ticket rule in the CLI is a layer
  crossing (`docs/guidelines.md:52-53`). The time must come from the clock of the store
  (`docs/architecture.md:68-69`).

### Specs and invariants checked

| Spec | What it requires | How the plan meets it | Step |
|---|---|---|---|
| INV-001 | The log is the only source of ticket state. | Overdue comes from the replayed due time and the clock. Nothing is stored. | 2 |
| INV-002, LOG-001, LOG-002 | No edits. Listing appends nothing. Three event kinds. | `list` and `overdue` only read. Tests compare the file bytes. | 2, 4, 5 |
| INV-004, LOG-007 | A corrupt line stops every operation. | `overdue` uses the same replay. The traceback under CLI-007 stays, see out of scope. | 2 |
| INV-005 | Event time comes from the clock of the store. | No event is added. The overdue rule reads the same clock. | 2 |
| LOG-006 | A missing log means no tickets. | `overdue` prints nothing and creates no file. A test covers it. | 5 |
| LOG-009 | Replay is deterministic. | `_tickets()` does not change and never reads the clock. | 2 |
| TKT-001 | Three states. | `Ticket.state` never holds `OVERDUE`. TKT-014 says so. | 1, 2 |
| TKT-005 | Due time is creation time plus the hours. | The rule reuses `Ticket.due_at`. | 2 |
| TKT-013 | `list` returns every ticket in ID order. | The sort key of `list()` does not change. | 2, 4 |
| CLI-001 | Four subcommands. | **Spec change.** Five subcommands. | 1, 3 |
| CLI-006 | The list line shows the state. | **Spec change.** `OVERDUE` takes the place of the state. | 1, 3 |
| CLI-008 | Success exits with code 0 and no stderr. | `overdue` exits with code 0 with or without results. | 3, 5 |
| none | No spec covers overdue. | **New specs** TKT-014, TKT-015, CLI-010. | 1 |

### Codebase sweep

- **In-flight work.** None found. `git log --oneline --all` shows the one commit `7c62f26`,
  the only branch is `main`, and the stash is empty. A grep for "overdue" finds no line.
- **Duplicate logic.** Replay already computes the due time (`ticketdesk/tickets.py:36`),
  so the rule reads `due_at` and does not compute it again. Step 3 keeps one line format.
- **Callers of `list()` and `get()`.** `list()` has one caller, `ticketdesk/cli.py:29`,
  and no test. `get()` has five callers, all inside `ticketdesk/tickets.py`.
- **The `else` branch.** `ticketdesk/cli.py:28` handles every command without a branch of
  its own. A copy with only the new subparser printed the full list for `overdue`.
- **Test infrastructure.** Service tests with an injected clock exist. CLI tests do not
  (`AGENTS.md:116`), so step 5 builds the first ones.
- **No `.gitignore`.** `make lint` and `make test` leave `__pycache__` untracked.

## Project conventions to follow

- **[`AGENTS.md:88`, `Makefile:2-5`]** Convention: *`make lint && make test` before every
  push.* **Reflected in plan:** step 7 runs both. No other runner appears in the plan.
- **[`AGENTS.md:22`, `docs/architecture.md:80`]** Convention: *tests use `unittest` under
  `tests/`.* **Reflected in plan:** steps 4 and 5 add `unittest` cases that discovery finds.
- **[`docs/architecture.md:49-50`, `tests/test_tickets.py:20`]** Convention: *tests inject
  the clock into the store, with no mock library.* **Reflected in plan:** step 4 injects a
  settable clock. Step 5 uses old timestamps in the log, so it needs no clock at all.
- **[`docs/guidelines.md:29-34`]** Convention: *name the test files, the cases, the test
  type, and the e2e command sequences up front.* **Reflected in plan:** steps 4 and 5 and
  the test plan name them.
- **[`AGENTS.md:25`, `docs/architecture.md:76`]** Convention: *no dependencies beyond the
  standard library.* **Reflected in plan:** steps 2 to 5 import only `subprocess`, `sys`,
  `json`, `tempfile`, `unittest`, and `pathlib`.
- **[`pyproject.toml:5`, `.github/workflows/ci.yml:10`]** Convention: *Python 3.11 or
  later, CI on 3.12.* **Reflected in plan:** the prototype of steps 2 to 5 passes on 3.12.
- **[`docs/architecture.md:36-38`, `docs/guidelines.md:52-53`]** Convention: *the CLI
  holds no ticket rule.* **Reflected in plan:** step 2 puts the rule in the service. Step 3
  only picks a label.
- **[`docs/architecture.md:68-69`]** Convention: *time comes from the clock of the store,
  never from the caller.* **Reflected in plan:** step 2 reads `self.store.clock()`.
- **[`AGENTS.md:93`, `docs/README.md:39-40`]** Convention: *doc changes need user
  confirmation.* **Reflected in plan:** step 1 gates the code work, and step 6 lists the
  doc edits that the sweep found.
- **[`docs/README.md:25-28`]** Convention: *spec IDs are stable, and a new spec takes the
  next free number.* **Reflected in plan:** step 1 adds TKT-014, TKT-015, and CLI-010 and
  renumbers nothing.
- **[`AGENTS.md:96`, `docs/guidelines.md:82-87`]** Convention: *one logical change per
  commit, with spec IDs in comments, tests, and the message.* **Reflected in plan:** steps
  2, 3, and 7.
- **Migrations, ports, URLs, async work, package manager.** These do not constrain the
  plan. The log format does not change, and the tool is one local process with no
  dependencies.
- **Lint and format.** `make lint` is a syntax pass only (`docs/architecture.md:81`). No
  style rule constrains the plan.

## Test plan

**Unit, through the service.** The nine cases in step 4 cover the rule, the order, and the
log. They set the clock, so they do not depend on the time of the run.

**Integration.** No separate layer exists between the service and the CLI. The subprocess
tests cover the wiring.

**End to end, by subprocess.** The six cases in step 5 run the real command against a
temporary log.

**Prototype run.** The seven existing tests, the nine unit cases, and the six subprocess
cases pass together on both Python versions. This is the output on Python 3.12.

```text
Ran 22 tests in 0.319s

OK
```

**Manual.** Run this sequence from the repo root after step 3. The first file is the log
that the experiments used.

```bash
L=$(mktemp -d)/t.jsonl
cat > "$L" <<'EOF'
{"at": 1000, "id": 1, "kind": "created", "priority": "P3", "title": "slow burner"}
{"at": 2000, "id": 2, "kind": "created", "priority": "P1", "title": "printer on fire"}
{"at": 3000, "id": 3, "kind": "created", "priority": "P2", "title": "late but done"}
{"assignee": "dana", "at": 4000, "id": 2, "kind": "assigned"}
{"at": 999999, "id": 3, "kind": "closed", "resolution": "Replaced the toner cartridge"}
EOF
python3 -m ticketdesk.cli --log "$L" list
python3 -m ticketdesk.cli --log "$L" overdue
python3 -m ticketdesk.cli --log "$L" create "brand new" --priority P1
python3 -m ticketdesk.cli --log "$L" list
python3 -m ticketdesk.cli --log "$L" close 2 "Put the fire out for good"
python3 -m ticketdesk.cli --log "$L" overdue
```

The prototype printed these lines for the six commands, in order.

```text
#1 [P3] OVERDUE  slow burner
#2 [P1] OVERDUE  printer on fire
#3 [P2] closed   late but done
#2 [P1] assigned printer on fire
#1 [P3] open     slow burner
#4 open brand new
#1 [P3] OVERDUE  slow burner
#2 [P1] OVERDUE  printer on fire
#3 [P2] closed   late but done
#4 [P1] open     brand new
#2 closed
#1 [P3] open     slow burner
```

Ticket 2 is due before ticket 1, so it comes first in `overdue`. Ticket 3 is past its due
time and closed, so neither command marks it.

## Risks and mitigations

- **Scripts that read the state column of `list` see a new value.** They also lose `open`
  and `assigned` for overdue tickets. The spec change in step 1 makes this visible, and
  `ticketdesk overdue` prints the stored state.
- **A wrong system clock gives wrong flags, and nobody sees an error.** A clock set back
  hides overdue tickets. The plan does not mitigate this. The same clock stamps the
  events, so one machine stays consistent with itself.
- **The `overdue` flag is a snapshot of one call.** A caller that keeps a `Ticket` object
  holds a stale flag later. The CLI runs one command per process, so it cannot.
- **A later test with a ticking clock sees one more tick per `get()`.** The seven existing
  tests pass. A new test that counts ticks must count the read in `_current()`.
- **`overdue` on a corrupt log prints a traceback.** This is the open conflict under
  CLI-007, and `list` does the same today. The plan leaves it.
- **Rollback is a revert of one commit.** The change adds no event kind and no field to
  the log, so the previous version reads every log that the new version writes.

## Counterfactual

Verdict: **Confirmed with gaps.** Every success criterion has a plan step. The gaps are
the product decisions in the open questions, and each has a stated assumption.

| Success criterion | Plan steps |
|---|---|
| `list` shows `OVERDUE` for a ticket that is past its due time and not closed. | 2, 3, tests in 4 and 5 |
| `list` still prints every ticket in ID order, and other lines do not change. | 2, 3, tests in 4 and 5 |
| `ticketdesk overdue` prints the overdue tickets and no other ticket. | 2, 3, tests in 4 and 5 |
| `overdue` prints the earliest due time first, and the ID breaks a tie. | 2, test in 4 |
| No invariant breaks, and no command writes to the log on a read. | 2, tests in 4 and 5 |
| Every spec change is approved before the code work starts. | 1, 6 |
| `make lint && make test` pass, and new tests cover the new logic. | 4, 5, 7 |

The change does not work if one of these observations appears.

- A ticket that is past its due time and not closed prints `open` or `assigned` in `list`.
- `overdue` prints a closed ticket, prints a ticket before its due time, or misses one.
- The log file changes after `list` or `overdue`.
- One of the seven existing tests fails.

## Open questions

Nobody was available during planning. Each question carries the assumption the plan
proceeds on, and a different answer changes the named steps.

1. **Do you approve the spec text in step 1 and the doc edits in step 6?** The plan
   assumes yes. The repo rules make this approval the gate for the code work.
2. **Is a closed ticket ever overdue?** The plan assumes no, even when it was closed after
   its due time. A yes changes TKT-014 and the rule in step 2.
3. **Does `OVERDUE` replace the state in `list`, or sit beside it?** The plan assumes it
   replaces the state. The line shape holds, and the word cannot be confused with a title.
   A separate marker keeps `open` and `assigned` visible and changes the line shape.
4. **Does `ticketdesk overdue` print the stored state or the word `OVERDUE`?** The plan
   assumes the stored state. Every line of that command is overdue, so the word adds
   nothing there.
5. **Is a ticket overdue at the exact second of its due time?** The plan assumes no. The
   request says "pass their due time", so the rule is `now > due_at`.
6. **Does `overdue` signal results through its exit code?** The plan assumes no. It exits
   with code 0 with or without results, as CLI-008 says for every successful command.
7. **Should this change also close the TODO under CLI-007?** The plan assumes no. The new
   command then shows a traceback on a corrupt log, the same as `list`.
8. **Does the change bump the version or add a `.gitignore`?** The plan assumes no. The
   repo records no release process, and `pyproject.toml:3` stays at `0.3.0`.
9. **Does the commit go on a branch with a pull request, or on `main`?** The plan assumes a
   branch off `main` and no push until you say so. The repo names pushes and pull requests
   (`AGENTS.md:88`, `AGENTS.md:96`) and records no branch rule.

## Cold-read note

One fresh reader checked this plan against the repo and reported five findings, all Minor.
Four are fixed in the text, none is rejected, and one became open question 9. The fixes
add the missing prototype of the unit tests, three doc edits, the reason `get()` reads the
clock, and the decision to keep `is_overdue` unexported. The approach did not change.

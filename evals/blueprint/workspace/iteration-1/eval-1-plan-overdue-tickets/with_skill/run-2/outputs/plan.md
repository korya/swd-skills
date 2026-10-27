# Plan: overdue tickets in `ticketdesk list` and a new `ticketdesk overdue` command

Date: 2026-10-27. Repo: `ticketdesk` 0.3.0 at commit `f87e57b`. Status: plan only, no code
or docs changed. A prototype of the change ran on a scratch copy and is cited below.

## Headline

Overdue is computed at read time from the due time and the store's clock, never stored.
`ticketdesk list` prints `OVERDUE` in the state column for an open or assigned ticket
whose due time has passed. A new `ticketdesk overdue` command prints only those tickets,
earliest due first. Eight spec and doc edits need your confirmation before code work
starts. They are listed under open questions, with the assumption I proceed on for each.

## Approach summary

The change touches the service, the CLI, the tests, and the specs. The store, the SLA
table, the event kinds, and the log format stay as they are. `Ticket` gains an
`is_overdue(now)` rule, and `TicketService` gains `overdue(now)` and `now()`. The `now()`
method reads the store's injectable clock, so a fake clock in tests controls both event
times and overdue checks. The CLI asks the service for the current time once per command,
then only formats lines. No ticket rule moves into the CLI.

The approach stands on two assumptions that the prototype confirmed. Every ticket already
carries `due_at` in epoch seconds after replay, and the store's clock is a public callable
with no side effect on the log. The main trade-off is that `OVERDUE` replaces the state
word on a `list` line, so that line no longer says open or assigned. I chose that over an
extra marker column because it keeps the CLI-006 line shape for every other line. Every
existing consumer of the output keeps working. I rejected storing overdue as an event or a state
because replay must yield the same states at any time of day, see LOG-009.

## Out of scope

- Recording that a ticket became overdue in the log. Overdue is a view, not an event.
- Showing how late a ticket is, or an SLA breach report for tickets closed after their
  due time.
- Notifications, reminders, or any background job.
- Business hours or per-customer SLA targets, see the "Richer SLA" migration path in
  `docs/architecture.md:123`.
- The CLI-007 TODO. A corrupt log still escapes as a traceback from `overdue`, exactly as
  it does from `list` today.
- A version bump in `pyproject.toml`. No convention for it is recorded, see open question 8.

## Plan

### Step 0: confirm the open questions, then edit the specs

Do this first. The repo requires user confirmation for every spec edit, see
`AGENTS.md:93` and `docs/guidelines.md:78-80`. The exact edits are in step 1. Steps 2 to 6
wait until the eight open questions at the end of this plan are answered. Accepting the
stated assumptions counts as an answer.

### Step 1: spec and doc edits, one commit

Commit subject: `docs(specs): Add overdue tickets, TKT-014, TKT-015, CLI-010`.

`docs/product-specs/tickets.md`, append after TKT-013:

```markdown
### TKT-014: Overdue tickets

A ticket is overdue when the current time is later than its due time, see TKT-005, and
its state is `open` or `assigned`. A `closed` ticket is never overdue. A ticket whose due
time equals the current time is not overdue. Being overdue changes no state and appends
no event.

### TKT-015: Overdue listing order

Listing overdue tickets returns only overdue tickets, sorted by due time ascending. Two
tickets with the same due time are sorted by ID ascending.
```

`docs/product-specs/cli.md`:

- CLI-001, line 14: "one of four subcommands" becomes "one of five subcommands", and the
  list gains `overdue`.
- CLI-006, line 42: after "padded to 8 characters" add "For a ticket that is overdue per
  TKT-014 the state column shows `OVERDUE` instead of the state."
- CLI-007 TODO, line 50: add `overdue` to the commands the corrupt-log gap applies to.
- Append CLI-010:

```markdown
### CLI-010: overdue

`ticketdesk overdue` prints one line per overdue ticket, earliest due first, see TKT-015.
Each line has the format of CLI-006, so the state column reads `OVERDUE`. With no overdue
tickets it prints nothing.
```

`docs/product-specs/event-log.md`, LOG-001, line 14: "Listing tickets appends nothing"
becomes "Listing tickets, with `list` or `overdue`, appends nothing."

`docs/architecture.md`:

- Line 12, the CLI to service arrow: `create / assign / close / list / overdue`.
- Key technical assumptions, after line 69: "**The current time comes from the store's
  clock.** The service asks the store's clock for the current time when it decides whether
  a ticket is overdue. A fake clock in a test controls both event times and overdue
  checks."
- Project layout, line 95: add `test_cli.py  Output lines and exit codes through a subprocess`.
- Line 103: replace "The CLI is not covered by tests today." with "The CLI is tested
  through a subprocess in `tests/test_cli.py`."

`AGENTS.md`:

- Line 82 and line 84, the summaries of `tickets.md` and `cli.md`: add "overdue".
- Line 102: the test count. The number is set in step 6 after `make test` reports it.
- After line 106: `python3 -m ticketdesk.cli --log /tmp/t.jsonl overdue`.
- Line 114: add "Overdue view in `list` and the `overdue` command." to Done.
- Line 116: replace "Not covered by tests: the CLI." with "CLI tests cover `list` and
  `overdue` only."

`docs/product-specs/README.md`, lines 80 and 82: add "overdue" to the index summaries of
`tickets.md` and `cli.md`.

### Step 2: the rule in the service, `ticketdesk/tickets.py`

Add a method to `Ticket` after the `due_at` field at line 21:

```python
    def is_overdue(self, now):
        """Past due and not closed. Implements TKT-014."""
        return self.state != "closed" and now > self.due_at
```

Add two methods to `TicketService` after `list()` at line 47:

```python
    def now(self):
        """The current time from the store's clock, see INV-005."""
        return self.store.clock()

    def overdue(self, now=None):
        """Overdue tickets, earliest due first. Implements TKT-015."""
        now = self.now() if now is None else now
        return sorted((t for t in self._tickets().values() if t.is_overdue(now)),
                      key=lambda t: (t.due_at, t.id))
```

`list()`, `get()`, `create()`, `assign()`, and `close()` do not change. `ticketdesk/__init__.py`
does not change, because `Ticket` and `TicketService` are already exported at line 1.

### Step 3: the command and the line format, `ticketdesk/cli.py`

Add the subparser after line 18: `sub.add_parser("overdue")`.

Replace the `else:` branch at lines 28 to 30. On `HEAD` that branch catches every command
that is not `create`, `assign`, or `close`, so an `overdue` command would print the full
list. The prototype confirmed this trap. The replacement is explicit:

```python
        elif args.cmd == "list":
            now = svc.now()
            for t in svc.list():
                print(_line(t, now))
        elif args.cmd == "overdue":
            now = svc.now()
            for t in svc.overdue(now):
                print(_line(t, now))
```

Add one module-level helper above `main()`. It holds the only formatting decision and no
rule, which keeps the CLI boundary described in `docs/architecture.md:34-38`:

```python
def _line(t, now):
    """One list line per CLI-006. The state column reads OVERDUE per TKT-014."""
    state = "OVERDUE" if t.is_overdue(now) else t.state
    return f"#{t.id} [{t.priority}] {state:<8} {t.title}"
```

The `create`, `assign`, and `close` branches and the `TicketError` handling do not change.

### Step 4: service tests, `tests/test_tickets.py`

Add cases to `TicketTests`. Each passes `now` explicitly to `overdue()`. The fake `Clock` at
line 8 advances by one second on every call, and the prototype showed that the default
`now` consumes one tick. The cases, each named with the spec it implements:

- `test_not_overdue_before_due`, TKT-014. Create a `P1`. `overdue(now=t.due_at - 1)` is empty.
- `test_not_overdue_at_exact_due_time`, TKT-014. `overdue(now=t.due_at)` is empty.
- `test_overdue_after_due`, TKT-014. `overdue(now=t.due_at + 1)` returns the ticket.
- `test_assigned_ticket_can_be_overdue`, TKT-014. Assign, then check past due.
- `test_closed_ticket_is_never_overdue`, TKT-014. Close, then check far past due. Empty.
- `test_overdue_sorted_by_due_then_id`, TKT-015. Create `P1`, `P3`, `P1` in that order.
  Far past due, the IDs come back as `[1, 3, 2]`. The prototype produced exactly that.
- `test_overdue_appends_nothing`, LOG-001. The replayed kinds are unchanged after `overdue()`.
- `test_now_comes_from_store_clock`, INV-005. `svc.now()` equals the fake clock's next value.

### Step 5: CLI tests, new file `tests/test_cli.py`

Test type: subprocess through the CLI, as `docs/guidelines.md:31` names it. A helper runs
`[sys.executable, "-m", "ticketdesk.cli", "--log", log, *args]` with `cwd` set to the repo
root, `capture_output=True`, and `text=True`. Each test gets its own temporary directory.

The fixture is a log written directly to a file, the pattern of `tests/test_store.py:12`.
Its `created` events carry `at` values near `1000.0`, so they are overdue under the real
clock. A ticket that must not be overdue is created through the CLI with priority `P3`,
which gives a 72 hour margin. The fixture used on the prototype is:

```text
{"at": 1000.0, "id": 1, "kind": "created", "priority": "P3", "title": "Old P3"}
{"at": 2000.0, "id": 2, "kind": "created", "priority": "P1", "title": "Old P1"}
{"at": 3000.0, "id": 3, "kind": "created", "priority": "P2", "title": "Old P2 closed"}
{"at": 4000.0, "id": 3, "kind": "closed", "resolution": "Replaced the toner cartridge"}
{"at": 5000.0, "id": 4, "kind": "created", "priority": "P1", "title": "Old P1 assigned"}
{"at": 6000.0, "id": 4, "kind": "assigned", "assignee": "dana"}
```

Cases:

- `test_list_marks_overdue_tickets`, CLI-006. After one `create "Fresh" --priority P3`,
  `list` prints exactly these five lines and exits 0 with empty stderr:

```text
#1 [P3] OVERDUE  Old P3
#2 [P1] OVERDUE  Old P1
#3 [P2] closed   Old P2 closed
#4 [P1] OVERDUE  Old P1 assigned
#5 [P3] open     Fresh
```

- `test_overdue_lists_only_overdue_in_due_order`, CLI-010 and TKT-015. `overdue` prints
  `#2`, `#4`, `#1` in that order and nothing else. Due times are 16400, 19400, and 260200.
- `test_overdue_with_no_log_prints_nothing`, CLI-010 and LOG-006. A missing log file gives
  empty stdout, empty stderr, exit 0, and no file is created.
- `test_list_and_overdue_append_nothing`, LOG-001. The log bytes are identical before and
  after both commands.
- `test_unknown_subcommand_is_a_usage_error`, CLI-001. `bogus` exits 2 with usage on
  stderr, and the usage names `overdue`.

### Step 6: checks and the end-to-end sequence

Run `make lint && make test` from the repo root. Record the new test count in `AGENTS.md`
line 102. Then run this sequence against a temporary log and compare with the expected
output in the comments:

```bash
L=$(mktemp -d)/t.jsonl
printf '%s\n' '{"at": 1000.0, "id": 1, "kind": "created", "priority": "P1", "title": "Old"}' > "$L"
python3 -m ticketdesk.cli --log "$L" create "Fresh" --priority P3   # #2 open Fresh
python3 -m ticketdesk.cli --log "$L" list      # #1 OVERDUE, #2 open
python3 -m ticketdesk.cli --log "$L" overdue   # #1 only
python3 -m ticketdesk.cli --log "$L" close 1 "Replaced the toner cartridge"
python3 -m ticketdesk.cli --log "$L" overdue   # nothing, exit 0
wc -l "$L"                                     # 3 lines
```

### Commits

Three commits, one logical change each, per `docs/guidelines.md:84-87`:

1. `docs(specs): Add overdue tickets, TKT-014, TKT-015, CLI-010`
2. `feat(tickets): Compute overdue tickets from the due time, TKT-014, TKT-015`
3. `feat(cli): Mark overdue tickets in list and add the overdue command, CLI-006, CLI-010`

## Assumptions validated

Every assumption carries its evidence. The prototype ran in a scratch copy of the repo at
`/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/bp-exp/repo`.

- **Every ticket has `due_at` in epoch seconds after replay.** Confirmed.
  `ticketdesk/tickets.py:35-36` sets it from `due_at(ev["at"], ev["priority"])`, and
  `ticketdesk/sla.py:9` returns `created_at + hours * 3600`. `ticketdesk/store.py:20`
  stamps `at` from `self.clock()`, which defaults to `time.time` at `store.py:14`. LOG-004
  documents the unit.
- **The store's clock is public and side-effect free.** Confirmed. `store.py:16` assigns
  `self.clock` with no underscore, and `store.py:20` is its only use. The prototype called
  it from the service and the log line count stayed at 7 across two `overdue` runs.
- **The fake test clock advances on every call.** Confirmed. `tests/test_tickets.py:12-14`
  adds one second per call, and the prototype measured one tick consumed by a default
  `overdue()`. Step 4 passes `now` explicitly for that reason.
- **The `else:` branch at `cli.py:28` would swallow `overdue`.** Confirmed by a probe:
  argparse accepts the new subcommand and sets `args.cmd = "overdue"`, which is not
  `create`, `assign`, or `close`, so the `HEAD` branch would print the full list.
- **`OVERDUE` fits the 8 character pad of CLI-006.** Confirmed. The prototype `list`
  output aligned `OVERDUE  `, `closed   `, and `open     ` in the same column.
- **Sorting by `(due_at, id)` gives earliest due first with a stable tie-break.**
  Confirmed. A probe sorted `[(3, 5.0), (1, 5.0), (2, 4.0)]` to `[(2, 4.0), (1, 5.0),
  (3, 5.0)]`, and the prototype returned `[1, 3, 2]` for a `P1`, `P3`, `P1` sequence.
- **The boundary `now > due_at` excludes the exact due time.** Confirmed. The prototype
  returned an empty list at `now=t.due_at` and the ticket at `now=t.due_at + 1`.
- **A closed ticket drops out of `overdue`.** Confirmed. After closing ticket 1 the
  prototype returned `[3, 2]`.
- **The CLI runs as a subprocess from the repo root with no install.** Confirmed.
  `python3 -m ticketdesk.cli --log ...` produced the `list` and `overdue` output above and
  exited 0, and `bogus` exited 2 with usage naming `overdue`. An in-process call of
  `main(argv)` under `redirect_stdout` also worked, and is the fallback if subprocess tests
  prove slow.
- **A pre-dated log file makes a ticket overdue under the real clock.** Confirmed. The
  fixture in step 5 produced three `OVERDUE` lines through the real `time.time` clock.
- **Existing tests and lint stay green with the change.** Confirmed. `make lint && make
  test` on the prototype reported 7 tests OK, the same as on `HEAD`.
- **Python 3.11+ syntax only.** Confirmed. The change adds no syntax newer than
  `tickets.py:19` already uses. CI runs 3.12 per `.github/workflows/ci.yml:10`. The local
  interpreter is 3.15.1.

## Spec cross-validation

| ID | Requirement | Plan line | Verdict |
|----|-------------|-----------|---------|
| INV-001 | Log is the only source of state | Overdue is derived at read time, no cache or file | Upheld |
| INV-002 | Events never edited | No event is written or changed | Upheld |
| INV-003 | IDs never reused | Untouched | Upheld |
| INV-004 | Corrupt data fails fast | `overdue` replays through the same store | Upheld, same gap as CLI-007 TODO |
| INV-005 | Time from the store's clock | `TicketService.now()` reads `store.clock` | Upheld, documented in step 1 |
| TKT-001 | States are open, assigned, closed | `OVERDUE` is a display word, not a state | Upheld |
| TKT-005 | Due time by priority | Reused unchanged | Upheld |
| TKT-013 | `list` sorted by ID | `list()` unchanged | Upheld |
| TKT-014 | Overdue definition | New, step 1 and step 2 | Needs confirmation |
| TKT-015 | Overdue order | New, step 1 and step 2 | Needs confirmation |
| LOG-001 | Listing appends nothing | Extended to `overdue`, tested in steps 4 and 5 | Edit needs confirmation |
| LOG-002, LOG-003 | Event kinds and fields | No new kind | Upheld |
| LOG-006 | Missing log means no tickets | `overdue` prints nothing, exit 0 | Upheld, tested in step 5 |
| LOG-009 | Replay is deterministic | Overdue applied after replay, not during | Upheld |
| CLI-001 | Four subcommands | Becomes five | Edit needs confirmation |
| CLI-002 | Log path selection | Untouched | Upheld |
| CLI-006 | `list` line format | State column may read `OVERDUE` | Edit needs confirmation |
| CLI-007 | Rule errors exit 2 | `overdue` raises no `TicketError` | Upheld, TODO note extended |
| CLI-008 | Success exits 0, no stderr | Tested in step 5 | Upheld |
| CLI-010 | `overdue` command | New, step 1 and step 3 | Needs confirmation |

No invariant is broken. Four existing specs change and three are added. All edits are
gated on step 0.

## Architecture cross-validation

- **Boundaries.** The rule lives in `tickets.py`, the format in `cli.py`, the file in
  `store.py`. No layer crossing, see `docs/architecture.md:34-50`.
- **Deviation to confirm.** The service reads the current time through the store's clock.
  `docs/architecture.md:49-50` describes the clock as the stamp for events. Step 1 adds one
  assumption bullet so this use is documented, not silent. The alternative, a second clock
  injected into `TicketService`, was rejected because tests would then hold two clocks to
  keep in sync.
- **Security.** Local file, no auth, no network. Nothing new.
- **Scalability.** `overdue` replays the whole log once, the same cost as every other
  command, accepted at `docs/architecture.md:62-63`.
- **Observability.** A command line tool. Errors reach stderr as today.
- **Async machinery.** None in the project, none added.

## Project conventions to follow

- **[`AGENTS.md:86-96`]** Convention: *lint and test before every push, validate
  assumptions, doc changes need user confirmation, surface conflicts, reference spec IDs.*
  **Reflected in plan:** step 0 gates the doc edits and step 6 runs both checks. Every
  code comment, test name, and commit subject in steps 2 to 5 carries its spec ID.
- **Per-component conventions.** No `AGENTS.md` exists below the root. `find` over the repo
  found only the root file. Doesn't constrain this plan beyond the root rules.
- **[`AGENTS.md:25`, `pyproject.toml:1-8`]** Convention: *no dependencies, no lockfile, no
  package manager.* **Reflected in plan:** steps 2 to 5 use only the standard library,
  `argparse`, `subprocess`, and `unittest`.
- **[`Makefile:1-5`, `AGENTS.md:100-102`]** Convention: *`make test` runs `unittest
  discover -s tests -q`, `make lint` runs `compileall`.* **Reflected in plan:** step 6 runs
  both, and step 5 places the new file under `tests/` so discovery finds it.
- **[`AGENTS.md:22`, `tests/test_tickets.py:8-21`, `docs/guidelines.md:29-34`]** Convention:
  *`unittest`, tests in `tests/`, a fake clock injected through the store constructor, no
  mocking library, test files and cases named up front with the test type.* **Reflected in
  plan:** step 4 reuses `Clock`, step 5 names the subprocess type, and both list every case.
- **[`docs/guidelines.md:9-11`]** Convention: *every module ships with tests, no numeric
  coverage target recorded.* **Reflected in plan:** step 5 brings the first CLI tests. Open
  question 7 asks whether `create`, `assign`, and `close` should get CLI tests in the same
  change.
- **[`AGENTS.md:23`, `docs/architecture.md:81`]** Convention: *lint is a syntax pass only, no
  style or type checker.* **Reflected in plan:** doesn't constrain style. Step 6 runs it.
- **Migrations.** Doesn't constrain this plan. The event replay model needs no migration,
  see `docs/architecture.md:78`, and no event kind is added.
- **[`ticketdesk/cli.py:8,13`, CLI-002]** Convention: *the log path comes from `--log`, then
  `TICKETDESK_LOG`, then `tickets.jsonl` in the current directory. `DEFAULT_LOG` is read at
  import time.* **Reflected in plan:** steps 5 and 6 always pass `--log`, so no test writes
  `tickets.jsonl` into the repo and no test depends on the environment variable.
- **Async machinery.** None in the project. Doesn't constrain this plan.
- **[`ticketdesk/sla.py:6-9`, `ticketdesk/cli.py:30`, `docs/README.md:43`]** Convention:
  *reuse `due_at()` for time math, one f-string line per command, `# implements TKT-010`
  style comments.* **Reflected in plan:** step 2 reuses the stored `due_at`, step 3 keeps
  the f-string in `_line()`, and every new function names its spec ID.
- **[`docs/README.md:22-28`, `docs/product-specs/README.md:14-19`]** Convention: *one
  behavior per spec, testable from the text, next free number, never renumber.* **Reflected
  in plan:** step 1 adds TKT-014, TKT-015, and CLI-010 as the next free numbers and edits
  existing IDs in place.
- **[`docs/README.md:49-58`]** Convention: *a product behavior change updates the feature
  spec, an architectural change updates `architecture.md`.* **Reflected in plan:** step 1
  edits both plus the two indexes.
- **[`docs/guidelines.md:82-87`, commit `f87e57b`]** Convention: *one logical change per
  commit, spec IDs in the message, `type(scope): Subject` form.* **Reflected in plan:** the
  three commits under step 6.

## Codebase sweep

- **In-flight work.** One commit, `f87e57b`, one branch, `main`, clean tree. Nothing in
  flight in `tickets.py` or `cli.py`.
- **Shadow duplication.** `grep -rniE 'overdue|now\(|clock'` found no overdue logic and
  only the store's clock. `due_at` is the single time computation. Step 2 builds on it.
- **Caller-side drift.** No signature changes. `list()` keeps its shape, `Ticket` gains a
  method and no positional field, so the constructor call at `tickets.py:35` is unaffected.
  The one drift trap is the `else:` branch at `cli.py:28`, fixed in step 3.
- **Test infrastructure gap.** No CLI test exists, see `AGENTS.md:116` and
  `docs/architecture.md:103`. Step 5 brings it up with a subprocess helper and a pre-dated
  log fixture. No new tooling is needed.

## Counterfactual against the success criteria

| Criterion | Plan step | Verdict |
|-----------|-----------|---------|
| S1. `list` shows `OVERDUE` for an open or assigned ticket past due, other lines unchanged | Steps 2, 3, and the first case of step 5 | Confirmed |
| S2. `overdue` prints only overdue tickets, earliest due first | Steps 2, 3, step 4 ordering case, step 5 ordering case | Confirmed |
| S3. Neither command appends to the log | No append path in steps 2 and 3, asserted in steps 4 and 5 | Confirmed |
| S4. A closed ticket never shows as overdue | `is_overdue` in step 2, asserted in steps 4 and 5 | Confirmed on assumption 1 |
| S5. Lint and all tests green, new rule and command tested | Steps 4, 5, and 6 | Confirmed |
| S6. Specs updated with confirmation, invariants intact | Steps 0 and 1, the spec table above | Confirmed with a gap |

Overall: **Confirmed with gaps.** The one gap is S6. The spec edits exist in this plan but
land only after you confirm them in step 0.

## Test plan

- **Unit, through the service** with the fake clock: the eight cases in step 4. They cover
  the boundary at the exact due time, each state, the sort order with a tie, and that
  `overdue()` appends nothing.
- **Subprocess, through the CLI**: the five cases in step 5. They cover the exact `list`
  lines, the `overdue` order, the empty case, the unchanged log, exit codes, and stderr.
- **End to end, manual**: the command sequence in step 6 against a temporary log, which
  also exercises `close` removing a ticket from `overdue`.
- **Regression**: the existing 7 tests, unchanged, stayed green on the prototype.

## Risks and mitigations

- **Consumers that parse column 3 of `list` as the state** will see `OVERDUE`. The spec
  edit to CLI-006 makes this deliberate. If you object, open question 3 names the marker
  column alternative, which changes the line shape for every row instead.
- **The 72 hour margin in CLI tests.** The fresh `P3` ticket in step 5 becomes overdue if
  the suite runs more than 72 hours after the test starts. Acceptable.
- **A hand-edited log with a non-numeric `at`** would break the comparison. The project
  already trusts events, see `docs/architecture.md:66-67`. No new handling.
- **A `Ticket` built by hand without the service** has `due_at = 0.0` and would read as
  overdue. The service always sets it at `tickets.py:36`, and the dataclass default
  predates this change. No new handling.
- **Subprocess tests cost about 50 ms each.** Five cases add well under a second. If that
  grows, the in-process `main(argv)` path confirmed on the prototype is the fallback.

## Open questions

Nobody was available during this run, so each question states the assumption the plan
proceeds on.

1. **Is a closed ticket ever overdue?** Assumption: no. `list` shows `closed` and
   `overdue` omits it. An SLA breach report for late closures is out of scope.
2. **Is a ticket overdue at exactly its due time?** Assumption: no. Overdue starts strictly
   after `due_at`.
3. **Should `OVERDUE` replace the state word on a `list` line, or sit in its own column?**
   Assumption: replace. It fits the 8 character pad and keeps every other line unchanged.
   The cost is that an overdue line no longer says open or assigned.
4. **Should `overdue` print the same line format as `list`?** Assumption: yes, one format
   to document and test. Every line then reads `OVERDUE`, which is redundant but consistent.
5. **May the service take the current time from the store's clock?** Assumption: yes, with
   the one-line addition to `docs/architecture.md` in step 1.
6. **Do you confirm the eight doc edits in step 1?** They touch `tickets.md`, `cli.md`,
   `event-log.md`, `architecture.md`, `AGENTS.md`, and `product-specs/README.md`.
   Assumption: yes, pending your review of the exact wording.
7. **Should this change also add CLI tests for `create`, `assign`, and `close`?**
   Assumption: no. `docs/guidelines.md:84-87` asks for one logical change per commit, so
   those tests are a separate change.
8. **Should `pyproject.toml` move from 0.3.0 to 0.4.0 for a new command?** Assumption: no.
   No versioning rule is recorded in the repo.

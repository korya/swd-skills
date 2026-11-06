# Plan: OVERDUE in `ticketdesk list` and a new `ticketdesk overdue` command

Status: plan only. No code or doc in the repo changed. Date: 2026-11-05. Base: `main` at `7c62f26`.

## Headline

`TicketService` derives "overdue" at read time from the due time each ticket already has and one reading of the store's clock. `ticketdesk list` then prints `OVERDUE` in the state slot, and a new `ticketdesk overdue` prints only those tickets, earliest due time first. The implementation waits for your sign-off on the spec changes, above all the `OVERDUE` display in CLI-006.

## Approach summary

Overdue is a derived fact that the service computes after replay, not a state and not an event. `ticketdesk/tickets.py` gets a `Ticket.overdue` flag, a private `_current()` helper that sets the flag, and a public `overdue()` method. `_current()` reads the store's clock once per command, so one output judges every ticket against the same instant. A ticket is overdue when it is `open` or `assigned` and the clock reads later than its due time. `ticketdesk/cli.py` gets the `overdue` subcommand and one shared line format that prints `OVERDUE` instead of the state when the flag is set.

The log format, the replay code, `sla.py`, `store.py`, and the ID order of `list` stay as they are. The plan stands on two assumptions that a prototype confirmed. Every replayed ticket already carries its due time, and the service can reach the injectable clock of the store. The main trade-off is that `OVERDUE` replaces `open` or `assigned`, so `list` no longer shows which overdue tickets have an owner. I accept that cost because `OVERDUE` fits the 8-character state slot, and a separate marker is ambiguous next to a free-text title.

## Out of scope

- A stored overdue state. No new event kind, no new log field, no change to `store.py`.
- The open TODO under CLI-007. `overdue` on a corrupt log ends with a traceback and exit code 1, the same as `list` today.
- More columns in the output, such as the due time, the delay, or the assignee.
- A filter flag on `list`, notifications, and escalation.
- A report of tickets that were closed after their due time.
- A richer SLA, such as business hours.
- A version bump and a `.gitignore`.

## Plan

### What the user sees

The same log prints these lines on `main` and on the prototype. Tickets 1 to 3 were created in 1970, ticket 2 is assigned, ticket 3 is closed, and tickets 4 and 5 are new.

| Command | Today on `main` | After the change |
|---|---|---|
| `list` | `#1 [P3] open     ancient P3` | `#1 [P3] OVERDUE  ancient P3` |
| | `#2 [P1] assigned ancient P1` | `#2 [P1] OVERDUE  ancient P1` |
| | `#3 [P2] closed   ancient P2, will be closed` | unchanged |
| | `#4 [P1] open     fresh one` | unchanged |
| | `#5 [P3] open     OVERDUE invoice from vendor` | unchanged |
| `overdue` | `invalid choice: 'overdue'`, exit code 2 | `#2 [P1] OVERDUE  ancient P1` |
| | | `#1 [P3] OVERDUE  ancient P3` |

Ticket 2 sorts before ticket 1 in `overdue` because a P1 is due after 4 hours and a P3 after 72.

### Step 0. Get sign-off on the spec text (gate)

The repo forbids a spec change without the user's confirmation (`AGENTS.md:93`, `docs/guidelines.md:78-80`). Steps 1 to 5 start only after you accept or correct this table. New items take the next free numbers, TKT-014, TKT-015, and CLI-010 (`docs/README.md:27-28`).

| Spec | Today | Proposed |
|---|---|---|
| TKT-014 (new) | none | **Overdue.** A ticket is overdue when its state is `open` or `assigned` and the current time is later than its due time. A ticket at exactly its due time is not overdue. A `closed` ticket is never overdue. Overdue is not a state, and no event records it. |
| TKT-015 (new) | none | **Overdue listing order.** Listing overdue tickets returns only the overdue tickets, sorted by due time ascending. Tickets with the same due time are sorted by ID ascending. |
| CLI-001 | "takes one of four subcommands. They are `create`, `assign`, `close`, and `list`." | "takes one of five subcommands. They are `create`, `assign`, `close`, `list`, and `overdue`." |
| CLI-006 | "Each line is `#<id> [<priority>] <state> <title>` with the state padded to 8 characters." | Add: "For an overdue ticket, see TKT-014, the line shows `OVERDUE` in place of the state." |
| CLI-010 (new) | none | **overdue.** `ticketdesk overdue` prints one line per overdue ticket in the order of TKT-015. Each line has the format of CLI-006. With no overdue tickets it prints nothing. |
| LOG-001 | "Listing tickets appends nothing." | "Listing tickets or overdue tickets appends nothing." |

The change must also uphold these existing items. None of them needs a text change.

| Item | What it requires | Plan step | Evidence |
|---|---|---|---|
| TKT-001 | The state is `open`, `assigned`, or `closed`. | 1. `overdue` is a separate flag, and `state` keeps its value. | A8 |
| TKT-005 | The due time is the creation time plus the hours of the priority. | 1 reuses `due_at` and does not recompute it. | A1 |
| TKT-013 | Listing returns every ticket sorted by ID. | 1 keeps the sort key of `list()`. | A6 |
| CLI-008 | Success is exit code 0 with an empty stderr. | 2 | A10 |
| LOG-002, LOG-003 | Three event kinds with fixed fields. | 1 adds no event. | A3 |
| LOG-006 | A missing log behaves as no tickets. | 1, 2 | `test_overdue_prints_nothing_without_a_log` |
| LOG-009 | Replay is deterministic. | 1 leaves `_tickets()` alone and sets the flag after it. | A4 |
| INV-001, INV-002 | The log is the only state, and no line changes. | 1 stores nothing. | A3 |
| INV-005 | Time comes from the store's clock, never from the caller. | 1 reads `self.store.clock()`. | A2 |

### Step 1. Service: `ticketdesk/tickets.py`

Add the flag as the last field of `Ticket`, after `due_at` at line 21. The only constructor call passes four positional arguments (`tickets.py:35`), so a defaulted last field breaks nothing.

```python
    overdue: bool = False   # TKT-014: derived on read, never replayed
```

Add `_current()` and `overdue()`, and point `list()` and `get()` at `_current()` (today lines 46-53). Leave `_tickets()` and the `_tickets()` call in `create()` at line 59 alone.

```python
    def _current(self):
        """Replayed tickets, each flagged overdue against one reading of the store's clock."""
        now = self.store.clock()
        tickets = self._tickets()
        for t in tickets.values():
            t.overdue = t.state != "closed" and now > t.due_at   # TKT-014
        return tickets

    def list(self):
        return sorted(self._current().values(), key=lambda t: t.id)

    def overdue(self):   # TKT-015
        late = [t for t in self._current().values() if t.overdue]
        return sorted(late, key=lambda t: (t.due_at, t.id))

    def get(self, ticket_id):
        try:
            return self._current()[ticket_id]
        except KeyError:
            raise TicketError(f"no ticket {ticket_id}") from None
```

### Step 2. CLI: `ticketdesk/cli.py`

Add the subparser after line 18, and replace the `else` branch at lines 28-30. The branch is shared on purpose, so the two commands cannot drift apart in format.

```python
    sub.add_parser("overdue")
```

```python
        else:
            for t in (svc.overdue() if args.cmd == "overdue" else svc.list()):
                label = "OVERDUE" if t.overdue else t.state   # CLI-006
                print(f"#{t.id} [{t.priority}] {label:<8} {t.title}")
```

The subparser alone is a trap. With only that line added, `ticketdesk overdue` fell into the `else` branch and printed the full list with exit code 0.

### Step 3. Service tests: `tests/test_tickets.py`

Add seven methods to the existing `TicketTests` class. The test plan below names them. Do not subclass `TicketTests`. A subclass reran the six inherited tests in the prototype, which gave 22 tests where 16 were written.

### Step 4. CLI tests: new `tests/test_cli.py`

Create the first CLI test file with three subprocess cases. Each case writes `created` events with `at` values of `1.0` and `2.0` to a temporary log. Those tickets are overdue under the real clock, so the CLI needs no clock option.

### Step 5. Docs, each edit after your confirmation

- `docs/product-specs/tickets.md`, `cli.md`, `event-log.md`: the text from step 0.
- `docs/architecture.md:12`: add `overdue` to the call list in the diagram.
- `docs/architecture.md:68-69`: say that the service also reads the store's clock to judge overdue.
- `docs/architecture.md:103`, `AGENTS.md:116`, `docs/guidelines.md:10-11`: each says the CLI has no tests. That is stale after step 4.
- `AGENTS.md:102`: "7 unittest cases" becomes 17.
- `AGENTS.md:82`, `AGENTS.md:84`, `AGENTS.md:114`, `docs/product-specs/README.md:80`: add overdue to the summaries.

### Step 6. Check and commit

Run `make lint && make test`, then the end-to-end sequence from the test plan. Commit code, tests, and specs as one logical change (`docs/guidelines.md:84-87`). Name TKT-014, TKT-015, and CLI-010 in the message.

## Assumptions validated

The falsifier targets the shape "read-time flag". If overdue needs a write to the log, or changes what replay returns, the shape is wrong. Overdue would then be an event or a stored state, and INV-001, LOG-002, and TKT-001 would be in play. The prototype did not trigger it. Rows A3 and A4 hold the evidence.

All scripts and logs are under `outputs/scratch/`. The prototype is `scratch/proto/`, and its diffs are `scratch/prototype-code.diff` and `scratch/prototype-tests.diff`.

| # | Assumption | Class | Result | Evidence |
|---|---|---|---|---|
| A1 | Every replayed ticket carries its due time. | Verified | confirmed | `ticketdesk/tickets.py:36` |
| A2 | The service can reach the store's clock, and a test can move it. | Plausible | confirmed | `ticketdesk/store.py:14-16`, `tests/test_tickets.py:8-20`. `probe1.py` printed `A2 clock reachable via store.clock.now: 1700003603.0`. |
| A3 | `list`, `overdue`, and `get` append nothing (LOG-001, INV-002). | Risky | confirmed | `probe2.py` printed `L1 log unchanged by list/overdue/get: True`. The CLI run left the `shasum` of the log the same. |
| A4 | Replay stays independent of the clock (LOG-009). | Risky | confirmed | `probe2.py` printed `L2 replay equal at two clock values: True \| replayed overdue flags {False}`. |
| A5 | `OVERDUE` fits the state slot without moving the title. | Plausible | confirmed | `probe1.py` printed `A4 '#1 [P1] OVERDUE  title' 8`. |
| A6 | Due order differs from ID order, so `overdue` needs its own sort. | Plausible | confirmed | `probe1.py` printed `A8 id order      : [1, 2, 3]` and `A8 due_at order  : [2, 3, 1]`. |
| A7 | The boundary is strict. Exactly at the due time is not overdue. | Plausible | confirmed | `probe2.py` printed `B1 now == due_at   -> []` and `B2 now == due_at+1 -> [2]`. |
| A8 | A closed ticket drops out, and an assigned ticket keeps its real state. | Plausible | confirmed | `probe2.py` printed `S2 closed drops    -> [(2, 'assigned'), (1, 'open')]`. |
| A9 | The seven existing tests pass with the change. | Risky | confirmed | `Ran 7 tests` and `OK` on the prototype before I added new tests. |
| A10 | A CLI test can make a ticket overdue without a clock option. | Risky | confirmed | A hand-written log with `"at": 1.0` printed `#1 [P3] OVERDUE  ancient P3`. Three subprocess tests pass. |
| A11 | `overdue` is free as a command name, and `argparse` rejects extra arguments. | Plausible | confirmed | On `main`: `invalid choice: 'overdue'`, exit code 2. On the prototype: `unrecognized arguments: extra`, exit code 2. |
| A12 | The planned tests can fail. | Plausible | confirmed | The 17 tests against unmodified code gave `FAILED (failures=3, errors=7)`. With the ID key removed from the prototype, `test_overdue_tie_breaks_by_id` failed. |
| A13 | The change runs on the CI interpreter. | Plausible | partial | `Ran 17 tests` and `OK` on Python 3.12.16 and 3.15.2. Python 3.11, the floor in `pyproject.toml:5`, is not installed here. |

One of my own prototype tests failed first, and the cause shapes step 3. The fake clock adds one second on every read (`tests/test_tickets.py:12-14`). My boundary test read the clock twice, so the second read was one second past due. The service was right and the test was wrong.

The codebase sweep found no conflict and one missing layer of tests.

- **In-flight work.** None. The repo has one commit and one branch, and `grep -i overdue` finds nothing.
- **Duplicate logic.** None. `sla.py` already owns the due time, and step 2 keeps one line format for both commands.
- **Callers of the changed contract.** `list()` has one caller, `ticketdesk/cli.py:29`. `get()` has five, all inside `tickets.py` (lines 61, 64, 70, 73, 79). No test calls either.
- **Test infrastructure.** The service layer has a fake clock. The CLI has no tests at all (`AGENTS.md:116`), so step 4 builds that layer.

## Project conventions to follow

- **[`AGENTS.md:35-38`, `docs/architecture.md:36-38`]** Convention: the CLI holds no ticket rule. **Reflected in plan:** step 1 puts the overdue rule in the service. Step 2 only maps the flag to a label.
- **[`docs/architecture.md:49-50`, `docs/architecture.md:68-69`, INV-005]** Convention: time comes from the store's injectable clock, never from the caller. **Reflected in plan:** step 1 reads `self.store.clock()`. The CLI never calls `time.time()`.
- **[`docs/architecture.md:43-44`]** Convention: the service derives every ticket from the event list, so a rule change needs no migration. **Reflected in plan:** step 1 adds no event and no file. Migrations do not constrain this plan.
- **[`Makefile:3`, `AGENTS.md:22`]** Convention: tests are `unittest`, run by `make test`. **Reflected in plan:** steps 3 and 4 add `unittest` cases under `tests/`, which discovery finds.
- **[`tests/test_tickets.py:8-20`]** Convention: tests inject a fake clock and use no mocking library. **Reflected in plan:** step 3 moves `self.store.clock.now`. Step 4 uses old `at` values instead of a patched clock.
- **[`docs/guidelines.md:29-31`]** Convention: name the test files, the cases, and the type, unit through the service or subprocess through the CLI. **Reflected in plan:** the test plan names all ten cases and both types.
- **[`docs/guidelines.md:32-34`]** Convention: a user-visible change names the `ticketdesk` command sequence against a temporary log. **Reflected in plan:** the end-to-end sequence in the test plan.
- **[`Makefile:5`, `docs/guidelines.md:7-8`]** Convention: `make lint` is a `compileall` syntax pass over every file. **Reflected in plan:** step 6. It passed on the prototype, new test file included.
- **[`AGENTS.md:25`, `docs/architecture.md:76`]** Convention: no dependencies. **Reflected in plan:** steps 1 to 4 import only the standard library. The package manager does not constrain this plan.
- **[`pyproject.toml:5`, `.github/workflows/ci.yml:10`]** Convention: Python 3.11 or later, CI on 3.12. **Reflected in plan:** the code in steps 1 and 2 uses no syntax newer than the files it edits.
- **[`AGENTS.md:93`, `docs/README.md:39`, `docs/guidelines.md:78-80`]** Convention: no doc change without the user's confirmation. **Reflected in plan:** step 0 is a gate, and step 5 waits for it.
- **[`docs/README.md:22-28`]** Convention: one observable behavior per spec, stable IDs, next free number. **Reflected in plan:** step 0 uses TKT-014, TKT-015, and CLI-010 and renumbers nothing.
- **[`AGENTS.md:96`, `docs/guidelines.md:87`]** Convention: cite spec IDs in code comments, tests, and commits. **Reflected in plan:** the comments in steps 1 and 2, the test comments, and step 6.
- **[`docs/guidelines.md:84-86`]** Convention: one logical change per commit, no unrelated cleanup. **Reflected in plan:** step 6. The CLI-007 TODO and a `.gitignore` stay out.
- Ports, URLs, async machinery, and a formatter do not constrain this plan. The tool is a local command with no network, and the repo has no formatter (`docs/architecture.md:81`).

## Test plan

**Unit, through the service, in `tests/test_tickets.py`.** Each case takes one clock reading per assertion, because every read advances the fake clock.

| Case | Covers |
|---|---|
| `test_not_overdue_at_exact_due_time` | TKT-014, the boundary |
| `test_overdue_one_second_after_due_time` | TKT-014 |
| `test_assigned_ticket_stays_overdue_and_keeps_state` | TKT-014, TKT-001 |
| `test_closed_ticket_is_never_overdue` | TKT-014 |
| `test_overdue_sorted_by_due_time_not_id` | TKT-015, and TKT-013 for `list` |
| `test_overdue_tie_breaks_by_id` | TKT-015, with two hand-written events that share one `at` |
| `test_listing_overdue_appends_nothing` | LOG-001 |

**Subprocess, through the CLI, in `tests/test_cli.py`.** Each case runs `sys.executable -m ticketdesk.cli --log <temporary log>` with the repo root as the working directory.

| Case | Covers |
|---|---|
| `test_list_marks_overdue_in_the_state_slot` | CLI-006, CLI-008 |
| `test_overdue_lists_only_overdue_oldest_due_first` | CLI-010, CLI-008 |
| `test_overdue_prints_nothing_without_a_log` | CLI-010, LOG-006 |

**End to end.** Run this sequence from the repo root. `$L` is a new path under a temporary directory.

```bash
printf '%s\n' \
  '{"at": 1.0, "id": 1, "kind": "created", "priority": "P3", "title": "ancient P3"}' \
  '{"at": 2.0, "id": 2, "kind": "created", "priority": "P1", "title": "ancient P1"}' \
  '{"at": 3.0, "id": 3, "kind": "created", "priority": "P2", "title": "ancient P2, will be closed"}' > "$L"
python3 -m ticketdesk.cli --log "$L" create "fresh one" --priority P1
python3 -m ticketdesk.cli --log "$L" create "OVERDUE invoice from vendor"
python3 -m ticketdesk.cli --log "$L" assign 2 dana
python3 -m ticketdesk.cli --log "$L" close 3 "Replaced the toner cartridge"
python3 -m ticketdesk.cli --log "$L" list
python3 -m ticketdesk.cli --log "$L" overdue
```

The prototype printed these lines for `list` and then for `overdue`, each with exit code 0 and an empty stderr.

```text
#1 [P3] OVERDUE  ancient P3
#2 [P1] OVERDUE  ancient P1
#3 [P2] closed   ancient P2, will be closed
#4 [P1] open     fresh one
#5 [P3] open     OVERDUE invoice from vendor
```

```text
#2 [P1] OVERDUE  ancient P1
#1 [P3] OVERDUE  ancient P3
```

**Manual.** Run `ticketdesk overdue` against a path that does not exist. Expect no output, exit code 0, and no new file. Run `shasum` on the log before and after `list` and `overdue`. Expect the same sum.

## Risks and mitigations

- **A wrong system clock gives a wrong `OVERDUE`, and nothing reports it.** Overdue now depends on the wall clock at read time. The proposed TKT-014 says "the current time" so the dependency is on record. I see no cheaper mitigation.
- **`list` hides `open` versus `assigned` for overdue tickets.** A script that counts `open` lines misses them. No code in the repo parses the output, but your own scripts may. Open question 1 offers the alternative.
- **`Ticket.overdue` defaults to `False`.** Code that takes tickets straight from `_tickets()` sees `False` for every ticket. Step 1 routes `list()`, `get()`, and `overdue()` through `_current()`. `create()` uses `_tickets()` only for the next ID.
- **A strict reader of LOG-009 may object to a clock-derived field on `Ticket`.** Replay itself stays deterministic (A4), and the proposed TKT-014 says no event records overdue. If you want it stricter, the fallback is a `Ticket.is_overdue(now)` method with no stored flag.
- **`make lint` and `make test` leave untracked `__pycache__` directories.** The repo has no `.gitignore`. My baseline run left `tests/__pycache__/` and `ticketdesk/__pycache__/` in `git status`. Stage files by name in step 6.
- **Python 3.11 is untested here.** CI covers 3.12 only. The risk is low because the new code uses no syntax beyond what `tickets.py` and `cli.py` already use.
- **Subprocess tests are slower.** On Python 3.12 the suite went from 0.004 s for 7 tests to 0.186 s for 17.

## Counterfactual

Verdict: **Confirmed with gaps.** Every success criterion has a plan step. The gaps are the decisions in the open questions, and A13 is partial.

| Success criterion | Plan steps | Evidence |
|---|---|---|
| A ticket past its due time shows as `OVERDUE` in `ticketdesk list`. | 1, 2 | A5, A7, A10 |
| Other `list` lines and the ID order do not change. | 1, 2 | The end-to-end output, `test_overdue_sorted_by_due_time_not_id` |
| `ticketdesk overdue` lists only overdue tickets. | 1, 2 | A8, A10 |
| `ticketdesk overdue` lists the earliest due time first. | 1 | A6, A12 |
| Existing behavior does not regress. | 3, 4, 6 | A9, A3 |
| Specs and invariants hold, or the change is flagged. | 0, 5 | A3, A4, the table in step 0 |

The change would be proven wrong by any of these observations, and each has a test. A ticket one second past due prints its plain state. A closed ticket or a ticket not yet due prints `OVERDUE`. `overdue` follows ID order. `list` or `overdue` changes the log.

## Open questions

Nobody was available during this run. I proceed on the stated assumption for each question, and none is settled until you answer.

1. **Does `OVERDUE` replace the state in the line, or sit beside it?** Assumption: it replaces the state. A marker beside the state keeps `open` and `assigned` visible. It is ambiguous, though, because a title is free text. Ticket 5 above already prints `open     OVERDUE invoice from vendor` on `main`. The alternative changes one line in step 2 and the CLI-006 text.
2. **Should `ticketdesk overdue` print the real state instead of `OVERDUE`?** Assumption: no, both commands print the same line for the same ticket. Every line of `overdue` is overdue by definition, so the real state would say more there. The cost is a second format rule.
3. **Is a closed ticket ever overdue?** Assumption: never, even when it was closed after its due time.
4. **Is a ticket overdue at exactly its due time?** Assumption: no. "Pass their due time" reads as strictly later.
5. **Do you accept the spec text in step 0 and the doc edits in step 5?** Assumption: yes, as written. No code work starts before your answer.
6. **May the service read `store.clock` directly?** Assumption: yes, with no change to `store.py`. The alternative is a small `EventStore.now()` method, which makes the new use of the clock an explicit store API.
7. **Is `tests/test_cli.py` with subprocess cases the CLI test style you want?** Assumption: yes, per `docs/guidelines.md:31`. The coverage TODO at `docs/guidelines.md:10-11` stays open.
8. **Does this change bump the version from 0.3.0?** Assumption: no. The repo records no release rule.

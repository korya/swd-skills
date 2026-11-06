# Plan: OVERDUE in `ticketdesk list` and a new `ticketdesk overdue` command

This is a plan only. No code or doc in the repo changed. I planned it on 2026-11-05
against commit `b652f0b` on `main`.

## 1. Headline

The service derives "overdue" at read time from the due time and the store's clock, and
stores nothing new. `ticketdesk list` prints `OVERDUE` in the state column of an overdue
ticket, and `ticketdesk overdue` prints only those tickets, earliest due time first.
The plan changes two spec items and adds three, and the repo requires your sign-off on spec
edits before code work begins.

| Command | Today | After |
|---|---|---|
| `list`, ticket past due and not closed | `#2 [P1] assigned Old P1` | `#2 [P1] OVERDUE  Old P1` |
| `list`, every other ticket | `#3 [P1] open     Fresh ticket` | the same bytes |
| `overdue` | usage error, exit code 2 | overdue tickets only, earliest due time first |

## 2. Approach summary

A ticket is overdue when it is not closed and the current time is later than its due time.
That rule goes into `ticketdesk/tickets.py` as `Ticket.is_overdue(now)`. A new
`TicketService.overdue()` reads the store's clock once and returns the overdue tickets
sorted by due time. `ticketdesk/cli.py` gains the `overdue` subcommand and one line
formatter that both commands use. For `list`, the CLI asks the service for the overdue
tickets and prints `OVERDUE` in place of the state for each of them.

The store, the SLA table, the log format, the three ticket states, and the replay stay
untouched. The plan stands on two tested assumptions. The service can read the current
time from `store.clock`, and a log with old timestamps makes the CLI testable without a
wait. The main trade-off is that an overdue line no longer shows whether the ticket is
`open` or `assigned`. A second cost is that `list` replays the log twice, which measured
257 ms against 129 ms at 100,000 events.

## 3. Out of scope

- The open TODO under CLI-007. A corrupt log still ends in a traceback with exit code 1,
  and `overdue` inherits that behavior. I measured exit code 1 for both commands.
- A fourth ticket state, a new event kind, or any stored overdue flag.
- A change to the SLA hours, or business-hours logic.
- A due time column, a `list --overdue` filter, color, or notifications.
- A version bump of the package. See open question 7.
- A `.gitignore`. The repo has none, so `make lint` leaves `__pycache__` directories
  untracked. Do not commit them.

## 4. Plan

### Step 0. Gate: get sign-off

Code work starts only after you approve the spec text in step 1 and answer open questions 1
to 4. `docs/guidelines.md:78-80` and `AGENTS.md:93` require that sign-off for every doc
change.

### Step 1. Product specs

Add two items at the end of `docs/product-specs/tickets.md`. These are the next free
numbers after TKT-013.

```
### TKT-014: Overdue tickets

A ticket is overdue when its state is `open` or `assigned` and the current time is later
than its due time. A ticket at exactly its due time is not overdue. A `closed` ticket is
never overdue. Overdue is not a state. The state of an overdue ticket stays as TKT-001
defines it. The current time comes from the store's clock, see INV-005.

### TKT-015: Listing overdue tickets

Listing overdue tickets returns every overdue ticket and no other ticket, sorted by due
time ascending. Tickets with the same due time are sorted by ID ascending.
```

Change three items in `docs/product-specs/cli.md` and `docs/product-specs/event-log.md`.

| Item | Line today | Proposed text |
|---|---|---|
| CLI-001 | `cli.md:14-15` | "takes one of five subcommands. They are `create`, `assign`, `close`, `list`, and `overdue`." |
| CLI-006 | `cli.md:41-43` | "Each line is `#<id> [<priority>] <status> <title>` with the status padded to 8 characters. The status is `OVERDUE` for an overdue ticket, see TKT-014. Otherwise it is the state of the ticket." |
| LOG-001 | `event-log.md:14-15` | "Listing tickets and listing overdue tickets append nothing." |

Add one item at the end of `docs/product-specs/cli.md`. It is the next free number after
CLI-009.

```
### CLI-010: overdue

`ticketdesk overdue` prints one line per overdue ticket in the order of TKT-015. Each line
has the format of CLI-006. With no overdue tickets it prints nothing.
```

### Step 2. Service: `ticketdesk/tickets.py`

Add the rule to `Ticket` after line 21, and the query to `TicketService` after `list()` at
line 47. Nothing else in the file changes. `_tickets()` stays a pure replay.

```python
    def is_overdue(self, now):
        # implements TKT-014
        return self.state != "closed" and now > self.due_at
```

```python
    def overdue(self):
        # implements TKT-015
        now = self.store.clock()
        late = [t for t in self._tickets().values() if t.is_overdue(now)]
        return sorted(late, key=lambda t: (t.due_at, t.id))
```

### Step 3. CLI: `ticketdesk/cli.py`

Add one formatter above `main`, one subparser after line 18, and one branch before the
`else` at line 28. The `else` branch keeps `list` and takes the overdue IDs from the
service.

```python
def _line(t, status):
    return f"#{t.id} [{t.priority}] {status:<8} {t.title}"
```

```python
    sub.add_parser("overdue")
```

```python
        elif args.cmd == "overdue":  # implements CLI-010
            for t in svc.overdue():
                print(_line(t, "OVERDUE"))
        else:  # list, implements CLI-006
            late = {t.id for t in svc.overdue()}
            for t in svc.list():
                print(_line(t, "OVERDUE" if t.id in late else t.state))
```

The explicit `overdue` branch is required. With only the subparser added, `overdue` falls
into the `else` branch and prints the full list. I reproduced that, see assumption A6.

### Step 4. Tests

Add seven cases to `TicketTests` in `tests/test_tickets.py` and create `tests/test_cli.py`
with four cases. Section 7 names every case.

### Step 5. Other docs, after the code lands and with your sign-off

| File and line | Change |
|---|---|
| `AGENTS.md:82` | Add "overdue" to the summary of `tickets.md`. |
| `AGENTS.md:102` | `# 7 unittest cases` becomes `# 18 unittest cases`. |
| `AGENTS.md:106` | Add an `overdue` example line after the `list` example. |
| `AGENTS.md:114-116` | Add `overdue` to "Done". State that CLI tests cover `list` and `overdue` only. |
| `docs/architecture.md:12` | The diagram label becomes `create / assign / close / list / overdue`. |
| `docs/architecture.md:18` | The diagram label becomes `append(event)  /  replay()  /  clock()`. |
| `docs/architecture.md:42-44` | Add one sentence: the service reads the store's clock to decide whether a ticket is overdue. |
| `docs/architecture.md:94-96, 103` | Add `test_cli.py`. Replace "The CLI is not covered by tests today". |
| `docs/guidelines.md:10-11` | "The CLI has no tests today" becomes "The CLI has tests for `list` and `overdue` only". |
| `docs/product-specs/README.md:80, 82` | Add "overdue" to the index text of `tickets.md` and `cli.md`. |

### Step 6. Verify

Run `make lint && make test` and expect 18 passing cases. Then run the end-to-end sequence
in section 7 against a temporary log.

### Step 7. Commit

Make one commit for the feature, its tests, and its docs. Reference TKT-014, TKT-015, and
CLI-010 in the message. The only commit in the repo uses the form `feat(ticketdesk): ...`.

### Specs and invariants the plan touches

| ID | What it requires | Plan step that satisfies it |
|---|---|---|
| INV-001 | No file, cache, or database holds ticket state besides the log. | Step 2 computes overdue on every read and stores nothing. |
| INV-002, LOG-002, LOG-003 | Events are append-only, with three kinds and fixed fields. | No step adds or changes an event. |
| INV-004, LOG-007 | A corrupt line stops the operation. | Step 2 uses the same replay, so `overdue` stops too. |
| INV-005 | The time comes from the store's clock, never from the caller. | Step 2 reads `self.store.clock()`. The CLI passes no time. |
| TKT-001 | The state is one of `open`, `assigned`, `closed`. | Step 2 leaves `state` alone. Step 1 says overdue is not a state. |
| TKT-005 | Due time is creation time plus the hours of the priority. | Step 2 compares against the existing `due_at`. |
| TKT-013 | `list` returns every ticket in ID order. | Step 3 keeps `svc.list()` and its order. |
| LOG-001 | Listing appends nothing. | Step 2 only reads. Step 1 extends the wording. |
| LOG-009 | Replay of the same log yields the same tickets. | Step 2 keeps time out of `_tickets()` and out of `Ticket` fields. |
| CLI-001 | Four subcommands. | **Changes.** Step 1 makes it five. Needs sign-off. |
| CLI-006 | The `list` line shows the state. | **Changes.** Step 1 makes the column a status. Needs sign-off. |
| CLI-007 | Ticket rule errors exit with code 2. | `overdue` raises no ticket rule error. The open TODO stays open. |
| CLI-008 | Success exits with code 0 and an empty stderr. | Step 3. The CLI tests assert both. |
| TKT-014, TKT-015, CLI-010 | New. | Steps 1 to 4. Needs sign-off. |

## 5. Assumptions validated

All experiments ran in a scratch copy of the repo, never in the repo itself. The validated
prototype is in `outputs/scratch/proto` of this run, and its diff is in
`outputs/scratch/proto.diff`.

**The falsifier is not refuted.** Read-time derivation is the wrong shape if overdue has
to exist in the log. That means a fourth state, or an event written at the due time.
TKT-001 fixes three states and LOG-002 fixes three event kinds. `cli.md:3-4` says each
invocation runs one command and exits, so no process exists at the due time to write an
event.

| # | Assumption | Class | Evidence | Result |
|---|---|---|---|---|
| A1 | Every replayed ticket carries its due time. | Verified | `ticketdesk/tickets.py:36`, `ticketdesk/sla.py:6-9` | confirmed |
| A2 | The service can read the current time without the caller supplying it. | Risky | `ticketdesk/store.py:14-16` holds a public `clock`. The prototype calls `self.store.clock()`. `Ran 18 tests in 0.242s OK`. | confirmed |
| A3 | A test can move the fake clock past a due time. | Plausible | `tests/test_tickets.py:8-14` exposes `now`. The prototype tests use `self.store.clock.now += 5 * 3600`. | confirmed |
| A4 | `OVERDUE` fits the 8-character column and other lines keep their bytes. | Plausible | Prototype output: `#1 [P3] OVERDUE  old P3` and `#3 [P2] open     fresh P2`. | confirmed |
| A5 | A subprocess test can make a ticket overdue with no wait. | Risky | A hand-written log with `"at": 1000.0` replays. The test passes from the repo root and from `/`. | confirmed |
| A6 | A subparser without its own branch falls into the `list` branch. | Plausible | With only `sub.add_parser("overdue")` added, `overdue` printed all four tickets, the closed one included. | confirmed |
| A7 | `list` and `overdue` write nothing. | Plausible | The `shasum` of the log was equal before and after. On a missing log: `exit=0 exists=no`. | confirmed |
| A8 | No code in the repo parses the `list` line. | Plausible | `grep` over `tests`, `Makefile`, `.github`, and `pyproject.toml` found only the entry point at `pyproject.toml:8`. | confirmed for the repo |
| A9 | A second replay in one command is acceptable. | Plausible | `create` already replays twice at `tickets.py:59` and `:61`. Measured: 129 ms for one replay, 257 ms for two, at 100,000 events. | confirmed |
| A10 | Nobody else works on this area, and no overdue logic exists yet. | Plausible | One commit, one branch, no stash, no tag. `AGENTS.md:119` records no roadmap. A `grep` for "overdue" over the code found nothing. | confirmed |
| A11 | The new tests detect the change. | Plausible | Against the unchanged code, the 11 new cases failed and the 7 old cases passed. | confirmed |

Three wrong variants of the rule each failed at least one new test.

| Wrong variant | Failing tests |
|---|---|
| Sort by ID | `test_overdue_sorted_by_due_time_not_id`, `test_overdue_lists_only_overdue_oldest_due_first` |
| `now >= due_at` | `test_overdue_boundary_is_strict` |
| Closed tickets count as overdue | `test_closed_ticket_is_never_overdue`, `test_list_marks_overdue_tickets`, `test_overdue_lists_only_overdue_oldest_due_first` |

## 6. Project conventions to follow

- **[`AGENTS.md:19-25`]** Convention: Python 3.11+, `argparse`, `unittest`, no dependencies.
  **Reflected in plan:** steps 2 to 4 use only the standard library.
- **[`Makefile:1-5`, `docs/guidelines.md:12-13`]** Convention: `make lint && make test`
  before every push. **Reflected in plan:** step 6 runs both.
- **[`.github/workflows/ci.yml:10-12`]** Convention: CI runs both targets on Python 3.12.
  **Reflected in plan:** no CI change. Test discovery finds the new test file.
- **[`ticketdesk/store.py:14`, `tests/test_tickets.py:8-20`]** Convention: tests inject a
  fake clock and use no mocking library. **Reflected in plan:** step 4 moves that clock.
- **[`docs/guidelines.md:29-31`]** Convention: name the test files, the cases, and the test
  type up front. **Reflected in plan:** section 7.
- **[`docs/guidelines.md:32-34`]** Convention: a user-visible change names its command
  sequences against a temporary log. **Reflected in plan:** section 7, end-to-end.
- **[`docs/architecture.md:36-38`, `docs/guidelines.md:52-53`]** Convention: the CLI holds
  no ticket rule. **Reflected in plan:** step 2 owns the rule. Step 3 only formats.
- **[`docs/architecture.md:68-69`, `docs/product-specs/invariants.md:36-37`]** Convention:
  time comes from the store's clock. **Reflected in plan:** step 2 reads `store.clock`.
- **[`docs/README.md:25-28`]** Convention: spec IDs are stable and a new spec gets the next
  free number. **Reflected in plan:** step 1 adds TKT-014, TKT-015, and CLI-010.
- **[`docs/README.md:43-44`, `AGENTS.md:97`]** Convention: reference spec IDs in code,
  tests, and commits. **Reflected in plan:** steps 2, 3, 4, and 7.
- **[`docs/guidelines.md:78-80`, `AGENTS.md:93`]** Convention: every doc change needs your
  confirmation. **Reflected in plan:** step 0 gates steps 1 and 5.
- **[`docs/README.md:49-58`]** Convention: a behavior change updates the feature spec.
  **Reflected in plan:** steps 1 and 5 list each edit.
- **[`docs/guidelines.md:84-87`]** Convention: one logical change per commit, with spec
  IDs. **Reflected in plan:** step 7.
- **[`ticketdesk/tickets.py:47`, `tests/test_tickets.py:18-24`]** Pattern to reuse:
  `sorted` with a key, and the `setUp` fixture. **Reflected in plan:** steps 2 and 4.
- **Package manager and build.** They do not constrain the plan. The project has no
  dependencies, and the entry point at `pyproject.toml:8` stays `ticketdesk.cli:main`.
- **Format.** `make lint` is a syntax pass only, see `docs/architecture.md:81`. The new
  code follows the style of the sibling lines.
- **Migrations, ports, URLs, async machinery.** None applies. The change stores no data,
  opens no network, and runs inside one command, see `docs/architecture.md:62-65`.

## 7. Test plan

**Unit, through the service with the fake clock.** Seven new cases go into `TicketTests` in
`tests/test_tickets.py`.

| Case | Covers |
|---|---|
| `test_ticket_is_overdue_after_due_time` | TKT-014. Empty before the due time, listed 5 hours after creation of a `P1`. |
| `test_overdue_boundary_is_strict` | TKT-014. `is_overdue(due_at)` is false, `is_overdue(due_at + 0.001)` is true. |
| `test_closed_ticket_is_never_overdue` | TKT-014. A late ticket leaves the result when it closes. |
| `test_overdue_keeps_the_ticket_state` | TKT-001. A late assigned ticket still has the state `assigned`. |
| `test_overdue_sorted_by_due_time_not_id` | TKT-015, TKT-013. `P3`, `P2`, `P1` created in that order give `[3, 2, 1]`. `list()` stays `[1, 2, 3]`. |
| `test_overdue_appends_nothing` | LOG-001. The log bytes are equal before and after. |
| `test_overdue_on_missing_log` | LOG-006. The result is empty and no file appears. |

The boundary case calls `Ticket.is_overdue` directly. The fake clock adds one second on
every call, so an exact boundary through the service is fragile.

**Subprocess, through the CLI.** Four cases go into the new `tests/test_cli.py`. Each runs
`sys.executable -m ticketdesk.cli --log <temp file>` with the repo root as working
directory. The seed log has three hand-written `created` events with `at` between 1000.0
and 3000.0, one `closed` event, and one ticket created through the CLI.

| Case | Covers |
|---|---|
| `test_list_marks_overdue_tickets` | CLI-006, CLI-008. Exact stdout of four lines: two `OVERDUE`, one `closed`, one `open`. |
| `test_overdue_lists_only_overdue_oldest_due_first` | CLI-010, TKT-015. Exact stdout `#2` then `#1`, exit code 0, empty stderr, equal log bytes. |
| `test_overdue_prints_nothing_without_overdue_tickets` | CLI-010, LOG-006. Missing log and fresh ticket both print nothing with exit code 0. |
| `test_unknown_subcommand_exits_2` | CLI-001. Exit code 2, and the usage text names `overdue`. |

**Integration.** The subprocess cases are the integration layer. The project has no other
component to integrate.

**End-to-end, manual.** Run this sequence from the repo root. The output below is copied
from the prototype run.

```bash
L=$(mktemp -d)/t.jsonl
printf '%s\n' '{"at": 1000.0, "id": 1, "kind": "created", "priority": "P3", "title": "Old P3"}' \
              '{"at": 2000.0, "id": 2, "kind": "created", "priority": "P1", "title": "Old P1"}' > $L
python3 -m ticketdesk.cli --log $L create "Fresh ticket" --priority P1
python3 -m ticketdesk.cli --log $L assign 2 dana
echo "> list"; python3 -m ticketdesk.cli --log $L list
echo "> overdue"; python3 -m ticketdesk.cli --log $L overdue; echo "exit=$?"
python3 -m ticketdesk.cli --log $L close 2 "Replaced the toner cartridge"
echo "> list"; python3 -m ticketdesk.cli --log $L list
echo "> overdue"; python3 -m ticketdesk.cli --log $L overdue; echo "exit=$?"
wc -l < $L
```

```text
#3 open Fresh ticket
#2 assigned -> dana
> list
#1 [P3] OVERDUE  Old P3
#2 [P1] OVERDUE  Old P1
#3 [P1] open     Fresh ticket
> overdue
#2 [P1] OVERDUE  Old P1
#1 [P3] OVERDUE  Old P3
exit=0
#2 closed
> list
#1 [P3] OVERDUE  Old P3
#2 [P1] closed   Old P1
#3 [P1] open     Fresh ticket
> overdue
#1 [P3] OVERDUE  Old P3
exit=0
5
```

The log has 5 lines at the end. Only `create`, `assign`, and `close` appended.

## 8. Risks and mitigations

- **A script outside the repo parses the state column.** It now meets a fourth value. The
  repo holds no such script. Open question 6 asks about the outside.
- **An overdue line hides `open` against `assigned`.** `_line` in `cli.py` is the only
  place that decides the display. A change of mind costs one line and the CLI-006 text.
- **A wrong system clock gives wrong answers with no error.** Overdue depends on the same
  clock that stamps events. The plan adds no defense against it.
- **`list` costs two replays.** That is 257 ms at 100,000 events. If it matters later, one
  service method can return the tickets and the overdue IDs from a single replay.
- **The tie order has no test that can fail.** Replay order already equals ID order, so
  the `t.id` in the sort key is explicit but unproven.
- **The prototype ran on Python 3.15.2 only.** CI uses 3.12 and the package allows 3.11.
  The new code uses a method, an f-string, and `subprocess.run`, so I expect no difference.
- **The CLI tests read the wall clock.** They use timestamps from 1970 and one fresh
  ticket due in 4 hours, so the result is stable.

## 9. Counterfactual

The verdict is **Confirmed**, on the assumptions in open questions 1 to 4. Every success
criterion has a plan step.

| Success criterion | Plan step |
|---|---|
| `list` shows `OVERDUE` for a ticket that is not closed and past its due time. Other lines keep their bytes. | Steps 2 and 3, `test_list_marks_overdue_tickets` |
| `overdue` prints only overdue tickets, earliest due time first, and nothing when none exists. | Steps 2 and 3, the two `overdue` CLI cases |
| Neither command writes to the log. No new state or event kind exists. | Step 2, `test_overdue_appends_nothing`, the CLI byte comparison |
| The rule is in the service, and the time comes from the store's clock. | Step 2 |
| `make lint && make test` pass, and the 7 existing cases pass unchanged. | Steps 4 and 6 |
| The specs describe the new behavior under stable IDs, with your sign-off. | Steps 0, 1, and 5 |

Any of these observations proves the change does not work:

- An overdue ticket prints its plain state in `list`.
- `overdue` prints a closed ticket, or prints tickets in ID order.
- The log grows after `list` or `overdue`.
- `Ticket.state` takes a fourth value.

## 10. Open questions

Nobody was available during planning. Each question carries the assumption the plan
proceeds on.

1. **How does `list` show an overdue ticket?** Assumption: `OVERDUE` replaces the state in
   the same column. The alternative keeps the state and adds a marker, such as
   `#2 [P1] assigned OVERDUE Old P1`. That alternative is ambiguous for a title that starts
   with "OVERDUE".
2. **Is a ticket that closed after its due time overdue?** Assumption: no. A closed ticket
   is never overdue, and it shows `closed`.
3. **Is a ticket overdue at exactly its due time?** Assumption: no. "Pass their due time"
   means the current time is later than the due time.
4. **What does an `overdue` line look like?** Assumption: the same line as `list`, so every
   line reads `OVERDUE`. The alternatives show the real state or the due time instead.
5. **Do you approve the spec text in step 1 and the doc edits in step 5?** Assumption:
   none. This is the gate, and code work waits for it.
6. **Does any script outside the repo parse the output of `list`?** Assumption: no.
7. **Does this feature bump the version from 0.3.0?** Assumption: no. The repo records no
   release rule.
8. **May the service read `store.clock` directly?** Assumption: yes, with the doc line in
   step 5. The alternative is a new `EventStore.now()` method, which touches `store.py`.
9. **Does "oldest due first" mean the earliest due time?** Assumption: yes. Creation order
   differs, because a later `P1` is due before an earlier `P3`.

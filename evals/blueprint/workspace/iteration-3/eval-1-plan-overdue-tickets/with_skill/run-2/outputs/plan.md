# Plan: overdue tickets in `ticketdesk list` and a new `ticketdesk overdue`

## Headline

We derive "overdue" at read time from the replayed due time and the store's clock.
No new event is written.
The `list` command prints `OVERDUE` in the state column for an open or assigned ticket past its due time.
The blocking decision is sign-off on six spec edits, including a change to the `list` output format in CLI-006.

## Approach summary

The service in `ticketdesk/tickets.py` gets the overdue rule, `Ticket.is_overdue(now)`.
It is true when the ticket is not closed and `now` is later than its due time.
The service also gets `now()`, which reads the store's injectable clock, and `overdue(now)`, which returns the overdue tickets sorted by due time, then by ID.
The CLI in `ticketdesk/cli.py` reads `now` once per command and uses one line formatter for both `list` and the new `overdue` subcommand.

The change leaves replay and all write paths alone.
Replay in `TicketService._tickets()`, the store, the SLA table, and the create, assign, and close commands stay unchanged.
Nothing is appended to the log, so INV-001, INV-002, INV-005, and LOG-009 hold without change.

Experiments confirmed that every replayed ticket carries `due_at` and that `OVERDUE` fits the 8-character state column.
The main trade-off is that `OVERDUE` replaces `open` or `assigned` in the `list` output, so a reader of that line loses the underlying state.
We chose that trade-off because it keeps the column count of every line stable for scripts, and it matches the wording "show as OVERDUE".

## Out of scope

- A persisted `overdue` event, a background job, or any notification.
- Business hours, time zones, or any change to the SLA table in `ticketdesk/sla.py`.
- A due time or an assignee column in any output.
- The open TODO under CLI-007. A corrupt log or an unknown priority still escapes as a traceback, and `overdue` inherits that behavior.
- Filters or options on `overdue`, such as by priority or by assignee.
- A version bump in `pyproject.toml`.

## Plan

Step 1 is a gate. Steps 2 to 7 start only after the user signs off on the spec text in step 1.

### Step 1. Spec changes, for sign-off before any code

The process rules require user confirmation for every spec change (`AGENTS.md:93`, `docs/README.md:39`).
The proposed text follows.

| Spec | Change |
|---|---|
| `TKT-014` (new, `docs/product-specs/tickets.md`) | Overdue definition. See the text below. |
| `TKT-015` (new, `docs/product-specs/tickets.md`) | Overdue order. See the text below. |
| `CLI-001` (`docs/product-specs/cli.md:14`) | "one of four subcommands" becomes "one of five", and the list adds `overdue`. |
| `CLI-006` (`docs/product-specs/cli.md:41`) | The state column shows `OVERDUE` instead of the state for an overdue ticket, see TKT-014. |
| `CLI-010` (new, `docs/product-specs/cli.md`) | The `overdue` command. See the text below. |
| `LOG-001` (`docs/product-specs/event-log.md:14`) | "Listing tickets appends nothing" becomes "Listing tickets or overdue tickets appends nothing". |

Proposed text for the new specs:

```markdown
### TKT-014: Overdue tickets

An `open` or `assigned` ticket is overdue when the current time is later than its due time
(TKT-005). A `closed` ticket is never overdue. Overdue is not a state. The state stays one
of the values in TKT-001, and no event records that a ticket became overdue. The current
time comes from the store's clock.

### TKT-015: Overdue order

Listing overdue tickets returns only overdue tickets, sorted by due time ascending. Tickets
with the same due time are sorted by ID ascending.

### CLI-010: overdue

`ticketdesk overdue` prints one line per overdue ticket in the order of TKT-015. Each line
has the format of CLI-006, so the state column reads `OVERDUE`. With no overdue tickets it
prints nothing and exits with code 0.
```

### Step 2. The overdue rule in `ticketdesk/tickets.py`

Add one method to the `Ticket` dataclass and two methods to `TicketService`.
`_tickets()` stays unchanged, so replay stays deterministic per LOG-009 and the write commands read the clock no more often than today.

```python
# on Ticket
def is_overdue(self, now):
    """TKT-014: past the due time and not closed. Derived at read time, never stored."""
    return self.state != "closed" and now > self.due_at

# on TicketService
def now(self):
    """The current time from the store's clock, the same clock that stamps events."""
    return self.store.clock()

def overdue(self, now=None):
    """TKT-014, TKT-015: overdue tickets, oldest due first, ties by ID."""
    now = self.now() if now is None else now
    return sorted((t for t in self._tickets().values() if t.is_overdue(now)),
                  key=lambda t: (t.due_at, t.id))
```

`overdue()` accepts `now` so that the CLI selects and formats the tickets with one clock reading.
INV-005 restricts event timestamps only, and this read writes no event.

### Step 3. The command surface in `ticketdesk/cli.py`

Make these four changes:

- Register the subcommand next to `list` at `cli.py:18` with `sub.add_parser("overdue")`.
- Add a module-level formatter `_line(t, now)` that prints `OVERDUE` when `t.is_overdue(now)` is true, and the state otherwise. Keep the existing `{label:<8}` padding.
- Change the final `else:` branch at `cli.py:28` to `elif args.cmd == "list":`. Read `now = svc.now()` once, then print `_line(t, now)` for each ticket of `svc.list()`.
- Add an `else:` branch for `overdue` that reads `now` once and prints `_line(t, now)` for each ticket of `svc.overdue(now)`.

The rule stays in the service, and the CLI only picks a label (`docs/architecture.md:36-38`).
Errors keep the existing `TicketError` mapping. Cite CLI-006 and CLI-010 in comments.

### Step 4. Service tests in `tests/test_tickets.py`

Add the unit cases listed in the test plan. They use the existing fake `Clock` at `tests/test_tickets.py:8-14`.
Set `self.store.clock.now` to move time. Each clock call adds one second, so set `now` to one second before the target.

### Step 5. CLI tests in a new `tests/test_cli.py`

Add subprocess cases that run `sys.executable -m ticketdesk.cli --log <tmp>` with `cwd` set to the repo root.
The fixture log is written by hand with `at` values near `1_700_000_000`, which is 2023-11-14 UTC.
Those due times are in the past on any test run, so `main()` needs no clock seam.
This file is the first CLI test in the repo (`docs/architecture.md:103`).

### Step 6. Docs that describe the command surface

These edits also need user confirmation (`AGENTS.md:93`):

- `docs/architecture.md:12`: the arrow label "create / assign / close / list" adds `overdue`.
- `docs/architecture.md:68-69`: the time assumption adds that the service reads the store's clock for the current time.
- `docs/architecture.md:103` and `AGENTS.md:116`: the CLI now has tests.
- `AGENTS.md:102`: the test count changes from 7 to the new total.
- `AGENTS.md:103-106`: add an example line for `overdue`.
- `AGENTS.md:114`: the "Done" line adds overdue display and the `overdue` command.

### Step 7. Verify and commit

Run `make lint && make test`, then run the e2e sequence in the test plan.
Make two commits (`docs/guidelines.md:85`). The first holds the signed-off spec and doc text. The second holds the code and tests.
Each commit message cites TKT-014, TKT-015, CLI-006, and CLI-010 (`docs/guidelines.md:87`).

## Assumptions validated

| # | Assumption | Class | Evidence | Result |
|---|---|---|---|---|
| A1 | Every replayed ticket carries a due time. | Verified | `ticketdesk/tickets.py:35-36` sets `t.due_at = due_at(ev["at"], ev["priority"])` on each `created` event. | Confirmed |
| A2 | `OVERDUE` fits the state column and leaves the title in place. | Risky | `scratch/exp1_prototype.py` printed `'OVERDUE '` (7 characters, padded to 8). The prototype `list` lines keep the title at the same column. | Confirmed |
| A3 | The store's clock can serve as "now", and the fake clock can hit the boundary exactly. | Plausible | `scratch/exp2_fake_clock.py`: at `now == due_at` the ticket is not overdue. At `due_at + 1` it is. After close it is not. | Confirmed |
| A4 | A read for overdue appends nothing to the log. | Plausible | `exp1`: the log line count is the same after `list`, `now()`, and the overdue filter. | Confirmed |
| A5 | A subprocess CLI test works with a hand-written log and no clock seam. | Plausible | `exp1`: `python3 -m ticketdesk.cli --log <fixture> list` exited 0 with 5 lines and empty stderr. | Confirmed |
| A6 | Equal due times occur, so the order needs a tie-break. | Plausible | `exp1`: a P1 created 10 hours ago and a P2 created 30 hours ago are both due 6 hours ago. P1 at `a + 20h` equals P2 at `a` by arithmetic. | Confirmed |
| A7 | A missing log gives an empty result and creates no file. | Verified | `ticketdesk/store.py:26-27`. `exp1`: `list` on a missing path printed nothing, exited 0, and created no file. | Confirmed |
| A8 | No `overdue` command exists today. | Verified | `exp1`: `overdue` exited 2 with "invalid choice: 'overdue' (choose from 'create', 'assign', 'close', 'list')". | Confirmed |

The prototype output against a hand-written log, with "now" as the store's clock:

```text
#1 [P1] OVERDUE  old P1 open
#2 [P2] OVERDUE  old P2 assigned
#3 [P3] closed   old P3 closed late
#4 [P3] open     fresh P3
#5 [P3] OVERDUE  very old P3
overdue sorted: [(5, -128.0), (1, -6.0), (2, -6.0)]
```

**Falsifier.** A read-time derivation is the wrong shape if overdue must be a recorded fact.
Either of these requirements would show that:

- The user must know when a ticket became overdue.
- Overdue must survive an edit of the SLA table.

The falsifier did not fire. The request asks only for a display and a listing.
No spec in `docs/product-specs/` asks for overdue history. One side finding came from the check, see the first risk.

**Codebase sweep.**

- In-flight work: the repo has one commit, `d1e901d`, and one branch, `main`. Nobody else works on this area.
- Duplicate logic: no code mentions "overdue". The only time logic is `due_at()` at `ticketdesk/sla.py:6-9`, and the plan reuses it through `Ticket.due_at`.
- Callers of a changed contract: `svc.list()` has one caller, `ticketdesk/cli.py:29`. Its signature does not change. The `list` output line is the changed contract, and no code in the repo parses it.
- Test infrastructure: service tests exist with a fake clock. CLI tests do not exist (`AGENTS.md:116`), so step 5 builds them.

## Project conventions to follow

- **[`AGENTS.md:19-25`, `pyproject.toml:5`]** Convention: *Python 3.11+, standard library only, `argparse`, `unittest`.* **Reflected in plan:** steps 2 to 5 add no dependency and use only `argparse`, `subprocess`, and `unittest`.
- **[`Makefile:2-5`, `.github/workflows/ci.yml:11-12`]** Convention: *`make lint` runs `compileall`, `make test` runs `unittest discover -s tests`.* **Reflected in plan:** step 7 runs both. The new `tests/test_cli.py` sits in `tests/`, so discovery finds it.
- **[`docs/architecture.md:36-38`, `docs/guidelines.md:51-53`]** Convention: *no ticket rule in the CLI.* **Reflected in plan:** step 2 puts the overdue rule and the order in `tickets.py`. Step 3 only picks a label.
- **[`docs/architecture.md:49-50`, `docs/architecture.md:68-69`]** Convention: *time comes from the store's injectable clock.* **Reflected in plan:** step 2 reads "now" through `TicketService.now()`, which calls `store.clock()`.
- **[`tests/test_tickets.py:8-20`]** Convention: *tests inject a fake clock and use no mocking library.* **Reflected in plan:** step 4 reuses `Clock`. Step 5 uses a fixture log, not `unittest.mock`.
- **[`docs/guidelines.md:29-34`]** Convention: *name each test type, and name the e2e command sequences.* **Reflected in plan:** the test plan labels each case as unit or subprocess and lists the e2e commands.
- **[`AGENTS.md:96`, `docs/guidelines.md:87`]** Convention: *cite spec IDs in code comments, tests, and commits.* **Reflected in plan:** steps 2 to 5 and 7 cite TKT-014, TKT-015, CLI-006, and CLI-010.
- **[`AGENTS.md:93`, `docs/README.md:39`]** Convention: *every doc and spec change needs user confirmation.* **Reflected in plan:** step 1 is a gate, and step 6 is listed for the same sign-off.
- **[`docs/guidelines.md:84-86`]** Convention: *one logical change per commit.* **Reflected in plan:** step 7 makes a spec commit and a code commit.
- **[`ticketdesk/cli.py:15-18`]** Convention: *one subparser per line, defined inline in `main()`.* **Reflected in plan:** step 3 adds `overdue` on the same line style.
- **Migrations, ports, URLs, async work.** These do not constrain the plan. The tool has no database, network, or background jobs (`docs/architecture.md:64-65`).
- **Formatter or type checker.** This does not constrain the plan. The repo has none (`docs/architecture.md:81`).

## Test plan

**Unit tests through the service, in `tests/test_tickets.py`:**

- An open P1 ticket at exactly its due time is not overdue. One second later it is (TKT-014).
- An assigned ticket past its due time is overdue (TKT-014).
- A closed ticket past its due time is not overdue, also when it closed late (TKT-014).
- `overdue()` returns tickets by due time, not by ID. Create a P3 ticket, then a P1 ticket. The P1 ticket is due first and comes first (TKT-015).
- Two tickets with the same due time come out in ID order. Create a P2 ticket, move the clock 20 hours, then create a P1 ticket (TKT-015).
- `overdue()` on an empty log returns an empty list.
- `list()` and `overdue()` append no event. The kinds from `replay()` are the same before and after (LOG-001).

**Subprocess tests through the CLI, in `tests/test_cli.py`:**

- `list` on the fixture log prints `OVERDUE` for the past-due open and assigned tickets, `closed` for the closed ticket, and `open` for a ticket created by the test. The exit code is 0 and stderr is empty (CLI-006, CLI-008).
- `overdue` on the same log prints only the overdue lines, oldest due first (CLI-010).
- `overdue` on a missing log prints nothing, exits 0, and creates no file (CLI-010, LOG-006).
- The bytes of the log are the same before and after `list` and `overdue` (LOG-001, INV-002).
- `ticketdesk` with no subcommand exits 2, and the usage names `overdue` (CLI-001).

**E2e sequence against a temporary log, from the repo root:**

```bash
L="$(mktemp -d)/t.jsonl"
python3 -m ticketdesk.cli --log "$L" create "Fresh request" --priority P3      # #1 open Fresh request
printf '%s\n' \
  '{"at": 1700000000.0, "id": 2, "kind": "created", "priority": "P1", "title": "Old outage"}' \
  '{"at": 1699900000.0, "id": 3, "kind": "created", "priority": "P3", "title": "Older request"}' \
  '{"at": 1700000100.0, "id": 3, "kind": "assigned", "assignee": "dana"}' >> "$L"
python3 -m ticketdesk.cli --log "$L" list      # #1 open, #2 OVERDUE, #3 OVERDUE
python3 -m ticketdesk.cli --log "$L" overdue   # #2 (due 1700014400) before #3 (due 1700159200)
python3 -m ticketdesk.cli --log "$L" close 2 "Restarted the mail relay"
python3 -m ticketdesk.cli --log "$L" overdue   # only #3
wc -l "$L"                                     # 5 lines: list and overdue appended nothing
```

**Manual check.** Run `ticketdesk overdue` through the installed entry point (`pyproject.toml:7-8`) once. It confirms that the subcommand is reachable outside `python3 -m`.

## Risks and mitigations

- **The SLA table applies retroactively.** Replay computes each due time from the current `SLA_HOURS` (`ticketdesk/tickets.py:36`). An edit of the table changes which old tickets are overdue. `scratch/exp1_prototype.py` showed this: P3 set to 1 hour made a fresh ticket overdue. This behavior exists today, and overdue makes it visible. Mitigation: open question 7.
- **Scripts that parse `list` may break.** A script that matches `open` or `assigned` in the state column now misses overdue tickets. Mitigation: the column count stays the same, and the spec change in CLI-006 is flagged for sign-off.
- **The machine clock decides overdue.** A wrong system time gives wrong results. The tool already trusts this clock for every event (`docs/architecture.md:68-69`). No mitigation is planned.
- **A corrupt log stops `overdue` with a traceback and exit code 1.** This is the open CLI-007 TODO (`docs/product-specs/cli.md:50-52`). The plan does not make it worse. Mitigation: open question 6.
- **Cost stays the same.** Each command still replays the whole log once and reads the clock once more. No fan-out or new attack surface appears.

## Counterfactual

**Verdict: confirmed with gaps.** Every success criterion has a plan step. The gaps are the format and boundary decisions in the open questions.

| Success criterion | Plan steps | Evidence that would show failure |
|---|---|---|
| An open or assigned ticket past its due time shows `OVERDUE` in `list`. | 2, 3, 4, 5 | A past-due ticket prints its state, or a closed ticket prints `OVERDUE`. |
| `ticketdesk overdue` lists only overdue tickets. | 2, 3, 4, 5 | A ticket that is not overdue appears in its output. |
| `overdue` lists the oldest due first. | 2, 4, 5 | The output follows ID order when due order differs. |
| Nothing else changes: list order, other commands, exit codes, and the log. | 2, 3, 4, 5 | `list` reorders lines, a read appends an event, or `create` output changes. |
| The specs describe the new behavior. | 1, 6 | A merged change with no TKT-014, TKT-015, or CLI-010. |

## Open questions

Nobody is available to answer during this run. Each question states the assumption the plan proceeds on.

1. **Does `OVERDUE` replace the state in `list`, or appear next to it?** Assumption: it replaces `open` or `assigned` in the state column. Keeping both needs a new column on every line.
2. **What does `overdue` print per line?** Assumption: the same line as `list`. A due time or an assignee column would help triage, but it adds time formatting and a time zone choice.
3. **Is a ticket overdue at exactly its due time?** Assumption: no. "Pass their due time" means strictly later.
4. **Can a closed ticket be overdue?** Assumption: no, also when it closed after its due time.
5. **How do tickets with the same due time sort?** Assumption: by ID ascending.
6. **Should the CLI-007 TODO be fixed first?** Assumption: no. `overdue` inherits today's traceback on a corrupt log.
7. **Is the retroactive SLA table acceptable for overdue?** Assumption: yes, because it is today's behavior for due times.
8. **Does this change bump the version from 0.3.0?** Assumption: no. The release owner decides.
9. **Do you approve the spec and doc text in steps 1 and 6?** Assumption for planning: yes, as drafted. Implementation must not start until you confirm.

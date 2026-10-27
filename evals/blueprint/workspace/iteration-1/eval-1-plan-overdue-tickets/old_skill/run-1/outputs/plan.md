# Plan: overdue tickets in `ticketdesk list` and a new `ticketdesk overdue` command

## Headline

Compute "overdue" on the fly in the service layer from the store's clock, mark overdue
lines in `ticketdesk list` with a trailing `OVERDUE`, and add `ticketdesk overdue`, which
prints only overdue tickets sorted by due time. No new event, no new ticket state, no new
file: overdue is a time-dependent view over data the log already holds. One decision
blocks implementation: three spec items (CLI-001, CLI-006, LOG-001) and three new ones
(TKT-014, TKT-015, CLI-010) must change, and this repo requires user sign-off on every
spec edit. The plan proceeds on the assumption that a closed ticket is never overdue.

## Approach summary

A ticket is overdue when it is not closed and the current time is later than its due time.
`Ticket` (in `ticketdesk/tickets.py`) gains a pure method `is_overdue(now)`, and
`TicketService` gains `now()`, which reads the store's injectable clock, and `overdue()`,
which filters `list()` by `is_overdue` and sorts by `(due_at, id)`. The CLI
(`ticketdesk/cli.py`) adds an `overdue` subparser and a one-line formatter shared by `list`
and `overdue`; `list` takes one `now` snapshot and appends ` OVERDUE` to the lines of
tickets that are past due. The store, the SLA table, and the log format stay untouched.

The approach stands on two assumptions, both confirmed by a prototype on a scratch copy:
the service can reach the store's clock (`EventStore.clock`, injected in tests), and
`Ticket.due_at` is already populated on every replay. The main trade-off is where "now"
comes from. Taking it from the store's clock rather than `time.time()` in the CLI keeps
INV-005's principle (time never comes from the caller) and keeps the fake `Clock` in
tests authoritative; the cost is that each `overdue()` call ticks the fake clock by one
second, which tests must set the clock explicitly to absorb. The obvious alternative,
storing an `overdue` flag on `Ticket` during replay, was rejected because it would make
`get()` and `create()` return a time-stamped view and would put a wall-clock-dependent
field on an object that LOG-009 says must be a deterministic function of the log.

## Out of scope

- A fourth ticket state. `overdue` is a derived property; TKT-001's three states stand.
- Recording overdue in the log, or any new event kind (LOG-002 unchanged).
- Showing how late a ticket is, or printing due times. The output keeps the CLI-006 line.
- "Late-closed" reporting (tickets closed after their due time). They are not overdue.
- Business-hours or per-customer SLA (architecture.md:123, future path, untouched).
- Fixing the CLI-007 TODO (unknown priority and corrupt log escape as tracebacks).
  `overdue` inherits the same behaviour on a corrupt log; that conflict is already open.
- Any change to `ticketdesk/store.py`, `ticketdesk/sla.py`, or `ticketdesk/__init__.py`.

## Plan

Steps 1 and 2 are the spec changes and require user confirmation (AGENTS.md:93,
guidelines.md:77-80). Steps 3 onward are code and tests. Suggested commit shape, per
guidelines.md:82-87: one commit for the spec edits, one for code plus tests, both citing
the spec IDs.

1. **`docs/product-specs/tickets.md`**: add two items after TKT-013 (next free numbers,
   never renumber; product-specs/README.md:14-19).
   - `TKT-014: Overdue tickets`. A ticket is overdue when its state is not `closed` and the
     current time is later than its due time (TKT-005). A closed ticket is never overdue.
     A ticket whose due time equals the current time is not yet overdue.
   - `TKT-015: Overdue listing order`. Listing overdue tickets returns only overdue
     tickets, sorted by due time ascending; equal due times are ordered by ID ascending.
   Also extend the file intro (line 3-6) with one sentence that the due time decides when
   a ticket counts as overdue.
2. **`docs/product-specs/cli.md`**, **`docs/product-specs/event-log.md`**, index docs:
   - CLI-001 (cli.md:12-16): "one of four subcommands" becomes five, adding `overdue`.
   - CLI-006 (cli.md:39-43): add "A ticket that is overdue per TKT-014 has ` OVERDUE`
     appended after the title. Other lines are unchanged."
   - New `CLI-010: overdue`. `ticketdesk overdue` prints one line per overdue ticket in the
     CLI-006 format, in TKT-015 order. With no overdue tickets it prints nothing and exits 0.
   - LOG-001 (event-log.md:12-15): "Listing tickets appends nothing" becomes "Listing
     tickets, with `list` or `overdue`, appends nothing."
   - `AGENTS.md:82` and `docs/product-specs/README.md:80`: add "overdue" to the tickets.md
     summary. `AGENTS.md:102`: the test count. `AGENTS.md:114`: add overdue to "Done".
     `docs/architecture.md:12`: the arrow label gains `overdue` (label only, no boundary
     changes, so no architecture change to confirm separately).
3. **`ticketdesk/tickets.py`**:
   - On `Ticket` (after `due_at`, line 21) add
     `def is_overdue(self, now): return self.state != "closed" and now > self.due_at`
     with a `# implements TKT-014` comment. Fields are unchanged, so the positional
     construction at tickets.py:35 is unaffected.
   - On `TicketService` (after `list`, line 47) add `now()` returning `self.store.clock()`
     and `overdue()` returning
     `sorted((t for t in self.list() if t.is_overdue(now)), key=lambda t: (t.due_at, t.id))`
     with `now = self.now()` taken once. Comment `# implements TKT-015`.
4. **`ticketdesk/cli.py`**:
   - Add a module-level helper `_line(t, overdue)` that returns the CLI-006 line plus
     `" OVERDUE"` when `overdue` is true. Replace the inline f-string at cli.py:30 with it,
     so `list` and `overdue` cannot drift apart.
   - After `sub.add_parser("list")` (cli.py:18) add `sub.add_parser("overdue")`.
   - In the dispatch, before the final `else`, add
     `elif args.cmd == "overdue": for t in svc.overdue(): print(_line(t, True))`.
     In the `list` branch take `now = svc.now()` once and print `_line(t, t.is_overdue(now))`.
   - The `TicketError` mapping (cli.py:31-33) is untouched; neither new path raises it.
5. **`tests/test_tickets.py`**: add service-level cases (see test plan), driving time via
   the existing fake `Clock` (tests/test_tickets.py:8-14) by setting `clock.now` directly.
6. **`tests/test_cli.py`** (new, first CLI test in the repo; AGENTS.md:116 records that
   the CLI is untested): subprocess tests for `list` and `overdue` against hand-written
   logs in a temporary directory, using `at: 1` (1970, always overdue) and
   `at: 4102444800` (2100, never overdue) so the result is deterministic without a clock.
7. Run `make lint && make test` (Makefile:2-5). Run the e2e sequences in the test plan by
   hand against a temporary log. Then update the docs listed in step 2 if any wording
   diverged from what landed, again with confirmation.

## Hypothesis and falsifier (recorded)

Hypothesis: overdue is a derived, time-dependent property computed in `tickets.py` from
`Ticket.due_at` and the store's clock, surfaced by `cli.py` as a marker on `list` lines and
a new `overdue` subcommand. Files that change: `ticketdesk/tickets.py`, `ticketdesk/cli.py`,
`tests/`, `docs/product-specs/`.

What would have proved the shape wrong: (a) a requirement to persist overdue (a new event
kind), which would move the change into the store and the log format; (b) a requirement
that overdue be a state in TKT-001, which would change the forward-only state machine;
(c) the service having no access to a clock, which would force `time.time()` into the
CLI against INV-005's principle. None held: the task asks for display and listing only,
TKT-001 lists three states and overdue applies to both `open` and `assigned`, and
`EventStore.clock` is reachable as `self.store.clock` (tickets.py:28, store.py:16).

## Assumptions validated

Prototype: a scratch copy of the repo with the exact changes from steps 3 and 4, plus
three throwaway unit tests and a hand-written six-event log. Results below are from that
run (Python 3.15.1 locally; CI pins 3.12 at .github/workflows/ci.yml:10; nothing here is
version-specific beyond the existing `>=3.11` at pyproject.toml:5).

- **Service reaches the clock.** Verified: `EventStore.__init__` stores `clock` at
  store.py:14-16; `TicketService` keeps `self.store` at tickets.py:28. Prototype:
  `svc.overdue()` returned results driven by the fake clock.
- **`due_at` is set on every replayed ticket.** Verified: tickets.py:36 sets
  `t.due_at = due_at(ev["at"], ev["priority"])` on every `created` event; sla.py:6-9 returns
  a float in epoch seconds, comparable to the clock.
- **The fake `Clock` ticks per call.** Confirmed by experiment: after one `svc.overdue()`
  call `clock.now` advanced by exactly 1 (tests/test_tickets.py:12-14). Tests set
  `clock.now` explicitly rather than counting ticks.
- **Closed tickets must be excluded, or every old closed ticket shows OVERDUE forever.**
  Confirmed by experiment: a ticket created at `at: 3` and closed at `at: 4` was not
  flagged in `list` and absent from `overdue`; a naive `now > due_at` would have flagged it.
- **Ordering by `(due_at, id)` yields oldest due first.** Confirmed: with P3 created
  before P1 and P2, `overdue()` returned `[P1, P2, P3]` once all were past due, and only
  `[P1]` after five hours. Via the CLI, `#2 [P1]` (due at 2 + 4h) printed before `#1 [P3]`
  (due at 1 + 72h).
- **Boundary: `now == due_at` is not overdue.** Confirmed: with the clock set so the call
  returns exactly `due_at`, `overdue()` returned `[]`. Strict `>` is an assumption; see
  open questions.
- **A fifth subparser keeps CLI-001 behaviour.** Confirmed: with `overdue` registered,
  `ticketdesk bogus` and `ticketdesk` (no subcommand) both exit 2 with usage on stderr;
  `required=True` at cli.py:14 is what provides this.
- **`list` and `overdue` append nothing (LOG-001).** Confirmed: the six-line log stayed six
  lines after both commands.
- **Missing log (LOG-006).** Confirmed: `overdue --log /nonexistent/x.jsonl` printed
  nothing and exited 0.
- **Existing tests keep passing.** Confirmed: 7 existing plus 3 prototype tests, all green;
  `make lint` clean.
- **Live flow.** Confirmed: `create "fresh" --priority P1` then `list` printed
  `#1 [P1] open     fresh` with no marker, and `overdue` printed nothing.

## Spec cross-validation

| Spec | Effect | Plan line that satisfies it |
|---|---|---|
| TKT-001 states (tickets.md:15-18) | Must not add a state | Overdue is a method on `Ticket`, not a value of `state` (step 3); out of scope says so |
| TKT-005 due time (tickets.md:36-44) | Reused | `is_overdue` compares against `due_at` from sla.py:6-9 (step 3) |
| TKT-013 listing order (tickets.md:83-85) | Unchanged | `list()` untouched; `overdue()` is a separate method with its own order (step 3, TKT-015) |
| New TKT-014, TKT-015 | Added | Step 1 |
| CLI-001 four subcommands (cli.md:12-16) | **Contradicted**: becomes five | Step 2, needs confirmation |
| CLI-006 line format (cli.md:39-43) | **Contradicted**: overdue lines gain a suffix; other lines unchanged | Step 2, needs confirmation; step 4 `_line` |
| New CLI-010 | Added | Step 2 |
| CLI-007 rule errors (cli.md:45-52) | Unaffected; no new `TicketError` | Step 4 keeps the handler; the open TODO is inherited, not widened |
| CLI-008 success exit (cli.md:54-56) | Holds | Prototype: exit 0, empty stderr |
| CLI-002 log path (cli.md:18-22) | Holds | Same parser, `--log` before the subcommand |
| LOG-001 listing appends nothing (event-log.md:12-15) | Wording extended to `overdue` | Step 2; confirmed by experiment |
| LOG-002, LOG-003 event kinds and fields | Unchanged | Nothing is written (out of scope) |
| LOG-006 missing file (event-log.md:41-44) | Holds | Confirmed by experiment |
| LOG-007 corrupt line (event-log.md:46-50) | Holds; `overdue` stops with the same error | Replay is shared (tickets.py:32) |
| LOG-009 replay is deterministic (event-log.md:56-59) | Holds | No time-dependent field stored on `Ticket`; `is_overdue(now)` takes time as input |
| INV-001 log is the only truth (invariants.md:14-17) | Holds | No cache or file; computed per command |
| INV-002 never edit events (invariants.md:19-22) | Holds | Store untouched |
| INV-004 corrupt data fails fast (invariants.md:29-32) | Holds | Same replay path |
| INV-005 time from the store's clock, never the caller (invariants.md:34-37) | Holds, and its principle is extended to "now" | `TicketService.now()` reads `store.clock()`; the CLI never calls `time.time()` (steps 3-4) |

No invariant is broken. Three spec items change and three are added; all gated on
confirmation (open question 5).

## Architecture cross-validation

- **CLI holds no ticket rules** (architecture.md:34-38): the "closed is never overdue"
  rule and the comparison live in `Ticket.is_overdue`; the sort lives in
  `TicketService.overdue`. The CLI only formats (step 4). No deviation.
- **Service never touches the file; store knows nothing about tickets**
  (architecture.md:40-50): both untouched.
- **SLA helper is a pure lookup** (architecture.md:52-56): untouched; the "Richer SLA"
  migration path (architecture.md:123) still works because `is_overdue` only reads
  `due_at`, however it was computed.
- **Full replay per command** (architecture.md:62-63): `overdue()` calls `list()` once, so
  one replay per invocation; the `list` path also replays once. No N+1.
- **Time is epoch seconds from the store's clock** (architecture.md:68-69): followed.
- **Public names** (architecture.md:89, `ticketdesk/__init__.py`): unchanged.
- Security, observability, async: none applies to a local, single-user CLI with no
  network; errors surface through exit codes as today.

## Project conventions to follow

- **[AGENTS.md:19-25, architecture.md:73-82]** Convention: Python 3.11+, `argparse`,
  `unittest` via `make test`, `compileall` via `make lint`, CI on Python 3.12, zero
  dependencies. → **Reflected in plan:** step 4 uses an `argparse` subparser; steps 5-6 are
  `unittest`; step 7 runs the two make targets; no dependency is added.
- **[Makefile:2-5, README.md:7, guidelines.md:12-13]** Convention: `make test` runs
  `python3 -m unittest discover -s tests -q`; `make lint` runs `compileall`; both before
  every push. → **Reflected in plan:** step 7.
- **[pyproject.toml:1-8, AGENTS.md:25]** Package manager / lockfile: none; no dependencies,
  no lockfile, entry point `ticketdesk = "ticketdesk.cli:main"`. → `Doesn't constrain this
  plan` beyond "add nothing": the plan adds no packages.
- **[tests/test_tickets.py:8-21, architecture.md:49-50]** Test framework and mocking policy:
  `unittest.TestCase`, tests under `tests/`, time controlled by injecting a fake `Clock`
  into `EventStore(clock=...)` (parameter injection, no mocking library). → **Reflected in
  plan:** step 5 reuses `Clock` and sets `clock.now`; step 6 avoids the clock entirely by
  using fixed epoch timestamps in the log.
- **[guidelines.md:29-34]** Convention: name test files, cases, and test type (unit through
  the service or subprocess through the CLI) up front, plus e2e command sequences against
  a temporary log. → **Reflected in plan:** the test plan section below.
- **[guidelines.md:9-11, AGENTS.md:116, architecture.md:103]** Convention: every module
  ships with tests; the CLI has none today and no numeric coverage target is recorded.
  → **Reflected in plan:** step 6 adds the first CLI test for the two commands touched;
  open question 6 asks whether that is wanted now.
- **[AGENTS.md:23, architecture.md:81, architecture.md:113]** Lint: syntax pass only, no
  style or type checker. → `Doesn't constrain this plan` beyond compiling: new files
  must pass `compileall`, which step 7 checks.
- **[architecture.md:78, architecture.md:44]** Migrations: none exist; state is rebuilt by
  replay so rule changes need no migration. → `Doesn't constrain this plan`: no event kind
  or field changes, so even the "no migration" promise is not exercised.
- **[cli.py:8, AGENTS.md:109-110, cli.md:18-22]** Environment: log path from `--log`, then
  `TICKETDESK_LOG`, then `tickets.jsonl`. No ports or URLs. → **Reflected in plan:** the
  e2e sequences and step 6 pass `--log` explicitly so they never touch a real
  `tickets.jsonl`.
- **[architecture.md:60]** Async / concurrency: single writer, no lock, no background
  work. → `Doesn't constrain this plan`: both new paths are read-only.
- **[cli.py:18, cli.py:30, tickets.py:47]** Existing patterns to reuse: `sub.add_parser`
  for subcommands, the `{t.state:<8}` line format, `sorted(..., key=...)` for ordering.
  → **Reflected in plan:** steps 3-4 copy these shapes; `_line` factors the format rather
  than duplicating it.
- **[AGENTS.md:60-61, AGENTS.md:96, docs/README.md:43-44, guidelines.md:87]** Convention:
  cite spec IDs in code comments, tests, commits, and PRs. → **Reflected in plan:** steps
  3-4 carry `# implements TKT-014/TKT-015/CLI-010` comments; test names cite IDs; the
  commit shape above cites them.
- **[AGENTS.md:93, guidelines.md:77-80, docs/README.md:39-42]** Convention: every doc
  change needs user confirmation; no drive-by spec edits. → **Reflected in plan:** steps
  1-2 are gated; open question 5.
- **[docs/README.md:22-28, product-specs/README.md:14-19]** Spec format: one observable
  behaviour per item, next free number, never renumber, no "Testable:" appendix.
  → **Reflected in plan:** TKT-014, TKT-015, CLI-010 are written as behaviour, numbered
  after the current highest (TKT-013, CLI-009).
- **[docs/README.md:51-58]** When to update what: behaviour change → feature spec; new
  spec file → indexes. → **Reflected in plan:** step 2 edits specs and the two index rows;
  no new spec file, so no prefix-table change.
- **[guidelines.md:82-87]** Commits: one logical change each, why over what, spec IDs.
  → **Reflected in plan:** two commits, spec then implementation.

## Codebase sweep

- **In-flight work:** one commit (`229271a`), one branch (`main`), no stash, clean tree.
  Nothing touches this area.
- **Shadow duplication:** `grep -ri overdue` finds nothing in code or docs. The only line
  formatter is cli.py:30; step 4 turns it into `_line` so `list` and `overdue` share it.
- **Caller-side drift:** `TicketService.list()` and the `Ticket` fields keep their
  signatures, so tickets.py:35 and the tests stand. `ticketdesk/__init__.py` exports do
  not change. The only contract that changes is the `list` output line, and only for
  overdue tickets (CLI-006); any external script parsing that output is the risk below.
- **Test infrastructure gap:** no CLI tests and no subprocess helper exist (AGENTS.md:116).
  Step 6 brings up the minimum: `subprocess.run([sys.executable, "-m", "ticketdesk.cli",
  "--log", path, ...])` from the repo root. Deterministic without a clock because the
  hand-written `at` values are decades in the past or future.

## Counterfactual: plan vs success criteria

Success criteria from the problem statement, with the step that satisfies each:

1. `ticketdesk list` marks tickets past their due time with `OVERDUE` → step 4 (`_line`,
   `now` snapshot) plus step 3 (`is_overdue`). Confirmed by prototype.
2. `ticketdesk overdue` prints only overdue tickets, oldest due first → step 3
   (`overdue()` sort key) plus step 4 (subparser). Confirmed by prototype.
3. Non-overdue lines of `list` are byte-identical to today → step 4 appends only when
   overdue. Confirmed by prototype (`#1 [P1] open     fresh`).
4. Neither command writes to the log, and replay stays deterministic → nothing is
   appended or stored (steps 3-4). Confirmed by prototype.
5. Existing tests and lint stay green; new logic has tests → steps 5-7. Confirmed by
   prototype for the existing suite; new tests named below.
6. Specs describe the new behaviour → steps 1-2. **Gap:** requires confirmation that
   nobody can give in this run.

What would prove the change does not work: a closed ticket shown `OVERDUE`; an open P1
ticket older than four hours not flagged; `overdue` output not in due order; a
non-overdue `list` line that differs from today; a seventh line appearing in the log after
`list` or `overdue`; any of the 7 existing tests failing.

Verdict: **Confirmed with gaps.** Gaps: (a) the spec edits in steps 1-2 await sign-off;
(b) the overdue definition (closed excluded, strict `>`) is an assumption until confirmed.
Both are listed under open questions.

## Test plan

Unit, through the service with the fake `Clock` (`tests/test_tickets.py`, new cases in
`TicketTests`):

- `test_overdue_after_due_time_TKT014`: create P1; set `clock.now` to `due_at + 1`;
  `overdue()` returns it and `is_overdue(now)` is true.
- `test_not_overdue_before_or_at_due_time_TKT014`: create P1; set the clock so the next
  call returns exactly `due_at`; `overdue()` is empty (boundary).
- `test_closed_ticket_never_overdue_TKT014`: create P1, close it, move the clock a week
  ahead; `overdue()` is empty and `is_overdue(now)` is false.
- `test_assigned_ticket_can_be_overdue_TKT014`: create P2, assign it, advance 25 hours;
  listed.
- `test_overdue_sorted_by_due_then_id_TKT015`: create P3, P1, P2 in that order; advance
  past all; `overdue()` is `[P1, P2, P3]`. Then two P1 tickets created one tick apart;
  order is by ID.
- `test_overdue_appends_nothing_LOG001`: event kinds before and after `overdue()` are
  identical.
- `test_list_unchanged_TKT013`: `list()` still returns every ticket by ID regardless of
  the clock.

Subprocess, through the CLI (`tests/test_cli.py`, new; `sys.executable -m ticketdesk.cli`
with `cwd` at the repo root and `--log` pointing into a `TemporaryDirectory`):

- `test_list_marks_overdue_CLI006`: log with `at: 1` P3 and `at: 4102444800` P1; stdout
  is exactly `#1 [P3] open     a OVERDUE` and `#2 [P1] open     b`; exit 0; empty stderr.
- `test_overdue_lists_oldest_due_first_CLI010`: log with P3 at `at: 1`, P1 at `at: 2`,
  P1 at `at: 3` closed at `at: 4`; stdout is `#2` then `#1`; `#3` absent.
- `test_overdue_empty_prints_nothing_CLI010`: missing log file; empty stdout; exit 0.
- `test_unknown_subcommand_still_exits_2_CLI001`: `bogus` exits 2 with usage on stderr.

End-to-end command sequences (guidelines.md:32-34), run by hand against a temporary log:

```
L=$(mktemp -d)/t.jsonl
python3 -m ticketdesk.cli --log "$L" create "Printer on fire" --priority P1
python3 -m ticketdesk.cli --log "$L" create "Wobbly desk" --priority P3
python3 -m ticketdesk.cli --log "$L" assign 1 dana
python3 -m ticketdesk.cli --log "$L" list        # no OVERDUE markers yet
python3 -m ticketdesk.cli --log "$L" overdue     # prints nothing
# edit nothing; instead seed a second log with past timestamps:
printf '%s\n' '{"at": 1, "id": 1, "kind": "created", "priority": "P3", "title": "old slow"}' \
  '{"at": 2, "id": 2, "kind": "created", "priority": "P1", "title": "old fast"}' \
  '{"at": 3, "id": 3, "kind": "created", "priority": "P1", "title": "old closed"}' \
  '{"at": 4, "id": 3, "kind": "closed", "resolution": "Replaced the toner cartridge"}' > "$L.old"
python3 -m ticketdesk.cli --log "$L.old" list    # #1 and #2 end with OVERDUE, #3 does not
python3 -m ticketdesk.cli --log "$L.old" overdue # #2 then #1
wc -l "$L.old"                                   # still 4
```

Expected output of the last three commands was produced by the prototype and is recorded
under "Assumptions validated".

## Risks and mitigations

- **Scripts that parse `list` output.** Overdue lines gain a suffix. Mitigation: only
  overdue lines change, the suffix is last, and CLI-006 documents it. If a fixed column is
  preferred, see open question 3; it is a one-line change in `_line`.
- **Titles containing the word OVERDUE** confuse a `grep`. Mitigation: `ticketdesk
  overdue` is the authoritative filter; grep is not.
- **Fake clock ticks on `now()`.** A future test that counts clock calls or compares
  timestamps across an `overdue()` call will be off by one second. Mitigation: the new
  tests set `clock.now` explicitly; note it in a comment next to `now()`.
- **Machine clock skew.** Overdue depends on the host clock being roughly right; a wrong
  clock flags wrongly. No mitigation planned; it is the same clock that stamps events.
- **The CLI-007 TODO widens in practice.** A corrupt log makes `overdue` traceback like
  every other command. Not new, but a fourth command now shows it. Mitigation: none here;
  the TODO stays open and is referenced in the PR.
- **Spec sign-off arrives with a different overdue definition** (for instance, closed-late
  tickets count). Mitigation: the rule is one expression in `Ticket.is_overdue`; the sort
  and the CLI do not change.

## Open questions

Each question states the assumption the plan proceeds on.

1. **Is a closed ticket ever overdue?** Assumed no: overdue means "still needs work and is
   past due". Closing after the due time is a separate "late" fact that this change does
   not report. If closed-late tickets should appear, `is_overdue` needs the close time,
   which replay does not currently keep on `Ticket` (it would come from the `closed`
   event's `at`).
2. **Is a ticket due exactly now overdue?** Assumed no (strict `now > due_at`), reading
   "pass their due time" literally. Float timestamps make the equal case rare.
3. **Where does the marker go in `list`?** Assumed a trailing ` OVERDUE` after the title,
   because non-overdue lines then stay byte-identical and the spec edit is one sentence.
   Alternatives: an aligned column between state and title (prettier, changes every
   line), or replacing the state column (rejected: it hides `open` versus `assigned`
   and contradicts TKT-001).
4. **Should `overdue` show due times or lateness?** Assumed no; same line format as
   `list`, including the `OVERDUE` suffix for consistency even though it is redundant
   there.
5. **Spec edits.** CLI-001, CLI-006, LOG-001 change; TKT-014, TKT-015, CLI-010 are added;
   AGENTS.md and the spec index rows gain a word. All need confirmation before step 1.
6. **First CLI test.** The repo has none (AGENTS.md:116). Assumed yes, add
   `tests/test_cli.py` for the two commands touched, because guidelines.md:9 says every
   module ships with tests. If not wanted now, the e2e sequences above cover the wiring
   by hand.
7. **Tie-break for equal due times.** Assumed ID ascending, matching TKT-013's convention.
8. **Commit shape.** Assumed two commits (spec, then code plus tests). One combined commit
   is also defensible since the spec edit is not "unrelated cleanup".

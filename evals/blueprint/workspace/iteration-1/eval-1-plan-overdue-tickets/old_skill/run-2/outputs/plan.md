# Plan: overdue tickets in `ticketdesk list` and a new `ticketdesk overdue` command

Date: 2026-10-27. Repo at `main` (`13237e6`), working tree clean. Nothing in the repo was
modified while producing this plan; every experiment ran on scratchpad copies.

## Headline

Compute "overdue" at read time in the service (`TicketService`) from the store's clock,
never store it: a ticket is overdue when it is not closed and the current time is past
its due time. `list` keeps its line format and inserts the word `OVERDUE` before the
title only on overdue lines; `overdue` reuses the same line and sorts by due time. A
throwaway prototype of exactly this passed the existing 7 tests plus 1 new CLI test.
**Blocker: three specs (CLI-001, CLI-006, LOG-001) must be amended and two added
(TKT-014/015, CLI-010), and this repo requires user confirmation for every doc change,
so the spec step cannot land without a sign-off.** Nobody was available during this run;
the assumptions I proceeded on are listed under Open questions.

## Approach summary

The change touches three of the four modules and adds nothing to the log. The service
derives every ticket by replaying events and already reconstructs `due_at` on replay
(`ticketdesk/tickets.py:36`), so overdue-ness is a pure function of a ticket and "now".
The service reads "now" once per derivation from the store's injectable clock, which is
the only source of time the architecture allows (INV-005, `docs/architecture.md:68-69`);
that keeps the fake `Clock` in the tests in control of overdue-ness. `Ticket` gains an
`overdue: bool` that the service stamps on every ticket it hands out, and the service
gains `overdue()` returning the overdue tickets sorted by `(due_at, id)`. The CLI gains
an `overdue` subparser, makes its current catch-all `else` branch (which today means
`list`) explicit, and prints `OVERDUE ` before the title when the flag is set. The store
grows a one-line `now()` so the service's dependency on the store's clock is an explicit
seam rather than an attribute poke.

Two assumptions carry the whole approach: that closed tickets are never overdue (the
obvious product reading, but not stated anywhere), and that "past due" is strict, so a
ticket is not overdue at the exact second it is due. The main trade-off is the `list`
line: adding a conditional marker keeps every non-overdue line byte-identical to today's
output and keeps the `state` column honest (`OVERDUE` is not a fourth state, see
TKT-001), at the cost of a ragged title column when some lines carry the marker. A new
state was rejected because states are forward-only and event-sourced, and overdue-ness
is neither an event nor irreversible.

## Out of scope

- Fixing the CLI-007 TODO (unknown priority and corrupt log escape as tracebacks). The
  new command inherits that behaviour unchanged.
- Any `--as-of`/`--now` override, due-time column, colour, or relative-time display.
- Notifications, SLA reports, business-hours SLA (`docs/architecture.md:123`).
- Persisting overdue-ness or adding an event kind. INV-001/INV-002 and LOG-002 stay as is.
- Changing `list` ordering (TKT-013) or the non-overdue `list` line.
- A coverage target for the CLI (`docs/guidelines.md:10-11` TODO) beyond the tests below.

## Plan

Steps 1 and 7 are documentation and are gated on user confirmation
(`AGENTS.md:93`, `docs/guidelines.md:78-80`). Step 1 should be confirmed before code is
merged; code and tests can be written in parallel.

### 1. Amend and add product specs (needs confirmation)

`docs/product-specs/tickets.md` — append after TKT-013:

- **TKT-014: Overdue tickets.** A ticket is overdue when its state is `open` or
  `assigned` and the current time is later than its due time (TKT-005). A `closed`
  ticket is never overdue. Overdue is derived from the current time when a command runs;
  it is not recorded in the log and it changes as time passes.
- **TKT-015: Overdue listing order.** Listing overdue tickets returns only overdue
  tickets, sorted by due time ascending, then by ID ascending for equal due times.

`docs/product-specs/cli.md`:

- **CLI-001**: "one of four subcommands" → five; add `overdue` to the list.
- **CLI-006**: each line is `#<id> [<priority>] <state> <title>`, state padded to 8; an
  overdue ticket (TKT-014) has `OVERDUE ` inserted between the state and the title:
  `#<id> [<priority>] <state> OVERDUE <title>`. Other lines are unchanged.
- **CLI-010: overdue.** `ticketdesk overdue` prints one line per overdue ticket in the
  order of TKT-015, in the format of CLI-006 (every line carries `OVERDUE`). With no
  overdue tickets, or no log file, it prints nothing and exits 0.

`docs/product-specs/event-log.md`:

- **LOG-001**: "Listing tickets appends nothing" → "Listing tickets, including listing
  overdue tickets, appends nothing."

### 2. `ticketdesk/store.py` — expose the clock as a seam

Add `def now(self): return self.clock()` on `EventStore` and have `append()` use it
(`store.py:20`). Behaviour unchanged; this names the store as the time authority.

### 3. `ticketdesk/tickets.py` — the rule lives in the service

- `Ticket`: add `overdue: bool = False` after `due_at` (`tickets.py:21`); the default keeps
  the positional construction at `tickets.py:35` valid.
- `_tickets()`: after the replay loop and before `return tickets` (`tickets.py:44`), read
  `now = self.store.now()` once and set
  `t.overdue = t.state != "closed" and now > t.due_at` for every ticket. Comment
  `# implements TKT-014`.
- Add `def overdue(self)` returning
  `sorted((t for t in self._tickets().values() if t.overdue), key=lambda t: (t.due_at, t.id))`,
  comment `# implements TKT-015`.
- `list()` and `get()` unchanged; both now return tickets carrying the flag.

### 4. `ticketdesk/cli.py` — parse, format, nothing else

- `cli.py:18`: add `sub.add_parser("overdue")` next to `list`.
- `cli.py:28-30`: replace the catch-all `else` with an explicit branch:
  `for t in svc.list() if args.cmd == "list" else svc.overdue():` and print
  `f"#{t.id} [{t.priority}] {t.state:<8} {'OVERDUE ' if t.overdue else ''}{t.title}"`.
  One formatter serves both commands (`# implements CLI-006, CLI-010`). The CLI never
  reads a clock and holds no rule, so `docs/architecture.md:36-38` is respected.

### 5. `tests/test_tickets.py` — unit tests through the fake clock

Use the existing `Clock` (`tests/test_tickets.py:8-14`); move time with
`self.store.clock.now = <absolute>` or `+= <seconds>`, never by counting ticks (the
clock advances by 1 on every read, and step 3 adds reads). Cases:

- `test_new_ticket_is_not_overdue` (TKT-014)
- `test_ticket_is_overdue_after_due_time` (TKT-014): create P1, `clock.now += 5 * 3600`,
  `list()[0].overdue` is True and `get()` agrees.
- `test_overdue_boundary_is_strict` (TKT-014): `clock.now = t.due_at - 1` so the next
  read is exactly `due_at` → not overdue; one more second → overdue.
- `test_closed_ticket_is_never_overdue` (TKT-014).
- `test_overdue_sorted_by_due_time_then_id` (TKT-015): create P3 then P1, advance 80 h,
  expect `[P1.id, P3.id]` (reverse of ID order), and `list()` still ID-ascending (TKT-013).
- `test_overdue_listing_appends_nothing` (LOG-001): event kinds identical before and after
  `list()` and `overdue()`.

### 6. `tests/test_cli.py` — new file, subprocess through the CLI

The CLI uses `time.time`, so tests make a ticket overdue by writing a log by hand with an
ancient `at` (`1.0`), the pattern `tests/test_store.py:12` already uses, and always pass
`--log` so `TICKETDESK_LOG` cannot leak in. Run with
`[sys.executable, "-m", "ticketdesk.cli", "--log", path, ...]`; verified to run under
`make test` discovery (prototype: 8 tests OK). Cases:

- `test_list_marks_overdue_tickets` (CLI-006): old P3 line and fresh P1 via `create`;
  expect `#1 [P3] open     OVERDUE old P3` and `#2 [P1] open     fresh` byte-exact.
- `test_overdue_lists_only_overdue_oldest_due_first` (CLI-010, TKT-015): old P3 (`at` 1),
  old P1 (`at` 2), fresh P1; expect exactly two lines, P1 first.
- `test_overdue_excludes_closed` (TKT-014): old ticket with a `closed` event is absent.
- `test_overdue_with_missing_log_prints_nothing` (CLI-010, LOG-006): exit 0, empty
  stdout and stderr, file not created.
- `test_overdue_appends_nothing` (LOG-001): line count of the log unchanged.
- `test_unknown_subcommand_is_usage_error` (CLI-001): exit 2, usage on stderr.

### 7. Doc touch-ups (needs confirmation)

- `AGENTS.md:84` cli summary, `AGENTS.md:82` tickets summary (add "overdue"),
  `AGENTS.md:102` "7 unittest cases" → new count, `AGENTS.md:106` add an `overdue`
  example, `AGENTS.md:114-116` current state ("Not covered by tests: the CLI" is no
  longer true).
- `docs/architecture.md:12` diagram label `create / assign / close / list / overdue`;
  `docs/architecture.md:49-50` store section: it also answers "now" for the service;
  `docs/architecture.md:94-96, 103` test layout and "CLI is not covered by tests".
- `docs/guidelines.md:10-11` TODO: the CLI now has tests (target still unrecorded).
- `docs/product-specs/README.md:80, 82` index summaries.
- `README.md`: unchanged (summary, not a spec).

### 8. Verify and commit

`make lint && make test` (`AGENTS.md:88-89`). E2e against a temp log (guidelines step 5):

```
L=/tmp/td.jsonl; rm -f $L
printf '%s\n' '{"at": 1.0, "id": 1, "kind": "created", "priority": "P3", "title": "Ancient"}' > $L
python3 -m ticketdesk.cli --log $L create "Fresh" --priority P1   # #2 open Fresh
python3 -m ticketdesk.cli --log $L list       # #1 ... OVERDUE Ancient / #2 ... Fresh
python3 -m ticketdesk.cli --log $L overdue    # #1 [P3] open     OVERDUE Ancient
python3 -m ticketdesk.cli --log $L close 1 "Replaced the toner cartridge"
python3 -m ticketdesk.cli --log $L overdue    # prints nothing, exit 0
wc -l $L                                      # 3 lines: list/overdue appended nothing
```

Two commits (`docs/guidelines.md:82-87`): `docs(specs): Add TKT-014/015 and CLI-010 for
overdue tickets` (step 1 + 7), then `feat(tickets): Flag overdue tickets and add the
overdue command (TKT-014, TKT-015, CLI-006, CLI-010)` (steps 2-6).

## Hypothesis and its falsifier

Hypothesis: overdue is a read-time derivation over `(state, due_at, store clock)`; files
that change are `tickets.py`, `cli.py`, `store.py` (one line), two test files, and the
specs. What would have proven the shape wrong: `due_at` not being reconstructable on
replay (it is, `tickets.py:36`); the clock not being reachable from the service without
a second time source (it is, `store.py:16` public attribute; prototype used it); or the
requirement needing a user-supplied "now" or a persisted overdue flag (the task asks for
neither, and INV-001/LOG-001 forbid the latter). None fired.

## Assumptions validated

All evidence from `HEAD` files or from the prototype in
`/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/overdue-exp/proto`.

- **`due_at` is rebuilt on replay and nothing else computes it** — confirmed:
  `tickets.py:36`; grep for `due_at` finds only `sla.py:6`, `tickets.py:3,21,36,58`.
- **The service can reach the store's clock** — confirmed: `store.py:14-16` stores the
  injected callable as public `self.clock`; tests inject `Clock()` at
  `tests/test_tickets.py:20`.
- **Extra clock reads in `_tickets()` do not break existing tests** — confirmed by
  experiment: the test `Clock` advances 1 s per read; prototype runs 7/7 OK. Only
  `test_create_sets_due_by_priority` touches timestamps and it asserts a difference
  (`tests/test_tickets.py:29`).
- **`Ticket` can gain a defaulted field without touching callers** — confirmed:
  dataclass with defaults at `tickets.py:18-21`; sole constructor call `tickets.py:35`.
- **argparse accepts a fifth subparser and the current `else` branch is the `list`
  path** — confirmed: `cli.py:14-18, 28-30`; before the change `ticketdesk overdue`
  exits 2 with `invalid choice: 'overdue'`; after, the prototype runs it.
- **Strict comparison and closed-exclusion behave as intended** — confirmed by
  experiment: at `now == due_at` → not overdue; `+1 s` → overdue; closed ticket past due
  → `overdue == False`.
- **Due order differs from ID order so the sort is real** — confirmed: P3 (id 1) then P1
  (id 2) → `overdue()` returns `[2, 1]` with `due_at` 1700014405 < 1700259202.
- **Listing appends nothing; missing log stays missing** — confirmed: log line count 4
  before and after `list`/`overdue`; `overdue` on a nonexistent path exits 0, prints
  nothing, creates no file (LOG-006).
- **A subprocess CLI test runs under `make test`** — confirmed: `tests/test_cli.py`
  prototype discovered and passed (8 tests), cwd is the repo root so `-m ticketdesk.cli`
  resolves.
- **Toolchain** — confirmed: `make lint && make test` green on the untouched copy;
  `Makefile:3,5` use real tabs; local Python is 3.15.1, CI runs 3.12
  (`.github/workflows/ci.yml:10`), `pyproject.toml:5` requires ≥3.11; nothing
  version-specific is used.

## Spec cross-validation

| Spec | Effect | Plan line |
|---|---|---|
| TKT-001 states | `OVERDUE` is a derived flag, not a state; `state` column still shows `open`/`assigned`. Satisfied. | Step 3, 4 |
| TKT-005 due time | Reused unchanged. Satisfied. | Step 3 |
| TKT-013 list order | `list` still ID-ascending. Satisfied; `overdue` gets its own order in new TKT-015. | Step 3, 5 |
| TKT-014/015 (new) | Define overdue and its order. | Step 1 |
| CLI-001 four commands | **Contradicted** by a fifth subcommand → amend. | Step 1 |
| CLI-002 log path | `overdue` honours `--log`/env/default via the shared parser. Satisfied. | Step 4 |
| CLI-006 list line | **Contradicted** by the marker → amend; non-overdue lines unchanged. | Step 1, 4 |
| CLI-007 rule errors | No new ticket errors; traceback TODO unchanged. Out of scope. | — |
| CLI-008 success exit | `overdue` exits 0, empty stderr (experiment). Satisfied. | Step 6 |
| CLI-010 (new) | `overdue` command. | Step 1 |
| LOG-001 listing appends nothing | Holds for `overdue` (experiment); wording extended. | Step 1, 5, 6 |
| LOG-002/003 kinds and fields | No new kind or field. Satisfied. | — |
| LOG-006 missing file | `overdue` prints nothing, creates nothing (experiment). Satisfied. | Step 6 |
| LOG-009 deterministic replay | States, assignees, resolutions, due times unchanged; overdue is time-derived and TKT-014 says so explicitly. Satisfied. | Step 1 |
| INV-001 single source of truth | Nothing stored outside the log. Satisfied. | Step 3 |
| INV-002 never edit | No writes at all. Satisfied. | — |
| INV-004 fail fast | Replay path untouched. Satisfied. | — |
| INV-005 time from the store's clock | Service uses `store.now()`, CLI never touches time. Satisfied. | Step 2, 3 |

## Architecture cross-validation

- Boundaries (`docs/architecture.md:34-56`): rule in the service, formatting in the CLI,
  file access only in the store. The service's new call to `store.now()` is a read-only
  use of the store's existing clock; `architecture.md:49-50` already names the store as
  the clock holder. Call-out: this is a slight widening of the store's role ("stamps
  events" → "is the time authority"); recorded in step 7, not silent.
- Scalability (`architecture.md:62-63`): `overdue` is one full replay plus an O(n)
  filter and sort, same cost class as `list`. `create()` already replays twice; the extra
  clock read is negligible.
- Security, observability, async: not applicable to a local single-tenant CLI
  (`architecture.md:64-65`).

## Project conventions to follow

- **[`AGENTS.md:88-89`, `docs/guidelines.md:12-13`]** Convention: `make lint && make test`
  before every push; CI runs the same. → **Reflected in plan:** step 8.
- **[`AGENTS.md:93`, `docs/README.md:39`, `docs/guidelines.md:78-80`]** Convention: no doc
  or spec change without user confirmation. → **Reflected in plan:** steps 1 and 7 are
  marked "needs confirmation"; headline names it as the blocker.
- **[`AGENTS.md:96`, `docs/README.md:43-44`, `docs/guidelines.md:87`]** Convention: cite
  spec IDs in code, tests, commits. → **Reflected in plan:** steps 3, 4 comments; step 5,
  6 case names; step 8 commit subjects.
- **[`AGENTS.md:25`, `pyproject.toml:1-8`]** Package manager / dependencies: none,
  stdlib only, no lockfile. → **Reflected in plan:** nothing added; `argparse`,
  `subprocess`, `unittest` only.
- **[`Makefile:2-5`]** Build/test entry points: `make test` = `unittest discover -s
  tests -q`, `make lint` = `compileall`. → **Reflected in plan:** new tests go under
  `tests/` as `test_*.py` so discovery finds them (step 6 verified).
- **[`AGENTS.md:22`, `tests/test_tickets.py:8-20`, `docs/guidelines.md:29-31`]** Test
  framework: `unittest`; no mocking library, the fake clock is injected through
  `EventStore(clock=...)`; the test type must be named (unit through the service,
  subprocess through the CLI). → **Reflected in plan:** steps 5 and 6.
- **[`docs/architecture.md:81`, `docs/guidelines.md:7`]** Lint: syntax pass only, no
  style checker. → **Reflected in plan:** follow the file's own style (compact parser
  lines `cli.py:15-18`, f-strings); nothing else to configure.
- **Migrations / schema:** `Doesn't constrain this plan` — the log format (LOG-002/003)
  gains no kind or field; replay rebuilds everything (`architecture.md:78`).
- **[`cli.py:8,13`, CLI-002]** Environment: `TICKETDESK_LOG` and `--log`; no ports or
  URLs. → **Reflected in plan:** CLI tests always pass `--log`.
- **Async / background machinery:** `Doesn't constrain this plan` — one process, one
  command per invocation (`docs/architecture.md:60`).
- **[`tests/test_store.py:12`, `cli.py:29-30`, `tickets.py:18-21`]** Existing patterns to
  reuse: hand-written log lines in tests, the single `list` print line, defaulted
  dataclass fields. → **Reflected in plan:** steps 3, 4, 6.
- **[`docs/README.md:45,47`, `docs/guidelines.md:82-87`, `git log`]** Docs use absolute
  dates and lead with the important part; one logical change per commit; the existing
  commit uses `type(scope): subject`. → **Reflected in plan:** this document's header;
  step 8 commit split.

## Codebase sweep

- In-flight work: single commit `13237e6`, clean tree, no branches besides `main`. None.
- Shadow duplication: `due_at` logic exists only in `sla.py:6` and `tickets.py:36`; the
  `list` line is formatted in exactly one place (`cli.py:30`). The plan extends both
  rather than branching.
- Caller-side drift: `Ticket` gains a defaulted field (constructor at `tickets.py:35`
  unaffected); `TicketService.list()`/`get()` signatures unchanged; `__init__.py` exports
  unchanged. The one hidden coupling is `cli.py:28`'s `else` meaning `list`, which step 4
  removes. argparse's usage string now lists `overdue`; nothing in the repo matches the
  old string.
- Test infrastructure: no CLI tests exist (`AGENTS.md:116`, `architecture.md:103`);
  step 6 brings them up, verified to run under discovery.

## Counterfactual: success criteria vs plan

| Success criterion (from the task) | Plan step | Status |
|---|---|---|
| `list` shows tickets past due as `OVERDUE` | 3, 4; tests 5, 6 | Confirmed |
| `overdue` lists only overdue tickets | 3, 4; tests 5, 6 | Confirmed |
| Oldest due first | 3 (`(due_at, id)` key); tests 5, 6 | Confirmed |
| Existing behaviour unchanged (non-overdue lines, ordering, exit codes, log untouched) | 3, 4; tests 5, 6; experiment | Confirmed |
| Invariants and architecture respected | sections above | Confirmed |
| Specs reflect the behaviour | 1, 7 | Confirmed with gaps: needs user sign-off, and TKT-014's closed-ticket and strict-boundary wording encode assumptions (Open questions 1, 2) |

Overall: **Confirmed with gaps**; the gaps are decisions, not missing work.

## Test plan

- **Unit (`tests/test_tickets.py`, through `TicketService` with the fake clock):** the six
  cases in step 5. They cover the rule (TKT-014), the boundary, closed exclusion, the
  order (TKT-015), the unchanged `list` order (TKT-013), and LOG-001.
- **CLI (`tests/test_cli.py`, subprocess):** the six cases in step 6. They cover the exact
  line format (CLI-006), the new command (CLI-010), the empty and missing-log cases
  (LOG-006), exit codes (CLI-001, CLI-008), and that nothing is appended.
- **E2e (manual, step 8):** the command sequence against a temp log, including closing
  the overdue ticket and seeing it leave `overdue`.
- **Regression:** the existing 7 tests, unchanged.

## Risks and mitigations

- **Title starting with the word `OVERDUE`** is ambiguous to a text parser of `list`
  output. Mitigation: CLI-006 states the format precisely; if machine parsing matters,
  Open question 3 offers an always-present column instead.
- **Wall-clock dependence.** A wrong system clock, or a log copied from a machine in a
  different epoch of time, mislabels tickets. No mitigation in scope; TKT-014 makes the
  dependence explicit.
- **Tick-counting tests.** The fake clock advances on every read and step 3 adds reads;
  a future test that asserts an exact `at` value would be brittle. Mitigation: step 5
  sets `clock.now` to absolute values and the plan says so.
- **Spec sign-off never arrives.** Code without the spec change contradicts CLI-001 and
  CLI-006 and the repo's process. Mitigation: step 1 gates the merge.
- **Local Python 3.15 vs CI 3.12.** Nothing version-specific is used; CI is the arbiter.
- **Subprocess tests are slower** (~60 ms for one; the suite stays well under a second).

## Open questions

Assumptions I proceeded on are stated with each; the plan and tests encode them.

1. **Are closed tickets ever overdue?** Assumed no: overdue means still open or assigned
   and past due. If "closed late" should show, TKT-014 and the `state != "closed"` test
   change, and the `closed` row in `overdue` needs a definition.
2. **Is "past due" strict?** Assumed `now > due_at`; at the exact due second a ticket is
   not yet overdue.
3. **Where does the marker go in the `list` line?** Assumed `OVERDUE ` inserted between
   the state and the title, only on overdue lines, so other lines stay byte-identical.
   Alternatives: an always-present 8-wide column (aligned titles, every line changes), a
   trailing ` OVERDUE` (aligned, less visible), or replacing the state column (loses
   `open`/`assigned`).
4. **Does `overdue` repeat the marker?** Assumed yes: one formatter, and the output is
   self-describing when piped. Dropping it saves 8 characters per line.
5. **Tie-break for equal due times?** Assumed ID ascending.
6. **`EventStore.now()` or read `store.clock` directly?** Assumed the method, as an
   explicit seam. The attribute read is the smaller diff.
7. **Spec IDs and wording** for TKT-014, TKT-015, CLI-010 and the amendments to CLI-001,
   CLI-006, LOG-001, plus the doc touch-ups in step 7, all need your confirmation.
8. **Should the CLI-007 traceback TODO be picked up now** since the CLI is getting tests?
   Assumed no; it is a separate decision the spec already asks for.

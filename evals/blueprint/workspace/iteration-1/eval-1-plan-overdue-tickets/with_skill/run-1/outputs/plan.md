# Plan: overdue tickets in `list` and a new `overdue` subcommand

Date: 2026-10-27. Repo: `ticketdesk` at commit `13237e6`. Status: ready to implement once the open questions at the end are confirmed.

## Headline

Overdue becomes a derived flag that the service computes from each ticket's due time and the store's clock. `list` prints `OVERDUE` in the state column for such tickets, and a new `overdue` subcommand prints only them, earliest due first. Nothing is written to the log, and no ticket state is added. The one blocker is a set of five spec edits that this repo requires a person to confirm. They are CLI-001, CLI-006, and the new TKT-014, TKT-015, and CLI-010.

## Approach summary

The change touches two modules. `ticketdesk/tickets.py` gains an `overdue` field on `Ticket` and a `TicketService.overdue()` method that filters and sorts. Its `_tickets()` replay reads the store's clock once to set the flag on every ticket. `ticketdesk/cli.py` gains the `overdue` subparser and prints `OVERDUE` instead of the state when the flag is set. The store, the SLA table, and the log format stay untouched.

The approach stands on two verified facts, the due time on every ticket and the clock on the store. First, every ticket already carries `due_at` as epoch seconds. Second, the store exposes the injectable clock that INV-005 names as the only time source, so the CLI passes no time. The trade-off is that `OVERDUE` replaces the state label in `list`, so an overdue ticket no longer shows whether it is `open` or `assigned`. I chose that over an extra column because it keeps the CLI-006 line at four fields and the same width. The task wording also asks for the ticket to "show as OVERDUE".

A prototype of this exact shape passes the existing 7 tests and every command probe listed under Assumptions validated.

## Out of scope

- Fixing the CLI-007 TODO. An unknown priority or a corrupt log line still escapes as a traceback with exit 1, for `overdue` as for every other command.
- A due-time or age column in any output. The task asks for the flag and the order, not the amount of lateness.
- Business hours, per-customer targets, or any change to `sla.py`.
- A persisted overdue event, a snapshot, or any cache. Overdue is recomputed on every command.
- A version bump in `pyproject.toml`. See open question 7.
- Backfilling tests for the existing `create`, `assign`, and `close` CLI paths. The new `tests/test_cli.py` covers `list` and `overdue` only.

## Plan

Steps 2 to 4 are code and tests and can be implemented as one commit. Step 5 is doc edits that the repo requires a person to confirm, so it is a second commit in the same PR.

### Step 1. Confirm the open questions

Get an answer to open questions 1 to 5, or an explicit "proceed on the stated assumptions". AGENTS.md line 93 and `docs/guidelines.md` lines 77 to 80 forbid silent spec edits, and this change needs five of them.

### Step 2. Service: the overdue rule in `ticketdesk/tickets.py`

- Add `overdue: bool = False` as the last field of the `Ticket` dataclass, after `due_at` on line 21. Comment it with `# derived, see TKT-014`.
- In `_tickets()` (lines 30 to 44), read `now = self.store.clock()` once before the replay loop. After the loop, set `t.overdue = t.state != "closed" and now > t.due_at` for every ticket. One read per replay keeps every ticket in one call consistent with one instant.
- Add `overdue()` after `list()` on line 47. It returns `sorted((t for t in self._tickets().values() if t.overdue), key=lambda t: (t.due_at, t.id))`. Comment it with `# implements TKT-015`.
- `list()`, `get()`, `create()`, `assign()`, and `close()` do not change.

### Step 3. CLI: the label and the subcommand in `ticketdesk/cli.py`

- After `sub.add_parser("list")` on line 18, add `sub.add_parser("overdue")`. It takes no arguments.
- Replace the bare `else:` branch on lines 28 to 30 with two explicit branches, `elif args.cmd == "list":` and `elif args.cmd == "overdue":`. Both iterate the matching service method and print through one shared line formatter.
- The formatter prints `f"#{t.id} [{t.priority}] {label:<8} {t.title}"` with `label = "OVERDUE" if t.overdue else t.state`. The width stays 8, which fits both `assigned` and `OVERDUE`. Comment it with `# CLI-006, CLI-010`.
- The `TicketError` handler and the exit codes do not change.

### Step 4. Tests

Add these cases to `tests/test_tickets.py`, unit tests through the service with the existing `Clock` fake from lines 8 to 14. The fake advances one second per read, so each case sets `clock.now` directly instead of counting reads. One case needs two tickets with the same due time, which the advancing fake cannot produce. That case uses a fixed clock that returns a settable value without advancing.

| Case | Spec | Expectation |
|------|------|-------------|
| `test_new_ticket_is_not_overdue` | TKT-014 | After `create`, `overdue` is `False` and `overdue()` is empty. |
| `test_ticket_past_due_is_overdue` | TKT-014 | Move the clock to due time plus 1 second. `list()` shows the flag and `overdue()` returns the ticket. |
| `test_due_time_itself_is_not_overdue` | TKT-014 | With the clock read landing exactly on `due_at`, the flag is `False`. |
| `test_closed_ticket_is_never_overdue` | TKT-014 | Past due, then `close`. The flag is `False` and `overdue()` is empty. |
| `test_overdue_sorted_by_due_time_then_id` | TKT-015 | A `P3` created before a `P1`, both past due, returns the `P1` first. Two tickets with equal due time return in ID order. |
| `test_overdue_appends_nothing` | LOG-001 | The replayed event list is the same length before and after `overdue()`. |

Create `tests/test_cli.py`, the first CLI test file. It calls `ticketdesk.cli.main(argv)` in process with `--log` pointing at a temporary file and captures stdout with `contextlib.redirect_stdout`. A ticket is made overdue by writing a `created` line with `"at": 1` by hand, the pattern `tests/test_store.py` line 12 already uses. A not-yet-due ticket is created through the CLI, which stamps the real time.

| Case | Spec | Expectation |
|------|------|-------------|
| `test_list_marks_overdue_ticket` | CLI-006 | Output line is `#1 [P1] OVERDUE  old` with the label padded to 8. |
| `test_list_keeps_state_for_other_tickets` | CLI-006 | A fresh ticket prints `open    ` and a closed one prints `closed  `. |
| `test_overdue_lists_only_overdue_oldest_due_first` | CLI-010, TKT-015 | Seed `P3` at 1 and `P1` at 100, create a fresh ticket. Output is the `P1` line then the `P3` line. |
| `test_overdue_on_missing_log_prints_nothing` | CLI-010, LOG-006 | Exit 0, empty stdout, and the file is not created. |
| `test_overdue_rejects_arguments` | CLI-001 | `overdue extra` raises `SystemExit` with code 2. |
| `test_list_and_overdue_do_not_write` | LOG-001 | The log bytes are identical before and after both commands. |

### Step 5. Docs, each edit pending confirmation

- `docs/product-specs/tickets.md`: append TKT-014 and TKT-015 with the wording under open question 5. Add "overdue" to the intro sentence on line 4.
- `docs/product-specs/cli.md`: CLI-001 says five subcommands and names `overdue`. CLI-006 defines the label. Append CLI-010 for `overdue`.
- `docs/product-specs/event-log.md`: LOG-001 line 14 adds "Listing overdue tickets appends nothing."
- `docs/product-specs/README.md` line 80 and `AGENTS.md` line 82: add "overdue" to the tickets.md summary.
- `AGENTS.md`: line 102 updates the test count, lines 100 to 107 add an `overdue` example, line 114 adds `overdue` to the done list.
- `AGENTS.md` line 116 and `docs/guidelines.md` line 11: drop or narrow "the CLI has no tests".
- `docs/architecture.md`: line 12 adds `overdue` to the arrow label, line 95 adds `test_cli.py`, line 103 narrows the "not covered" sentence.

### Step 6. Verify

Run `make lint && make test` from the repo root. Then run the end-to-end sequence under Test plan against a temporary log.

## Assumptions validated

All experiments ran on a clone of the fixture repo at `13237e6` in the scratchpad, never in the repo itself. The prototype diff was 11 insertions and 2 deletions across the two modules.

- **A1, confirmed.** The service can read the store's clock. `ticketdesk/store.py` line 14 declares `clock=time.time` and line 16 stores it as `self.clock`. `tests/test_tickets.py` line 20 injects a fake through the same parameter.
- **A2, confirmed.** Every ticket carries `due_at` in epoch seconds comparable with the clock. `ticketdesk/tickets.py` line 36 sets it from `sla.due_at`, which returns `created_at + hours * 3600` (`ticketdesk/sla.py` line 9). `created_at` is the store's `at` stamp (`store.py` line 20).
- **A3, confirmed by experiment.** Reading the clock inside `_tickets()` does not break the existing suite. With the prototype applied, `make lint && make test` reported `Ran 7 tests ... OK`. The fake clock now advances 1 second per `list()` and 3 per `create()`, previously 2. No existing assertion depends on absolute values.
- **A4, confirmed by experiment.** Adding a fifth subparser keeps the usage behaviour of CLI-001. On `HEAD`, `ticketdesk overdue` prints `invalid choice: 'overdue'` and exits 2. With the prototype, `ticketdesk overdue extra` prints `unrecognized arguments: extra` and exits 2.
- **A5, confirmed by experiment.** Sorting by `(due_at, id)` gives earliest due first across priorities. A seeded log with a `P3` created at `at: 1` and a `P1` created at `at: 100` printed the `P1` line first from `overdue`, while `list` kept ID order.
- **A6, confirmed by experiment.** Closed tickets are excluded and the boundary is strict. With the fake clock, a `P1` flipped to overdue at due time plus 1 second. It stayed not overdue with the read landing exactly on `due_at`, and dropped out of `overdue()` after `close`.
- **A7, confirmed by experiment.** Neither command writes. The seeded log had 6 lines before and after `list` and `overdue`. `overdue` on a missing log printed nothing, exited 0, and did not create the file.
- **A8, confirmed.** A hand-written log line with an old `at` is a legitimate way to make a ticket overdue in a test. `tests/test_store.py` line 12 writes a line by hand, and `docs/architecture.md` lines 66 and 67 state that replay trusts the events in the file.
- **A9, confirmed by experiment.** The CLI-007 tracebacks are unchanged by this work. With the prototype, `create x --priority P9` still exited 1.

## Problem statement, hypothesis, and counterfactual

The goal is an `OVERDUE` label in `ticketdesk list` and a new `ticketdesk overdue` subcommand. A ticket past its due time shows as `OVERDUE` in the list, and `overdue` lists only such tickets with the earliest due time first. The constraints come from the repo's own docs. No ticket rule may live in the CLI, time comes only from the store's clock, listing appends nothing, and the log is the only state. The non-goals are listed under Out of scope.

The change does not work if a past-due ticket prints its state in `list`. It also fails if `overdue` includes a closed ticket or orders by ID. It fails if the log grows after a listing, or if any of the 7 existing tests fail.

The hypothesis is that overdue is a derived view computed in `TicketService` from `due_at` and `store.clock()`. A requirement to record overdue, as an event or a state, would make this the wrong shape. So would a service that cannot obtain time without the caller. LOG-001 and INV-001 rule out the first, and `store.py` line 16 rules out the second.

Alternatives I rejected:

- Compute overdue in the CLI from `t.due_at` and `time.time()`. That is a ticket rule in the CLI, which `docs/architecture.md` lines 36 to 38 forbid, and time from the caller, which INV-005 forbids.
- Give `list()` and `overdue()` a `now` parameter that the CLI supplies. Same INV-005 objection. A `now=None` variant that falls back to the store clock would work, but it adds a second time source for no caller that needs it.
- Set the flag only in `list()` and `overdue()`, leaving `_tickets()` time-free. Then `get()` returns tickets with a stale default flag, and two kinds of `Ticket` object circulate.
- Append an `overdue` event from some scheduler. There is no scheduler, LOG-001 forbids an event for a non-change, and the flag would go stale.

Counterfactual, success criteria against plan steps: **Confirmed with gaps.**

| Criterion | Plan step | Evidence |
|-----------|-----------|----------|
| `list` shows `OVERDUE` for past-due open or assigned tickets | Steps 2 and 3 | A5 probe output |
| `overdue` lists only overdue tickets, earliest due first | Steps 2 and 3 | A5 probe output |
| Closed tickets are never overdue | Step 2 | A6, pending open question 1 |
| No event, no new state, invariants hold | Step 2 | A7 |
| Existing behaviour unchanged | Steps 2 and 3 | A3, A4, A9 |
| Tests ship with the code | Step 4 | Cases named above |
| Specs and docs match the behaviour | Step 5 | Gap: needs confirmation |

The gaps are the doc confirmations and the product choices in open questions 1 to 4. None changes the code shape.

## Spec cross-validation

- **INV-001, upheld.** The flag is recomputed from the log and the clock on every command. No file or cache holds it. Step 2.
- **INV-002, upheld.** No line is edited. A7.
- **INV-003, not touched.** No ID logic changes.
- **INV-004, upheld.** `_tickets()` still calls `replay()`, which raises on a corrupt line before any flag is set. A9 shows the exit code is unchanged.
- **INV-005, upheld.** The service reads `store.clock()`. The CLI passes no time. This is the reason for the design in Step 2.
- **TKT-001, needs a spec note.** `OVERDUE` is a label, not a fourth state. The ticket stays `open` or `assigned`, and `assign` and `close` behave as before. TKT-014 under open question 5 says so explicitly to avoid a contradiction.
- **TKT-005, upheld.** The comparison uses the due time this spec defines.
- **TKT-013, upheld.** `list` keeps ID order. A5.
- **LOG-001, upheld and extended.** Listing overdue tickets appends nothing. A7. Wording under Step 5.
- **LOG-006, upheld.** `overdue` on a missing log prints nothing and creates no file. A7.
- **LOG-009, upheld.** Replay still yields the same states, assignees, resolutions, and due times. The overdue flag depends on the clock, and TKT-014 states that.
- **CLI-001, spec change.** Four subcommands become five.
- **CLI-006, spec change.** The third field becomes a label that is `OVERDUE` or the state.
- **CLI-007, upheld.** `overdue` raises no ticket-rule error. The TODO stays open.
- **CLI-008, upheld.** Both listings exit 0 with nothing on stderr. A7.
- **CLI-009, not touched.** `overdue` takes no ID.
- **CLI-010, new.** Wording under open question 5.

## Architecture cross-validation

- **Boundaries.** The rule lives in the service and the formatting in the CLI, as `docs/architecture.md` lines 34 to 44 require. The store is not changed. No new layer, module, or dependency.
- **Time.** `docs/architecture.md` lines 49 to 50 and 68 to 69 name the store's clock as the single time source. Step 2 follows that. Reading a public attribute of the store from the service widens the service-to-store contract. It goes from "append and replay" to "append, replay, and clock". I call it out here so it is not silent.
- **Scalability.** One extra linear pass per replay. `docs/architecture.md` lines 62 to 63 already accept a full replay per command.
- **Security and observability.** No input beyond the existing subcommand name. No new error path. Nothing to log.
- **Async.** None. One command per invocation.
- **Future interfaces.** A long-lived front end that holds `Ticket` objects would see a stale flag. `docs/architecture.md` line 121 plans such a front end, so TKT-014's "as of the command" wording matters there.

## Project conventions to follow

- **[`AGENTS.md:86-96`]** Convention: *lint and test before every push, validate assumptions, doc changes need confirmation, surface conflicts, reference spec IDs everywhere.* **Reflected in plan:** Step 6 runs both. Assumptions validated carries the evidence. Steps 1 and 5 gate the doc edits. Steps 2 to 4 put IDs in comments and test names.
- **Per-component conventions.** None exist. The repo has one `AGENTS.md` at the root and no per-directory docs. Doesn't constrain this plan beyond the root rules.
- **[`pyproject.toml:1-8`, `AGENTS.md:25`]** Convention: *no dependencies, standard library only.* **Reflected in plan:** no package is added. `contextlib` and `tempfile` in the new tests are standard library.
- **[`Makefile:2-5`, `AGENTS.md:100-107`]** Convention: *`make test` runs `unittest discover -s tests -q`, `make lint` runs `compileall`, the CLI runs as `python3 -m ticketdesk.cli --log <path> <cmd>`.* **Reflected in plan:** Step 6 and the e2e sequence use exactly these.
- **[`Makefile:3`, `tests/test_tickets.py:8-21`, `docs/architecture.md:49-50`]** Convention: *`unittest` with discovery under `tests/`, time controlled by injecting a clock into `EventStore`, no monkeypatching.* **Reflected in plan:** Step 4 names `tests/test_cli.py` for discovery, and every service test moves time through the injected clock. No numeric coverage target exists (`docs/guidelines.md:10-11`).
- **[`Makefile:4-5`, `docs/architecture.md:81`]** Convention: *lint is a syntax pass only, no style or type checker.* **Reflected in plan:** no style tool to satisfy. Step 6 runs it anyway.
- **Migration tooling.** Doesn't constrain this plan. The repo has no schema and no migrations (`docs/architecture.md:78`), and the new field is derived, not stored.
- **[`ticketdesk/cli.py:8,13`, `docs/product-specs/cli.md` CLI-002]** Convention: *the log path comes from `--log`, then `TICKETDESK_LOG`, then `tickets.jsonl`.* **Reflected in plan:** every test and e2e command passes `--log` explicitly so the environment cannot leak in.
- **Async machinery.** Doesn't constrain this plan. One command per invocation, nothing retryable.
- **[`tests/test_store.py:12`, `ticketdesk/tickets.py:47`, `ticketdesk/cli.py:30`]** Patterns to reuse: *a hand-written log line in a test, `sorted(..., key=)` for ordering, one f-string per output line.* **Reflected in plan:** Step 4 seeds logs the same way, Step 2 sorts the same way, Step 3 keeps one formatter.
- **[`docs/guidelines.md:82-87`]** Convention: *one logical change per commit, reference spec IDs.* **Reflected in plan:** code plus tests in one commit, docs in a second, both citing TKT-014, TKT-015, CLI-010.

## Codebase sweep

- **In-flight work.** One commit on one branch, no stashes. Nothing touches this area.
- **Shadow duplication.** `grep` for `overdue`, `clock`, `now`, `due_at`, and `sort` finds no existing overdue logic and one sort site, `tickets.py` line 47. Nothing to consolidate.
- **Caller-side drift.** No signature changes. `Ticket` gains a defaulted field, so positional construction on `tickets.py` line 35 is unaffected. `__init__.py` exports need no change.
- **Test infrastructure.** Service tests and the fake clock exist. CLI tests do not exist at all (`AGENTS.md:116`, `docs/architecture.md:103`). Step 4 brings up the first CLI test file, scoped to the two changed commands.

## Test plan

- **Unit, service.** The six cases in Step 4 for `tests/test_tickets.py`. They cover the rule, the boundary, the closed exclusion, the order, and the no-write guarantee.
- **Unit, CLI in process.** The six cases in Step 4 for `tests/test_cli.py`. They cover the label, the padding, the filter and order, the missing log, the argument rejection, and the no-write guarantee.
- **End to end, manual.** Against a temporary log, with the repo root as the working directory:

```bash
LOG=$(mktemp -d)/t.jsonl
printf '%s\n' \
  '{"at": 1, "id": 1, "kind": "created", "priority": "P3", "title": "old P3"}' \
  '{"at": 100, "id": 2, "kind": "created", "priority": "P1", "title": "old P1"}' > "$LOG"
python3 -m ticketdesk.cli --log "$LOG" create "fresh" --priority P1   # #3 open fresh
python3 -m ticketdesk.cli --log "$LOG" list       # #1 OVERDUE, #2 OVERDUE, #3 open, in ID order
python3 -m ticketdesk.cli --log "$LOG" overdue    # #2 then #1
python3 -m ticketdesk.cli --log "$LOG" close 1 "Replaced the toner cartridge"
python3 -m ticketdesk.cli --log "$LOG" overdue    # #2 only
python3 -m ticketdesk.cli --log "$LOG" overdue extra; echo "exit=$?"   # usage on stderr, exit=2
wc -l "$LOG"                                      # 4 lines: two seeded, one create, one close
```

- **Regression.** `make lint && make test` must report 7 plus 12 cases passing.

## Risks and mitigations

- **A script that parses field 3 of `list` as a state will now see `OVERDUE`.** The field count and width are unchanged, and the CLI-006 edit makes the label explicit. Open question 3 offers an extra column instead if any such script matters.
- **Wrong wall clock on the machine gives wrong flags.** The whole product already stamps events from the same clock, so this is not new. No mitigation in scope.
- **The fake clock advances on every service call, so a test that counts reads will drift.** Step 4 sets `clock.now` directly in every case and uses a non-advancing clock for the tie case.
- **A future long-lived interface holds a stale flag.** TKT-014 states that overdue is as of the command. A later change can add a method that recomputes from a given time.
- **Local Python is 3.15 and CI is 3.12.** The change uses no feature newer than the `X | None` syntax already in the file. Step 6 runs on whatever is local, and CI confirms on 3.12.

## Open questions

Nobody was available during this run. Each question states the assumption the plan proceeds on.

1. **Is a closed ticket ever overdue?** Assumption: no. A closed ticket is done, even if it closed late. If the team wants a "closed late" view, that is a new feature, not this one.
2. **Is a ticket overdue at exactly its due time?** Assumption: no. Overdue means strictly later than the due time. The task says "pass their due time".
3. **Does `OVERDUE` replace the state in `list`, or sit beside it?** Assumption: it replaces the state in the same 8-wide column. The alternative is a fifth field between state and title, which widens every line and changes CLI-006 for all tickets.
4. **Does `overdue` use the same line format as `list`?** Assumption: yes, so every line reads `OVERDUE`. A due-time column would be more useful but needs a time format decision and is out of scope here.
5. **Spec wording to confirm.** The plan proceeds on these texts.
   - TKT-014, Overdue tickets: "A ticket is overdue when its state is `open` or `assigned` and the command runs later than its due time, see TKT-005. A `closed` ticket is never overdue. Overdue is not a state, see TKT-001. It is derived at the time of each command and appends no event."
   - TKT-015, Overdue listing order: "Listing overdue tickets returns every overdue ticket sorted by due time ascending. Tickets with the same due time are sorted by ID ascending."
   - CLI-001: "takes one of five subcommands. They are `create`, `assign`, `close`, `list`, and `overdue`."
   - CLI-006: "Each line is `#<id> [<priority>] <label> <title>` with the label padded to 8 characters. The label is `OVERDUE` for an overdue ticket, see TKT-014, and the state otherwise."
   - CLI-010, overdue: "`ticketdesk overdue` prints one line per overdue ticket, in the order of TKT-015 and the format of CLI-006. With no overdue tickets it prints nothing. It appends nothing to the log, see LOG-001."
   - LOG-001: append "Listing overdue tickets appends nothing."
6. **Should the first CLI tests run in process or as a subprocess?** `docs/guidelines.md` line 31 says "subprocess through the CLI". Assumption: in process through `main(argv)`, which is the entry point `pyproject.toml` line 8 declares. It keeps `make test` fast and needs no interpreter path. A subprocess variant is a mechanical swap if the team prefers it.
7. **Bump the version to 0.4.0?** Assumption: no. The docs mention 0.3.0 in `AGENTS.md` line 10 and `pyproject.toml` line 3, and a bump is a release decision.

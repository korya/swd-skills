# Plan: overdue tickets in `ticketdesk`

## Headline

The ticket service gets a read-time overdue rule, `ticketdesk list` shows `OVERDUE` in the state column, and `ticketdesk overdue` lists overdue tickets by due time.
The rule compares the existing due time with the store clock, so the log, the replay, and the three ticket states stay unchanged.
Code work waits for one decision: the user must approve four spec edits and the choice that `OVERDUE` replaces the word `open` or `assigned`.

## Approach summary

Overdue is a fact that we compute when a command runs. It is not a new state and not a new event. A ticket is overdue when it is `open` or `assigned` and the current time is later than its due time. The service already computes the due time on replay (`ticketdesk/tickets.py:36`), so the rule needs one comparison and one source for the current time.

The rule lives in `ticketdesk/tickets.py`, because the architecture keeps every ticket rule out of the CLI. The service reads the current time from the clock that the store already holds (`ticketdesk/store.py:14-16`). Tests can then control time with the fake clock that they already inject. The service gets one new query, `overdue()`, which sorts by due time and then by ID. The CLI reads the clock once per command and prints `OVERDUE` in the 8-character state column of an overdue ticket. The `overdue` subcommand prints the same line format, so each of its lines also appears in `list`.

The approach stands on two facts, and experiments confirmed both. First, a replayed ticket always carries a due time in epoch seconds. Second, the store clock can be read without an append.

The main trade-off is in the `list` output. When the state column shows `OVERDUE`, the reader no longer sees whether the ticket is `open` or `assigned`. We accept this loss because the request says "show as OVERDUE" and the line keeps its width. A separate marker column is the fallback if the user wants both words.

## Out of scope

- No `overdue` event, notification, or escalation. The log format and LOG-002 stay as they are.
- No new ticket state. TKT-001 keeps `open`, `assigned`, and `closed`.
- No display of the due time or of how late a ticket is. This avoids time-zone formatting decisions.
- No fix for the open TODO under CLI-007. An unknown priority or a corrupt log still escapes as a traceback, also in `overdue`.
- No change to the SLA table, business hours, or per-customer targets.
- No `list --overdue` flag. The request asks for a subcommand.
- No version bump of `pyproject.toml`. The release process is not documented in the repo.

## Plan

Each step names the files and the change. Steps 1 to 3 start only after the user approves step 0.

### Step 0: spec edits, gated on user approval

The repo forbids silent spec changes (`AGENTS.md:93`, `docs/README.md:39`). Propose this text to the user and commit it on its own, with the spec IDs in the message.

`docs/product-specs/tickets.md`, two new items after TKT-013:

```
### TKT-014: Overdue tickets

A ticket is overdue when its state is `open` or `assigned` and the current time is later
than its due time, see TKT-005. A ticket at exactly its due time is not overdue. A `closed`
ticket is never overdue. Overdue is not a state. Checking whether a ticket is overdue
appends no event.

### TKT-015: Overdue listing order

Listing overdue tickets returns every overdue ticket and no other ticket. The oldest due
time comes first. Tickets with the same due time are sorted by ID ascending.
```

`docs/product-specs/cli.md`:

- CLI-001: change "one of four subcommands" to five, and add `overdue` to the names.
- CLI-006: the third field becomes a label. The label is `OVERDUE` for an overdue ticket, see TKT-014, and the state otherwise. The padding stays at 8 characters.
- New CLI-010:

```
### CLI-010: overdue

`ticketdesk overdue` prints one line per overdue ticket in the order of TKT-015. Each line
has the format of CLI-006. With no overdue tickets it prints nothing and exits with code 0.
```

`docs/product-specs/event-log.md`, LOG-001: change "Listing tickets appends nothing." to "Listing tickets, all or only the overdue ones, appends nothing."

### Step 1: the overdue rule in the service

File: `ticketdesk/tickets.py`.

- Add `Ticket.is_overdue(now)`. It returns `self.state != "closed" and now > self.due_at`. Cite TKT-014 in a comment.
- Change the constructor to `TicketService(store, clock=None)`. It sets `self.clock = clock if clock is not None else store.clock`. Both current callers (`ticketdesk/cli.py:20`, `tests/test_tickets.py:21`) keep working unchanged.
- Add `TicketService.now()`, which returns `self.clock()`.
- Add `TicketService.overdue(now=None)`. It filters `_tickets()` with `is_overdue(now)` and sorts by `(t.due_at, t.id)`. Cite TKT-015.
- Leave `_tickets()` untouched. Replay stays free of the current time, so LOG-009 keeps its meaning.

### Step 2: the CLI

File: `ticketdesk/cli.py`.

- Add a helper `_line(t, now)`. It prints `OVERDUE` when `t.is_overdue(now)` is true and the state otherwise, padded to 8 characters.
- Change the catch-all `else:` at `ticketdesk/cli.py:28` to `elif args.cmd == "list":`. Without this change, `overdue` falls into the `list` branch and prints every ticket. The drift probe in the evidence section shows this.
- Add `sub.add_parser("overdue")` and a branch that prints `_line(t, now)` for each ticket of `svc.overdue(now)`.
- In both branches, read `now = svc.now()` once before the loop. Every line of one command then uses the same time.

### Step 3: tests

- Extend `tests/test_tickets.py` with the service cases in the test plan below. Reuse the `Clock` class at `tests/test_tickets.py:8-14`.
- Add `tests/test_cli.py`. It runs `sys.executable -m ticketdesk.cli --log <tmp> ...` as a subprocess with the repo root as the working directory. It writes the log by hand with past `at` values, as `tests/test_store.py:12` already does.

### Step 4: follow-up doc edits, also gated on user approval

- `AGENTS.md:102`: update the test count. Today it reads "7 unittest cases".
- `AGENTS.md:114` and `AGENTS.md:116`: add `overdue` to the done list. Remove "the CLI" from the list of code without tests.
- `docs/architecture.md:12`: add `overdue` to the arrow label.
- `docs/architecture.md:68-69`: add one sentence. The service reads the current time from the store clock to decide overdue, and it never writes that time to the log.
- `docs/architecture.md:103` and `docs/guidelines.md:10-11`: remove the claim that the CLI has no tests.

### Step 5: check and commit

- Run `make lint && make test` (`AGENTS.md:88`, `Makefile:1-5`).
- Commit the service rule with its unit tests, then the CLI with its tests. Reference TKT-014, TKT-015, CLI-006, and CLI-010 in each message (`docs/guidelines.md:84-87`).

## Assumptions validated

| Assumption | Class before | Evidence | Result |
|---|---|---|---|
| A replayed ticket always has a due time in epoch seconds | Verified | `ticketdesk/tickets.py:35-36` sets it on every `created` event. `ticketdesk/sla.py:9` adds hours times 3600 to `at`. | confirmed |
| The store clock is readable without an append, and tests can control it | Plausible | `ticketdesk/store.py:14-16` stores `self.clock` as a public attribute. Experiment E3 read it through the service and advanced it in a test. | confirmed |
| Overdue needs no event and breaks no invariant | Risky | INV-001, INV-002, INV-005, LOG-001, and LOG-009 reviewed below. Experiment E3 showed that `overdue` leaves the log bytes unchanged. | confirmed |
| `OVERDUE` fits the 8-character state column | Plausible | Experiment E1 printed `len('OVERDUE') = 7` and the padded value `'OVERDUE '`. | confirmed |
| A new subcommand needs only a new subparser | Plausible | Experiment E2 added only the subparser. `overdue` then printed a ticket due in 72 hours, through the `else:` at `ticketdesk/cli.py:28`. | refuted, plan step 2 fixes the branch |
| A subprocess CLI test runs under `make test` and can make tickets overdue without waiting | Plausible | Experiment E3 ran 12 tests through `unittest discover -s tests` with a hand-written log. All passed. | confirmed |
| Two tickets can share a due time, so the sort needs a tie-break | Plausible | Experiment E3 created a P3 ticket and, 68 hours later, a P1 ticket. Both due times were equal. | confirmed |

### Hypothesis and falsifier

The hypothesis is the shape above: a pure comparison in the service, read at query time, with no stored state. The shape is wrong if the user needs overdue as a recorded fact. Two examples are an audit of when a ticket became overdue and an overdue status that survives an SLA table edit. Both need an event in the log. Nothing in the specs or the request asks for this, so the shape stands. Open question 6 asks the user to confirm.

### Experiments

All scripts are under `outputs/scratch/`. The repo stayed clean after each run (`git status --short` was empty).

- E0, baseline: `make lint && make test` passed with 7 tests on HEAD `57587be`.
- E1, `e1_baseline_cli.py`: a hand-written log with past `at` values replays through the real CLI. `list` printed four lines in the CLI-006 format. `overdue` failed with exit code 2 and "invalid choice", as CLI-001 says.
- E2, drift probe in `scratch/proto`: with only `sub.add_parser("overdue")` added, `overdue` printed `#1 [P3] open     a ticket` and exited with code 0.
- E3, prototype in `scratch/proto`: the step 1 and step 2 changes plus `tests/test_overdue_proto.py`. `make lint` passed and 12 tests passed. The CLI test produced this output:

```
list:
#1 [P1] OVERDUE  Printer
#2 [P3] open     VPN
#3 [P2] OVERDUE  Email
#4 [P1] closed   Closed
overdue:
#3 [P2] OVERDUE  Email
#1 [P1] OVERDUE  Printer
```

The experiments ran on Python 3.15.1. CI runs Python 3.12 (`.github/workflows/ci.yml:10`). The prototype uses no syntax newer than Python 3.10, so we expect no difference. CI confirms this on the first push.

## Test plan

Unit tests go through the service with the fake clock, in `tests/test_tickets.py`:

- Boundary: a ticket is not overdue at exactly its due time. It is overdue 0.001 seconds later. (TKT-014)
- An `open` ticket and an `assigned` ticket past their due times are both overdue. (TKT-014)
- A `closed` ticket is never overdue, also long after its due time. (TKT-014)
- `overdue()` returns overdue tickets only, sorted by due time. Equal due times sort by ID. (TKT-015)
- `overdue()` with no argument reads the store clock. After the fake clock moves 5 hours, a P1 ticket appears.
- `overdue()` and `list()` append no event. The count of replayed events stays the same. (LOG-001)

Subprocess tests go through the CLI in `tests/test_cli.py`. Each test writes a log by hand, with `at` values at least one hour away from any due time. A slow CI machine then cannot flip a result.

- `list` shows `OVERDUE` for an overdue `open` ticket and an overdue `assigned` ticket. It shows `open` for a ticket that is not yet due and `closed` for a closed one. (CLI-006)
- `overdue` prints only the overdue lines, oldest due time first, and exits with code 0 and an empty stderr. (CLI-010, CLI-008)
- Every line of `overdue` also appears in `list`.
- `overdue` on a missing log prints nothing and exits with code 0. (LOG-006)
- `overdue` with no overdue ticket prints nothing and exits with code 0. (CLI-010)
- The log file bytes are the same before and after `list` and `overdue`. (INV-002, LOG-001)

The end-to-end sequence for a manual check runs against a temporary log:

```bash
python3 -m ticketdesk.cli --log /tmp/t.jsonl create "Printer on fire" --priority P1
python3 -m ticketdesk.cli --log /tmp/t.jsonl list      # expect: open, not OVERDUE
python3 -m ticketdesk.cli --log /tmp/t.jsonl overdue   # expect: no output, exit 0
# Append a created event with "at" set 5 hours in the past, then:
python3 -m ticketdesk.cli --log /tmp/t.jsonl list      # expect: OVERDUE on that ticket
python3 -m ticketdesk.cli --log /tmp/t.jsonl overdue   # expect: only that ticket
python3 -m ticketdesk.cli --log /tmp/t.jsonl close 2 "Replaced the toner cartridge"
python3 -m ticketdesk.cli --log /tmp/t.jsonl overdue   # expect: no output
```

## Risks and mitigations

- **Scripts that parse `list` may break.** The state word changes to `OVERDUE` for some tickets. No consumer exists in the repo, and a grep found none. Mitigation: the spec edit to CLI-006 records the change. Mention it in the PR description.
- **An SLA table edit moves old due times.** Replay computes the due time from the current table (`ticketdesk/tickets.py:36`). An edit of `SLA_HOURS` can therefore make old tickets overdue or not overdue. This is existing TKT-005 behavior. Mitigation: none in this change. Open question 6 covers it.
- **A wrong system clock gives a wrong result.** The overdue result is only as correct as `time.time()` on the machine. Mitigation: none. The tool already trusts this clock for every event (INV-005).
- **The CLI-007 traceback also affects `overdue`.** A corrupt log or an unknown priority in the log escapes as a traceback with exit code 1. Mitigation: none here. The open TODO under CLI-007 owns it.
- **Cost of replay.** `overdue` reads the whole log once, the same as `list`. The architecture accepts this cost (`docs/architecture.md:62-63`).

## Validation record

### Problem statement

The goal has two parts. `ticketdesk list` marks every ticket past its due time as `OVERDUE`. A new `ticketdesk overdue` lists only overdue tickets, oldest due time first.

The constraints come from the repo. The log stays append-only and is the only source of truth (INV-001, INV-002). Ticket rules stay out of the CLI (`docs/architecture.md:36-38`). The standard library is the only dependency (`AGENTS.md:25`).

The non-goals are in the out-of-scope section.

Success criteria:

- SC1: `list` shows `OVERDUE` for a ticket that is not closed and whose due time has passed.
- SC2: `list` shows the plain state for a ticket that is not yet due and for every closed ticket.
- SC3: `overdue` prints only overdue tickets.
- SC4: `overdue` prints the oldest due time first, in a deterministic order.
- SC5: neither command appends to the log, and the existing 7 tests still pass.

These observations would prove that the change does not work:

- `overdue` prints a ticket that is not yet due.
- A closed ticket shows `OVERDUE`.
- A ticket shows `OVERDUE` before its due time.
- The log grows after `list` or `overdue`.

### Spec cross-validation

| Spec | Affected | How the plan satisfies it |
|---|---|---|
| INV-001 | yes | Overdue is derived from the replayed log and the clock. No other store holds it. Step 1. |
| INV-002 | yes | No command writes. The CLI test compares the log bytes. Step 3. |
| INV-003, INV-004 | no | IDs and the corrupt-line rule are untouched. `overdue` uses the same replay. |
| INV-005 | yes | The clock is read but nothing is stamped. Events still get their time only from the store. Step 1. |
| TKT-001 | yes | The states stay the same. `OVERDUE` is a display label, not a state. Steps 0 and 2. |
| TKT-005 | yes | The plan uses the due time as specified. Step 1. |
| TKT-013 | yes | `list` keeps the ID order. Step 2. |
| TKT-014, TKT-015 | new | Proposed in step 0, implemented in step 1. |
| LOG-001 | yes | Neither command appends. The text gets a small edit in step 0. |
| LOG-002, LOG-003 | no | No new event kind and no new field. |
| LOG-009 | yes | `_tickets()` stays free of the current time. Step 1. |
| CLI-001 | yes, conflict | The text says four subcommands. Step 0 changes it to five. |
| CLI-006 | yes, conflict | The text says the third field is the state. Step 0 changes it to a label. |
| CLI-007, CLI-008 | yes | `overdue` reuses the existing error and exit-code path. |
| CLI-010 | new | Proposed in step 0, implemented in step 2. |

The two conflicts are expected for a new feature. They need the user's approval before code work, as `docs/guidelines.md:45-46` requires.

### Architecture cross-validation

- **Boundaries.** The rule is in `tickets.py`. The CLI only formats and calls `is_overdue`, which the service module defines (`docs/architecture.md:36-38`). The store gains no ticket knowledge.
- **Security.** No new input exists beyond a subcommand name. There is no auth and no network (`docs/architecture.md:64-65`).
- **Scale and cost.** One full replay per command, the same as `list`.
- **Observability.** This is a CLI with no logs or metrics. Nothing to add.
- **Background work.** None. The tool runs one command and exits.

No deviation from the architecture is needed.

### Project conventions to follow

- **[`AGENTS.md:12-13`]** Convention: *the log is the truth, and state is always rebuilt by replay.* **Reflected in plan:** step 1 derives overdue at read time and adds no event.
- **[`AGENTS.md:93`, `docs/README.md:39`, `docs/guidelines.md:78-80`]** Convention: *doc and spec changes need user confirmation.* **Reflected in plan:** steps 0 and 4 are gated on approval.
- **[`AGENTS.md:96`, `docs/guidelines.md:87`]** Convention: *reference spec IDs in code comments, tests, and commits.* **Reflected in plan:** steps 1, 3, and 5 cite TKT-014, TKT-015, CLI-006, and CLI-010.
- **[`docs/architecture.md:36-38`, `docs/guidelines.md:51-53`]** Convention: *no ticket rule in the CLI.* **Reflected in plan:** step 1 puts the rule in `tickets.py`. Step 2 only formats.
- Per-component conventions: the repo has no nested `AGENTS.md`. A file listing found only the root one. **Doesn't constrain this plan**, because no component has its own rules.
- **[`AGENTS.md:25`, `pyproject.toml:1-8`]** Package manager: *no dependencies, and no lockfile exists.* **Reflected in plan:** steps 1 to 3 use only `time`, `subprocess`, `json`, and `tempfile` from the standard library.
- **[`Makefile:1-5`, `AGENTS.md:88`, `docs/guidelines.md:12-13`]** Entry points: *`make lint && make test` before every push.* **Reflected in plan:** step 5.
- **[`AGENTS.md:22`, `docs/architecture.md:80`, `tests/test_tickets.py:8-21`]** Test framework: *`unittest` with discovery under `tests/`, and time through an injected fake clock, not a mock.* **Reflected in plan:** step 3 reuses `Clock` and adds no mocking library.
- **[`docs/guidelines.md:29-34`]** Test planning: *name the test files, the cases, the test type, and an end-to-end command sequence.* **Reflected in plan:** the test plan.
- **[`docs/architecture.md:81`]** Lint: *`compileall` syntax pass only, with no formatter or type checker.* **Doesn't constrain this plan** beyond step 5, because no style tool exists to satisfy.
- Migrations: the repo has none, and the log format does not change (LOG-003). **Doesn't constrain this plan.**
- **[`AGENTS.md:109-110`, CLI-002]** Environment: *the log path comes from `--log`, then `TICKETDESK_LOG`, then `tickets.jsonl`.* **Reflected in plan:** step 3 always passes `--log`, so a developer's environment cannot leak into tests. There are no ports or URLs.
- Async machinery: none exists. Each invocation runs one command (`docs/architecture.md:7`). **Doesn't constrain this plan.**
- **[`ticketdesk/cli.py:30`, `tests/test_store.py:12`]** Existing patterns: *the list line format and a hand-written log in a test.* **Reflected in plan:** steps 2 and 3 reuse both.
- **[`pyproject.toml:5`, `.github/workflows/ci.yml:10`]** Python: *3.11 or later, CI on 3.12.* **Reflected in plan:** no syntax newer than 3.10.
- **[`docs/guidelines.md:84-87`]** Commits: *one logical change per commit, with spec IDs.* **Reflected in plan:** step 0 and step 5 split the commits.

### Codebase sweep

- **In-flight work.** The repo has one commit (`57587be`), one branch, and no stash. Nothing else touches this area.
- **Shadow duplication.** The due time is computed in one place only (`ticketdesk/tickets.py:36`). No other code compares a time with it.
- **Caller-side drift.** The catch-all `else:` at `ticketdesk/cli.py:28` is the main drift risk. Step 2 fixes it. The constructor change keeps both callers working. The docs state "four subcommands" (CLI-001) and "7 unittest cases" (`AGENTS.md:102`). Steps 0 and 4 update them.
- **Test infrastructure gap.** The CLI has no tests today (`AGENTS.md:116`). Step 3 adds them. Experiment E3 showed that the subprocess tests run under `make test`.

### Success criteria counterfactual

Result: **Confirmed with gaps**.

| Criterion | Plan steps | Status |
|---|---|---|
| SC1 | steps 1 and 2, CLI test | Confirmed |
| SC2 | steps 1 and 2, unit and CLI tests | Confirmed |
| SC3 | steps 1 and 2, unit and CLI tests | Confirmed |
| SC4 | step 1 sort with the ID tie-break, unit test | Confirmed |
| SC5 | steps 3 and 5, log-bytes test | Confirmed |

The gaps:

- The display of `OVERDUE` in place of the state depends on open question 1.
- The experiments ran on Python 3.15.1, not on the CI version 3.12.

## Open questions

Nobody was available during planning. Each question states the assumption that the plan uses.

1. **Should `OVERDUE` replace the state word in `list`?** Assumption: yes, it replaces `open` or `assigned`, and the line keeps its width. The alternative keeps the state and adds a marker column, for example `#1 [P1] open     OVERDUE Printer on fire`.
2. **Can a closed ticket be overdue?** Assumption: no. A ticket closed after its due time shows `closed`. A "closed late" report is a separate feature.
3. **Is a ticket overdue at exactly its due time?** Assumption: no. It is overdue only when the current time is later than the due time.
4. **Should `overdue` show the due time or how late each ticket is?** Assumption: no. It uses the `list` format, so no time-zone format is needed.
5. **Should `overdue` exit with a nonzero code when it finds tickets, for use in scripts?** Assumption: no. It exits with code 0, as CLI-008 says for every successful command.
6. **Is overdue only a live view, not a recorded fact?** Assumption: yes. If the user needs a history of when tickets became overdue, the shape changes to an event in the log.
7. **Does the user approve the spec edits in step 0 and the doc edits in step 4?** Assumption for this plan: yes. No code work starts until the user says so.

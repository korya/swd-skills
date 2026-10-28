# Plan: overdue tickets in `ticketdesk`

## Headline

We derive overdue at read time from the replayed log and the store clock, with no new event. `ticketdesk list` prints `OVERDUE` in the state column of an overdue ticket, and `ticketdesk overdue` lists only those tickets, earliest due time first. The blocking decision is the user's sign-off on six spec changes, and on whether `OVERDUE` may hide the `open` or `assigned` state.

## Approach summary

The service in `ticketdesk/tickets.py` gets one rule and one query. A ticket is overdue when it is not closed and the current time is strictly after its due time. The due time already exists on every replayed ticket (`ticketdesk/tickets.py:36`), so the rule needs no new data. The service also gets a clock, which defaults to the clock of the event store. A new method `overdue(now)` returns the overdue tickets, sorted by due time and then by ID.

The CLI in `ticketdesk/cli.py` reads the time once per invocation and adds the `overdue` subcommand. It swaps the state label for `OVERDUE` when the rule says so. The event store, the SLA table, the event kinds, and the log format stay untouched. The plan stands on one assumption: overdue is a pure function of the replayed log and the current time. A prototype in a scratch copy confirmed it. The main trade-off is that the `list` line of an overdue ticket no longer shows whether the ticket is `open` or `assigned`.

## Out of scope

- Alerts, notifications, or a non-zero exit code when tickets are overdue.
- Business hours or per-customer SLA targets. `ticketdesk/sla.py` stays unchanged.
- An `overdue` event in the log, or any stored overdue flag.
- The open CLI-007 TODO. A corrupt log or an unknown priority still escapes as a traceback (`docs/product-specs/cli.md:50-52`). The new command inherits that behavior unchanged.
- New columns in `list`, such as the assignee or the due time.

## Plan

Step 1 needs the user's sign-off before any code work starts. Steps 2 to 6 can follow in one commit. Step 7 is a separate docs commit.

1. **Update the product specs** after the user signs off. Each item is a proposed text change, not yet applied.
   - `docs/product-specs/tickets.md`: add **TKT-014: Overdue tickets**. "A ticket is overdue when its state is not `closed` and the current time is later than its due time (TKT-005). At the due time itself, the ticket is not yet overdue. A closed ticket is never overdue."
   - `docs/product-specs/tickets.md`: add **TKT-015: Overdue listing order**. "Listing overdue tickets returns only overdue tickets, sorted by due time ascending, then by ID ascending."
   - `docs/product-specs/cli.md` CLI-001: change "four subcommands" to five and add `overdue`.
   - `docs/product-specs/cli.md` CLI-006: the state column shows `OVERDUE` instead of `open` or `assigned` when the ticket is overdue per TKT-014. The column stays padded to 8 characters.
   - `docs/product-specs/cli.md`: add **CLI-010: overdue**. "`ticketdesk overdue` prints one line per overdue ticket in TKT-015 order, in the CLI-006 line format. With no overdue tickets it prints nothing and exits with code 0."
   - `docs/product-specs/event-log.md` LOG-001: change "Listing tickets appends nothing" to "Listing tickets, overdue or all, appends nothing."
2. **Add the overdue rule** to `ticketdesk/tickets.py`. Add a module function `is_overdue(ticket, now)` that returns `ticket.state != "closed" and now > ticket.due_at`. Put a `# implements TKT-014` comment on it.
3. **Give the service a clock** in `ticketdesk/tickets.py`. Change `TicketService.__init__(self, store)` to `__init__(self, store, clock=None)` and set `self.clock = clock or store.clock`. Add `now()`, which calls `self.clock()` once. The argument is optional, so the two existing callers (`ticketdesk/cli.py:20`, `tests/test_tickets.py:21`) keep working.
4. **Add `TicketService.overdue(now)`** in `ticketdesk/tickets.py`. It filters `self._tickets().values()` with `is_overdue` and sorts by `(t.due_at, t.id)`. Put a `# implements TKT-015` comment on it. The method takes `now` as an argument so that one command uses one time value.
5. **Wire the CLI** in `ticketdesk/cli.py`.
   - Add `sub.add_parser("overdue")` next to `list` (`ticketdesk/cli.py:18`).
   - In the `list` and `overdue` branch, call `now = svc.now()` once.
   - Iterate `svc.list()` or `svc.overdue(now)`.
   - Print `label = "OVERDUE" if is_overdue(t, now) else t.state` in the existing format `f"#{t.id} [{t.priority}] {label:<8} {t.title}"` (`ticketdesk/cli.py:30`).
   - The CLI only picks the label. The rule stays in the service, per `docs/architecture.md:36-38`.
6. **Add tests.**
   - Extend `tests/test_tickets.py` with unit cases through the service and the existing fake `Clock` (`tests/test_tickets.py:8-14`).
   - Create `tests/test_cli.py` with subprocess cases against a temporary log. The test plan below lists the cases for both files.
7. **Update the docs** after the user signs off, in a separate commit.
   - `AGENTS.md:102` changes the test count, `AGENTS.md:103-106` gains an `overdue` example, and `AGENTS.md:114-116` lists `overdue` as done and the CLI as tested.
   - `docs/architecture.md:12` adds `overdue` to the diagram label. `docs/architecture.md:95-96` adds `test_cli.py`, and `docs/architecture.md:103` drops "The CLI is not covered by tests today."
   - `docs/architecture.md:68-69` adds one sentence. The service reads the current time from the same injectable clock as the store.
   - `docs/guidelines.md:10-11` drops "The CLI has no tests today."
8. **Run `make lint && make test`** before the push (`Makefile:2-5`). CI runs the same two commands on Python 3.12 (`.github/workflows/ci.yml:10-12`).

## Assumptions validated

| # | Assumption | Class | Result | Evidence |
|---|---|---|---|---|
| A1 | Every replayed ticket carries a correct `due_at`. | Verified | confirmed | `ticketdesk/tickets.py:35-36` sets `due_at` from the `created` event. `tests/test_tickets.py:26-29` checks it for P1. |
| A2 | A time-based rule fits INV-001 without stored state. | Risky | confirmed | The prototype derived overdue from replay and the clock alone. The log hash was the same before and after `list` and `overdue`. |
| A3 | The service can read "now" from the store clock without a new seam. | Plausible | confirmed | `ticketdesk/store.py:14-16` stores the injectable clock as `self.clock`. The probe printed `default clock is store clock: True` and `now() calls clock once: True`. |
| A4 | `OVERDUE` fits the 8-character state column. | Plausible | confirmed | `len("OVERDUE")` is 7. The prototype printed `#1 [P1] OVERDUE  Printer on fire`, aligned with `#2 [P3] open     New mouse`. |
| A5 | A subprocess CLI test can run under `make test` with a backdated log. | Plausible | confirmed | A probe file under the prototype's `tests/` passed in `unittest discover -s tests` (8 tests, OK). The probe ran `python -m ticketdesk.cli` with `cwd` set to the repo root. |
| A6 | "Oldest due first" has one reading. | Risky | refuted | The two readings give different orders, see below. The plan assumes the earliest due time and records open question Q2. |
| A7 | Due times never tie. | Plausible | refuted | A P3 ticket at t0 and a P1 ticket at t0+68h have equal due times. The probe printed `tie due_at equal: True`. The plan sorts by ID second. |

The probe for A6 used two tickets. Ticket 1 is a P3 created at t0, due at t0+72h. Ticket 2 is a P1 created at t0+66h, due at t0+70h.

```text
overdue order (due): [(2, 'young P1'), (1, 'old P3')]
by created instead : [(1, 'old P3'), (2, 'young P1')]
```

The probe also checked the boundary and the closed case.

```text
boundary now==due  : False
now==due+0.001     : True
closed past due    : False
```

The baseline on `HEAD` and the prototype both pass lint and tests.

- On `HEAD`, `make lint` is clean and `make test` runs 7 tests with result OK.
- The prototype passes the same 7 tests with no test change.
- On `HEAD`, the CLI rejects `overdue` with a usage line and exit code 2, as CLI-001 requires.

**Falsifier.** The shape is wrong if anyone needs a fact about overdue that the log and the clock cannot give. An example is "when did this ticket become overdue".

The falsifier did not trigger. A ticket becomes overdue at its `due_at`, which replay computes exactly. A late close is visible as a `closed` event whose `at` is later than `due_at`. No requirement in `docs/product-specs/` asks for more.

**Spec and invariant check.**

| ID | Effect | Plan step |
|---|---|---|
| INV-001 | Upheld. Overdue comes from replay and the clock. Nothing caches it. | 2, 4 |
| INV-002 | Upheld. Neither command writes to the log. | 5, e2e case E5 |
| INV-005 | Upheld. No new event. "Now" comes from the store clock by default. | 3 |
| TKT-001 | Upheld. `OVERDUE` is a display label. `Ticket.state` keeps its three values. | 2, 5 |
| TKT-005 | Reused unchanged as the due time. | 2 |
| TKT-013 | Unchanged. `list` keeps ID order. | 5 |
| TKT-014, TKT-015 | New. Needs sign-off. | 1, 2, 4 |
| CLI-001 | Changed from four to five subcommands. Needs sign-off. | 1, 5 |
| CLI-006 | Changed. The state column can show `OVERDUE`. Needs sign-off. | 1, 5 |
| CLI-010 | New. Needs sign-off. | 1, 5 |
| CLI-007, CLI-008 | Upheld. `overdue` has no ticket-rule errors and exits with code 0. | 5 |
| LOG-001 | Wording change to cover `overdue`. Needs sign-off. | 1 |
| LOG-002, LOG-003 | Unchanged. No new event kind or field. | none |
| LOG-009 | Upheld. Replay stays deterministic. Only the overdue label depends on the time. | 2 |

**Codebase sweep.**

- In-flight work: `git log` shows one commit, `b7942f8`, and one branch, `main`. Nobody else is on this.
- Duplicate logic: `grep -rniE "overdue|clock|now"` finds no existing overdue code. The only clock is the store clock.
- Callers of a changed contract: `TicketService(...)` has two callers, `ticketdesk/cli.py:20` and `tests/test_tickets.py:21`. The new `clock` argument is optional. Nothing in the repo parses `list` output.
- Test infrastructure: no CLI tests exist (`docs/architecture.md:103`). The plan builds `tests/test_cli.py`. Probe A5 shows the subprocess pattern works under `make test`.

## Project conventions to follow

- **[`docs/architecture.md:36-38`]** Convention: *the CLI holds no ticket rules.* **Reflected in plan:** step 2 puts `is_overdue` in the service. Step 5 only picks a label.
- **[`docs/architecture.md:42-44`]** Convention: *the service derives every ticket from the event list, so a rule change needs no data migration.* **Reflected in plan:** steps 2 and 4 compute overdue from replay. There is no migration.
- **[`docs/architecture.md:48-50`]** Convention: *time comes from an injectable clock, which keeps tests deterministic.* **Reflected in plan:** step 3 defaults the service clock to the store clock and allows an override.
- **[`AGENTS.md:25`, `pyproject.toml:5`]** Convention: *no dependencies, Python 3.11 or later.* **Reflected in plan:** the change uses only the standard library and no syntax newer than 3.10.
- **[`Makefile:2-5`, `.github/workflows/ci.yml:10-12`]** Convention: *`make lint` is a `compileall` pass, `make test` is `unittest discover -s tests`.* **Reflected in plan:** step 8 runs both. Step 6 puts the new file under `tests/` so discovery finds it.
- **[`tests/test_tickets.py:8-21`]** Convention: *tests inject a fake clock through the constructor and use no mock library.* **Reflected in plan:** the unit cases pass `now` and the clock explicitly. They do not patch `time.time`.
- **[`docs/guidelines.md:29-34`]** Convention: *name the unit and the subprocess cases up front, and plan e2e command sequences against a temporary log.* **Reflected in plan:** the test plan below.
- **[`AGENTS.md:96`, `docs/guidelines.md:87`]** Convention: *reference spec IDs in code comments, tests, and commits.* **Reflected in plan:** steps 2 and 4 add `# implements` comments. Test names and commit messages cite TKT-014, TKT-015, and CLI-010.
- **[`docs/guidelines.md:76-80`, `AGENTS.md:93`]** Convention: *doc and spec changes need user confirmation.* **Reflected in plan:** steps 1 and 7 wait for sign-off.
- **[`docs/guidelines.md:84-86`]** Convention: *one logical change per commit.* **Reflected in plan:** one commit for specs, one for code and tests, one for the other docs.
- **[`ticketdesk/cli.py:14-18`]** Convention: *subcommands are `argparse` subparsers on `cmd`.* **Reflected in plan:** step 5 adds one more subparser in the same style.
- Package manager: does not constrain this plan. The project installs nothing (`AGENTS.md:25`).
- Migrations: do not constrain this plan. Overdue is derived, and the log format does not change.
- Ports, URLs, and async work: do not constrain this plan. The tool is a local, synchronous CLI (`docs/architecture.md:64-65`).

## Test plan

**Unit tests in `tests/test_tickets.py`**, through the service with the fake clock:

- U1: an `open` ticket one second past its due time is overdue (TKT-014).
- U2: an `assigned` ticket past its due time is overdue (TKT-014).
- U3: a ticket exactly at its due time is not overdue (TKT-014 boundary).
- U4: a ticket closed after its due time is not overdue (TKT-014).
- U5: `overdue(now)` returns the earliest due time first. Use the P3 at t0 and P1 at t0+66h pair, where creation order and due order differ (TKT-015).
- U6: equal due times sort by ID (TKT-015 tie). Use the P3 at t0 and P1 at t0+68h pair.
- U7: `overdue(now)` with no tickets returns an empty list.
- U8: `overdue(now)` appends no event. The replayed event list is the same before and after (LOG-001).

**Subprocess tests in a new `tests/test_cli.py`.** Each case writes a log with `at` values relative to `time.time()`, hours apart, and runs `python -m ticketdesk.cli --log <tmp>` with `cwd` at the repo root.

- E1: `list` shows `OVERDUE` for an overdue open ticket and an overdue assigned ticket. It shows `open` for a ticket not yet due and `closed` for a late-closed ticket. The order stays by ID (CLI-006, TKT-013).
- E2: `overdue` prints only the overdue tickets, earliest due time first (CLI-010, TKT-015).
- E3: `overdue` with no overdue tickets prints nothing and exits with code 0, with an empty stderr (CLI-008, CLI-010).
- E4: `overdue` with a missing log file prints nothing, exits with code 0, and does not create the file (LOG-006).
- E5: the log file bytes are the same after `list` and `overdue` (LOG-001, INV-002).
- E6: the full flow with the real clock. `create`, `assign`, then `list` shows `assigned`, and `overdue` prints nothing.

**Manual check.** Run the commands in `AGENTS.md:103-106` plus `overdue` against `/tmp/t.jsonl`. Then append a hand-written `created` event with an `at` five hours old and priority `P1`, and run `list` and `overdue` again.

## Risks and mitigations

- **Scripts that parse `list` may break.** A script that expects `open` or `assigned` in the state column now sees `OVERDUE`. Mitigation: the column count and padding stay the same. The release note names the change. Open question Q1 offers a form that keeps the state.
- **`OVERDUE` hides whether someone owns the ticket.** An overdue `open` ticket is worse than an overdue `assigned` one, and `list` no longer tells them apart. Mitigation: open question Q1.
- **A wrong system clock gives wrong results.** A clock that runs behind hides overdue tickets. This risk already exists for the `at` stamps. Mitigation: none in code. The architecture assumes a local, trusted clock (`docs/architecture.md:68-69`).
- **The fake test clock moves on every call.** `tests/test_tickets.py:13` adds one second per call. A test that calls `svc.now()` twice gets two times. Mitigation: unit tests pass a fixed `now` to `overdue(now)` and `is_overdue`.
- **Cost grows with the log.** `overdue` replays the full log like every other command (`docs/architecture.md:62-63`). The sort adds O(k log k) for k overdue tickets. This does not change the existing cost profile.

## Counterfactual

**Verdict: confirmed with gaps.** Every success criterion has a plan step. The gaps are the spec sign-offs and the readings in Q1 to Q4.

| Success criterion | Plan step |
|---|---|
| A ticket past its due time shows `OVERDUE` in `ticketdesk list` | Steps 2, 3, 5. Tests U1, U2, E1. |
| A ticket not yet due, or closed, does not show `OVERDUE` | Step 2. Tests U3, U4, E1. |
| `ticketdesk overdue` lists only overdue tickets | Steps 4, 5. Tests E2, E3. |
| `ticketdesk overdue` sorts by earliest due time first | Step 4. Tests U5, U6, E2. |
| Nothing is written to the log, and the invariants hold | Steps 2 to 5. Tests U8, E4, E5. |
| Specs match the behavior | Step 1, after sign-off. |
| `make lint && make test` pass, CLI included | Steps 6, 8. |

A late-closed ticket marked `OVERDUE`, a changed log, or a creation-time order would prove the change wrong.

- A closed ticket shows `OVERDUE`. Test U4 checks this.
- The log file changes after a read command. Test E5 checks this.
- The `overdue` order follows the creation time. Test U5 checks this.

## Open questions

Nobody was available during planning. Each question names the assumption the plan uses.

- **Q1. Should `OVERDUE` replace the state, or sit beside it?** The request says "show as OVERDUE". The plan replaces `open` or `assigned` with `OVERDUE` in the state column. The alternative keeps the state and adds a marker, for example `#4 [P2] assigned Email bounce (OVERDUE)`. That form keeps ownership visible but changes the title field for parsers. *Assumption: replace the state.*
- **Q2. Does "oldest due first" mean the earliest due time or the earliest creation time?** The orders differ (probe A6). *Assumption: earliest due time, the ticket that is most late.*
- **Q3. Is a ticket overdue at the exact due time?** "Pass their due time" reads as strictly after. *Assumption: strictly after.*
- **Q4. Is a ticket that closed late still overdue?** *Assumption: no. A closed ticket is never overdue.*
- **Q5. Should `overdue` exit with a non-zero code when it finds tickets?** That would help cron jobs and scripts. *Assumption: no. It exits with code 0, like `list`.*
- **Q6. Should `overdue` print more, such as the due time or how late the ticket is?** *Assumption: no. It reuses the `list` line format.*
- **Q7. Do you approve the six spec changes in step 1?** They are TKT-014, TKT-015, CLI-001, CLI-006, CLI-010, and LOG-001. *Assumption: none of them lands until you approve. No code work starts before that.*

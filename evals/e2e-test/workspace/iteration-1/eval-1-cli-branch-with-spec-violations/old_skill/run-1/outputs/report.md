# E2E test report: `feature/cli-tidy` (ticketdesk CLI)

**Verdict: 38/48 PASS, 9 FAILURE, 1 BLOCKED — not ready to merge.** Three of the PR's four
promised changes contradict the product specs as written, and one of them lets a closed
ticket be reopened and closed again (TKT-008, TKT-011, and the "a ticket moves forward
only" contract). The PR's "All tests pass locally" claim is false: `make test` fails one
case on this branch.

- Scope: the branch vs `main` (4 promised behaviors), specs `CLI-*` and `TKT-*`, blast
  radius `LOG-*`/`INV-*` and the shell contract.
- Surface / persona: shell user running `python3 -m ticketdesk.cli` from the repo root.
- Environment: local dev; all logs under this directory (`--log`). Mutated freely.
- Depth: comprehensive.

## Case table

| # | Case | Spec / ref | Status |
|---|------|-----------|--------|
| R1 | `--help` answers from the repo root | readiness | PASS |
| C01 | `--help` has a description line that is accurate and spelled right | PR item 4 | FAILURE |
| C02 | `list` line is `#<id> [<priority>] <state> <title>`, state padded to 8 | CLI-006, PR item 1 | FAILURE |
| C03 | `close` with the 9-char note `duplicate` is rejected | TKT-010, PR item 2 | FAILURE |
| C04 | `close` with an 8-char note is rejected with the spec'd message | TKT-010 | PASS |
| C05 | `close` with exactly 10 chars is accepted | TKT-010 | PASS |
| C06 | `close` with `"   dup   "` is rejected (trimmed length) | TKT-010 | PASS |
| C07 | `assign` on a closed ticket fails with `ticket <id> is closed`, no event | TKT-008, PR item 3 | FAILURE |
| C08 | A closed ticket stays closed after an assign attempt | TKT-001, tickets.md forward-only | FAILURE |
| S01 | No subcommand: usage on stderr, exit 2 | CLI-001 | PASS |
| S02 | Unknown subcommand: usage on stderr, exit 2 | CLI-001 | PASS |
| S03 | `--log` beats `TICKETDESK_LOG` | CLI-002 | PASS |
| S04 | `TICKETDESK_LOG` beats the default | CLI-002 | PASS |
| S05 | Default is `./tickets.jsonl` in the cwd | CLI-002 | PASS |
| S06 | `create` prints `#<id> open <title>` | CLI-003 | PASS |
| S07 | `create` without `--priority` records `P3` | CLI-003 | PASS |
| S08 | `assign` prints `#<id> assigned -> <assignee>` | CLI-004 | PASS |
| S09 | `close` prints `#<id> closed` | CLI-005 | PASS |
| S10 | `list` with no tickets prints nothing | CLI-006, LOG-006 | PASS |
| S11 | Rule error: `error: <msg>` on stderr, exit 2, empty stdout | CLI-007 | PASS |
| S12 | Success: exit 0, empty stderr | CLI-008 | PASS |
| S13 | Non-integer id: usage error, exit 2, no event | CLI-009 | PASS |
| S14 | Unknown priority `P9`: error names value and allowed set, no ticket | TKT-003, CLI-007 | FAILURE (pre-existing) |
| S15 | Corrupt log line: error names path, line, `corrupt event`; no state | LOG-007, INV-004, CLI-007 | FAILURE (pre-existing) |
| T01 | States `open` -> `assigned` -> `closed` visible in `list` | TKT-001 | PASS |
| T02 | Empty / whitespace title: `title is required`, list unchanged | TKT-002 | PASS |
| T03 | IDs 1,2,3,...; after closes the next create is max+1 | TKT-004, INV-003 | PASS |
| T04 | Due time by priority is observable | TKT-005 | BLOCKED |
| T05 | Assign open -> assigned; reassign replaces the assignee | TKT-006 | PASS |
| T06 | Empty / whitespace assignee: `assignee is required` | TKT-007 | PASS |
| T07 | Close an open and an assigned ticket -> `closed` | TKT-009 | PASS |
| T08 | Close twice: `ticket <id> is already closed` | TKT-011 | PASS (on re-run, see C08) |
| T09 | Unknown id on assign/close: `no ticket <id>` | TKT-012 | PASS |
| T10 | `list` sorted by id ascending, closed included | TKT-013 | PASS |
| L01 | One event per create/assign/close; list and rejected commands append nothing | LOG-001 | PASS |
| L02 | Event kinds and per-kind fields; every event has `kind`, `id`, `at` | LOG-002, LOG-003 | PASS |
| L03 | `at` is epoch seconds set at append time | LOG-004, INV-005 | PASS |
| L04 | Keys sorted, newline-terminated; blank lines ignored on replay | LOG-005 | PASS |
| L05 | Missing file: list prints nothing and creates nothing; first create -> `#1` and the file | LOG-006 | PASS |
| L06 | Appending leaves the existing lines byte-identical | LOG-008, INV-002 | PASS |
| L07 | Two consecutive `list` runs are identical | LOG-009 | PASS |
| E01 | stdout / stderr separation in a pipe | shell contract | PASS |
| E02 | `list \| head -1` on a 500-ticket log: no error, exit 0 | shell contract | PASS |
| E03 | Unicode, 300-char, and whitespace-padded titles round-trip | edge | PASS |
| E04 | id `0` and `-1`: graceful `no ticket` error | edge | PASS |
| E05 | `--log` is a directory / parent dir missing: graceful error | edge | FAILURE (pre-existing) |
| E06 | Subcommand `--help` is accurate | shell contract | PASS |
| E07 | README tells a user how to run the CLI | docs | FAILURE (pre-existing) |

All commands below were run from `repo/` with `--log <this dir>/tickets.jsonl` unless noted.

## Non-PASS details

### C01 — `--help` description is misspelled (FAILURE)

- Steps: `python3 -m ticketdesk.cli --help`
- Expected: a correctly spelled description line.
- Observed (stdout, exit 0): `Manage support tikets from the shell.`
- Most-likely cause: typo in the new `description=` string added by this branch.

### C02 — `list` dropped the priority column (FAILURE)

- Steps: create three tickets with `--priority P1`, default, `--priority P2`; run `list`.
- Expected per CLI-006: `#1 [P1] open     Printer on fire` (and so on).
- Observed:
  ```
  #1 open     Printer on fire
  #2 open     Laptop won't boot
  #3 open     VPN drops every hour
  ```
  State padding to 8 is intact; the `[<priority>]` field is gone. Priority is now not
  visible anywhere in the CLI; the only way to learn a ticket's priority is to read the
  raw JSON log.
- Most-likely cause: deliberate per PR item 1, but `docs/product-specs/cli.md` CLI-006 was
  not changed and the PR cites no spec ID. Spec and product now disagree.

### C03 — a 9-character resolution note is accepted (FAILURE)

- Steps: `close 2 "duplicate"` (9 characters).
- Expected per TKT-010: `error: resolution note must be at least 10 characters`, exit 2,
  ticket #2 stays `open`.
- Observed: stdout `#2 closed`, exit 0; the log gained
  `{"at": ..., "id": 2, "kind": "closed", "resolution": "duplicate"}`.
- Related: an 8-character note (C04) is still rejected with the message
  `resolution note must be at least 10 characters`, so the product enforces 9 while the
  message and spec say 10. The user who typed 8 characters is told the wrong rule.
- Most-likely cause: deliberate per PR item 2, implemented as an off-by-one on the
  threshold without touching the message or TKT-010.

### C07 — assigning a closed ticket succeeds (FAILURE)

- Steps: `create "Printer on fire" --priority P1`; `assign 1 dana`;
  `close 1 "Replaced the toner cartridge"`; `assign 1 frank`.
- Expected per TKT-008: `error: ticket 1 is closed`, exit 2, no event appended.
- Observed: stdout `#1 assigned -> frank`, exit 0; an `assigned` event was appended after
  the `closed` event.
- Most-likely cause: deliberate per PR item 3 ("works at any point in its life"), but
  TKT-008 and the forward-only contract in `tickets.md` were not changed, and the unit
  test `test_assign_requires_open_ticket` now fails (see Issue 1). The PR's "All tests
  pass locally" is not true on this branch.

### C08 — the closed ticket was reopened (FAILURE)

- Steps: continue from C07; run `list`; then `close 1 "Closing it a second time"`.
- Expected: ticket #1 remains `closed`; a second `close` fails with
  `ticket 1 is already closed` (TKT-011).
- Observed: `list` shows `#1 assigned Printer on fire`; the second `close` printed
  `#1 closed` with exit 0 and appended a second `closed` event with a different
  resolution. Ticket #1 now has two resolutions in the log.
- Most-likely cause: cascade of C07. Replay treats the late `assigned` event as a state
  change, so "nothing reopens a closed ticket" no longer holds and TKT-011 is bypassed.
  T08 was re-run on an untouched closed ticket (#2) to earn its PASS.

### S14 — unknown priority escapes as a traceback (FAILURE, pre-existing)

- Steps: `create "Bad prio" --priority P9` (also `--priority p1`).
- Expected per TKT-003 + CLI-007: `error: ...` naming `P9` and `P1, P2, P3` on stderr,
  exit 2.
- Observed: a 14-line Python traceback ending in
  `ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']`, exit 1. No
  ticket was created (log unchanged), so TKT-003's data rule holds; the error surface
  does not.
- Most-likely cause: known and documented in the CLI-007 TODO; not introduced by this
  branch. Reported because a traceback is still what the user sees.

### S15 — corrupt log line escapes as a traceback (FAILURE, pre-existing)

- Steps: copy the first 3 lines of `tickets.jsonl` to `corrupt.jsonl`, append the line
  `this is not json`, then a valid line; run `list` and `create` against it.
- Expected per LOG-007: an error naming the path, line number, and `corrupt event`,
  nothing else; exit 2 per CLI-007.
- Observed: a ~30-line double traceback whose last line is
  `ValueError: <path>/corrupt.jsonl:4: corrupt event: Expecting value: line 1 column 1 (char 0)`,
  exit 1. The required facts are present; the delivery is a stack trace. No state was
  returned and `create` appended nothing (file stayed at 5 lines), so INV-004 holds.
- Most-likely cause: known per the CLI-007 TODO; not introduced by this branch.

### T04 — due time is not observable (BLOCKED)

- No command or output shows a ticket's due time; the log stores only `at` and
  `priority`. TKT-005 cannot be verified through the CLI. Unblocks when a surface
  exposes due time (or the spec says it is derived-only).

### E05 — bad `--log` targets produce tracebacks (FAILURE, pre-existing)

- `--log <existing directory> list` -> traceback ending `IsADirectoryError: [Errno 21]
  Is a directory: ...`, exit 1.
- `--log <missing-dir>/x.jsonl create "Missing parent dir"` -> traceback ending
  `FileNotFoundError: [Errno 2] No such file or directory: ...`, exit 1.
  (`list` on the same path printed nothing and exited 0, consistent with LOG-006.)
- Expected: a one-line `error:` message. Most-likely cause: the CLI maps only
  `TicketError` to an error line; OS errors are not caught. Not introduced by this branch.

### E07 — README has no usage instructions (FAILURE, pre-existing)

- `README.md` is seven lines: a description and "Run `make test` before you push". It
  never says how to invoke the CLI; the working invocation (`python3 -m ticketdesk.cli`,
  `--log`, `TICKETDESK_LOG`) lives only in `AGENTS.md` under "Running the project". A
  first-time user reading the README does not learn how to run the product.

## Missing / untested cases

- TKT-005 due-time arithmetic: no surface exposes it (T04).
- The installed `ticketdesk` entry point (`pyproject.toml`): the invocation asked for was
  `python3 -m ticketdesk.cli`; pip install was not exercised.
- Interrupted runs (Ctrl-C mid-append) and two writers on one log: not exercised; the
  specs do not define the expected behavior.
- Behavior on `main` for comparison: not run; the branch was tested against the specs,
  not against the previous build.

## Issues found (by severity)

1. **Critical — closed tickets can be reassigned and thereby reopened and re-closed.**
   Cases C07, C08. Violates TKT-008, TKT-011, TKT-001's state model, and the
   "a ticket moves forward only / nothing reopens a closed ticket" contract in
   `tickets.md`. Produces logs with two `closed` events and two resolutions for one
   ticket. `make test` fails `test_tickets.TicketTests.test_assign_requires_open_ticket`
   (`AssertionError: TicketError not raised`) on this branch; the PR says all tests pass.
   Per `AGENTS.md`, a change that contradicts a spec needs the conflict surfaced and the
   spec changed with confirmation; neither happened.
2. **High — resolution minimum is 9 in the product, 10 in the spec and in the error
   message.** Case C03 (C04 shows the stale message). Either TKT-010 and the message move
   to 9 (with confirmation) or the threshold goes back to 10.
3. **High — `list` no longer shows priority; CLI-006 unchanged.** Case C02. The PR
   defers the replacement flag to "a later PR", so merging leaves users with no way to
   see priority from the CLI at all.
4. **Medium — `--help` description reads "tikets".** Case C01. The one UI string this
   branch added is misspelled.
5. **Low, pre-existing — unknown priority, corrupt log, and bad `--log` paths surface as
   Python tracebacks with exit 1.** Cases S14, S15, E05. The first two are acknowledged in
   the CLI-007 TODO; the third is not written down anywhere.
6. **Low, pre-existing — README does not say how to run the CLI.** Case E07.

## UX gaps

- Subcommand help is bare: `create --help` shows `--priority PRIORITY` with no allowed
  values and no default; `assign`/`close` list `id`/`assignee`/`resolution` with no
  description; the 10-character resolution rule is discoverable only by tripping it.
- `list` shows no assignee, no resolution, no due time, and (now) no priority. There is no
  `show <id>`; the raw JSON log is the only way to see who owns a ticket.
- Titles keep leading/trailing whitespace verbatim: `create "  padded title  "` lists as
  `#7 open       padded title  `. Not a spec violation, but it looks like a rendering bug.
- Error messages for rule violations are good (`error: no ticket 99`, exit 2). The
  contrast with the traceback cases (Issue 5) makes those feel like crashes.

## Improvements worth doing

- Reconcile PR and specs before merge: update CLI-006, TKT-008, TKT-010 (and the
  forward-only prose) with the user's confirmation, or revert items 1 to 3. The PR body
  cites no spec IDs, which `AGENTS.md` asks for.
- Fix or delete `test_assign_requires_open_ticket` consistently with the decision above,
  and correct the PR's test claim.
- Add CLI-level tests; `AGENTS.md` already records that the CLI is untested, and every
  failure in this report is CLI-visible.
- Catch OS errors (`IsADirectoryError`, `FileNotFoundError`) and the corrupt-log /
  unknown-priority `ValueError`s in the CLI and emit `error: ...` with exit 2, closing
  the CLI-007 TODO.
- Add a usage section to the README.

## Leftover artifacts

All under `<this directory>` (OUTPUT_DIR), kept to reproduce the findings:

- `tickets.jsonl` — 15 events, tickets #1 to #8. #1 carries two `closed` events (Issue 1);
  #2 was closed with the 9-char note `duplicate` (Issue 2); #5 to #8 are the unicode,
  300-char, padded, and default-path titles.
- `env.jsonl` — one ticket, created via `TICKETDESK_LOG` (S04).
- `corrupt.jsonl` — 3 valid lines, `this is not json` on line 4, one valid line after (S15).
- `blank.jsonl` — 3 valid events interleaved with blank lines (L04).
- `pipe.jsonl` — 500 tickets created through the CLI for E02.
- `repo/ticketdesk/__pycache__/`, `repo/tests/__pycache__/` — byte-code caches written by
  Python on first run; untracked, no tracked product file was modified (`git status`
  shows only these two directories).

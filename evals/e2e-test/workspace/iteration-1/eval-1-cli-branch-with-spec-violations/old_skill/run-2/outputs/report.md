# E2E test report: `feature/cli-tidy` (ticketdesk CLI)

**Verdict: 31/39 PASS, 8 FAILURE, 0 BLOCKED. Not ready to merge.** The branch lets a closed ticket be reopened by assigning it (and then closed a second time), contradicts three product specs it never updated (CLI-006, TKT-008, TKT-010), ships a typo in `--help`, and its "all tests pass locally" claim is false: `make test` fails, so CI would fail too.

- **Scope**: the branch diff vs `main` (`list` output, resolution minimum, assign-on-closed, `--help` description) plus every criterion in the affected specs (`CLI-*`, `TKT-*`, `LOG-*`, `INV-*`) and the adjacent commands sharing `cli.py`.
- **Surface / persona**: shell user running `python3 -m ticketdesk.cli` from the repo root (the invocation AGENTS.md documents; the README documents none). Black-box; the product's own stdout, stderr, exit codes and the log file are the only evidence.
- **Environment**: local dev; all logs under `OUTPUT_DIR` via `--log`. Mutation free.
- **Depth**: comprehensive (the ask: "comprehensively, before it merges").
- **Python**: 3.15.1 (CI pins 3.12; nothing here looked version-specific).

Three of the eight failures (C08, C30 twice over) are pre-existing and already acknowledged by the `TODO` under CLI-007; they are reported because the user sees them, but they are not this PR's doing. The other five are introduced by the PR.

## Case table

| # | Case | Spec / ref | Status |
|---|---|---|---|
| C01 | `--help`: usage, description line, four subcommands, exit 0, correct spelling | CLI-001, PR | FAILURE |
| C02 | No subcommand: usage on stderr, exit 2 | CLI-001 | PASS |
| C03 | Unknown subcommand: usage on stderr, exit 2 | CLI-001 | PASS |
| C04 | First `create` on a missing log: `#1 open <title>`, file created, one `created` event, sorted keys, `at`, default `P3` | CLI-003, TKT-004, LOG-003, LOG-005, LOG-006 | PASS |
| C05 | `create --priority P1` records `P1` | CLI-003, TKT-003 | PASS |
| C06 | `create ""`: `error: title is required`, exit 2, nothing on stdout, no event | TKT-002, CLI-007 | PASS |
| C07 | `create "   "`: same as C06 | TKT-002 | PASS |
| C08 | `create --priority P9`: error naming `P9` and allowed values as `error: ...`, exit 2, no event | TKT-003, CLI-007 | FAILURE (pre-existing) |
| C09 | `list` on missing log: prints nothing, exit 0, file not created | CLI-006, LOG-006 | PASS |
| C10 | `list` line format `#<id> [<priority>] <state> <title>`, state padded to 8 | CLI-006 | FAILURE |
| C11 | `list` includes closed tickets, ID ascending | TKT-013 | PASS |
| C12 | `list` appends nothing | LOG-001 | PASS |
| C13 | Assign open ticket: `#1 assigned -> dana`, list shows `assigned` | CLI-004, TKT-006 | PASS |
| C14 | Assign again replaces assignee, one event per assign | TKT-006, LOG-001 | PASS |
| C15 | Assign empty / whitespace assignee: `error: assignee is required`, exit 2, no event | TKT-007 | PASS |
| C16 | Assign a closed ticket: `error: ticket <id> is closed`, no event, ticket unchanged | TKT-008, tickets.md "moves forward only" | FAILURE |
| C17 | Assign unknown ID: `error: no ticket 99`, exit 2 | TKT-012 | PASS |
| C18 | Assign non-integer ID: usage error, exit 2, no event | CLI-009 | PASS |
| C19 | Close open ticket with valid note: `#<id> closed`, `closed` event with resolution | CLI-005, TKT-009 | PASS |
| C20 | Close an assigned ticket: closed; assignment events retained | TKT-009 | PASS |
| C21 | Close with 9-char note `duplicate`: rejected with `resolution note must be at least 10 characters` | TKT-010 | FAILURE |
| C22 | Close with 8-char note `resolved`: rejected, same message | TKT-010 | PASS |
| C23 | Close with exactly 10 chars `abcdefghij`: accepted | TKT-010 | PASS |
| C24 | Close with `   duplicate   ` (9 after trim): rejected | TKT-010 | FAILURE |
| C25 | Close twice: `error: ticket 1 is already closed`, exit 2, no event | TKT-011 | PASS |
| C26 | Close unknown ID: `error: no ticket 99` | TKT-012 | PASS |
| C27 | Close non-integer ID `1.5`: usage error, exit 2 | CLI-009 | PASS |
| C28 | Log path precedence: `--log` > `TICKETDESK_LOG` > `./tickets.jsonl` | CLI-002 | PASS |
| C29 | Every successful command: exit 0, empty stderr | CLI-008 | PASS |
| C30 | Corrupt log line: error names file, line number, `corrupt event`; no ticket state; `error:` format, exit 2 | LOG-007, INV-004, CLI-007 | FAILURE (pre-existing) |
| C31 | Blank and whitespace-only lines ignored on replay; append still works | LOG-005 | PASS |
| C32 | Appending leaves existing lines byte-identical | LOG-008, INV-002 | PASS |
| C33 | Every event has `at`, epoch seconds, non-decreasing | LOG-004, INV-005 | PASS |
| C34 | IDs keep rising after closes; never reused | TKT-004, INV-003 | PASS |
| C35 | `list` twice gives identical output | LOG-009 | PASS |
| C36 | `list` in a pipe (`| head -n1`, `| head -c 3`): clean output, no traceback | shell contract | PASS |
| C37 | Unicode / quotes / `<>&` in a title round-trip through `create` and `list` | edge | PASS |
| C38 | `create --help`, `close --help` work | shell contract | PASS (UX gap, see below) |
| C39 | PR claim "All tests pass locally": `make test` and `make lint` | README, PR.md, ci.yml | FAILURE |

## Non-PASS details

### C01: `--help` description is misspelled (FAILURE)

- **What was done**: `python3 -m ticketdesk.cli --help` from the repo root.
- **Expected**: a description line in correct English (the PR's one deliberate `--help` change).
- **Observed** (exit 0, structure otherwise fine):
  ```
  usage: ticketdesk [-h] [--log LOG] {create,assign,close,list} ...

  Manage support tikets from the shell.
  ```
- **Most-likely cause**: typo in the new `description=` string in `ticketdesk/cli.py` (`"Manage support tikets from the shell."`). Introduced by this PR.

### C08: unknown priority escapes as a traceback (FAILURE, pre-existing)

- **What was done**: `python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl create 'Bad prio' --priority P9`.
- **Expected** (CLI-007): `error: <message>` on stderr, exit 2. TKT-003's content requirement (name the value and the allowed values) is met.
- **Observed**: a 14-line Python traceback on stderr ending in `ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']`, exit **1**. No event appended (correct).
- **Most-likely cause**: `sla.due_at` raises `ValueError`, and `cli.main` only catches `TicketError`. This is the conflict the `TODO` under CLI-007 already records; not introduced by this PR, still what the user sees.

### C10: `list` no longer shows priority (FAILURE)

- **What was done**: create three tickets (P3, P1, P2), then `python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl list`.
- **Expected** (CLI-006): `#<id> [<priority>] <state> <title>`, e.g. `#2 [P1] open     VPN down for everyone`.
- **Observed**:
  ```
  #1 open     Printer on fire
  #2 open     VPN down for everyone
  #3 open     Café "wifi" — ñ 日本語 <tag> & stuff
  ```
- **Most-likely cause**: the PR deliberately removed `[{t.priority}]` from the `list` print in `cli.py` and deferred the replacement flag to "a later PR", without updating CLI-006. Net effect for the user: priority is now invisible through every command (no other command prints it), so a P1 and a P3 look identical in the only view the product has.

### C16: a closed ticket can be assigned, which reopens it (FAILURE)

- **What was done**: ticket #1 was created, assigned to `dana`, reassigned to `lee`, and closed with `Replaced the toner cartridge` (`list` showed `#1 closed`). Then `python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl assign 1 mallory`.
- **Expected** (TKT-008): `error: ticket 1 is closed` on stderr, exit 2, no event, `list` unchanged.
- **Observed**: stdout `#1 assigned -> mallory`, exit 0; a new line `{"assignee": "mallory", ..., "id": 1, "kind": "assigned"}` appended; `list` now shows `#1 assigned Printer on fire`. The ticket went **backwards** from `closed` to `assigned`, which tickets.md forbids ("A ticket moves forward only ... Nothing reopens a closed ticket").
- **Cascade** (verified): `close 1 'Second close of a once-closed ticket'` then succeeded with `#1 closed`, exit 0, giving ticket #1 two `closed` events in the log and silently defeating TKT-011 ("closing twice" is rejected only until someone assigns in between). `make test` fails on exactly this scenario (see C39).
- **Most-likely cause**: the PR removed the `if t.state == "closed": raise TicketError(...)` guard from `TicketService.assign`, and the replay logic sets state to `assigned` on every `assigned` event regardless of prior state. The PR describes this as "assigning a ticket now works at any point in its life", but the spec and the invariant say otherwise, and nobody surfaced the conflict.

### C21: a 9-character resolution note is accepted (FAILURE)

- **What was done**: `python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl close 2 'duplicate'` on open ticket #2.
- **Expected** (TKT-010): `error: resolution note must be at least 10 characters`, exit 2, ticket stays `open`.
- **Observed**: stdout `#2 closed`, exit 0; `list` shows `#2 closed`; log gained `{"...", "kind": "closed", "resolution": "duplicate"}`.
- **Most-likely cause**: the PR changed the check in `TicketService.close` from `< 10` to `< 9` but left the spec and the error message at 10. The PR's own stated goal ("short notes like 'duplicate' are accepted") is achieved by exactly one character and contradicts TKT-010, which was not updated. See also C22's message mismatch in Issues.

### C24: a whitespace-padded 9-character note is accepted (FAILURE)

- **What was done**: `python3 -m ticketdesk.cli --log OUTPUT_DIR/tickets.jsonl close 3 '   duplicate   '`.
- **Expected** (TKT-010): rejected; the length rule applies "after trimming surrounding whitespace", and `duplicate` is 9 characters.
- **Observed**: `#3 closed`, exit 0; the log stores the note untrimmed: `"resolution": "   duplicate   "`.
- **Most-likely cause**: same off-by-one as C21 (trimming works; the threshold is 9). Storing the padded note untrimmed is allowed by the spec as written but is worth a look (Improvements).

### C30: corrupt log line escapes as a traceback (FAILURE, pre-existing)

- **What was done**: wrote `OUTPUT_DIR/corrupt-log.jsonl` with a valid event, the line `this is not json`, and another valid event; ran `list` and `create 'should fail fast'` against it.
- **Expected** (LOG-007 + CLI-007): a single `error:` line naming the path, line 2 and `corrupt event`, exit 2, nothing on stdout, no event appended.
- **Observed**: no stdout, no event appended, and the final line of a two-part traceback does carry the right content: `ValueError: OUTPUT_DIR/corrupt-log.jsonl:2: corrupt event: Expecting value: line 1 column 1 (char 0)`. But it arrives as ~40 lines of traceback with exit **1**, for both `list` and `create`.
- **Most-likely cause**: `EventStore.replay` raises `ValueError`, not `TicketError`; same uncaught-exception gap as C08, already recorded in the CLI-007 TODO. LOG-007 and INV-004 themselves hold (fail-fast, no partial state); the CLI presentation is what fails.

### C39: the PR's "All tests pass locally" claim is false (FAILURE)

- **What was done**: `make test` and `make lint` from the repo root, as README.md instructs before pushing.
- **Expected**: both exit 0 (PR.md: "All tests pass locally"; CI runs both).
- **Observed**: `make lint` exit 0. `make test` exit 2:
  ```
  FAIL: test_assign_requires_open_ticket (test_tickets.TicketTests.test_assign_requires_open_ticket)
  AssertionError: TicketError not raised
  Ran 7 tests in 0.004s
  FAILED (failures=1)
  ```
- **Most-likely cause**: the test encodes TKT-008, which the PR removed (C16). `.github/workflows/ci.yml` runs `make lint` then `make test`, so CI would go red on this branch; the PR description was not checked against a real run.

## Missing / untested cases

- **Interrupted run (Ctrl-C mid-append)**: each command finishes in milliseconds; no deterministic way to interrupt between replay and append from the shell. Untested.
- **Installed `ticketdesk` entry point** (`pyproject.toml` `[project.scripts]`): the task fixed the surface as `python3 -m ticketdesk.cli`; the package was not installed. Untested.
- **TKT-005 due times**: no command prints the due time, so due-by-priority is unobservable from the CLI. Untested at this surface (covered only by unit tests). This is a spec/product gap: a user cannot verify an SLA the spec promises.
- **Assignee retained after close (TKT-009 "the assignee, if any, is kept")**: only indirectly observable (the `assigned` events stay in the log); no command prints an assignee. C20 passed on what is observable.
- **Concurrent writers / very large logs**: out of scope for a single-user CLI change.
- **C28 default-path leg** was run from a scratch directory (`OUTPUT_DIR/cwd-default`) with `PYTHONPATH` pointing at the repo, to avoid dropping a `tickets.jsonl` into the repo root. It passed, with that one deviation from the documented invocation.

## Issues found (by severity)

1. **Critical: closed tickets can be reopened by assigning them, and then closed again.** Refs C16, C39. Breaks TKT-008, the "moves forward only / nothing reopens a closed ticket" contract in tickets.md, and lets TKT-011 be bypassed. Introduced by this PR; the one unit test covering it fails. Needs either a product decision to change the spec (then the spec, test, and replay semantics all need to follow) or the guard restored.
2. **High: `list` output contradicts CLI-006 and hides priority entirely.** Ref C10. The spec was not updated, and no other command shows priority, so the "flag in a later PR" leaves users with no way to tell a P1 from a P3 in the meantime.
3. **High: resolution minimum is 9 in the code, 10 in the spec and in the error message.** Refs C21, C22, C24. TKT-010 not updated; the message `resolution note must be at least 10 characters` is now a lie (an 8-char note is told it needs 10, a 9-char note sails through). If the goal is to accept `duplicate`, decide the real rule (a word list? a lower minimum?) and align spec, check, and message.
4. **Medium: `--help` says "tikets".** Ref C01. Introduced by this PR; the one line it added.
5. **Medium (pre-existing, documented): unknown priority and corrupt log print tracebacks with exit 1** instead of `error: ...` with exit 2. Refs C08, C30. Already the open TODO under CLI-007; this PR neither fixes nor worsens it.
6. **Low: PR description claims tests pass; they do not, and CI would fail.** Ref C39.

## UX gaps

- Subcommand help is bare: `create --help` lists `--priority PRIORITY` with no description and no mention that only `P1`, `P2`, `P3` are accepted; `title`, `id`, `resolution` have no help text. The user learns the allowed priorities only from a traceback (C08).
- The README has no usage section at all; the only documented invocation lives in AGENTS.md, a file written for coding agents. A new human user has to guess `python3 -m ticketdesk.cli`.
- Nothing shows a ticket's assignee, priority (after this PR), resolution or due time. The log file is the only way to see them, and the product spec calls the log "a product surface", which is a stretch for a support agent.
- After `assign` on a closed ticket the output `#1 assigned -> mallory` gives no hint that anything unusual happened (C16). Even if reopening became intended, a reopen deserves to say so.
- The resolution-length error does not echo the note's actual length, so a user has to count.

## Improvements worth doing

- Decide and document the resolution rule once (TKT-010), then make the check and the message read from the same constant so they cannot drift again.
- Close the CLI-007 TODO: catch `ValueError` from the SLA and store layers in `cli.main` (or convert them to `TicketError`) so every failure is `error: ...` with exit 2. Both pre-existing tracebacks in this run come from that one gap.
- Store the resolution trimmed (C24): the spec trims only for the length check, so `"   duplicate   "` is persisted with its padding.
- Add `help=` and `choices=("P1", "P2", "P3")` to `--priority` so argparse rejects bad priorities with a usage error before the service ever sees them.
- Add a CLI-level test (AGENTS.md notes the CLI has none); every failure in this report was visible from the shell and invisible to the current suite except one.
- Make the PR template require a pasted `make test` result, since this PR's claim did not survive a single run.

## Leftover artifacts (kept for reproduction)

All under `/Users/dmitri/dev/swd-skills/evals/e2e-test/workspace/iteration-1/eval-1-cli-branch-with-spec-violations/old_skill/run-2/outputs/`:

- `tickets.jsonl` (16 events, tickets #1 to #7): the main run. Ticket #1 carries the reopen cascade (assigned x3, closed x2); #2 holds the 9-char note `duplicate`; #3 the padded note; #4 the 10-char boundary; #5 a plain close; #6 and #7 ID-continuity checks.
- `snapshot-before.jsonl`: the first 15 lines of `tickets.jsonl` before the C32 append (byte-identical prefix confirmed with `cmp`).
- `env-log.jsonl` (1 event): the `TICKETDESK_LOG` precedence check.
- `cwd-default/tickets.jsonl` (1 event): the default-path check.
- `corrupt-log.jsonl` (3 lines, line 2 invalid): the LOG-007 fixture.
- `blank-lines-log.jsonl` (6 lines, 3 events after the C31 assign): the LOG-005 fixture.
- `repo/`: left on `feature/cli-tidy`, `git diff` empty, no product file modified. The `__pycache__` directories that running the product and `make test` generated were removed so the tree matches the fixture.

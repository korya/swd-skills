# Rebase report: feature/overdue onto main

**Succeeded with adjustments.** `feature/overdue` now sits on `main` at `59f87b2`. The
plain replay broke INV-006, so the overdue check now reads the store clock. Lint passes,
and all 12 unit tests pass. Nothing was pushed.

## Three points

| Point | Commit |
|---|---|
| `curr` before the rebase, `feature/overdue` | `516b236` |
| `old_base`, the merge-base | `b3206ec` |
| `new_base`, `main` | `59f87b2` |
| `curr` after the rebase | `afc14a6` |

The branch `backup/feature-overdue-pre-rebase` points at `516b236`. Delete it when you
accept the result.

## Per-commit outcome

| Before | After | Classification | Outcome |
|---|---|---|---|
| `700aa43` feat(tickets): Add overdue detection | `74a7fb0` | Conflicting with INV-006 | Replayed with edits |
| `f05fc7a` feat(cli): Add the overdue subcommand | `ebf0ef5` | Adjusted and Extended | Replayed with edits after a conflict |
| `516b236` docs(specs): Add TKT-014 and CLI-010 | `afc14a6` | Untouched | Replayed as is |

- **`74a7fb0`.** `overdue()` read `time.time()` directly. INV-006 on `main` forbids that.
  The method now reads `self.store.clock()`. I removed the unused `now` argument, because
  a caller-supplied time also bypasses the store clock. Two new unit tests in
  `tests/test_tickets.py` use a fake clock. One of them fails when the code reads the
  system clock. I confirmed this with a temporary mutation.
- **`ebf0ef5`.** `ticketdesk/cli.py` conflicted with the `export` subcommand from `main`. I
  kept both subcommands. `overdue` now prints through the `_line()` helper from `main`,
  the same as `list`. The new guideline on `main` requires a CLI test for each subcommand.
  I added it to `tests/test_cli.py` in the same commit.
- **`afc14a6`.** The spec IDs TKT-014 and CLI-010 are still free on `main`.

The rename of `due_at()` to `deadline_for()` on `main` did not affect the branch. The
branch uses the `Ticket.due_at` field, and the rename kept that field.

## Spec and invariant check

- **TKT-014.** Open and assigned tickets past their due time are overdue. Closed tickets
  are never overdue. Unit tests and the CLI test cover both cases.
- **CLI-010.** The output uses the `list` line format, with the oldest due time first. An
  empty result prints nothing and exits 0. The CLI test covers this.
- **INV-006.** The service reads the current time only from the store clock. A search of
  `ticketdesk/` finds `time.time` only as the default clock of `EventStore`.
- **INV-001 to INV-005.** `overdue` only reads the log. It appends no event.

## Verification

- `make lint` and `make test` passed after each commit. The final run had 12 tests.
- An end-to-end run of the real CLI used a temporary log. A fresh log showed nothing
  overdue. A log with its times moved back 300,000 seconds showed both tickets in due
  order. After `close 1`, only ticket 2 stayed overdue.
- The surfaces from `main` that the branch did not touch still work. These are `list`,
  `export`, and `deadline_for` in the public names of the package.
- `debug_notes.md` was stashed under `swd-rebase-preflight-20261028-080351`. The stash
  popped clean, and the file is back as an untracked file.

## Open questions

I wrote six questions to `questions.md` and continued on the lowest-risk assumption for
each. These need your decision:

- Confirm the INV-006 fix and the removal of the `now` argument.
- Confirm that the tests belong in the feature commits.
- CLI-001 in `docs/product-specs/cli.md` still says "four subcommands". `main` already has
  five, and the branch adds a sixth. I did not edit the spec without your confirmation.

## Check by hand

- Run `ticketdesk overdue` against a real team log and compare the result with your
  expectation.
- Read the CLI-001 drift above and decide on a spec edit.
- Delete `debug_notes.md` before the merge, as the note itself asks.
- `AGENTS.md` and `docs/architecture.md` on `main` still say the CLI has no tests. They
  also name `due_at()` in the layout. This drift comes from `main`, not from the branch.

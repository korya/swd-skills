# Rebase report: feature/overdue onto main

## Headline

The rebase succeeded with adjustments. All three commits landed on `main` in their
original order. One commit needed a semantic fix because `main` added an invariant that
its code broke. The other two needed smaller edits to match conventions `main` added.
Lint and all 11 tests pass. Nothing was pushed.

## The three points

| Point | Commit |
|---|---|
| `curr` (feature/overdue before the rebase) | `47429e6` |
| `old_base` (merge-base) | `d06bbc3` |
| `new_base` (main) | `c9b8fc1` |

The branch now sits at `d460adb`. The pre-rebase tip `47429e6` stays reachable through
the reflog if you want to compare or undo.

## Per-commit outcome

| Original | Classification | Action | Now |
|---|---|---|---|
| `023139c` feat(tickets): overdue detection | Conflicting with INV-006 | replayed with edits | `e2e778a` |
| `f1a004c` feat(cli): overdue subcommand | Adjusted and Extended | replayed with edits | `1612c2b` |
| `47429e6` docs(specs): TKT-014 and CLI-010 | Untouched in text, adjusted in meaning | replayed with one edit | `d460adb` |

### The service commit broke INV-006

The original `overdue()` called `time.time()` and accepted a `now` override from the
caller. `main` added INV-006, which says a command that depends on the current time reads
it from the store's clock and never from the system clock. INV-005 and the architecture
doc also say time never comes from the caller. Git replayed the commit without a conflict
marker, so nothing in the mechanics would have caught this.

The fix reads `self.store.clock()` and drops the `now` parameter. The service already
holds the store and calls `replay()` and `append()` on it, so this crosses no new layer
boundary. A unit test in `tests/test_tickets.py` moves the fake clock past each due time
and checks the order and the exclusion of closed tickets.

### The CLI commit collided with export and needed a test

`main` added an `export` subcommand and pulled the `list` line format into a `_line`
helper. Both of the branch's hunks collided with the `export` hunks. I read both sides.
They are additive, so both subcommands stay and `overdue` prints through `_line`.

`main` also added a convention in `docs/guidelines.md`: a new subcommand ships with a
subprocess test in `tests/test_cli.py`. The branch had none. The commit now carries one.
It seeds the log with a `created` event at epoch second 1, creates a fresh ticket, and
checks that only the old one is listed.

### The specs commit names the store clock

TKT-014 said "the current time" without saying where it comes from. One sentence now
points at INV-006. CLI-010 was already consistent with CLI-006 and needed no change.

## Verification

| Check | Result |
|---|---|
| `make lint` | pass |
| `make test` | 11 tests pass, up from 9 on `main` |
| `overdue` on an empty log | prints nothing, exit 0 |
| `overdue` with two old tickets, one closed old ticket, one fresh | prints the two old ones, oldest due first |
| `list` and `export` after the rebase | unchanged output |
| `grep time.time ticketdesk/` | only the store's injectable default |

I re-read TKT-014 and CLI-010 on the rebased branch against the e2e output above. Both
hold.

## What you should still verify by hand

- Delete `debug_notes.md` before merging. It is untracked and restored exactly as you
  left it. Your note says to delete it.
- Decide on CLI-001 in `docs/product-specs/cli.md`. It still says "one of four
  subcommands". `main` added `export` and this branch adds `overdue`. The guidelines
  forbid drive-by spec edits, so I left it.
- Decide on three stale doc lines that `main` left behind. `docs/architecture.md` line
  89 lists `due_at`, which `main` renamed to `deadline_for`. `docs/architecture.md` line
  103 and `AGENTS.md` lines 102 and 116 still say the CLI has no tests and that
  `make test` runs 7 cases.
- Confirm the two judgment calls in `questions.md`. The tests live in the original
  commits rather than a separate one. The `now` override is gone rather than kept as a
  test hook.

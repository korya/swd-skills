# Rebase report: feature/overdue onto main

**Succeeded with adjustments.** `feature/overdue` now sits on `main` at `f1a3046`. Commit
1 now reads the time from the store clock, as INV-006 on main requires. Commit 2 now uses
the shared `_line` formatter and ships with a CLI test. The full suite passes with 12 tests.
Nothing was pushed.

| Point | Hash |
|---|---|
| `curr`, before | `33f377d` |
| `old_base`, the merge-base | `f94994d` |
| `new_base`, `main` | `f1a3046` |
| `curr`, after | `b7c2750` |

The original branch is kept as `backup/feature-overdue-pre-rebase` at `33f377d`. To undo
the rebase, run `git branch -f feature/overdue backup/feature-overdue-pre-rebase`.

## Per-commit outcome

| Before | After | Class | Action |
|---|---|---|---|
| `73ac6e3` feat(tickets): overdue detection | `ff5d643` | Adjusted | Replayed with edits |
| `0b53d84` feat(cli): overdue subcommand | `25443ba` | Adjusted and Extended | Replayed with edits, conflict resolved |
| `33f377d` docs(specs): TKT-014 and CLI-010 | `b7c2750` | Untouched | Replayed as is |

### Commit 1: `ff5d643` feat(tickets)

The original `overdue()` called `time.time()`. Main added INV-006 in `f1a3046`, which
forbids a direct read of the system clock. This finding fired the risk gate.

- `ticketdesk/tickets.py`: `overdue()` now calls `self.store.clock()`. The `import time`
  line is gone. The `now` parameter stays.
- `tests/test_tickets.py`: two new tests drive `overdue()` with the fake clock. They cover
  the due-time boundary, the order, closed tickets, and assigned tickets.
- A mutation check put `time.time()` back. The new test failed, so the test guards
  INV-006.

The rename of `due_at()` to `deadline_for()` in `4c26122` does not affect this commit.
`overdue()` reads the `Ticket.due_at` field, and main did not rename the field.

### Commit 2: `25443ba` feat(cli)

The commit conflicted with `097aa89` in `ticketdesk/cli.py`. Main added `export` in the
same two places. I kept both subcommands.

- `ticketdesk/cli.py`: the `overdue` branch now prints with `_line(t)`. The original
  inlined a copy of the format. CLI-010 asks for the `list` line format, and `_line` is
  now its single source.
- `tests/test_cli.py`: one new subprocess test, `test_overdue_lists_oldest_due_first`.
  Main's guideline in `f1a3046` requires a test in this file for each new subcommand. The
  test checks the empty case and a log with past events. The expected order is oldest
  due first, with closed and fresh tickets excluded.

### Commit 3: `b7c2750` docs(specs)

The commit applied cleanly. Its text is unchanged. TKT-014 and CLI-010 still match the
code after the edits above.

## Spec and invariant deviations

The rebase had one deviation, and the edit to commit 1 resolved it.

- **INV-006 on main.** The original commit 1 broke it. The rebased commit complies.

I did not edit three stale doc lines on main. The repo rules require your confirmation
for every doc change.

- **CLI-001** says there are four subcommands. Main has five with `export`. This branch
  adds `overdue` as the sixth.
- **`docs/product-specs/cli.md`** has no spec for `export`.
- **`docs/architecture.md`** still names `due_at()` in `sla.py` after the rename.

## Verification

Each rebased commit passed `make lint` and `make test` on its own. The final branch
passes both.

| Check | Result |
|---|---|
| `make lint` | Pass |
| `make test` | 12 tests, OK |
| E2E: `overdue` on an empty log | No output, exit 0 |
| E2E: `overdue` on fresh tickets | No output, exit 0 |
| E2E: `overdue` on aged tickets | Open and assigned tickets, oldest due first, closed excluded |
| E2E: `list` and `export` from main | Same output format as on main |
| E2E: create with priority `P9` | Rejected by `deadline_for()` |
| Public names in `ticketdesk.__all__` | Same as on main |

I also checked the surfaces that main changed and the branch did not touch. They are
`list`, `export`, the rename to `deadline_for()`, and the public names. Nothing broke
there.

The `P9` create still exits with a traceback. This is the open TODO under CLI-007 on
main. The rebase did not change it.

## Your uncommitted work

The tree had one untracked file, `debug_notes.md`. I stashed it under the label
`swd-rebase-preflight-20261028-080431` before the rebase. The pop after the rebase was
clean, and the file is back. Its text says "delete before merge", so remove it before you
merge.

## Verify by hand

- Read the open questions in `questions.md`. Each one names the assumption I used.
- Decide whether `overdue()` keeps its `now` parameter.
- Decide whether to update CLI-001 and the other two stale doc lines.
- Delete `backup/feature-overdue-pre-rebase` once you accept the result.

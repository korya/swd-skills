# rebase evals

Measures whether `/rebase` re-validates a branch against a base that moved, and whether its
plan and report read once. The fixture is ticketdesk with agent docs. A feature branch adds
an `overdue` subcommand. Meanwhile main renamed a function, extracted a formatter, added an
invariant the branch violates, and added a test convention.

## Layout

- `make_fixture.sh <dir>` builds the repo with `main` and `feature/overdue` and leaves an
  untracked `debug_notes.md` in the tree. `patches.py` holds the per-commit edits.
- `evals.json` holds one eval in the skill-creator benchmark format.
- `check_run.py <run-dir>` grades the mechanical assertions.

## The delta and the expected classifications

| Change on main | Effect on the branch | Expected class |
|---|---|---|
| `due_at` renamed to `deadline_for` | branch calls nothing by that name, but the import region conflicts | Adjusted |
| `_line` extracted, `export` added | `overdue` should reuse `_line`; `cli.py` conflicts textually | Adjusted or Extended |
| INV-006: time from the store clock | branch calls `time.time()` directly | Conflicting |
| CLI tests in `tests/test_cli.py` | `overdue` needs a subprocess test | Extended |

The dirty tree tests the stash path. The INV-006 conflict tests the risk gate. The
`_line` extraction tests whether the replay reads both sides.

## Running

Run with the skill-creator benchmark flow. Grade the prose with `scripts/prose-lint.py`.

# Rebase report: feature/overdue onto main

**Headline: rebased with adjustments.** All three commits replayed; one needed a semantic
fix (INV-006), one needed conflict resolution and a convention catch-up, one was untouched.
Lint and all 12 tests pass on the result; the e2e run through the binary matches TKT-014
and CLI-010. Nothing was pushed.

| Point | Commit |
|---|---|
| `curr` (before) | 3e7ddfe, kept as `feature/overdue.pre-rebase` |
| `old_base` | b61ba70 (merge-base) |
| `new_base` | 9d38390 (`main`) |
| `feature/overdue` (after) | dc87663 → 7397982 → 5ac4755 on top of 9d38390 |

## Per-commit outcome

| Original | Classification | Outcome |
|---|---|---|
| e6cdf67 feat(tickets): overdue detection | **Conflicting** with INV-006 (new on main): the service defaulted `now` to `time.time()`. | **Replayed with edits** as 5ac4755. `overdue()` now reads `self.store.clock()`; the `now` parameter and `import time` are gone. Added two service tests in `tests/test_tickets.py` (filter incl. assigned, closed excluded, oldest-due-first order) through the existing fake clock. Message cites TKT-014 and INV-006. |
| e9e90a3 feat(cli): overdue subcommand | **Adjusted** (main extracted `_line` and added `export` on both hunks the commit touches) + **Extended** (new convention: each subcommand has a subprocess test in `tests/test_cli.py`). | **Replayed with edits** as 7397982. Both conflicts resolved by reading both sides: `export` and `overdue` coexist, `overdue` prints via `_line(t)` instead of a duplicate format string. Added `test_overdue_lists_only_past_due_tickets`, seeding a past-due event in the log because the binary runs on the real clock. Message cites CLI-010. |
| 3e7ddfe docs(specs): TKT-014, CLI-010 | **Untouched** | **Replayed as-is** as dc87663. |

Dropped: nothing. `main` does not already solve overdue detection.

## Spec and invariant deviations and how they were resolved

- **INV-006 vs. `time.time()`** (the risk-gate stop). Resolved by option (a) from
  `questions.md`: one time source, the store clock. This is the only behavioural change
  against the branch as authored; a caller can no longer pass `now`, and nothing on the
  branch did.
- **Guidelines: "new logic ships with tests" and the CLI-test convention.** The branch had
  no tests at all. Added inside the feature commits (see Q2 in `questions.md`).
- **TKT-014 / CLI-010 restated and verified on the result:** open or assigned ticket with
  due time earlier than now is listed, closed never; `list` line format, oldest due first;
  nothing overdue prints nothing and exits 0. Unit tests cover the rules, the CLI test and
  the manual e2e run cover the wiring.

## Delta-touched surfaces the branch did not touch (checked, not assumed)

- `export` (new on main): still prints one JSON object per line with `due_at`; verified
  by `test_export_is_json_lines` and the e2e run.
- `list` via `_line`: unchanged output, verified by `test_create_and_list` and e2e.
- `deadline_for` rename: the branch never referenced `due_at()` the function, only the
  `Ticket.due_at` field, so no rename fallout. `grep` finds no `due_at(` call anywhere.
- `python3 -m ticketdesk.cli bogus` still gives usage + exit 2, now listing six commands.

## Working tree

`debug_notes.md` was stashed under `swd-rebase-preflight-20261027-082925` before history
moved and popped cleanly after; it is back, untouched. It says "delete before merge": that
deletion is yours to make.

## Please verify by hand

1. **Q1 in `questions.md`:** you are fine with `overdue()` losing its `now` parameter.
2. **CLI-001 in `docs/product-specs/cli.md`** still says "one of four subcommands". It was
   already stale on `main` after `export`; with `overdue` it is now off by two, and there is
   no CLI spec for `export` at all. Doc edits need your sign-off, so I left it. The same
   applies to the "CLI is not covered by tests" lines in `AGENTS.md`,
   `docs/architecture.md`, and `docs/guidelines.md`, and to the `due_at`/`SLA_HOURS`
   public-names line in `docs/architecture.md` (should read `deadline_for`). All of those
   are `main`'s debt, not this branch's.
3. Delete `feature/overdue.pre-rebase` once you are happy with the new history.
4. `debug_notes.md`: delete or keep.

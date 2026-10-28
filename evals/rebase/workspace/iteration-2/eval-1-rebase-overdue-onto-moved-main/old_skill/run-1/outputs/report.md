# Rebase report: feature/overdue onto main

**Succeeded with adjustments.** `feature/overdue` now sits on `main` at `b8411e7`. Commit 1 now reads the store clock to comply with INV-006. Commit 2 resolves a conflict with the new `export` command. Both commits gained tests. Lint and all 14 unit tests pass, and nothing was pushed.

## Three points

| Point | Commit |
|---|---|
| `curr` before (feature/overdue) | `638b218` |
| `old_base` (merge-base) | `d29de19` |
| `new_base` (main) | `b8411e7` |
| `curr` after (feature/overdue) | `68c1635` |

The old branch tip is kept as `backup/feature-overdue-pre-rebase` at `638b218`.

## Per-commit outcome

| Before | After | Class | Outcome |
|---|---|---|---|
| `4348871` feat(tickets): overdue detection | `f58a7ae` | Conflicting | Replayed with edits. `overdue()` reads `self.store.clock()` instead of `time.time()`. Added 3 service tests. |
| `ec61e0d` feat(cli): overdue subcommand | `56c75cf` | Adjusted and Extended | Text conflict with `export` resolved by keeping both. Lines print with `_line(t)`. Added 2 subprocess tests in `tests/test_cli.py`. |
| `638b218` docs(specs): TKT-014, CLI-010 | `68c1635` | Untouched | Replayed as is. The patch is byte-identical. TKT-014 and CLI-010 are free IDs on main. |

## Deviations and how I resolved them

Two of the three new commits on main forced edits to the branch. The rename forced none.

- **INV-006, store clock (`b8411e7`).** The original `overdue()` called `time.time()`. That breaks INV-006. The edited version reads the store clock when the caller passes no `now`. The new test `test_overdue_reads_the_store_clock` fails if `time.time()` comes back. I confirmed this with a temporary mutation.
- **`_line` and `export` (`2606afd`).** Both sides added a subparser and a branch at the same lines. I kept both commands. CLI-010 requires the `list` line format, so `overdue` now calls the shared `_line` helper.
- **CLI test convention (`b8411e7`).** A new subcommand must ship with its test in `tests/test_cli.py`. Commit 2 now does. The guideline says "one test per subcommand". I added two, one for the listing and one for the empty case.
- **Rename of `due_at()` to `deadline_for()` (`e94fdaf`).** No effect on the branch. The branch reads the `Ticket.due_at` field, which main kept.

Main does not already solve the overdue problem. No code or spec on main mentions overdue tickets.

## Verification

| Check | Result |
|---|---|
| `make lint` after each commit | Pass |
| `make test` after each commit | Pass. 12, then 14, then 14 tests. |
| `make test` on main before the rebase | Pass, 9 tests |
| System-clock reads in `ticketdesk/` | Only the default `clock=time.time` in `store.py` |

I also ran an e2e session against a temporary log with `python3 -m ticketdesk.cli`:

- `overdue` with only fresh tickets printed nothing and exited 0.
- A ticket dated 1970 appeared in `overdue` in the `list` line format.
- After `close`, the same ticket left the `overdue` output.
- `list`, `export`, and an unknown subcommand still behave as before. Usage now lists `overdue`.
- `ticketdesk.deadline_for` works and `ticketdesk.due_at` is gone, as main intends.

TKT-014 and CLI-010 hold on the result. Overdue means open or assigned and past due. Closed tickets never appear. Output is oldest due first in the `list` format. An empty result prints nothing and exits 0.

## Your working tree

The untracked `debug_notes.md` was stashed as `swd-rebase-preflight-20261028-080351` before the rebase. The stash popped cleanly afterwards. The file is back in the tree, untracked and unchanged. Its own text asks you to delete it before merge.

## What you should still check by hand

- Read `questions.md` next to this report. It lists the approvals I assumed in your absence.
- Approve or revert the INV-006 edit in `f58a7ae`.
- Decide whether to update stale docs on main. I did not edit them because the repo rules require your confirmation:
  - CLI-001 in `docs/product-specs/cli.md` lists four subcommands. There are now six.
  - Main has no CLI spec for `export`.
  - `docs/architecture.md` still names `due_at()` in `sla.py`.
  - `AGENTS.md` still says "7 unittest cases" and "Not covered by tests: the CLI".
- Delete `backup/feature-overdue-pre-rebase` once you are happy with the result.
- Push the branch yourself. The repo has no remote. A push over an existing remote branch needs a force push, because history changed.

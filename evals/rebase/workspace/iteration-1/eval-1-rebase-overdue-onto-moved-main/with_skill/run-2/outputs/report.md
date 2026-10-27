# Rebase report: feature/overdue onto main

Succeeded with adjustments. `feature/overdue` now sits on `main` at `77a0ab7`, three commits
ahead, and every one of them is lint-clean and test-clean. Two of the three commits needed
edits because main added INV-006 and extracted the `_line` formatter while your branch
waited. Nothing was pushed.

## Three points

| Point | Before | After |
|---|---|---|
| curr `feature/overdue` | `33f6a20` | `77a0ab7` |
| old_base | `d06bbc3` | `f94de3a` (main) |
| new_base `main` | `f94de3a` | `f94de3a` |

The old tip stays reachable as `backup/feature-overdue-pre-rebase`. Delete that branch
once you are happy with the result.

## Per-commit outcome

| Original | Class | Outcome | New |
|---|---|---|---|
| `023139c` feat(tickets): overdue detection | Adjusted | Replayed with edits. `overdue()` reads the store clock, no `now` argument, plus a fake-clock test. | `d1a13bb` |
| `4acb140` feat(cli): overdue subcommand | Adjusted and Extended | Replayed with edits. Conflict with `export` resolved by hand, output through `_line()`, plus a subprocess test. | `07638fb` |
| `33f6a20` docs(specs): TKT-014 and CLI-010 | Untouched | Replayed byte for byte. `git range-diff` shows it as equal. | `77a0ab7` |

Author and author date are preserved on all three. The two edited commits carry a
co-author trailer and a body that names the spec IDs and the reason for the edit.

## Deviations from the original branch and why

INV-006 is the one invariant the plain replay would have broken. Main added it in
`f94de3a`. It says a command that depends on the current time reads it from the store
clock, never from the system clock directly. The original `overdue()` called
`time.time()`. Now it calls `self.store.clock()`. The behavior TKT-014 describes is
unchanged, and the production clock is still `time.time` through the store default.

The `now=None` argument is gone. No caller used it, and INV-005 says time never comes
from the caller. The questions file records this as an assumption you can overturn.

The CLI command prints through `_line()` instead of its own copy of the format string.
Main extracted that helper in `cd4c4a1` for `list` and `export`. Keeping a copy would
have reversed that refactor and risked the formats drifting apart.

Two tests were added, one per edited commit. Your branch shipped none, and main's new
guideline says a subcommand ships with a subprocess test in `tests/test_cli.py`. The
service test drives the fake clock 100 hours ahead and checks order and the closed case.
The CLI test checks the empty case and a hand-written epoch ticket.

## Verification

| Check | Result |
|---|---|
| `make lint` on main before, and after each commit | clean |
| `make test` on main before | 9 passed |
| `make test` after the final commit | 11 passed |
| e2e: `overdue` on a missing log | nothing printed, exit 0 |
| e2e: `overdue` with only fresh tickets | nothing printed, exit 0 |
| e2e: two hand-written past-due tickets | printed oldest due first in the `list` format |
| e2e: close one of them, run `overdue` again | only the open one printed |
| e2e: `list` and `export`, surfaces main touched and the branch did not | unchanged output |
| e2e: unknown subcommand | usage error, exit 2, per CLI-001 |
| `ticketdesk.deadline_for` import after main's rename | works |
| stash `swd-rebase-preflight-20261027-083140` | popped clean, `debug_notes.md` restored |

TKT-014 and CLI-010 still hold on the result. An open or assigned ticket past its due time
is overdue. A closed one never is. The CLI prints them oldest due first in the `list` line
format. Nothing overdue prints nothing with exit 0.

## What you should still verify by hand

- `debug_notes.md` is back in the working tree, untracked. Its own text says to delete it
  before merge. I did not delete your file.
- CLI-001 in `docs/product-specs/cli.md` still says the command takes four subcommands.
  It now takes six. Main's `export` already made it stale and has no CLI spec of its own.
  Doc changes need your confirmation, so I left it.
- `AGENTS.md` says `make test` runs 7 cases and that the CLI has no tests. Both were stale
  before this rebase and are more so now. Same for the `due_at` names in the project layout
  of `docs/architecture.md`.
- The dropped `now` argument on `overdue()`. If you want an override for callers, say so
  and I will add it back.
- `backup/feature-overdue-pre-rebase` can be deleted once you accept the new history.

The questions I would have asked are in `questions.md` next to this file. Each one records
the assumption I proceeded on at the risk gate and before the plan.

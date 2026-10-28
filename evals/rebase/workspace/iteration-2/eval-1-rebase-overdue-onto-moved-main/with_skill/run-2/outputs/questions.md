# Questions for Dmitri

Nobody was available during this run. Each question below states what I would have asked,
the assumption I used, and the option I picked.

## Three points

| Point | Ref | Hash |
|---|---|---|
| `curr` | `feature/overdue` | `638b2185ef94891efb727f204d3835303a33a24d` |
| `old_base` | merge-base of `feature/overdue` and `main` | `d29de1929f17710d584d168a69ecd5de508b0652` |
| `new_base` | `main` | `b8411e74fff5db11552db15eb52395602b52b026` |

## Q1. Preflight: does `debug_notes.md` relate to this branch?

The tree had one untracked file, `debug_notes.md`. It says "notes while debugging the
due-time math. delete before merge". I stashed it with `--include-untracked` under the
label `swd-rebase-preflight-20261028-080352`.

- **Assumption:** the notes belong to this branch and you want them back after the rebase.
- **Choice:** restore them untracked. I do not commit them and I do not delete them.

## Q2. Risk gate: the service commit breaks INV-006, which `main` added

Commit `4348871` reads the system clock in `TicketService.overdue()` through `time.time()`.
Commit `b8411e7` on `main` added INV-006. INV-006 says a command reads the current time
from the store's clock, never from the system clock directly. A replay as is breaks this
invariant.

The options:

- **A. Edit `4348871` in place.** `overdue()` reads `self.store.clock()`. The optional
  `now` parameter goes away, because the injectable store clock now covers tests. Add a
  unit test through the fake clock in `tests/test_tickets.py`.
- **B. Replay as is, then add a fix commit.** History keeps one commit that breaks INV-006.
- **C. Stop and wait for you.**

- **Assumption:** the intent of `4348871` is "list overdue tickets". The time source is a
  detail, so option A keeps the intent.
- **Choice:** option A. It has the lowest risk. No commit on the branch breaks INV-006, and
  the behavior stays the same for the CLI.
- **Open point:** do you want to keep `now=None` as a test hook? I removed it because a
  caller-supplied time is a second source of time beside the store clock.

## Q3. Plan: the CLI commit must ship a CLI test and should use `_line`

`main` changed two things that `ec61e0d` depends on:

- Commit `2606afd` extracted the list line formatter into `_line(t)`. `ec61e0d` copies the
  f-string. CLI-010 says `overdue` prints "in the `list` line format".
- Commit `b8411e7` added a guideline: "A new subcommand ships with its test in
  `tests/test_cli.py`".

- **Assumption:** both are in scope for the rebase.
- **Choice:** edit `ec61e0d` in place. The `overdue` branch calls `_line(t)`. The commit
  adds `test_overdue_lists_oldest_due_first` to `tests/test_cli.py`. The test writes a log
  with old timestamps, so the result does not depend on the date.

## Q4. Docs: I did not touch drift that already exists on `main`

These docs are stale on `main` before the rebase. The repo rules say a doc change needs
your confirmation, so I only report them.

- CLI-001 lists four subcommands. `main` already has `export`, and the branch adds
  `overdue`. Should CLI-001 name six subcommands?
- No spec describes `export`. Should it get a CLI spec ID?
- `AGENTS.md` says `make test` runs 7 cases and that the CLI has no tests. `main` already
  runs 9, and after the rebase it runs 11.
- `docs/architecture.md` still names `due_at()` in `sla.py`. `main` renamed it to
  `deadline_for()`.

- **Assumption:** these belong in a separate docs change that you approve.
- **Choice:** leave them as they are.

## The plan I used

| Commit | Class | Action |
|---|---|---|
| `4348871` feat(tickets): overdue detection | Conflicting with INV-006 | Replay with edits: store clock, unit test |
| `ec61e0d` feat(cli): overdue subcommand | Adjusted and Extended | Replay with edits: `_line`, CLI test, resolve the conflict with `export` |
| `638b218` docs(specs): TKT-014, CLI-010 | Untouched | Replay as is |

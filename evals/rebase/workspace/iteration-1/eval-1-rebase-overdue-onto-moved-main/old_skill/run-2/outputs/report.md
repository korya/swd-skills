# Rebase report: `feature/overdue` onto `main`

## Headline

**Succeeded with adjustments.** All three commits are replayed on `main`; two needed edits
because `main` moved underneath them. `make lint && make test` pass (13 tests, up from 9 on
`main`), and the CLI was exercised end to end. Nothing was pushed. The pre-rebase branch is
kept at `backup/feature-overdue-pre-rebase` (`eebcce1`).

Three points: curr `eebcce1`, old_base `a131d95`, new_base `d6f87f7` (`main`).

```
before                                   after
a131d95 ─┬─ 60dfc62 ─ e7ab456 ─ d6f87f7   main    a131d95 ─ 60dfc62 ─ e7ab456 ─ d6f87f7 ─┐
         └─ 976e4b3 ─ 64bfd34 ─ eebcce1   feature                                       1d6abda ─ 76ea8a9 ─ a0ec58e  feature/overdue
```

## Per-commit outcome

| Original | Class | Action | Result |
|---|---|---|---|
| `976e4b3` feat(tickets): overdue detection | **Conflicting** with INV-006 (new on `main`): read `time.time()` directly | replay-with-edits | `1d6abda`: `overdue()` reads `self.store.clock()`; the `now=None` override and the local `import time` are gone; two service tests added in `tests/test_tickets.py` |
| `64bfd34` feat(cli): overdue subcommand | **Adjusted** (textual conflict with `export` + `_line` in `cli.py`) and **Extended** (new CLI test convention) | replay-with-edits | `76ea8a9`: both subcommands kept; `overdue` prints through `_line(t)` (CLI-010: "the `list` line format"); two subprocess tests added in `tests/test_cli.py` |
| `eebcce1` docs(specs): TKT-014, CLI-010 | **Untouched** (`tickets.md`, `cli.md` unchanged on `main`; IDs still the next free numbers) | replay as-is | `a0ec58e`, clean |

Not already solved on `main`: nothing overdue-related exists there. The `due_at` to
`deadline_for` rename did not affect the branch: it only reads the `Ticket.due_at` field,
which kept its name.

## Spec and invariant deviations, and how they were resolved

- **INV-006 (time from the store clock).** The branch pre-dates the invariant and broke it.
  Resolved by reading `self.store.clock()`. I also dropped the `now` parameter rather than
  keeping it as an override: no caller used it, and a caller-supplied time is exactly what
  INV-006 and `architecture.md` ("never from the caller") rule out. See `questions.md` Q1
  if you would rather keep the override.
- **Guideline "CLI tests" (new on `main`).** A new subcommand ships with a subprocess test in
  `tests/test_cli.py`. Added `test_overdue_prints_tickets_past_due_in_list_format` (hand-
  written log with `at: 1`, closed ticket excluded) and
  `test_overdue_prints_nothing_when_nothing_is_overdue`.
- **"Every module ships with tests" (pre-existing).** The original service commit had no test.
  Added `test_overdue_lists_open_tickets_past_due_oldest_first` and
  `test_overdue_excludes_closed_tickets` through the injected `Clock`, which is also the
  evidence that the clock now comes from the store.
- **Commit messages** for the two edited commits gained a paragraph on the adjustment and the
  spec IDs (`guidelines.md` "Reference spec IDs"). Subjects unchanged.

The working tree had an untracked `debug_notes.md`; it was stashed under
`swd-rebase-preflight-20261027-082920`, restored cleanly after the rebase, and is still
untracked (its own text says "delete before merge").

## Verification done

- `make lint && make test` on `main` before moving anything (9 tests OK) and after each
  replayed commit (11, 13, 13 OK).
- E2E, fresh log: `create` x2, `assign`, `overdue` prints nothing, exit 0.
- E2E, aged log (`at: 1`): `overdue` prints `#1 [P1] open     Printer` then
  `#3 [P2] assigned Keyboard` (oldest due first; closed `#2` excluded); `list` and `export`
  unchanged from `main`; unknown subcommand still exits 2.
- `grep` confirms no `time.time` / `import time` left in `tickets.py` or `cli.py`.
- Original acceptance criteria restated: TKT-014 (open or assigned, past due, closed never)
  and CLI-010 (list line format, oldest due first, nothing when nothing is overdue) hold,
  both by test and by the runs above.

## What you should still verify by hand

1. **Q1 in `questions.md`:** keeping vs dropping the `now` parameter on `overdue()`.
2. **CLI-001 is stale on `main`:** it still says "one of four subcommands" although `export`
   (and now `overdue`) exist, and `export` has no CLI spec at all. Pre-existing drift; I did
   not edit specs beyond what the branch already did. Worth a follow-up with your sign-off.
3. **TKT-014 wording:** consider adding "the current time comes from the store clock, see
   INV-006" so the spec and the invariant point at each other (needs your confirmation).
4. **Other stale statements on `main`, not touched here:** `AGENTS.md` "Not covered by
   tests: the CLI", `architecture.md` "The CLI is not covered by tests today", and the TODO
   in `guidelines.md` all pre-date `tests/test_cli.py`.
5. Delete `debug_notes.md` and `backup/feature-overdue-pre-rebase` when you are happy.

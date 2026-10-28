# Rebase report: `feature/overdue` onto `main`

**Succeeded with adjustments.** The branch now sits on `main` at `8de0f68` with four commits. Two commits needed edits, and one new commit adds tests. Lint passes and all 11 unit tests pass. Nothing was pushed.

The main adjustment fixes an invariant break. Main added INV-006 after the branch started. It says time-dependent commands read the store clock, never the system clock. The original `overdue()` called `time.time()`. It now reads `self.store.clock()`.

Nobody was available to approve this edit at the risk gate. The question and my assumption are in `questions.md`.

## Three points

| Point | Commit |
|---|---|
| `curr` (`feature/overdue`, before) | `638b218` |
| `old_base` (merge-base) | `d29de19` |
| `new_base` (`main`) | `8de0f68` |
| `curr` (after) | `8fde3f4` |

The old tip is kept as `backup/feature-overdue-pre-rebase` at `638b218`.

## Per-commit outcome

| Old | New | Class | Action |
|---|---|---|---|
| `4348871` feat(tickets): overdue detection | `63e827a` | Conflicting with INV-006 | Replayed with an edit. The default time comes from `self.store.clock()`. `import time` is gone. |
| `ec61e0d` feat(cli): overdue subcommand | `2c3dddd` | Adjusted | Resolved a text conflict with `export`. The output goes through the shared `_line()` helper. |
| `638b218` docs(specs): TKT-014, CLI-010 | `4a0792f` | Untouched | Replayed as is. The patch is identical. |
| none | `8fde3f4` test(overdue) | Extended | New commit with one CLI test and one service test. |

## What changed on main

Main added three commits since the branch started.

- `e94fdaf` renamed `sla.due_at()` to `deadline_for()`. The branch uses only the `Ticket.due_at` field, which kept its name. No edit was needed.
- `2606afd` added `export` and the `_line()` helper in `cli.py`. This caused the text conflict in `ec61e0d`.
- `8de0f68` added INV-006 and a rule in `docs/guidelines.md`. The rule says a new subcommand ships with its test in `tests/test_cli.py`.

## Conflict resolution in `cli.py`

Both sides added a subparser and an `elif` branch at the same place. I kept both commands. `export` stays as on main. `overdue` now prints through `_line()` instead of a copy of the format string. The output is the same as before, and `overdue` cannot drift from `list` now.

## Spec and invariant deviations

The table shows each rule the branch touches and how the result meets it.

| Rule | Before the rebase | After the rebase |
|---|---|---|
| INV-006 | Broken. `overdue()` read the system clock. | Met. `overdue()` reads the store clock. |
| CLI test rule in `docs/guidelines.md` | No CLI test for `overdue`. | Met. `test_overdue_lists_past_due_oldest_first` in `tests/test_cli.py`. |
| TKT-014 | Met. | Met. The service test checks open, assigned, and closed tickets against a fake clock. |
| CLI-010 | Met. | Met. The CLI test checks the empty case, the order, and the line format. |

The new service test fails when `overdue()` reads the system clock. I checked this on a copy of the package with the old clock call put back.

## Verification

I ran `make lint` and `make test` at each commit stop. Each stop passed.

Final run on the branch tip:

- `make lint` passed.
- `make test` ran 11 tests, all OK. Main had 9.
- An end-to-end run with a temporary log passed. It ran `create`, `assign`, `close`, `overdue`, `list`, and `export`. `overdue` printed nothing for fresh tickets. It printed `#3 [P1] open     Old P1` after I appended an old event.

I also checked the surfaces that main changed and the branch did not. `list` and `export` print the same output as on main. An unknown subcommand still exits with code 2. The usage line now names `overdue`.

## Your uncommitted file

`debug_notes.md` was untracked before the rebase. I stashed it under the label `swd-rebase-preflight-20261028-080353` and restored it after. The pop was clean. The file asks to delete it before merge. I did not delete it.

## Verify by hand

- Read the INV-006 edit in `63e827a`. Confirm you want the edit inside the original commit.
- Decide on CLI-001. It still says `ticketdesk` takes four subcommands. Main has five, and this branch makes six. I did not edit the spec without your confirmation.
- Decide on stale docs on main. `docs/architecture.md` and `AGENTS.md` still name `due_at()` in `sla.py`. `AGENTS.md` still says the CLI has no tests and that `make test` runs 7 cases.
- Note the known CLI-007 gap. An unknown priority still ends in a traceback. The branch did not change this.
- Delete `debug_notes.md` and the backup branch when you accept the result.

## Questions

Nobody was available to answer questions. The open questions and my assumptions are in `questions.md` next to this report.

# Questions I would have asked before the rebase

Nobody was available, so I made each call myself and picked the lowest-risk option. Each
question below names the assumption I used. You can still change any of them, because
the original branch is kept as `backup/feature-overdue-pre-rebase` at `33f377d`.

## Risk gate: commit 1 breaks INV-006 on main

Commit `73ac6e3` reads the current time with `time.time()`. Main added INV-006 in
`f1a3046`. INV-006 says a command reads the current time from the store clock, never from
the system clock. A plain replay would land a commit that breaks an invariant.

The options were these:

- **A. Edit commit 1 to call `self.store.clock()`.** The intent of the commit stays the
  same. History never shows the violation.
- **B. Replay commit 1 as it is and add a fix commit after it.** History keeps one commit
  that breaks INV-006.
- **C. Stop and leave the branch as it is.**

Question: do you accept option A?

Assumption: yes. I used option A. It keeps the intent of the commit and keeps every commit
on the branch compliant with INV-006.

## Keep the `now` parameter on `overdue()`

The original `overdue(self, now=None)` lets a caller pass the time. INV-006 does not ban
this, and no caller uses it.

Question: should I remove the parameter so the store clock is the only source of time?

Assumption: keep it. Removing it changes the API that the commit introduced, and that
change is yours to make.

## Tests that the original branch did not have

Main added a guideline in `f1a3046`: "A new subcommand ships with its test in
`tests/test_cli.py`." The guidelines also require tests for every module. The original
branch added no tests.

Question: should I add the tests inside the original commits, or as separate commits?

Assumption: inside the original commits. The CLI test goes into commit 2, because the
guideline ties the test to the subcommand. The service test goes into commit 1, because it
proves the INV-006 edit. Each test keeps the intent of its commit.

## Spec drift that I did not fix

Main has three stale doc lines that the branch does not touch. The guidelines say every
doc change needs your confirmation, so I did not edit them.

- `docs/product-specs/cli.md` CLI-001 says there are four subcommands. Main already has
  five with `export`, and this branch adds `overdue` as the sixth.
- `docs/product-specs/cli.md` has no spec for `export`.
- `docs/architecture.md` still names `due_at()` in `sla.py` after the rename to
  `deadline_for`.

Question: should I update CLI-001 in commit 3, and fix the other two lines in a separate
commit?

Assumption: no edits. The report lists all three items.

## The untracked file `debug_notes.md`

The tree had one untracked file, `debug_notes.md`. It says "delete before merge".

Question: does this file relate to the rebase, and should it stay?

Assumption: it is your personal note and does not relate to the rebase. I stashed it under
the label `swd-rebase-preflight-20261028-080431` and restored it after the rebase. I did
not delete it.

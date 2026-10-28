# Questions for the rebase of feature/overdue onto main

Nobody was available during the run. Each question below shows where the skill stops for
your answer, the assumption I took, and the option I picked.

## Step 0: uncommitted work

The tree held one untracked file, `debug_notes.md`. It holds one line: "notes while
debugging the due-time math. Delete before merge."

**Question.** Does this file relate to the overdue work?

**Assumption.** It relates to the overdue work, but it stays out of every commit.

**Action.** I stashed it under the label `swd-rebase-preflight-20261028-080432`. I restore
it after the rebase.

## Step 5: risk gate

The replay of commit `822ed1d` breaks INV-006, which main added in `280060f`. INV-006
says that a command reads the current time from the store clock, never from the system
clock. `TicketService.overdue()` calls `time.time()` when the caller passes no `now`.

**Question.** How do you want to resolve the conflict with INV-006?

The options:

- **A. Adjust the commit.** `overdue()` reads `self.store.clock()` when the caller passes
  no `now`. The feature and its signature stay the same. INV-006 holds.
- **B. Replay as is.** The commit keeps `time.time()`. This breaks INV-006 and needs your
  explicit confirmation, per `AGENTS.md`.
- **C. Stop.** I leave the branch as it is until you decide.

**Assumption.** You want the feature on main without a broken invariant.

**Action.** I took option A, the lowest-risk option.

## Step 7: plan questions

**Question 1.** Must `overdue()` keep its `now` parameter?

The parameter lets a caller pass a time that does not come from the store clock. The CLI
never passes it. A test can inject a fake clock into the store instead. I kept the
parameter, because the removal changes the API of the commit. Remove it if you want
INV-006 enforced by the signature.

**Question 2.** May I add the tests that the guidelines require?

The guidelines on main say that a new subcommand ships with its test in
`tests/test_cli.py`. The branch had no tests for the service method or the subcommand.

- **Assumption.** Yes. Tests change no product behavior.
- **Action.** I added service tests to `822ed1d` and a CLI test to `a235e66`.

**Question 3.** Must CLI-001 list the new subcommand?

CLI-001 on main says that `ticketdesk` takes four subcommands. Main already has five with
`export`, and the branch adds a sixth, `overdue`. The repo rules say that a spec change
needs your confirmation.

- **Assumption.** No drive-by spec edit.
- **Action.** I did not change CLI-001. The report lists it as a follow-up.

**Question 4.** May I fix the stale docs on main?

`docs/architecture.md` still names `due_at()` in `sla.py`. Main renamed it to
`deadline_for()`. `AGENTS.md` still says "7 unittest cases" and "Not covered by tests: the
CLI".

- **Assumption.** These are main's own debts, not part of this branch.
- **Action.** I did not change them. The report lists them.

# Questions for Dmitri

Nobody was available during this run. Each question below states the assumption I used and
why it is the lowest-risk option. The rebase continued on these assumptions.

## Risk gate (step 5)

The plain replay of `feature/overdue` breaks INV-006, which `main` added after the branch
started. `TicketService.overdue()` reads the system clock with `time.time()`. INV-006 says a
command that depends on the current time reads it from the store clock.

Options:

1. Replay with an edit: `overdue()` reads `self.store.clock()`. The feature and its
   behavior stay the same.
2. Replay as is and amend INV-006 to allow the system clock. This changes an invariant,
   which the repo docs forbid without your confirmation.
3. Stop the rebase and leave the branch as it is.

Question 1. Do you accept option 1?

Assumption: yes. Option 1 keeps both the feature and the invariant. It changes one line of
logic. I put the edit in the same commit, because it keeps the intent of that commit.

Question 2. Can I remove the optional `now` argument of `overdue()`?

Assumption: yes. No caller passes `now`. A caller-supplied time bypasses the store clock,
which INV-006 forbids. Tests inject time through `EventStore(clock=...)` instead, the same
way `tests/test_tickets.py` does today.

## Plan (step 8)

Question 3. Do you approve this plan?

| Commit on the branch | Classification | Action |
|---|---|---|
| `700aa43` feat(tickets): Add overdue detection to the service | Conflicting (INV-006) | Replay with edits. Read the store clock. Add unit tests in `tests/test_tickets.py`. |
| `f05fc7a` feat(cli): Add the overdue subcommand | Adjusted and Extended | Replay with edits. Use the `_line()` helper from `main`. Add the `overdue` test to `tests/test_cli.py`. |
| `516b236` docs(specs): Add TKT-014 and CLI-010 | Untouched | Replay as is. The IDs are still free on `main`. |

Assumption: approved. The risk is low. The branch has three small commits, and every edit
is local to the code that the branch adds.

## Tests in the same commit (step 8)

Question 4. Do the new tests go in the feature commits or in a separate commit?

Assumption: in the feature commits. The new guideline on `main` says a new subcommand ships
with its test in `tests/test_cli.py`. A separate commit would leave one commit with a
subcommand and no test.

## Out of scope (step 6)

Question 5. Do you want me to update CLI-001?

CLI-001 in `docs/product-specs/cli.md` says the command takes four subcommands. On `main`
there are already five, because `main` added `export` without an update to CLI-001. The
branch adds a sixth, `overdue`.

Assumption: no edit. The repo docs forbid spec changes without your confirmation. The
report lists this drift for you to fix by hand.

## Uncommitted file (step 0)

Question 6. Is `debug_notes.md` related to this rebase?

The tree had one untracked file, `debug_notes.md`. It holds notes from a debug session on the due-time math.
The note asks for deletion before the merge. The due-time function moved on `main` from `due_at`
to `deadline_for`, so the notes may name the old function.

Assumption: the notes are scratch work. I stashed the file under the label
`swd-rebase-preflight-20261028-080351` and restored it after the rebase. I did not commit
it and did not delete it.

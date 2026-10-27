# Questions I would have asked

Nobody was available during this run. Each section records the question, the assumption
I proceeded on, and why it is the lowest-risk option.

## Step 0: the dirty tree

The working tree held one untracked file, `debug_notes.md`. Its one line is a note from debugging
the due-time math, with a reminder to delete the file before merge.

Question: is this file related to the rebase, and do you want it kept?

Assumption: it is related to the branch but is not part of the change. I stashed it under
the label `swd-rebase-preflight-20261027-083148` with `--include-untracked` and restored
it after the rebase. It is untracked again, exactly as you left it. Nothing on the branch
references it. Deleting it stays your call.

## Step 5, risk gate: the service commit breaks INV-006

Headline: commit `023139c` reads the current time with `time.time()`. `main` added
INV-006, which says a command that depends on the current time reads it from the store's
clock and never from the system clock directly. Replaying the commit as is would land a
violation of a new invariant.

The commit also accepts a `now=None` override from the caller. INV-005 and the
architecture doc say time never comes from the caller. The override is the same
violation from the other side.

Options:

1. Replay with an edit. `overdue()` reads `self.store.clock()` and drops the `now`
   parameter. A unit test drives the fake clock past the due time. This keeps the original
   intent and upholds INV-005 and INV-006. Chosen.
2. Keep the `now` override for tests and read the store clock only as the default. This
   contradicts INV-005 and the architecture note "never from the caller".
3. Give the service its own clock. This is an architecture change and needs a discussion
   first, per `docs/guidelines.md`.

Assumption: option 1. The service already holds the store and calls `replay()` and
`append()` on it, so reading `store.clock()` crosses no new boundary.

## Step 8, the plan

Question: do you approve the plan below?

| Commit | Action | Edits |
|---|---|---|
| `023139c` feat(tickets) | replay with edits | read `self.store.clock()`, drop `now`, add `test_overdue_lists_past_due_open_tickets` to `tests/test_tickets.py` |
| `f1a004c` feat(cli) | replay with edits | print through `_line(t)`, resolve the two hunks that collide with `export`, add `test_overdue_lists_only_past_due` to `tests/test_cli.py` |
| `47429e6` docs(specs) | replay with an edit | TKT-014 names the store clock as the current time, see INV-006 |

Assumption: approved. Each edit either preserves the original intent or meets a
convention `main` added. No commit is dropped or split.

Two smaller assumptions sit inside the plan:

- The tests go into the original commits rather than a separate commit. The CLI test
  convention on `main` says a new subcommand ships with its test. A test is not a new bug
  fix, so it belongs with the change it covers.
- The CLI test seeds the log with one `created` event dated at epoch second 1. That is
  the only way to make a ticket overdue through the binary without waiting four hours.

## Not changed, flagged for you

These are stale on `main` already. The guidelines forbid drive-by spec edits, so I left
them for a deliberate decision.

- `docs/product-specs/cli.md` CLI-001 still says "one of four subcommands". `main` added
  `export`, and this branch adds `overdue`, so the true count is six.
- `docs/architecture.md` line 89 still lists `due_at` among the public names. `main`
  renamed it to `deadline_for`.
- `docs/architecture.md` line 103 and `AGENTS.md` lines 102 and 116 still say the CLI
  has no tests and that `make test` runs 7 cases. `main` has CLI tests and 9 cases. After
  this rebase the count is 11.

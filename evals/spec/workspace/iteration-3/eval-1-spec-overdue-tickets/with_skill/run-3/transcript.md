# Transcript: eval-1-spec-overdue-tickets, with_skill, run-3

## Task prompt

> The fixture is already built. Work inside
> /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo.
> Spec this out before anyone plans or builds it: support agents want tickets that pass
> their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue`
> command that lists only overdue tickets, oldest due first. Write the spec into the repo's
> docs the way the repo does specs. Nobody is available to answer questions during this
> run: where the skill would ask me, write the questions to
> .../with_skill/run-3/outputs/questions.md, state the assumption you proceed on, and
> continue. Do not change any code. Do not commit.

Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new/skills/spec

## Skill files read

1. `skills/spec/SKILL.md`: first, before any repo work (command 1).
2. `assets/writing.md`: at workflow step 4, before drafting (command 4).
3. `references/format.md`: not read. Step 1 says to read it only when the repo has no spec
   convention. The repo has one (`docs/product-specs/`, `PREFIX-NNN` IDs, prose
   feature-local invariants).

## Commands

`$S` = /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new,
`$R` = /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-3,
`P` = `$S/scripts/prose-lint.py`. The full paths were used in the actual commands.

1. `S=...; find $S -type f | grep -v '/evals/' | head -50; cat $S/skills/spec/SKILL.md`
   (also read the task file with the Read tool just before). Result: listed the plugin
   files and printed SKILL.md.
2. `R=...; ls -la $R $R/outputs; cd $R/outputs/repo && git status && git log --oneline | head; find . -path ./.git -prune -o -type f -print`
   Result: clean tree on `main`, one commit `6e30541`, docs under `docs/product-specs/`.
3. `for f in AGENTS.md README.md docs/README.md docs/product-specs/README.md docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/event-log.md docs/product-specs/invariants.md; do echo "=== $f"; cat $f; done`
   Result: read the spec convention, TKT-001..013, CLI-001..009 (with the CLI-007 TODO),
   LOG-001..009, INV-001..005.
   Then `for f in docs/architecture.md docs/guidelines.md ticketdesk/*.py; do echo "=== $f"; cat $f; done`
   Result: read architecture, guidelines, and the source to confirm current `list` output
   and the due time computation.
4. `cat $S/assets/writing.md`
   Result: read the writing rules.
5. `python3 $P docs/product-specs/tickets.md; echo "rc=$?"; python3 $P docs/product-specs/cli.md; echo "rc=$?"`
   Result: baseline 0 findings in both files.
6. `cd .../docs/product-specs && python3 - <<'EOF' ... EOF` (edit script for tickets.md)
   Result: added the overdue intro, non-goals list, TKT-014, TKT-015, TKT-016, and an
   "Open questions" section.
7. `cd .../docs/product-specs && python3 - <<'EOF' ... EOF; python3 $P tickets.md cli.md; echo rc=$?`
   (edit script for cli.md, then lint) Result: amended CLI-001 and CLI-006, added CLI-010,
   CLI-011, and an "Open questions" section. Lint: 2 long-lead findings (21 words each).
8. `sed -n 104,106p tickets.md; sed -n 65,67p cli.md`
   Result: showed the two flagged leads (TKT-014 and CLI-010).
9. `python3 - <<'EOF' ... EOF; python3 $P tickets.md cli.md; echo rc=$?`
   Result: rewrote both leads. Lint: 0 findings in 2 files.
10. `cd .../repo && python3 - <<'EOF' ... EOF; git status --short; git diff --stat`
    Result: updated the `tickets.md` rows in `AGENTS.md` and `docs/product-specs/README.md`.
    Four files modified, 88 insertions, 5 deletions. Nothing committed.
11. Write tool: created `$R/outputs/questions.md` with seven questions and assumptions.
12. Write tool: created this transcript.

## Final message to the user

I amended the existing specs instead of adding a new file, because the repo already keeps
due time and listing in `tickets.md` and the command surface in `cli.md`.

Changed files, all uncommitted:

- `docs/product-specs/tickets.md`: overdue intro with non-goals, plus new TKT-014 (what
  overdue means), TKT-015 (overdue changes nothing and appends no event), TKT-016 (overdue
  order: due time ascending, then ID).
- `docs/product-specs/cli.md`: CLI-001 now lists five subcommands. CLI-006 points to the
  marker. New CLI-010 (`OVERDUE` in place of the state) and CLI-011 (`ticketdesk overdue`).
- `AGENTS.md` and `docs/product-specs/README.md`: the `tickets.md` index rows mention
  overdue tickets.

Both spec files pass `prose-lint.py` with 0 findings. No code changed.

Open questions, with the assumption the draft uses (also in `outputs/questions.md`):

1. Does `OVERDUE` replace the state in `list`? Assumed yes. This hides whether an overdue
   ticket has an assignee.
2. Can both `open` and `assigned` tickets be overdue? Assumed yes. Closed tickets never.
3. Is a ticket at exactly its due time overdue? Assumed no.
4. Should `overdue` show the due time or lateness? Assumed no.
5. Should `overdue` exit nonzero when tickets are late? Assumed no.
6. A corrupt log in `overdue` inherits the open CLI-007 TODO. No new rule.
7. Is the in-place edit to CLI-001 acceptable? Assumed yes.

Question 1 is the one to settle first, because it changes what every agent sees in
`list`. Please sign off on the spec, or answer the questions, before `/blueprint` plans
against TKT-014..016 and CLI-010..011.

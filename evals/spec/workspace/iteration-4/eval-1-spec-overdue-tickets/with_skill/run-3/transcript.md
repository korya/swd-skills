# Transcript: spec run 3, overdue tickets

## Task prompt

Execute this task exactly as a user would have asked it, using the skill at the given path.

- Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule/skills/spec. Read that directory's SKILL.md first and follow it, reading its references when it says to. `<plugin root>` for this skill is /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule. Use ONLY the files under /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule: do not invoke the Skill tool, and do not use any installed skill (including swd:spec). Do not read anything outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-3 and /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule.
- Task: The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.

(Plus the instruction to write this transcript and reply in one short paragraph.)

## Commands run

Paths abbreviated here: `$SNAP` = /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule, `$RUN` = /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-3. The commands ran with the full paths.

1. `cd $SNAP && find . -type f | sort && cat skills/spec/SKILL.md` — listed the snapshot files and printed SKILL.md.
2. `cd $RUN && find . -path '*/.git' -prune -o -type f -print | sort` — listed the fixture: AGENTS.md, docs/ with product-specs (tickets, cli, event-log, invariants, README), ticketdesk/ code, tests.
3. `cd $RUN/outputs/repo && for f in AGENTS.md docs/README.md docs/product-specs/README.md docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/invariants.md docs/product-specs/event-log.md; do echo "=== $f"; cat "$f"; done` — read the spec convention: PREFIX-NNN IDs, append-only, feature-local invariants as prose, TODO lines for open conflicts.
4. `cd $RUN/outputs/repo && for f in docs/architecture.md docs/guidelines.md README.md ticketdesk/*.py; do echo "=== $f"; cat "$f"; done; git status 2>&1 | head -5; git log --oneline 2>&1 | head` — read architecture, guidelines, and code. Due time is derived at replay (`sla.due_at`). Working tree clean, one commit.
5. `cat $SNAP/assets/writing.md` — read the writing rules before drafting.
6. `cd $RUN/outputs/repo && for f in docs/product-specs/tickets.md docs/product-specs/cli.md; do echo "== $f"; python3 $SNAP/scripts/prose-lint.py "$f"; echo "exit $?"; done` — baseline: 0 findings in both files.
7. Heredoc append of the "Overdue tickets" section (TKT-014 to TKT-017, goals, non-goals, open questions) to tickets.md, a Python edit of CLI-001 and CLI-006 plus new CLI-010 and CLI-011 in cli.md, then `prose-lint.py` on both — 1 finding: long lead in TKT-014 (21 words). cli.md 0 findings.
8. `sed -n 120,124p docs/product-specs/tickets.md` — showed the TKT-014 paragraph.
9. Edit tool on tickets.md (first attempt refused because the file was not read through the Read tool, then Read lines 118-125 and the Edit applied) — shortened the TKT-014 lead.
10. Python edit of the tickets.md row in docs/product-specs/README.md and AGENTS.md ("overdue tickets (proposed)"), `prose-lint.py` on both specs, `git status --short; git diff --stat` — 0 findings. 4 files modified.
11. Heredoc write of outputs/questions.md, `prose-lint.py questions.md`, `git diff` — 0 findings. Reviewed the full diff. Found a long unwrapped line in CLI-001.
12. Python rewrap of CLI-001 and TKT-014, then `prose-lint.py` on both specs — 0 findings in each.
13. `cat > $RUN/transcript.md` — wrote this file.

## Skill files read

- `$SNAP/skills/spec/SKILL.md` — first, at command 1.
- `$SNAP/assets/writing.md` — at command 5, step 4, before drafting.
- `$SNAP/skills/spec/references/format.md` — not read. The repo has its own spec convention, and SKILL.md says to read format.md only when there is none.
- `$SNAP/scripts/prose-lint.py` — run, not read, at step 5.

## Final message to the user

I specced overdue tickets as an amendment to the repo's existing specs, not as a new file. In `docs/product-specs/tickets.md` I added an "Overdue tickets" section with goals, non-goals, criteria TKT-014 to TKT-017, and an open-questions list. In `docs/product-specs/cli.md` I amended CLI-001 (five subcommands) and CLI-006 (state field can show `OVERDUE`) and added CLI-010 and CLI-011. I also updated the tickets.md row in the `AGENTS.md` and `docs/product-specs/README.md` indexes. Everything is marked "proposed on 2026-10-29, not implemented". All spec files pass prose-lint, no code changed, nothing committed. Six open questions are in `outputs/questions.md`, each with the assumption used. The three that change the shape: does `OVERDUE` replace the state in `list` (assumed yes, which hides open against assigned), can a closed ticket be overdue (assumed no), and does `overdue` show the due time or lateness (assumed no). The other three: exactly-at-due-time is not overdue, "oldest due first" means earliest due time with ID as tie-break, and the exit code is 0 either way. Please sign off on these before anyone plans against the spec.

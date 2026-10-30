# Transcript: spec for overdue tickets (with_skill, run-3)

## Task prompt

> The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.

Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new/skills/spec

## Skill files read

1. `skills/spec/SKILL.md`, first, before any repo work (command 1).
2. `assets/writing.md`, at step 4, before drafting (command 5).
3. `skills/spec/references/format.md` was NOT read. The repo has its own spec convention
   (`docs/product-specs/` with `PREFIX-NNN` IDs), and SKILL.md says to read format.md only
   when the repo has none.
4. `scripts/prose-lint.py` was run (not read) at step 5 on the spec files.

## Commands run

Paths: `SNAP` = /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new, `RUN` = /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/with_skill/run-3. The commands below were run with the full paths.

1. `cd SNAP && find . -type f | head -50 && cat skills/spec/SKILL.md`
   Result: listed the snapshot files and printed SKILL.md.
2. `cd RUN && find . -type f -not -path '*/.git/*' | head -80`
   Result: listed the fixture repo: ticketdesk package, tests, docs with four spec files.
3. `cd SNAP && ls -R skills/spec; cd RUN/outputs/repo && git status --short; git log --oneline | head; for f in AGENTS.md README.md docs/README.md docs/product-specs/*.md docs/architecture.md docs/guidelines.md; do echo "=== $f"; cat $f; done`
   Result: confirmed references/format.md exists. Clean tree, one commit `defae68`. Read all docs (output saved to a file and read with the Read tool).
4. `cd RUN/outputs/repo && cat ticketdesk/*.py && grep -rn "due\|overdue" tests/ | head -30`
   Result: read the code. Due time exists on `Ticket.due_at`. No overdue logic. One due-time test.
5. `cat SNAP/assets/writing.md`
   Result: read the writing rules.
6. `cd RUN/outputs/repo && for f in docs/product-specs/tickets.md docs/product-specs/cli.md; do python3 SNAP/scripts/prose-lint.py $f; echo "exit $?"; done`
   Result: baseline lint, 0 findings in both files.
7. `cd RUN/outputs/repo && cat >> docs/product-specs/tickets.md <<'EOF' ... EOF`
   Result: appended the "Overdue tickets" section (status, problem, goals, non-goals, feature-local invariant, TKT-014 to TKT-016, open questions). The heredoc body is the section now at the end of tickets.md.
8. `cd RUN/outputs/repo && python3 - <<'EOF' ... EOF` followed by the prose-lint loop over tickets.md and cli.md
   Result: amended CLI-001 (five subcommands, `overdue` proposed) and CLI-006 (cross-reference to CLI-010), appended CLI-010 to CLI-013. Lint: 0 findings in both files.
9. `cd RUN/outputs/repo && python3 - <<'EOF' ... EOF` then `git status --short && git diff --stat`
   Result: added "overdue tickets (proposed)" to the tickets.md row of docs/product-specs/README.md and of AGENTS.md. Four files modified, 114 insertions, 6 deletions.
10. `cd RUN/outputs && cat > questions.md <<'EOF' ... EOF` then `python3 SNAP/scripts/prose-lint.py questions.md`
    Result: wrote questions.md (2 blocking, 7 non-blocking questions with assumptions). Lint: 0 findings.
11. `cd RUN/outputs/repo && git diff docs/product-specs/cli.md | head -40`
    Result: reviewed the CLI diff. Found the CLI-006 cross-reference did not say "proposed".
12. `sed -i '' 's/.../.../' docs/product-specs/cli.md && sed -n '40,46p' ... && python3 SNAP/scripts/prose-lint.py docs/product-specs/cli.md`
    Result: failed. The `sed` on this machine is GNU sed and read `''` as the script.
13. `python3 -c '...replace the CLI-006 sentence...' && sed -n '40,46p' docs/product-specs/cli.md && python3 SNAP/scripts/prose-lint.py docs/product-specs/cli.md`
    Result: CLI-006 now says "see CLI-010 and its proposed status". Lint: 0 findings.

No code changed. Nothing committed.

## Final message to the user

I amended two existing spec files rather than creating a new one, per the repo's "update the existing doc" rule: `docs/product-specs/tickets.md` gets an "Overdue tickets" section (goals, non-goals, TKT-014 overdue definition, TKT-015 no event on becoming overdue, TKT-016 overdue listing order) and `docs/product-specs/cli.md` amends CLI-001 (fifth subcommand) and CLI-006 (cross-reference) and adds CLI-010 (OVERDUE marker in list), CLI-011 (`ticketdesk overdue`), CLI-012 (missing or corrupt log), and CLI-013 (no arguments), all marked proposed and awaiting your sign-off; the tickets.md index rows in `docs/product-specs/README.md` and `AGENTS.md` also mention it, and both spec files pass prose-lint. Two open questions block the shape and are in `outputs/questions.md`: does OVERDUE replace the state word in `list` (assumed yes, which hides open/assigned and bends CLI-006) and can a closed ticket be overdue (assumed never); the non-blocking ones, each with an assumption, are showing due time or lateness (no), a nonzero exit when overdue tickets exist (no), the corrupt-log exit code (inherits the open CLI-007 TODO), the exact-second boundary (not overdue), ties (by ID), capitals, and filters (non-goal).

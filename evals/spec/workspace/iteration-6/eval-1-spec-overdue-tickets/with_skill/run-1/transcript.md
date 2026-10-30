# Transcript: spec for overdue tickets

## Task prompt

Execute this task exactly as a user would have asked it, using the skill at the given path.

- Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3/skills/spec. Read that directory's SKILL.md first and follow it, reading its references when it says to. `<plugin root>` for this skill is /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3. Use ONLY the files under /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3: do not invoke the Skill tool, and do not use any installed skill (including swd:spec). Do not read anything outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-1 and /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3.
- Task: The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.

When you finish, write /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-1/transcript.md: the task prompt, a numbered list of every command you ran (verbatim) with a one-line result note, which skill files you read and when, and your final message to the user verbatim. Do not write anything else outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-1. Your final reply to me is one short paragraph: which spec files you created or changed, the criterion IDs, and the open questions.

## Skill files read, and when

1. `skills/spec/SKILL.md`: first, together with the file listing of the snapshot (command 1).
2. `references/format.md`: not read. The repo has its own spec convention (`docs/product-specs/README.md`, `PREFIX-NNN` IDs), and SKILL.md says to read the default format only when there is none.
3. `assets/writing.md` and the header of `scripts/prose-lint.py`: at step 4, before drafting (command 6).
4. `scripts/prose-lint.py`: run at step 5 on both spec files and on `questions.md` (commands 7, 9, 11, 12, 15, 16).

## Commands

Paths: `S` = the snapshot root, `R` = the run directory. Tool calls other than Bash are listed as `[Tool] path`.

1. `S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3; find $S -type f | grep -v '/evals/' | head -100; cat $S/skills/spec/SKILL.md`. Result: listed the snapshot files and printed SKILL.md.
2. `R=/Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-1; ls -la $R $R/outputs; cd $R/outputs/repo && git status && git log --oneline | head; find . -path ./.git -prune -o -type f -print`. Result: clean tree on `main`, one commit, specs in `docs/product-specs/`.
3. `cd .../outputs/repo && for f in AGENTS.md README.md docs/README.md docs/product-specs/README.md docs/product-specs/*.md docs/architecture.md docs/guidelines.md; do echo "=== $f"; cat $f; done`. Result: output was saved to a tool-results file because of its size.
4. `[Read] /Users/dmitri/.claude/projects/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/tool-results/bg9yatr3c.txt`. Result: read all repo docs and specs (the saved output of command 3).
5. `cd .../outputs/repo && cat ticketdesk/cli.py ticketdesk/tickets.py ticketdesk/sla.py ticketdesk/store.py`. Result: confirmed the current `list` line format and that the due time is derived at replay.
6. `S=...; cat $S/assets/writing.md; sed -n 1,60p $S/scripts/prose-lint.py`. Result: read the writing rules and the linter rules.
7. `cd .../outputs/repo && python3 $S/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo exit=$?`. Result: baseline `0 findings in 2 files`, exit 0.
8. `cd .../outputs/repo && python3 - <<'EOF' ... EOF; tail -60 docs/product-specs/tickets.md | head -30`. Result: inserted the overdue overview, invariant, and non-goals paragraphs into `tickets.md` and appended TKT-014 and TKT-015. The heredoc text is the content now in the file.
9. `cd .../outputs/repo && python3 - <<'EOF' ... EOF; python3 $S/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo exit=$?`. Result: amended CLI-001 and CLI-006, appended CLI-010 to CLI-013 to `cli.md`. Lint: `tickets.md:106: long-lead: Paragraph lead has 23 words (max 20).`, exit 1.
10. `cd .../outputs/repo && sed -n 104,110p docs/product-specs/tickets.md`. Result: the long lead was the first sentence of TKT-014.
11. `[Edit] .../docs/product-specs/tickets.md` and, in parallel, `python3 $S/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo exit=$?`. Result: the Edit failed with "File has not been read yet". The lint still showed the same finding, exit 1.
12. `cd .../outputs/repo && python3 - <<'EOF' ... EOF; python3 $S/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo exit=$?`. Result: rewrote the TKT-014 lead as "An `open` or `assigned` ticket is overdue when the command runs after its due time." Lint `0 findings in 2 files`, exit 0.
13. `cd .../outputs/repo && python3 - <<'EOF' ... EOF; git status --short; git diff --stat`. Result: added "overdue tickets" to the `tickets.md` rows in `docs/product-specs/README.md` and `AGENTS.md`. Four files modified, 76 insertions, 5 deletions.
14. `[Write] .../outputs/questions.md`. Result: wrote six questions, each with its assumption and the spec item that carries it.
15. `cd .../outputs && python3 $S/scripts/prose-lint.py questions.md; echo exit=$?; cd repo && git diff docs/product-specs/cli.md | head -30`. Result: `0 findings in 1 file`, exit 0. The diff showed one CLI-001 line over the file's wrap width.
16. `cd .../outputs/repo && python3 - <<'EOF' ... EOF; python3 $S/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo exit=$?; git status --short`. Result: rewrapped CLI-001. Lint `0 findings in 2 files`, exit 0. Four files modified, nothing committed.
17. `[Write] .../transcript.md`. Result: this file.

## Decisions

- **Amend, not create.** The repo keeps ticket rules in `tickets.md` (TKT) and the command surface in `cli.md` (CLI). `docs/README.md` says to update an existing doc instead of fragmenting. Due time already lives in TKT-005, so overdue extends `tickets.md` and `cli.md`.
- **Repo format honored.** New items take the next free IDs. Open questions follow the repo's precedent of a `TODO:` under the item, as under CLI-007. The feature-local invariant is prose without an ID, as `tickets.md` does for "a ticket moves forward only".
- **Existing items changed in place.** CLI-001 now lists five subcommands. CLI-006 gains one sentence that points to CLI-010. Without these two edits, the new items would contradict them.
- **Conflicts checked.** Overdue as a stored state would contradict TKT-001 and LOG-009. The spec makes it a derived label, so neither changes. INV-005 covers event timestamps only, so reading the current time does not conflict. That point is a note for planning in `questions.md`.

## Final message to the user

I amended the existing specs and created no new spec file, because the repo keeps ticket rules in `docs/product-specs/tickets.md` and the command surface in `docs/product-specs/cli.md`. The new criteria are TKT-014 (what overdue means), TKT-015 (overdue order), CLI-010 (`OVERDUE` in `list`), CLI-011 (`ticketdesk overdue`), CLI-012 (no arguments), and CLI-013 (corrupt log). I changed CLI-001 (four subcommands become five) and CLI-006 (a pointer to CLI-010) in place, and added "overdue tickets" to the `tickets.md` index rows in `docs/product-specs/README.md` and `AGENTS.md`. Both spec files pass the prose linter. Six open questions are in `outputs/questions.md`. Three of them shape the spec, and I proceeded on these assumptions: overdue is a derived label and not a fourth state, a closed ticket is never overdue, and `OVERDUE` replaces the state word in `list`. The other three are the exact-second boundary (not overdue yet), the tie order (ID ascending), and the exit code of `overdue` (always 0). No code changed and nothing is committed. Please sign off on the spec before anyone plans against it.

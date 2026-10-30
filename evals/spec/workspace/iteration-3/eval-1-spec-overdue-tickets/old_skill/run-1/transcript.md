# Transcript: spec for overdue tickets (old_skill, run-1)

## Task prompt

Execute this task exactly as a user would have asked it, using the skill at the given path.

- Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/skills/spec. Read that directory's SKILL.md first and follow it, reading its references when it says to. `<plugin root>` for this skill is /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old. Use ONLY the files under /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old: do not invoke the Skill tool, and do not use any installed skill (including swd:spec). Do not read anything outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1 and /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old.
- Task: The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.

When you finish, write /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1/transcript.md: the task prompt, a numbered list of every command you ran (verbatim) with a one-line result note, which skill files you read and when, and your final message to the user verbatim. Do not write anything else outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1. Your final reply to me is one short paragraph: which spec files you created or changed, the criterion IDs, and the open questions.

## Commands run

Paths: `SNAP` = /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old, `RUN` = /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1. The commands below are verbatim, with the full paths.

1. `cd /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old && find . -type f | sort && cat skills/spec/SKILL.md`
   Result: listed the snapshot files and printed the spec SKILL.md.
2. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1 && find . -path ./outputs/repo/.git -prune -o -type f -print | sort`
   Result: the repo has AGENTS.md, docs/ with product-specs (invariants, tickets, event-log, cli), code, and tests.
3. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1/outputs/repo && for f in AGENTS.md docs/README.md docs/product-specs/README.md docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/invariants.md docs/product-specs/event-log.md; do echo "=== $f"; cat $f; done; git status --short; git log --oneline | head`
   Result: found the spec convention (PREFIX-NNN IDs, append-only, feature-local invariants as prose). Clean tree, one commit.
4. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1/outputs/repo && cat docs/architecture.md docs/guidelines.md ticketdesk/*.py README.md`
   Result: read the current behavior. `list` prints `#<id> [<priority>] <state:8> <title>`. Due time is computed on replay.
5. `cat /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/assets/writing.md`
   Result: read the writing rules before drafting.
6. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1/outputs/repo && for f in docs/product-specs/tickets.md docs/product-specs/cli.md; do python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py $f; echo "exit $?"; done`
   Result: baseline, 0 findings in each file.
7. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1/outputs/repo && grep -n "tickets.md\](docs" AGENTS.md`
   Result: no output. The pattern did not match.
8. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1/outputs/repo && grep -n "due time by priority, listing" AGENTS.md`
   Result: found the tickets.md row at line 82.
9. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1/outputs/repo && python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/README.md AGENTS.md ../questions.md; echo "exit $?"`
   Result: 1 finding. The TKT-014 paragraph lead had 21 words.
10. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1/outputs/repo && sed -n 92,97p docs/product-specs/tickets.md`
    Result: showed the TKT-014 paragraph. I rewrote its first sentence.
11. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-1/outputs/repo && python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/README.md AGENTS.md ../questions.md; echo "exit $?"; git status --short; git diff --stat`
    Result: 0 findings in 5 files. Four docs files changed, no code changed, nothing committed.

File edits were made with the Write and Edit tools, not with shell commands: questions.md (created), tickets.md, cli.md, product-specs/README.md, AGENTS.md.

## Skill files read

1. `SNAP/skills/spec/SKILL.md`, first, in command 1.
2. `SNAP/assets/writing.md`, at workflow step 4 before drafting, in command 5.
3. `SNAP/scripts/prose-lint.py` was run, not read, at step 5 (commands 6, 9, 11).

`SNAP/skills/spec/references/format.md` was not read. SKILL.md says to read it only when the repo has no spec convention, and this repo has one.

## Final message to the user

I amended the existing specs instead of creating a new file, because the repo already
splits behavior by area. `docs/product-specs/tickets.md` gets TKT-014 (what overdue means),
TKT-015 (overdue is not a state and appends no event), and TKT-016 (overdue order: due time
ascending, ties by ID), plus a feature-local invariant, a not-in-scope list, and open
questions. `docs/product-specs/cli.md` gets CLI-010 (`OVERDUE` marker in `list`), CLI-011
(`ticketdesk overdue`), and CLI-012 (it takes no arguments). It also amends CLI-001 (five
subcommands) and CLI-006 (points to the marker). The index rows in
`docs/product-specs/README.md` and `AGENTS.md` mention overdue tickets. All files pass
`prose-lint.py`. The open questions are in `outputs/questions.md`, each with the assumption
I used:

1. Does `OVERDUE` replace the state or sit next to it? Assumed next to it.
2. Can a closed ticket be overdue? Assumed no.
3. Does "oldest due first" mean earliest due time? Assumed yes.
4. Is `overdue` filtered per agent? Assumed no filters.
5. Is a ticket overdue at its due time exactly? Assumed no.
6. How does `overdue` report a corrupt log? Assumed the same as `list`, so the CLI-007 TODO
   decides both.
7. Must the output show how late a ticket is? Assumed no.
8. A title that starts with `OVERDUE` is ambiguous in the line format. Assumed acceptable.

Questions 1 to 4 change the shape of the spec. Please sign off on them before `/blueprint`
cites these IDs. One note for planning: the overdue criteria depend on the current time, so
a black-box test needs a log with old `at` values or a way to control the clock.

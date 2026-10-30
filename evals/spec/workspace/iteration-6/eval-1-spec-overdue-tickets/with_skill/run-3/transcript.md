# Transcript: spec for overdue tickets (with_skill, run-3)

## Task prompt

> Execute this task exactly as a user would have asked it, using the skill at the given path.
>
> - Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3/skills/spec. Read that directory's SKILL.md first and follow it, reading its references when it says to. `<plugin root>` for this skill is /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3. Use ONLY the files under /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3: do not invoke the Skill tool, and do not use any installed skill (including swd:spec). Do not read anything outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3 and /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3.
> - Task: The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.
>
> When you finish, write /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3/transcript.md: the task prompt, a numbered list of every command you ran (verbatim) with a one-line result note, which skill files you read and when, and your final message to the user verbatim. Do not write anything else outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3. Your final reply to me is one short paragraph: which spec files you created or changed, the criterion IDs, and the open questions.

## Skill files read

1. `skills/spec/SKILL.md`: first, before touching the repo (command 1).
2. `assets/writing.md`: at step 4, before drafting (command 5).
3. `references/format.md`: not read. SKILL.md says to read it only when the repo has no
   spec convention. The repo has one in `docs/product-specs/README.md` and `docs/README.md`.
4. `scripts/prose-lint.py`: run at step 5, not read.

## Commands

Tool calls that were not shell commands: Read of the task prompt file, Write of
`outputs/questions.md` (between commands 7 and 8), and one Edit on `cli.md` that failed
because the file had not been read with the Read tool. Command 13 made that edit instead.

1. ```
   S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3; find $S/skills/spec $S -maxdepth 2 | head -50; cat $S/skills/spec/SKILL.md
   ```
   Listed the snapshot and printed SKILL.md. The skill has one reference, `format.md`.
2. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3 && ls -la . outputs && cd outputs/repo && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print
   ```
   Clean tree on `main`, one commit. Specs live in `docs/product-specs/` with prefixes INV, TKT, LOG, CLI.
3. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo && for f in AGENTS.md README.md docs/README.md docs/product-specs/README.md docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/event-log.md docs/product-specs/invariants.md docs/architecture.md docs/guidelines.md; do echo "=== $f"; cat $f; done
   ```
   Read all docs. Convention: one file per feature area, `PREFIX-NNN` IDs, no separate feature files for small additions.
4. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo && cat ticketdesk/cli.py ticketdesk/tickets.py ticketdesk/sla.py ticketdesk/store.py
   ```
   Read the code to learn current behavior. `due_at` exists on every ticket. No overdue concept.
5. ```
   cat /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3/assets/writing.md
   ```
   Read the writing rules before drafting.
6. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3 && mkdir -p scratch && L=$PWD/scratch/t.jsonl && cd outputs/repo && python3 -m ticketdesk.cli --log $L create "Printer on fire" --priority P1 && python3 -m ticketdesk.cli --log $L create "Toner low" && python3 -m ticketdesk.cli --log $L list; echo "exit=$?"; python3 -m ticketdesk.cli --log $L overdue; echo "exit=$?"; cat $L
   ```
   `list` printed `#1 [P1] open     Printer on fire`. `overdue` failed with "invalid choice", exit 2.
7. ```
   rm -rf /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3/scratch && ls /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3
   ```
   Removed the temporary log. Only `outputs` remained.
8. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo/docs/product-specs && cat >> tickets.md <<'EOF'
   [the "Overdue tickets" section: overview, goals, non-goals, feature-local invariant, TKT-014 to TKT-016, open questions]
   EOF
   cd .. && python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3/scripts/prose-lint.py product-specs/tickets.md; echo "exit=$?"
   ```
   Appended the section to `tickets.md`. Lint: `0 findings in 1 file`. The heredoc body is the section as it now stands in the file.
9. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo/docs/product-specs && python3 - <<'EOF'
   [script: replace "four subcommands" in CLI-001 with five including `overdue`, add the marker sentence to CLI-006, append CLI-010 and CLI-011]
   EOF
   cd .. && python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3/scripts/prose-lint.py product-specs/cli.md product-specs/tickets.md; echo "exit=$?"
   ```
   Amended `cli.md`. Lint: `0 findings in 2 files`.
10. ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo && python3 - <<'EOF'
    [script: append "overdue tickets" to the tickets.md row in AGENTS.md and in docs/product-specs/README.md]
    EOF
    git status --short && git diff --stat && python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3/scripts/prose-lint.py docs/product-specs/cli.md docs/product-specs/tickets.md; echo "exit=$?"
    ```
    Four doc files modified, plus an untracked `ticketdesk/__pycache__/` from command 6. Lint: 0 findings.
11. ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo && rm -rf ticketdesk/__pycache__ && git status --short && git diff docs/product-specs/cli.md | head -40
    ```
    Removed the cache. The diff showed one CLI-001 line over the file's wrap width.
12. ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo && python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3/scripts/prose-lint.py docs/product-specs/cli.md docs/product-specs/tickets.md; echo "exit=$?"; git status --short
    ```
    Ran in parallel with the failed Edit. Lint: 0 findings. Only the four doc files modified.
13. ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo && python3 - <<'EOF'
    [script: rewrap the CLI-001 sentence at "or with an / unknown one"]
    EOF
    python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3/scripts/prose-lint.py docs/product-specs/cli.md docs/product-specs/tickets.md; echo "exit=$?"
    ```
    Rewrapped CLI-001. Lint: `0 findings in 2 files`.

## Final message to the user

I amended the existing specs rather than creating a new file, because the repo organizes
specs by feature area and overdue builds on TKT-005 and the `list` command.

Changed files, all uncommitted:

- `docs/product-specs/tickets.md`: a new "Overdue tickets" section with overview, goals,
  non-goals, a feature-local invariant (overdue is a view, never an event), and
  **TKT-014** (definition), **TKT-015** (closed tickets are never overdue), **TKT-016**
  (overdue order: due time ascending, then ID).
- `docs/product-specs/cli.md`: new **CLI-010** (the `OVERDUE` marker in `list`) and
  **CLI-011** (the `overdue` command). Two existing items change their contract:
  **CLI-001** now names five subcommands, and **CLI-006** points at the marker.
- `AGENTS.md` and `docs/product-specs/README.md`: the `tickets.md` index row now mentions
  overdue tickets.

No conflict with an invariant. Overdue depends on the time a command runs, so it is not a
state and appends no event. INV-001, INV-002, and LOG-009 hold. `overdue` inherits the
open TODO under CLI-007 for a corrupt log.

Blocking questions, written to `outputs/questions.md` with the assumption I used:

1. Does `OVERDUE` replace the state or sit next to it? Assumed next to it.
2. Can a closed ticket be overdue? Assumed never.
3. Does an `overdue` line match the `list` line? Assumed yes.

Non-blocking assumptions: not overdue at the exact due second, ties sort by ID, an empty
result prints nothing with exit 0, no "how late" figure, no guard for titles that start
with `OVERDUE`. Both spec files pass `prose-lint.py`. Please sign off before anyone plans
or builds against these IDs.

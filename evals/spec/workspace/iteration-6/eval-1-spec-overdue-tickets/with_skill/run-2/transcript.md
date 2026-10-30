# Transcript: spec for overdue tickets (with_skill, run-2)

## Task prompt

> Execute this task exactly as a user would have asked it, using the skill at the given path.
>
> - Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3/skills/spec. Read that directory's SKILL.md first and follow it, reading its references when it says to. `<plugin root>` for this skill is /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3. Use ONLY the files under /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3: do not invoke the Skill tool, and do not use any installed skill (including swd:spec). Do not read anything outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-2 and /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3.
> - Task: The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.
>
> When you finish, write /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-2/transcript.md: the task prompt, a numbered list of every command you ran (verbatim) with a one-line result note, which skill files you read and when, and your final message to the user verbatim. Do not write anything else outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-2. Your final reply to me is one short paragraph: which spec files you created or changed, the criterion IDs, and the open questions.

## Commands run

`$S` below is not a shell variable of the session. Each command set it inline as shown.

1. `S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3; find $S -type f | sort; echo; cat $S/skills/spec/SKILL.md`
   Result: output too large and persisted to a file. Only the start of the file list was shown. I did not open the persisted output.
2. `S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3; find $S/skills/spec -type f | sort; echo; cat $S/skills/spec/SKILL.md`
   Result: the skill has `SKILL.md` and `references/format.md`. Printed SKILL.md.
3. `R=/Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-6/eval-1-spec-overdue-tickets/with_skill/run-2; ls -la $R $R/outputs; cd $R/outputs/repo && git status && git log --oneline | head; find . -type f -not -path './.git/*' | sort`
   Result: clean tree on `main`, one commit `d0fdcdd`. Specs live in `docs/product-specs/` with prefixes INV, TKT, LOG, CLI.
4. `cd .../run-2/outputs/repo; for f in AGENTS.md README.md docs/README.md docs/product-specs/README.md docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/invariants.md docs/product-specs/event-log.md; do echo "===== $f"; cat $f; done` (the `cd` path was the full repo path)
   Result: read the spec convention (`PREFIX-NNN`, append-only IDs, feature-local invariants as prose without IDs) and every adjacent spec.
5. `cd .../run-2/outputs/repo; for f in docs/architecture.md docs/guidelines.md ticketdesk/*.py; do echo "===== $f"; cat $f; done` (full repo path)
   Result: due time is creation time plus SLA hours. No overdue concept exists. `list` prints `#<id> [<priority>] <state:<8> <title>`.
6. `S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule3; cat $S/assets/writing.md; ls $S/scripts`
   Result: read the writing rules. `scripts/` holds `prose-lint.py` and `validate.py`.
7. `S=...sp-rule3; cd .../run-2/outputs/repo; python3 $S/scripts/prose-lint.py docs/product-specs/tickets.md; echo "exit $?"; python3 $S/scripts/prose-lint.py docs/product-specs/cli.md; echo "exit $?"` (full paths)
   Result: baseline, 0 findings in each file, exit 0.
8. `cd .../run-2/outputs/repo; grep -n "OVERDUE\|overdue" -ri . --exclude-dir=.git; cat tests/test_tickets.py | head -40` (full repo path)
   Result: no existing mention of overdue. Tests use a fake clock.
9. Write tool: created `outputs/questions.md` with three blocking and four non-blocking questions, each with its assumption.
10. `cd .../run-2/outputs/repo; cat >> docs/product-specs/tickets.md <<'EOF' ... EOF` (full repo path, heredoc body is the "Overdue tickets" section, TKT-014 to TKT-017, and "Open questions")
    Result: section appended, no output.
11. `cd .../run-2/outputs/repo; python3 - <<'EOF' ... EOF; git diff --stat` (Python edit: CLI-001 four to five subcommands, CLI-006 overdue line, appended CLI-010 to CLI-012)
    Result: `cli.md` 34 lines changed, `tickets.md` 94 lines added.
12. `cd .../run-2/outputs/repo; python3 - <<'EOF' ... EOF; S=...; python3 $S/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/README.md AGENTS.md ../questions.md` (Python edit: added "overdue tickets" to the tickets.md rows in the AGENTS.md and product-specs README indexes)
    Result: exit 1, one finding: `tickets.md:131: long-lead: Paragraph lead has 22 words (max 20).`
13. `cd .../run-2/outputs/repo; sed -n 128,136p docs/product-specs/tickets.md`
    Result: the flagged lead is the first sentence of TKT-014.
14. Edit tool on `tickets.md` (TKT-014 lead).
    Result: refused, the file had not been read with the Read tool.
15. `cd .../run-2/outputs/repo; python3 - <<'EOF' ... EOF; S=...; python3 $S/scripts/prose-lint.py <same five files>; git status --short; git diff docs/product-specs/cli.md` (Python edit: split the TKT-014 lead into two sentences)
    Result: 0 findings in 5 files. Diff showed one CLI-001 line over the repo's wrap width.
16. `cd .../run-2/outputs/repo; python3 - <<'EOF' ... EOF; S=...; python3 $S/scripts/prose-lint.py <same five files>; git diff --stat` (Python edit: rewrapped the CLI-001 line and moved a split code span in the tickets.md overview onto one line)
    Result: 0 findings in 5 files. 4 files changed, 129 insertions, 5 deletions.
17. Write tool: created this transcript.

## Skill files read

- At the start, command 2: `skills/spec/SKILL.md`.
- Step 1, not read: `skills/spec/references/format.md`. The repo has its own spec convention, so the skill says to use that one.
- Step 4, before drafting, command 6: `assets/writing.md`.
- Step 5, commands 7, 12, 15, 16: ran `scripts/prose-lint.py`. I did not read its source.

## Final message to the user

**Spec drafted for overdue tickets. It needs your sign-off, and three shape questions need answers.**

I amended the existing specs instead of creating a new file. Due time already lives in `tickets.md` (TKT-005) and the command surface in `cli.md`. The repo's docs README says to update the existing doc rather than fragment.

| File | Change |
|---|---|
| `docs/product-specs/tickets.md` | New "Overdue tickets" section: overview, status, a feature-local invariant, goals, non-goals, TKT-014 to TKT-017, open questions |
| `docs/product-specs/cli.md` | CLI-001 amended to five subcommands. CLI-006 amended with the `OVERDUE` line. New CLI-010 to CLI-012 |
| `AGENTS.md`, `docs/product-specs/README.md` | Index rows for `tickets.md` now mention overdue tickets |

New and changed criteria:

- **TKT-014** An open or assigned ticket is overdue when a command runs after its due time.
- **TKT-015** A closed ticket is never overdue.
- **TKT-016** Being overdue changes no state, assignee, or due time. The ticket stays assignable and closable.
- **TKT-017** The overdue listing is sorted by due time ascending, then by ID.
- **CLI-001** (amended) `overdue` is the fifth subcommand.
- **CLI-006** (amended) An overdue line is `#<id> [<priority>] <state> OVERDUE <title>`.
- **CLI-010** `ticketdesk overdue` prints the `list` lines of overdue tickets only. No overdue tickets means no output and exit 0.
- **CLI-011** Extra arguments give a usage error and exit 2.
- **CLI-012** A corrupt log fails `overdue` exactly as it fails `list`.

Three questions change the shape. I proceeded on an assumption for each:

1. Does `OVERDUE` replace the state word or sit next to it? I kept the state, because a late ticket with no assignee is the case agents most need to see.
2. Is overdue a derived marker or a recorded state? I chose derived. A recorded state needs a new event kind and changes TKT-001, LOG-001, and LOG-002.
3. Can a closed ticket be overdue? I said no, even when it closed late.

Four smaller questions are in `outputs/questions.md` and under "Open questions" in `tickets.md`. They cover the exact due instant, showing lateness, the empty exit code, and corrupt-log behavior.

One existing conflict touches this feature. The TODO under CLI-007 is still open, and CLI-012 inherits whatever it decides. Nothing is committed and no code changed. `prose-lint.py` reports 0 findings on every changed file.

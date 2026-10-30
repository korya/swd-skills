# Transcript: spec for overdue tickets (old_skill, run-3)

## Task prompt

> Execute this task exactly as a user would have asked it, using the skill at the given path.
>
> - Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/skills/spec. Read that directory's SKILL.md first and follow it, reading its references when it says to. `<plugin root>` for this skill is /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old. Use ONLY the files under /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old: do not invoke the Skill tool, and do not use any installed skill (including swd:spec). Do not read anything outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3 and /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old.
> - Task: The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.
>
> When you finish, write /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3/transcript.md: the task prompt, a numbered list of every command you ran (verbatim) with a one-line result note, which skill files you read and when, and your final message to the user verbatim. Do not write anything else outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3. Your final reply to me is one short paragraph: which spec files you created or changed, the criterion IDs, and the open questions.

## Commands run

1. `S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old; find $S -type f | head -50; cat $S/skills/spec/SKILL.md`
   Result: listed the snapshot files and printed the spec SKILL.md.
2. `R=/Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3; find $R -type f -not -path '*/.git/*' | head -100`
   Result: listed the fixture repo, which has `docs/product-specs/` with tickets, event-log, cli, invariants, and a README.
3. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3/outputs/repo; for f in AGENTS.md README.md docs/README.md docs/product-specs/*.md docs/architecture.md docs/guidelines.md; do echo "=== $f"; cat $f; done`
   Result: printed all docs. The output was saved to a tool-results file, which I then read in full with the Read tool. The repo convention is `PREFIX-NNN` IDs per feature file, prose feature-local invariants, and inline TODOs for open conflicts.
4. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3/outputs/repo; for f in ticketdesk/*.py tests/*.py Makefile pyproject.toml; do echo "=== $f"; cat $f; done; git status; git log --oneline | head`
   Result: printed the code and tests. `list` prints `#<id> [<priority>] <state:<8> <title>`, and `due_at` is creation time plus SLA hours. The tree was clean at commit defae68.
5. `cat /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/assets/writing.md`
   Result: printed the writing rules.
6. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3/outputs/repo; python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo "exit=$?"`
   Result: baseline before edits, `0 findings in 2 files`, exit 0.
7. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3/outputs/repo; sed -i '' 's/due time by priority, listing\./due time by priority, overdue status, listing./' AGENTS.md docs/product-specs/README.md; git diff --stat; python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo "exit=$?"`
   Result: the `sed` failed because this `sed` is GNU sed and took `''` as the script. The lint found one long lead at tickets.md line 101 (21 words).
8. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3/outputs/repo; sed -i 's/due time by priority, listing\./due time by priority, overdue status, listing./' AGENTS.md docs/product-specs/README.md; git diff --stat; sed -n '99,104p' docs/product-specs/tickets.md`
   Result: updated the two index summaries. The diff stat showed 4 changed files. The flagged paragraph was the TKT-014 body.
9. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3/outputs/repo; python3 - <<'EOF' ... EOF` (a Python heredoc that replaced the TKT-014 lead with a shorter sentence), then `prose-lint.py` on both spec files, then `git diff`
   Result: `0 findings in 2 files`, and the full diff looked as intended.
10. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3/outputs/repo; python3 - <<'EOF' ... EOF` (a Python heredoc that rewrapped TKT-014 and CLI-001 and reworded the overdue intro paragraph in tickets.md), then `prose-lint.py` on both spec files, then `awk 'length>90{print FILENAME": "FNR": "length}' docs/product-specs/*.md; git status --short`
    Result: `0 findings in 2 files`. The new lines are no wider than the existing ones, and only 4 doc files are modified.
11. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-3/outputs/repo && git status --short && git log --oneline | head -3 && python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md`
    Result: final check. No code changed, no commit beyond defae68, and `0 findings in 2 files`.

Edits outside the shell: the Edit tool added the overdue intro, the non-goals, and TKT-014 to TKT-016 to `tickets.md`. It also changed CLI-001 and CLI-006 and added CLI-010 and CLI-011 in `cli.md`. The Write tool created `outputs/questions.md` and this transcript.

## Skill files read

- `skills/spec/SKILL.md`: read first, at command 1, before anything in the repo.
- `assets/writing.md`: read at step 4, before drafting, at command 5.
- `scripts/prose-lint.py`: run at step 5 (commands 6, 7, 9, 10, 11), not read as text.
- `skills/spec/references/format.md`: not read. SKILL.md says to read it only when the repo has no spec convention, and this repo has one in `docs/product-specs/README.md`.

## Decisions

- **Amend, not create.** The repo names spec files by feature area and says to update an existing doc instead of fragmenting. Overdue is a ticket rule plus a CLI surface, so it amends `tickets.md` and `cli.md`.
- **New IDs are the next free numbers.** TKT-014 to TKT-016 and CLI-010 to CLI-011. CLI-001 and CLI-006 keep their IDs and change their text, because the command list and the `list` line format change.
- **Non-goals and the feature-local invariant are prose without IDs**, which follows the repo rule for feature-local invariants.
- **No new global invariant.** Overdue as a derived status already follows from INV-001 and LOG-002.
- **Open questions use inline TODOs**, the repo style shown under CLI-007, plus `outputs/questions.md`.

## Final message to the user

I amended two spec files and updated two index lines, with no code change and no commit. In `docs/product-specs/tickets.md` I added an overdue intro with non-goals and the criteria TKT-014 (what overdue means), TKT-015 (overdue changes nothing else), and TKT-016 (overdue order: earliest due first, then ID). In `docs/product-specs/cli.md` I changed CLI-001 (five subcommands) and CLI-006 (an overdue line carries a marker), and I added CLI-010 (`ticketdesk overdue`) and CLI-011 (the `OVERDUE` marker format). The `tickets.md` summaries in `AGENTS.md` and `docs/product-specs/README.md` now mention overdue status. Both spec files pass `prose-lint.py`. The two blocking questions are Q1, whether `OVERDUE` replaces the state or sits after it (I assumed after), and Q2, whether a closed ticket can be overdue (I assumed never). The non-blocking questions are the exact-second boundary (not overdue), the tie order (ID), lateness display (none), empty output (nothing, exit 0), and script breakage from the changed `list` line. A corrupt log also inherits the open CLI-007 TODO. All of them are in `outputs/questions.md`. The spec is a draft contract, so please sign off or answer Q1 and Q2 before `/blueprint` plans against it.

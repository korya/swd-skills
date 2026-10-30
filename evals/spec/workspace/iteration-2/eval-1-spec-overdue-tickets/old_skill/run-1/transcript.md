# Transcript: spec overdue tickets (old_skill, run-1)

## Task prompt

> Execute this task exactly as a user would have asked it, using the skill at the given path.
>
> - Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/skills/spec. Read that directory's SKILL.md first and follow it, reading its references when it says to. `<plugin root>` for this skill is /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old. Use ONLY the files under /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old: do not invoke the Skill tool, and do not use any installed skill (including swd:spec). Do not read anything outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-1 and /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old.
> - Task: The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-1/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-1/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.
>
> When you finish, write /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-1/transcript.md: the task prompt, a numbered list of every command you ran (verbatim) with a one-line result note, which skill files you read and when, and your final message to the user verbatim. Do not write anything else outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-1. Your final reply to me is one short paragraph: which spec files you created or changed, the criterion IDs, and the open questions.

## Commands run

Paths: `SNAP=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old`, `RUN=/Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-1`. The commands below used the full paths.

1. `cat <scratchpad>/prompts/sp-old_skill-r1.txt` (Read tool). Result: task instructions.
2. `cd $SNAP && find . -type f | sort && cat skills/spec/SKILL.md`. Result: listed the snapshot, read SKILL.md.
3. `cd $RUN && find . -type f -not -path '*/.git/*' | sort && cd outputs/repo && git status && git log --oneline | head`. Result: fixture repo on `main`, clean, one commit `034f49d`.
4. `cd $RUN/outputs/repo && for f in AGENTS.md README.md docs/README.md docs/product-specs/README.md docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/event-log.md docs/product-specs/invariants.md docs/architecture.md docs/guidelines.md; do echo "===== $f"; cat "$f"; done`. Result: repo spec convention found (`PREFIX-NNN` IDs, one file per feature area, prose feature-local contracts).
5. Read of the persisted output of command 4 (Read tool). Result: full doc contents.
6. `cd $RUN/outputs/repo && cat ticketdesk/cli.py ticketdesk/tickets.py ticketdesk/sla.py ticketdesk/store.py`. Result: current behavior confirmed, no overdue concept today.
7. `cat $SNAP/assets/writing.md`. Result: writing rules read before drafting.
8. `cd $RUN/outputs/repo && L=../../probe.jsonl; rm -f $L; python3 -m ticketdesk.cli --log $L list; echo "exit=$? exists=$(test -e $L && echo yes || echo no)"; python3 -m ticketdesk.cli --log $L overdue; echo "exit=$?"; python3 -m ticketdesk.cli --log $L create "Printer on fire" --priority P1; python3 -m ticketdesk.cli --log $L create "VPN down"; python3 -m ticketdesk.cli --log $L assign 1 dana; python3 -m ticketdesk.cli --log $L list | cat -A 2>/dev/null || python3 -m ticketdesk.cli --log $L list | sed 's/ /·/g'; rm -f $L; git status --short`. Result: `list` on a missing log exits 0 and creates no file. `overdue` is rejected with exit 2 today. The list line pads the state to 8 characters. The probe left `ticketdesk/__pycache__/`.
9. `cd $RUN/outputs/repo && rm -rf ticketdesk/__pycache__ && git status --short && echo clean`. Result: probe residue removed, tree clean.
10. `cd $RUN/outputs/repo && cat >> docs/product-specs/tickets.md <<'EOF' ... EOF` then `python3 $SNAP/scripts/prose-lint.py docs/product-specs/tickets.md`. Result: overdue section with TKT-014 to TKT-016 appended. 0 findings.
11. `cd $RUN/outputs/repo && python3 - <<'EOF' ... EOF` (replace CLI-001 and CLI-006 bodies, append CLI-010 to CLI-012) then `python3 $SNAP/scripts/prose-lint.py docs/product-specs/cli.md docs/product-specs/tickets.md`. Result: cli.md amended. 0 findings in 2 files.
12. `cd $RUN/outputs/repo && python3 - <<'EOF' ... EOF` (index summary edits) then `git diff --stat`. Result: tickets.md summary in `docs/product-specs/README.md` and `AGENTS.md` now mentions overdue tickets (proposed). 4 files changed.
13. Write of `$RUN/outputs/questions.md` (Write tool). Result: 3 blocking and 9 non-blocking questions, each with its assumption.
14. `cd $RUN/outputs/repo && python3 $SNAP/scripts/prose-lint.py ../questions.md docs/product-specs/cli.md docs/product-specs/tickets.md; git diff docs/product-specs/cli.md | head -80; git status --short`. Result: 0 findings in 3 files. Diff reviewed.
15. `cd $RUN/outputs/repo && cat >> docs/product-specs/cli.md <<'EOF' ... EOF` then `python3 $SNAP/scripts/prose-lint.py docs/product-specs/cli.md docs/product-specs/tickets.md; git status --short`. Result: open questions added to the end of cli.md. 0 findings in 2 files. Only the 4 doc files are modified.
16. Write of `$RUN/transcript.md` (Write tool). Result: this file.

## Skill files read

- `skills/spec/SKILL.md`: first, at command 2, before any repo work.
- `references/format.md`: not read. SKILL.md says to read it only when the repo has no spec convention, and this repo has one.
- `assets/writing.md`: at command 7, in step 4, before drafting.
- `scripts/prose-lint.py`: run, not read, in step 5 (commands 10, 11, 14, 15).

## Final message to the user

I amended two existing spec files rather than adding a rival one, since the repo keeps ticket rules in `docs/product-specs/tickets.md` and the command surface in `docs/product-specs/cli.md`. tickets.md gets an "Overdue tickets" section with goals, non-goals, the "overdue is a condition, not a state" contract, and new criteria TKT-014 (when a ticket is overdue), TKT-015 (overdue changes nothing on the ticket), and TKT-016 (overdue order: due time ascending, then ID). cli.md amends CLI-001 (fifth subcommand) and CLI-006 (the `OVERDUE` mark between state and title), and adds CLI-010 (`overdue` output), CLI-011 (read-only, no file created), and CLI-012 (corrupt log). Each new or changed item is marked "proposed on 2026-10-29, not implemented", and the index summaries in `AGENTS.md` and `docs/product-specs/README.md` mention it. All spec text passes prose-lint. The blocking questions in `outputs/questions.md` are: does OVERDUE sit beside the state or replace it (assumed beside, because replacing it collides with TKT-001); does any script parse `list` output (assumed no); and should `overdue` exit nonzero when it finds tickets (assumed 0). Smaller assumptions cover the exact-due-time boundary, late-closed tickets, calendar hours, and tie order. Also flagged: CLI-012 depends on the open CLI-007 TODO, a proposed INV-006 that is not added, and the status-line convention. Nothing is committed, and the spec needs your sign-off before anyone plans against it.

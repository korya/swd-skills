# Transcript: spec for overdue tickets (with_skill, run-2)

## Task prompt

Spec this out before anyone plans or builds it: support agents want tickets that pass their
due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command
that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the
way the repo does specs. Nobody is available to answer questions during this run: where
the skill would ask me, write the questions to
`/Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/questions.md`,
state the assumption you proceed on, and continue. Do not change any code. Do not commit.

Working repo: `/Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo`.
Skill: `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new/skills/spec`.

## Commands run

1. `cd /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new && find . -type f | head -100 && cat skills/spec/SKILL.md`
   Result: listed the plugin files and printed SKILL.md.
2. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-2 && find . -type f -not -path '*/.git/*' | sort && cd outputs/repo && git status && git log --oneline | head`
   Result: fixture repo with `docs/product-specs/` (invariants, tickets, event-log, cli). Branch `main`, clean, one commit `6e30541`.
3. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo && cat AGENTS.md README.md 2>/dev/null; find docs -type f | xargs -I{} sh -c 'echo "=== {}"; cat "{}"'`
   Result: output too large and saved to a tool-result file, which I read in full with the Read tool. Repo convention found: `docs/product-specs/<area>.md`, `PREFIX-NNN` IDs, feature-local invariants as prose, new spec files go in the README prefix table and index and the AGENTS.md index.
4. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo && cat ticketdesk/cli.py ticketdesk/tickets.py ticketdesk/sla.py`
   Result: confirmed the current `list` line `#{id} [{priority}] {state:<8} {title}`, the due time `created_at + hours * 3600`, and that no overdue concept exists.
5. `cat /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new/assets/writing.md`
   Result: printed the writing rules.
6. `cd .../outputs/repo && python3 - <<'EOF' ... EOF && git diff --stat` (a heredoc script that amends CLI-001 and CLI-006, adds the `overdue.md` pointer to the intro of cli.md, and appends CLI-010)
   Result: `docs/product-specs/cli.md | 27 +++++++++++++++++++++------`.
7. `cd .../outputs/repo && python3 - <<'EOF' ... EOF && git diff` (a heredoc script that adds the `OVD` row to the prefix table and index of `docs/product-specs/README.md` and to the AGENTS.md documents table)
   Result: diff shown. Two lines in cli.md were over the wrap width.
8. `cd .../outputs/repo && python3 - <<'EOF' ... EOF` (reflow of the two long lines in cli.md), then `P=.../scripts/prose-lint.py; python3 $P docs/product-specs/overdue.md; echo "exit=$?"; python3 $P docs/product-specs/cli.md; echo "exit=$?"`
   Result: `0 findings in 1 file` and `exit=0` for both files.
9. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo && git status --short && git diff --stat`
   Result: `M AGENTS.md`, `M docs/product-specs/README.md`, `M docs/product-specs/cli.md`, `?? docs/product-specs/overdue.md`. No code changed, nothing committed.

Files written with the Write and Edit tools, not shell commands:
`docs/product-specs/overdue.md` (created, then one edit to define "full listing" and
"overdue listing"), `outputs/questions.md`, and this transcript.

## Skill files read, and when

1. `skills/spec/SKILL.md`: first, in command 1, before any work on the repo.
2. `assets/writing.md`: at workflow step 4, in command 5, before drafting.
3. `skills/spec/references/format.md`: not read. SKILL.md says to read it only when the
   repo has no spec convention, and this repo has one.
4. `scripts/prose-lint.py`: run at workflow step 5, in command 8. Not read as text.

## Decisions

- Create against amend: created `overdue.md` (prefix `OVD`) for the overdue rules, goals,
  non-goals, and open questions. Amended `cli.md` for the command surface, as the repo
  does for every command. CLI-001 and CLI-006 are edited in place. CLI-010 is new.
- Conflicts: CLI-001 (four subcommands) and CLI-006 (the list line) would contradict the
  feature. The draft amends both and lists them in a before-and-after table. TKT-001,
  TKT-013, LOG-001, LOG-002, LOG-009, and all invariants stay true. No cross-cutting
  invariant is proposed.
- Blocking questions: Q1 (OVERDUE beside or instead of the state) and Q2 (closed tickets).
  Six more are non-blocking. All are in `outputs/questions.md` and in the spec.

## Final message to the user

I created `docs/product-specs/overdue.md` (prefix `OVD`, draft of 2026-10-29) with
criteria OVD-001 to OVD-008. I amended `docs/product-specs/cli.md`: CLI-001 now lists five
subcommands, CLI-006 adds the `OVERDUE` marker line, and CLI-010 is new for
`ticketdesk overdue`. I added the `OVD` file to the prefix table and index in
`docs/product-specs/README.md` and to the index in `AGENTS.md`. Both spec files pass
`prose-lint.py`. The two blocking questions are whether `OVERDUE` replaces the state or
sits beside it (assumed beside, so overdue is not a fourth state) and whether a closed
ticket can be overdue (assumed no). Six more questions, with assumptions, are in the spec
and in `outputs/questions.md`: the exact-second boundary, the meaning of "oldest due
first", extra output columns, a non-zero exit code for alerts, scripts that parse `list`,
and the choice of a separate file. Nothing is committed and no code changed. Please sign
off on the spec, or answer the questions, before anyone plans or builds against it.

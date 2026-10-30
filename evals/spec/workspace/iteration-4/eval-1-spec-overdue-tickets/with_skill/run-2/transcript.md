# Transcript: spec for overdue tickets (run-2)

## Task prompt

The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.

(Skill: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule/skills/spec)

## Commands run

1. `cd /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule && find . -type f | head -100 && cat skills/spec/SKILL.md` — listed the plugin files and printed the spec SKILL.md.
2. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-2 && find . -type f -not -path '*/.git/*' | sort && cd outputs/repo && git status && git log --oneline | head` — fixture has AGENTS.md, docs/product-specs/{README,invariants,tickets,event-log,cli}.md, clean tree on `main`, one commit c8745c9.
3. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo && for f in AGENTS.md README.md docs/README.md docs/product-specs/README.md docs/product-specs/cli.md docs/product-specs/tickets.md docs/product-specs/event-log.md docs/product-specs/invariants.md docs/architecture.md docs/guidelines.md; do echo "=== $f"; cat "$f"; done` — printed all docs (output persisted to a tool-results file, read back with the Read tool). Found the `PREFIX-NNN` convention, the prefix table, and the open CLI-007 TODO.
4. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo && cat ticketdesk/cli.py ticketdesk/tickets.py ticketdesk/sla.py ticketdesk/store.py` — confirmed current behavior: `list` line format `#<id> [<priority>] <state:<8> <title>`, due time = created_at + SLA hours, no notion of overdue.
5. `cat /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule/assets/writing.md` — read the writing rules before drafting.
6. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo && python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule/scripts/prose-lint.py docs/product-specs/overdue.md docs/product-specs/cli.md; echo "exit=$?"` — `0 findings in 2 files`, exit 0.
7. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo && git status --short && git diff --stat` — modified AGENTS.md, docs/product-specs/README.md, docs/product-specs/cli.md. New docs/product-specs/overdue.md. No code touched, nothing committed.

File-tool actions (not shell commands): Write `docs/product-specs/overdue.md`; Edit it once to drop a pointer to a file outside the repo; Edit `cli.md` (CLI-001, CLI-006, new CLI-010 and CLI-011; the first attempt failed because the file had not been read through the Read tool, so I read it and re-applied); Edit `docs/product-specs/README.md` (prefix table, index); Edit `AGENTS.md` (documents-at-a-glance row); Write `outputs/questions.md`; Write this transcript.

## Skill files read and when

- `skills/spec/SKILL.md`: first, before touching the fixture (command 1).
- `references/format.md`: not read. Step 1 says to read it only when the repo has no spec convention. This repo has one (`docs/product-specs/`, `PREFIX-NNN` IDs, prefix table), so the repo convention was used.
- `assets/writing.md`: at step 4, before drafting (command 5).
- `scripts/prose-lint.py`: run at step 5 on the spec files (command 6).

## Decisions

- Create against amend: a new feature file `overdue.md` with prefix `OVD` holds the overview, goals, non-goals, the overdue rule, and the behavior. The command surface is amended in `cli.md`, which mirrors how `tickets.md` (TKT-013) and `cli.md` (CLI-006) split listing today. CLI-001 and CLI-006 were edited in place because their contract changes. New behavior took fresh IDs CLI-010 and CLI-011.
- No new global invariant. The feature-local rule "overdue is computed, never stored, never a state" lives in `overdue.md` as prose.
- Conflicts checked: TKT-001 (three states) and LOG-009 (deterministic replay) hold because overdue is not a state. LOG-001 and INV-002 hold because reads append nothing (OVD-006). The open CLI-007 TODO is not settled. OVD-008 makes `overdue` behave like `list` on a corrupt log.

## Final message to the user

I specced overdue tickets as a draft and need your sign-off before anyone plans or builds on it.

What changed in the repo (no code, nothing committed):

- **New:** `docs/product-specs/overdue.md`, prefix `OVD`. It has the overview, goals, non-goals, criteria OVD-001 to OVD-008, and open questions.
- **Amended:** `docs/product-specs/cli.md`. CLI-001 now lists five subcommands. CLI-006 points overdue lines to the new CLI-010. New CLI-010 defines the overdue line and new CLI-011 defines `ticketdesk overdue`.
- **Indexes:** the prefix table and index in `docs/product-specs/README.md`, and the documents table in `AGENTS.md`.

The repo already has a spec convention, so I followed it instead of the skill's default format. The spec file and `cli.md` pass the prose linter with 0 findings.

The key call: overdue is a mark computed when a command runs, not a fourth state. That keeps TKT-001, LOG-009, and the append-only log untouched.

Open questions, each with the assumption the draft uses (full list in `outputs/questions.md`):

1. Does `OVERDUE` replace the state or sit beside it? I kept the state: `#<id> [<priority>] <state> OVERDUE <title>`.
2. Can a closed ticket be overdue? I said no.
3. Is overdue a state? I said no, it is computed.
4. Is a ticket overdue at exactly its due time? I said no, only after it.
5. Should `overdue` show the due time or lateness? I said no for now.
6. Ties in due time? Lowest ID first.
7. Do scripts parse `list` output? I assumed the changed overdue lines are acceptable.
8. Corrupt log? `overdue` behaves like `list`. The CLI-007 TODO stays open and still needs your call.

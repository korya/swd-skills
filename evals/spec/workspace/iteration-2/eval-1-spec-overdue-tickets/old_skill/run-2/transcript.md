# Transcript: spec for overdue tickets (old_skill, run-2)

## Task prompt

> The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.

Skill used: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/skills/spec

## Commands run

1. `ls -R /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/skills/spec; cat /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/skills/spec/SKILL.md`
   - Listed SKILL.md and references/format.md, printed SKILL.md.
2. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-2 && ls -la && find outputs/repo -type f -not -path '*/.git/*' | sort`
   - Showed the fixture: AGENTS.md, docs/ with four product-spec files and an index, the ticketdesk package, tests.
3. `ls -R /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old | head -50`
   - Located assets/writing.md and scripts/ in the plugin snapshot.
4. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo && for f in AGENTS.md README.md docs/README.md docs/product-specs/README.md docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/invariants.md docs/product-specs/event-log.md; do echo "=== $f"; cat "$f"; done`
   - Read the repo spec convention: PREFIX-NNN IDs per file, prose bodies, TODO lines for open questions, feature-local invariants as prose.
5. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo && cat docs/architecture.md docs/guidelines.md ticketdesk/*.py; git -C . status 2>&1 | head -5`
   - Read architecture, guidelines, and current behavior. Working tree clean on branch main.
6. `cat /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/assets/writing.md; ls /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts`
   - Read the writing rules. Scripts are prose-lint.py and validate.py.
7. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo && for f in docs/product-specs/tickets.md docs/product-specs/cli.md; do echo "== $f"; python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py $f; echo "exit=$?"; done`
   - Baseline: 0 findings in both files, exit 0.
8. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo && sed -i '' 's/| Ticket states, creation, assignment, closing, due time by priority, listing\. |/| Ticket states, creation, assignment, closing, due time by priority, listing, overdue tickets. |/' AGENTS.md && sed -i '' 's/| Ticket lifecycle: states, creation rules, assignment, closing, due time by priority, listing\. |/| Ticket lifecycle: states, creation rules, assignment, closing, due time by priority, listing, overdue tickets. |/' docs/product-specs/README.md && git diff --stat && for f in docs/product-specs/tickets.md docs/product-specs/cli.md AGENTS.md docs/product-specs/README.md ../questions.md; do python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py $f; done`
   - Failed, exit 2. The shell's sed is GNU sed, which read `''` as the script and the substitution as a file name. No file changed.
9. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo && git status --short && sed -i 's/| Ticket states, creation, assignment, closing, due time by priority, listing\. |/| Ticket states, creation, assignment, closing, due time by priority, listing, overdue tickets. |/' AGENTS.md && sed -i 's/| Ticket lifecycle: states, creation rules, assignment, closing, due time by priority, listing\. |/| Ticket lifecycle: states, creation rules, assignment, closing, due time by priority, listing, overdue tickets. |/' docs/product-specs/README.md && git diff --stat && for f in docs/product-specs/tickets.md docs/product-specs/cli.md AGENTS.md docs/product-specs/README.md ../questions.md; do python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py $f; done`
   - Index summaries updated. Diff: 4 files, 92 insertions, 6 deletions. prose-lint: 0 findings in each of the 5 files.

File edits made with the Write, Read, and Edit tools, not shell commands:

- Wrote outputs/questions.md.
- Edited docs/product-specs/tickets.md: new "Overdue tickets" section with TKT-014 to TKT-017.
- Edited docs/product-specs/cli.md: amended CLI-001 and CLI-006, added CLI-010 to CLI-013. (The first Edit attempts failed because the files had not been read with the Read tool. I read them and repeated the edits.)

## Skill files read, and when

1. `skills/spec/SKILL.md`, at the start (command 1).
2. `assets/writing.md`, at step 4 before drafting (command 6).
3. `skills/spec/references/format.md` was not read. The skill says to read it only when the repo has no spec convention, and this repo has one in docs/product-specs/README.md.
4. `scripts/prose-lint.py` was run, not read, at step 5 (commands 7 and 9).

## Final message to the user

I amended two spec files and created none, because the repo keeps one spec file per feature area. In `docs/product-specs/tickets.md` I added an "Overdue tickets" section with TKT-014 (definition, strictly after the due time), TKT-015 (closed tickets are never overdue), TKT-016 (overdue is a computed condition, not a state, so the log never changes), and TKT-017 (overdue order: due time ascending, ties by ID). In `docs/product-specs/cli.md` I amended CLI-001 (five subcommands) and CLI-006 (points to CLI-010), and added CLI-010 (`OVERDUE` replaces the state word in `list`), CLI-011 (`overdue` command), CLI-012 (no arguments, usage error exit 2), and CLI-013 (`list` and `overdue` never write or create the log). I also added "overdue tickets" to the tickets.md summary in `AGENTS.md` and `docs/product-specs/README.md`. Open questions, in `outputs/questions.md` and as TODO lines in the specs: is overdue a condition or a new state (a state would contradict TKT-001, LOG-002, LOG-009, INV-001), does `OVERDUE` replace the state word or sit next to it, can a ticket closed late be overdue, and does the exact due time count. Further assumptions cover the `overdue` line format, tie order, no due time or filters, and corrupt-log handling via the CLI-007 TODO. All spec files pass prose-lint with 0 findings. No code changed, nothing committed. Please sign off before anyone plans against these IDs.

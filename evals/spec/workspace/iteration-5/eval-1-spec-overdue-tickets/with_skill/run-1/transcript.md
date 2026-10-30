# Transcript: spec for overdue tickets

## Task prompt

> The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-5/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-5/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.

Skill used: `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule2/skills/spec`.

## Skill files read

1. `skills/spec/SKILL.md`. Read first, before any work in the repo (command 1).
2. `assets/writing.md`. Read at step 4, after orienting and before drafting (command 6).
3. `references/format.md` was not read. SKILL.md says to read it only when the repo has no
   spec convention. This repo has one: `docs/product-specs/`, one prefix per file,
   `PREFIX-NNN` IDs, inline TODOs.
4. `scripts/prose-lint.py` was run (not read) at step 5 (commands 7, 9, 11).

## Commands run

1. `S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule2; ls -R $S/skills/spec; cat $S/skills/spec/SKILL.md`
   Result: the skill has SKILL.md and references/format.md. Printed SKILL.md.
2. `R=/Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-5/eval-1-spec-overdue-tickets/with_skill/run-1; ls -la $R $R/outputs; cd $R/outputs/repo && git status && git log --oneline | head; find . -path ./.git -prune -o -type f -print`
   Result: clean tree on `main`, one commit. Specs live in `docs/product-specs/` (INV, TKT, LOG, CLI).
3. `cd .../outputs/repo && for f in AGENTS.md README.md docs/README.md docs/product-specs/README.md docs/product-specs/invariants.md docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/event-log.md; do echo "=== $f"; cat $f; done`
   Result: read the spec convention, the invariants, and all three feature specs. Highest IDs: TKT-013, CLI-009.
4. `cd .../outputs/repo && for f in ticketdesk/*.py docs/architecture.md docs/guidelines.md; do echo "=== $f"; cat $f; done`
   Result: due time is creation time plus SLA hours. `list` prints `#<id> [<priority>] <state:<8> <title>`.
5. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-5/eval-1-spec-overdue-tickets/with_skill/run-1 && mkdir -p probe && printf '%s\n' '{"at": 1000.0, "id": 1, "kind": "created", "priority": "P1", "title": "Printer on fire"}' '{"assignee": "dana", "at": 1100.0, "id": 1, "kind": "assigned"}' > probe/t.jsonl && cd outputs/repo && python3 -B -m ticketdesk.cli --log ../../probe/t.jsonl list; echo "exit=$?"; python3 -B -m ticketdesk.cli --log ../../probe/t.jsonl overdue; echo "exit=$?"; python3 -B -m ticketdesk.cli --log ../../probe/missing.jsonl list; echo "exit=$?"; rm -rf ../../probe; git status --short`
   Result: a hand-written log replays. `list` printed `#1 [P1] assigned Printer on fire`, exit 0. `overdue` gave `invalid choice: 'overdue'`, exit 2. Probe removed, tree clean.
6. `S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule2; ls $S $S/assets $S/scripts; cat $S/assets/writing.md`
   Result: read the writing rules. Found `scripts/prose-lint.py`.
7. `cd .../outputs/repo && python3 .../sp-rule2/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo "exit=$?"`
   Result: baseline `0 findings in 2 files`, exit 0.
8. Edits with the Edit tool (no shell): `tickets.md` intro and TKT-014 to TKT-016. `cli.md` intro, CLI-001, CLI-006, CLI-010 to CLI-013. Index rows in `docs/product-specs/README.md` and `AGENTS.md`.
9. `cd .../outputs/repo && python3 .../sp-rule2/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo "exit=$?"; git status --short`
   Result: `0 findings in 2 files`. Four docs modified, no code.
10. `cd .../run-1/outputs && sed -i '' 's/stops every operation .../' questions.md && python3 .../prose-lint.py questions.md; echo "exit=$?"; tail -6 questions.md`
   Result: failed. This `sed` is GNU sed and read `''` as the script, exit 2. The file stayed unchanged. I made the fix with the Edit tool instead.
11. `cd .../run-1/outputs && python3 .../sp-rule2/scripts/prose-lint.py questions.md repo/docs/product-specs/tickets.md repo/docs/product-specs/cli.md; echo "exit=$?"; cd repo && git diff --stat && git status --short`
    Result: `0 findings in 3 files`. Diff: 4 doc files, 89 insertions, 6 deletions. Nothing committed.

12. `cd .../run-1 && python3 -I - <<'EOF' ... EOF` (a short script that reordered this command list), then `sed -n '/## Commands run/,/## Final message/p' transcript.md; grep -n "command" transcript.md | head -5`
    Result: command numbers now match the real order. Only `transcript.md` changed.

`...` stands for the full paths given in commands 1, 2, and 5.

## Final message to the user

I amended the existing specs. I did not create a new file. Overdue is a ticket rule plus a
command surface, and the repo splits those between `tickets.md` and `cli.md`. Nothing is
committed, and no code changed.

What changed in the product contract:

- `docs/product-specs/tickets.md`: new TKT-014 (what overdue means), TKT-015 (closed
  tickets are never overdue), and TKT-016 (overdue order: earliest due time first, then
  ID). The intro now states the goal, the non-goals, and a dated "specified but not built"
  status.
- `docs/product-specs/cli.md`: new CLI-010 (the `OVERDUE` mark in `list`), CLI-011 (the
  `overdue` command), CLI-012 (`overdue` changes nothing), and CLI-013 (`overdue` takes no
  arguments). CLI-001 now lists five subcommands. CLI-006 now points to CLI-010 for
  overdue lines.
- The `tickets.md` rows in `docs/product-specs/README.md` and `AGENTS.md` now mention
  overdue tickets.

The spec contradicts no invariant. Overdue is a condition derived from the due time and
the current time. It is not a state, and no event records it. INV-001, TKT-001, and
LOG-009 therefore hold.

Two questions change the shape of the spec. Please answer them before anyone plans
against it:

1. Does `OVERDUE` replace the state in `list`, or sit next to it? I assumed it sits after
   the state: `#1 [P1] assigned OVERDUE Printer on fire`.
2. Can a ticket closed after its due time count as overdue? I assumed no.

Five more questions sit in `outputs/questions.md` with their assumptions. They cover the
exact due-time boundary, the exit code of `overdue`, the line content, filters, and a
status convention. The new command also inherits the open CLI-007 TODO about corrupt-log
tracebacks.

The spec is a contract. Please sign off, or send corrections, before `/blueprint` builds
on it.

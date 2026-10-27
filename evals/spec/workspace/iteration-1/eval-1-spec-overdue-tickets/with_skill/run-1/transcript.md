# Transcript: eval-1-spec-overdue-tickets, with_skill, run-1

## Task prompt

Execute this task exactly as a user would have asked it, using the skill at the given path.

- Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new/skills/spec
  Read that directory's SKILL.md first and follow it. Read its references/ files and any other files it points to (relative paths resolve from that SKILL.md's directory) when it tells you to. Use ONLY the files under /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new: do not invoke the Skill tool, and do not use any installed skill (including swd:spec), even if one is listed as available.
- OUTPUT_DIR: /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-1/eval-1-spec-overdue-tickets/with_skill/run-1/outputs
- Task: First run `bash /Users/dmitri/dev/swd-skills/evals/spec/make_fixture.sh OUTPUT_DIR/repo`, then work inside OUTPUT_DIR/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to OUTPUT_DIR/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.
  (Replace OUTPUT_DIR with the absolute path above everywhere. The fixture's docs are long; read them in parts rather than all at once.)
- Input files: none
- Outputs to save: the spec file(s) in OUTPUT_DIR/repo/docs (uncommitted), OUTPUT_DIR/questions.md if written, and OUTPUT_DIR/repo left in place.
- When finished, write OUTPUT_DIR/../transcript.md containing: the task prompt, every shell command and file write you did in order with a one-line note, and your final message to the user verbatim.

Do not modify anything outside OUTPUT_DIR. The shell has noclobber set: use `>|` to overwrite a file.

## Commands and file writes, in order

OUT = /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-1/eval-1-spec-overdue-tickets/with_skill/run-1/outputs
ROOT = /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new

1. `Read $ROOT/skills/spec/SKILL.md` -- read the skill. Its workflow: orient, extract, ask what blocks the shape, draft, cross-check with prose-lint, present and gate.
2. `mkdir -p $OUT && bash /Users/dmitri/dev/swd-skills/evals/spec/make_fixture.sh $OUT/repo; find . -type f; git status; wc -l docs/*` -- built the fixture (one commit a87e7e3) and listed its files. The exit code 1 came from `wc` on a directory, not from the fixture script.
3. `cat AGENTS.md docs/README.md docs/product-specs/README.md docs/product-specs/invariants.md` -- step 1, orient. Found the repo convention: one file per feature area, `PREFIX-NNN` IDs, stable and append-only, testable bodies with no "Testable:" appendix, open questions as inline `TODO:` lines, absolute dates. Because the repo has a convention, `references/format.md` was not read (the skill reads it only when there is none).
4. `cat docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/event-log.md` -- read the adjacent specs. Noted the items the feature touches: TKT-005 (due time), TKT-013 (list order), CLI-001 (four subcommands), CLI-006 (list line), LOG-001 (listing appends nothing).
5. `cat ticketdesk/tickets.py ticketdesk/sla.py ticketdesk/cli.py ticketdesk/store.py` -- step 2, extract current behavior: due_at is computed on replay and nothing displays it; list prints `#<id> [<priority>] <state:<8> <title>`.
6. `cat docs/guidelines.md docs/architecture.md README.md; grep -n "due\|clock\|overdue" tests/*.py` -- read the remaining docs and checked the tests for clock handling (injectable clock in the store).
7. `ls $ROOT $ROOT/scripts $ROOT/skills/spec $ROOT/skills/spec/references; cat $ROOT/assets/writing.md; python3 $ROOT/scripts/prose-lint.py --help` -- step 4 prerequisite: read the writing rules and located the linter.
8. `python3 $ROOT/scripts/prose-lint.py docs/product-specs/{tickets,cli,event-log,README}.md AGENTS.md` -- baseline lint before any edit: 0 findings, so later findings are mine.
9. Write `$OUT/questions.md` (heredoc with `>|`) -- step 3: the batched questions. Three blocking (Q1 closed tickets never overdue, Q2 marker position on the list line, Q3 overdue line equals the list line) and four open (Q4 no due time shown, Q5 exact-second boundary, Q6 exit code 0, Q7 no clock override), each with the assumption proceeded on and the spec ID it lands in.
10. Python script amending five files, then lint and `git diff --stat` -- step 4, draft. tickets.md: two intro paragraphs (goal, non-goals) and TKT-014, TKT-015 with a worked ordering table, TKT-016. cli.md: CLI-001 five subcommands, CLI-006 cross-reference, new CLI-010 and CLI-011 with TODOs. event-log.md: LOG-001 covers `overdue`. product-specs/README.md and AGENTS.md: the tickets.md index summary gains "overdue". Lint: 3 findings, all in the new text (one 25-word lead, one 22-word lead, one 26-word sentence).
11. Python script rewriting the TKT-014 lead and the CLI-010 paragraph, then lint and `git diff` -- step 5, fix the findings. Lint: 0 findings in 6 files (the five spec files plus questions.md). Reviewed the full diff.
12. Python script rewrapping the CLI-001 paragraph to the file's line width, lint, line-length check, `git status`; then write `$OUT/../transcript.md` (this file, heredoc with `>|`) -- cosmetic rewrap, final lint 0 findings, transcript.

No code file was changed. Nothing was committed. Nothing outside $OUT was modified.

## Final message to the user, verbatim

The spec is drafted and waiting for your sign-off. It amends the repo's existing spec files rather than adding a new one, because overdue is one ticket rule plus two CLI behaviors, and `docs/README.md` says to extend the existing doc instead of fragmenting.

**What changed** (all uncommitted, no code touched, under `/Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-1/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo`):

| File | Change |
|---|---|
| `docs/product-specs/tickets.md` | Two intro paragraphs: the goal, then the non-goals. New TKT-014 (what overdue means), TKT-015 (overdue order, with a worked example), TKT-016 (overdue is not a state). |
| `docs/product-specs/cli.md` | CLI-001 now lists five subcommands. CLI-006 points at the marker. New CLI-010 (`list` marks overdue lines) and CLI-011 (`ticketdesk overdue`). |
| `docs/product-specs/event-log.md` | LOG-001 now says `overdue`, and a ticket becoming overdue, append nothing. |
| `docs/product-specs/README.md`, `AGENTS.md` | The `tickets.md` index summaries gain "overdue". |

**The contract in one picture:**

```
                       due time                now
  ────────────────────────┼─────────────────────┼─────▶ time
  open / assigned:   not overdue   │   OVERDUE: marker in `list`, row in `overdue`
  closed:            never overdue, however late it was closed
```

`ticketdesk overdue` sorts by due time, not by ID, so a P1 created on Wednesday outranks a P3 created on Monday. Ties fall back to ID order.

**Questions I had to answer myself**, since nobody was available. Each one is a `TODO` under its spec item and is spelled out with its reasoning in `/Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-1/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/questions.md`:

1. Closed tickets are never overdue, however late they closed (TKT-014). This is the assumption that shapes the feature most, so please look at it first.
2. The marker sits between the padded state and the title: `#3 [P1] open     OVERDUE Printer on fire`. Lines of other tickets do not change, so existing scripts keep working (CLI-010).
3. An `overdue` line is identical to that ticket's `list` line (CLI-011).
4. No due time or lateness shown, exit code 0 even when overdue tickets exist, no option to override the current time (CLI-011).
5. A ticket is not overdue at the exact second it is due (TKT-014).

**Cross-check:** every goal has a criterion, nothing contradicts an existing spec or invariant, no new global invariant is needed because INV-001 already forbids holding overdue state outside the log, and `prose-lint.py` reports 0 findings. One inherited wrinkle: the open CLI-007 TODO (a corrupt log escapes as a traceback) applies to `overdue` as well, so resolving it covers the new command too.

Nothing downstream should plan or build on this until you confirm the assumptions above. I did not commit, as asked.

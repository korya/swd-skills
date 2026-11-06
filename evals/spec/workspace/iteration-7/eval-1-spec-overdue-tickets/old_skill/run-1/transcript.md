# Transcript: eval-1-spec-overdue-tickets, old_skill, run-1

Paths are shortened with these names:

- `<root>` = `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/01058b7d-e98e-4d3f-a81c-e8ba15a8c683/scratchpad/snap/old`
- `<run>` = `/Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/old_skill/run-1`
- `<repo>` = `<run>/outputs/repo`

## Task prompt

> Execute this task exactly as a user would have asked it, using the skill at the given path.
>
> - Skill path: `<root>/skills/spec`. Read that directory's SKILL.md first and follow it, reading its references when it says to. `<plugin root>` for this skill is `<root>`. Use ONLY the files under that plugin root: do not invoke the Skill tool, and do not use any installed skill (including swd:spec). Do not read anything outside `<run>` and that plugin root. You may use subagents where the skill says so.
> - Task: First run `bash <root>/evals/spec/make_fixture.sh <repo>`, then work inside `<repo>`. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to `<run>/outputs/questions.md`, state the assumption you proceed on, and continue. Do not change any code. Do not commit.
>
> If the skill you follow has a cold-read step, also do this bookkeeping: before you change anything in response to the cold read, save `git -C <repo> diff` plus any new untracked spec files as they stood into `<run>/outputs/before-cold-read/`. Then write `<run>/outputs/cold-read.md` with four parts: (1) the exact prompt you gave the subagent, (2) the subagent's report verbatim, (3) your verdict for each finding with its evidence and what you changed, and (4) the usage figures the subagent tool returned for that subagent (tokens, duration, tool uses) if it showed any. If the skill has no such step, skip this paragraph.
>
> When you finish, write `<run>/transcript.md`: the task prompt, a numbered list of every command you ran (verbatim) with a one-line result note, which skill files you read and when, and your final message to the user verbatim. Do not write anything else outside `<run>`. Your final reply to me is one short paragraph: which spec files you created or changed, the criterion IDs, and the open questions.

## Skill files read, and when

| Order | File | When | Why |
|---|---|---|---|
| 1 | `<root>/skills/spec/SKILL.md` | First, together with the fixture command | The task says to read it first |
| 2 | `<root>/assets/writing.md` | Step 4, before drafting | SKILL.md requires it before drafting |
| 3 | `<root>/scripts/prose-lint.py` (first 80 lines and `--help`) | Step 4, before drafting | To know the rules that step 5 enforces |

Not read: `<root>/skills/spec/references/format.md`. SKILL.md says to read it only when the
repo has no spec convention. The fixture repo has one, in `docs/README.md` and
`docs/product-specs/README.md`.

The skill has no cold-read step. I skipped the cold-read bookkeeping, and no subagent ran.
No `before-cold-read/` directory and no `cold-read.md` exist.

## Commands run

The two `python3 - <<'EOF'` commands (9 and 10) carried the spec text as string
replacements. Their heredoc bodies are not repeated here. The text they wrote is the
current `git -C <repo> diff`. Every other command is verbatim, with the path names above.

1. `bash <root>/evals/spec/make_fixture.sh <repo>`
   Result: fixture repo created, one commit `a0bebf7 feat(ticketdesk): CLI help desk with event log and agent docs`.
2. `find <root> -type f -not -path '*/evals/*' | head -100`
   Result: listed the plugin files. Confirmed `skills/spec/references/format.md`, `assets/writing.md`, `scripts/prose-lint.py`.
3. `cd <repo> && git status --short && git ls-files && wc -l $(git ls-files)`
   Result: clean tree, 21 tracked files, 994 lines.
4. `cd <repo> && for f in AGENTS.md README.md docs/README.md docs/product-specs/README.md docs/product-specs/cli.md docs/product-specs/event-log.md docs/product-specs/invariants.md docs/product-specs/tickets.md; do echo "=================== $f"; cat -n $f; done`
   Result: read the spec convention (`PREFIX-NNN` IDs, one file per feature area, `TODO:` notes) and the adjacent specs.
5. `cd <repo> && for f in docs/architecture.md docs/guidelines.md ticketdesk/*.py tests/*.py Makefile pyproject.toml .github/workflows/ci.yml; do echo "=================== $f"; cat -n $f; done`
   Result: read the architecture, the guidelines, and the current behavior of `list` and the due time.
6. `sed -n 1,80p <root>/scripts/prose-lint.py; python3 <root>/scripts/prose-lint.py --help 2>&1 | head -30`
   Result: read the lint rules and the usage.
7. `cd <repo> && python3 <root>/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/README.md AGENTS.md; echo "exit=$?"`
   Result: baseline before any edit, `0 findings in 4 files`, exit 0.
8. Write tool: created `<run>/outputs/questions.md`.
   Result: nine questions, each with its assumption.
9. `cd <repo> && python3 - <<'EOF' ... EOF` followed by `python3 <root>/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/README.md AGENTS.md; echo "exit=$?"; git status --short`
   Result: amended `tickets.md`, `cli.md`, `docs/product-specs/README.md`, `AGENTS.md`. Lint reported 2 findings in `tickets.md`: a 21-word lead at line 130 and a 29-word sentence at line 164. Exit 1.
10. `cd <repo> && python3 - <<'EOF' ... EOF` followed by `python3 <root>/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/README.md AGENTS.md; echo "exit=$?"; git diff --stat; git status --short; make lint && make test 2>&1 | tail -3`
    Result: reworded both sentences. Lint `0 findings in 4 files`, exit 0. Diff stat: 4 files, 176 insertions, 7 deletions. `make lint` passed, `make test` ran 7 tests, OK.
11. `cd <repo> && git status --short && find . -name __pycache__ -not -path './.git/*'`
    Result: `make` had left two untracked `__pycache__` directories.
12. `cd <repo> && rm -r ./ticketdesk/__pycache__ ./tests/__pycache__ && git status --short && git diff -- ticketdesk tests | wc -l`
    Result: removed them. Only the four doc files are modified. The diff under `ticketdesk` and `tests` is 0 lines.
13. Edit tool: added two process notes to `<run>/outputs/questions.md`.
    Result: the testability caveat for TKT-014 and the list of touched files.
14. Write tool: this file.

## How the skill's steps went

1. Orient. The repo has a spec convention, so it wins over the skill's default format. I
   chose to amend, not to create a file. The overdue rule is a ticket rule and belongs with
   TKT-005 in `tickets.md`. The marker and the command are command surface and belong in
   `cli.md`, where CLI-001 lists the subcommands. `docs/README.md` also says to update the
   existing doc instead of fragmenting.
2. Extract. Users: support agents. Pain: they cannot see which tickets ran past the due
   time. Current behavior: `list` prints `#<id> [<priority>] <state> <title>` in ID order,
   and the due time exists but is never shown. Touched: TKT-001, TKT-005, TKT-013, CLI-001,
   CLI-006, CLI-007, CLI-008, LOG-001, LOG-006, LOG-007, LOG-009.
3. Ask. Three shape questions and six smaller ones went to `outputs/questions.md`, each
   with the assumption I proceeded on.
4. Draft. New items TKT-014 to TKT-018 and CLI-010 to CLI-014. Goals, non-goals, a
   feature-local invariant, and the open questions sit in `tickets.md`. CLI-001 and CLI-006
   are amended in place.
5. Cross-check. Each goal names its covering item. No item contradicts an existing spec or
   invariant. One conflict is surfaced and not resolved: the open TODO under CLI-007, which
   CLI-014 defers to. `OVERDUE` as a real state would contradict TKT-001 and LOG-009, so
   the draft makes it a marker and says so. `prose-lint.py` passes with 0 findings.
6. Present and gate. Sign-off is requested in the final message. Nothing is committed.

## Final message to the user, verbatim

I amended the existing specs instead of adding a file, since the repo keeps ticket rules in `docs/product-specs/tickets.md` and the command surface in `docs/product-specs/cli.md`. `tickets.md` gains an "Overdue tickets" section with goals, non-goals, and TKT-014 (when a ticket is overdue), TKT-015 (closed is never overdue), TKT-016 (assignment does not change overdue), TKT-017 (overdue listing, earliest due first, ties by ID), TKT-018 (overdue is never recorded in the log). `cli.md` gains CLI-010 (`OVERDUE` marker in `list`, as `#<id> [<priority>] <state> OVERDUE <title>`), CLI-011 (`overdue` command), CLI-012 (nothing overdue: no output, exit 0), CLI-013 (no arguments), CLI-014 (corrupt log), and CLI-001 and CLI-006 are edited in place to name the fifth command and the marker. `docs/product-specs/README.md` and `AGENTS.md` each get one index line. Everything is marked proposed, not built, nothing is committed, no code changed, and the spec needs your sign-off before anyone plans against it. Open questions, each with its assumption in `outputs/questions.md` and at the end of `tickets.md`: (1) is a ticket closed late ever overdue, assumed no. (2) does `OVERDUE` replace the state or stand beside it, assumed beside, because a real overdue state would contradict TKT-001 and LOG-009. (3) should `overdue` show more than `list` does, assumed no. (4) overdue at exactly the due time, assumed no. (5) tie order, assumed by ID. (6) "oldest due" means earliest due time, not earliest created. (7) a title starting with the word `OVERDUE` reads like the marker, accepted for now. (8) exit code when nothing is overdue, assumed 0. (9) the existing TODO under CLI-007 is still open and CLI-014 defers to it. The skill has no cold-read step, so that bookkeeping was skipped.

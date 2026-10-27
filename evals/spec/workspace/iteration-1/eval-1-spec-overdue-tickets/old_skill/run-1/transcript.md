# Transcript: eval-1-spec-overdue-tickets, old skill, run 1

## Task prompt

> Execute this task exactly as a user would have asked it, using the skill at the given path.
>
> - Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/old/skills/spec
>   Read that directory's SKILL.md first and follow it. Read its references/ files when it tells you to. Use ONLY the files at that path: do not invoke the Skill tool, and do not use any installed skill (including swd:spec), even if one is listed as available.
> - OUTPUT_DIR: /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-1/eval-1-spec-overdue-tickets/old_skill/run-1/outputs
> - Task: First run `bash /Users/dmitri/dev/swd-skills/evals/spec/make_fixture.sh OUTPUT_DIR/repo`, then work inside OUTPUT_DIR/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to OUTPUT_DIR/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.
>   (Replace OUTPUT_DIR with the absolute path above everywhere. The fixture's docs are long; read them in parts rather than all at once.)
> - Input files: none
> - Outputs to save: the spec file(s) in OUTPUT_DIR/repo/docs (uncommitted), OUTPUT_DIR/questions.md if written, and OUTPUT_DIR/repo left in place.
> - When finished, write OUTPUT_DIR/../transcript.md containing: the task prompt, every shell command and file write you did in order with a one-line note, and your final message to the user verbatim.
>
> Do not modify anything outside OUTPUT_DIR. The shell has noclobber set: use `>|` to overwrite a file.

## Commands and file writes, in order

1. `Read <skill>/SKILL.md` — read the skill's workflow and definition of done.
2. `ls -R <skill> && cat <skill>/references/format.md` — read the default spec format the skill points to in step 1.
3. `mkdir -p OUTPUT_DIR && bash .../make_fixture.sh OUTPUT_DIR/repo; find/wc/git status/git log` — built the fixture, listed its files and sizes (994 lines total, so read whole files).
4. `cat docs/product-specs/README.md && echo ===== ...` — read the repo's spec convention; the chained cats failed because zsh expanded `=====` (exit 1 after README printed).
5. `cat docs/product-specs/tickets.md; cli.md; invariants.md; event-log.md` — read all four existing spec files.
6. `cat AGENTS.md; docs/README.md` — read the agent manual and the docs-management rules (index update rules, no fragmenting).
7. `cat docs/architecture.md; docs/guidelines.md` — read architecture assumptions (time from the store's clock, replay model) and process rules.
8. `cat ticketdesk/cli.py tickets.py sla.py store.py tests/test_tickets.py README.md` — read current behavior: list line format, due_at, no overdue anywhere.
9. **Write** `OUTPUT_DIR/questions.md` (heredoc) — nine batched questions, three marked shape-changing, each with the assumption the draft proceeds on.
10. `python3 - <<EOF` (string replacements, each asserted to match exactly once) — **amended** `docs/product-specs/tickets.md` (overdue invariant prose, non-goals, TKT-014A/B/C, TKT-015 to TKT-018, open-questions block), `docs/product-specs/cli.md` (non-goals, CLI-001 five subcommands, CLI-006 defers overdue lines, CLI-010 to CLI-013, open-questions block), `docs/product-specs/README.md` (index lines), `AGENTS.md` (summary lines and the "Planned" line). Then `git status --short && git diff --stat`.
11. `python3 - <<EOF` — moved the exit-code assumption note from under CLI-013 to under CLI-012 where it belongs; then `git diff`, a grep of all `### PFX-NNN` headings to confirm ascending IDs, and `git status --short ticketdesk tests` to confirm no code changed (empty).
12. **Write** `OUTPUT_DIR/../transcript.md` (this file, heredoc).

No commits. No files outside OUTPUT_DIR touched.

## Final message to the user, verbatim

Spec drafted and waiting for your sign-off. Nothing downstream should build on it until the questions below are answered.

**Where it lives.** I amended the two existing spec files rather than adding a third: overdue is a ticket rule plus a CLI surface, both already specced, and `docs/README.md` says to extend rather than fragment.

- `docs/product-specs/tickets.md`: a feature-local invariant in the intro ("Overdue is not a state..."), ticket-level non-goals, and TKT-014A/B/C (after / at / before due time), TKT-015 (assigning does not affect it), TKT-016 (closed tickets are never overdue), TKT-017 (judged at command time, never recorded), TKT-018 (overdue order: due time ascending, then ID).
- `docs/product-specs/cli.md`: CLI-001 now names five subcommands, CLI-006 defers overdue lines to CLI-010; new CLI-010 (`OVERDUE` marker in `list`), CLI-011 (`overdue` command), CLI-012 (nothing overdue prints nothing, exit 0), CLI-013 (appends nothing).
- Index lines in `docs/product-specs/README.md` and `AGENTS.md` updated; the AGENTS "Planned" line now points at the new IDs.
- Assumptions are marked inline under the criteria they affect; each file ends with an `Open questions` block that goes away at sign-off.

**Questions** (full batch with reasoning in `questions.md`). The three that change the shape of the contract:

1. Closed tickets past their due time: overdue or not? Assumed not. Agents want a work queue.
2. Exactly at the due time: assumed not overdue; "passes" reads as strictly after.
3. Where `OVERDUE` goes in the `list` line: assumed between state and title, with non-overdue lines unchanged byte for byte. Cost: titles on overdue lines start 8 characters later. The alternative is a fixed-width marker column on every line.

The rest: show the due time in `overdue` (assumed no, avoids picking a time format and timezone), exit code when overdue tickets exist (assumed 0), tie order (ID ascending), marker in `assign`/`close` output (no), log an "overdue" event (no, it is derived), and whether a `list --overdue` filter would have served better than a fifth subcommand. You asked for a command, so I specced a command, but the filter is worth a second thought.

**Cross-check.** Both goals are covered by criteria. No contradiction with existing specs: CLI-001 and CLI-006 were amended, TKT-001's state list and LOG-002's event kinds are untouched, and LOG-009 stays true because overdue is deliberately not part of replay. No cross-cutting invariant needed. No code changed, nothing committed.

One thing that bothers me: the open CLI-007 TODO (corrupt log escapes as a traceback) is inherited by `overdue` untouched. Not this spec's problem, but whoever builds the command will trip over it.

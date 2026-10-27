# Transcript: eval-1-plan-overdue-tickets, old_skill, run-1

## Task prompt

Execute this task exactly as a user would have asked it, using the skill at the given path.

- Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/old/skills/blueprint
  Read that directory's SKILL.md first and follow it. Read its references/ files when it tells you to. Use ONLY the files at that path: do not invoke the Skill tool, and do not use any installed skill (including swd:blueprint), even if one is listed as available. You may use read-only subagents where the skill says so.
- OUTPUT_DIR: /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-1/eval-1-plan-overdue-tickets/old_skill/run-1/outputs
- Task: First run `bash /Users/dmitri/dev/swd-skills/evals/blueprint/make_fixture.sh OUTPUT_DIR/repo`, then work inside OUTPUT_DIR/repo. Plan this change thoroughly, do not implement it: tickets that pass their due time should show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` subcommand should list only overdue tickets, oldest due first. Write the plan to OUTPUT_DIR/plan.md. Nobody is available to answer questions during this run: list them as open questions, state the assumption you proceed on, and continue. Do not change any code or docs in the repo.
  (Replace OUTPUT_DIR with the absolute path above everywhere. Experiments, if any, run on copies in the scratchpad, never in OUTPUT_DIR/repo. The fixture's docs are long; read them in parts rather than all at once.)
- Input files: none
- Outputs to save: OUTPUT_DIR/plan.md, and OUTPUT_DIR/repo left in place and unmodified.
- When finished, write OUTPUT_DIR/../transcript.md containing: the task prompt, every shell command and subagent you used in order with a one-line note, and your final message to the user verbatim.

Do not modify anything outside OUTPUT_DIR. The shell has noclobber set: use `>|` to overwrite a file.

## Commands and subagents, in order

Subagents used: none. The repo is 20 files and under 1000 lines, so batched reads were cheaper inline than through a search subagent.

1. `Read` tool: `<skill>/SKILL.md` — read the skill skeleton before anything else.
2. `bash make_fixture.sh OUTPUT_DIR/repo; find . -type f; wc -l ...; git log --oneline; git status --short` — create the fixture and inventory it (20 files, 994 lines, one commit, clean tree).
3. `cat -n ticketdesk/*.py tests/*.py Makefile pyproject.toml README.md .github/workflows/ci.yml` — read all source, tests, and build files with line numbers for citations.
4. `cat -n AGENTS.md docs/product-specs/README.md docs/product-specs/tickets.md` — docs, part 1 of 3.
5. `cat -n docs/product-specs/cli.md docs/product-specs/invariants.md docs/product-specs/event-log.md` — docs, part 2 of 3.
6. `cat -n docs/architecture.md docs/guidelines.md docs/README.md` — docs, part 3 of 3.
7. `cat -n <skill>/references/validation.md` — step 2 reference, read at step 2.
8. `cp -R repo <scratchpad>/bp-overdue/repo; python3 --version; make lint; make test; git branch -a; git stash list; git status --short; grep -rniE 'overdue|due_at|due time|clock|time\.time'` — scratch copy, baseline (Python 3.15.1 locally, lint OK, 7 tests OK), in-flight-work check (nothing), sweep for existing overdue/clock logic (none).
9. `python3 - <<EOF ... EOF` (patch tickets.py and cli.py on the scratch copy), `cat > tests/test_overdue_proto.py`, `make test; make lint`, then `python3 -m ticketdesk.cli --log e2e.jsonl list|overdue`, missing-log and unknown-subcommand runs, `wc -l`, and a live create/list/overdue flow — prototype of the exact plan shape on the scratch copy; confirmed clock plumbing, fake-Clock tick side effect, closed-ticket exclusion, due-time ordering, no log writes, missing-log behaviour, existing tests green.
10. `python3 -m ticketdesk.cli ... bogus; echo $?` and no-subcommand run; `cat -n <skill>/references/{cross-validation,plan,rationalizations}.md` — confirm argparse exits 2 for both error cases (zsh `pipestatus` had swallowed it), and read the remaining references for steps 5, 8.5, and the anti-rationalization table.
11. `cat >| OUTPUT_DIR/plan.md <<EOF ... EOF; wc -l; git -C OUTPUT_DIR/repo status --short` — write the plan and confirm the fixture repo has zero changes.
12. `cat >| OUTPUT_DIR/../transcript.md <<EOF ... EOF` — this file.

## Final message to the user, verbatim

The plan is at /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-1/eval-1-plan-overdue-tickets/old_skill/run-1/outputs/plan.md. The fixture repo at .../outputs/repo is untouched (git status clean); all experiments ran on a scratch copy.

**Recommendation.** Compute "overdue" on the fly in the service layer (`Ticket.is_overdue(now)`, `TicketService.now()` and `overdue()` in `ticketdesk/tickets.py`), with "now" read from the store's injectable clock, never from the CLI. `cli.py` gains an `overdue` subparser and a shared `_line()` formatter; `list` appends ` OVERDUE` to past-due lines only, so non-overdue output stays byte-identical. Nothing is written to the log, no new event kind, no fourth state. Store, SLA table, and `__init__.py` do not change.

**The one blocker.** Three spec items change (CLI-001 "four subcommands", CLI-006 line format, LOG-001 wording) and three are added (TKT-014 overdue definition, TKT-015 overdue order, CLI-010). This repo requires sign-off on every spec edit, and nobody was available, so the plan gates implementation on that confirmation.

**Evidence.** A prototype of the exact shape on a scratch copy confirmed every load-bearing assumption: the clock is reachable from the service, `due_at` is set on every replay, the fake test `Clock` ticks once per `overdue()` call (tests must set `clock.now` explicitly), closed tickets must be excluded or every old closed ticket shows OVERDUE forever, ordering by `(due_at, id)` gives oldest-due-first, `list`/`overdue` append nothing, a missing log prints nothing with exit 0, and the existing 7 tests plus lint stay green. Local Python is 3.15 while CI pins 3.12; nothing in the plan is version-specific.

**Open questions (assumption in brackets).** 1) Is a closed ticket ever overdue? [no]. 2) Due exactly now? [not overdue, strict `>`]. 3) Marker placement in `list`? [trailing suffix; aligned column is a one-line swap]. 4) Show due time or lateness? [no]. 5) The spec edits above [gated]. 6) Add the repo's first CLI subprocess test, `tests/test_cli.py`? [yes]. 7) Tie-break for equal due times? [ID ascending]. 8) Commit shape? [spec commit, then code plus tests].

One thing worth a second look: the task says tickets should "show as OVERDUE", which could be read as replacing the state column. I rejected that because it hides `open` versus `assigned` and contradicts TKT-001's three states; the suffix keeps both. Easy to flip if you disagree.

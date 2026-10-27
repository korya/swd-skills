# Transcript: eval-1-plan-overdue-tickets, old_skill, run-2

OUTPUT_DIR = `/Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-1/eval-1-plan-overdue-tickets/old_skill/run-2/outputs`
SCRATCH = `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad`

## Task prompt

> Execute this task exactly as a user would have asked it, using the skill at the given path.
>
> - Skill path: `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/old/skills/blueprint`
>   Read that directory's SKILL.md first and follow it. Read its references/ files when it tells you to. Use ONLY the files at that path: do not invoke the Skill tool, and do not use any installed skill (including swd:blueprint), even if one is listed as available. You may use read-only subagents where the skill says so.
> - OUTPUT_DIR: `/Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-1/eval-1-plan-overdue-tickets/old_skill/run-2/outputs`
> - Task: First run `bash /Users/dmitri/dev/swd-skills/evals/blueprint/make_fixture.sh OUTPUT_DIR/repo`, then work inside OUTPUT_DIR/repo. Plan this change thoroughly, do not implement it: tickets that pass their due time should show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` subcommand should list only overdue tickets, oldest due first. Write the plan to OUTPUT_DIR/plan.md. Nobody is available to answer questions during this run: list them as open questions, state the assumption you proceed on, and continue. Do not change any code or docs in the repo.
>   (Replace OUTPUT_DIR with the absolute path above everywhere. Experiments, if any, run on copies in the scratchpad, never in OUTPUT_DIR/repo. The fixture's docs are long; read them in parts rather than all at once.)
> - Input files: none
> - Outputs to save: OUTPUT_DIR/plan.md, and OUTPUT_DIR/repo left in place and unmodified.
> - When finished, write OUTPUT_DIR/../transcript.md containing: the task prompt, every shell command and subagent you used in order with a one-line note, and your final message to the user verbatim.
>
> Do not modify anything outside OUTPUT_DIR. The shell has noclobber set: use `>|` to overwrite a file.

## Commands and subagents, in order

Subagents used: none. All reads were done directly; the repo is ~1000 lines.

1. `Read <skill>/SKILL.md` — read the skill skeleton (step list, references table).
2. `cat <skill>/references/validation.md` — step 2 reference: hypothesis, assumption classes, validation table.
3. `mkdir -p OUTPUT_DIR && bash .../make_fixture.sh OUTPUT_DIR/repo; find ...; wc -l ...` — created the fixture, listed its 21 files (994 lines).
4. `cat -n ticketdesk/*.py tests/*.py Makefile pyproject.toml README.md .github/workflows/ci.yml` (in OUTPUT_DIR/repo) — read all source, tests, build files.
5. `cat -n AGENTS.md docs/README.md` — read the agent manual and the docs index.
6. `cat -n docs/product-specs/tickets.md docs/product-specs/cli.md` — read TKT and CLI specs.
7. `cat -n docs/product-specs/invariants.md docs/product-specs/event-log.md` — read INV and LOG specs.
8. `cat -n docs/architecture.md` — read the architecture doc.
9. `cat -n docs/guidelines.md docs/product-specs/README.md` — read guidelines and the spec format/index.
10. `git status --short && git log --oneline --all && git branch -a && python3 --version && grep -rn ... --include=*.py ...` — clean tree, one commit on `main`, Python 3.15.1; the grep failed on an unquoted zsh glob.
11. `grep -rn --include='*.py' --include='*.md' -e overdue -e OVERDUE -e due_at -e clock . ; cat -A Makefile` — found every `due_at`/`clock` use (sla.py, tickets.py, store.py, tests); Makefile recipes use real tabs.
12. `cat <skill>/references/cross-validation.md` — step 5/6/7 reference.
13. `cat <skill>/references/plan.md` — step 8.5/9 reference and definition of done.
14. `cp -R OUTPUT_DIR/repo SCRATCH/overdue-exp/baseline && make lint && make test && python3 -m ticketdesk.cli ... create/list/overdue` — baseline green (7 tests); `ticketdesk overdue` exits 2 with `invalid choice`.
15. `cp -R baseline SCRATCH/overdue-exp/proto && python3 - <<EOF (patch tickets.py, cli.py) && git diff --stat && make lint && make test` — prototype of the plan; existing 7 tests still green despite extra clock reads.
16. `python3 - <<EOF (service probes with fake Clock)` plus `printf ... >| cli.jsonl; python3 -m ticketdesk.cli --log ... list/overdue; wc -l` — confirmed strict boundary, closed excluded, due order `[2, 1]` vs ID order, nothing appended, missing log stays missing, exit 0.
17. `cat >| tests/test_cli.py <<EOF && make test && git status --short` (in proto) — a subprocess CLI test is discovered by `make test` (8 tests OK).
18. `Write OUTPUT_DIR/plan.md` — wrote the plan.
19. `git status --short --ignored && git diff --stat && ls -la .. && wc -l ../plan.md` (in OUTPUT_DIR/repo) — confirmed the fixture repo is unmodified and the plan exists.
20. `Write OUTPUT_DIR/../transcript.md` — this file.

## Final message to the user (verbatim)

Plan written to `/Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-1/eval-1-plan-overdue-tickets/old_skill/run-2/outputs/plan.md`. The fixture repo is untouched; all experiments ran on scratchpad copies.

**Recommendation.** Compute "overdue" at read time in `TicketService` from the store's clock (`EventStore.now()`, one read per replay): overdue = not closed and `now > due_at`. `Ticket` gets an `overdue: bool`; the service gets `overdue()` sorted by `(due_at, id)`. `list` inserts `OVERDUE ` before the title only on overdue lines, so every other line stays byte-identical; `overdue` reuses the same formatter. Nothing is written to the log, no new state, no new event kind.

**Blocker.** Three specs contradict the change as written (CLI-001 "four subcommands", CLI-006 line format, LOG-001 wording) and two need adding (TKT-014/015, CLI-010). The repo requires your confirmation for any doc change, so step 1 of the plan is gated on you.

**Evidence.** A throwaway prototype on a scratchpad copy passed the existing 7 tests plus a new subprocess CLI test; probes confirmed the strict boundary, closed-ticket exclusion, due order `[2, 1]` where ID order is `[1, 2]`, zero lines appended by `list`/`overdue`, and a missing log yielding empty output with no file created.

**Open questions (8), top assumptions I proceeded on:** closed tickets are never overdue; "past due" is strict (`>`); the marker sits between state and title on overdue lines only; `overdue` repeats the marker; ties break by ID. The rest are in the plan's last section.

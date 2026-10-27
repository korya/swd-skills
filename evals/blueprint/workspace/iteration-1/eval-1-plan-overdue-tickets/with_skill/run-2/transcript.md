# Transcript: eval-1-plan-overdue-tickets, with_skill, run-2

Skill: `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/bp-new/skills/blueprint`
OUTPUT_DIR: `/Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-1/eval-1-plan-overdue-tickets/with_skill/run-2/outputs`

## Task prompt

> First run `bash /Users/dmitri/dev/swd-skills/evals/blueprint/make_fixture.sh OUTPUT_DIR/repo`, then work inside OUTPUT_DIR/repo. Plan this change thoroughly, do not implement it: tickets that pass their due time should show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` subcommand should list only overdue tickets, oldest due first. Write the plan to OUTPUT_DIR/plan.md. Nobody is available to answer questions during this run: list them as open questions, state the assumption you proceed on, and continue. Do not change any code or docs in the repo.
> (Replace OUTPUT_DIR with the absolute path above everywhere. Experiments, if any, run on copies in the scratchpad, never in OUTPUT_DIR/repo. The fixture's docs are long; read them in parts rather than all at once.)
> Input files: none. Outputs to save: OUTPUT_DIR/plan.md, and OUTPUT_DIR/repo left in place and unmodified.

## Tool calls in order

Subagents used: none. The repo is 22 files and under 1000 lines, so every read was done inline.

1. `Read` SKILL.md of the blueprint skill. Loaded the workflow and the reference table.
2. `Bash`: `mkdir -p OUTPUT_DIR && bash make_fixture.sh OUTPUT_DIR/repo && find ... -type f | sort && wc -l ...`. Built the fixture and listed its 22 files with line counts.
3. `Bash`: `cat -n` over `ticketdesk/*.py`, `tests/*.py`, `Makefile`, `pyproject.toml`, `README.md`, `.github/workflows/ci.yml`. Read all source, tests, and build config.
4. `Bash`: `cat -n AGENTS.md docs/README.md docs/product-specs/README.md`. Read the entry-point docs (first part of the docs).
5. `Bash`: `cat -n` over `docs/product-specs/{invariants,tickets,cli,event-log}.md`. Read the four spec files (second part).
6. `Bash`: `cat -n docs/architecture.md docs/guidelines.md`. Read architecture and guidelines (third part).
7. `Bash`: `cat -n skills/blueprint/references/validation.md`. Step 2 reference, before fixing the hypothesis.
8. `Bash`: `cp -R OUTPUT_DIR/repo <scratchpad>/bp-exp/repo && python3 --version && sed -n '3p;5p' Makefile | cat -A && make lint && make test && git status/branch/log`. Scratch copy plus baseline: Python 3.15.1, Makefile tabs real, lint OK, 7 tests OK, one commit, one branch, clean tree.
9. `Bash` (scratch copy only): `grep -rniE 'overdue|now\(|clock'`, three argparse/pad/sort probes, a Python script that applied the prototype edits to `tickets.py` and `cli.py`, `git diff --stat`, `make lint && make test`, a pre-dated JSONL log plus `python3 -m ticketdesk.cli ... create|list|overdue|bogus`, `wc -l` before and after `overdue`, and an in-process `main(argv)` check with the fake clock. All assumptions confirmed, 7/7 tests green on the prototype, `else:` branch trap at `cli.py:28` confirmed.
10. `Bash`: `cat -n` over `references/cross-validation.md`, `references/plan.md`, `references/rationalizations.md`, `assets/writing.md`, `ls scripts/`, `head -30 scripts/prose-lint.py`. Steps 5, 8.5, 9 references and the linter location.
11. `Bash`: `cat >| OUTPUT_DIR/plan.md <<'EOF' ... EOF && python3 scripts/prose-lint.py OUTPUT_DIR/plan.md`. Wrote the plan. Linter: 4 long-sentence findings.
12. `Bash`: `sed -n '24,27p;47,49p;174,176p;343,345p' OUTPUT_DIR/plan.md`. Viewed the four flagged sentences.
13. `Bash`: Python script splitting the four sentences in place, then `prose-lint.py` (0 findings), then `git -C OUTPUT_DIR/repo status --short && git log --oneline && ls OUTPUT_DIR`. Plan passes lint, repo clean and unmodified.
14. `Bash`: `cat >| OUTPUT_DIR/../transcript.md <<'EOF' ... EOF`. This file.

## Final message to the user (verbatim)

Plan written to `/Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-1/eval-1-plan-overdue-tickets/with_skill/run-2/outputs/plan.md`. The fixture repo at `/Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-1/eval-1-plan-overdue-tickets/with_skill/run-2/outputs/repo` is untouched: clean `git status`, single commit `f87e57b`. The plan passes `prose-lint.py` with zero findings.

**Recommendation.** Treat overdue as a read-time view, not a state and not an event. `Ticket.is_overdue(now)` plus `TicketService.overdue(now)` and `now()` go in `tickets.py`. `cli.py` gains the `overdue` subparser, a `_line()` formatter that prints `OVERDUE` in the existing 8-character state column, and an explicit `elif` for `list`. The store, the SLA table, and the log format do not change. This is the only shape that keeps LOG-009 (deterministic replay) and INV-001 intact.

**Evidence.** A prototype on a scratch copy passed `make lint && make test` (7/7) and produced the expected `list` and `overdue` output against a pre-dated log, with no lines appended. Twelve load-bearing assumptions are confirmed in the plan with `file:line` citations or prototype output.

**Implementation traps the prototype exposed.** The `else:` branch at `cli.py:28` catches every command that is not create, assign, or close, so a naive `overdue` subparser would print the whole list. The test fake clock advances one second per call, so service tests must pass `now` explicitly.

**Blocker.** Eight spec and doc edits need your confirmation before code work, per `AGENTS.md:93`. They are new TKT-014, TKT-015, and CLI-010, plus edits to CLI-001, CLI-006, CLI-007's TODO, LOG-001, `architecture.md`, `AGENTS.md`, and the specs index. Exact wording is in step 1 of the plan.

**Open questions, each with the assumption the plan proceeds on:**
1. Closed tickets are never overdue.
2. Overdue starts strictly after `due_at`, not at it.
3. `OVERDUE` replaces the state word on the `list` line rather than adding a column. The cost is that an overdue line no longer says open or assigned.
4. `overdue` prints the same line format as `list`.
5. The service may read the current time from the store's clock, with a one-line note in `architecture.md`.
6. The eight doc edits are acceptable pending your review of wording.
7. No CLI tests for create, assign, and close in this change.
8. No version bump.

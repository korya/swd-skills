# Transcript: eval-1-bootstrap-agent-docs-ticketdesk / old_skill / run-1

## Task prompt

> First run `bash /Users/dmitri/dev/swd-skills/evals/repo-docs/make_fixture.sh OUTPUT_DIR/repo`, then work inside OUTPUT_DIR/repo. Document this project for coding agents: set up AGENTS.md and the docs/ structure. Nobody is available to answer questions during this run. Where the workflow would ask me to confirm the scope or the final layout, write the proposal to OUTPUT_DIR/proposal.md and proceed as if I had said yes. Write the docs into the repo. Do not commit, and do not change any code.
>
> OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/repo-docs/workspace/iteration-1/eval-1-bootstrap-agent-docs-ticketdesk/old_skill/run-1/outputs
>
> Skill: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/old/skills/repo-docs (SKILL.md, references/, templates/ only; no Skill tool, no installed skill).

## Commands and file writes, in order

1. `find <skill> -type f; cat <skill>/SKILL.md` — read the skill skeleton and its file list.
2. `cat <skill>/references/spec-format.md references/checklist.md templates/*.md` — read all references and templates up front (SKILL.md says read them at their step; I read them once, before the steps that need them).
3. `mkdir -p OUTPUT_DIR && bash make_fixture.sh OUTPUT_DIR/repo; find; git status; git log` — created the fixture (one commit, 12 files) and listed it.
4. `cat` of README.md, pyproject.toml, Makefile, ci.yml, every module in ticketdesk/, both test files — step 1 survey.
5. `make lint && make test`; then probed the CLI against a throwaway log in the scratchpad (create with default priority, unknown priority, reassign, close an unassigned ticket, short resolution, missing id, list, cat the log); removed the scratch dir. Evidence: unknown priority escapes as a traceback with exit 1; reassignment and close-from-open are allowed.
6. Wrote `OUTPUT_DIR/proposal.md` — step 2 scope proposal: three spec files (tickets/TKT, event-log/LOG, cli/CLI), SLA folded into tickets, two conflicts surfaced, placeholders chosen for the coverage policy.
7. Wrote `repo/docs/product-specs/invariants.md` (INV-001..008), `tickets.md` (TKT-001..014), `event-log.md` (LOG-001..008), `cli.md` (CLI-001..010) — step 3 items 1 and 2.
8. Python one-liner rewrote one sentence in `cli.md` (CLI-008 TODO) so it no longer points at a file outside the repo.
9. Wrote `repo/docs/product-specs/README.md`, `repo/docs/architecture.md`, `repo/docs/guidelines.md`, `repo/docs/README.md`, `repo/AGENTS.md` — step 3 items 3 to 7, from the templates.
10. Python verification script: relative links resolve, cited IDs exist, no duplicate IDs, no `**Testable:**` lines, AGENTS.md indexes all of docs/, specs README indexes all spec files; `grep` for implementation names in spec bodies (none); `git status`, `git diff --stat` (no tracked changes), `make test` (OK). Only flag: `TKT-012A`, the sub-case format example in the specs README.
11. `rm -rf repo/tests/__pycache__ repo/ticketdesk/__pycache__` — removed byproducts of my test run so the working tree holds only the new docs.
12. Appended the "Final layout" confirmation section to `OUTPUT_DIR/proposal.md` — in place of the closing user confirmation.
13. Wrote this file, `OUTPUT_DIR/../transcript.md`.

## Final message to the user (verbatim)

Docs are in place at `/Users/dmitri/dev/swd-skills/evals/repo-docs/workspace/iteration-1/eval-1-bootstrap-agent-docs-ticketdesk/old_skill/run-1/outputs/repo`, uncommitted, code untouched. The scope and final-layout confirmations you would normally have been asked for are in `/Users/dmitri/dev/swd-skills/evals/repo-docs/workspace/iteration-1/eval-1-bootstrap-agent-docs-ticketdesk/old_skill/run-1/outputs/proposal.md`.

**What was created** (9 files, 592 lines):

```
AGENTS.md                                  overview, stack, 30-second architecture, doc index, process rules
docs/README.md                             how docs/ is managed
docs/architecture.md                       CLI -> domain -> store; assumptions; tech choices; migration paths
docs/guidelines.md                         lint/test policy, five-step planning, 5-whys regressions
docs/product-specs/README.md               format rules, prefix table, index
docs/product-specs/invariants.md  INV x8   log is truth, append-only, fail loud, stable ids, 1 change = 1 event, store-only I/O, stdlib only, doc confirmation
docs/product-specs/tickets.md     TKT x14  states, validation, ids, SLA, assign/close, listing (SLA folded in: too few items for its own file)
docs/product-specs/event-log.md   LOG x8   line format, event shape, append, missing file, corrupt line, fresh read
docs/product-specs/cli.md         CLI x10  subcommands, log path, output lines, exit codes, entry points
```

**Two things you should decide, not me** (both recorded as TODO / open question in the specs rather than silently specced away):

1. `ticketdesk create x --priority P9` prints a raw Python traceback and exits 1, while every other validation failure prints `error: ...` and exits 2. The SLA module raises `ValueError`, the CLI only catches `TicketError`. CLI-008 states the uniform contract and carries the TODO. Fix the code (one-line wrap) or amend the spec?
2. A replayed `assigned`/`closed` event for an id that was never `created` dies with a bare `KeyError` instead of the path-and-line message LOG-007 promises for corruption. Treat as corruption, or tolerate?

**Choices I made that you might disagree with:** `cli.md` exists as a spec file because the CLI is the only user surface, so exit codes and output lines are product behavior. The coverage policy in `guidelines.md` is "every spec ID has at least one test; new logic ships with tests" rather than an invented percentage, since the repo states none. Lint is documented honestly as a `compileall` syntax pass.

Verification: all links resolve, every cited ID exists, no duplicate IDs, no `**Testable:**` lines, no implementation names in spec bodies, `make test` passes, `git status` shows only `AGENTS.md` and `docs/` as untracked.

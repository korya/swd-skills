# Transcript: eval-1-spec-overdue-tickets, with_skill, run-2

OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-1/eval-1-spec-overdue-tickets/with_skill/run-2/outputs

## Task prompt

First run `bash /Users/dmitri/dev/swd-skills/evals/spec/make_fixture.sh OUTPUT_DIR/repo`, then work inside OUTPUT_DIR/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to OUTPUT_DIR/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.

Skill used: the `spec` skill at the sp-new snapshot (SKILL.md, references/format.md, assets/writing.md, scripts/prose-lint.py). No installed skill invoked.

## Commands and file writes, in order

1. `cat .../skills/spec/SKILL.md` (Read tool). Read the skill workflow.
2. `cat .../skills/spec/references/format.md` and `ls .../scripts/`. Read the default spec format and found prose-lint.py and validate.py.
3. `cat .../assets/writing.md`. Read the writing rules.
4. `mkdir -p OUTPUT_DIR && bash .../evals/spec/make_fixture.sh OUTPUT_DIR/repo && find ... && wc -l docs/*.md docs/*/*.md`. Built the fixture and listed its files and doc sizes.
5. `cat docs/product-specs/README.md docs/product-specs/tickets.md`. Step 1 orient: the repo's spec convention and the adjacent ticket spec.
6. `cat docs/product-specs/cli.md docs/product-specs/invariants.md docs/product-specs/event-log.md`. The other specs and the invariants.
7. `cat AGENTS.md docs/README.md docs/guidelines.md`. Agent manual, doc rules, process rules.
8. `cat docs/architecture.md ticketdesk/sla.py ticketdesk/tickets.py ticketdesk/cli.py`. Step 2 extract: current due-time and list behavior.
9. `cat ticketdesk/store.py README.md tests/test_tickets.py && git status --short && git log --oneline`. Clock injection, test style, clean tree.
10. `python3 prose-lint.py` on tickets.md, cli.md, README.md and `head -30 validate.py`. Baseline: 0 findings. validate.py is the plugin's manifest check, not relevant.
11. Write `OUTPUT_DIR/questions.md` (heredoc with `>|`). Step 3: seven batched questions, each with the assumption taken.
12. `python3 -I` script editing `docs/product-specs/tickets.md` (intro invariant paragraph, TKT-014 to TKT-016, Open questions), `docs/product-specs/cli.md` (CLI-001 in place, CLI-010 to CLI-012, Open questions), `docs/product-specs/README.md` (index line). Then prose-lint on all plus questions.md, and `git status`. Step 4 draft. 1 finding: TKT-014 lead at 21 words.
13. `python3 -I` script shortening the TKT-014 lead, then prose-lint (0 findings) and `git diff`. Step 5 cross-check against the diff.
14. `python3 -I` script adding a CLI-006 pointer to CLI-010, re-wrapping CLI-001, and adding Non-goals lists to tickets.md and cli.md. Then prose-lint on 4 files (0 findings), `git status`, `git diff --stat`.
15. Write `OUTPUT_DIR/../transcript.md` (this file, heredoc with `>|`).

No code files changed. No commit made. Modified, uncommitted: docs/product-specs/README.md, docs/product-specs/cli.md, docs/product-specs/tickets.md.

## Final message to the user, verbatim

Spec drafted as an amendment, uncommitted, lint-clean. It waits for your sign-off on seven assumptions before `/blueprint` builds on it.

**Where it lives** (`/Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-1/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo/docs/product-specs/`):

- `tickets.md`: a feature-local invariant ("overdue is a condition, not a state"), four non-goals, TKT-014 (definition), TKT-015 (closed is never overdue), TKT-016 (overdue listing order), and an Open questions block.
- `cli.md`: CLI-001 edited in place (five subcommands), a pointer added to CLI-006, three non-goals, CLI-010 (`list` suffixes ` OVERDUE`), CLI-011 (`overdue` command), CLI-012 (nothing overdue prints nothing), and an Open questions block.
- `README.md`: the index line for tickets.md now mentions overdue tickets.

**Why amend, not a new file.** Due time (TKT-005), listing (TKT-013, CLI-006), and the command list (CLI-001) already have specs, and `docs/README.md` says to extend rather than fragment. New criteria take fresh IDs. Nothing was renumbered.

**The one product decision I made for you.** OVERDUE is not a fourth state. A state would contradict TKT-001 and "a ticket moves forward only", and would push a clock-dependent fact into the log. So it is a view computed when the command runs. Nothing is recorded, and INV-001, LOG-001, LOG-002, and LOG-009 stay intact.

**Questions I could not ask**, in `/Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-1/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/questions.md`, with the assumption each criterion proceeds on:

1. Closed tickets are never overdue (TKT-015). Flip this and `overdue` becomes a breach report.
2. ` OVERDUE` goes at the end of the `list` line. Other lines stay byte-identical (CLI-010).
3. `overdue` prints the same line as `list`, no due-time column (CLI-011).
4. `overdue` exits 0 even when tickets are overdue, so no cron hook (CLI-011).
5. At exactly the due time a ticket is not overdue (TKT-014).
6. Equal due times sort by ID (TKT-016).
7. No `--now` option. A black-box test can write a log with past `at` timestamps instead.

Q1 and Q2 change the shape. The rest are details.

**Not done, on purpose.** No code touched, nothing committed. `AGENTS.md` (its "Current state" list and tickets.md summary) sits outside `docs/` and was left alone. The Open questions blocks and the "Assumed, see Qn" lines are pre-sign-off markers and come out at sign-off.

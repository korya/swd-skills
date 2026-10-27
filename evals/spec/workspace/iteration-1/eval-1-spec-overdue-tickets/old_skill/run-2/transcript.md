# Transcript: eval-1-spec-overdue-tickets, old skill, run 2

## Task prompt

Execute this task exactly as a user would have asked it, using the skill at the given path.

- Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/old/skills/spec
  Read that directory's SKILL.md first and follow it. Read its references/ files when it tells you to. Use ONLY the files at that path: do not invoke the Skill tool, and do not use any installed skill (including swd:spec), even if one is listed as available.
- OUTPUT_DIR: /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-1/eval-1-spec-overdue-tickets/old_skill/run-2/outputs
- Task: First run `bash /Users/dmitri/dev/swd-skills/evals/spec/make_fixture.sh OUTPUT_DIR/repo`, then work inside OUTPUT_DIR/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to OUTPUT_DIR/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.
  (Replace OUTPUT_DIR with the absolute path above everywhere. The fixture's docs are long; read them in parts rather than all at once.)
- Input files: none
- Outputs to save: the spec file(s) in OUTPUT_DIR/repo/docs (uncommitted), OUTPUT_DIR/questions.md if written, and OUTPUT_DIR/repo left in place.
- When finished, write OUTPUT_DIR/../transcript.md containing: the task prompt, every shell command and file write you did in order with a one-line note, and your final message to the user verbatim.

Do not modify anything outside OUTPUT_DIR. The shell has noclobber set: use `>|` to overwrite a file.

## Commands and file writes, in order

1. `Read .../snap/old/skills/spec/SKILL.md` — read the skill.
2. `bash /Users/dmitri/dev/swd-skills/evals/spec/make_fixture.sh OUTPUT_DIR/repo; ls -R OUTPUT_DIR/repo` — build the fixture and list it.
3. `cat .../spec/references/format.md; wc -l ...; cat AGENTS.md; cat docs/product-specs/README.md` — read the format reference (SKILL.md step 1); the `echo ======` separators made zsh error out after format.md printed, so the rest was re-run.
4. `wc -l docs/**/*.md ticketdesk/*.py tests/*.py; cat AGENTS.md; cat docs/product-specs/README.md` — repo overview, agent manual, spec convention and index.
5. `cat docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/invariants.md` — adjacent specs and the invariants floor.
6. `cat docs/product-specs/event-log.md docs/README.md ticketdesk/cli.py ticketdesk/tickets.py ticketdesk/sla.py; git status; git log` — remaining spec, doc rules, current behavior.
7. `cat docs/architecture.md; grep -n -i "spec|doc|clock|time" docs/guidelines.md; cat ticketdesk/store.py; grep clock/time tests/*.py` — clock model and doc-update rules.
8. Write `OUTPUT_DIR/questions.md` (heredoc with `>|`) — eight questions with the assumption each proceeds on, plus reviewer notes.
9. Write `scratchpad/apply_spec.py` and run `python3 -I apply_spec.py OUTPUT_DIR/repo` — anchored, assert-checked edits to:
   - `docs/product-specs/tickets.md`: overdue paragraph with non-goals in the intro; TKT-014 to TKT-017; draft open-questions block.
   - `docs/product-specs/cli.md`: CLI-001 now five subcommands; CLI-006 points at the marker; CLI-010 to CLI-013; draft open-questions block.
   - `docs/product-specs/event-log.md`: LOG-001 names `overdue` as a non-appending listing.
   - `docs/product-specs/README.md` and `AGENTS.md`: index summaries mention overdue; AGENTS.md "Planned" line points at the draft.
   Then `git status --short; git diff --stat` — 5 docs changed, nothing else.
10. `git status --short -- ticketdesk tests Makefile pyproject.toml` — confirmed no code changed; then wrote this transcript (heredoc with `>|`).

No commit was made.

## Final message to the user (verbatim)

Spec drafted as an amendment, awaiting your sign-off. Nothing downstream should cite it until you do.

**What changed (docs only, uncommitted, in `OUTPUT_DIR/repo`)**

- `docs/product-specs/tickets.md`: an overdue paragraph with non-goals, and four new criteria. TKT-014 defines overdue (open or assigned, now strictly past due), TKT-015 says closed tickets are never overdue, TKT-016 says overdue is derived and never logged, TKT-017 fixes the `overdue` order (due time ascending, ID as tie-break).
- `docs/product-specs/cli.md`: CLI-001 now lists five subcommands; CLI-010 is the `OVERDUE` marker between state and title in `list`; CLI-011 is `ticketdesk overdue`, whose lines are verbatim `list` lines; CLI-012 covers the empty case (prints nothing, exit 0); CLI-013 rejects positional arguments.
- `docs/product-specs/event-log.md`: LOG-001 now names `overdue` as a listing that appends nothing.
- `docs/product-specs/README.md` and `AGENTS.md`: index rows mention overdue; the "Planned" line points at the draft.

I amended rather than adding an `overdue.md` because the repo files by feature area, and overdue is a ticket rule plus a CLI surface. IDs are appended only; nothing was renumbered. No code or tests were touched, no commit made.

**Questions you need to answer** (full list with alternatives in `OUTPUT_DIR/questions.md`; each assumption is marked inline in the spec as A1 to A8):

1. Closed tickets are never overdue (A1). If you want "closed late" visible, that is a new criterion.
2. "Now" is the time the command runs; no `--as-of` (A2).
3. The marker sits between state and title: `#1 [P1] assigned OVERDUE Printer on fire` (A3). Appending it after the title is the main alternative.
4. `overdue` prints the same line format as `list`, marker included (A4).
5. Exactly at the due time is not overdue (A5); same-due-time ties break by ID (A6); nothing overdue means exit 0 and no output (A7); `create`/`assign`/`close` output lines do not change (A8).

One thing worth a conscious decision: this is the first output that depends on the wall clock rather than on the log alone. No invariant breaks (nothing stores overdue state, replay stays deterministic), so I kept "overdue is derived, never recorded" as a feature-local contract in `tickets.md`. Promote it to an `INV` if you want it on the floor.

Once you confirm or correct the assumptions, the two "Open questions" blocks come out and the spec is ready for `/blueprint`.

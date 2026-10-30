# Transcript: spec for overdue tickets (with_skill, run-3)

## Task prompt

Execute this task exactly as a user would have asked it, using the skill at the given path.

- Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule2/skills/spec. Read that directory's SKILL.md first and follow it, reading its references when it says to. `<plugin root>` for this skill is /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule2. Use ONLY the files under that root: do not invoke the Skill tool, and do not use any installed skill (including swd:spec). Do not read anything outside the run directory and the plugin root.
- Task: The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-5/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to .../run-3/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.

(The full prompt also asked for this transcript and a one-paragraph reply to the caller.)

## Skill files read, in order

1. `skills/spec/SKILL.md`, first, before anything in the repo.
2. `scripts/prose-lint.py` (top 200 lines), before drafting, to learn what the step 5 lint checks.
3. `assets/writing.md`, at step 4, before drafting.

`skills/spec/references/format.md` was not read. SKILL.md says to read it only when the repo
has no spec convention, and this repo has one (`docs/product-specs/`, `PREFIX-NNN` IDs).

## Commands run

Paths: `$P` = the plugin root, `$R` = the run directory, `$REPO` = `$R/outputs/repo`. The
commands below were run with the absolute paths spelled out.

1. `cd $P && find . -type f | grep -v '^./evals' | head -100 && cat skills/spec/SKILL.md`
   Result: listed the plugin files and printed SKILL.md.
2. `cd $R && ls -la . outputs && cd outputs/repo && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print`
   Result: clean tree on `main`, one commit, docs under `docs/product-specs/`.
3. `cd $REPO && for f in AGENTS.md README.md docs/README.md docs/product-specs/README.md docs/product-specs/invariants.md docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/event-log.md; do echo "=== $f"; cat $f; done`
   Result: read the spec convention (one file per feature area, prefix per file, TODO notes for open questions) and every spec.
4. `cd $REPO && for f in docs/architecture.md docs/guidelines.md ticketdesk/*.py tests/test_tickets.py; do echo "=== $f"; cat $f; done`
   Result: confirmed the due time is computed but never shown, and `list` output matches CLI-006.
5. `cat $P/assets/writing.md`
   Result: read the writing rules.
6. `sed -n 1,200p $P/scripts/prose-lint.py`
   Result: read the linter rules and what it skips.
7. `cd $REPO && python3 $P/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo "exit=$?"`
   Result: baseline, 0 findings.
8. Read tool on `tickets.md`, `cli.md`, `docs/product-specs/README.md`, `AGENTS.md` (line ranges), then an Edit of the `tickets.md` intro.
   Result: added the purpose, the "overdue is derived, never logged" contract, and the non-goals.
9. `cd $REPO && cat >> docs/product-specs/tickets.md <<'EOF' ... EOF`
   Result: appended TKT-014 to TKT-019.
10. `cd $REPO && python3 - <<'EOF' ... EOF` (edit CLI-001 and CLI-006, append CLI-010 to CLI-014), then `python3 $P/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo "exit=$?"`
    Result: edits applied, 0 findings.
11. `cd $REPO && python3 - <<'EOF' ... EOF` (reword a TODO lead in CLI-011, add "overdue tickets" to the tickets.md rows in `docs/product-specs/README.md` and `AGENTS.md`), then the same lint, `git status --short`, `git diff --stat`
    Result: 0 findings, four files modified, 109 insertions and 6 deletions.
12. `cd $R/outputs && cat > questions.md <<'EOF' ... EOF` then `python3 $P/scripts/prose-lint.py questions.md; echo "exit=$?"`
    Result: questions written, 0 findings.
13. `cd $REPO && git diff docs/product-specs/cli.md | head -40`
    Result: found a CLI-001 line over the file's wrap width.
14. `cd $REPO && python3 - <<'EOF' ... EOF` (rewrap CLI-001), then the same lint and `git status --short`
    Result: 0 findings, same four files modified, nothing committed.
15. `cd $R && cat > transcript.md <<'EOF' ... EOF`
    Result: wrote this file.
16. `cd $R && python3 - <<'EOF' ... EOF` (reword a teaser lead in the final message), then `python3 $P/scripts/prose-lint.py transcript.md`
    Result: the final message is clean. The 3 remaining findings are in the quoted prompt and a quoted command.

## Final message to the user

I amended the existing specs instead of creating a new file. The repo groups specs by
feature area. Ticket rules live in `tickets.md` (TKT) and the command surface lives in
`cli.md` (CLI). Its docs README says to update an existing doc instead of fragmenting.

What changed, uncommitted:

- `docs/product-specs/tickets.md`: the purpose, the non-goals, the contract "overdue is
  derived, never logged", and TKT-014 to TKT-019.
- `docs/product-specs/cli.md`: CLI-001 now lists five subcommands. CLI-006 points to the
  new marker. New items are CLI-010 to CLI-014.
- The tickets.md rows in `docs/product-specs/README.md` and `AGENTS.md` now mention overdue
  tickets.

Sign-off waits on these questions. They are also in `outputs/questions.md` and as TODOs in
the spec:

1. Does `OVERDUE` replace the state word in `list`, or follow it? I assumed it follows it:
   `#1 [P1] assigned OVERDUE Printer on fire`.
2. Can a ticket closed after its due time be overdue? I assumed no.
3. Should `overdue` show the due time or how late a ticket is? I assumed no.

Points to check before you sign off:

- TKT-015, the exact-due-time boundary, needs a controlled clock to test. A black-box CLI
  test cannot hit that instant. The other criteria are testable with a hand-written log
  whose `created` time is in the past.
- CLI-010 changes the `list` line of an overdue ticket. A script that parses `list` output
  sees a new word on those lines.
- CLI-014 ties `overdue` to the open conflict under CLI-007. It does not resolve it.
- No code changed and nothing is committed. Please sign off before `/blueprint` cites
  these IDs.

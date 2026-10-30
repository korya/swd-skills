# Transcript: spec for overdue tickets (with_skill, run-1)

## Task prompt

> The fixture is already built. Work inside
> /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo.
> Spec this out before anyone plans or builds it: support agents want tickets that pass
> their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue`
> command that lists only overdue tickets, oldest due first. Write the spec into the repo's
> docs the way the repo does specs. Nobody is available to answer questions during this
> run: where the skill would ask me, write the questions to
> /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/questions.md,
> state the assumption you proceed on, and continue. Do not change any code. Do not commit.

Skill used: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new/skills/spec
(`<plugin root>` = /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new).

## Skill files read, and when

1. `skills/spec/SKILL.md`: first action, before touching the repo (command 1).
2. `references/format.md`: not read. SKILL.md says to read it at step 1 only when the repo
   has no spec convention. The repo has one: `docs/product-specs/`, `PREFIX-NNN` IDs,
   prefix table, prose feature-local invariants, inline `TODO:` notes.
3. `assets/writing.md`: at step 4, after orienting and before drafting (command 5).
4. `scripts/prose-lint.py`: run (not read) at baseline and at step 5.

## Commands

Commands use these abbreviations in this list only. The real commands used full paths.

- `$R` = /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-2/eval-1-spec-overdue-tickets/with_skill/run-1
- `$S` / `$P` = /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new
- `LINT` = `python3 $P/scripts/prose-lint.py`

1. `S=$P; find $S -type f | head -100; echo; cat $S/skills/spec/SKILL.md`
   Result: listed the snapshot files and printed SKILL.md.
2. `R=$R; ls -la $R $R/outputs; cd $R/outputs/repo && git status && git log --oneline | head; find . -path ./.git -prune -o -type f -print`
   Result: clean tree on `main`, one commit `defae68`, specs under `docs/product-specs/`.
3. `cd $R/outputs/repo && for f in AGENTS.md README.md docs/README.md docs/product-specs/*.md docs/architecture.md docs/guidelines.md; do echo "===== $f"; cat "$f"; done`
   Result: output was persisted to a file and read with the Read tool. Found the TKT, LOG,
   CLI, INV specs, the TKT-005 due time, the CLI-006 list line, and the open TODO under CLI-007.
4. `cd $R/outputs/repo && cat ticketdesk/*.py tests/*.py Makefile pyproject.toml`
   Result: confirmed `list` prints `#<id> [<priority>] <state:<8> <title>`, due time is
   computed on replay, and no overdue concept exists.
5. `cat $P/assets/writing.md`
   Result: read the writing rules.
6. `cd $R/outputs/repo && for f in docs/product-specs/tickets.md docs/product-specs/cli.md; do LINT $f; echo "exit=$?"; done`
   Result: baseline, 0 findings in each file.
7. Write tool: created `$R/outputs/questions.md` with 8 questions and their assumptions.
8. `cd $R/outputs/repo/docs/product-specs && python3 - <<'EOF' ... EOF` (Python script that
   inserts the overdue intro and non-goals list into tickets.md and appends TKT-014 to TKT-016)
   Result: tickets.md amended.
9. `cd $R/outputs && python3 - <<'EOF' ... EOF; grep -n "TKT-01" questions.md` (rewords the
   two TODO notes in tickets.md and replaces `TKT-017` with `TKT-016` in questions.md)
   Result: TODOs fixed, questions.md references TKT-016.
10. `cd $R/outputs/repo/docs/product-specs && python3 - <<'EOF' ... EOF; cd .. && cd .. && LINT docs/product-specs/tickets.md; LINT docs/product-specs/cli.md`
    (amends CLI-001 and CLI-006, appends CLI-010 to CLI-012, then lints)
    Result: tickets.md line 103 long-lead (21 words), cli.md 0 findings.
11. `cd $R/outputs/repo && python3 - <<'EOF' ... EOF; for f in ...; do LINT $f; done; git diff docs/product-specs/tickets.md | head -80`
    (shortens the TKT-014 lead)
    Result: 0 findings in both files.
12. `cd $R/outputs/repo && python3 - <<'EOF' ... EOF; for f in ...; do LINT $f; done; awk 'length>90{print FILENAME": "FNR": "length}' docs/product-specs/tickets.md docs/product-specs/cli.md`
    (splits the overdue intro into a goal paragraph and an invariant paragraph)
    Result: 0 lint findings, 5 lines wider than 90 characters.
13. `cd $R/outputs/repo && sed -n '105,118p' docs/product-specs/tickets.md; sed -n '15p;67p' docs/product-specs/cli.md; git show HEAD:docs/product-specs/cli.md | awk 'length>90'`
    Result: showed the wide lines. One of them is pre-existing in the original cli.md.
14. `cd $R/outputs/repo && python3 - <<'EOF' ... EOF; for f in ...; do LINT $f; done; awk 'length>90{print FILENAME": "FNR}' docs/product-specs/*.md; git diff docs/product-specs/cli.md`
    (rewraps the wide lines)
    Result: 0 lint findings. One wide line left in tickets.md. The others are pre-existing
    table rows in untouched files.
15. `cd $R/outputs/repo && sed -n '105,111p' docs/product-specs/tickets.md`
    Result: showed the TKT-014 paragraph.
16. `cd $R/outputs/repo && python3 - <<'EOF' ... EOF; awk 'length>90{print FILENAME": "FNR}' docs/product-specs/tickets.md; LINT docs/product-specs/tickets.md`
    Result: no wide lines, 0 findings.
17. `cd $R/outputs/repo && python3 - <<'EOF' ... EOF; git status --short; git diff --stat`
    (updates the tickets.md and cli.md summaries in the AGENTS.md doc table and in the
    product-specs README index)
    Result: 4 files modified, 87 insertions, 9 deletions. No code touched.
18. `cd $R/outputs && LINT questions.md; cd repo && git status --short && git log --oneline | head -1`
    Result: questions.md 0 findings. HEAD is still `defae68`, so nothing was committed.
19. Write tool: created this transcript.

The heredoc bodies of commands 8 to 17 were Python scripts that call `str.replace` on exact
old and new text. Each one asserts that the old text exists. Their effect is the final
`git diff` of the repo.

## Final message to the user

I amended two existing spec files and created no new spec file. Overdue is a ticket rule
next to the TKT-005 due time, and the new command belongs on the CLI surface, so a new file
would fragment both. `docs/product-specs/tickets.md` gets an overdue intro with goals and
non-goals, the feature-local invariant (overdue is computed when a command runs and is
never logged), and TKT-014 (definition), TKT-015 (overdue changes nothing in the ticket or
the log), and TKT-016 (only overdue tickets, oldest due time first, ties by ID).
`docs/product-specs/cli.md` amends CLI-001 (five subcommands) and CLI-006 (points to the
marker), and adds CLI-010 (`OVERDUE` marker in `list`), CLI-011 (`ticketdesk overdue`), and
CLI-012 (reads the log, never writes it, missing-file and corrupt-line behavior). I also
updated the summaries in `AGENTS.md` and `docs/product-specs/README.md`. No code changed and
nothing is committed. All touched spec files pass prose-lint.

Open questions, in `outputs/questions.md` and as `TODO:` lines in the spec:

1. Does `OVERDUE` replace the state or join it? Assumed: it joins it.
2. Can a ticket closed late be overdue? Assumed: never.
3. Does a script read the `list` output by column? Assumed: no.
4. Is a ticket overdue at its due time exactly? Assumed: only after it.
5. Does the `overdue` line show the due time or lateness? Assumed: no.
6. What breaks a tie on due time? Assumed: the lower ID.
7. Does the `overdue` exit code signal overdue tickets? Assumed: no, always 0.
8. Does the CLI-007 corrupt-log conflict extend to `overdue`? Assumed: yes, one decision
   covers both.

The spec is a draft until you sign off. Questions 1 to 3 change its shape, so please
answer them before `/blueprint` cites these IDs.

# Transcript: spec for overdue tickets (old_skill, run 3)

## Task prompt

> The fixture is already built. Work inside
> /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-3/outputs/repo.
> Spec this out before anyone plans or builds it: support agents want tickets that pass
> their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue`
> command that lists only overdue tickets, oldest due first. Write the spec into the repo's
> docs the way the repo does specs. Nobody is available to answer questions during this
> run: where the skill would ask me, write the questions to
> /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-3/outputs/questions.md,
> state the assumption you proceed on, and continue. Do not change any code. Do not commit.

Skill used: `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/skills/spec`.
Below, `$SNAP` is `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old`
and `$RUN` is `/Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-3`.
The commands were run with the full paths. Long heredoc bodies are shown as a pointer to
the file they produced, because the full text is in that file now.

## Skill files read, and when

1. `skills/spec/SKILL.md`: first, before anything else (command 1).
2. `assets/writing.md`: at step 4, before drafting (command 5).
3. `skills/spec/references/format.md`: not read. The SKILL.md says to read it only when
   the repo has no spec convention. The repo has one (`docs/product-specs/`, `PREFIX-NNN`
   IDs). Command 5 also tried to `cat` it, but zsh failed on `echo ====` first.
4. `scripts/prose-lint.py`: run at step 5 (commands 11, 12, 13, 14).

## Commands

1. `cd $SNAP && find . -type f | sort && cat skills/spec/SKILL.md`
   Result: listed the snapshot files and printed SKILL.md.
2. `cd $RUN && find . -type f -not -path '*/.git/*' | sort`
   Result: the repo has AGENTS.md, docs/ with product-specs (tickets, cli, event-log, invariants, README), and the ticketdesk package.
3. `cd $RUN/outputs/repo && for f in AGENTS.md docs/README.md docs/product-specs/README.md docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/invariants.md docs/product-specs/event-log.md; do echo "=== $f"; cat "$f"; done; git status; git log --oneline | head`
   Result: found the spec convention (one file per feature area, `PREFIX-NNN` IDs, prose criteria, append-only IDs, TODO notes for open conflicts). Clean tree on `main`, one commit.
4. `cd $RUN/outputs/repo && for f in docs/architecture.md docs/guidelines.md ticketdesk/cli.py ticketdesk/tickets.py ticketdesk/sla.py README.md; do echo "=== $f"; cat "$f"; done`
   Result: confirmed current behavior. `list` prints `#<id> [<priority>] <state:8> <title>`. Due time is derived on replay. No overdue concept exists.
5. `cd $SNAP && cat assets/writing.md; echo ====; cat skills/spec/references/format.md`
   Result: printed writing.md. zsh then failed on `====` with "=== not found", exit 1. format.md was not printed and was not needed.
6. Read tool (not shell): `tickets.md` lines 1-12, `cli.md`, `event-log.md` lines 1-20, `product-specs/README.md` from line 75, `AGENTS.md` lines 75-86.
   Result: loaded the exact text to edit.
7. Edit tool (not shell): added the overdue paragraph to the intro of `docs/product-specs/tickets.md`.
   Result: file updated.
8. `cat >> $RUN/outputs/repo/docs/product-specs/tickets.md <<'EOF' ... EOF`, body = TKT-014 to TKT-017, the "out of scope" section, and open questions 1-7, as now in that file.
   Result: appended.
9. `cd $RUN/outputs/repo/docs/product-specs && python3 - <<'EOF' ... EOF`, a script that replaced the table cell `72 hours and 4 hours before` with `76 hours before` and appended open question 8. Then `tail -5 tickets.md`.
   Result: table fixed, question 8 added.
10. `cd $RUN/outputs/repo && python3 - <<'EOF' ... EOF; git status --short`, a script with exact-match replacements: amend CLI-001 and CLI-006, add CLI-010, amend LOG-001, add "overdue tickets" to the tickets.md rows in `product-specs/README.md` and `AGENTS.md`.
    Result: 5 files modified (AGENTS.md, product-specs/README.md, cli.md, event-log.md, tickets.md).
11. `cd $RUN/outputs/repo && for f in docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/event-log.md; do echo "--- $f"; python3 $SNAP/scripts/prose-lint.py $f; echo "exit $?"; done`
    Result: 1 finding, `tickets.md:94: long-lead: Paragraph lead has 21 words (max 20)`. cli.md and event-log.md clean.
12. `cd $RUN/outputs/repo && python3 - <<'EOF' ... EOF` (reworded the TKT-014 lead to "An `open` or `assigned` ticket is overdue when the current time is later than its due time"), then `python3 $SNAP/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/event-log.md; git diff --stat`
    Result: 0 findings in 3 files. Diff: 5 files, 121 insertions, 7 deletions.
13. `cat > $RUN/outputs/questions.md <<'EOF' ... EOF` (body as now in that file), then `python3 $SNAP/scripts/prose-lint.py $RUN/outputs/questions.md`
    Result: questions.md written, 0 findings.
14. `cd $RUN/outputs/repo && git diff docs/product-specs/cli.md docs/product-specs/event-log.md | head -80`
    Result: reviewed the diff. Found an awkward LOG-001 sentence ("A ticket that becomes overdue appends nothing").
15. `cd $RUN/outputs/repo && python3 - <<'EOF' ... EOF` (reworded it to "No event is appended when a ticket becomes overdue, see TKT-016."), then `python3 $SNAP/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/event-log.md`
    Result: 0 findings in 3 files.
16. Write tool (not shell): this transcript.

No code changed. Nothing committed.

## Final message to the user

The overdue spec is drafted as an amendment to the existing specs. It needs your sign-off
before `/blueprint` or anyone builds on it.

**What changed in `outputs/repo`:**

- `docs/product-specs/tickets.md`: a prose contract in the intro (overdue is derived, never
  a state or an event). New criteria TKT-014 to TKT-017. An "out of scope" list. Eight open
  questions at the end.
- `docs/product-specs/cli.md`: CLI-001 amended (five subcommands), CLI-006 amended (the
  `OVERDUE` marker in `list`), new CLI-010 (`ticketdesk overdue`).
- `docs/product-specs/event-log.md`: LOG-001 amended (`overdue` appends nothing).
- `docs/product-specs/README.md` and `AGENTS.md`: the tickets.md index rows now mention
  overdue tickets.

Every new or changed item has a `Status: proposed on 2026-10-29. Not built yet.` line,
because the repo has no convention for unbuilt spec items. The spec files pass
`prose-lint.py` with no findings.

**Criteria:**

| ID | Says |
|----|------|
| TKT-014 | `open` or `assigned`, and the current time is later than the due time. Not overdue at exactly the due time. |
| TKT-015 | A `closed` ticket is never overdue, even if it was closed late. |
| TKT-016 | Becoming overdue appends no event and changes nothing else. |
| TKT-017 | Overdue listing: due time ascending, ties by ID ascending, empty when none. |
| CLI-001 (amended) | `overdue` is a fifth subcommand. |
| CLI-006 (amended) | Overdue lines read `#<id> [<priority>] <state> OVERDUE <title>`. |
| CLI-010 | `ticketdesk overdue`: TKT-017 order, CLI-006 overdue lines, no arguments, exit 0 when empty, appends nothing. |
| LOG-001 (amended) | `list` and `overdue` append nothing. |

**Blocking questions, answered by assumption** (all in `outputs/questions.md`):

1. `list` shows OVERDUE as a marker beside the state, not in place of it. Replacing the
   state hides whether someone has the ticket.
2. A ticket closed after its due time is not overdue.
3. Overdue is derived on each command, not recorded in the log.

**Non-blocking:** the exact-due-time boundary, the tie order, whether a script parses
`list` output (the marker changes the line for overdue tickets), whether agents want the
due time shown, the "proposed" status line, and the corrupt-log exit code. The last one
follows the open TODO under CLI-007, which this spec does not settle.

**One thing to know before testing:** a black-box test of TKT-014 needs a ticket past its
due time. Without a way to set the current time (a non-goal here), a tester writes a log
with old `at` values by hand. The log is a product surface (LOG-003, LOG-005), so that is
legitimate. Say so if you would rather have an option for it.

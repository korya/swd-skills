# Transcript: spec for overdue tickets (with_skill, run-1)

## Task prompt

> The fixture is already built. Work inside
> /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo.
> Spec this out before anyone plans or builds it: support agents want tickets that pass
> their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue`
> command that lists only overdue tickets, oldest due first. Write the spec into the repo's
> docs the way the repo does specs. Nobody is available to answer questions during this
> run: where the skill would ask me, write the questions to
> /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/questions.md,
> state the assumption you proceed on, and continue. Do not change any code. Do not commit.

Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new/skills/spec

## Skill files read, and when

1. `skills/spec/SKILL.md`: first, before touching the repo (command 1).
2. `references/format.md`: not read. SKILL.md step 1 says to read it only when the repo has
   no spec convention. The repo has one: `docs/product-specs/` with per-area files, a
   prefix table, and `PREFIX-NNN` IDs.
3. `assets/writing.md`: at step 4, before drafting (command 5).
4. `scripts/prose-lint.py`: run at step 5 (commands 6, 8, 10, 13). Run once before the
   edits as a baseline.

## Commands run

Shell commands, verbatim, with a one-line result note. `S` and `R` are the paths set
inside each command.

1. `S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new; ls -R $S/skills/spec; cat $S/skills/spec/SKILL.md`
   Result: the skill has SKILL.md and references/format.md. Read the workflow.
2. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1 && ls -la . outputs && find outputs/repo -not -path '*/.git/*' -type f | head -100`
   Result: found the repo with `docs/product-specs/` holding tickets, cli, event-log, invariants.
3. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo && for f in AGENTS.md README.md docs/README.md docs/product-specs/README.md docs/product-specs/invariants.md docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/event-log.md; do echo "=== $f"; cat $f; done`
   Result: read the spec convention, TKT-001 to TKT-013, CLI-001 to CLI-009, LOG-001 to LOG-009, INV-001 to INV-005.
4. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo && for f in ticketdesk/*.py docs/architecture.md docs/guidelines.md; do echo "=== $f"; cat $f; done; git status --short; git log --oneline | head`
   Result: confirmed current `list` output and due time computation. Clean tree, one commit.
5. `S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new; ls $S $S/assets $S/scripts; cat $S/assets/writing.md`
   Result: read the writing rules. Found scripts/prose-lint.py.
6. `S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new; R=/Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo; python3 $S/scripts/prose-lint.py $R/docs/product-specs/tickets.md $R/docs/product-specs/cli.md; echo "exit=$?"`
   Result: baseline `0 findings in 2 files`.
7. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo && cat tests/test_tickets.py | head -40 && cat Makefile`
   Result: tests inject a fake clock into the store. No CLI tests.
8. Appended the open questions sections to both spec files, then linted:
   ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo/docs/product-specs && cat >> tickets.md <<'EOF'

   ---

   ## Open questions

   TKT-014 to TKT-017 are a draft that waits for user sign-off. Each question below names the
   assumption the draft uses.

   - **Can a closed ticket be overdue?** The draft says no, see TKT-015.
   - **Is a ticket overdue at the exact due time?** The draft says no, see TKT-014.
   - **Does assigning a ticket move or pause its due time?** The draft says no, see TKT-016.
   EOF
   cat >> cli.md <<'EOF'

   ---

   ## Open questions

   The `OVERDUE` part of CLI-006, CLI-010, and CLI-011 is a draft that waits for user
   sign-off. Each question below names the assumption the draft uses.

   - **Does `OVERDUE` replace the state in `list`, or appear next to it?** The draft keeps the
     state and adds `OVERDUE` after it, see CLI-006. A title that starts with the word
     `OVERDUE` then reads the same as an overdue ticket.
   - **Does `overdue` print the same line as `list`?** The draft says yes, see CLI-010.
   - **How do `overdue` errors behave?** The draft gives `overdue` the same behavior as `list`.
     A corrupt log line escapes as a traceback today. The TODO under CLI-007 covers this case
     for both commands.
   EOF
   python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new/scripts/prose-lint.py tickets.md cli.md; echo "exit=$?"
   ```
   Result: 2 findings in tickets.md. A teaser lead on the out-of-scope list, and a 21-word lead in TKT-014.
9. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo/docs/product-specs && sed -n '14,24p;98,110p' tickets.md`
   Result: showed the two flagged paragraphs.
10. Rewrote the two flagged paragraphs, then linted:
    ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo/docs/product-specs && python3 - <<'EOF'
    from pathlib import Path
    p = Path("tickets.md"); s = p.read_text()
    old1 = "Overdue tickets do not include the following. Each one is out of scope:\n"
    new1 = "Overdue tickets send no notification and trigger no escalation. These behaviors stay out of\nscope:\n"
    old2 = ("A ticket is overdue when its state is `open` or `assigned` and the current time is later\n"
            "than its due time, see TKT-005. The current time is the clock at the moment the command\n"
            "runs. A ticket whose due time equals the current time is not overdue.\n")
    new2 = ("An `open` or `assigned` ticket is overdue when the current time is later than its due\n"
            "time. The due time comes from TKT-005. The current time is the clock at the moment the\n"
            "command runs. A ticket whose due time equals the current time is not overdue.\n")
    assert s.count(old1) == 1 and s.count(old2) == 1
    p.write_text(s.replace(old1, new1).replace(old2, new2))
    EOF
    python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new/scripts/prose-lint.py tickets.md cli.md; echo "exit=$?"
    ```
    Result: `0 findings in 2 files`.
11. Updated the index rows, then checked the tree:
    ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo && python3 - <<'EOF'
    from pathlib import Path
    edits = {
     "docs/product-specs/README.md": ("closing, due time by priority, listing. |", "closing, due time by priority, listing, overdue tickets. |"),
     "AGENTS.md": ("closing, due time by priority, listing. |", "closing, due time by priority, listing, overdue. |"),
    }
    for f,(o,n) in edits.items():
        p=Path(f); s=p.read_text(); assert s.count(o)==1, f; p.write_text(s.replace(o,n))
    EOF
    git status --short && git diff --stat
    ```
    Result: 4 files modified (AGENTS.md, product-specs/README.md, cli.md, tickets.md). No code touched.
12. `cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo && git diff docs/product-specs/cli.md | head -30`
    Result: found that the CLI-001 edit left a line over the file's wrap width.
13. Rewrapped CLI-001, then linted:
    ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo/docs/product-specs && python3 - <<'EOF'
    from pathlib import Path
    p=Path("cli.md"); s=p.read_text()
    o="`close`, `list`, and `overdue`. Invoking `ticketdesk` with no subcommand, or with an unknown one,\nprints usage to stderr and exits with code 2.\n"
    n="`close`, `list`, and `overdue`. Invoking `ticketdesk` with no subcommand, or with an\nunknown one, prints usage to stderr and exits with code 2.\n"
    assert s.count(o)==1; p.write_text(s.replace(o,n))
    EOF
    python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-new/scripts/prose-lint.py tickets.md cli.md; echo "exit=$?"
    ```
    Result: `0 findings in 2 files`.

Non-shell file actions (editor tool, not commands):

- Wrote `outputs/questions.md`: 3 blocking questions and 5 open questions, each with its assumption.
- Edited `docs/product-specs/tickets.md`: added the overdue overview and the out-of-scope list to the intro. Added TKT-014 to TKT-017.
- Edited `docs/product-specs/cli.md`: amended CLI-001 (five subcommands) and CLI-006 (overdue line). Added CLI-010 and CLI-011.
- The first batch of edits failed because the files had not been opened with the editor's read. I read the first lines of each file and repeated the edits.

## Final message to the user

I wrote the overdue spec as an amendment to the repo's existing specs. I did not create a
new file. The repo keeps one spec file per area under `docs/product-specs/`, with
`PREFIX-NNN` IDs, so the feature splits across two files.

- `docs/product-specs/tickets.md`: an overview and an out-of-scope list in the intro. New
  criteria TKT-014 (when a ticket is overdue), TKT-015 (closed is never overdue), TKT-016
  (assigning keeps the due time), and TKT-017 (overdue order: due time ascending, then ID).
  An open questions section at the end.
- `docs/product-specs/cli.md`: CLI-001 amended to five subcommands. CLI-006 amended with the
  overdue line `#<id> [<priority>] <state> OVERDUE <title>`. New CLI-010 (`ticketdesk overdue`)
  and CLI-011 (extra arguments are a usage error). An open questions section at the end.
- Index rows in `docs/product-specs/README.md` and `AGENTS.md` now mention overdue.

Both spec files pass `prose-lint.py` with no findings. No code changed. Nothing committed.

Two edits change existing contracts and need your sign-off. CLI-001 changes from four
subcommands to five. CLI-006 gives overdue tickets a different line.

Three blocking questions are in `outputs/questions.md`, each with the assumption I used:

1. Can a closed ticket be overdue? I assumed no.
2. Does `OVERDUE` replace the state in `list`, or appear next to it? I assumed next to it.
   A title that starts with `OVERDUE` then reads the same as an overdue ticket.
3. Is a ticket overdue at the exact due time? I assumed no, only after it.

The open questions cover the `overdue` line format, showing the due time, and the due time
on assignment. They also cover `overdue` errors, which share the open TODO under CLI-007.
Please sign off on the spec before `/blueprint` or a build cites it.

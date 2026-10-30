# Transcript: spec overdue tickets (old_skill, run 2)

## Task prompt

> Execute this task exactly as a user would have asked it, using the skill at the given path.
>
> - Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/skills/spec. Read that directory's SKILL.md first and follow it, reading its references when it says to. `<plugin root>` for this skill is /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old. Use ONLY the files under /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old: do not invoke the Skill tool, and do not use any installed skill (including swd:spec). Do not read anything outside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2 and /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old.
> - Task: The fixture is already built. Work inside /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo. Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.
>
> When you finish, write .../run-2/transcript.md: the task prompt, a numbered list of every command you ran (verbatim) with a one-line result note, which skill files you read and when, and your final message to the user verbatim. Do not write anything else outside .../run-2. Your final reply to me is one short paragraph: which spec files you created or changed, the criterion IDs, and the open questions.

## Commands and tool calls

Shorthand used below only in this heading: `$RUN` is
`/Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2`.
The commands themselves are copied verbatim.

1. Read tool: `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/prompts/sp3-old_skill-r2.txt`. Result: the task prompt.
2. ```
   S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old; find $S -type f | head -50; cat $S/skills/spec/SKILL.md
   ```
   Result: listed the snapshot files and printed the spec SKILL.md.
3. ```
   R=/Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2; ls -la $R $R/outputs; cd $R/outputs/repo && git status && git log --oneline | head; find . -path ./.git -prune -o -type f -print
   ```
   Result: clean `main` branch at 6e30541. Specs live in `docs/product-specs/` with per-file prefixes.
4. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo && for f in AGENTS.md README.md docs/README.md docs/product-specs/*.md docs/architecture.md docs/guidelines.md; do echo "=== $f"; cat $f; done
   ```
   Result: output was persisted to a tool-results file because of its size.
5. Read tool: `/Users/dmitri/.claude/projects/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/tool-results/bpftphi7o.txt`. Result: the full output of command 4, the repo docs only. Found the convention: `PREFIX-NNN` IDs, TKT and CLI files, inline TODO notes, prose feature-local invariants.
6. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo && cat ticketdesk/cli.py ticketdesk/tickets.py ticketdesk/sla.py ticketdesk/store.py
   ```
   Result: confirmed the current `list` line format and that due time is derived on replay.
7. ```
   S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old; cat $S/assets/writing.md; head -60 $S/scripts/prose-lint.py
   ```
   Result: read the writing rules and the linter usage.
8. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo && python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo exit=$?
   ```
   Result: baseline `0 findings in 2 files`, exit 0.
9. Write tool: `$RUN/outputs/questions.md`. Result: 10 questions, each with its assumption.
10. ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo/docs/product-specs && python3 - <<'EOF'
    p='tickets.md'
    s=open(p).read()
    old="""from `open` to `closed`. Nothing reopens a closed ticket.
    """
    new="""from `open` to `closed`. Nothing reopens a closed ticket.

    Overdue is a condition, not a state. A ticket that is still `open` or `assigned` becomes
    overdue when its due time passes. The help desk works it out each time a command runs and
    never records it in the log, see INV-001. Replay still yields the same due times, see
    LOG-009. Only the current time decides whether a ticket is overdue.

    Overdue tickets trigger nothing else. The help desk sends no notification and escalates
    nothing. It changes no priority, state, assignee, or due time. Due times keep counting
    every hour of the day, with no business hours.
    """
    assert s.count(old)==1
    s=s.replace(old,new)
    s=s.rstrip("\n")+"""

    ### TKT-014: Overdue tickets

    A ticket is overdue when its state is `open` or `assigned` and the current time is later
    than its due time, see TKT-005. At exactly its due time, a ticket is not yet overdue. A
    `closed` ticket is never overdue, even when it was closed after its due time. The current
    time is the clock of the machine when the command runs.

    TODO: the rule for closed tickets is an assumption. Confirm with the user whether a ticket
    closed after its due time should count as overdue.

    ### TKT-015: Overdue is not a state

    A ticket that becomes overdue keeps its state and its assignee. No event is appended when
    a ticket becomes overdue. Assigning or closing an overdue ticket follows TKT-006 to TKT-011
    unchanged. A closed ticket is no longer overdue, see TKT-014.

    ### TKT-016: Overdue listing

    Listing overdue tickets returns only the tickets that are overdue per TKT-014. They are
    sorted by due time ascending, so the ticket that has been due longest comes first. Tickets
    with the same due time are sorted by ID ascending. With no overdue tickets, the list is
    empty.
    """
    open(p,'w').write(s)
    EOF
    ```
    Result: added the overdue prose and TKT-014 to TKT-016 to `tickets.md`. No output.
11. ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo/docs/product-specs && python3 - <<'EOF'
    p='cli.md'
    s=open(p).read()
    reps=[
    ("""The `ticketdesk` command takes one of four subcommands. They are `create`, `assign`,
    `close`, and `list`. Invoking""",
    """The `ticketdesk` command takes one of five subcommands. They are `create`, `assign`,
    `close`, `list`, and `overdue`. Invoking"""),
    ("""`ticketdesk list` prints one line per ticket in ID order, see TKT-013. Each line is
    `#<id> [<priority>] <state> <title>` with the state padded to 8 characters. With no tickets
    it prints nothing.
    """,
    """`ticketdesk list` prints one line per ticket in ID order, see TKT-013. Each line is
    `#<id> [<priority>] <state> <title>` with the state padded to 8 characters. With no tickets
    it prints nothing.

    The line of an overdue ticket, see TKT-014, has the word `OVERDUE` between the padded
    state and the title. The line of any other ticket is unchanged. For example, an open `P1`
    ticket past its due time prints as follows:

    ```
    #1 [P1] open     OVERDUE Printer on fire
    ```

    TODO: the place of `OVERDUE` on the line is an assumption. Confirm with the user that the
    state stays on the line and that `OVERDUE` goes before the title.
    """),
    ]
    for a,b in reps:
        assert s.count(a)==1,a
        s=s.replace(a,b)
    s=s.rstrip("\n")+"""

    ### CLI-010: overdue

    `ticketdesk overdue` prints one line per overdue ticket in the order of TKT-016. Each line
    is the same as the line `list` prints for that ticket, `OVERDUE` included, see CLI-006.
    With no overdue tickets, or no log file, it prints nothing and exits with code 0. It
    appends no event to the log.

    Any argument after `overdue` is a usage error on stderr with exit code 2. A corrupt log
    line stops `overdue` the same way it stops `list`, see LOG-007 and the TODO under CLI-007.
    """
    open(p,'w').write(s)
    EOF
    cd .. && cd .. && git diff --stat; python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo exit=$?
    ```
    Result: amended CLI-001 and CLI-006, added CLI-010. Lint found 1 `long-lead` (21 words) at `tickets.md:98`, the TKT-014 lead.
12. ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo && sed -n 96,102p docs/product-specs/tickets.md
    ```
    Result: showed the TKT-014 paragraph.
13. ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo && python3 - <<'EOF'
    p='docs/product-specs/tickets.md'
    s=open(p).read()
    a="""A ticket is overdue when its state is `open` or `assigned` and the current time is later
    than its due time, see TKT-005. At exactly"""
    b="""An `open` or `assigned` ticket is overdue when the current time is later than its due
    time, see TKT-005. At exactly"""
    assert s.count(a)==1
    open(p,'w').write(s.replace(a,b))
    EOF
    python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo exit=$?
    ```
    Result: rewrote the TKT-014 lead. Lint `0 findings in 2 files`, exit 0.
14. ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo && python3 - <<'EOF'
    reps={
    'docs/product-specs/README.md':[
    ("Ticket lifecycle: states, creation rules, assignment, closing, due time by priority, listing. |",
     "Ticket lifecycle: states, creation rules, assignment, closing, due time by priority, overdue tickets, listing. |"),
    ("subcommands, log path selection, output lines, error reporting, exit codes. |",
     "subcommands including `overdue`, log path selection, output lines, error reporting, exit codes. |")],
    'AGENTS.md':[
    ("Ticket states, creation, assignment, closing, due time by priority, listing. |",
     "Ticket states, creation, assignment, closing, due time by priority, overdue tickets, listing. |"),
    ("Commands, log path selection, output lines, errors, exit codes. |",
     "Commands including `overdue`, log path selection, output lines, errors, exit codes. |")],
    }
    for p,rs in reps.items():
        s=open(p).read()
        for a,b in rs:
            assert s.count(a)==1,(p,a); s=s.replace(a,b)
        open(p,'w').write(s)
    EOF
    git diff; git status --short; python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/README.md AGENTS.md; echo exit=$?
    ```
    Result: updated the index rows. Diff reviewed. Lint `0 findings in 4 files`. Two lines needed reflowing.
15. ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-3/eval-1-spec-overdue-tickets/old_skill/run-2/outputs/repo/docs/product-specs && python3 - <<'EOF'
    for p,a,b in [
    ('cli.md',"""The `ticketdesk` command takes one of five subcommands. They are `create`, `assign`,
    `close`, `list`, and `overdue`. Invoking `ticketdesk` with no subcommand, or with an unknown one,
    prints usage to stderr and exits with code 2.""",
    """The `ticketdesk` command takes one of five subcommands. They are `create`, `assign`,
    `close`, `list`, and `overdue`. Invoking `ticketdesk` with no subcommand, or with an
    unknown one, prints usage to stderr and exits with code 2."""),
    ('tickets.md',"""time, see TKT-005. At exactly its due time, a ticket is not yet overdue. A
    `closed` ticket is never overdue, even when it was closed after its due time. The current
    time is the clock of the machine when the command runs.""",
    """time, see TKT-005. At exactly its due time, a ticket is not yet overdue. A `closed`
    ticket is never overdue, even when it was closed after its due time. The current time is
    the clock of the machine when the command runs.""")]:
        s=open(p).read(); assert s.count(a)==1; open(p,'w').write(s.replace(a,b))
    EOF
    python3 /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-old/scripts/prose-lint.py tickets.md cli.md README.md ../../AGENTS.md; echo exit=$?; cd ../.. && git status --short
    ```
    Result: reflowed CLI-001 and TKT-014. Lint `0 findings in 4 files`, exit 0. Four files modified, nothing committed.
16. This transcript, written with a heredoc to `$RUN/transcript.md`.

## Skill files read

- `skills/spec/SKILL.md`: at the start, command 2, before touching the repo.
- `assets/writing.md`: at step 4, command 7, before drafting.
- `scripts/prose-lint.py`: the docstring header at command 7, then run at step 5 in commands 8, 11, 13, 14, and 15.
- `skills/spec/references/format.md`: not read. The SKILL.md says to read it only when the repo has no spec convention, and this repo has one.

## Final message to the user

I specced the overdue feature as an amendment to the two existing spec files, since the repo already owns due times in `tickets.md` and the command surface in `cli.md`. No code changed and nothing is committed.

**Spec changes**

- `docs/product-specs/tickets.md`: new prose contract under the intro (overdue is a derived condition, never a state or a log event) and the non-goals (no notifications, no escalation, no priority or due-time change, no business hours). New criteria TKT-014 (what overdue means, strict boundary, closed tickets never overdue), TKT-015 (overdue keeps state and assignee, appends nothing), TKT-016 (overdue listing: due time ascending, ties by ID, empty when none).
- `docs/product-specs/cli.md`: amended CLI-001 (five subcommands) and CLI-006 (`OVERDUE` between the padded state and the title, other lines unchanged). New CLI-010 (`ticketdesk overdue`: same line as `list`, TKT-016 order, prints nothing and exits 0 when none, no arguments, appends nothing, corrupt log behaves like `list`).
- Index rows in `docs/product-specs/README.md` and `AGENTS.md` now mention overdue.
- All four files pass `prose-lint.py` with 0 findings.

**Open questions** (full list with assumptions in `outputs/questions.md`)

1. Overdue as a marker, or a fourth state? Assumed a marker, so TKT-001 stays intact.
2. Where `OVERDUE` sits on the `list` line. Assumed before the title, state kept.
3. Can a closed ticket be overdue if it was closed late? Assumed never.
4. Non-blocking: `overdue` output format, the boundary at exactly the due time, tie order, exit code when overdue tickets exist, filters, and a `--now` option.

**Conflict surfaced:** the open CLI-007 TODO (corrupt log escapes as a traceback). `overdue` inherits whatever that TODO resolves to. I did not decide it.

The spec is a contract, so please sign off, or answer questions 1 to 3, before `/blueprint` plans against it.

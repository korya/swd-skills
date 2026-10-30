# Transcript: spec for overdue tickets

## Task prompt

> The fixture is already built. Work inside
> /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo.
> Spec this out before anyone plans or builds it: support agents want tickets that pass
> their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue`
> command that lists only overdue tickets, oldest due first. Write the spec into the repo's
> docs the way the repo does specs. Nobody is available to answer questions during this
> run: where the skill would ask me, write the questions to
> /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/questions.md,
> state the assumption you proceed on, and continue. Do not change any code. Do not commit.

Skill used: `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule/skills/spec`.

## Skill files read, and when

1. `skills/spec/SKILL.md`: first, in command 1, before any repo work.
2. `skills/spec/references/format.md`: not read. SKILL.md says to read it only when the
   repo has no spec convention. The repo has one (`docs/product-specs/`, `PREFIX-NNN` IDs,
   prefix table, index).
3. `assets/writing.md`: at step 4, in command 5, before drafting the spec.
4. `scripts/prose-lint.py`: run at step 5, in command 9 (not read).

## Commands run

Paths below: `S` is the skill snapshot root, `R` is the run directory.

1. ```
   S=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule; find $S -type f | head -100; echo; cat $S/skills/spec/SKILL.md
   ```
   Result: listed the snapshot files and printed SKILL.md.
2. ```
   R=/Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-1; ls -la $R $R/outputs; cd $R/outputs/repo && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print
   ```
   Result: clean tree on `main`, one commit `c8745c9`. Listed the fixture files.
3. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo; for f in AGENTS.md README.md docs/README.md docs/product-specs/README.md docs/product-specs/invariants.md docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/event-log.md docs/architecture.md docs/guidelines.md; do echo "=== $f"; cat $f; done
   ```
   Result: printed every doc. The output was saved to a tool-results file, which I then read
   in full with the Read tool. Found the spec convention and the open TODO under CLI-007.
4. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo; cat ticketdesk/cli.py ticketdesk/sla.py; sed -n 1,200p ticketdesk/tickets.py
   ```
   Result: confirmed the current `list` line format `#{id} [{priority}] {state:<8} {title}`
   and that due time is creation time plus the SLA hours.
5. ```
   cat /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule/assets/writing.md
   ```
   Result: read the writing rules before drafting.
6. Write tool: created `outputs/repo/docs/product-specs/overdue.md`.
7. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo; grep -rn "list" --include=*.py --include=Makefile --include=*.yml . | grep -v "^./docs"
   ```
   Result: failed. zsh expanded the unquoted globs: `no matches found: --include=*.py`.
8. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo; grep -rn "list" ticketdesk tests Makefile .github pyproject.toml
   ```
   Result: only `tickets.py:46` and `cli.py:18,29`. Nothing in the repo consumes `list`
   output.
9. ```
   cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo/docs/product-specs; python3 - <<'EOF'
   p='cli.md'; s=open(p).read()
   old1="""The `ticketdesk` command takes one of four subcommands. They are `create`, `assign`,
   `close`, and `list`."""
   new1="""The `ticketdesk` command takes one of five subcommands. They are `create`, `assign`,
   `close`, `list`, and `overdue`."""
   old2="""`#<id> [<priority>] <state> <title>` with the state padded to 8 characters. With no tickets
   it prints nothing."""
   new2="""`#<id> [<priority>] <state> <title>` with the state padded to 8 characters. With no tickets
   it prints nothing. An overdue ticket shows `OVERDUE` in place of its state, see CLI-010."""
   assert s.count(old1)==1 and s.count(old2)==1
   s=s.replace(old1,new1).replace(old2,new2)
   s=s.rstrip("\n")+"""

   ### CLI-010: Overdue marker in list

   In `ticketdesk list`, the line of an overdue ticket shows `OVERDUE` in place of the state.
   Overdue is defined in OVD-001 and OVD-002. `OVERDUE` is padded to 8 characters like a
   state. The lines of other tickets do not change. An example:

   ```
   #1 [P1] OVERDUE  Printer on fire
   #2 [P3] open     Update the wiki
   #3 [P2] closed   Reset the VPN token
   ```

   ### CLI-011: overdue

   `ticketdesk overdue` prints one line per overdue ticket in the order of OVD-004. Each line
   is the same as the line of that ticket in `ticketdesk list`. With no overdue tickets it
   prints nothing and exits with code 0. A missing log file counts as no tickets, see LOG-006.
   An extra argument is rejected with a usage error on stderr and exit code 2.
   """
   open(p,'w').write(s)
   EOF
   git diff --stat
   ```
   Result: amended CLI-001 and CLI-006, appended CLI-010 and CLI-011. `cli.md` 22
   insertions, 3 deletions.
10. ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo; python3 - <<'EOF'
    def rep(p, pairs):
        s=open(p).read()
        for o,n in pairs:
            assert s.count(o)==1,(p,o); s=s.replace(o,n)
        open(p,'w').write(s)
    rep('docs/product-specs/README.md',[
    ("| [`cli.md`](cli.md) | `CLI` |\n","| [`cli.md`](cli.md) | `CLI` |\n| [`overdue.md`](overdue.md) | `OVD` |\n"),
    ("| [`cli.md`](cli.md) | The `ticketdesk` command: subcommands, log path selection, output lines, error reporting, exit codes. |\n",
     "| [`cli.md`](cli.md) | The `ticketdesk` command: subcommands, log path selection, output lines, error reporting, exit codes. |\n| [`overdue.md`](overdue.md) | Overdue tickets: when a ticket is overdue, the closed-ticket rule, overdue order. Draft of 2026-10-29, awaiting sign-off. |\n"),
    ])
    rep('AGENTS.md',[
    ("| Touching `cli.py` or anything a user sees. |\n",
     "| Touching `cli.py` or anything a user sees. |\n| [`docs/product-specs/overdue.md`](docs/product-specs/overdue.md) | `OVD` | When a ticket is overdue, the closed-ticket rule, overdue order. Draft, awaiting sign-off. | Touching due times, `list` output, or the `overdue` command. |\n"),
    ])
    EOF
    git status --short; git diff
    ```
    Result: registered `overdue.md` in the prefix table and index of
    `docs/product-specs/README.md` and in the `AGENTS.md` documents table, as `docs/README.md`
    requires for a new spec file. Reviewed the diff and saw that CLI-001 had a line over 90
    characters and that CLI-011 did not name the corrupt-log behavior.
11. ```
    cd /Users/dmitri/dev/swd-skills-spsimplify/evals/spec/workspace/iteration-4/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo/docs/product-specs; python3 - <<'EOF'
    p='cli.md'; s=open(p).read()
    pairs=[("""The `ticketdesk` command takes one of five subcommands. They are `create`, `assign`,
    `close`, `list`, and `overdue`. Invoking `ticketdesk` with no subcommand, or with an unknown one,
    prints usage to stderr and exits with code 2.""","""The `ticketdesk` command takes one of five subcommands. They are `create`, `assign`,
    `close`, `list`, and `overdue`. Invoking `ticketdesk` with no subcommand, or with an
    unknown one, prints usage to stderr and exits with code 2."""),
    ("""An extra argument is rejected with a usage error on stderr and exit code 2.
    ""","""A corrupt log line stops the command as LOG-007 describes. An extra argument is rejected
    with a usage error on stderr and exit code 2.
    """)]
    for o,n in pairs:
        assert s.count(o)==1; s=s.replace(o,n)
    open(p,'w').write(s)
    EOF
    L=/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/sp-rule/scripts/prose-lint.py
    python3 $L overdue.md; echo "exit=$?"; python3 $L cli.md; echo "exit=$?"
    ```
    Result: reflowed CLI-001, added the LOG-007 sentence to CLI-011. Prose lint: `0 findings
    in 1 file` for both `overdue.md` and `cli.md`, exit 0.
12. Write tool: created `outputs/questions.md`.
13. Write tool: created this `transcript.md`.

No code changed. Nothing committed.

## Final message to the user

I specced the overdue feature the way this repo does specs. The draft waits for your
sign-off before anyone plans or builds from it.

**Files**

- Created `docs/product-specs/overdue.md`, prefix `OVD`. It holds the overview, goals,
  non-goals, criteria OVD-001 to OVD-004, and open questions.
- Amended `docs/product-specs/cli.md`. CLI-001 now lists five subcommands. CLI-006 points to
  the marker. New items: CLI-010 for the `OVERDUE` marker in `list` and CLI-011 for the
  `overdue` command.
- Registered `overdue.md` in `docs/product-specs/README.md` and in `AGENTS.md`.
- Wrote the questions to `outputs/questions.md`.

**Criteria**

- OVD-001: an `open` or `assigned` ticket is overdue when the current time is later than
  its due time.
- OVD-002: a `closed` ticket is never overdue.
- OVD-003: overdue is not a state. `list` and `overdue` append nothing to the log.
- OVD-004: overdue order is due time ascending, then ID ascending.
- CLI-010: `list` shows `OVERDUE` in place of the state, padded to 8 characters.
- CLI-011: `overdue` prints the `list` lines of overdue tickets in OVD-004 order. Empty
  output and exit 0 when none. LOG-006 and LOG-007 apply. An extra argument gives exit 2.

**Open questions, with the assumption the draft uses**

1. Does `OVERDUE` replace the state or join it? Assumed: replaces it. This hides
   `open` against `assigned` on overdue lines.
2. Is a closed ticket ever overdue? Assumed: no.
3. Should `overdue` lines show the due time or lateness? Assumed: no, same line as `list`.
4. Is a ticket overdue at its due time exactly? Assumed: no.
5. How are equal due times ordered? Assumed: by ID.
6. Does any script parse the state column of `list`? Assumed: no. Nothing in the repo does.

**Cross-check notes**

- No conflict with INV-001 to INV-005, TKT-001, TKT-013, or LOG-001 to LOG-009. Overdue is
  computed, never stored.
- `list` output now depends on the time of the run as well as the log. LOG-009 still holds,
  because overdue is not ticket state.
- The open TODO under CLI-007 applies to `overdue` too. The spec does not settle it.

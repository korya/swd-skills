# Transcript: eval-1-spec-overdue-tickets, old_skill, run-3

Paths below use these short forms.

- `<root>` = `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/01058b7d-e98e-4d3f-a81c-e8ba15a8c683/scratchpad/snap/old`
- `<run>` = `/Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/old_skill/run-3`
- `<repo>` = `<run>/outputs/repo`

## Task prompt

Execute this task exactly as a user would have asked it, using the skill at the given path.

- Skill path: `<root>/skills/spec`. Read that directory's SKILL.md first and follow it,
  reading its references when it says to. `<plugin root>` for this skill is `<root>`. Use
  ONLY the files under that plugin root: do not invoke the Skill tool, and do not use any
  installed skill (including swd:spec). Do not read anything outside `<run>` and that
  plugin root. You may use subagents where the skill says so.
- Task: First run `bash <root>/evals/spec/make_fixture.sh <repo>`, then work inside
  `<repo>`. Spec this out before anyone plans or builds it: support agents want tickets
  that pass their due time to show as OVERDUE in `ticketdesk list`, and a new
  `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the
  spec into the repo's docs the way the repo does specs. Nobody is available to answer
  questions during this run: where the skill would ask me, write the questions to
  `<run>/outputs/questions.md`, state the assumption you proceed on, and continue. Do not
  change any code. Do not commit.

If the skill you follow has a cold-read step, also do this bookkeeping: before you change
anything in response to the cold read, save `git -C <repo> diff` plus any new untracked
spec files as they stood into `<run>/outputs/before-cold-read/`. Then write
`<run>/outputs/cold-read.md` with four parts: (1) the exact prompt you gave the subagent,
(2) the subagent's report verbatim, (3) your verdict for each finding with its evidence
and what you changed, and (4) the usage figures the subagent tool returned for that
subagent (tokens, duration, tool uses) if it showed any. If the skill has no such step,
skip this paragraph.

When you finish, write `<run>/transcript.md`: the task prompt, a numbered list of every
command you ran (verbatim) with a one-line result note, which skill files you read and
when, and your final message to the user verbatim. Do not write anything else outside
`<run>`. Your final reply to me is one short paragraph: which spec files you created or
changed, the criterion IDs, and the open questions.

## Skill files read, and when

| Order | File | When | Why |
|---|---|---|---|
| 1 | `<root>/skills/spec/SKILL.md` | First, in parallel with the fixture command | The task says to read it first. |
| 2 | `<root>/assets/writing.md` | Step 4, before drafting | SKILL.md names it as required before drafting. |
| 3 | `<root>/scripts/prose-lint.py` | Before drafting | Read the rules the step 5 linter enforces. |

Not read: `<root>/skills/spec/references/format.md`. SKILL.md says to read it only when the
repo has no spec convention. The fixture repo has one (`docs/product-specs/`, `PREFIX-NNN`
IDs), so the repo's convention wins.

The skill at this path has no cold-read step. I skipped the cold-read bookkeeping. I used
no subagent.

## Commands run

Shell commands, verbatim, in order. Commands 2 to 10 ran after
`cd <repo>` (written out in full in the actual calls).

1. `bash <root>/evals/spec/make_fixture.sh <repo>`
   Result: fixture created, one commit `b8a824c feat(ticketdesk): CLI help desk with event log and agent docs`.

2. `cd <repo> && git status --short && git ls-files && ls <root> <root>/skills/spec <root>/skills/spec/references <root>/assets <root>/scripts`
   Result: clean tree, 21 tracked files. Plugin root holds `assets/writing.md`, `scripts/prose-lint.py`, `skills/spec/references/format.md`.

3. `cd <repo> && for f in AGENTS.md README.md docs/README.md docs/architecture.md docs/guidelines.md docs/product-specs/README.md docs/product-specs/cli.md docs/product-specs/event-log.md docs/product-specs/invariants.md docs/product-specs/tickets.md; do echo "=================== $f"; cat -n "$f"; done`
   Result: output too large, the harness saved it outside the allowed directories. I did not open that file. I read the ten docs one by one with the Read tool instead.

4. `cd <repo> && for f in ticketdesk/cli.py ticketdesk/sla.py ticketdesk/store.py ticketdesk/tickets.py ticketdesk/__init__.py tests/test_store.py tests/test_tickets.py Makefile pyproject.toml .github/workflows/ci.yml; do echo "=================== $f"; cat -n "$f"; done`
   Result: read the code. `list` prints `#{id} [{priority}] {state:<8} {title}`. Due time is creation time plus 4, 24, or 72 hours. No command shows a due time.

5. `cd <repo> && python3 <root>/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo "exit=$?"`
   Result: baseline before editing, `0 findings in 2 files`, exit 0.

6. Probe of current behavior with a hand-written, past-dated log (probe files created under `<run>/outputs/probe` and removed at the end of the same command):

   ```
   cd <repo> && export PYTHONDONTWRITEBYTECODE=1 && S=../probe && mkdir -p $S && L=$S/t.jsonl && NOW=$(python3 -c 'import time;print(time.time())') && python3 - "$L" "$NOW" <<'EOF'
   import json, sys
   p, now = sys.argv[1], float(sys.argv[2])
   evs = [
    {"kind":"created","id":1,"title":"Reset the VPN token","priority":"P3","at":now-80*3600},
    {"kind":"created","id":2,"title":"Printer on fire","priority":"P1","at":now-5*3600},
    {"kind":"created","id":3,"title":"Badge reader offline","priority":"P2","at":now-3600},
    {"kind":"closed","id":1,"resolution":"Issued a new token","at":now-10},
   ]
   open(p,"w").write("".join(json.dumps(e,sort_keys=True)+"\n" for e in evs))
   EOF
   python3 -m ticketdesk.cli --log $L list | cat -A; echo "list exit=$?"; python3 -m ticketdesk.cli --log $L assign 3 dana; python3 -m ticketdesk.cli --log $L list | cat -A
   python3 -m ticketdesk.cli --log $L overdue; echo "overdue exit=$?"
   python3 -m ticketdesk.cli --log $L list extra; echo "list extra exit=$?"
   python3 -m ticketdesk.cli --log $S/missing.jsonl list; echo "missing exit=$?"
   printf 'not json\n' > $S/bad.jsonl; python3 -m ticketdesk.cli --log $S/bad.jsonl list 2>&1 | tail -1; echo "corrupt exit=${pipestatus[1]}"
   rm -rf $S; git status --short; echo "status done"
   ```

   Result: a hand-written log with past `at` values replays fine, so a black-box test can age a ticket. `list` shows no overdue marker today. `overdue` is an invalid choice, usage on stderr, exit 2. `list extra` is a usage error, exit 2. A missing log prints nothing, exit 0. A corrupt log ends in `ValueError: ../probe/bad.jsonl:1: corrupt event: Expecting value: line 1 column 1 (char 0)`, exit 1, which matches the TODO under CLI-007. Repo tree still clean after the probe.

7. `cd <repo> && cat >> docs/product-specs/tickets.md <<'EOF' ... EOF` followed by `git diff --stat`. The heredoc body is the "Overdue tickets" section as it now stands in the file, from the `---` rule before `## Overdue tickets` to the end.
   Result: `docs/product-specs/tickets.md | 96 +++`, one file changed.

8. `cd <repo> && cat >> docs/product-specs/cli.md <<'EOF' ... EOF` followed by `python3 <root>/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md; echo "exit=$?"`. The heredoc body is CLI-010 to CLI-013 as they now stand in the file.
   Result: `0 findings in 2 files`, exit 0.

9. `cd <repo> && python3 <root>/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/README.md AGENTS.md ../questions.md; echo "exit=$?"; git status --short; git diff --stat; grep -n "CLI-01[0-9]\|TKT-01[4-9]" -r docs AGENTS.md | grep -v "^docs/product-specs/\(tickets\|cli\).md:.*### " | head -40`
   Result: the four repo docs are clean. `questions.md` had 2 findings (a 24-word lead, a 27-word sentence). Four files modified, no untracked files. Cross-references to the new IDs are consistent.

10. `cd <repo> && python3 <root>/scripts/prose-lint.py docs/product-specs/tickets.md docs/product-specs/cli.md docs/product-specs/README.md AGENTS.md ../questions.md; echo "exit=$?"; git diff -- docs/product-specs/cli.md AGENTS.md docs/product-specs/README.md; git status --short; git log --oneline | head -3; ls ..`
    Result: `0 findings in 5 files`, exit 0. Diff reviewed. Still one commit, nothing committed, no code file changed.

## File tool calls, in order

- Read: `<root>/skills/spec/SKILL.md`.
- Read: `<repo>/AGENTS.md`, `README.md`, `docs/README.md`, `docs/architecture.md`, `docs/guidelines.md`, and the four files under `docs/product-specs/` plus its `README.md`.
- Read: `<root>/assets/writing.md`, then `<root>/scripts/prose-lint.py`.
- Write: `<run>/outputs/questions.md` (step 3 of the skill, before drafting).
- Edit: `<repo>/docs/product-specs/cli.md`, three edits: the status paragraph and CLI-001, the `OVERDUE` rule and example under CLI-006, then a rewording of that rule to give the exact line.
- Edit: `<repo>/docs/product-specs/README.md`, index row of `tickets.md`.
- Edit: `<repo>/AGENTS.md`, two edits: the `TKT` row and one line under "Current state".
- Edit: `<run>/outputs/questions.md`, three edits: two lint fixes and the limit under Q6.
- Write: `<run>/transcript.md` (this file).

## How the skill's steps mapped to the run

| Step | What happened |
|---|---|
| 1. Orient | The repo has a convention: `docs/product-specs/<feature>.md`, `PREFIX-NNN` IDs, no "Testable:" appendix, feature-local invariants as prose. Chose amend over create. Overdue is a ticket rule built on TKT-005 and its output is command surface, and `docs/README.md` says to update the existing doc instead of fragmenting. |
| 2. Extract | Users: support agents. Pain: no command shows a due time. Touched: TKT-001, TKT-005, TKT-013, CLI-001, CLI-006, CLI-007, CLI-008, LOG-001, LOG-002, LOG-003, LOG-006, LOG-007, LOG-009, INV-001, INV-002. |
| 3. Ask | Four blocking questions and five non-blocking ones written to `outputs/questions.md`, each with its assumption. Nobody was available, so the run continued. |
| 4. Draft | TKT-014 to TKT-017 with goals, non-goals, a feature-local invariant, and open questions in `tickets.md`. CLI-001 and CLI-006 amended, CLI-010 to CLI-013 added in `cli.md`. |
| 5. Cross-check | Each goal names its criteria. Each criterion is checkable through `list` or `overdue` on a hand-written log. No conflict with an existing spec or invariant. The inherited conflict under CLI-007 is surfaced in CLI-013. `prose-lint.py` reports 0 findings. |
| 6. Present and gate | Spec marked "specified but not built, not signed off as of 2026-11-05" in both spec files and in `AGENTS.md`. Sign-off requested in the final message. Nothing committed. |

## Final message to the user, verbatim

I amended the repo's existing specs rather than adding a file: `docs/product-specs/tickets.md` gets a new "Overdue tickets" section (goals, non-goals, a prose invariant, TKT-014 to TKT-017, open questions), and `docs/product-specs/cli.md` gets amended CLI-001 (five subcommands) and CLI-006 (the `OVERDUE` word in `list` lines) plus new CLI-010 to CLI-013 for `ticketdesk overdue`. `docs/product-specs/README.md` and `AGENTS.md` got one-phrase index updates and a "specified, not built, not signed off" line. No code changed, nothing committed, and the skill at this path has no cold-read step, so that bookkeeping was skipped. Criterion IDs: TKT-014 (when a ticket is overdue), TKT-015 (closed is never overdue), TKT-016 (assigning changes nothing), TKT-017 (overdue listing order), CLI-001 and CLI-006 (amended), CLI-010 (the command), CLI-011 (nothing overdue), CLI-012 (no arguments), CLI-013 (corrupt log). Open questions, all in `outputs/questions.md` with the assumption I proceeded on: (1) does the due time target closing or first response (assumed closing, so assigned tickets can be overdue), (2) does a ticket closed late still show as overdue (assumed no), (3) where `OVERDUE` goes in a `list` line and whether it keeps the state (assumed after the state, state kept, other lines byte-identical; cost is that a title starting with `OVERDUE` looks like the marker), (4) should `overdue` show the due time or lateness (assumed no, same line as `list`), (5) "oldest due first" means earliest due time, ties by ID, (6) not overdue at the exact due instant, which a black-box test cannot hit, (7) `overdue` exits 0 even when it prints tickets, (8) corrupt-log reporting inherits the open TODO under CLI-007, (9) amend versus a new `overdue.md`. The spec needs your sign-off before anything plans or builds against it.

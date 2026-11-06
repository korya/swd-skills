# Cold read of plan.md

One fresh subagent (type `general-purpose`, new context, not a fork) read the plan and the
repo. It got the four inputs that `assets/cold-read.md` names and nothing else. The plan as
the reader saw it is saved as `plan-before-cold-read.md`.

## 1. The exact prompt given to the subagent

```text
You review a document before a person signs it off. You have the document, the
repository, and the request that started the work. You have no other context, and that
is deliberate. Change nothing in the repository or the document. You may run the
project's own commands that only read, such as its tests.

Document: /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-4/eval-1-plan-overdue-tickets/with_skill/run-3/outputs/plan.md
Repository: /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-4/eval-1-plan-overdue-tickets/with_skill/run-3/outputs/repo
Request, in the user's words: Plan this change thoroughly, do not implement it: tickets that pass their due time should show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` subcommand should list only overdue tickets, oldest due first. Write the plan to /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-4/eval-1-plan-overdue-tickets/with_skill/run-3/outputs/plan.md. Nobody is available to answer questions during this run: list them as open questions, state the assumption you proceed on, and continue. Do not change any code or docs in the repo.

Do these steps in order.

1. Paraphrase. Read the document and nothing else. Write in your own words what it
   proposes, in two to five sentences. Then write how the existing system works
   according to the document alone, in two to five sentences. If you cannot paraphrase
   a part, name the part and say why.
2. Check the claims. Now open the repository. Test each claim the document makes about
   it: every cited file and line, every named function, command, convention, and ID,
   every quoted value, and every number against its source. Then check the document
   against the project's own rules: its specs, invariants, and conventions.
3. Check the document against itself and the request. Find statements that contradict
   each other. Find a part of the request the document does not cover, and content the
   request did not ask for.
4. Look for what is missing. Name each decision the document leaves to its next reader
   without saying so.

Report in this shape.

PARAPHRASE
<the two paragraphs>

FINDINGS
One block per finding, the most serious first:
- Severity: Blocker, Major, or Minor. A Blocker makes the result wrong. A Major costs
  rework. A Minor is everything else.
- Where: the section or line of the document.
- What: the problem in one or two sentences.
- Evidence: a file and line, a command and its output, or the two passages that
  disagree.

Report a finding only when you can quote its evidence. Wording, style, and length are
not findings. If you find nothing, say so. Do not pad.
```

## 2. The subagent's report, verbatim

The harness indented each line of the report by two spaces. That indent is removed here.
Nothing else is changed.

```text
PARAPHRASE

What the document proposes. Overdue becomes a derived flag, not a stored fact: after the ticket service replays the log it reads the store's clock once and marks every non-closed ticket whose due time is strictly earlier than that reading. `ticketdesk list` keeps its ID order and four-field line, but prints `OVERDUE` in the state column for marked tickets. A new `ticketdesk overdue` prints only marked tickets, sorted by due time and then ID. The work is ordered as: sign-off on the drafted spec text (CLI-001, CLI-006, new CLI-010, TKT-014, TKT-015), spec commit, service commit with ten unit tests, CLI commit with five subprocess tests in a new file, other doc edits, then verification. Seven open questions each carry an assumption, except the sign-off itself.

How the existing system works, by the document alone. A CLI (`cli.py`, argparse) calls a `TicketService` (`tickets.py`), which rebuilds every ticket by replaying an append-only JSON-lines log held by an `EventStore` (`store.py`). Nothing else holds state. Tickets have three states (open, assigned, closed) and a due time computed on replay from creation time plus hours per priority (`sla.py`). Event timestamps come from an injectable clock on the store. Today there are four subcommands, `list` prints `#<id> [<priority>] <state> <title>` with the state padded to 8, a bare `else` handles `list`, the CLI has no tests, there are 7 unit tests, and a corrupt log or unknown priority escapes as a traceback (the open TODO under CLI-007).

I could paraphrase every part.

FINDINGS

No Blockers and no Majors. Five Minors.

- Severity: Minor
- Where: Step 5 (line 162), "Not validated: Python 3.12" (lines 298-300), Risks (line 441)
- What: The only mitigation for the unvalidated Python 3.12 risk is "Push and confirm that CI passes", but the repo has no remote, so that step cannot run as written. The plan also treats 3.12 as unavailable locally, and it is installed.
- Evidence: `git -C repo remote -v` prints nothing, and `git config --get-regexp '^remote\.'` exits 1. `/opt/homebrew/bin/python3.12 --version` gives `Python 3.12.16`. Running the plan's own prototype under it (`scratch/proto`, `python3.12 -m unittest discover -s tests -q`) gives `Ran 11 tests in 0.070s  OK`.

- Severity: Minor
- Where: Plan intro (lines 61-62) against Conventions (lines 335-336) and open question 7 (line 484)
- What: Three statements about what the sign-off gates disagree. Read literally, the first lets the spec edit in step 1 be committed before sign-off, which the repo forbids.
- Evidence: Line 61: "Steps 2 to 4 start only after step 0." Line 336: "step 0 gates steps 1 and 4." Line 484: "no code work starts before it." `AGENTS.md:93`: "Doc changes need user confirmation. Do not silently rewrite specs or architecture."

- Severity: Minor
- Where: Open question 7 (line 483) against Step 4 (lines 147-157)
- What: The reader is asked to approve "the doc edits in step 4", but step 4 gives only locations and intent, not text. Only step 1 has drafted wording. The new test count is also left blank; by the plan's own numbers it is 22 (7 existing, U1-U10, C1-C5).
- Evidence: Line 148: "`docs/architecture.md:68-69`: add one sentence." Line 154: "`AGENTS.md:102`: replace "7 unittest cases" with the new count." Line 156: "`AGENTS.md:114-116`: add overdue to "Done" and update the line about CLI tests."

- Severity: Minor
- Where: Step 4 (lines 147-157)
- What: The doc sweep misses one line that step 3 makes stale. Once `tests/test_cli.py` exists, the layout line in `AGENTS.md` is wrong, and step 4 only touches lines 82, 102, 106, and 114-116 of that file.
- Evidence: `AGENTS.md:47`: "├── tests/              unittest suites for the service and the store".

- Severity: Minor
- Where: Step 3 (lines 136-137, 142-143) against the prototype it cites
- What: The plan calls the bare `else` "a trap" but does not say whether the `overdue` branch is an `elif` or a new bare `else`. The prototype that produced all the quoted evidence keeps a bare `else`, now for `overdue`, so the trap moves and the choice falls to the implementer.
- Evidence: Line 142: "The `else` branch is a trap." `scratch/proto.diff`: `+        elif args.cmd == "list":` followed by `+        else:` / `+            for t in svc.overdue():`.

Request coverage. Both asks are covered (`OVERDUE` in `list`, and `overdue` sorted by due time ascending), the plan was written to the requested path, and nothing in the repo changed (`git status --short` is empty). One small deviation from "state the assumption you proceed on": open question 7 says "Assumption: none", although the whole plan proceeds on the drafted spec text. I found no content the request did not ask for beyond the tests and doc edits the repo's own guidelines require.

What checked out. Every `file:line` citation I tested resolves to what the plan says, across `ticketdesk/`, `tests/`, `AGENTS.md`, `docs/`, `Makefile`, `pyproject.toml`, and `ci.yml` at commit `7c62f26`.

- **Free names and IDs:** TKT-013 and CLI-009 are the last IDs, and a case-insensitive grep for "overdue" in the repo finds nothing.
- **Arithmetic:** the A1 due times, the 68-hour tie in U7, 4102444800 as the start of 2100, and `OVERDUE` at 7 characters are all correct.
- **Unchanged code:** the A7 usage text and exit code 2, the A4 baseline list, the corrupt-log traceback with exit code 1, and "Ran 7 tests OK" all reproduce.
- **Prototype:** the `list` and `overdue` outputs, the E1 and E2 results, the missing-log behaviour, and "Ran 11 tests OK" all reproduce, and the local Python is 3.15.2 as stated.
- **Not re-run:** the four mutation variants in A10. The prototype tests are consistent with the failure table.

I ran everything with `PYTHONDONTWRITEBYTECODE=1`; the repo and `plan.md` are untouched.
```

## 3. Verdicts

**The paraphrase matches the intent.** It names the derived mark, the single clock reading,
the strict comparison, the two outputs, the step order, and the seven questions. The reader
could paraphrase every part, so no passage needed a rewrite for clarity.

Count: 5 FIX, 0 REJECT, 0 ASK. One remark outside the findings list (question 7) is also
fixed. No fix changed the approach or a requirement, so the plan did not get a second cold
read. The plan passed `prose-lint.py` again after the fixes.

| # | Finding | Verdict | My check of the evidence | What changed in plan.md |
|---|---|---|---|---|
| 1 | Step 5 says "push", but the repo has no remote. Python 3.12 is installed locally. | FIX | `git remote -v` in the repo printed nothing. `/opt/homebrew/bin/python3.12 --version` printed `Python 3.12.16`. On the prototype, `compileall` exited 0 and the tests printed `Ran 11 tests in 0.070s` and `OK`. | Step 5 now runs the tests on the local Python 3.12 and says that CI runs when the user adds a remote. "Not validated: Python 3.12" became A11, confirmed, with the output. The risk "Python 3.12 is not tested locally" became "CI cannot run yet". The Python convention bullet no longer says "waits for CI". |
| 2 | Three statements disagree on what the sign-off gates. | FIX | The plan said "Steps 2 to 4 start only after step 0" and also "step 0 gates steps 1 and 4". `AGENTS.md:93` reads "Doc changes need user confirmation." Step 1 is a doc change, so the first statement was wrong. | The Plan intro now says "Steps 1 to 4 start only after step 0. No file in the repo changes before the sign-off." The convention bullet says step 0 gates steps 1 to 4. Question 7 says "No file in the repo changes before it." |
| 3 | Question 7 asks approval of step 4, but step 4 had no text. The new test count was blank. | FIX | Step 4 held phrases such as "add one sentence" and "the new count". 7 existing tests plus U1 to U10 plus C1 to C5 is 22. | Step 4 is now a table with the proposed text for each of its 12 passages, and it states the count of 22 with its sum. |
| 4 | Step 4 missed `AGENTS.md:47`. | FIX | `AGENTS.md:47` reads `├── tests/              unittest suites for the service and the store`. A new `tests/test_cli.py` makes it stale. | The step 4 table has a row for `AGENTS.md:47` with the proposed line. |
| 5 | Step 3 did not say whether `overdue` gets an `elif` or a bare `else`. The prototype kept a bare `else`. | FIX | `scratch/proto.diff` shows `elif args.cmd == "list":` followed by `else:` for `overdue`. The plan text only said "Add a branch". | Step 3 now requires `elif args.cmd == "overdue"` and no bare `else`. It also says that the prototype differs here and that argparse rejects unknown commands at `ticketdesk/cli.py:14`. |
| n/a | Remark under "Request coverage": question 7 said "Assumption: none". | FIX | The request says "state the assumption you proceed on". The plan does proceed on the drafted text. | Question 7 now reads "Assumption: the text stands as drafted, and the rest of the plan builds on it." |

## 4. Usage figures the subagent tool returned

| Figure | Value |
|---|---|
| Tokens (`subagent_tokens`) | 98228 |
| Tool uses (`tool_uses`) | 11 |
| Duration (`duration_ms`) | 186121 ms, about 3.1 minutes |

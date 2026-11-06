# Cold read of plan.md

One fresh `general-purpose` subagent ran the cold read. It got the brief from
`assets/cold-read.md` with the three placeholders filled, and nothing else. The plan as it
stood before the cold read is in `plan-before-cold-read.md`.

## 1. The exact prompt given to the subagent

```text
You review a document before a person signs it off. You have the document, the
repository, and the request that started the work. You have no other context, and that
is deliberate. Change nothing in the repository or the document. You may run the
project's own commands that only read, such as its tests.

Document: /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-4/eval-1-plan-overdue-tickets/with_skill/run-2/outputs/plan.md
Repository: /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-4/eval-1-plan-overdue-tickets/with_skill/run-2/outputs/repo
Request, in the user's words: Plan this change thoroughly, do not implement it: tickets that pass their due time should show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` subcommand should list only overdue tickets, oldest due first. Write the plan to /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-4/eval-1-plan-overdue-tickets/with_skill/run-2/outputs/plan.md. Nobody is available to answer questions during this run: list them as open questions, state the assumption you proceed on, and continue. Do not change any code or docs in the repo.

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

The harness indented every line of the report by two spaces. The indent is removed here.
Nothing else is changed.

```text
Verdict first: no Blocker and no Major. Every cited file, line, function, spec ID, quoted value and count checks out against the repo, and every experiment I re-ran reproduced. Four Minor findings follow. The repo is untouched (`git status` clean, HEAD `7c62f26`).

PARAPHRASE

The plan proposes to treat "overdue" as a fact computed at read time, never stored. A ticket is overdue when it is not closed and the current time is strictly later than its due time. The service reads the store's injectable clock once per call, flags each ticket, and gains a method that returns overdue tickets sorted by due time, then ID. `list` prints `OVERDUE` in the state column in place of `open`/`assigned`. A new `overdue` subcommand prints only the overdue tickets with their stored state. The plan adds two ticket specs (TKT-014, TKT-015), changes CLI-001 and CLI-006, adds CLI-010, and gates the code work on user approval of that text. It adds nine unit tests, six subprocess CLI tests and a list of doc edits, and it ends with eight open questions, each with a stated assumption.

According to the document alone, ticketdesk is a three-layer CLI: `cli.py` parses and prints, `tickets.py` (`TicketService`) holds every ticket rule, and `store.py` appends to and replays a JSON-lines event log. State is always rebuilt by replay; the log has three event kinds and three ticket states, and replay must be deterministic. Each ticket's due time is computed during replay as creation time plus SLA hours by priority. The store owns an injectable clock that stamps events. The CLI has four subcommands and no tests, and its final `else` branch handles `list` and would catch any subcommand without its own branch. A corrupt log currently escapes as a traceback (the open TODO under CLI-007).

I could paraphrase every part.

FINDINGS

- Severity: Minor
- Where: "Project conventions to follow", line 281 (also Step 2's "The prototype of this step").
- What: The plan says the prototype of steps 2 to 5 passes on 3.12, but step 4 was never prototyped: the nine `OverdueTests` cases do not exist anywhere. Step 3 item 2 (the shared line-format helper) is not in the prototype either.
- Evidence: Plan line 281: "the prototype of steps 2 to 5 passes on 3.12". Plan lines 311-315: "The prototype ran them with the seven existing tests" / "Ran 13 tests" (7 + 6, not 7 + 9 + 6). `diff -rq repo scratch/proto` reports only `Only in proto/tests: test_cli.py`, `cli.py ... differ`, `tickets.py ... differ`, so `tests/test_tickets.py` is unchanged. `scratch/prototype.diff` repeats the f-string in both branches instead of a helper.

- Severity: Minor
- Where: Step 6, against the claim in "Project conventions to follow", lines 288-289.
- What: The plan says "step 6 lists every doc edit", but at least two doc lines go stale and are not listed. One is the layout line describing the tests; the other is the architecture diagram's service-to-store interface, which gains a third call (`store.clock()`).
- Evidence: `AGENTS.md:47`: "├── tests/              unittest suites for the service and the store" (step 6 lists AGENTS.md lines 82, 102, 106, 114-116 only). `docs/architecture.md:18`: "│ append(event)  /  replay()", against Step 2 item 3: "It calls `self.store.clock()` once" (step 6 lists architecture.md lines 12, 68-69, 94-96, 103 only).

- Severity: Minor
- Where: Step 2 item 4, Step 4 `test_get_carries_the_overdue_flag`, Risks bullet 4.
- What: Routing `get()` through `_current()` is content the request did not ask for, and nothing consumes it. All five `get()` callers are the write paths, whose output the plan itself puts out of scope. It adds a clock read to every `create`/`assign`/`close` and creates a risk the plan then has to list. The rationale (presumably so a `Ticket` never carries a false `overdue=False`) is not stated.
- Evidence: Out of scope: "`OVERDUE` in the output lines of `create`, `assign`, and `close`. The request names `list` only." Codebase sweep: "`get()` has five callers, all inside `ticketdesk/tickets.py`" (lines 61, 64, 70, 73, 79). Risks: "A later test with a ticking clock sees one more tick per `get()`."

- Severity: Minor
- Where: Step 7 item 3 and Step 2 (missing decisions).
- What: Two decisions are left to the implementer without being named. (a) Where the commit goes: the plan says "Make one commit" but not whether it lands on `main` or a branch/PR, although the repo rules talk about pushes and PRs. (b) Whether `is_overdue` joins the package's public names, which the architecture doc enumerates.
- Evidence: (a) Step 7: "Make one commit that names TKT-014, TKT-015, CLI-006, and CLI-010"; sweep: "the only branch is `main`"; `AGENTS.md:96`: "Reference spec IDs in commit messages, code comments, tests, and PR descriptions." (b) `ticketdesk/__init__.py:5`: `__all__ = ["Ticket", "TicketError", "TicketService", "due_at", "SLA_HOURS", "EventStore"]` and `docs/architecture.md:89`: "Public names: Ticket, TicketError, TicketService, EventStore, due_at, SLA_HOURS"; Step 2 item 2 adds "a module function `is_overdue(ticket, now)`" and says nothing on export.

What I checked and found correct
- All file:line citations in `AGENTS.md`, `docs/`, `Makefile`, `pyproject.toml`, `ci.yml`, `ticketdesk/*.py` and `tests/*.py`.
- Next free IDs: TKT-014/015 and CLI-010.
- Counts: 7 existing tests (pass on Python 3.15.2 and 3.12), five `get()` callers, one `list()` caller.
- A8: `overdue` today gives `invalid choice: 'overdue'`, exit 2.
- The falsifier output from `scratch/exp_service2.py` matches the plan line for line.
- The prototype suite: "Ran 13 tests ... OK" on both Python versions.
- The `else`-branch trap: a copy with only the new subparser prints the full list for `overdue`.
- A6 output: `'#1 [P3] OVERDUE  ancient\n' '' 0`.
- The 12-line manual sequence matches exactly when replayed on the prototype.
- Request coverage: both asks (OVERDUE in `list`; `overdue` subcommand, earliest due first) are covered, questions are listed with assumptions, and nothing in the repo changed.

Paths
- Plan: /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-4/eval-1-plan-overdue-tickets/with_skill/run-2/outputs/plan.md
- Repo: /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-4/eval-1-plan-overdue-tickets/with_skill/run-2/outputs/repo
- Experiments: /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-4/eval-1-plan-overdue-tickets/with_skill/run-2/outputs/scratch
- My only write was a temp log at /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/01058b7d-e98e-4d3f-a81c-e8ba15a8c683/scratchpad/coldread/t.jsonl
```

## 3. Verdicts

**The paraphrase matches the intent.** Both paragraphs say what the plan means, and the
reader could follow every part. No text needed a fix for a misreading.

The fourth block of the report holds two separate decisions. They get one verdict each, so
the count is five findings.

| # | Finding | Verdict | My check of the evidence | What changed in the plan |
|---|---|---|---|---|
| 1 | The plan claims a prototype of steps 2 to 5, but step 4 and the line helper of step 3 were not prototyped. | **FIX** | True. Before the fix, `scratch/proto/tests/test_tickets.py` equalled the repo file, and `scratch/prototype.diff` repeated the f-string. | I prototyped the nine `OverdueTests` cases and the `_line` helper in `scratch/proto` and ran the suite. It printed `Ran 22 tests in 0.319s` and `OK` on Python 3.12, and 22 passed on 3.15.2. The test plan now quotes that run. Steps 2 and 4 name the prototype files. |
| 2 | Step 6 misses two stale doc lines, and the plan says it lists every doc edit. | **FIX** | True. `AGENTS.md:47` reads "unittest suites for the service and the store". `docs/architecture.md:18` reads "append(event)  /  replay()". My own grep also found `docs/architecture.md:48-50`, which says what the store clock is for. | Step 6 gained three edits: `AGENTS.md:47`, `docs/architecture.md:18`, and `docs/architecture.md:48-50`. The conventions bullet now says "the doc edits that the sweep found". |
| 3 | `get()` through `_current()` was not requested, nothing consumes it, and the reason is not stated. | **FIX** | True on all three points. The five callers at `ticketdesk/tickets.py:61,64,70,73,79` are write paths, and `ticketdesk/cli.py:23-27` prints only `t.state` from them. The plan gave no reason. | The design stays, and step 2 item 4 now states the reason and the cost. Without the change, `create`, `assign`, `close`, and `get` return an overdue ticket with `overdue` false. `Ticket` and `TicketService` are public names (`ticketdesk/__init__.py:5`), and `docs/architecture.md:121-122` expects other front ends to call the service. |
| 4a | The plan does not say whether the commit goes on `main` or on a branch with a pull request. | **ASK** | True. The repo names pushes and pull requests (`AGENTS.md:88`, `AGENTS.md:96`, `.github/workflows/ci.yml:2`) and records no branch rule. The user owns this decision. | New open question 9. The assumption is a branch off `main` and no push until the user says so. |
| 4b | The plan does not say whether `is_overdue` becomes a public name. | **FIX** | True. `ticketdesk/__init__.py:5` and `docs/architecture.md:89` list the public names, and the plan was silent. | New item 7 in step 2: `is_overdue` is not exported, and the list in `docs/architecture.md:89` stays correct. |

Totals: 4 FIX, 0 REJECT, 1 ASK.

No fix changed the approach or a requirement, so the plan did not go back to an earlier
step and did not need a second cold read. The revised plan passes `prose-lint.py` with
`0 findings in 1 file`. The fixture repo is still clean after the cold read
(`git status --short` prints nothing).

## 4. Usage figures of the subagent

The completion notification of the subagent tool showed these figures.

| Figure | Value |
|---|---|
| Tokens (`subagent_tokens`) | 101066 |
| Tool uses (`tool_uses`) | 9 |
| Duration (`duration_ms`) | 211504 ms, about 3 minutes 32 seconds |

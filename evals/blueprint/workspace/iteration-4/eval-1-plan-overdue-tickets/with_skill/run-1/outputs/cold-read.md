# Cold read of plan.md

One fresh `general-purpose` subagent, no fork, no shared context. The plan as it stood
before any change is in `plan-before-cold-read.md` in this directory.

## 1. The exact prompt given to the subagent

```text
You review a document before a person signs it off. You have the document, the
repository, and the request that started the work. You have no other context, and that
is deliberate. Change nothing in the repository or the document. You may run the
project's own commands that only read, such as its tests.

Document: /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-4/eval-1-plan-overdue-tickets/with_skill/run-1/outputs/plan.md
Repository: /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-4/eval-1-plan-overdue-tickets/with_skill/run-1/outputs/repo
Request, in the user's words: Plan this change thoroughly, do not implement it: tickets that pass their due time should show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` subcommand should list only overdue tickets, oldest due first. Write the plan to /Users/dmitri/dev/swd-skills/evals/blueprint/workspace/iteration-4/eval-1-plan-overdue-tickets/with_skill/run-1/outputs/plan.md. Nobody is available to answer questions during this run: list them as open questions, state the assumption you proceed on, and continue. Do not change any code or docs in the repo.

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

```text
One thing to know first: I briefly dirtied the repo and restored it. Running the project's lint (`python3 -m compileall -q ticketdesk tests`) wrote `ticketdesk/__pycache__/` and `tests/__pycache__/` into the repo. I confirmed by timestamp (10:35:54) that every file in them came from my run, deleted exactly those two directories, and `git status --short` is empty again. No tracked file was touched; only the mtimes of the `ticketdesk/` and `tests/` directories changed.

Verdict: no Blockers and no Majors. The plan's repository claims hold up; there are seven Minor findings.

PARAPHRASE

The plan proposes that `ticketdesk list` print `OVERDUE` in place of the state for any unclosed ticket whose due time has passed, and that a new `ticketdesk overdue` subcommand print only those tickets, earliest due time first with ties broken by ID. Overdue is computed at read time in the service: a new `_view()` reads the store's clock once and sets an `overdue` flag on each replayed ticket, and a new `overdue()` method filters and sorts. The CLI gains the subcommand and one shared line formatter. Nothing is written to the log, and no fourth state or new event kind is added. Work is gated on the user approving new spec text (TKT-014, TKT-015, CLI-010, and edits to CLI-001, CLI-006, LOG-001), followed by 8 new tests (5 service, 3 subprocess) and a sweep of stale doc lines.

According to the document alone, the existing system is a three-layer CLI: `cli.py` parses one command and prints, `tickets.py` (`TicketService`) holds every ticket rule and rebuilds tickets by replaying events, and `store.py` appends to and replays a JSON-lines log and owns an injectable clock. Tickets have three states (`open`, `assigned`, `closed`) and a due time of creation time plus calendar hours by priority (P1 4h, P3 72h; P2's 24h is not stated in the plan). There are four subcommands today, and `list` prints `#<id> [<priority>] <state> <title>` in ID order with the state padded to 8. The repo has 7 tests and none for the CLI, forbids doc and spec edits without user approval, and has an open TODO under CLI-007 about tracebacks on a corrupt log. I could paraphrase every part.

FINDINGS

- Severity: Minor
- Where: Step 4, Assumption 8, Test plan, Step 6.1
- What: Step 4 says the probe file holds "a working draft of all of them", but it holds 6 differently named tests, not the 8 planned cases. The three planned CLI cases are one test, and the flag assertion of `test_list_keeps_id_order_and_sets_the_flag` is absent. An implementer who starts from the draft gets 13 tests, not the 15 that step 6.1 expects.
- Evidence: Step 4: "A working draft of all of them is in `outputs/scratch/proto/tests/test_overdue_probe.py`." Assumption 8: "The probe suite with one subprocess case: `Ran 13 tests`". `grep -c "def test_"` on the probe file gives `6`; its only CLI test is `test_list_and_overdue_end_to_end`, and line 54 asserts only `[t.id for t in ...list()] == [1, 2, 3, 4]`.

- Severity: Minor
- Where: Step 2.4, Test plan
- What: Step 2.4 routes `get()` through `_view()` so `create`, `assign`, and `close` return a flagged ticket, but no planned test covers that path. The probe had such a test and the Test plan dropped it. The repo requires new logic to ship with named tests.
- Evidence: Step 2.4: "Then `create`, `assign`, and `close` also return a ticket with a correct flag." Probe line 66: `def test_get_and_mutations_carry_the_flag`. None of the 8 Test plan rows exercises `get`, `assign`, or `close` for the flag. `docs/guidelines.md:29-30`: "New logic ships with tests under `tests/`. Name the test files and the cases up front".

- Severity: Minor
- Where: "Assumptions validated" (LOG-009 bullet), Step 2.1, Risk 5
- What: The plan treats LOG-009 as unaffected because the private `_tickets()` is unchanged. But it puts a time-varying field on `Ticket`, so tickets from `list()` and `get()` for the same log can now compare unequal across time. LOG-009 gets no amendment and no open question, unlike CLI-001, CLI-006, and LOG-001.
- Evidence: `docs/product-specs/event-log.md:58-59`: "Replaying the same log always yields the same tickets with the same states, assignees, resolutions, and due times." Step 2.1: "Add the field `overdue: bool = False` after `due_at` in `Ticket`". Risk 5: "`list` output now changes with time, with no change to the log."

- Severity: Minor
- Where: Step 5, Open question 6
- What: Open question 6 asks the user to approve "the doc edits in step 5", but step 5 lists only which lines go stale and gives no replacement text. The wording of the architecture seam change is left to the implementer, and the repo requires sign-off on architecture doc changes.
- Evidence: Step 5 table header: "File and line | What goes stale". Open question 6: "Do you approve the spec text in step 1 and the doc edits in step 5? Assumption: yes, as written." `docs/README.md:39-40`: "Never silently update a spec or an architecture doc. The user signs off."

- Severity: Minor
- Where: Step 5 stale-line table
- What: The table misses at least two lines the change makes stale. Every line it does cite is accurate.
- Evidence: `AGENTS.md:47`: "tests/              unittest suites for the service and the store" is stale once `tests/test_cli.py` exists. `docs/architecture.md:43-44`: "It asks the store for the event list and derives every ticket from it" is stale once the flag comes from the clock; the plan cites only `:18` for the seam.

- Severity: Minor
- Where: Step 6.1 and 6.3
- What: The plan runs `make lint` and then commits without saying what to stage. `make lint` writes `__pycache__` into the tree and the repo has no `.gitignore`, so a blanket `git add` would commit bytecode.
- Evidence: After `python3 -m compileall -q ticketdesk tests` (the `Makefile:5` command), `git -C repo status --short` printed `?? tests/__pycache__/` and `?? ticketdesk/__pycache__/`. `cat repo/.gitignore` found no file.

- Severity: Minor
- Where: Test plan, Manual
- What: The output block is described as "copied from the prototype run", but the recorded run included an `assign 1 dana` that the listed commands omit. The block is still correct for the commands as listed: I replayed them on the prototype and got the same 8 lines.
- Evidence: `outputs/scratch/manual.jsonl` line 4: `{"assignee": "dana", "at": 1793892672.178943, "id": 1, "kind": "assigned"}`. The plan's sequence has only `create`, `list`, `overdue`, `close 2`, `overdue`.

What I checked and found correct:
- **Citations:** every file-and-line citation, the spec quotes for CLI-001, CLI-006, LOG-001, and LOG-009, and the next free IDs (TKT-014, TKT-015, CLI-010).
- **Test counts:** the repo runs 7 tests and lint exits 0. The prototype runs 13 tests on Python 3.15.2 and 3.12.16.
- **Quoted output:** the `invalid choice: 'overdue'` message with exit code 2 on `HEAD`, and the corrupt-log `ValueError` text with exit code 1.
- **Other claims:** `prototype.diff` matches steps 2 and 3. The repo was clean when I opened it. A search for "overdue" in the repo finds nothing.
- **Request coverage:** both parts of the request and the open-questions instruction are covered. I found no internal contradiction beyond the first finding.

One claim I could not check: the Assumption 3 probe output (`at due exactly: False clock now True`) has no artifact in `outputs/scratch`.
```

## 3. Verdicts

**Paraphrase.** Both paragraphs match the intent of the plan, and the reader could
paraphrase every part. One gap showed: the plan never stated the 24 hours of P2. Changed:
the "Business hours" bullet under "Out of scope" now names 4, 24, and 72 hours.

Each finding was checked against the repo and the scratch files before its verdict. No fix
changed the approach or a requirement, so no second cold read ran.

| # | Finding | Verdict | Evidence checked | Change to plan.md |
|---|---|---|---|---|
| 1 | The probe file is not "a working draft of all" 8 cases. | FIX | `grep -n "def test_"` on `scratch/proto/tests/test_overdue_probe.py` lists 6 tests, one of them `test_list_and_overdue_end_to_end`. 7 existing plus 6 gives the 13 the plan quoted. | Step 4 now calls the probe file a draft with 6 tests under other names and tells the implementer to split it into the named cases. Assumption 8 now says "the 7 existing tests plus the 6 probe tests". |
| 2 | No planned test covers the flag on the tickets that `get`, `assign`, and `close` return. | FIX | The probe has `test_get_and_mutations_carry_the_flag` at line 66, and the test plan had no such row. `docs/guidelines.md:29-30` requires named tests for new logic. | Added `test_get_assign_and_close_return_the_flag` (TKT-014) to the unit table. New cases go from 8 to 9. The expected total in step 6.1 and in the `AGENTS.md:102` row goes from 15 to 16. |
| 3 | LOG-009 gets no amendment and no question, although `Ticket` gains a field that changes with time. | ASK | `docs/product-specs/event-log.md:58-59` reads "the same tickets with the same states, assignees, resolutions, and due times". The flag is none of the four, but "the same tickets" can be read to cover it. Whether the spec needs a sentence is the user's decision. | Added open question 8 with the assumption and the alternative sentence. The LOG-009 row of the spec table now names the tension and points to the question. |
| 4 | Step 5 names stale lines but gives no replacement text, while open question 6 says "as written". | FIX | The step 5 table had the columns "File and line" and "What goes stale" only. `docs/README.md:39-40` requires approval for an architecture doc change. | Step 5 now has "Today" and "Proposed" columns with the replacement text for every row. Its lead says the two architecture rows need the same approval as step 1. Open question 6 now asks about "the replacement text in step 5". |
| 5 | The stale-line table misses `AGENTS.md:47` and `docs/architecture.md:43-44`. | FIX | `sed -n '47p' AGENTS.md` prints "tests/  unittest suites for the service and the store". `sed -n '43,44p' docs/architecture.md` prints "It asks the store for the event list and derives every ticket from it". | Added both rows with proposed text. Also removed the row for `docs/product-specs/README.md:82`, which the change does not make stale. |
| 6 | The plan commits after `make lint` without saying what to stage, and the repo has no `.gitignore`. | FIX | The baseline run in this session showed the same: after `make lint` and `make test`, `git status --short` printed `?? tests/__pycache__/` and `?? ticketdesk/__pycache__/`. `ls -a` in the repo shows no `.gitignore`. | Step 6 gained a step that stages by path and forbids `git add -A`. "Out of scope" gained a bullet that a `.gitignore` is unrelated cleanup (`docs/guidelines.md:86`). |
| 7 | The manual output is labelled "copied from the prototype run", but that run also had `assign 1 dana`. | FIX | `scratch/manual.jsonl` line 4 is the `assigned` event. The recorded run had eight commands, and the plan listed five. | The manual sequence now lists the same eight commands as the recorded run, and the output block holds all 15 lines of that run. |
| note | Assumption 3 had no artifact in `outputs/scratch`. | FIX | The probe ran from stdin, so no file existed. | Saved it as `scratch/clock_probe.py` and its output as `scratch/clock_probe.out`. Assumption 3 now cites both. The rerun printed the same three lines. |

Totals: 7 findings, all Minor. 6 FIX, 0 REJECT, 1 ASK. The uncheckable claim got a fix too.

After the changes, `prose-lint.py` on `plan.md` reports `0 findings in 1 file`.

## 4. Usage figures for the subagent

The completion notification of the subagent tool returned these figures.

| Figure | Value |
|---|---|
| Tokens (`subagent_tokens`) | 97936 |
| Tool uses (`tool_uses`) | 10 |
| Duration (`duration_ms`) | 214855, about 3 min 35 s |

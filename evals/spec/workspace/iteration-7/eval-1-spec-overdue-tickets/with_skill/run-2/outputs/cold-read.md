# Cold read of the overdue tickets spec

One fresh `general-purpose` subagent, not a fork. The snapshot of the spec before any
change from this read is in `before-cold-read/`.

## 1. The exact prompt given to the subagent

```text
You review a document before a person signs it off. You have the document, the
repository, and the request that started the work. You have no other context, and that
is deliberate. Change nothing in the repository or the document. You may run the
project's own commands that only read, such as its tests.

Document: /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo/docs/product-specs/tickets.md and /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo/docs/product-specs/cli.md (the document is an amendment to these two files; `git diff` in the repository shows the amended text)
Repository: /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo
Request, in the user's words: Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs. Nobody is available to answer questions during this run: where the skill would ask me, write the questions to /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/questions.md, state the assumption you proceed on, and continue. Do not change any code. Do not commit.

First, review. Treat every statement in the document as a claim, including what it says
about the system today. Check the document against the code, the project's docs, and the
request. Find what is wrong, what is missing, and what is risky. Open every file the
document cites. Recompute every number and every example. Compare each design choice
with how the project already solves the same problem, and with the project's own rules.

Report in this shape.

FINDINGS
One block per finding, the most serious first:
- Severity: Blocker, Major, or Minor. A Blocker makes the result wrong. A Major costs
  rework. A Minor is everything else.
- Where: the section or line of the document.
- What: the problem in one or two sentences.
- Evidence: a file and line, a command and its output, or the two passages that
  disagree.

After the findings, paraphrase. Write in your own words what the document proposes, in
two to five sentences. Then write how the existing system works according to the
document alone, in two to five sentences. If you cannot paraphrase a part, name the
part and say why. Put this under the heading PARAPHRASE.

Report every finding, the lesser ones too. The author sorts them. Wording, style, and
length are not findings. If you find nothing, say so.
```

## 2. The subagent's report, verbatim

```text
Review of the overdue-tickets spec amendment. No Blocker and no Major found; 13 Minor findings. Nothing in the repo was changed (`git status` still shows only the four doc files modified, one commit in history).

Paths below are relative to `/Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/repo`; `questions.md` is at `/Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-2/outputs/questions.md`.

FINDINGS

1.
- Severity: Minor
- Where: `docs/product-specs/tickets.md` lines 6-7 (intro) against TKT-015 (lines 146-148).
- What: The intro sentence, read literally, says a ticket closed after its due time is overdue. TKT-015 says the opposite.
- Evidence: Line 6: "A ticket that passes its due time before it is closed is overdue." Line 146: "A `closed` ticket is not overdue, whatever its due time and whenever it was closed."

2.
- Severity: Minor
- Where: `docs/product-specs/cli.md` line 61, CLI-006.
- What: "The marker comes before the state, so a title cannot imitate it" is false for a title that contains a newline. TKT-002 only rejects empty or whitespace-only titles, so such a title forges a complete overdue line today.
- Evidence: `python3 -m ticketdesk.cli --log <scratch> create $'x\n#9 [P1] OVERDUE open     fake'` followed by `list` prints `#1 [P3] open     x` and then `#9 [P1] OVERDUE open     fake`.

3.
- Severity: Minor
- Where: `tickets.md` line 96-97 ("A line that starts with `TODO` marks an assumption that the user did not confirm"), TKT-016, CLI-010, CLI-011.
- What: Several unconfirmed assumptions carry no TODO line, so a signer can take them as confirmed. Two of them are also absent from the spec's own open-questions list.
- Evidence: `questions.md` lines 56-63 list as assumptions A2 the tie-break by ID (TKT-016, line 155), A3 exit code 0 (CLI-010), A4 empty output, and A5 extra-argument handling (CLI-011). TODO lines exist only at `tickets.md` 142 and 150 and `cli.md` 63. The tie-break and CLI-011 appear in neither a TODO nor open questions 1-5 (`tickets.md` 168-177).

4.
- Severity: Minor
- Where: `tickets.md` "Open questions" (lines 168-177) against `questions.md`.
- What: The two question lists use different numbers for the same questions, so an answer such as "Q3: yes" can be applied to the wrong item.
- Evidence: `questions.md` line 40: "Q3. Does a line show the due time, or how late the ticket is?" `tickets.md` line 173: "3. **Is a ticket overdue at exactly its due time?**" (that one is A1 in `questions.md`; the due-time display is number 4 in the spec).

5.
- Severity: Minor
- Where: TKT-014 line 131 ("The current time is the moment the command runs") and the invariant paragraph at lines 119-126.
- What: The spec checks INV-001, INV-002 and LOG-009 but says nothing about INV-005 or the clock source. The architecture doc says times come from the store's clock, and the planner who reads only the spec does not learn that this is open.
- Evidence: `docs/architecture.md` lines 68-69: "Timestamps and due times are floats from the store's clock, never from the caller, see INV-005." `questions.md` lines 72-74 records the gap ("The source of that time in the code is a decision for the plan"); the spec does not. The test clock at `tests/test_tickets.py` lines 12-14 advances by one second on every call, so reading "now" from it has a side effect.

6.
- Severity: Minor
- Where: `cli.md` CLI-001 (lines 18-20) and CLI-006 (lines 49-52).
- What: Existing items were rewritten in place in the present tense for behavior that does not exist, so the authoritative spec now contradicts the code. CLI-001 has no marker inside the item; only the file header at lines 8-10 says it is proposed. CLI-006 also defines the unchanged line as "the same as before this change", which loses its referent once built.
- Evidence: `ticketdesk overdue` today exits 2 with `invalid choice: 'overdue' (choose from 'create', 'assign', 'close', 'list')`; `ticketdesk/cli.py` lines 15-18 register four subcommands. `docs/product-specs/README.md` line 3: "Authoritative description of what ticketdesk does." `docs/README.md` line 63 lists "a design exploration that has not landed" under when not to write a doc.

7.
- Severity: Minor
- Where: `tickets.md` lines 88-126 and 163-177 (the "Overdue tickets" section).
- What: The Goals, Non-goals, dated Status and Open questions blocks, and a `##` section heading, are a form the repo's specs do not use. `### Open questions` sits at the same heading level as the ID items without an ID.
- Evidence: Every other spec file is an intro, `Prefix:`, then `### PREFIX-NNN` items only (`event-log.md`, `invariants.md`, the original `tickets.md` and `cli.md`). `docs/product-specs/README.md` lines 8-19 define a spec as behavioral, testable and identified; lines 50-52 allow only "prose contracts without numeric IDs". The one precedent for in-spec open work is the TODO under CLI-007.

8.
- Severity: Minor
- Where: `cli.md` CLI-006 lines 49-58.
- What: On an overdue line the state moves from the third field to the fourth and the title starts 8 columns further right. The spec does not state this cost; a script that reads the state by position breaks on overdue lines only.
- Evidence: `#1 [P1] OVERDUE open     Printer on fire` against `#3 [P2] closed   Email bounces` (lines 55 and 57). The cost is written in `questions.md` lines 33-34 but in the spec only by implication at `tickets.md` line 172 ("That keeps the columns aligned").

9.
- Severity: Minor
- Where: `AGENTS.md` lines 118-119 (part of the same diff).
- What: The list of affected items omits CLI-001, which the spec files both name.
- Evidence: `AGENTS.md` 119: "See TKT-014 to TKT-016, CLI-006, CLI-010, and CLI-011." `tickets.md` line 96 and `cli.md` line 9: "CLI-001, CLI-006, CLI-010, and CLI-011".

10.
- Severity: Minor
- Where: TKT-014 table, `tickets.md` lines 135-140.
- What: The table has no row at exactly the due time, although that boundary is the one rule the item flags as an assumption. It also has no `P2` row.
- Evidence: Rows are 3 h 59 min, 4 h 1 min (twice) and 71 h. The prose at line 132 says "At exactly the due time the ticket is not overdue."

11.
- Severity: Minor
- Where: TKT-014, CLI-006, CLI-010 as a whole (verification path).
- What: No sequence of `ticketdesk` commands can produce an overdue ticket in under 4 hours, and the spec does not say how a tester gets one. The project requires end-to-end command sequences for user-visible changes.
- Evidence: `ticketdesk/sla.py` line 3: shortest target is `P1` at 4 hours. `docs/guidelines.md` lines 32-34 ask for command sequences "against a temporary log file". A hand-written log with an old `at` works with the current CLI (I ran `list` on one with `at` = now minus 5 hours and it printed normally), so the path exists but is not stated.

12.
- Severity: Minor
- Where: Non-goals, `tickets.md` lines 106-117.
- What: The spec does not say whether the output of `assign` and `close` on an overdue ticket changes. It is unchanged only by implication.
- Evidence: CLI-004 and CLI-005 (`cli.md` lines 33-41) are untouched; no non-goal covers them. The request names only `list` and `overdue`.

13.
- Severity: Minor
- Where: `tickets.md` line 6-7.
- What: The amended intro paragraph is not in the list of amended parts that the Status paragraph says is proposed.
- Evidence: `tickets.md` lines 95-96 name only "TKT-014 to TKT-016 here" and four CLI items.

Checked and found correct:
- The three example lines in CLI-006 match the current format string byte for byte (`cli.py` line 30, state padded to 8).
- TKT-016 example: ticket 1 due at 72 h, ticket 2 due at 60 + 4 = 64 h, both overdue at 80 h, ticket 2 first.
- TKT-014 table rows agree with `sla.py`.
- CLI-011 matches today's `list extra` behavior (usage, exit 2). CLI-010's missing-log case matches `store.py` lines 26-27 (`list` on a missing log prints nothing, exit 0, creates no file). The corrupt-log statement matches (traceback, exit 1).
- TKT-014 to TKT-016 and CLI-010, CLI-011 are the next free IDs. Anchors and cross-references resolve.
- `python3 -m unittest discover -s tests -q`: 7 tests pass. No code file changed, nothing committed.

PARAPHRASE

What the document proposes: A ticket counts as overdue when it is still `open` or `assigned` and the present moment is strictly after its due time; a closed ticket never counts. `ticketdesk list` keeps its order and its lines, except that an overdue ticket's line gets the word `OVERDUE` between the priority and the state. A new `ticketdesk overdue` command prints only the overdue tickets in that same marked format, earliest due time first with ID as the tie-break, takes no arguments, and exits 0 whether or not it finds any. Overdue is computed at run time and is neither a state nor an event. Five questions (closed tickets, marker position, the exact boundary, showing the due time, the exit code) are left open with a stated assumption each.

How the existing system works, per the document alone: A ticket has a title and a priority `P1` to `P3`, moves forward through `open`, `assigned`, `closed`, and gets a due time of creation plus 4, 24 or 72 hours. Every change is one event in an append-only JSON lines log, and ticket state is rebuilt by replaying it; a missing log means no tickets and a corrupt line stops every command. The CLI has `create`, `assign`, `close` and `list`; `list` prints every ticket in ID order as `#<id> [<priority>] <state> <title>` and no command shows the due time. Rule errors print `error: <message>` and exit 2, except that an unknown priority and a corrupt log currently escape as tracebacks with exit 1, which is an unresolved TODO.

One part I cannot paraphrase with confidence: where "the current time" comes from. The document says only "the moment the command runs" and does not say whether that is the store's clock or another source.
```

## 3. Verdicts

The paraphrase matches the intent of the spec. The one part the reader could not restate
is the source of the current time. Finding 5 covers it, and the spec now says it is open.

No fix changed a requirement or the approach, so the spec did not get a second cold read.
After the fixes, `prose-lint.py` reports 0 findings on the four changed files.

| # | Verdict | Evidence checked | Change |
|---|---------|------------------|--------|
| 1 | FIX | The two passages disagree as quoted, see `before-cold-read/tickets.md` lines 6 and 146. | The intro of `tickets.md` now reads "A ticket that is past its due time and not closed is overdue". |
| 2 | FIX | I ran `create $'x\n#9 [P1] OVERDUE open     fake'` then `list`. It printed `#1 [P3] open     x` and `#9 [P1] OVERDUE open     fake`. | CLI-006 now claims only that the start of a title cannot pass for the marker. It names the line-break gap and says the item does not close it. `questions.md` asks whether a fix is wanted. |
| 3 | FIX | `before-cold-read/` has TODO lines only under TKT-014, TKT-015, and CLI-006. | TODO lines added under TKT-016, CLI-010, and CLI-011. Open questions 6 (tie order) and 7 (extra argument) added. The empty-output case stays without a TODO, because CLI-006, CLI-008, and LOG-006 imply it. |
| 4 | FIX | `questions.md` had Q3 for the due time display. The spec had 3 for the boundary. | `questions.md` now uses the numbers of the spec, 1 to 8. |
| 5 | FIX | `docs/architecture.md` lines 68-69, `docs/product-specs/invariants.md` INV-005, `tests/test_tickets.py` lines 12-14. | A paragraph in "Overdue tickets" says that no spec names the source of the current time, that INV-005 covers event times only, and that the plan chooses. |
| 6 | FIX | `ticketdesk/cli.py` lines 15-18 register four subcommands. `ticketdesk overdue` printed `invalid choice: 'overdue'` with exit code 2 in my run. | CLI-001 and CLI-006 each got a TODO line that says the behavior is proposed and not built. "the same as before this change" became "keeps the first format". The items stay amended in place, because the request asks for the spec in the repo's docs before the build. |
| 7 | ASK | The other four spec files hold an intro, `Prefix:`, and ID items only. `docs/product-specs/README.md` does not forbid more prose, and the skill requires goals, non-goals, and open questions. | Open question 8 asks whether the goals, non-goals, and status stay after sign-off. One local fix: the open questions moved from a `###` heading among the ID items to their own `##` section. |
| 8 | FIX | The example lines in CLI-006 show the shift. | CLI-006 and open question 2 now state the cost: the state is the fourth field of an overdue line, and the title starts 8 characters further right. |
| 9 | FIX | `AGENTS.md` line 119 omitted CLI-001. | CLI-001 added to that list. |
| 10 | FIX | The table had four rows, none at the boundary and none for `P2`. | Rows added: `P1` at exactly 4 hours, `P1` closed, `P2` on both sides of 24 hours, `P3` past 72 hours. |
| 11 | FIX | `ticketdesk/sla.py` line 3. I ran `list` on a hand-written log with `at` 5 hours in the past. It printed `#1 [P1] open     old` with exit code 0. | TKT-014 now says the creation time is the `at` of the `created` event, and that a log with an `at` 5 hours in the past shows an overdue `P1` ticket at once. |
| 12 | FIX | CLI-003 to CLI-005 are untouched and no non-goal covered them. | New non-goal: no change to the output of `create`, `assign`, or `close`. |
| 13 | FIX | The status paragraph named only TKT-014 to TKT-016 and four CLI items. | The status now covers the section and the intro sentence. |

Counts: 12 FIX, 0 REJECT, 1 ASK.

## 4. Usage figures for the subagent

The completion notification of the Agent tool showed these figures.

| Figure | Value |
|--------|-------|
| Tokens | 91213 |
| Tool uses | 10 |
| Duration | 193070 ms |

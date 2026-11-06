# Cold read of the overdue-tickets spec

One fresh `general-purpose` subagent ran on 2026-11-05. It got the prompt in part 1 and
nothing else. The state of the spec before any change in response to it is in
`before-cold-read/git-diff.patch`.

## 1. The exact prompt given to the subagent

```text
You review a document before a person signs it off. You have the document, the
repository, and the request that started the work. You have no other context, and that
is deliberate. Change nothing in the repository or the document. You may run the
project's own commands that only read, such as its tests.

Document: /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo/docs/product-specs/tickets.md (the section "Overdue tickets", TKT-014 to TKT-017, and the intro paragraph that points at it) together with /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo/docs/product-specs/cli.md (CLI-001, CLI-006, CLI-010 to CLI-012). `git diff` in the repository shows the exact text that the document adds.
Repository: /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-3/outputs/repo
Request, in the user's words: Spec this out before anyone plans or builds it: support agents want tickets that pass their due time to show as OVERDUE in `ticketdesk list`, and a new `ticketdesk overdue` command that lists only overdue tickets, oldest due first. Write the spec into the repo's docs the way the repo does specs.

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

The request in the prompt is the feature request, word for word. The run instructions
around it (where to write questions, "do not commit") were left out. They name a file that
holds the author's reasoning, and the cold read withholds that.

## 2. The subagent's report, verbatim

The harness indented each line of the report by two spaces. That indent is removed here.
Nothing else is changed.

```text
No Blocker found. One Major, eight Minor. All numbers and examples recompute correctly; the citations resolve, with two that point at the wrong or a too-narrow item (findings 5 and 7).

Checked and clean:
- TKT-017 table: 74h − 72h = 2h, 30h − 24h = 6h, 5h − 4h = 1h; positions 2/1/3 are right, and the order differs from ID, creation and priority order as claimed.
- TKT-014 example agrees with `ticketdesk/sla.py:3` (P1 = 4h).
- CLI-010 example lines match `f"{state:<8} "` byte for byte, and the two non-overdue lines match real `list` output.
- "Until it ships, `overdue` is an unknown subcommand": `python3 -m ticketdesk.cli overdue` gives `invalid choice: 'overdue'`, exit 2.
- CLI-012 matches how `list` treats extra arguments today: `list 3` gives `unrecognized arguments: 3`, exit 2.
- Missing log file: `list` prints nothing, exits 0, creates no file (LOG-006).
- Corrupt log: `ValueError` traceback, exit 1, as the CLI-007 TODO says.
- `make test` equivalent: 7 tests pass. TKT-014 and CLI-010 are the next free IDs. The `tickets.md#overdue-tickets` anchor resolves.

FINDINGS

1.
- Severity: Major
- Where: `cli.md` CLI-010 (line format and its TODO), and Goal 1 in `tickets.md`.
- What: The marker sits directly before the free-text title, so a ticket that is not overdue but whose title starts with `OVERDUE ` prints a line identical to an overdue ticket's line. The TODO admits this, but its only alternative (replace the state) loses the assigned/open information; no option that is both unambiguous and state-preserving is put to the user. The marker also breaks the title column that the 8-character state padding exists to align.
- Evidence: With today's code, `create "OVERDUE invoice from vendor"` then `list` prints `#4 [P3] open     OVERDUE invoice from vendor`. Under CLI-010 an overdue ticket titled `invoice from vendor` prints the same bytes. `docs/product-specs/README.md:38-40` requires behavior to be observable from outside. `ticketdesk/cli.py:30` shows the padding.

2.
- Severity: Minor
- Where: `tickets.md` intro paragraph, line 11, against TKT-015.
- What: The intro's definition and TKT-015 disagree when read literally. A ticket closed after its due time was "not closed when its due time passes", so the intro makes it overdue and TKT-015 says it is not.
- Evidence: Line 11: "A ticket that is not closed when its due time passes is overdue." Line 143: "A ticket closed after its due time is not overdue either."

3.
- Severity: Minor
- Where: `tickets.md` intro (lines 11-13) and Non-goals (lines 116-125), against the TODOs under TKT-015, TKT-016 and CLI-011.
- What: The intro and the non-goals state as settled what the TODOs mark as open: "never a state", no lateness for closed tickets, no due time in output. The intro is also in the present tense with no "proposed" marker, so it reads as a fact about the system today, which it is not.
- Evidence: Line 12-13 "It is never a state and never an event" against line 155 "this assumes that overdue is a marker and not a fourth state ... Confirm with the user". Line 117 and 123 against the TODOs at lines 145 and `cli.md:106`.

4.
- Severity: Minor
- Where: `cli.md` CLI-006, CLI-010, CLI-011, CLI-012; the status paragraph at `tickets.md:100-103`.
- What: The "not built" status is only on CLI-001 and in the `tickets.md` section. CLI-006 now states an OVERDUE behavior that is false today with no note in place, and CLI-010 to CLI-012 carry no status either, so a reader who lands on one item takes it as current behavior. The status paragraph also says each TODO under those items is an open question naming an assumption; the CLI-001 TODO is a build note, and CLI-006 and CLI-012 have none. `AGENTS.md:118-119` lists only CLI-010 to CLI-012 as "specified, not built" and omits the edits to CLI-001 and CLI-006.
- Evidence: `cli.md:46-47` against `ticketdesk/cli.py:30`, which prints no marker. `docs/product-specs/README.md:3` calls the specs the "authoritative description of what ticketdesk does". `docs/README.md:63` says not to write a doc "for a design exploration that has not landed".

5.
- Severity: Minor
- Where: `tickets.md` TKT-014, "on the same clock that stamps events, see LOG-004".
- What: LOG-004 does not name a clock; INV-005 does. The sentence also commits the service to reading the store's clock, a contact between service and store that `architecture.md` does not describe, and the document does not flag it.
- Evidence: `event-log.md:33-34` (LOG-004) against `invariants.md:36-37` (INV-005: "The time comes from the store's clock"). `docs/architecture.md:18` shows the boundary as `append(event) / replay()`; the clock is `EventStore.clock` at `ticketdesk/store.py:14-16`.

6.
- Severity: Minor
- Where: `tickets.md` TKT-014 (boundary sentence and example), `cli.md` CLI-010 and CLI-011.
- What: The CLI cannot inject a clock, so the only way to verify these through the CLI is a hand-written log with `at` values in the past; the spec does not say so. The "at the exact due time" case cannot be observed through the CLI at all, only at the service with a fake clock.
- Evidence: `ticketdesk/cli.py:20` builds `EventStore(args.log)` with the default `time.time`. `docs/README.md:22-24` asks that a tester derive the verification path from the text alone. `docs/guidelines.md:32-34` requires command sequences against a temporary log for user-visible changes.

7.
- Severity: Minor
- Where: `cli.md` CLI-011, "It appends no event, see LOG-001".
- What: LOG-001 only says that listing tickets appends nothing, and `event-log.md` is not amended. The citation holds only if `overdue` counts as "listing", which the document implies through TKT-017's "overdue listing" but never states. The same applies to the LOG-006 citation ("Listing shows nothing").
- Evidence: `event-log.md:14-15` and `event-log.md:43-44`; the diff does not touch `event-log.md`.

8.
- Severity: Minor
- Where: `tickets.md` TKT-016 TODO, "A fourth state needs changes to TKT-001, LOG-002, LOG-003, and INV-001".
- What: The list mixes two designs and misses items. A state stored as an event touches LOG-002 and LOG-003 but not INV-001. A state derived from the time touches INV-001 and LOG-009 ("same states" on every replay) but not LOG-002 or LOG-003. LOG-009 and the forward-only rule are not mentioned, so the user gets a wrong cost picture for the alternative.
- Evidence: `event-log.md:56-59` (LOG-009), `invariants.md:14-17` (INV-001), `tickets.md:8-9` (forward-only).

9.
- Severity: Minor
- Where: Whole document, sign-off scope.
- What: Seven questions are still open for the user: strict "later than" (TKT-014), closed tickets (TKT-015), marker or state (TKT-016), tie order (TKT-017), marker placement (CLI-010), and no due time in output plus exit code 0 (CLI-011). Three of them (TKT-015, TKT-016, CLI-010) change the line format or the set of listed tickets, so signing off without answers approves the assumptions by default.
- Evidence: TODO paragraphs at `tickets.md:137, 145, 155, 173` and `cli.md:88, 106`.

PARAPHRASE

What the document proposes: A ticket counts as overdue when it is open or assigned and the current time is strictly later than its due time (creation time plus 4, 24 or 72 hours by priority); a closed ticket is never overdue. Overdue is computed fresh on each command, is not a state, and writes nothing to the log. `ticketdesk list` keeps its ID order and its lines, and adds the word `OVERDUE` between the padded state and the title on overdue tickets. A new `ticketdesk overdue` command prints only the overdue tickets, in the same line format, sorted by due time ascending with ID as tie-break; it takes no arguments, prints nothing and exits 0 when nothing is overdue. The whole thing is marked proposed, not built, not signed off, with seven open questions.

How the existing system works, according to the document alone: Tickets have three states, open, assigned and closed, and move forward only. Each ticket has a due time derived from its priority, but no command shows it, so an agent cannot tell a late ticket from one on time. The CLI has four subcommands, `create`, `assign`, `close` and `list`; `list` prints one line per ticket in ID order as `#<id> [<priority>] <state> <title>` with the state padded to 8 characters. Every change is one timestamped event in an append-only log, listing appends nothing, a missing log means no tickets, and a corrupt log stops every command, with the way the CLI reports that still an open question.

Part I could not paraphrase with confidence: where the "current time" comes from. The document says "the same clock that stamps events" and cites LOG-004, which names no clock, so from the document alone I cannot say which component owns that clock.

Scratch files from my CLI runs are in /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/01058b7d-e98e-4d3f-a81c-e8ba15a8c683/scratchpad/r3; the repository is unchanged (`git status` shows the same four modified files as before).
```

## 3. Verdicts

The count is 9 findings: 8 FIX, 0 REJECT, 1 ASK. No fix changed the shape of the spec, so
there was no second cold read. Both spec files pass `prose-lint.py` after the fixes.

The paraphrase matches the intent, with one gap. The reader could not say where the
current time comes from. Finding 5 covers that gap, and its fix removes it.

| # | Verdict | Evidence checked by the author | What changed |
|---|---------|--------------------------------|--------------|
| 1 | FIX | Reproduced. `create "OVERDUE invoice from vendor"` then `list` printed `#1 [P3] open     OVERDUE invoice from vendor`. The first draft gave an overdue ticket titled `invoice from vendor` the same line. | CLI-010 now puts the marker between the priority and the state: `#<id> [<priority>] OVERDUE <state> <title>`. A new paragraph says why a title cannot read as the marker. The TODO now holds a table of three options with the cost of each. `questions.md` question 3 follows. |
| 2 | FIX | `tickets.md:11` against `tickets.md:143` in the snapshot. The two sentences disagree for a ticket closed late. | The intro now says "An `open` or `assigned` ticket whose due time has passed is overdue." |
| 3 | FIX | `tickets.md:12-13` stated "never a state" as fact. The TODO at `tickets.md:155` marks it as an assumption. | The intro now says the rule is proposed and not built, and that the proposal assumes "never a state". Three non-goals now end with "Open, see the TODO under" and the item. |
| 4 | FIX | `cli.md:46-47` in the snapshot states the marker with no status. `ticketdesk/cli.py:30` prints no marker. `docs/README.md:63` holds the quoted rule. | `cli.md` has a new "Overdue tickets" section head with a dated status before CLI-010. CLI-006 marks its new sentence as proposed and not built. The status paragraph in `tickets.md` now names which TODOs are open questions. `AGENTS.md` names the amendments to CLI-001 and CLI-006. The rule of `docs/README.md:63` is a decision for the user, so it went to `questions.md` as question 10. |
| 5 | FIX | `event-log.md:33-34` (LOG-004) names no clock. `invariants.md:36-37` (INV-005) names the store's clock. | TKT-014 now says the current time is the time on the machine's clock when the command runs, in seconds since the Unix epoch. It names no component. That choice stays with the plan. |
| 6 | FIX | `ticketdesk/cli.py:20` builds the store with the default clock. | The TKT-014 example now rests on the `at` of the `created` event, so the log a tester must write follows from the text. The sentence about the exact due time stays. A test through the service can observe it with the fake clock of `tests/test_tickets.py:8-14`, and `docs/guidelines.md:29-31` names that test type. |
| 7 | FIX | `event-log.md:14-15` and `event-log.md:43-44` speak of "listing" only. | CLI-011 now says `overdue` is a listing in the sense of LOG-001 and LOG-006. It states the two behaviors itself: no event, and no file created for a missing log. `event-log.md` is not amended. |
| 8 | FIX | `event-log.md:58` (LOG-009) says "the same states". The first draft did not cite it, and its list mixed two designs. | The TODO under TKT-016 now splits the two forms of a fourth state and names what each one changes. `questions.md` question 2 follows. |
| 9 | ASK | The seven TODO paragraphs exist as cited. The answers belong to the user. | The status paragraph in `tickets.md` now names the three questions that change the listed tickets or the line. It says that a sign-off without them accepts the assumptions. `questions.md` has a matching "Sign-off" section. |

Two side notes. The subagent wrote scratch files to the `r3` directory of the session
scratchpad, outside this run directory. The author did not read or remove them. After the
cold read, `git diff` in the repo was identical to the snapshot, so the subagent changed
nothing in the repo.

## 4. Usage figures of the subagent

| Figure | Value |
|--------|-------|
| Tokens | 87018 |
| Tool uses | 8 |
| Duration | 184588 ms |

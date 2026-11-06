# Cold read of the overdue-tickets spec

One fresh `general-purpose` subagent, started with no context from the authoring session.
The state of the spec before any change made in response is in `before-cold-read/`.

## 1. The exact prompt given to the subagent

```text
You review a document before a person signs it off. You have the document, the
repository, and the request that started the work. You have no other context, and that
is deliberate. Change nothing in the repository or the document. You may run the
project's own commands that only read, such as its tests.

Document: /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo/docs/product-specs/tickets.md (the "Overdue tickets" section) and /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo/docs/product-specs/cli.md (the overdue items)
Repository: /Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo
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

## 2. The subagent's report, verbatim

No Blockers. Two Majors and seven Minors. Every number, example and claim about today's system that I could check holds, except the ones listed below.

Paths below are relative to `/Users/dmitri/dev/swd-skills/evals/spec/workspace/iteration-7/eval-1-spec-overdue-tickets/with_skill/run-1/outputs/repo`. I changed nothing in the repo; probe logs went to the scratchpad.

FINDINGS

**1. Severity: Major**
- Where: `docs/product-specs/cli.md` CLI-006 (lines 51-54), CLI-010 (82-85); `docs/product-specs/tickets.md` Goals (110-111) and the open question at 176-177.
- What: `OVERDUE` replaces the state, so `list` and `overdue` no longer show whether a late ticket is `open` or `assigned`. The document flags this as a TODO but understates the cost: a script that filters on `open` or `assigned` silently drops every late ticket, and any unclosed ticket older than 72 hours is late. In `overdue` every line carries the same word, so the column tells the agent nothing.
- Evidence: the CLI-006 line format is still `#<id> [<priority>] <state> <title>`, and TKT-001 limits state to `open`, `assigned`, `closed`. Goal 3 promises no change only "for a ticket that is not overdue". The open question names only one cost: "`list` does not show whether an overdue ticket is assigned".

**2. Severity: Major**
- Where: `cli.md` CLI-010 (82-85); `tickets.md` Non-goals (121-122), TKT-019 (161-163).
- What: `overdue` sorts by due time but prints neither the due time nor the lateness. The agent cannot see why the order is what it is, and the order can only be verified by reading the log file and adding the hours by hand. It is flagged as a TODO (178-179), but it is the main output of the new command.
- Evidence: TKT-019 says "sorted by due time ascending"; the non-goal says "No command prints the due time of a ticket or how late the ticket is". In the TKT-019 example the output would be ticket 2 then ticket 1, with nothing on either line to explain it.

**3. Severity: Minor**
- Where: `tickets.md` TKT-014 (131-134).
- What: "The current time is the time at which the command runs" does not name a clock, and the clause "At the exact due time the ticket is not overdue yet" cannot be observed through the CLI. Times are float seconds, so the boundary is testable only with an injected clock, which the spec does not tie to the project's existing one.
- Evidence: `docs/architecture.md` 68-69 says "Timestamps and due times are floats from the store's clock, never from the caller, see INV-005". `ticketdesk/store.py:14` has the injectable `clock=time.time`. `docs/product-specs/README.md` 38-40 requires behavior to be observable "from outside".

**4. Severity: Minor**
- Where: `tickets.md` line 5-6 and line 92-93, against TKT-015 (138-139).
- What: both intro sentences define overdue as "not closed when its due time passes". Read literally, a ticket closed after its due time qualifies, which TKT-015 denies.
- Evidence: line 92-93 says "A ticket that is not closed when its due time passes shows as `OVERDUE` in the ticket list"; TKT-015 says "A `closed` ticket is never overdue, whatever the time at which it was closed".

**5. Severity: Minor**
- Where: `cli.md` CLI-001 (20-22), CLI-006 (51-60); `tickets.md` intro (5-6).
- What: draft behavior is written in the present tense into two existing items and the file intro, with the draft marker only in the file banner. The repo tells readers to cite items by ID, so a reader who lands on CLI-001 sees "five subcommands" with no flag. If the draft is rejected, these items need reverting.
- Evidence: `ticketdesk/cli.py:15-18` registers four subcommands, and `ticketdesk overdue` today gives `invalid choice: 'overdue'`, exit 2. `docs/product-specs/README.md:3` calls the specs the "Authoritative description of what ticketdesk does". `AGENTS.md:95` says only one doc-versus-code conflict is open, the CLI-007 TODO.

**6. Severity: Minor**
- Where: `cli.md` CLI-011 (89-90); `tickets.md` Non-goals (123-124).
- What: "An extra argument is rejected with a usage error on stderr and exit code 2. Nothing is printed to stdout" also covers `ticketdesk overdue -h`. argparse gives every existing subcommand `-h` for free, so the item either forbids it for `overdue` alone or is wrong on that case. CLI-011 also sets a rule for `overdue` that no item sets for `list`.
- Evidence: `python3 -m ticketdesk.cli list --help` prints `usage: ticketdesk list [-h]` to stdout and exits 0. `list foo` exits 2 with `unrecognized arguments: foo`, and no CLI item specifies that.

**7. Severity: Minor**
- Where: `cli.md` CLI-012 (94-99).
- What: CLI-012 ties `overdue` to `list` only for a line that is not valid JSON (LOG-007). Other replay failures on a hand-edited log are left undefined for `overdue`, such as an unknown priority in a `created` event.
- Evidence: a log with `"priority": "P9"` makes `list` end in `ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']`. `docs/architecture.md` 66-67 says "A hand-edited log that violates this stops with an error".

**8. Severity: Minor**
- Where: `cli.md` CLI-010 (84-85); `tickets.md` TKT-017 (149-150).
- What: for a missing log file the spec says `overdue` prints nothing and exits 0, but not that the file stays missing. "Unchanged byte for byte" does not define that case.
- Evidence: LOG-006 says only "the first create produces ticket `1` and creates the file". Today `list` on a missing path exits 0 and creates no file.

**9. Severity: Minor**
- Where: `cli.md` line 10.
- What: "ticketdesk 0.3.0 … never prints `OVERDUE`" is false for a ticket whose title contains the word. Under the spec, only the column position separates a late ticket from a ticket titled "OVERDUE", so a script that greps for the word misfires.
- Evidence: `create "OVERDUE" --priority P1` then `list` prints `#1 [P1] open     OVERDUE` on 0.3.0.

**Checked and correct**
- TKT-014 example: at 5 hours, P1 (4 h) is overdue and P2 (24 h) is not.
- TKT-019 example: 73 − 72 = 1 hour late and 10 − 4 = 6 hours late, so ticket 2 comes first.
- CLI-006 example: the padding matches `{t.state:<8}` at `cli.py:30`, with two spaces after `OVERDUE` and three after `closed`.
- "Today `list` on a corrupt log prints a Python traceback and exits with code 1": confirmed, exit 1 with empty stdout.
- The new IDs TKT-014 to TKT-019 and CLI-010 to CLI-012 are the next free numbers, and nothing was renumbered.
- The citations of LOG-001, LOG-002, LOG-006, LOG-007, LOG-009, TKT-001, TKT-005, TKT-009 and TKT-013 say what the document claims.
- `make test` passes, 7 tests.

PARAPHRASE

**What the document proposes.** A ticket counts as overdue when it is not closed and the time at which the command runs is strictly later than its creation time plus the hours for its priority. Overdue is computed on every run and never written to the log, so assigning does not clear it and closing does. In `ticketdesk list`, an overdue ticket shows the word `OVERDUE` where its state would be; all other lines and the ID order stay as they are. A new `ticketdesk overdue` command prints only the overdue tickets, in the same line format, earliest due time first with ties broken by ID. It prints nothing and exits 0 when there are none, rejects extra arguments with exit 2, and on a corrupt log behaves as `list` does. The whole thing is a draft with eight assumptions awaiting the user's confirmation.

**How the existing system works, by the document alone.** ticketdesk 0.3.0 is a CLI with four subcommands (`create`, `assign`, `close`, `list`) that each run against one append-only JSON lines log. Tickets move from `open` to `assigned` to `closed`, or straight from `open` to `closed`. Each ticket gets a due time of creation plus 4, 24 or 72 hours for P1, P2 or P3. `list` prints every ticket in ID order as `#<id> [<priority>] <state> <title>`, with the state padded to 8 characters. Rule errors print `error: <message>` and exit 2, but a corrupt log line and an unknown priority currently escape as a traceback with exit 1, which is an open TODO.

**What I could not paraphrase.** The document does not say where "the current time" comes from, or whether any command today reads a clock outside event appends. I had to go to `store.py` and `architecture.md` for that.

## 3. Verdicts

The paraphrase matches the intent of the spec. The one part the reader could not follow is
the source of "the current time". That is a defect of the text and is fixed under
finding 3.

Counts: 7 FIX, 2 ASK, 0 REJECT. No fix changed the shape of the spec, so there was no
second cold read.

| # | Severity | Verdict | Evidence checked | What changed |
|---|----------|---------|------------------|--------------|
| 1 | Major | ASK | Holds. CLI-006 keeps `<state>` in the line format and TKT-001 limits the state to three values. A filter on `open` or `assigned` misses a line that shows `OVERDUE`. The choice between "in place of the state" and "beside the state" belongs to the user. | The open question in `tickets.md` now names both costs: neither `list` nor `overdue` shows whether an overdue ticket is assigned, and a script that selects by `open` or `assigned` misses every overdue ticket. It now cites CLI-010 too. Question 2 in `questions.md` carries the same costs. The assumption stays. |
| 2 | Major | ASK | Holds. TKT-019 sorts by due time and the non-goal says no command prints it. Whether `overdue` shows the due time is a scope decision of the user. | The open question in `tickets.md` now says that the output of `overdue` does not show why its tickets are in that order. Question 3 in `questions.md` says the same. The non-goal stays. |
| 3 | Minor | FIX | Holds. `docs/architecture.md` lines 68-69 and `ticketdesk/store.py` line 14 show one clock that stamps events. The reader could not tell where the current time comes from. | TKT-014 now says the current time is read from the same clock that stamps events, see LOG-004. A tester who controls that clock can reach the exact due instant. |
| 4 | Minor | FIX | Holds. "Not closed when its due time passes" also fits a ticket closed after its due time, which TKT-015 denies. | Both sentences now say that a ticket whose due time has passed is overdue, or shows as `OVERDUE`, until it is closed. |
| 5 | Minor | FIX | Holds. `ticketdesk/cli.py` lines 15-18 register four subcommands. A reader who lands on CLI-001 or CLI-006 by ID saw no draft marker. | CLI-001 and CLI-006 each say that the overdue part is a draft and is not built. CLI-010 to CLI-012 sit under a new "Overdue command" heading with a status line. The intro of `tickets.md` now says "see the draft under". `AGENTS.md` already lists the feature as specified and not built. |
| 6 | Minor | FIX | Holds. `python3 -m ticketdesk.cli list --help` prints `usage: ticketdesk list [-h]` and exits with code 0. `list extra` exits with code 2. | CLI-011 now rejects an unrecognized argument, gives `ticketdesk overdue extra` as the example, says 0.3.0 rejects `ticketdesk list extra` in the same way, and puts `-h` outside the item. |
| 7 | Minor | FIX | Holds. A log whose `created` event has priority `P9` ends `list` with `ValueError: unknown priority 'P9'; expected one of ['P1', 'P2', 'P3']` and exit code 1. | CLI-012 now covers every log that stops `list` with an error and names both cases. It also asks for the same error message and exit code, not the same stderr output, because a traceback differs between two commands. |
| 8 | Minor | FIX | Holds. `list` on a missing path exits with code 0 and creates no file. The spec did not say so for either listing. | TKT-017 now says that neither listing creates a missing log file. |
| 9 | Minor | FIX | Holds. `create "OVERDUE" --priority P1` then `list` prints `#1 [P1] open     OVERDUE` on 0.3.0. | The status note in `cli.md` now says 0.3.0 has no overdue behavior. CLI-006 now says the word marks an overdue ticket only in the position of the state and that a title may contain it. |

After the fixes, `prose-lint.py` reports 0 findings in `tickets.md`, `cli.md`,
`README.md`, `AGENTS.md`, and `questions.md`.

## 4. Usage figures of the subagent

| Figure | Value |
|--------|-------|
| Tokens | 85948 |
| Tool uses | 6 |
| Duration | 164514 ms |

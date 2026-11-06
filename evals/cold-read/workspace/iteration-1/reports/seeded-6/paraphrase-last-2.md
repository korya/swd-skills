FINDINGS

- Severity: Blocker
  Where: Step 2, `Ticket.is_overdue`
  What: The code is `return now > self.due_at`, with no check on state. The docstring, TKT-014, and the headline all say a closed ticket is never overdue. With this code, `overdue()` returns closed tickets, and `list` would too if it used the method. The prototype output in the document (`#3 closed`) comes from the CLI formatter, which does check state, so it doesn't exercise this method.
  Evidence: `plan.md:81-83`, against `plan.md:13` ("not closed") and `plan.md:57-58`. Unit test 3 in the test plan would fail against this code.

- Severity: Blocker
  Where: Step 2 `now()`, and the line "The store keeps its clock in the private attribute `_clock` (`ticketdesk/store.py:16`)"
  What: The attribute is the public `clock`. `self.store._clock()` raises `AttributeError` on every `overdue` and `list` call. The document contradicts itself, because the conventions section says `now()` "calls `store.clock()`".
  Evidence: `ticketdesk/store.py:16` is `self.clock = clock`, and `grep _clock` finds nothing in the package. See `plan.md:88`, `plan.md:97`, and `plan.md:187`.

- Severity: Blocker
  Where: Test plan, same-due-time case, and assumption A6
  What: The tie arithmetic is wrong. P1 is 4 hours and P2 is 24 hours, so a P1 created 12 hours after a P2 is due at a+16h, not a+24h. The tie needs a 20-hour gap. The test would not produce equal due times, so it would not test the ID tie-break. A6 has the same error. "P1 at a+12h equals P2 at a" is false. A P2 created 22 hours ago is due in 2 hours, not 6 hours ago, so it is not tied with the P1 that is due 6 hours ago.
  Evidence: `ticketdesk/sla.py:3` has `{"P1": 4, "P2": 24, "P3": 72}`. See `plan.md:151` and `plan.md:205`.

- Severity: Blocker
  Where: Step 1 CLI-010 text ("prints nothing and exits with code 1")
  What: This contradicts CLI-008, which says a successful command exits 0 and writes nothing to stderr. It also contradicts the document's own test plan ("`overdue` on a missing log prints nothing, exits 0"). Exit code 1 is what the CLI-007 TODO describes as the traceback code. Nothing in the request asks for a nonzero exit on an empty result. The spec text proposed for sign-off and the tests disagree.
  Evidence: `plan.md:71` against `plan.md:213`, and `docs/product-specs/cli.md` (CLI-008 and the CLI-007 TODO).

- Severity: Major
  Where: Step 3 (the `_line` formatter) and the conventions entry "no ticket rule in the CLI"
  What: The plan duplicates the overdue rule inside the CLI. `_line` re-implements `state in ("open","assigned") and now > due_at`, separately from `Ticket.is_overdue`. This is a ticket rule in the CLI, which the project names as a layer crossing. The document claims "Step 3 only picks a label" and that "the service keeps the query". The two copies can drift. The `list` path (formatter) and the `overdue` path (service) would then disagree about which tickets are overdue. Using the service method would fix this, and Blocker 1 shows the two copies already differ.
  Evidence: `plan.md:106`, `plan.md:186`, `docs/architecture.md:36-38`, and `docs/guidelines.md:51-53` ("A ticket rule in the CLI … is a layer crossing").

- Severity: Major
  Where: Step 6 ("These edits need no sign-off, because `AGENTS.md:93` limits the confirmation rule to product specs")
  What: The project rules say the opposite. `AGENTS.md:93` says "Do not silently rewrite specs or architecture". `docs/README.md:39` says never silently update a spec or an architecture doc. `docs/guidelines.md:78` says to confirm every doc change, and `:55` requires confirmation for `architecture.md` updates. Step 6 edits `architecture.md` and `AGENTS.md`, so it would bypass the gate the plan itself builds in Step 1.
  Evidence: `AGENTS.md:93`, `docs/README.md:39`, `docs/guidelines.md:55` and `:78-79`.

- Severity: Major
  Where: Assumptions A2–A8, the prototype output, the falsifier, and the Risks section
  What: The evidence cites `scratch/exp1_prototype.py`, `scratch/exp2_fake_clock.py`, and "exp1" runs. No `scratch/` directory exists in the repo and `git status` shows only `plan.md` untracked. I can't verify any of the experiments. The prototype output block and the "P3 set to 1 hour" result are unreproducible from what I was given.
  Evidence: `ls scratch` returns "No such file or directory".

- Severity: Minor
  Where: Step 1, TKT-014 text ("The current time comes from the store's clock")
  What: This puts an implementation detail in a behavioral spec. The spec format requires specs to be "decoupled from implementation". The wording also fits poorly next to INV-005, which is about event timestamps.
  Evidence: `docs/product-specs/README.md` ("Behavioral… describes what, not how"), and `plan.md:58-59`.

- Severity: Minor
  Where: Step 1, LOG-001 edit, and the test "`list()` and `overdue()` append no event"
  What: The unit test only compares event kinds before and after, which is weaker than the byte comparison used in the CLI test. An appended duplicate event of an existing kind would be caught only by the count, which the test doesn't state.
  Evidence: `plan.md:207` against `plan.md:214`.

- Severity: Minor
  Where: Headline and open question 1, "keeps the column count … stable for scripts"
  What: The reason given for replacing the state is that the column count stays stable. The Risks section then says scripts matching `open` or `assigned` will break. The trade-off is acknowledged but the justification oversells it, because the state information is lost. A grep-based script that filters on `open` will silently drop overdue tickets.
  Evidence: `plan.md:22-23` against `plan.md:238`.

Checked and fine: the line citations in `cli.py` (18, 28, 29), `tickets.py` (35-36), `store.py` (26-27), `AGENTS.md` (93, 102-106, 114, 116), and `architecture.md` (12, 68-69, 103). The e2e due times (1700014400 and 1700159200), the 5-line `wc` count, the claim of 7 existing tests (`make test` passes 7), and the new spec IDs (TKT-014, CLI-010) also check out.

PARAPHRASE

The document proposes a read-only change. Overdue is computed at display time and never stored. A non-closed ticket whose due time is strictly before "now" prints `OVERDUE` in the state column of `list`. A new `overdue` subcommand prints only those tickets, ordered by due time and then by ID. A service method supplies the rule and the ordering, a CLI formatter does the labeling, and six spec edits are gated on the user's sign-off before any code is written.

According to the document alone, the system works like this. A CLI parses one command and calls `TicketService`, which rebuilds every ticket by replaying an append-only log held by `EventStore`. The service computes each ticket's `due_at` from the SLA table. The store stamps events using an injectable clock, and the service holds all ticket rules. There are four subcommands and `list` prints tickets in ID order. The CLI has no tests, and every spec edit needs user confirmation. A corrupt log or an unknown priority escapes as a traceback.
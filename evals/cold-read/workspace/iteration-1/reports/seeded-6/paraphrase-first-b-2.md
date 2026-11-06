PARAPHRASE

The plan marks a ticket as overdue when it is not closed and the current time is later than its due time. It computes this at read time, so nothing new goes into the log. `ticketdesk list` would print `OVERDUE` in place of `open` or `assigned` in the state column. A new `ticketdesk overdue` subcommand would list only overdue tickets, sorted by due time and then by ID. The service would get `is_overdue`, `now()` and `overdue(now)`, and the CLI would get one shared line formatter. Six spec edits need sign-off before any code. Then come service tests, new subprocess CLI tests, doc updates, and two commits.

According to the document, the system replays an append-only event log into tickets, and each ticket carries a `due_at` derived from the SLA table. The CLI has four subcommands (`create`, `assign`, `close`, `list`). `list` prints `#id [prio] state title` with the state padded to 8 characters. The store has a private `_clock` that stamps events. The CLI has no tests, and a corrupt log or unknown priority escapes as a traceback.

FINDINGS

- Severity: Blocker
  Where: Step 2, `TicketService.now()` (and the "Project conventions" bullet, which says `store.clock()`)
  What: `now()` calls `self.store._clock()`, but the attribute is public `clock`. The plan's own convention bullet calls `store.clock()`, so the plan contradicts itself. As written, every `list` and `overdue` call would raise `AttributeError`.
  Evidence: `ticketdesk/store.py:16` is `self.clock = clock`. I ran `hasattr(store, '_clock')` and got `False`, and `hasattr(store, 'clock')` gave `True`. The plan's cite "`store.py:16` private attribute `_clock`" is wrong.

- Severity: Blocker
  Where: Step 2, `Ticket.is_overdue`
  What: The docstring and TKT-014 say "not closed", but the body is `return now > self.due_at`. `overdue()` filters only with this method, so closed past-due tickets would be listed. This breaks TKT-014, the "only overdue" request, and the e2e step "close 2, then overdue shows only #3". The CLI formatter checks state separately, so `list` hides the bug while `overdue` shows it.
  Evidence: plan lines 81-83 against lines 57-58 and 13. The unit test "closed ticket … not overdue" would fail.

- Severity: Major
  Where: Step 1, CLI-010 text, against Test plan and CLI-008
  What: The proposed CLI-010 says no overdue tickets means "prints nothing and exits with code 1". The test plan says `overdue` on a missing log "exits 0". CLI-008 says success exits 0 with nothing on stderr, and exit 1 is currently the traceback code. The spec text also contradicts the plan's own tests and the Counterfactual's "exit codes unchanged".
  Evidence: plan lines 70-71 against line 213; `docs/product-specs/cli.md:54-56`. No open question covers it.

- Severity: Major
  Where: Test plan (unit, same-due-time case) and A6
  What: The tie-break arithmetic is wrong. Creating a P2, moving the clock 12 hours, then creating a P1 gives due times a+24h and a+16h, which are not equal. The tie needs a 20-hour gap. A6 repeats the error. "P2 created 22 hours ago" is due 2 hours in the future, not 6 hours ago, and "P1 at a+12h equals P2 at a" is false. The test as written would not exercise the tie-break.
  Evidence: `ticketdesk/sla.py:3` has P1=4 and P2=24. 12+4=16, not 24. 22 hours ago plus 24 hours is +2h.

- Severity: Major
  Where: Step 3 (`_line` formatter) and "Project conventions" bullet on `architecture.md:36-38`
  What: The plan writes the overdue rule a second time in the CLI (`state in ("open","assigned") and now > due_at`) instead of calling `Ticket.is_overdue`. It justifies this with "display does not depend on a service method". That puts a ticket rule in the CLI, which the architecture forbids. It also creates two copies of the rule, and they have already diverged (see the second finding). The convention bullet then claims "Step 3 only picks a label".
  Evidence: `docs/architecture.md:36-38` ("It holds no ticket rules") and `docs/guidelines.md:51-53`.

- Severity: Major
  Where: Step 6 preamble ("These edits need no sign-off")
  What: The plan says `AGENTS.md:93` limits confirmation to product specs, which misreads it. Rewording the architecture doc and AGENTS.md without confirmation contradicts the rule. It names architecture explicitly, and the guidelines say to confirm every doc change.
  Evidence: `AGENTS.md:93` ("Do not silently rewrite specs or architecture"); `docs/guidelines.md:55` and `:78` ("Confirm every doc change with the user"). The Step 1 gate and the open questions omit the `architecture.md` and `AGENTS.md` edits.

- Severity: Minor
  Where: "Assumptions validated", prototype output, and A2 to A8
  What: Every piece of evidence cites `scratch/exp1_prototype.py` and `scratch/exp2_fake_clock.py`, but neither exists in the repo and none is in git. I could not rerun them, so the reported outputs are unverified. The A6 numbers above are demonstrably wrong, so the experiments may not match what is claimed.
  Evidence: `ls scratch` gives "No such file or directory". `git status` shows only `plan.md` untracked.

Checked and fine:
- The e2e fixture's due times (1700014400 and 1700159200).
- The `wc -l` result of 5.
- The "7 tests" count (`make test` ran 7).
- The six spec rows.
- A1 and A7.
- The line citations for `cli.py`, `AGENTS.md` and `docs/`.
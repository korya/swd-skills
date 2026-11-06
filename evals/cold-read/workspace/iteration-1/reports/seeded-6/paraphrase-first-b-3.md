PARAPHRASE

The document proposes deriving "overdue" at read time, with no new log event. A ticket would be overdue when it is not closed and the current time is later than its due time. `ticketdesk list` would show `OVERDUE` in place of `open` or `assigned`, and a new `ticketdesk overdue` subcommand would list only overdue tickets, sorted by due time and then by ID. The work is a spec-edit gate first (new TKT-014, TKT-015 and CLI-010, plus edits to CLI-001, CLI-006 and LOG-001), then service code, CLI code, service tests, new CLI subprocess tests, doc updates and two commits.

According to the document alone, the system works like this. `cli.py` calls `TicketService`, which rebuilds tickets by replaying an append-only log held by `EventStore`, and every ticket carries a `due_at` computed from an SLA table. The store owns an injectable clock that stamps events. Tickets are listed in ID order, the CLI has four subcommands and no tests, and spec changes need user sign-off. I could not paraphrase the `scratch/exp1_prototype.py` and `scratch/exp2_fake_clock.py` experiments. The document cites them as evidence, but they are not in the document.

FINDINGS

- **Severity:** Blocker
  **Where:** Step 2, `TicketService.now()`, and the sentence "The store keeps its clock in the private attribute `_clock` (`ticketdesk/store.py:16`)".
  **What:** `EventStore` has no `_clock` attribute. The attribute is the public `clock`, so `self.store._clock()` raises `AttributeError` on every `overdue` and `list` call. The plan contradicts itself, because the conventions section says `now()` "calls `store.clock()`".
  **Evidence:** `store.py:16` is `self.clock = clock`, and `grep _clock` finds nothing in `ticketdesk/`. The plan's own convention row reads "`TicketService.now()`, which calls `store.clock()`".

- **Severity:** Blocker
  **Where:** Step 2, `Ticket.is_overdue`.
  **What:** The method is `return now > self.due_at` and never checks the state. Its docstring says "past the due time and not closed", and TKT-014 says a closed ticket is never overdue. As written, `overdue()` would list closed tickets that closed after their due time. Step 3's formatter does check the state, so `list` and `overdue` would disagree.
  **Evidence:** Step 2 code against the TKT-014 text and the test case "A closed ticket past its due time is not overdue". Nothing in `tickets.py` filters closed tickets.

- **Severity:** Blocker
  **Where:** CLI-010 draft text (Step 1), against the test plan and CLI-008.
  **What:** CLI-010 says that with no overdue tickets `overdue` "prints nothing and exits with code 1". The test plan says `overdue` on a missing log "prints nothing, exits 0". CLI-008 says every successful command exits 0. The Step 3 code has no exit-1 path. The user would be asked to sign off a self-contradicting spec.
  **Evidence:** The plan's CLI-010 block, the test-plan bullet "`overdue` on a missing log prints nothing, exits 0", and `cli.md:54-56`.

- **Severity:** Major
  **Where:** Assumption A6, the test plan's same-due-time case, and the e2e commentary.
  **What:** The tie-break arithmetic is wrong. P1 is due after 4h and P2 after 24h, so equal due times need the P1 to be created 20h after the P2, not 12h. In the prototype description, a P2 created 22h ago is due in 2h, which is in the future, not 6h ago. The planned unit test would not produce a tie, so it would not exercise the ID tie-break.
  **Evidence:** `sla.py:3` has `{"P1": 4, "P2": 24, "P3": 72}`. P2 at a is due at a+24h. P1 at a+12h is due at a+16h, which is not equal. P2 created 22h ago is due at +2h.

- **Severity:** Major
  **Where:** Step 3, `_line`, against the convention row "no ticket rule in the CLI".
  **What:** The plan puts a second copy of the overdue rule (`t.state in ("open","assigned") and now > t.due_at`) in the CLI, and says `Ticket.is_overdue` is not used for display. The project treats a ticket rule in the CLI as a layer crossing. The duplicate also invites the divergence in the finding on `is_overdue`. The plan claims the opposite: "step 3 only picks a label", and the display check "sits next to the formatting".
  **Evidence:** `architecture.md:36-38` ("It holds no ticket rules") and `guidelines.md:51-53` ("A ticket rule in the CLI… is a layer crossing"). The Step 3 bullet writes the check out in the formatter.

- **Severity:** Major
  **Where:** Step 6, "These edits need no sign-off, because `AGENTS.md:93` limits the confirmation rule to product specs".
  **What:** The project rules do not limit confirmation to specs. Edits to `architecture.md` and to `AGENTS.md` also need sign-off, and Step 1's gate does not cover them. Doing Step 6 unconfirmed breaks a process rule, and the commit would need reworking.
  **Evidence:** `AGENTS.md:93` ("Doc changes need user confirmation. Do not silently rewrite specs or architecture"). `docs/README.md:39` ("Never silently update a spec or an architecture doc"). `guidelines.md:55` and `guidelines.md:78` ("Confirm every doc change").

- **Severity:** Major
  **Where:** "Assumptions validated" table, the prototype output, and the Risks section.
  **What:** All the experiment evidence (A2 to A8, the prototype output, the P3-to-1-hour claim) cites `scratch/exp1_prototype.py` and `scratch/exp2_fake_clock.py`. Those files are not in the repository. `git status` shows only `plan.md` as untracked. The reviewer and the user cannot re-run any of it, and the A6 numbers that can be checked are wrong.
  **Evidence:** `ls scratch` returns "No such file or directory".

- **Severity:** Minor
  **Where:** Step 3, "Register the subcommand… with `sub.add_parser("overdue")`", and the final `else:` branch.
  **What:** The new `elif args.cmd == "list"` / `else` structure makes `overdue` the catch-all, so a future subcommand that is not handled would silently run `overdue`. An explicit `elif args.cmd == "overdue":` is safer.
  **Evidence:** The Step 3 bullets against `cli.py:28`.

- **Severity:** Minor
  **Where:** Step 6, `architecture.md:68-69`, and the text of TKT-014.
  **What:** The architecture says the service "never reads or writes the file itself" and gets everything from the store. Having the service reach into the store's clock is a new service-to-store coupling that the plan treats as a doc tweak. A public `clock` accessor or a service-level clock would be cleaner, and the plan does not raise this as a decision.
  **Evidence:** `architecture.md:40-44`.

Checked and fine: the due-time arithmetic in the e2e sequence (1700014400 and 1700159200), the 5-line `wc -l` count, the "7 tests" count (`make test` runs 7), the `OVERDUE` width (7 characters, padded to 8), and the six rows of spec edits.
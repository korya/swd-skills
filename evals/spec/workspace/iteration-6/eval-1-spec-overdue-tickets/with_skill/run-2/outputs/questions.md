# Questions for the overdue tickets spec

Nobody was available to answer during this run. Each question below states the assumption
the spec proceeds on and the criteria that change if the answer differs. The spec repeats
these questions under "Open questions" at the end of `docs/product-specs/tickets.md`.

## Blocking: these change the shape of the spec

I would have asked these three as one batch before drafting, and waited for the answers.

1. **Does `OVERDUE` replace the state word in `ticketdesk list`, or sit next to it?**
   The request says overdue tickets "show as OVERDUE". A replacement hides whether anyone
   is assigned, and that matters most for a late ticket.
   - Assumption: the line keeps its state and adds `OVERDUE` after it, as in
     `#5 [P1] assigned OVERDUE VPN down`.
   - Affects: CLI-006, CLI-010, TKT-016.
2. **Is overdue a derived marker, or a new ticket state that the log records?**
   A recorded state needs a new event kind and a command that appends it. That changes
   TKT-001, LOG-001, and LOG-002.
   - Assumption: overdue is derived each time a command runs. It is never a state and
     never an event.
   - Affects: the overdue invariant in `tickets.md`, TKT-016, the first non-goal.
3. **Can a closed ticket be overdue?**
   - Assumption: no. This holds also for a ticket that closed after its due time.
   - Affects: TKT-015 and the non-goal "No history of late closes".

## Non-blocking: the draft proceeds on an assumption

4. **Is a ticket overdue at the exact instant of its due time?**
   - Assumption: no. A ticket is overdue only when the time is later than its due time.
   - Affects: TKT-014.
5. **Does `ticketdesk overdue` show how late each ticket is?**
   - Assumption: no. It prints the same line as `list`.
   - Affects: CLI-010.
6. **What exit code does `ticketdesk overdue` return when no ticket is overdue?**
   A nonzero code would let a script test for overdue tickets.
   - Assumption: code 0 with no output, as `list` does with no tickets.
   - Affects: CLI-010.
7. **How does `ticketdesk overdue` report a corrupt log?**
   The open TODO under CLI-007 already covers this case for every command.
   - Assumption: `overdue` behaves exactly as `list` does, whatever that TODO decides.
   - Affects: CLI-012.

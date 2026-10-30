# Questions for the overdue tickets spec

Nobody was available to answer during this run. Each question below states the assumption
the draft spec uses. The spec marks each one with a `TODO:` line at the item it affects.

## Blocking questions (these change the shape of the spec)

1. **Is overdue a new ticket state, or a condition shown on top of the state?**
   - Assumption: a condition. The state stays `open` or `assigned` (TKT-016). The help desk
     computes overdue from the current time each time a command runs. It never writes
     overdue to the log.
   - Why it matters: a new state would contradict TKT-001 and LOG-002. It would also break
     INV-001 and LOG-009, because the state would then depend on the clock and not only on
     the log.
2. **Does `OVERDUE` replace the state word in `ticketdesk list`, or appear next to it?**
   - Assumption: it replaces the state word, padded to 8 characters like a state (CLI-010).
   - Cost of the assumption: the line no longer tells whether an overdue ticket is `open`
     or `assigned`. The alternative keeps the state and adds a marker, which changes the
     CLI-006 line format.
3. **Can a closed ticket be overdue?**
   - Assumption: no. A `closed` ticket is never overdue, also when it was closed after its
     due time (TKT-015).

## Non-blocking questions (the draft proceeds on the assumption)

4. **Which moment counts as overdue?** Assumption: a ticket is overdue only when the
   current time is later than its due time. At the exact due time it is not overdue
   (TKT-014).
5. **What does a `ticketdesk overdue` line look like?** Assumption: the same line as
   `ticketdesk list` prints for that ticket, with `OVERDUE` in the state column (CLI-011).
6. **How are overdue tickets with the same due time ordered?** Assumption: by ID ascending
   (TKT-017).
7. **Should `overdue` show the due time or how late a ticket is?** Assumption: no. Today no
   command shows a due time. The spec lists this as out of scope.
8. **Should `overdue` take filters such as priority or assignee?** Assumption: no. It takes
   no arguments, and an extra argument is a usage error (CLI-012).
9. **What happens when `overdue` meets a corrupt log line?** Assumption: the same as every
   other command, per LOG-007. The open TODO under CLI-007 decides how that error reaches
   the user, and its answer covers `overdue` too.

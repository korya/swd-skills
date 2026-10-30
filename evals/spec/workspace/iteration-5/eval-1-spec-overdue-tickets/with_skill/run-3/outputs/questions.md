# Questions for the overdue tickets spec

Nobody was available to answer during this run. Each question states the assumption the
spec uses until someone answers. The spec marks each assumption with a TODO under the
criterion it shapes.

## Blocking: these change the shape of the spec

1. **In `ticketdesk list`, does `OVERDUE` replace the state word, or does it appear next to
   it?**
   Assumption: the state stays and `OVERDUE` follows it, as in
   `#1 [P1] assigned OVERDUE Printer on fire` (CLI-010). Lines of tickets that are not
   overdue stay unchanged. If `OVERDUE` must replace the state, CLI-010 changes. If overdue
   must become a real state, it conflicts with TKT-001 and the forward-only rule.
2. **Can a closed ticket be overdue, for example one closed after its due time?**
   Assumption: no. Only `open` and `assigned` tickets can be overdue (TKT-014, TKT-016).
   A report of tickets closed late is a non-goal.
3. **Does `ticketdesk overdue` need to show the due time or how late each ticket is?**
   Assumption: no. Its lines use the `list` format with the marker (CLI-011). A display of
   due time or lateness is a non-goal.

## Not blocking: assumptions in the draft

4. A ticket at exactly its due time is not yet overdue (TKT-015).
5. Overdue tickets with the same due time sort by ID ascending (TKT-018).
6. `ticketdesk overdue` exits with code 0 whether or not overdue tickets exist (CLI-011).
7. With no overdue tickets, `ticketdesk overdue` prints nothing (CLI-012), as `list` does.
8. `ticketdesk overdue` takes no arguments or filters (CLI-013).
9. The due time stays the wall-clock rule of TKT-005. Business hours are a non-goal.
10. On a corrupt log, `overdue` behaves as `list` does (CLI-014). The open TODO under
    CLI-007 still decides the exit code for both.

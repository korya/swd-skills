# Questions for the overdue-tickets spec

Nobody was available to answer these on 2026-10-29. The spec proceeds on the stated
assumption for each. The same list is the "Open questions for overdue tickets" section at
the end of `repo/docs/product-specs/tickets.md`.

Questions that change the shape of the spec:

1. **How does `ticketdesk list` show an overdue ticket?**
   Assumption: `OVERDUE` replaces `open` or `assigned` in the state field (CLI-010). This
   hides whether an overdue ticket has an assignee. The alternative shows the state and an
   `OVERDUE` marker together, which changes the line format of CLI-006.
2. **Can a closed ticket be overdue?**
   Assumption: no (TKT-015). A ticket closed after its due time shows `closed` and never
   appears in `ticketdesk overdue`. Reporting late closes is a non-goal.
3. **Does `ticketdesk overdue` show the due time or how late each ticket is?**
   Assumption: no. Each line uses the `list` format of CLI-006 (CLI-011).

Questions that do not change the shape:

4. **Is a ticket overdue at exactly its due time?** Assumption: no, only after it (TKT-014).
5. **Does "oldest due first" mean the earliest due time, not the earliest creation time?**
   Assumption: earliest due time, ties by ID ascending (TKT-017).
6. **Should `ticketdesk overdue` signal overdue tickets through its exit code?**
   Assumption: no. It exits with code 0 in both cases (CLI-011).

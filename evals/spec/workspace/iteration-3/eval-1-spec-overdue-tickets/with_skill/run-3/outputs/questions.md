# Questions for the overdue spec

Nobody was available to answer during this run. Each question states the assumption the
draft spec proceeds on. The spec files carry the same questions in their "Open questions"
sections.

## Blocking the shape (one batched round)

1. **Does `OVERDUE` replace the state in `ticketdesk list`, or add to it?**
   Assumption (CLI-010): `OVERDUE` takes the place of `open` or `assigned` in the state
   column, for example `#3 [P1] OVERDUE  Printer on fire`. Cost: `list` no longer shows
   whether an overdue ticket has an assignee. Alternative: keep the state and add the
   marker as a separate column.

2. **Which tickets can be overdue?**
   Assumption (TKT-014): both `open` and `assigned` tickets. A `closed` ticket is never
   overdue, even when it was closed after its due time.

## Proceeding as assumptions

3. **Is a ticket at exactly its due time overdue?**
   Assumption (TKT-014): no. Only a current time strictly later than the due time makes a
   ticket overdue, which matches "pass their due time".

4. **Should `ticketdesk overdue` show the due time or how late each ticket is?**
   Assumption (CLI-011): no. Each line uses the `list` line format. The extra columns are a
   non-goal for now.

5. **Should `ticketdesk overdue` exit nonzero when overdue tickets exist?**
   Assumption (CLI-011): no, it exits 0 either way. A nonzero code would collide with the
   error code 2 of CLI-007.

6. **How does `overdue` handle a corrupt log?**
   Assumption: it adds no rule. LOG-007 stops it, and the open TODO under CLI-007 (traceback
   with exit code 1 today) applies to it unchanged.

7. **Is the in-place edit to CLI-001 acceptable?**
   Assumption: yes. CLI-001 now lists five subcommands instead of four. The ID stays
   because the rule is the same and only the list grew.

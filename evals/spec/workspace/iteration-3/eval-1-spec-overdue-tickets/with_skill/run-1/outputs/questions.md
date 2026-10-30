# Questions for the overdue-tickets spec

Nobody was available to answer during this run. Each question below states the assumption
the draft spec proceeds on. Change the assumption and the listed criteria change with it.

## Blocking questions (they change the shape of the spec)

These would normally be asked as one batch before drafting.

1. **Can a closed ticket be overdue?**
   Assumption: no. Only `open` and `assigned` tickets can be overdue. A ticket closed after
   its due time shows as `closed` and never as `OVERDUE`. Affects TKT-014, TKT-015, CLI-010.
2. **Does `OVERDUE` replace the state in `ticketdesk list`, or appear next to it?**
   Assumption: next to it. The line keeps the state and adds the word `OVERDUE` between
   the state and the title: `#3 [P1] assigned OVERDUE Printer on fire`. The agent still
   sees whether someone owns the ticket. Lines of tickets that are not overdue do not
   change. Affects CLI-006 and CLI-010.
3. **When exactly does a ticket become overdue?**
   Assumption: when the clock at the moment the command runs is later than the due time
   from TKT-005. At exactly the due time the ticket is not yet overdue. Affects TKT-014.

## Open questions (the draft proceeds, they can be settled at sign-off)

4. **Should `ticketdesk overdue` print the same line as `list`?**
   Assumption: yes, the same line format, so every line carries `OVERDUE`. Affects CLI-010.
5. **Should either command show the due time or how late a ticket is?**
   Assumption: no. This is listed as out of scope in `tickets.md`. Agents may want it to
   triage, so it is a candidate follow-up.
6. **Should a ticket's due time pause or move when it is assigned?**
   Assumption: no. The due time stays as TKT-005 defines it. Affects TKT-016.
7. **How do errors from `overdue` behave while the CLI-007 TODO is open?**
   Assumption: `overdue` behaves exactly like `list`. A corrupt log line escapes the same
   way it does for `list` today. The spec defers to the open CLI-007 TODO and does not
   resolve it.
8. **Is a title that starts with the word `OVERDUE` a problem?**
   With assumption 2, the line `#4 [P3] open     OVERDUE invoices` is ambiguous. It can
   mean an overdue ticket titled `invoices` or a ticket titled `OVERDUE invoices`. The
   draft accepts this. Say if scripts parse `list` output and need an unambiguous column.

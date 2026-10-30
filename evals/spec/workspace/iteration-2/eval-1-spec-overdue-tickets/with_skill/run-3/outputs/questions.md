# Questions for the overdue-tickets spec

Nobody was available to answer during this run. The spec proceeds on the stated assumption
for each question. The spec lists the same items under "Open questions for overdue
tickets" in `docs/product-specs/tickets.md`.

## Blocking: these change the shape of the spec

The skill asks these as one batch and waits for the answers. This run did not wait.

1. **Does `OVERDUE` replace the state in `ticketdesk list`, or appear next to it?**
   Assumption: it replaces the state word, padded to 8 characters like the state (CLI-010).
   Cost of the assumption: an overdue line no longer shows `open` or `assigned`. CLI-006
   changes, because its state column can now hold a value that is not a TKT-001 state.
   The alternative adds a column and changes the line shape for every ticket.
2. **Can a `closed` ticket be overdue?**
   Assumption: never (TKT-014). A ticket that an agent closed after its due time shows
   `closed`. The alternative needs the close time in the overdue rule.

## Non-blocking: proceeding on an assumption

3. **Does `ticketdesk overdue` show the due time or how late each ticket is?**
   Assumption: no. The line has the `ticketdesk list` shape (CLI-011). Recorded as a
   non-goal.
4. **Does `ticketdesk overdue` exit nonzero when overdue tickets exist, for scripts?**
   Assumption: no. It exits with code 0 with or without overdue tickets (CLI-011).
5. **Which exit code does a corrupt log give for `ticketdesk overdue`?**
   Assumption: the same as for `ticketdesk list`. The TODO under CLI-007 leaves that code
   open for every command (CLI-012).
6. **Is a ticket overdue at the exact second of its due time?**
   Assumption: no. It is overdue only after its due time (TKT-014).
7. **How are tickets with the same due time ordered in `ticketdesk overdue`?**
   Assumption: by ID ascending (TKT-016).
8. **Is `OVERDUE` written in capitals, unlike the lowercase states?**
   Assumption: yes, as the request wrote it. The capitals set the marker apart from the
   states.
9. **Does `ticketdesk overdue` take filters, such as by assignee or priority?**
   Assumption: no. Recorded as a non-goal. An argument after `overdue` is a usage error
   (CLI-013).

# Questions for the overdue tickets spec

Nobody could answer during this run. The spec proceeds on the assumption under each
question. The same questions sit at the end of `docs/product-specs/tickets.md`.

## Blocking: these change the shape of the spec

The skill asks these as one batch before drafting. Each answer can move a criterion
between files or change the output format.

1. **How does `ticketdesk list` show an overdue ticket?** The request says "show as
   OVERDUE".
   - Assumption: a marker between the state and the title, as in
     `#5 [P1] open     OVERDUE Printer on fire`. The state stays visible. See CLI-006.
   - Other option: `OVERDUE` replaces the state. That hides whether someone has the ticket.
     It also makes OVERDUE look like a fourth state next to TKT-001.
2. **Is a ticket that was closed after its due time overdue?**
   - Assumption: no. A `closed` ticket is never overdue. See TKT-015.
3. **Is overdue derived on each command, or recorded in the log?**
   - Assumption: derived from the due time and the current time. No event is appended. See
     TKT-016 and LOG-001.
   - Other option: an overdue event. That adds a new event kind to LOG-002 and needs a
     process that appends it.

## Not blocking: open questions in the draft

4. **Is a ticket overdue at exactly its due time?** Assumption: no. See TKT-014.
5. **How are overdue tickets with the same due time ordered?** Assumption: by ID, lowest
   first. See TKT-017.
6. **Does any script parse the output of `ticketdesk list`?** The marker changes the line
   format for overdue tickets. A script that reads the title after the state column then
   reads `OVERDUE` as part of the title.
7. **Do agents want the due time, or how late a ticket is, in the `overdue` output?**
   Assumption: no. The `overdue` lines are the same as the `list` lines. See CLI-010.
8. **How does the repo mark a spec item that is not built yet?** No convention exists.
   Assumption: a `Status: proposed` line under each new or changed item.
9. **Should a corrupt log stop `overdue` with a traceback?** It does for every command
   today, see the open TODO under CLI-007. Assumption: `overdue` follows whatever the
   answer to that TODO is. This spec does not settle it.

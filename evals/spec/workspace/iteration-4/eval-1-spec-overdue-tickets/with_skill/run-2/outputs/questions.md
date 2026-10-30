# Questions for the overdue-tickets spec

Nobody was available to answer during the run. Each question below names the assumption the
draft in `docs/product-specs/overdue.md` uses until the user answers.

## Questions that change the shape of the spec

These would normally be asked as one batch before drafting.

1. **Does `OVERDUE` replace the state in `ticketdesk list`, or sit beside it?**
   "Show as OVERDUE" can mean that the state column reads `OVERDUE`. That reading hides
   whether a ticket is `open` or `assigned`.
   - Assumption: the line keeps the state and adds `OVERDUE` after it. The line is
     `#<id> [<priority>] <state> OVERDUE <title>`, see CLI-010.
2. **Can a closed ticket be overdue?** A ticket closed after its due time missed its
   target, but nobody needs to work on it.
   - Assumption: a closed ticket is never overdue, see OVD-002. Reports of late closes are
     a non-goal.
3. **Is overdue a ticket state or a computed mark?** A fourth state would change TKT-001
   and LOG-009, and it would need an event in the log.
   - Assumption: overdue is a mark computed at the time a command runs. It is not a state
     and the log never records it.

## Questions that do not change the shape

4. **Is a ticket overdue at exactly its due time?** The request says "pass their due time".
   - Assumption: no. A ticket is overdue only when the current time is later than its due
     time, see OVD-001.
5. **Should `ticketdesk overdue` show the due time or how late each ticket is?**
   - Assumption: no. It prints the same line as `ticketdesk list` prints for that ticket,
     see CLI-011. This is listed as a non-goal until the user decides.
6. **How are tickets with the same due time ordered?**
   - Assumption: by ticket ID, lowest first, see OVD-004.
7. **Do scripts parse the output of `ticketdesk list`?** The new mark changes the line of
   an overdue ticket.
   - Assumption: the change is acceptable. Lines of tickets that are not overdue are
     unchanged.
8. **What does `ticketdesk overdue` do on a corrupt log?** CLI-007 has an open TODO. Today
   a corrupt line escapes as a Python traceback with exit code 1.
   - Assumption: `overdue` behaves exactly like `list` on the same log, see OVD-008. The
     spec does not settle the CLI-007 TODO.

# Questions for the overdue-tickets spec

Nobody was available to answer these during the run. Each question states the assumption
the spec uses until you answer. The spec marks the same items as open questions.

## Blocking questions: they change the shape of the spec

1. **Does `OVERDUE` replace the state in `ticketdesk list`, or appear next to it?**
   The request says overdue tickets "show as OVERDUE". Replacing the state hides whether
   somebody has the ticket. Adding a marker keeps that information.
   Assumption: the line keeps its state and adds a marker before the title.
   Example: `#2 [P1] assigned OVERDUE Printer on fire`. See CLI-010.

2. **Can a closed ticket be overdue?**
   A ticket that was closed after its due time missed its target. The request is about
   tickets that agents still have to work on.
   Assumption: a `closed` ticket is never overdue. Reports on late closures are out of
   scope. See TKT-014.

3. **Does "oldest due first" mean the earliest due time?**
   It can also mean the oldest ticket, by creation time or ID. The two orders differ
   because priorities have different due times.
   Assumption: earliest due time first, ties by ID ascending. See TKT-016.

4. **Is `ticketdesk overdue` for the whole team, or for one agent?**
   An agent may want only the overdue tickets assigned to them.
   Assumption: the command lists every overdue ticket and takes no filter arguments.
   See CLI-011 and CLI-012.

## Questions that do not block the draft

5. **Is a ticket overdue at the exact second of its due time?**
   Assumption: no. A ticket is overdue only when the current time is later than its due
   time. See TKT-014.

6. **How must `ticketdesk overdue` report a corrupt log line?**
   Today `list` lets a corrupt line escape as a Python traceback with exit code 1. That
   is the open TODO under CLI-007.
   Assumption: `overdue` behaves the same as `list`. The answer to the CLI-007 TODO
   applies to both commands. See CLI-011.

7. **Must the output show how late a ticket is, for example "3h over"?**
   Assumption: no. The marker shows only that the ticket is overdue.

8. **What happens when a ticket title starts with the word `OVERDUE`?**
   A reader of the list line then cannot tell the marker from the title.
   Assumption: the spec accepts this ambiguity. See CLI-010.

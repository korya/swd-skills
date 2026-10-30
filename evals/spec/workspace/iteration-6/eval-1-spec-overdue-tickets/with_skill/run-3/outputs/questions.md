# Questions for the overdue spec

Nobody was available to answer these during the run. The spec proceeds on the stated
assumption for each one. Change an answer, and the listed criteria change with it.

## Blocking questions, asked as one round

These answers change the shape of the spec. Each one decides who the feature serves or
where its boundary sits.

1. **Does `OVERDUE` replace the state in `ticketdesk list`, or sit next to it?**
   The request says overdue tickets "show as OVERDUE". The line has one state column
   today, see CLI-006.
   - Assumption: the state stays, and the word `OVERDUE` appears between the state and
     the title. Overdue is not a fourth state, so TKT-001 is unchanged. Agents still see
     whether an overdue ticket has an assignee.
   - Affects: CLI-006, CLI-010, TKT-014.
2. **Can a closed ticket be overdue?**
   A ticket can close after its due time. The request is about work that agents still
   have to do.
   - Assumption: a closed ticket is never overdue, whenever it closed. It gets no marker
     and `ticketdesk overdue` does not show it.
   - Affects: TKT-015, CLI-010, CLI-011.
3. **What does one line of `ticketdesk overdue` look like?**
   The request names the content and the order, but not the line format.
   - Assumption: each line is the same line that `ticketdesk list` prints for that
     ticket, the `OVERDUE` marker included. Agents learn one format.
   - Affects: CLI-011.

## Questions that do not block the shape

These proceed as assumptions. They are listed as open questions at the end of the
overdue section in `docs/product-specs/tickets.md`.

4. **Is a ticket overdue at the exact second of its due time?**
   Assumption: no. A ticket becomes overdue only when the current time is later than its
   due time. The request says "pass their due time". See TKT-014.
5. **How are tickets with the same due time ordered in `ticketdesk overdue`?**
   Assumption: by ticket ID, ascending. See TKT-016.
6. **What does `ticketdesk overdue` print when no ticket is overdue?**
   Assumption: nothing, with exit code 0. This matches `list` with no tickets, see
   CLI-006. See CLI-011.
7. **Should agents see how late a ticket is, such as "3h late"?**
   Assumption: no. The marker only says that a ticket is overdue. This is a non-goal
   until someone asks for it.
8. **Does a title that starts with the word `OVERDUE` need protection?**
   A script that reads `list` output cannot tell such a title from the marker.
   Assumption: no. Agents read the output, and scripts are not a stated user.
9. **Does a corrupt log make `ticketdesk overdue` fail the same way as `list`?**
   CLI-007 has an open TODO: a corrupt log line escapes as a traceback with exit code 1.
   Assumption: `overdue` follows whatever answer that TODO gets. This spec does not
   decide it. See CLI-011.

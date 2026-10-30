# Questions for the overdue-tickets spec

Nobody could answer questions during this run. Each question below states the assumption the
draft spec uses. The spec amends `docs/product-specs/tickets.md` (TKT-014 to TKT-016) and
`docs/product-specs/cli.md` (CLI-001, CLI-006, CLI-010, CLI-011).

## Blocking: these change the shape of the spec

The spec skill asks these in one batch before drafting. The draft proceeds on the stated
assumption, and a TODO in the spec marks each one.

1. **Q1. Does `OVERDUE` replace the state in `ticketdesk list`, or appear next to it?**
   Assumption: it appears after the padded state and before the title, as in
   `#4 [P1] assigned OVERDUE Printer on fire`. Replacing the state would hide whether an
   overdue ticket has an assignee. Lines of tickets that are not overdue do not change.
   See CLI-011.
2. **Q2. Can a closed ticket be overdue?**
   Assumption: no. Only `open` and `assigned` tickets are overdue. A ticket closed after
   its due time is not shown as overdue, and nothing records that it closed late. See
   TKT-014 and the non-goals in `tickets.md`.

## Not blocking: the draft states an assumption

3. **Q3. Is a ticket overdue at the exact second of its due time?**
   Assumption: no. A ticket is overdue only when the current time is later than its due
   time. See TKT-014.
4. **Q4. How does `ticketdesk overdue` order tickets with the same due time?**
   Assumption: by ID ascending, which matches the order of `list` in TKT-013. See TKT-016.
5. **Q5. Does `ticketdesk overdue` show the due time or how late each ticket is?**
   Assumption: no. Each line is the same as the line of that ticket in `list`. Showing
   lateness is listed as a non-goal. See CLI-010.
6. **Q6. What does `ticketdesk overdue` print when no ticket is overdue?**
   Assumption: nothing, with exit code 0. This matches `list` with no tickets in CLI-006.
   See CLI-010.
7. **Q7. Is a changed `list` line acceptable for scripts that read the output?**
   Assumption: yes. The overdue marker changes the line format of CLI-006 for overdue
   tickets only. A title that starts with `OVERDUE ` makes a line ambiguous to a script.
   The repo records no script that reads `list` output.

## Existing conflict that the new command inherits

8. **Q8. Should CLI-007 cover a corrupt log line?**
   The open TODO under CLI-007 already asks this. Today a corrupt log line escapes as a
   Python traceback with exit code 1. The draft says `overdue` fails as `list` fails, see
   CLI-010. The answer to the CLI-007 TODO then applies to both commands.

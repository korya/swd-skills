# Questions for the overdue tickets spec

Nobody was available to answer during this run. The spec proceeds on the assumption under
each question. Answer any of them and the spec changes at the cited ID.

## Blocking the shape of the spec

These three questions set the boundary of the feature and its visible contract.

1. **Closed tickets.** Should a ticket that was closed after its due time count as overdue?
   - Assumption: no. A `closed` ticket is never overdue. Only `open` and `assigned` tickets
     can be overdue (TKT-014).
2. **The marker in `ticketdesk list`.** Should `OVERDUE` sit next to the state, or replace
   the state word?
   - Assumption: next to it. The line is `#<id> [<priority>] <state> OVERDUE <title>`, so the
     agent still sees `open` or `assigned` (CLI-011).
   - Side effect: a script that splits a `list` line on spaces sees one extra word on an
     overdue line. Lines of other tickets do not change.
3. **The `ticketdesk overdue` line.** Should each line also show the due time, or how long
   ago the due time passed?
   - Assumption: no. Each line is the same as the `list` line for that ticket (CLI-010).

## Open, not blocking

4. **The exact due time.** Is a ticket overdue at the exact second of its due time?
   - Assumption: no, only when the current time is later than the due time (TKT-014).
5. **Equal due times.** How are overdue tickets with the same due time ordered?
   - Assumption: by ID ascending (TKT-015).
6. **The current time.** Should a user be able to set the current time, for example to see
   what will be overdue tomorrow?
   - Assumption: no. The command uses the clock of the machine that runs it. No criterion
     covers such an option.
7. **Corrupt log.** `ticketdesk overdue` fails on a corrupt log exactly as `ticketdesk list`
   does (CLI-010B). The open TODO under CLI-007 still decides whether that failure is a
   traceback with exit code 1 or `error: <message>` with exit code 2.
   - Assumption: this spec takes no side on that TODO. It only ties the two commands
     together.

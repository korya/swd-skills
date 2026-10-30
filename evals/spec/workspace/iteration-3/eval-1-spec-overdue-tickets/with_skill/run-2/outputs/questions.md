# Questions for the overdue-tickets spec

Nobody was available to answer on 2026-10-29. The draft in
`docs/product-specs/overdue.md` proceeds on the assumption under each question. The same
questions close that file.

## Blocking: these change the shape of the spec

Asked as one batch. The skill would wait for answers here.

1. **Does `OVERDUE` replace the state in `ticketdesk list`, or does it appear next to it?**
   Replacing the state would hide whether the ticket is `open` or `assigned`. It would
   also make "overdue" look like a fourth state, against TKT-001.
   Assumption: next to it. The line becomes `#<id> [<priority>] <state> OVERDUE <title>`.
   Overdue is derived, not a state (OVD-003, CLI-006).
2. **Can a closed ticket be overdue?** For example, a ticket closed after its due time.
   Assumption: no. Only `open` and `assigned` tickets can be overdue (OVD-002).

## Non-blocking: proceeding on the assumption

3. **Is a ticket overdue at the exact second of its due time?**
   Assumption: no. Overdue means the current time is strictly later than the due time
   (OVD-001).
4. **Does "oldest due first" mean the earliest due time first?**
   Assumption: yes. Equal due times go by ID ascending (OVD-006).
5. **Should `ticketdesk overdue` show more than the `list` line, such as the due time or
   the time since the due time?**
   Assumption: no. It prints the same line as `list` (CLI-010).
6. **Should `ticketdesk overdue` exit with a non-zero code when overdue tickets exist, so
   a script can alert on it?**
   Assumption: no. It exits with code 0 (CLI-008).
7. **Does any script parse the output of `ticketdesk list`?** The marker changes the line
   of an overdue ticket.
   Assumption: no script depends on the old line.
8. **Should the feature have its own spec file, or only new items in `tickets.md` and
   `cli.md`?**
   Assumption: its own file, `overdue.md` with prefix `OVD`. The command surface stays in
   `cli.md`, as for every other command.

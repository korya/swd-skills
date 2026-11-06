# Questions for the overdue-tickets spec

Nobody was available during this run, so each question carries the assumption the spec
proceeds on. An answer that differs from the assumption changes the IDs named beside it.

## Blocking questions

Each answer here moves the boundary of the feature or the meaning of success. The skill
asks these as one batch and waits for the answers.

1. **Which tickets can be overdue?** Is a ticket overdue only while it is `open` or
   `assigned`, or does a ticket that was closed after its due time also show as late?
   - Assumption: only `open` and `assigned` tickets can be overdue. A `closed` ticket is
     never overdue, even when it was closed late.
   - Affects: TKT-014, TKT-015, CLI-006.

2. **How does `OVERDUE` show in `ticketdesk list`?** Does the word take the place of the
   state, or does the line show the state and `OVERDUE` together?
   - Assumption: `OVERDUE` takes the place of `open` or `assigned` in the state column.
     Lines of tickets that are not overdue stay byte for byte as they are today.
   - Cost of the assumption: neither `list` nor `overdue` shows whether an overdue ticket
     is assigned. A script that selects lines by `open` or `assigned` misses every overdue
     ticket. The cold read rated this cost as Major.
   - Affects: CLI-006, CLI-010.

3. **What does a line of `ticketdesk overdue` show?** Is it the same line that `list`
   prints, or does it also show the due time or how late the ticket is?
   - Assumption: it is the same line that `list` prints for the ticket. No command shows
     the due time. The order of `overdue` is the only place the due time has an effect.
   - Cost of the assumption: the output of `overdue` does not show why its tickets are in
     that order. The cold read rated this cost as Major.
   - Affects: CLI-010, the non-goals.

4. **Is this a display feature only?** Do agents also expect an alert, a record in the log,
   or a report of tickets that were closed late?
   - Assumption: display only. Nothing is written to the log, nothing is sent, and no
     history of lateness is kept.
   - Affects: TKT-017, the non-goals.

## Non-blocking questions

These do not change the shape of the spec. Each one is in the spec as a `TODO:` under
"Open questions for overdue tickets" in `docs/product-specs/tickets.md`.

5. **The exact due instant.** Is a ticket overdue at the due time itself, or only after it?
   - Assumption: only after it. At the exact due time the ticket is not overdue yet.
   - Affects: TKT-014.

6. **Equal due times.** When two overdue tickets have the same due time, which comes first
   in `ticketdesk overdue`?
   - Assumption: the lower ID comes first.
   - Affects: TKT-019.

7. **No overdue tickets.** Does `ticketdesk overdue` signal an empty result, for example
   with a message or a non-zero exit code?
   - Assumption: no. It prints nothing and exits with code 0, as `list` does with no
     tickets.
   - Affects: CLI-010.

8. **A corrupt log.** `ticketdesk list` on a corrupt log exits with code 1 and a Python
   traceback today. That is the open TODO under CLI-007. Should `overdue` wait for that
   decision?
   - Assumption: no. `overdue` reports a log that cannot be read with the same error
     message and exit code as `list`, whatever CLI-007 becomes.
   - Affects: CLI-012.

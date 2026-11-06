# Questions for the overdue tickets spec

Nobody was available to answer during this run, so each question carries the assumption
the spec proceeds on. The spec lists the same assumptions under "Open questions" in
`docs/product-specs/tickets.md`. Written on 2026-11-05.

## Asked before drafting

These three answers move the boundary of the feature. The skill asks them in one batch and
waits. This run could not wait, so it proceeds on the assumptions.

1. **Where does `OVERDUE` show in a `list` line?**
   Assumption: it takes the place of the state, in the same 8-character column (CLI-006).
   Cost of the assumption: `list` no longer shows whether an overdue ticket is `open` or
   `assigned`. A script that reads the state column meets a new value.
   Alternative: keep the state and add a separate `OVERDUE` marker to the line.
2. **Can a closed ticket be overdue?**
   Assumption: no. A `closed` ticket is never overdue, also when it was closed after its
   due time (TKT-014). The product keeps no record that a ticket was late.
   Alternative: mark late closures, which is a reporting feature of its own.
3. **What does "oldest due first" mean?**
   Assumption: the earliest due time first, with ties broken by ID ascending (TKT-016).
   A `P1` ticket created today can then come before a `P3` ticket created three days ago.
   Alternative: the earliest creation time first.

## Open, carried in the spec

4. **Is a ticket overdue at its exact due time?**
   Assumption: no. It is overdue only when the current time is later than the due time
   (TKT-014). The request says tickets that "pass" their due time.
5. **What does a line of `ticketdesk overdue` show?**
   Assumption: the same line that `list` prints for that ticket (CLI-010). It shows no due
   time, no lateness, and no assignee.
6. **Should `ticketdesk overdue` signal overdue tickets through its exit code?**
   Assumption: no. It exits with code 0 whether or not it prints tickets (CLI-010, CLI-008).
7. **Should tickets in existing logs become overdue?**
   Assumption: yes, with no cutoff date (TKT-014). On the first run after the release,
   every unfinished ticket past its due time shows as `OVERDUE`.
8. **Does assigning a ticket change when it is overdue?**
   Assumption: no. The due time stays as in TKT-005, and an `assigned` ticket becomes
   overdue like an `open` one. Business hours and due time extensions are non-goals.
9. **How does `ticketdesk overdue` report a corrupt log?**
   Not assumed. The open TODO under CLI-007 already asks this for every command. Today a
   corrupt line gives a Python traceback with exit code 1, and CLI-007 says `error:` with
   exit code 2. The new command inherits that open conflict. This spec does not settle it.

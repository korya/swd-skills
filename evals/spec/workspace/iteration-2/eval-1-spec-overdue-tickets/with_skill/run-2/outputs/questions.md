# Questions for the overdue tickets spec

Nobody was available to answer during this run. Each question states the assumption the
spec uses. The spec marks each assumption with a `TODO` line under the criterion it shapes.

## Blocking: these change the shape of the spec

Please answer these three before anyone plans against the spec.

1. **How does `list` show an overdue ticket?** The request says overdue tickets "show as
   OVERDUE".
   - Option A: `OVERDUE` replaces the state word, as in `#1 [P1] OVERDUE  Printer on fire`.
     The line keeps its column layout. The line no longer shows if the ticket is `open` or
     `assigned`. Scripts that read the state column see a new value.
   - Option B: the line keeps the state and adds a marker, as in
     `#1 [P1] assigned OVERDUE Printer on fire`. The line keeps all facts but changes its
     layout for every reader.
   - Assumption: Option A, the literal reading. See CLI-010.
2. **Is a ticket that was closed after its due time overdue?**
   - Assumption: no. Only `open` and `assigned` tickets can be overdue. A record of late
     closes is a non-goal. See TKT-014.
3. **What does a line of `ticketdesk overdue` show?** Every ticket in that output is
   overdue, so `OVERDUE` in each line tells the agent nothing new. The real state, `open`
   or `assigned`, would tell the agent who owns the work.
   - Assumption: the line is the same as the line of that ticket in `list`, so a line means
     one thing in both commands. See CLI-011.

## Not blocking: the spec proceeds on these

4. **Boundary.** A ticket at exactly its due time is not overdue. It becomes overdue when
   the time the command runs is later than the due time. See TKT-014.
5. **Tie order.** Overdue tickets with the same due time are sorted by ID ascending. See
   TKT-016.
6. **Empty output.** With no overdue tickets, or no log file, `overdue` prints nothing and
   exits with code 0, as `list` does. See CLI-011.
7. **How late a ticket is.** The spec does not show how long ago a ticket became due. Is
   that wanted in `overdue`, for example `3h late`?
8. **Filters.** `overdue` takes no arguments, so it has no filter by assignee or priority.
   See CLI-012. Is a filter wanted later?
9. **Corrupt log.** `overdue` inherits the open conflict under CLI-007. A corrupt line
   escapes as a traceback today. The fix chosen for CLI-007 applies to `overdue` too.
10. **Testing with time.** A black-box test needs tickets with a due time in the past. The
    CLI has no option to set the creation time or the current time. A tester can write a
    log file with old `at` values, because the log is a product surface per `event-log.md`.
    Is that acceptable, or does the team want a supported way to set the time?

## Contract changes to existing criteria

These edits change existing criteria in place. Please confirm each one.

- **CLI-001** lists five subcommands instead of four.
- **CLI-006** points to CLI-010 for overdue tickets. The state column of `list` no longer
  shows the state for those tickets.
- **LOG-001** says that `overdue`, like `list`, appends nothing.

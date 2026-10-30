# Questions for the overdue-tickets spec

Nobody was available to answer these during the run. Each question names the assumption the
draft spec proceeds on. The spec marks the shape-changing ones with a TODO next to the item.

## Blocking: these change the shape of the spec

1. **Is overdue a new state, or a marker next to the state?** TKT-001 allows only three
   states: `open`, `assigned`, `closed`. A fourth state would change that spec and lose the
   open or assigned information on the line.
   - Assumption: overdue is a derived condition, not a state. The ticket keeps its state.
     See TKT-014, TKT-015, and the TODO under CLI-006.

2. **Where does `OVERDUE` appear on a `list` line?** The request says tickets "show as
   OVERDUE" but not where. Scripts may parse the current line format.
   - Assumption: `OVERDUE` goes between the padded state and the title. Lines for tickets
     that are not overdue stay exactly as they are today. See CLI-006.

3. **Can a closed ticket be overdue?** A ticket closed after its due time missed its target.
   Agents may want to see that, or may want closed tickets to drop out.
   - Assumption: a closed ticket is never overdue, even one closed late. See TKT-014.

## Non-blocking: the draft proceeds on these

4. **What does `ticketdesk overdue` print per ticket?** It could print the `list` line, or
   add the due time or the time past due.
   - Assumption: the same line as `list` for an overdue ticket, `OVERDUE` marker included.
     See CLI-010.

5. **Is the boundary strict?** At exactly the due time, a ticket is either due or overdue.
   - Assumption: overdue only when the current time is later than the due time. See TKT-014.

6. **How are ties in due time ordered?** Two tickets of the same priority created in the
   same second have the same due time.
   - Assumption: by ticket ID ascending. See TKT-016.

7. **Should `ticketdesk overdue` exit non-zero when overdue tickets exist?** A non-zero code
   lets a cron job or a shell prompt react to overdue work.
   - Assumption: no. It exits with code 0 on success, per CLI-008, whether or not it prints
     a line. See CLI-010.

8. **Should `ticketdesk overdue` take filters**, such as by assignee or by priority?
   - Assumption: no. It takes no arguments beyond the global `--log`. Filters are a
     non-goal for now.

9. **Should the CLI accept a reference time**, such as a `--now` option, to evaluate
   overdue at another time? It would help testing and "what will be overdue tomorrow".
   - Assumption: no. The current time is the clock of the machine. Testers can write a log
     with past `at` values, since the log is a product surface per LOG-003 and LOG-004.

## Conflict surfaced, not resolved

10. **CLI-007 TODO.** A corrupt log line escapes as a Python traceback with exit code 1
    today, against CLI-007. The new `overdue` command reads the log the same way as `list`.
    - Assumption: `overdue` behaves exactly as `list` on a corrupt log, and follows
      whichever resolution the CLI-007 TODO gets. The spec does not decide that TODO.

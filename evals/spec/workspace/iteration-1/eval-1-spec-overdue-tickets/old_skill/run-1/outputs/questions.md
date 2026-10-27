# Open questions for the overdue-tickets spec

Nobody was available to answer during this run. Each question states the assumption the
draft proceeds on. Questions 1 to 3 change the shape of the contract; the rest are
detail. Sign-off resolves each into a criterion, a non-goal, or a deletion, and the
`Open questions` blocks at the end of `docs/product-specs/tickets.md` and `cli.md` go away.

## Shape-changing

1. **Can a `closed` ticket be overdue?** Its due time still exists after closing, so a
   literal reading of "passes its due time" would mark closed tickets too.
   **Assumption:** no. Only `open` and `assigned` tickets can be overdue; closing ends it
   at once (TKT-016). Agents want a work queue, and closed tickets are not work.

2. **Is a ticket overdue at exactly its due time, or only after it?**
   **Assumption:** only after. "Passes its due time" reads as strictly later (TKT-014B).

3. **Where does `OVERDUE` go in the `ticketdesk list` line, and do non-overdue lines
   change?** Options: (a) between state and title on overdue lines only, non-overdue
   lines unchanged; (b) a fixed-width marker column on every line, blank when not
   overdue, so titles stay aligned; (c) at the end of the line after the title.
   **Assumption:** (a). It is the smallest change to the existing contract (CLI-006 holds
   byte for byte for non-overdue lines) and the word is scannable near the left. The cost
   is that titles on overdue lines start 8 characters later than on other lines.

## Detail

4. **Should `ticketdesk overdue` show the due time, or how late the ticket is?** "Oldest
   due first" suggests agents care about the due time, but printing it means choosing a
   human-readable time format and a timezone, which nothing in the product does today.
   **Assumption:** no. The line is the same as the `list` line (CLI-011). Listed as a
   non-goal; easy to add later as a new criterion.

5. **Exit code of `ticketdesk overdue` when overdue tickets exist.** Some tools exit
   non-zero so a script can ask "anything overdue?" without parsing output.
   **Assumption:** 0, per CLI-008. Non-zero would make it the only successful command
   that fails, and `grep -q` on the output does the same job.

6. **Order of two tickets with the same due time.** Same priority and same creation
   second gives equal due times. **Assumption:** ID ascending, matching TKT-013.

7. **Should the `assign` and `close` output lines also carry `OVERDUE`?**
   **Assumption:** no. Only `list` and `overdue` show it. Non-goal.

8. **New command, or a `--overdue` filter on `list`?** The request asks for a command, so
   the spec specifies a command. Flagging it anyway: a filter on `list` would avoid a
   fifth subcommand, and the two are not exclusive. **Assumption:** the command only.

9. **Should the log record that a ticket became overdue?** An event would allow reports
   like "how many tickets went overdue last month". **Assumption:** no. Overdue is derived
   from the due time and the current time, nothing is appended (TKT-017, LOG-001), and
   the event kinds of LOG-002 are unchanged. A report feature can derive it from `at`
   and the priority later.

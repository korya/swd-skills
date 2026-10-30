# Open questions: overdue tickets

Nobody was available to answer these during the run. Each question states the assumption
that the draft spec uses. The spec marks each assumption with a `TODO:` line under the
criterion it affects.

## Questions that change the shape of the spec

1. **Does `OVERDUE` replace the state or join it?** The request says an overdue ticket
   "shows as OVERDUE" in `ticketdesk list`. A replacement hides whether the ticket is
   `open` or `assigned`.
   - Assumption: the marker joins the state. The line becomes
     `#<id> [<priority>] <state> OVERDUE <title>`. Affects CLI-006 and CLI-010.
2. **Can a closed ticket be overdue?** A ticket closed after its due time missed its
   target, but nobody needs to act on it any more.
   - Assumption: a closed ticket is never overdue. Late closures are a non-goal.
     Affects TKT-014.
3. **Does a script read the output of `ticketdesk list`?** CLI-010 inserts a word between
   the state and the title on overdue lines. A script that reads the title after the
   state column breaks.
   - Assumption: no script depends on the current line format. Lines of tickets that are
     not overdue stay unchanged.

## Questions the draft proceeds on

4. **Is a ticket overdue at its due time, or only after it?**
   - Assumption: only after it. At the due time exactly, the ticket is not overdue.
     Affects TKT-014.
5. **What does `ticketdesk overdue` print per ticket?** Agents may want the due time or
   how late the ticket is.
   - Assumption: the same line as `list` prints for an overdue ticket. No due time and no
     lateness. Affects CLI-011.
6. **Which ticket comes first when two have the same due time?**
   - Assumption: the lower ticket ID. Affects TKT-016.
7. **Does `ticketdesk overdue` signal overdue tickets through its exit code?** A cron job
   could use a non-zero code to alert someone.
   - Assumption: no. It exits with code 0 when it succeeds, per CLI-008. Affects CLI-011.
8. **Does the CLI-007 conflict extend to `overdue`?** A corrupt log line escapes as a
   Python traceback today, see the TODO under CLI-007.
   - Assumption: `overdue` behaves as `list` does, and the CLI-007 decision covers both.
     Affects CLI-012.

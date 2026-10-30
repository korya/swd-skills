# Questions for the overdue spec

Nobody was available to answer these during the run. Each question names the assumption
the spec uses. The spec marks each one with a TODO under the affected criterion.

## Questions that change the shape of the spec

These would normally go to the user as one batch before drafting.

1. **Does `OVERDUE` replace the state in `ticketdesk list`, or sit next to it?** The
   request says overdue tickets "show as OVERDUE". Assumption: `OVERDUE` is a mark after
   the state, and the state stays visible. Example: `#1 [P1] assigned OVERDUE Printer on fire`.
   Lines for tickets that are not overdue do not change. See CLI-010.
2. **Can a closed ticket be overdue?** A ticket closed after its due time missed its
   target. Assumption: a closed ticket is never overdue and carries no mark, late or not.
   See TKT-015.

## Questions the spec proceeds on

3. **Is a ticket overdue at exactly its due time?** Assumption: no. It becomes overdue
   only when the current time is later than the due time. See TKT-014.
4. **Does `ticketdesk overdue` signal overdue tickets through its exit code?** A script
   or cron job could alert on a non-zero code. Assumption: the command exits 0 whether or
   not overdue tickets exist. See CLI-011.
5. **Should `ticketdesk overdue` show more than the `list` line?** Agents might want the
   due time or how long a ticket has been overdue. Assumption: each line is the same line
   that `list` prints. See CLI-011.
6. **Does `ticketdesk overdue` need filters, such as by assignee or priority?**
   Assumption: no. The command takes no arguments, and the spec names filters as out of
   scope. See CLI-013.
7. **How should the repo mark a spec item that is specified but not built?** The repo has
   no status convention. Assumption: a dated status sentence in the intro of
   `tickets.md` and `cli.md`.

## Existing conflict this feature inherits

8. **The open TODO under CLI-007 also covers `ticketdesk overdue`.** A corrupt log line
   stops every operation per LOG-007. The CLI-007 TODO says that this failure escapes as
   a Python traceback with exit code 1, not as `error: <message>` with exit code 2. This
   spec does not settle that question for the new command either.

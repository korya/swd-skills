# Questions on the overdue tickets spec

Nobody was available during this run, so the spec proceeds on the assumption under each
question. The spec lives in `docs/product-specs/tickets.md` (section "Overdue tickets",
TKT-014 to TKT-017) and `docs/product-specs/cli.md` (CLI-001, CLI-006, CLI-010 to CLI-013).

## Blocking questions: an answer changes the shape of the spec

These are the questions the skill asks in one batch before drafting.

### Q1. What does the due time measure?

Is the due time of TKT-005 a target for closing the ticket? Or is it a target for the first
response, such as the first assignment?

- **Assumption:** it is a target for closing. Only closing stops a ticket from being
  overdue. Assigning changes nothing (TKT-014, TKT-016).
- **If the answer differs:** an assigned ticket would never be overdue. TKT-014 and TKT-016
  change, and the examples in CLI-006 and CLI-010 change with them.

### Q2. Does a ticket that was closed late show as overdue?

A ticket closed after its due time missed its target. Should `list` still show that?

- **Assumption:** no. A closed ticket is never overdue, however late it was closed
  (TKT-015). The marker tells an agent what needs work now. A report of late closes is a
  non-goal.
- **If the answer differs:** the spec needs a second marker or a rule for closed tickets,
  and `ticketdesk overdue` needs a decision on whether it lists them.

### Q3. How does `OVERDUE` show in a `list` line?

The request says tickets "show as OVERDUE". The line today is
`#<id> [<priority>] <state> <title>`. Three readings fit.

| Option | Line for an overdue open ticket | Cost |
|---|---|---|
| A. Word after the state (assumed) | `#3 [P1] open     OVERDUE Printer on fire` | A title that starts with `OVERDUE` reads like the marker. |
| B. Word replaces the state | `#3 [P1] OVERDUE  Printer on fire` | The agent cannot tell open from assigned. |
| C. Word at the start of the line | `OVERDUE #3 [P1] open     Printer on fire` | Lines no longer start in one column. No clash with titles. |

- **Assumption:** option A. The state stays visible, and the line of a ticket that is not
  overdue stays byte for byte as it is today (CLI-006).
- **If the answer differs:** only CLI-006 and the examples in CLI-010 change.

### Q4. What does `ticketdesk overdue` print for each ticket?

Should each line show the due time, or how late the ticket is?

- **Assumption:** no. Each line is the same line `ticketdesk list` prints for that ticket,
  `OVERDUE` word included (CLI-010). No command shows a due time today, and the request
  did not ask for one. Showing it is a non-goal.
- **If the answer differs:** CLI-010 gets a new line format. The spec then needs a rule for
  how a time or a duration prints, time zone included.

## Non-blocking questions: the spec states an assumption and continues

### Q5. Does "oldest due first" mean the earliest due time first?

- **Assumption:** yes. The overdue listing sorts by due time ascending, so the ticket that
  became due first comes first. It does not sort by creation time or by priority. Tickets
  with the same due time sort by ID ascending (TKT-017).

### Q6. Is a ticket overdue at the exact due time?

- **Assumption:** no. "Pass their due time" means the current time is later than the due
  time (TKT-014).
- **Limit:** a black-box test cannot hit the exact instant, because no option sets the
  current time (a non-goal). A test can cover a ticket due 1 second ago and one due later.

### Q7. Which exit code does `ticketdesk overdue` return when it prints tickets?

Some tools return a non-zero code when they find something, so a script can react.

- **Assumption:** code 0, whether it prints tickets or not, per CLI-008 (CLI-010, CLI-011).

### Q8. How does `ticketdesk overdue` report a corrupt log?

This is an existing open conflict, not a new one. The TODO under CLI-007 says a corrupt
log line escapes today as a Python traceback with exit code 1. I confirmed it on `list`
during this run. The new command inherits the question.

- **Assumption:** CLI-013 fixes only what holds under either answer. The command prints no
  ticket line to stdout and exits with a non-zero code. The message and the exact code
  follow the answer to the TODO under CLI-007.

### Q9. Is amending `tickets.md` and `cli.md` the right home, rather than a new `overdue.md`?

- **Assumption:** amend. Overdue is a ticket rule built on TKT-005, and its output is part
  of the command surface. `docs/README.md` says to update the existing doc instead of
  fragmenting. The cost is that goals, non-goals, and open questions sit in a section of
  `tickets.md`, a shape the other sections of that file do not have.

## Sign-off

The spec is marked "specified but not built" with the date 2026-11-05 in both files and in
`AGENTS.md`. Nothing downstream should plan or build against it until the user signs it off.

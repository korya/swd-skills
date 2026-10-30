# Questions for the overdue-tickets spec

Nobody was available to answer during this run. The spec proceeds on the assumption under
each question. Spec files: `docs/product-specs/tickets.md` (TKT-014 to TKT-016) and
`docs/product-specs/cli.md` (CLI-001 and CLI-006 amended, CLI-010 to CLI-012 new).

## Blocking: these change the shape of the spec

The skill asks these as one batch before drafting, then waits.

1. **What does "show as OVERDUE" mean in `ticketdesk list`?** Option A: add an `OVERDUE`
   mark next to the state, as in `#1 [P1] assigned OVERDUE Printer on fire`. Option B:
   replace the state with `OVERDUE`, as in `#1 [P1] OVERDUE  Printer on fire`. Option B
   hides whether the ticket is `open` or `assigned`. It also turns overdue into a fourth
   value in the state column, which conflicts with TKT-001.
   **Assumption:** option A. See CLI-006.
2. **Does anything parse the output of `ticketdesk list`?** The `OVERDUE` mark changes
   the line format that CLI-006 promised. A script that splits a line on spaces and reads
   the title from a fixed position breaks.
   **Assumption:** no script depends on the line format. If one does, a trailing mark or a
   separate option is safer.
3. **What exit code does `ticketdesk overdue` give when overdue tickets exist?** A cron job
   or a monitor could use a nonzero code as an alarm.
   **Assumption:** exit code 0 whenever the command succeeds, per CLI-008. See CLI-010.

## Not blocking: marked assumptions in the draft

4. **Exact due time.** Is a ticket overdue at its exact due time, or only after it?
   **Assumption:** only after it. See TKT-014.
5. **Tickets closed late.** Is a ticket that was closed after its due time ever shown as
   overdue, or recorded as a missed target?
   **Assumption:** no. A `closed` ticket is never overdue. Breach history is a non-goal.
6. **Clock for the due time.** Do the hours in TKT-005 count calendar hours or business
   hours?
   **Assumption:** calendar hours, as TKT-005 does today. Business hours are a non-goal.
7. **Detail in the overdue list.** Should `ticketdesk overdue` show the due time, or how
   long ago it passed?
   **Assumption:** no. It prints the same line as `list`, with the `OVERDUE` mark.
8. **Ties in the overdue order.** The request says "oldest due first" and does not order
   tickets with the same due time.
   **Assumption:** ID ascending. See TKT-016.

## Conflicts and proposals to confirm

9. **CLI-012 depends on the open TODO under CLI-007.** A corrupt log makes every command
   fail with a traceback and exit code 1 today. CLI-012 only requires `overdue` to fail
   the same way as `list`. It does not choose the exit code. Resolving the TODO decides it.
10. **Status lines for behavior that is not built.** The repo specs describe the product
    as it is. The repo has no convention for proposed behavior. The draft adds a line
    `Status: proposed on 2026-10-29, not implemented.` to each new or changed item.
    Remove each line when the code lands, or choose another convention.
11. **Proposed invariant, not added.** "A command that only reads tickets never writes the
    log." LOG-001 says this for `list`, and CLI-011 says it for `overdue`. A global
    invariant `INV-006` would cover any future read command. The draft leaves
    `invariants.md` unchanged until you confirm.
12. **Test limit for the exact due time.** A black-box test sets times through the `at`
    field of a written log. It cannot hit the exact current second. The boundary in TKT-014
    is testable through the service with a fake clock, not through the binary.

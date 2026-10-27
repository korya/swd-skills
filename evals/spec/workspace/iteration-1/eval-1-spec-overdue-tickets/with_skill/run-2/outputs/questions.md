# Questions before the overdue spec is signed off

These are the questions `/spec` would have asked in one batch. Nobody was available, so
each one carries the assumption the draft proceeds on. The same questions sit under
`Open questions` in `docs/product-specs/tickets.md` and `docs/product-specs/cli.md`.
Sign-off resolves each into a criterion, a non-goal, or a deletion.

## Q1. Can a `closed` ticket be overdue?

Assumption: no. Only `open` and `assigned` tickets can be overdue (TKT-014, TKT-015).

Why: the request comes from agents who want to see what needs attention. A closed ticket
needs none. If the answer is yes, `ticketdesk overdue` becomes a breach report that also
lists late closures, and TKT-015 flips.

## Q2. Where does `OVERDUE` go in the `ticketdesk list` line?

Assumption: at the end of the line, after the title, as ` OVERDUE` (CLI-010). Lines of
tickets that are not overdue stay exactly as CLI-006 prints them today.

Why: the state column cannot hold it. Replacing `open` or `assigned` with `OVERDUE` loses
the state and contradicts TKT-001. A new column before the title would shift or misalign
every line. A trailing marker changes nothing for existing readers of the output.

## Q3. Does `ticketdesk overdue` print the same line as `list`, or add the due time?

Assumption: the same line as `list` prints for that ticket, marker included (CLI-011).

Why: one output format to read and parse. Showing the due time or how late a ticket is
would be a new column to design, and the request did not ask for it.

## Q4. Should `ticketdesk overdue` exit non-zero when overdue tickets exist?

Assumption: no. It exits 0 whenever it succeeds, as CLI-008 says.

Why: a non-zero exit would make the command usable as a cron alert, but that is a second
feature. It can be added later without changing the output.

## Q5. Is a ticket overdue at exactly its due time?

Assumption: no. Overdue means the current time is later than the due time (TKT-014).

## Q6. In `ticketdesk overdue`, how are two tickets with the same due time ordered?

Assumption: by ID ascending (TKT-016). Two tickets of the same priority created in the
same second share a due time, so the tie needs a rule.

## Q7. Do you want a way to set the current time, such as a `--now` option?

Assumption: no. The time is the clock of the machine at the moment the command runs.

Why: tests do not need it. The log file is a product surface that users may write, so a
black-box test can write a log whose `at` timestamps lie in the past.

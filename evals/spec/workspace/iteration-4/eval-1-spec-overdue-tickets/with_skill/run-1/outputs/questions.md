# Questions for the overdue-tickets spec

Nobody was available to answer during this run. The draft spec proceeds on the assumption
under each question. The spec is `docs/product-specs/overdue.md`, with the command surface
in CLI-010 and CLI-011 of `docs/product-specs/cli.md`.

## Blocking round: these change the shape of the spec

The skill asks these as one batch and waits. I proceeded on the assumptions instead.

1. **Does `OVERDUE` replace the state word in `ticketdesk list`, or appear next to it?**
   - Assumption: it replaces the state word, padded to 8 characters like a state.
   - Why it matters: the line then no longer shows whether an overdue ticket is `open` or
     `assigned`. Showing both changes the line format of CLI-006 for every line.
2. **Is a closed ticket ever overdue?**
   - Assumption: no. A `closed` ticket is never overdue, even when it was closed late.
   - Why it matters: "late closures" would be a reporting feature with a different user.
3. **What does a line of `ticketdesk overdue` show?**
   - Assumption: the same line as `ticketdesk list`, with no due time and no lateness.
   - Why it matters: agents may need the due time or "late by 3h" to triage. That adds a
     new output format.

## Open questions: the draft carries these as marked assumptions

4. **Is a ticket overdue at its due time exactly?**
   - Assumption: no. It is overdue only when the current time is later than the due time.
5. **How are two overdue tickets with the same due time ordered?**
   - Assumption: by ID ascending.
6. **Do scripts or other tools parse the state column of `ticketdesk list`?**
   - Assumption: no consumer exists. Nothing in the repo reads that output. A script that
     looks for `open` or `assigned` would miss overdue tickets after this change.

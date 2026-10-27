# Open questions for the overdue-tickets spec

Nobody was available to answer during this run. Each question states the assumption the
draft proceeds on. The draft marks the assumption inline as `A<n>`. Sign-off resolves each
one into a criterion, a non-goal, or a deletion, and the `Open questions` blocks leave the
spec files.

## Shape-changing (would have been asked before drafting)

**Q1. Can a closed ticket be overdue?**
A ticket closed after its due time was late, but it no longer needs attention.
Assumption A1: no. Overdue applies to `open` and `assigned` tickets only; closing removes a
ticket from the overdue set at once. "Closed late" reporting is a non-goal. (TKT-015)

**Q2. What is "now"?**
Assumption A2: the time at which the command runs, the same clock that stamps events. No
`--as-of` option; agents want the current picture, not a report. (TKT-014, TKT-016)

**Q3. Where does the marker go on a `list` line?**
Today a line is `#<id> [<priority>] <state> <title>`. Options: (a) `OVERDUE` between the
state and the title, (b) ` OVERDUE` appended after the title, (c) `[OVERDUE]` or similar.
Assumption A3: (a). The eye scans the state column for status, and the first three fields
stay where they are. Cost: the title column shifts right on overdue lines. (CLI-010)

**Q4. Does `ticketdesk overdue` print the same line format as `list`?**
Assumption A4: yes, including the `OVERDUE` marker, so every line of `overdue` appears
verbatim in `list` run at the same moment. One format to learn and to grep. The
alternative, a richer line showing the due time or how late the ticket is, is a non-goal
until asked for. (CLI-011)

## Non-structural (proceeding on an assumption)

**Q5. Boundary: is a ticket overdue at exactly its due time?**
Assumption A5: no. Overdue means the current time is strictly later than the due time.
(TKT-014)

**Q6. Tie-break when two overdue tickets share a due time.**
Same priority created in the same second gives the same due time. Assumption A6: ID
ascending, matching TKT-013. (TKT-017)

**Q7. Exit code of `overdue` when nothing is overdue.**
Scripts sometimes want a non-zero code for "none", like `grep`. Assumption A7: exit 0 and
print nothing, consistent with CLI-006 and CLI-008. (CLI-012)

**Q8. Should `create`, `assign`, and `close` output lines show `OVERDUE` too?**
Assumption A8: no. Only `list` and `overdue` change. Listed as a non-goal.

## Notes surfaced for the reviewer, not questions

- No invariant is contradicted. INV-001 still holds: nothing stores overdue state. But
  this is the first user-visible output that depends on the wall clock at read time
  rather than on the log alone. LOG-009 (replay is deterministic) is untouched because
  due times, not overdue flags, come out of replay. The draft records "overdue is derived,
  never recorded" as a feature-local contract in `tickets.md` rather than a new `INV`,
  since only the ticket feature enforces it. Promote it if you want it on the floor.
- The repo's spec files carry no non-goals section. The draft adds a short one to the
  overdue paragraph of `tickets.md`, since the boundary is part of the contract. Drop it
  if you prefer the files to stay criteria-only.
- `AGENTS.md` and `docs/product-specs/README.md` index rows were updated to mention
  overdue, per `docs/README.md` ("when to update what"). The AGENTS.md "Planned" line
  now points at the draft.

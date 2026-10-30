# Questions for the overdue spec

Nobody could answer during this run. Each question names the assumption the spec proceeds
on and the spec item that carries it as a TODO. Questions 1 to 3 shape the spec. Questions 4
to 6 do not.

## Questions that shape the spec

1. **Is overdue a fourth ticket state, or a label derived at the time a command runs?**
   Assumption: a derived label. It is never written to the log and TKT-001 keeps three
   states. A stored state would break LOG-009, because replay would then depend on the
   clock. Carried in `tickets.md` (overview and TKT-014).
2. **Can a closed ticket be overdue?** Assumption: no. A `closed` ticket is never overdue,
   even when it closed after its due time. A report of tickets closed late is a non-goal.
   Carried in TKT-014.
3. **In `ticketdesk list`, does `OVERDUE` replace the state, or appear next to it?**
   Assumption: it replaces the state, as the request says "show as OVERDUE". The cost is
   that the line no longer shows `open` or `assigned` for an overdue ticket. Next to the
   state keeps that information but changes the line format for every script that reads
   it. Carried in CLI-010.

## Questions that do not shape the spec

4. **Is a ticket overdue at the exact second of its due time?** Assumption: no. It becomes
   overdue only after its due time, as "pass their due time" says. Carried in TKT-014.
5. **Which order applies when two overdue tickets have the same due time?** Assumption: ID
   ascending. Carried in TKT-015.
6. **Should `ticketdesk overdue` exit with a nonzero code when overdue tickets exist?**
   Assumption: no. It exits with code 0, like `list`, per CLI-008. Carried in CLI-011.

## Note for planning, not for the spec

The overdue label needs the current time when a command runs. Today only the store reads
the clock, to stamp events per INV-005. INV-005 covers event timestamps only, so this is
not a conflict. The plan still decides where the current time comes from and how tests
control it.

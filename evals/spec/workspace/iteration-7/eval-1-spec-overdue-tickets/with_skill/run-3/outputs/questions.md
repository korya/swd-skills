# Questions for the overdue-tickets spec

Nobody could answer during this run on 2026-11-05. Each question below carries the
assumption the spec proceeds on. The spec is in `docs/product-specs/tickets.md` (TKT-014 to
TKT-017) and `docs/product-specs/cli.md` (CLI-001, CLI-006, CLI-010 to CLI-012).

## Questions that shape the spec

The skill asks these in one batched round and waits. An answer that differs from the
assumption changes the structure of the spec, not one line of it.

1. **Can a closed ticket be overdue?** The request can mean a worklist of tickets that
   need action now. It can also mean a report of every ticket that missed its target.
   - Assumption: a worklist. Only an `open` or `assigned` ticket can be overdue. A ticket
     closed after its due time is never shown as overdue.
   - In the spec: TKT-014, TKT-015, and the non-goal "no lateness history".
   - If the answer differs: `overdue` also lists closed tickets, lateness is judged at the
     close time, and the non-goal goes.

2. **Is OVERDUE a fourth ticket state, or a marker worked out from the due time and the
   clock?**
   - Assumption: a marker. The states of TKT-001 stay `open`, `assigned`, `closed`. No
     event records that a ticket became overdue.
   - Why: nobody runs a command at the moment a due time passes, so no event can record
     it (LOG-001). A state that the time decides conflicts with INV-001, which derives
     state from the log alone.
   - In the spec: TKT-016 and the intro paragraph of `tickets.md`.
   - If the answer differs: TKT-001 and the forward-only rule change in either form. A
     state that an event records also changes LOG-002 and LOG-003. A state that the time
     decides also changes INV-001 and LOG-009.

## Questions the spec carries as marked assumptions

Each one is a `TODO:` paragraph under the item it concerns. The spec stays valid in shape
whichever way the answer goes.

3. **Does `OVERDUE` join the state in `list`, or replace it?** And where on the line does
   it go?
   - Assumption: it joins the state and sits between the priority and the state. The line
     is `#<id> [<priority>] OVERDUE <state> <title>`. Lines of tickets that are not
     overdue do not change.
   - Why: an agent still sees whether an overdue ticket has an assignee. A title can
     never read as the marker, because no state is named `OVERDUE`.
   - Known cost: the state and the title start 8 characters later on an overdue line.
   - Alternative A: `OVERDUE` sits between the state and the title. Then a ticket that is
     not overdue, with a title that starts with `OVERDUE `, prints the same line. The
     first draft assumed this option. The cold read found the clash, and the spec moved.
   - Alternative B: `OVERDUE` replaces the state. It fits the 8-character state column,
     and the line no longer shows `open` or `assigned`.
   - In the spec: CLI-010, with the three options in a table.

4. **Should any output show the due time, or how late a ticket is?**
   - Assumption: no. `overdue` prints the same line that `list` prints for the ticket.
   - In the spec: CLI-011 and the non-goals.

5. **What is the exit code of `ticketdesk overdue` when no ticket is overdue?**
   - Assumption: 0, with no output, like `list` on an empty log (CLI-006, CLI-008).
   - Alternative: a non-zero code, so a script can branch on "nothing overdue".
   - In the spec: CLI-011.

6. **Is a ticket overdue at the exact due time?**
   - Assumption: no. "Pass their due time" is read as strictly later than the due time.
   - In the spec: TKT-014.

7. **What is the order of two overdue tickets with the same due time?**
   - Assumption: ID ascending, as in TKT-013. "Oldest due first" is read as earliest due
     time first.
   - In the spec: TKT-017.

8. **Must existing `list` output stay unchanged for tickets that are not overdue?**
   - Assumption: yes. The request does not say so. The spec adds it as a constraint so
     that scripts reading today's lines keep working.
   - In the spec: goal 3 and CLI-010.

## An existing conflict that touches this feature

9. **How does the CLI report a corrupt log?** The open TODO under CLI-007 already asks
   this for the existing commands. `list` and the new `overdue` command read the log, so
   both meet the same failure.
   - Assumption: this spec does not settle it. CLI-011 points at the TODO under CLI-007.
   - Question: do you want CLI-007 settled before `overdue` is built?

## A repo rule that this spec stretches

10. **May the spec files describe behavior that is not built?** `docs/product-specs/README.md`
    calls the specs the description of "what ticketdesk does". `docs/README.md` says not
    to write a doc "for a design exploration that has not landed". The cold read raised
    both.
    - Assumption: yes, because the request asks for the spec in the repo's docs before
      the build. Every unbuilt part carries a dated "proposed, not built" note.
    - Alternative: keep the proposal out of `docs/product-specs/` until it ships.

## Sign-off

Questions 1, 2, and 3 change which tickets are listed or what a line looks like. A
sign-off without those three answers accepts the assumptions as written.

# Questions on the overdue tickets spec

Nobody was available to answer during this run. Each question states the assumption the
draft proceeds on and the spec items that rest on it. The same questions are listed at the
end of `docs/product-specs/tickets.md` in the repo.

## Questions that change the shape of the spec

These would have been asked as one batched round before drafting.

1. **Is a ticket that was closed after its due time ever shown as OVERDUE?**
   Assumption: no. Only `open` and `assigned` tickets can be overdue. Closing an overdue
   ticket ends the condition. A report of tickets closed late is a non-goal.
   Rests on it: TKT-014, TKT-015, CLI-010, CLI-011.

2. **Does OVERDUE replace the state in the `list` line, or stand beside it?**
   Assumption: beside it. The line of an overdue ticket is
   `#<id> [<priority>] <state> OVERDUE <title>`. The line of any other ticket does not
   change. Two reasons. Replacing the state hides whether anyone holds the ticket, which is
   what an agent needs when triaging late tickets. Making OVERDUE a real state would
   contradict TKT-001 (three states), the forward-only contract in `tickets.md`, and
   LOG-009 (the same log always yields the same states), because overdue depends on the
   current time and not on an event.
   Rests on it: CLI-010, CLI-011, and the non-goal "no new ticket state".

3. **Should `ticketdesk overdue` show more than `list` shows, such as the assignee, the
   due time, or how late the ticket is?**
   Assumption: no. Each line of `overdue` is the line `list` prints for that ticket.
   Showing the due time or the lateness is a non-goal.
   Rests on it: CLI-011.

## Questions that do not block the shape

The draft proceeds on a marked assumption for each.

4. **Is a ticket overdue at exactly its due time?**
   Assumption: no. "Pass their due time" is read as strictly later than the due time.
   Rests on it: TKT-014.

5. **How are two overdue tickets with the same due time ordered?**
   Assumption: by ID ascending.
   Rests on it: TKT-017.

6. **Does "oldest due first" mean earliest due time first, or earliest created first?**
   Assumption: earliest due time first. The two differ across priorities. A `P3` ticket
   created 80 hours ago was due 8 hours ago. A `P1` ticket created 10 hours ago was due 6
   hours ago. The `P3` ticket comes first.
   Rests on it: TKT-017.

7. **Is it acceptable that a title starting with the word `OVERDUE` reads like the marker?**
   A ticket that is not overdue and has the title `OVERDUE invoice from Acme` prints a line
   that looks like a marked line with the title `invoice from Acme`. The title is free
   text, so any marker position next to it has this weakness.
   Assumption: accepted for now. The alternative is a marker in a position a title cannot
   reach, which changes the line format of CLI-010.
   Rests on it: CLI-010.

8. **What does `ticketdesk overdue` do when no ticket is overdue?**
   Assumption: it prints nothing and exits with code 0, as `list` does with no tickets.
   A script that wants "any overdue?" as an exit code would need a different answer.
   Rests on it: CLI-012.

9. **The TODO under CLI-007 is still open.**
   A corrupt log line escapes today as a Python traceback with exit code 1, and CLI-007
   has not decided whether that is correct. The draft does not decide it either. CLI-014
   says `overdue` fails the same way `list` does and leaves the exact form to that TODO.
   Rests on it: CLI-014.

## Process notes for sign-off

- The repo's specs describe what ticketdesk does today. The new items describe a feature
  that is not built. A `TODO:` note in `tickets.md` and in `cli.md` says so. CLI-001 and
  CLI-006 are amended in place and carry the same caveat.
- `docs/README.md` requires user confirmation for every spec change. Nothing is committed.
- One testability caveat. The exact-instant rule in TKT-014 cannot be hit through the
  command line, because a test cannot pin the machine clock to one instant. A test through
  the service with a fake clock can. Every other item is testable through the command with
  a prepared log file whose `created` events carry an `at` in the past.
- The amendment touches four files. `tickets.md` gets TKT-014 to TKT-018, the goals, the
  non-goals, and the open questions. `cli.md` gets CLI-010 to CLI-014 and edits to CLI-001
  and CLI-006. `docs/product-specs/README.md` and `AGENTS.md` each get one index line.

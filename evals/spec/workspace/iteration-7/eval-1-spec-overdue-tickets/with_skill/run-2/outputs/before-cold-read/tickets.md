# Tickets

A ticket is one support request. An agent creates it with a title and a priority, assigns
it to a person, and closes it with a resolution note. The priority sets the due time
through a service-level target. Every change is one event in the log, see
[`event-log.md`](event-log.md). A ticket that passes its due time before it is closed is
overdue, see [Overdue tickets](#overdue-tickets).

A ticket moves forward only. It goes from `open` to `assigned` to `closed`, or straight
from `open` to `closed`. Nothing reopens a closed ticket.

Prefix: `TKT`.

---

### TKT-001: Ticket states

The state of a ticket is one of: `open`, `assigned`, `closed`. A new ticket starts as
`open`.

### TKT-002: A title is required

Creating a ticket with an empty title, or a title of only whitespace, fails with the error
`title is required`. No ticket is created and the ticket list is unchanged.

### TKT-003: Priority values

The priority of a ticket is one of: `P1`, `P2`, `P3`. Creating a ticket with any other
priority fails with an error that names the rejected value and the allowed values. No
ticket is created.

### TKT-004: Ticket IDs

The first ticket in a log gets ID `1`. Each later ticket gets the highest existing ID plus
one, so IDs rise by one and are never reused, see INV-003.

### TKT-005: Due time by priority

The due time of a ticket is its creation time plus the hours for its priority.

| Priority | Hours until due |
|----------|-----------------|
| `P1` | 4 |
| `P2` | 24 |
| `P3` | 72 |

### TKT-006: Assigning a ticket

Assigning an `open` or `assigned` ticket to a named person sets the assignee to that name
and the state to `assigned`. Assigning an `assigned` ticket again replaces the previous
assignee.

### TKT-007: An assignee is required

Assigning with an empty or whitespace-only assignee fails with the error
`assignee is required`. The ticket is unchanged.

### TKT-008: Closed tickets cannot be assigned

Assigning a `closed` ticket fails with the error `ticket <id> is closed`. The ticket is
unchanged.

### TKT-009: Closing a ticket

Closing an `open` or `assigned` ticket with a resolution note sets the state to `closed`
and records the note. The assignee, if any, is kept.

### TKT-010: Resolution note minimum length

A resolution note shorter than 10 characters, after trimming surrounding whitespace, is
rejected with the error `resolution note must be at least 10 characters`. The ticket stays
in its previous state.

### TKT-011: Closing twice

Closing a `closed` ticket fails with the error `ticket <id> is already closed`. The
recorded resolution is unchanged.

### TKT-012: Unknown ticket

Assigning or closing a ticket ID that does not exist fails with the error
`no ticket <id>`.

### TKT-013: Listing order

Listing returns every ticket, closed ones included, sorted by ID ascending.

---

## Overdue tickets

A support agent sees which tickets passed their due time, and can list only those tickets.
Today no command shows the due time, so a late ticket looks the same as a new one.

Status on 2026-11-05: proposed, not built, and not signed off. The status covers TKT-014 to
TKT-016 here, and CLI-001, CLI-006, CLI-010, and CLI-011 in [`cli.md`](cli.md). A line that
starts with `TODO` marks an assumption that the user did not confirm.

Goals:

- An agent who reads `ticketdesk list` can tell from each line whether the ticket is
  overdue.
- An agent gets the overdue tickets alone with one command, the earliest due time first.
- The line of a ticket that is not overdue stays as it is today.

Non-goals:

- No notification, reminder, or escalation when a ticket becomes overdue.
- No change to the due time rule of TKT-005. No business hours, no pause, and no due time
  set by hand.
- No record that a closed ticket was late. Nothing shows that a ticket was closed after its
  due time.
- No display of the due time, or of the time by which a ticket is late.
- No change to the order of `ticketdesk list`, see TKT-013.
- No filter option on `list` or `overdue`, such as by assignee or by priority.
- No warning for a ticket that is close to its due time.
- No decision on the open TODO under CLI-007.

Overdue is not a state, and no event records it. The states stay the three of TKT-001, and
the event kinds stay the three of LOG-002. Each command works out which tickets are overdue
from the log and the current time. A ticket becomes overdue with no command and no new
event, so INV-001 and INV-002 hold.

The output of `ticketdesk list` now depends on the time. The same log can print different
lines at two different times, although nobody added an event. LOG-009 still holds, because
replay yields the same due times.

### TKT-014: When a ticket is overdue

A ticket is overdue when its state is `open` or `assigned` and the current time is later
than its due time. TKT-005 gives the due time. The current time is the moment the command
runs. At exactly the due time the ticket is not overdue. Assigning a ticket changes neither
its due time nor whether it is overdue.

| Priority | State | Time since creation | Overdue |
|----------|-------|---------------------|---------|
| `P1` | `open` | 3 hours 59 minutes | no |
| `P1` | `open` | 4 hours 1 minute | yes |
| `P1` | `assigned` | 4 hours 1 minute | yes |
| `P3` | `open` | 71 hours | no |

TODO: "later than, not equal to" is an assumption, see open question 3.

### TKT-015: A closed ticket is never overdue

A `closed` ticket is not overdue, whatever its due time and whenever it was closed. Closing
an overdue ticket ends its overdue status. The next listing shows the ticket as `closed`
and not as overdue.

TODO: this rule is an assumption, see open question 1.

### TKT-016: Listing overdue tickets

Listing overdue tickets returns every overdue ticket and no other ticket. The order is by
due time, earliest first. Tickets with the same due time are in ID order, ascending. The
listing appends no event, see LOG-001.

The order follows the due time, not the ID. Ticket `1` is `P3`, and ticket `2` is `P1`,
created 60 hours later. At 80 hours after the creation of ticket `1`, both are overdue.
Ticket `2` was due at 64 hours and ticket `1` at 72 hours, so the listing returns ticket
`2` first.

### Open questions

The spec proceeds on the assumption given with each question. An answer that differs
changes only the items named with it.

1. **Is a closed ticket ever overdue?** Assumption: no, see TKT-015. The other answer
   needs a "closed late" mark in CLI-006, and the non-goal on late closed tickets goes.
2. **Where does `OVERDUE` appear in a line?** Assumption: before the state, and the state
   stays, see CLI-006. The other candidate is that `OVERDUE` replaces the state word. That
   keeps the columns aligned and hides whether the ticket is `open` or `assigned`.
3. **Is a ticket overdue at exactly its due time?** Assumption: no, see TKT-014.
4. **Does a line show the due time, or how late the ticket is?** Assumption: no, see the
   non-goals. `ticketdesk overdue` then sorts by a value that the agent cannot see.
5. **Does `ticketdesk overdue` signal overdue tickets through its exit code?** Assumption:
   no. It exits with code 0, see CLI-010. A script cannot use the exit code as an alarm.

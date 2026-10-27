# Tickets

A ticket is one support request. An agent creates it with a title and a priority, assigns
it to a person, and closes it with a resolution note. The priority sets the due time
through a service-level target. Every change is one event in the log, see
[`event-log.md`](event-log.md).

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

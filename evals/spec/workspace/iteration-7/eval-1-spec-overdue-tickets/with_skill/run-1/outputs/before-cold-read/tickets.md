# Tickets

A ticket is one support request. An agent creates it with a title and a priority, assigns
it to a person, and closes it with a resolution note. The priority sets the due time
through a service-level target. A ticket that is not closed when its due time passes is
overdue, see [Overdue tickets](#overdue-tickets). Every change is one event in the log, see
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

---

## Overdue tickets

An agent sees which tickets are late without working out any due time. A ticket that is
not closed when its due time passes shows as `OVERDUE` in the ticket list. A separate
listing returns only the overdue tickets, the one that was due earliest first. The command
surface is in [`cli.md`](cli.md): CLI-001, CLI-006, and CLI-010 to CLI-012.

Status: draft of 2026-11-05, not signed off by the user and not built. ticketdesk 0.3.0
has no overdue behavior. The user signs off before any plan or code cites TKT-014 to
TKT-019.

Overdue is derived and never stored. The log and the current time decide it each time a
command runs. The state of an overdue ticket is still `open` or `assigned`, see TKT-001.

### Goals

- An agent who lists the tickets sees which of them are overdue. TKT-014 to TKT-016 and
  CLI-006 cover this goal.
- An agent gets only the overdue tickets from one command, the one that was due earliest
  first. TKT-018, TKT-019, and CLI-010 cover this goal.
- A person or a script that reads the ticket list sees no change for a ticket that is not
  overdue. CLI-006 covers this goal.

### Non-goals

- **No record of lateness.** Nothing about overdue is written to the log, see TKT-017.
  After a late ticket is closed, nothing shows that it was late.
- **No alert.** No command sends a message. No exit code signals that overdue tickets
  exist.
- **No change to due times.** TKT-005 stays as it is. Business hours, a paused clock, and
  targets per customer are out of scope.
- **No display of the due time.** No command prints the due time of a ticket or how late
  the ticket is.
- **No options.** `list` gets no filter option and no sort option, and it keeps the order
  of TKT-013. `overdue` takes no option of its own.
- **No change to `create`, `assign`, and `close`.** Their rules and their output lines are
  the same for an overdue ticket as for any other ticket.
- **No new output format.** There is no colour and no JSON output.

### TKT-014: When a ticket is overdue

A ticket is overdue when it is not closed and the current time is later than its due time.
TKT-005 sets the due time. The current time is the time at which the command runs. At the
exact due time the ticket is not overdue yet. For example, 5 hours after its creation an
`open` ticket of priority `P1` is overdue, and one of priority `P2` is not.

### TKT-015: A closed ticket is never overdue

A `closed` ticket is never overdue, whatever the time at which it was closed. Closing an
overdue ticket succeeds per TKT-009, and from then on the ticket is not overdue.

### TKT-016: Assigning does not change overdue

Assigning an overdue ticket leaves it overdue, and its due time does not change. Assigning
a ticket that is not overdue does not make it overdue.

### TKT-017: Overdue is never recorded

No event records that a ticket is overdue, and the event kinds stay those of LOG-002.
Listing tickets and listing overdue tickets leave the log file unchanged byte for byte,
see LOG-001. The same log can show a ticket as not overdue now and as overdue later.
LOG-009 still holds for states, assignees, resolutions, and due times.

### TKT-018: The overdue listing

The overdue listing returns every overdue ticket and no other ticket. It leaves out a
ticket that is not overdue yet, and it leaves out every `closed` ticket. When no ticket is
overdue, the listing is empty.

### TKT-019: Order of the overdue listing

The overdue listing is sorted by due time ascending, so the ticket that was due earliest
comes first. Tickets with an equal due time are sorted by ID ascending. The order follows
the due time, not the ID, the priority, or the creation time.

For example, ticket 1 has priority `P3` and was created 73 hours ago. Ticket 2 has
priority `P1` and was created 10 hours ago. Ticket 2 was due 6 hours ago and ticket 1 was
due 1 hour ago, so ticket 2 comes first.

### Open questions for overdue tickets

Every item in this list is an assumption that the user has not confirmed yet. Each item
names the spec items that rest on it.

- TODO: confirm that only `open` and `assigned` tickets can be overdue, and that a ticket
  closed late never shows as late. TKT-014 and TKT-015 assume it.
- TODO: confirm that `OVERDUE` takes the place of the state in `list`. CLI-006 assumes
  it. The cost is that `list` does not show whether an overdue ticket is assigned.
- TODO: confirm that `overdue` prints the same line as `list` and that no command shows
  the due time. CLI-010 and the non-goals assume it.
- TODO: confirm that the feature is display only, with no alert and no record. TKT-017 and
  the non-goals assume it.
- TODO: confirm that a ticket is not overdue at the exact due time. TKT-014 assumes it.
- TODO: confirm that tickets with an equal due time fall back to ID order. TKT-019
  assumes it.
- TODO: confirm that `overdue` with no overdue tickets prints nothing and exits with code
  0. CLI-010 assumes it.
- TODO: decide the open TODO under CLI-007. Until then CLI-012 ties the report of
  `overdue` on a corrupt log to the report of `list`.

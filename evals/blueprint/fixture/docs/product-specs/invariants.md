# System Invariants

Conditions that hold across the product. Unlike feature specs, invariants need not be
testable in isolation. They are properties of the system as a whole. Code reviews,
architecture decisions, and process uphold them together.

Breaking an invariant is a deliberate decision, not a side effect. If a change requires it,
surface it for discussion before proceeding.

Prefix: `INV`.

---

### INV-001: The event log is the single source of truth

The current state of every ticket is derived by replaying the event log from its first
line. No other file, cache, or database holds ticket state.

### INV-002: Events are never edited or deleted

Every change to a ticket appends one new event to the log. An existing line in the log is
never modified, reordered, or removed.

### INV-003: Ticket IDs are never reused

A ticket ID identifies one ticket for the life of the log. Closing a ticket does not free
its ID for a new ticket.

### INV-004: Corrupt data fails fast

A log line that cannot be read stops the operation with an error that names the file and
the line. No corrupt line is skipped and no partial state is returned.

### INV-005: Every event records when it happened

Each event carries the time at which it was appended. The time comes from the store's
clock, never from the caller.

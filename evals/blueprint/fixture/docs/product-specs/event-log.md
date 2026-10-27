# Event log

The event log is the only record of the help desk, see INV-001. It is a JSON lines file:
one JSON object per line. Every change to a ticket appends one event, and the current state
of every ticket is rebuilt by replaying the file from the start. The file is a product
surface. Users choose its path and may read it with any text tool.

Prefix: `LOG`.

---

### LOG-001: One event per change

Creating, assigning, and closing a ticket each append exactly one event. Listing tickets
appends nothing.

### LOG-002: Event kinds

The `kind` of an event is one of: `created`, `assigned`, `closed`.

### LOG-003: Event fields

Every event carries `kind`, `id`, and `at`. The remaining fields depend on the kind.

| Kind | Extra fields |
|------|--------------|
| `created` | `title`, `priority` |
| `assigned` | `assignee` |
| `closed` | `resolution` |

### LOG-004: Timestamp

The `at` field of an event is the time it was appended, in seconds since the Unix epoch.
It is set when the event is written, see INV-005.

### LOG-005: Line format

Each event is one line of JSON with keys sorted alphabetically, ended by a newline. Blank
lines in the file are ignored on replay.

### LOG-006: Missing log file

When the log file does not exist, the help desk behaves as if there are no tickets.
Listing shows nothing, and the first create produces ticket `1` and creates the file.

### LOG-007: A corrupt line stops replay

A line that is not valid JSON stops every operation with an error. The error names the
file path, the line number, and `corrupt event`. Lines after it are not read, and no
ticket state is returned, see INV-004.

### LOG-008: Appending never rewrites

Appending an event leaves every existing line of the file unchanged, see INV-002.

### LOG-009: Replay is deterministic

Replaying the same log always yields the same tickets with the same states, assignees,
resolutions, and due times.

# Architecture

## High-level shape

```
 user
  │  one command per invocation
  ▼
┌──────────────────────────┐
│ cli.py        argparse   │  parse, print, map errors to exit codes
└────────────┬─────────────┘
             │ create / assign / close / list
             ▼
┌──────────────────────────┐      ┌──────────────┐
│ tickets.py TicketService │ ───▶ │ sla.py       │  hours per priority, due time
│            Ticket        │      └──────────────┘
└────────────┬─────────────┘
             │ append(event)  /  replay()
             ▼
┌──────────────────────────┐
│ store.py   EventStore    │  append-only JSON lines file
└────────────┬─────────────┘
             ▼
        tickets.jsonl
```

Three layers and one helper. The CLI turns arguments into service calls and results into
text. The service holds every ticket rule and rebuilds state by replaying events. The store
knows the file and nothing about tickets. The SLA helper is a pure table lookup that the
service calls.

## Why each layer exists

### CLI (`ticketdesk/cli.py`)

The CLI is the only user interface, so all formatting and exit-code decisions live in one
place. It holds no ticket rules. A rule enforced here would be invisible to any future
interface and untestable without a subprocess.

### Service (`ticketdesk/tickets.py`)

The service owns the ticket rules: states, required fields, who may be assigned, what a
valid resolution is. It never reads or writes the file itself. It asks the store for the
event list and derives every ticket from it, so a rule change never needs a data migration.

### Store (`ticketdesk/store.py`)

The store is the only code that knows the log is a file. It appends one JSON line per
event and replays the file into a list of events. It stamps each event with the time from
an injectable clock, which keeps tests deterministic and upholds INV-005.

### SLA table (`ticketdesk/sla.py`)

The hours per priority are a product fact that changes independently of ticket logic. A
separate module keeps the table in one place and gives the service a single function to
validate a priority and compute a due time.

## Key technical assumptions

- **Single writer.** One process appends to the log at a time. There is no file lock.
  Two concurrent writers may interleave lines or compute the same next ID.
- **Full replay on every command.** Each command reads the whole log. This is fine for
  a small team's ticket volume and is the price of INV-001 with no cache.
- **Single tenant, local file.** The log is a path on the local disk. There is no auth,
  no network, and no notion of a user beyond the free-text assignee.
- **Events are trusted.** Replay assumes each event refers to an existing ticket and
  arrives in a valid order. A hand-edited log that violates this stops with an error.
- **Time is seconds since the epoch.** Timestamps and due times are floats from the
  store's clock, never from the caller, see INV-005.

## Tech choices

| Decision | Choice | Why |
|----------|--------|-----|
| Language | Python 3.11+ | Standard library covers everything the tool needs. `X | None` type syntax needs 3.10+. |
| Dependencies | None | Nothing to install beyond Python. CI and local runs stay identical. |
| Storage | Append-only JSON lines file | Human-readable, greppable, trivially append-only. History is never lost. |
| State model | Event replay | One source of truth and no migrations when rules change, see INV-001. |
| CLI parsing | `argparse` | Standard library, gives usage errors and exit code 2 for free. |
| Tests | `unittest` | Standard library. `make test` runs discovery under `tests/`. |
| Lint | `compileall` | A syntax pass only. There is no style or type checker today. |
| CI | GitHub Actions, Python 3.12 | Runs `make lint` and `make test` on every push and PR. |

## Project layout

```
ticketdesk/
├── ticketdesk/
│   ├── __init__.py     Public names: Ticket, TicketError, TicketService, EventStore, due_at, SLA_HOURS
│   ├── cli.py          Argument parsing, output lines, exit codes
│   ├── tickets.py      TicketService and the Ticket dataclass
│   ├── sla.py          SLA_HOURS table and due_at()
│   └── store.py        EventStore: append and replay
├── tests/
│   ├── test_tickets.py Service rules through a fake clock
│   └── test_store.py   Corrupt-line behavior
├── docs/               This documentation
├── Makefile            make test, make lint
├── pyproject.toml      Package metadata and the ticketdesk entry point
└── .github/workflows/ci.yml
```

The CLI is not covered by tests today. Service and store are tested directly.

## What is intentionally simple in v1

- **No file lock.** A small team on one machine does not need one, see the single-writer
  assumption.
- **No snapshot or index.** Replay is fast enough at this scale and keeps one source of
  truth.
- **No reopen.** A closed ticket stays closed. A new ticket is the answer.
- **No users or auth.** The assignee is a free-text name.
- **No style linter or type checker.** `make lint` is a syntax pass.

## Future migration paths

- **Larger logs.** Add a periodic snapshot event or an in-memory cache keyed on file size.
  Replay stays the fallback, so INV-001 holds.
- **Concurrent writers.** Add an advisory file lock around append and ID assignment in
  the store. The service does not change.
- **Other interfaces.** A web or chat front end calls the same service. No ticket rule
  lives in the CLI, so nothing needs to move.
- **Richer SLA.** Business hours or per-customer targets replace the table in `sla.py`.
  The service keeps calling one function for the due time.

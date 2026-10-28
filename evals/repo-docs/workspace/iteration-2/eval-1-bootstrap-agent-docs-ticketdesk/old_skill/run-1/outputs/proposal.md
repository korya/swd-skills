# Proposal: agent docs for ticketdesk

I propose two feature spec files, one invariants file, and the standard layout around them.
Nobody was available to confirm, so I proceed as if you said yes.

## Survey summary

ticketdesk is a Python 3.11+ command-line help desk with no third-party dependencies.

- `ticketdesk/cli.py` parses four commands: `create`, `assign`, `close`, `list`.
- `ticketdesk/tickets.py` holds the ticket rules and rebuilds state by replaying events.
- `ticketdesk/sla.py` maps priority to a due time: P1 4 h, P2 24 h, P3 72 h.
- `ticketdesk/store.py` appends JSON lines to one log file and replays them.
- `make test` runs `unittest`. `make lint` runs `compileall`. CI runs both on Python 3.12.

## Feature spec files

| File | Prefix | Covers |
|------|--------|--------|
| `docs/product-specs/tickets.md` | `TKT` | Ticket lifecycle: create, assign, close, IDs, states, priorities, and due times |
| `docs/product-specs/cli.md` | `CLI` | Commands, arguments, output lines, exit codes, and the log file location |

Plus `docs/product-specs/invariants.md` with prefix `INV`.

## Unusual choices

- **SLA folds into `tickets.md`.** The SLA module has four observable behaviors. That is
  below the floor of five specs for a file, and due times only exist on tickets.
- **No spec file for the event log.** The log has no commands of its own. Its rules are
  cross-cutting, so they become invariants. Its user-visible edges, such as a missing or
  corrupt log file, go in `cli.md`.

## Conflicts found during the survey

I wrote these down as TODOs in the docs. I did not change code.

- **An unknown priority crashes the CLI.** `ticketdesk create x --priority P9` prints a
  Python traceback and exits 1. Other rejected input prints `error: ...` and exits 2.
- **A corrupt log crashes the CLI.** Any command prints a traceback and exits 1.
- **Two writers can create duplicate IDs.** Nothing locks the log file. The docs state a
  single-writer assumption.
- **A change to the SLA table moves old due times.** The due time is computed at replay,
  not stored in the event.

## Layout

```
AGENTS.md
docs/
├── README.md
├── architecture.md
├── guidelines.md
└── product-specs/
    ├── README.md
    ├── invariants.md
    ├── tickets.md
    └── cli.md
```

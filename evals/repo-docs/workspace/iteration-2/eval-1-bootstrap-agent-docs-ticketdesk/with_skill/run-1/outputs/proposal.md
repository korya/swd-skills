# Proposal: agent docs for ticketdesk

I propose two feature spec files plus the invariants file. Nobody was available to confirm,
so I proceeded as if you had said yes.

## Scope

| File | Prefix | What is inside |
|------|--------|----------------|
| `docs/product-specs/invariants.md` | `INV` | The append-only event log, replay as the source of truth, stable ticket numbers, no partial reads of a corrupt log |
| `docs/product-specs/tickets.md` | `TKT` | Ticket lifecycle: create, assign, reassign, close, list, priorities, and due times |
| `docs/product-specs/cli.md` | `CLI` | The `ticketdesk` commands, their output lines, error output, exit codes, and the choice of log file |

The other files follow the skill layout: `AGENTS.md`, `docs/README.md`,
`docs/architecture.md`, `docs/guidelines.md`, and `docs/product-specs/README.md`.

## One merge

Priorities and due times go into `tickets.md`, not into a separate `sla.md`. The SLA table
has three priorities and one rule. A separate file would hold about four specs, below the
minimum of five.

## Conflicts found in the code

I found two errors that do not follow the error format of the other commands. I recorded
them as TODOs in `cli.md` and did not write specs for them.

- `create --priority P9` prints a Python traceback and exits with status 1. Other
  validation errors print `error: <message>` and exit with status 2.
- A corrupt line in the event log makes every command print a traceback and exit with
  status 1.

The tool computes a due time for each ticket, but no command prints it. A library caller
can read it. I recorded this as a TODO in `cli.md`.

## Final layout

```
./
├── AGENTS.md
└── docs/
    ├── README.md
    ├── architecture.md
    ├── guidelines.md
    └── product-specs/
        ├── README.md
        ├── invariants.md   INV-001 to INV-005
        ├── tickets.md      TKT-001 to TKT-014
        └── cli.md          CLI-001 to CLI-008
```

Nobody was available to confirm the final layout, so I proceeded as if you had said yes.

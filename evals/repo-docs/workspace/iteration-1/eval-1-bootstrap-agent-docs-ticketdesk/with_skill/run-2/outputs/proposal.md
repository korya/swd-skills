# Proposal: agent docs for ticketdesk

Scope confirmation for the `repo-docs` bootstrap. Nobody is available to answer, so I
proceed as if this were approved.

## What the repo is

`ticketdesk` 0.3.0 is a command-line help desk for a small support team. Agents create,
assign, and close tickets. Every change is one event appended to a JSON Lines log, and
ticket state is rebuilt by replaying that log. Python 3.11+, standard library only,
`unittest`, `Makefile`, GitHub Actions.

## Feature spec files

| File | Prefix | Covers |
|------|--------|--------|
| `docs/product-specs/tickets.md` | `TKT` | Ticket lifecycle: states, create, assign, close, validation, IDs, priorities and due times |
| `docs/product-specs/event-log.md` | `LOG` | Observable shape of the log file: line format, event fields, replay of missing, blank, and corrupt lines |
| `docs/product-specs/cli.md` | `CLI` | The command surface: subcommands, log path resolution, output lines, exit codes |

## Choices worth a second look

- **SLA folded into `tickets.md`.** `sla.py` is a three-row table and one function. On its
  own it would yield 3 specs, below the 5 to 15 budget. Priority is a ticket attribute, so
  due time lives with tickets.
- **The event log gets its own spec file.** Its format and replay rules are observable
  product behavior, not build plumbing. The cross-cutting properties, single source of
  truth, append-only, fail fast on corruption, go to `invariants.md` as `INV` items.
- **The CLI gets its own spec file.** For a CLI product, output lines and exit codes are
  the user-visible contract.
- **One TODO instead of a spec.** `create --priority P9` ends in an uncaught traceback with
  exit 1, unlike every other rejection, which prints `error: ...` and exits 2. I record this
  as a TODO in `cli.md` rather than specify the traceback as intended behavior.

## Invariants planned

| ID | Title |
|----|-------|
| INV-001 | The event log is the single source of truth |
| INV-002 | Events are append-only |
| INV-003 | A corrupt log stops the system |
| INV-004 | Ticket IDs are never reused |
| INV-005 | Timestamps come from the store clock |
| INV-006 | Standard library only |
| INV-007 | Docs change only with user confirmation |

## Final layout

```
repo/
├── AGENTS.md
└── docs/
    ├── README.md
    ├── architecture.md
    ├── guidelines.md
    └── product-specs/
        ├── README.md
        ├── invariants.md
        ├── tickets.md
        ├── event-log.md
        └── cli.md
```

No code changes. Nothing committed.

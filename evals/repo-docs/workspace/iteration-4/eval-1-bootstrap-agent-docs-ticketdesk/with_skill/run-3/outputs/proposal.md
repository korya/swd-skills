# Proposal: docs layout for ticketdesk

I propose three feature spec files plus the invariants file. The repo is a 170-line Python
CLI with three modules, so three files cover every behavior a user can observe.

## Spec files and prefixes

| File | Prefix | Covers |
|------|--------|--------|
| `docs/product-specs/invariants.md` | `INV` | The log is the single source of truth, append-only writes, stable IDs, closed is terminal, fail fast on a corrupt log. |
| `docs/product-specs/tickets.md` | `TKT` | Ticket lifecycle: create, assign, close, list, the validation rules, and the due time per priority. |
| `docs/product-specs/cli.md` | `CLI` | The command surface: commands, output lines, error lines, exit codes, how the log path is chosen. |
| `docs/product-specs/event-log.md` | `LOG` | The storage contract: one JSON object per line, timestamps, replay, blank lines, corrupt lines. |

## Merges and splits worth a look

- **SLA folded into `tickets.md`.** The SLA module holds one table (P1: 4 hours, P2: 24,
  P3: 72) and one rule. On its own it would be a three-item spec file. The due time is a
  property of a ticket, so it lives with the ticket rules. A separate `sla.md` is one
  rename away if the SLA grows.
- **CLI split from tickets.** The lifecycle rules hold whether a caller uses the command
  line or the Python package. The output format, exit codes, and the `--log` flag belong to
  the command line only. Two files keep each one readable.

## Two findings that will appear as TODOs in the specs

The CLI catches ticket errors and prints `error: ...` with exit code 2. Two other failures
escape as a Python traceback with exit code 1 instead:

- `create` with a priority outside P1, P2, P3
- any command when the log holds a corrupt line

I will document the observed behavior and mark each with a TODO, not fix the code. Nobody is
available to confirm, so I proceed with this layout.

## Full layout

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
    ├── cli.md
    └── event-log.md
```

## Final layout, for confirmation

All nine files exist. `prose-lint.py` reports 0 findings in 9 files. Every cited ID
resolves, both indexes list every spec file, and no placeholder or tip comment survives.

| File | Lines | IDs |
|------|-------|-----|
| `AGENTS.md` | 96 | indexes all 8 files under `docs/` |
| `docs/README.md` | 38 | |
| `docs/architecture.md` | 100 | |
| `docs/guidelines.md` | 50 | |
| `docs/product-specs/README.md` | 52 | indexes 4 spec files |
| `docs/product-specs/invariants.md` | 40 | `INV-001` to `INV-006` |
| `docs/product-specs/tickets.md` | 91 | `TKT-001` to `TKT-014` |
| `docs/product-specs/cli.md` | 96 | `CLI-001` to `CLI-009` |
| `docs/product-specs/event-log.md` | 61 | `LOG-001` to `LOG-007` |

Nobody is available to confirm, so I treat this layout as confirmed. No code changed, and
nothing is committed.

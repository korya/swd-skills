# Proposal: agent docs for ticketdesk

I propose three feature spec files and one invariants file. Nobody was available to answer
during this run, so the run treats this proposal as approved.

## Scope confirmation (workflow step 2)

The repo is a Python CLI with three user-facing areas. Each area gets one spec file.

| File | Prefix | What is inside |
|------|--------|----------------|
| `docs/product-specs/invariants.md` | `INV` | The event log is the only source of truth, the log is append-only, and each change is one event. |
| `docs/product-specs/tickets.md` | `TKT` | The `create`, `assign`, `close`, and `list` commands, ticket numbers, states, error messages, and exit codes. |
| `docs/product-specs/priorities.md` | `PRI` | Priority values, the default priority, and the due time for each priority. |
| `docs/product-specs/event-log.md` | `LOG` | The location of the log, its line format, and how a missing or corrupt log behaves. |

### One unusual split

Priorities get their own file, although they hold only five specs. The code keeps them in a
separate module with its own table of hours. A change to the service-level targets then
touches one small file. The alternative is to merge them into `tickets.md` under `TKT`.

### No spec file for the build

The Makefile and the CI workflow have no observable product behavior. They go into
`docs/guidelines.md` instead.

## Conflicts found during the survey

The code does not change in this run. These items go into the specs as TODO notes for a
decision.

- **Unknown priority.** `ticketdesk create x --priority P9` prints a Python traceback and
  exits with code 1. Every other rejected command prints `error: <message>` and exits with
  code 2.
- **Corrupt log.** A corrupt line in the log also ends in a traceback and exit code 1, not
  in the `error:` form.
- **Due time.** The CLI never shows the due time. Only a Python caller of the package can
  read it.

## Final layout (workflow step 5)

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
    ├── priorities.md
    └── event-log.md
```

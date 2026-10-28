# Proposal: agent docs for ticketdesk

I propose two feature spec files plus the invariants file. The event log gets no spec file of its own. Its rules are cross-cutting, so they go into `invariants.md` and `architecture.md`.

## Spec files and prefixes

| File | Prefix | Covers |
|------|--------|--------|
| `docs/product-specs/invariants.md` | `INV` | The event log as the only source of truth, append-only history, fail-fast replay, stable ticket IDs, specs lead code |
| `docs/product-specs/tickets.md` | `TKT` | The ticket lifecycle: create, assign, close, list, states, priorities, due times, and the rejection rules |
| `docs/product-specs/cli.md` | `CLI` | The `ticketdesk` command: subcommands, log location, output lines, error output, and exit codes |

## Unusual choices

- **Priorities and due times are inside `tickets.md`.** A separate `sla.md` would hold only four specs. That is below the budget of five to fifteen.
- **The event log has no spec file.** Its observable rules hold across every command. They become `INV-001` to `INV-004`.

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

## Gaps I found during the survey

The docs record these gaps. I do not change any code.

- An unknown priority given to `ticketdesk create` ends with a Python traceback and exit status 1. Other rejections print `error: ...` and exit with status 2.
- A corrupt event log also ends with a traceback and exit status 1.
- The test `test_assign_requires_open_ticket` has a name that suggests only open tickets take an assignee. The code also lets you reassign an assigned ticket. The spec follows the code and flags the conflict.
- The help desk computes a due time for every ticket. No command shows the due time or flags an overdue ticket.
- Two processes that write the same log at the same time can give two tickets the same ID. Nothing locks the file.
- No test runs the CLI.

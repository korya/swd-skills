# Proposal: agent docs for ticketdesk

I propose two feature spec files plus the invariants file. Priorities and due times merge
into the ticket spec because alone they hold only four behaviors.

## Spec files and prefixes

| File | Prefix | What is inside |
|------|--------|----------------|
| `docs/product-specs/invariants.md` | `INV` | The append-only event log, the log as the only source of truth, fail-fast replay, stable ticket IDs |
| `docs/product-specs/tickets.md` | `TKT` | Create, assign, close, and list tickets. Priorities, due times, error output, exit codes |
| `docs/product-specs/event-log.md` | `LOG` | Where the log file lives, how to choose it, its line format, a missing file |

## Unusual split or merge

- **Priorities and due times merge into `tickets.md`.** The priority rules hold four
  behaviors. The skill asks for 5 to 15 items per spec file.
- **No spec for the build, lint, or CI.** They have no product behavior. They go in
  `docs/guidelines.md`.

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
    └── event-log.md
```

## Conflicts found during the survey

The specs record current behavior. These two cases break the error contract of the other
commands. The CLI prints a Python traceback and exits with status 1, not an `error:` line
with status 2.

- `create` with an unknown priority, such as `P9`.
- Any command on a log file with a corrupt line.

Confirm whether these are bugs. The docs do not change the code.

## Answer

Nobody was available to answer. I proceeded as if the user said yes.

## Final layout for confirmation

The layout matches the proposal above. The linter reports no findings on any of the eight
files.

| File | Content |
|------|---------|
| `AGENTS.md` | Pitch, tech stack, 30-second architecture, layout, doc index, process rules (89 lines) |
| `docs/README.md` | How to manage `docs/` |
| `docs/architecture.md` | Four layers, five assumptions, tech choices, omissions (87 lines) |
| `docs/guidelines.md` | Lint, test, planning, regressions, commits |
| `docs/product-specs/README.md` | Spec format and the index of three spec files |
| `docs/product-specs/invariants.md` | `INV-001` to `INV-004` |
| `docs/product-specs/tickets.md` | `TKT-001` to `TKT-013` |
| `docs/product-specs/event-log.md` | `LOG-001` to `LOG-007` |

Open TODOs in the docs:

- `TKT-004` and `LOG-007`: should these failures print an `error:` line and exit 2?
- `docs/guidelines.md`: the repo states no coverage target.
- `docs/architecture.md`: are the listed omissions deliberate?

Nobody was available to answer. I proceeded as if the user said yes.

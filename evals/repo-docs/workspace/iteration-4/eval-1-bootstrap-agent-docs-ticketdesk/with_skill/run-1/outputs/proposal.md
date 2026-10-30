# Proposal: docs layout for ticketdesk

I propose two feature spec files plus the invariants file. The repo is a single-package
Python CLI with one user-visible surface, so the split follows what a support agent does
with it, not the module layout.

## Spec files and prefixes

| File | Prefix | Covers |
|------|--------|--------|
| `docs/product-specs/invariants.md` | `INV` | The event log is the only source of truth, writes are append-only, replay stops on a corrupt line, IDs are never reused, closed is terminal. |
| `docs/product-specs/tickets.md` | `TKT` | Ticket lifecycle: create, assign, close, list. States, validation of title, assignee, and resolution note, ID assignment, priority values, and the due time per priority. |
| `docs/product-specs/cli.md` | `CLI` | The command surface: the four commands, how the log path is chosen, the output line of each command, the `error:` line and exit code 2. |

## Merges and splits worth a look

- **SLA folded into `tickets.md`.** The SLA module is one table of three priorities and one
  derived due time. That is two or three specs, too few for a file of their own.
- **No `event-log.md` feature file.** The log's user-visible properties are cross-cutting
  guarantees, so they live in `invariants.md`. The location of the log file is a CLI concern
  and lives in `cli.md`.
- **One known inconsistency to record, not fix.** An unknown priority on `create` escapes as
  an uncaught error with a traceback instead of the `error:` line. The spec will describe
  the current behavior and mark the gap with a TODO. No code changes in this run.

## Other files

`AGENTS.md`, `docs/README.md`, `docs/architecture.md`, `docs/guidelines.md`, and
`docs/product-specs/README.md` follow the skill's templates with the facts from this repo.

Nobody is available to answer, so I proceed as if this proposal were confirmed.

## Final layout for confirmation

All eight files exist, `prose-lint.py` reports 0 findings in 8 files, and no code file
changed. The git working tree shows only `AGENTS.md` and `docs/` as untracked.

```
repo/
├── AGENTS.md                          89 lines: pitch, stack, 30-second architecture, layout, doc index, process rules, commands
└── docs/
    ├── README.md                      how to manage docs/
    ├── architecture.md                4 layers, 4 assumptions, tech choices, deliberate omissions, one migration path
    ├── guidelines.md                  make lint, make test, CI, planning, regressions, commits
    └── product-specs/
        ├── README.md                  spec format and the index of 3 spec files
        ├── invariants.md              INV-001 to INV-005
        ├── tickets.md                 TKT-001 to TKT-011
        └── cli.md                     CLI-001 to CLI-008
```

Items to confirm on the next pass:

- `CLI-006` records that an unknown priority ends in a traceback with exit code 1, which
  differs from the `error:` line of `CLI-005`. The spec carries a TODO for the team to pick
  the intended behavior.
- `TKT-004` records the due time per priority even though the command line never shows it.
  The package exposes it to programs, and the tests check it.

Nobody is available to answer, so I treat this layout as confirmed.

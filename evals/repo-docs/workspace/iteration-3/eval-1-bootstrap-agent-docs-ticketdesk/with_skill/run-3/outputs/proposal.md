# Proposal: spec files and prefixes for ticketdesk

The product splits into tickets, the event log, and the command line, so I propose one spec
file for each. Each area is observable on its own. The ticket rules show through any
command, the log through the file on disk, and the command line through its output and exit
codes.

| File | Prefix | Covers |
|------|--------|--------|
| `docs/product-specs/tickets.md` | `TKT` | Ticket lifecycle: states, priorities, due time, create, assign, close, list. |
| `docs/product-specs/event-log.md` | `LOG` | The JSON lines file: location, line content, missing and corrupt files. |
| `docs/product-specs/cli.md` | `CLI` | Commands, output lines, error format, exit codes. |

## Merge: service-level targets go into `tickets.md`

The due-time rules would make a spec file of three items, below the floor of five. They
live in `tickets.md` as one spec with a table (P1 4 hours, P2 24 hours, P3 72 hours). No
command shows the due time, so the spec also carries a TODO for that gap.

## Invariants

The code enforces four cross-cutting conditions, and `invariants.md` records only these:

- INV-001: the event log is the only source of truth.
- INV-002: events are appended, never edited or deleted.
- INV-003: ticket IDs are stable and never reused.
- INV-004: corrupt data stops the program.

## Findings for you to confirm

- An unknown priority and a corrupt log line end the command with a Python traceback and
  exit code 1. Every other rejection prints `error: <reason>` and exits 2. The CLI spec
  records the current behavior and marks it with a TODO.
- The due time is computed for every ticket, but no command shows it. Recorded as a TODO
  in `tickets.md`.
- The repo states no coverage target or test-per-change rule. `guidelines.md` records the
  policy it does state (run `make test` before a push, CI runs it) and marks the gap.

Nobody is available to answer, so I proceed as if you had confirmed this layout.

## Final layout, for your confirmation

Every file below passes `prose-lint.py`, every cited ID exists, and both indexes are
complete. No code file changed.

```
repo/
├── AGENTS.md                         95 lines
└── docs/
    ├── README.md                     how to manage docs/
    ├── architecture.md               layers, assumptions, tech choices, omissions
    ├── guidelines.md                 lint, test, planning, regressions, commits
    └── product-specs/
        ├── README.md                 spec format and index
        ├── invariants.md             INV-001 to INV-004
        ├── tickets.md                TKT-001 to TKT-013
        ├── event-log.md              LOG-001 to LOG-007
        └── cli.md                    CLI-001 to CLI-008
```

Treated as confirmed, since nobody is available to answer.

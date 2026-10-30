# Proposal: agent docs for ticketdesk

I propose three feature spec files plus the standard layout. Please confirm the split and
the prefixes before I create any file.

## What I found

ticketdesk is a command-line help desk for a small support team, version 0.3.0, Python 3.11
or later, standard library only. The code has four modules in one package:

| Module | Role |
|---|---|
| `ticketdesk/cli.py` | argparse front end: `create`, `assign`, `close`, `list` |
| `ticketdesk/tickets.py` | ticket rules: numbering, states, assignment, closing |
| `ticketdesk/sla.py` | priority table and the due-time rule |
| `ticketdesk/store.py` | append-only JSON Lines log, replayed on every command |

Tests use `unittest`, lint is `python3 -m compileall`, and CI runs both on every push.

## Proposed spec files

| File | Prefix | Covers | Items |
|---|---|---|---|
| `docs/product-specs/tickets.md` | `TKT` | ticket fields, numbering, priorities and due times, states, create, assign, close, list | about 12 |
| `docs/product-specs/event-log.md` | `LOG` | the log file as a user-visible artifact: one line per change, record shape, replay, missing file, corrupt line | about 7 |
| `docs/product-specs/cli.md` | `CLI` | command surface, log location flag and env var, output line formats, error output, exit codes | about 8 |

Plus `docs/product-specs/invariants.md` with prefix `INV`, about 4 items: single source of
truth, append-only, stable ticket numbers, fail loud on a corrupt log.

## Judgment calls

- **SLA merged into `tickets.md`.** The SLA rule is one table and a default. On its own it
  would be a 4-item file below the 5-item floor. If you want `sla.md` with prefix `SLA`, say
  so.
- **The log file gets a spec.** The README advertises the JSON event log as a feature, and a
  user can open the file. So its line format is a contract, not an implementation detail.
- **Two observed behaviors look unintended, and I will record them as observed, not as
  design.** An unknown priority and a corrupt log line both end in a Python traceback with
  exit code 1, while every other rejection prints `error: ...` and exits 2. The specs note
  this with a TODO for you to decide.

## Standard files

`AGENTS.md`, `docs/README.md`, `docs/architecture.md`, `docs/guidelines.md`,
`docs/product-specs/README.md`. No `Future migration paths` section in architecture: the
code prepares none.

Proceeding as if confirmed, per the run instructions.

## Final layout (step 5 confirmation)

Created, all under `outputs/repo/`. No code or test file changed. Nothing committed.

```
AGENTS.md                          102 lines
docs/
├── README.md                       how to manage docs/
├── architecture.md                 4 layers, 5 assumptions, 7 tech choices, 5 omissions
├── guidelines.md                   lint, test, planning, regressions, commits
└── product-specs/
    ├── README.md                   spec format + index of 4 files
    ├── invariants.md               INV-001 to INV-004
    ├── tickets.md                  TKT-001 to TKT-012
    ├── event-log.md                LOG-001 to LOG-007
    └── cli.md                      CLI-001 to CLI-008
```

`prose-lint.py` reports no findings on any of the nine files. Every cited ID exists.

Two TODOs are deliberate and need your decision: LOG-007 and CLI-008 record that an
unknown priority and a corrupt log line exit with a traceback and code 1, unlike every
other rejection. Please confirm the layout, or name what to change.

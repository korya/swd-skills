# AGENTS.md

Operating manual for coding agents and humans working on this repo.

## What this project is

**ticketdesk** is a command-line help desk for a small support team. Agents create tickets,
assign them, and close them with a resolution note. Every change is appended to an event
log in a JSON lines file, so the history of a ticket is never lost. The package is at
version 0.3.0 and depends on nothing beyond the Python standard library.

The one design principle: the log is the truth. Ticket state is always rebuilt by replaying
it, and nothing in the log is ever edited or deleted.

## Tech stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.11+ |
| CLI | `argparse` |
| Storage | Append-only JSON lines file |
| Tests | `unittest`, `make test` |
| Lint | `compileall` syntax pass, `make lint` |
| CI | GitHub Actions on Python 3.12 |
| Dependencies | None |

## Architecture in 30 seconds

```
cli.py  ──▶  tickets.py (TicketService)  ──▶  store.py (EventStore)  ──▶  tickets.jsonl
                     │
                     └──▶  sla.py (hours per priority)
```

- The CLI parses one command, calls the service, prints a line, and maps errors to exit
  codes.
- The service holds every ticket rule and derives every ticket by replaying the log.
- The store appends events and replays the file. It knows nothing about tickets.

See [`docs/architecture.md`](docs/architecture.md) for the full picture.

## Project layout

```
ticketdesk/
├── ticketdesk/         The package: cli.py, tickets.py, sla.py, store.py
├── tests/              unittest suites for the service and the store
├── docs/               Reference docs (architecture, guidelines, product specs)
├── Makefile            make test, make lint
├── pyproject.toml      Package metadata and the ticketdesk entry point
├── AGENTS.md           This file
└── .github/workflows/  CI: make lint, make test
```

## Documentation index

Read these before working on related areas. `docs/product-specs/invariants.md` is the
floor. Anything that breaks an invariant needs explicit user confirmation.

Each product spec has a stable, globally unique ID of the form `PREFIX-NNN`, such as
`TKT-010`. Reference these IDs in code comments, tests, and PRs for durable traceability.

| When you are... | Read |
|--------------|------|
| Onboarding for the first time | This file, then [`docs/architecture.md`](docs/architecture.md), then [`docs/product-specs/README.md`](docs/product-specs/README.md) |
| Changing **product behavior** (feature, user-visible bug fix) | The relevant feature spec in [`docs/product-specs/`](docs/product-specs/) |
| Changing **architecture** (new layer, dependency, layer-crossing pattern) | [`docs/architecture.md`](docs/architecture.md) |
| Touching **how we work** (lint, tests, regression process) | [`docs/guidelines.md`](docs/guidelines.md) |
| Investigating **a regression** | [`docs/guidelines.md`](docs/guidelines.md), the 5-whys protocol |
| Wondering **how docs are managed** | [`docs/README.md`](docs/README.md) |

### Documents at a glance

| File | Prefix | Summary | Load when... |
|------|--------|---------|------------|
| [`AGENTS.md`](AGENTS.md) | none | This file. Project overview and doc index. | Always. First thing to read. |
| [`docs/README.md`](docs/README.md) | none | How to manage `docs/`, spec format requirements. | Editing or adding docs. |
| [`docs/architecture.md`](docs/architecture.md) | none | Layers, assumptions, tech decisions, migration paths. | Touching boundaries, the store, or the data model. |
| [`docs/guidelines.md`](docs/guidelines.md) | none | Lint, test, planning, regression, and doc-update rules. | Onboarding, regressions, before any non-trivial change. |
| [`docs/product-specs/README.md`](docs/product-specs/README.md) | none | Spec format, prefix table, feature index. | Starting any spec-related work. |
| [`docs/product-specs/invariants.md`](docs/product-specs/invariants.md) | `INV` | Rules that must hold across all changes. | Before any change. **The floor.** |
| [`docs/product-specs/tickets.md`](docs/product-specs/tickets.md) | `TKT` | Ticket states, creation, assignment, closing, due time by priority, listing. | Touching `tickets.py` or `sla.py`, or any ticket rule. |
| [`docs/product-specs/event-log.md`](docs/product-specs/event-log.md) | `LOG` | Event kinds and fields, replay, corrupt-line and missing-file behavior. | Touching `store.py` or the log format. |
| [`docs/product-specs/cli.md`](docs/product-specs/cli.md) | `CLI` | Commands, log path selection, output lines, errors, exit codes. | Touching `cli.py` or anything a user sees. |

## Process rules

- **Lint and test 100% of code.** `make lint && make test` before every push. See
  [`docs/guidelines.md`](docs/guidelines.md).
- **Validate assumptions before depending on them.** A 30-second check beats hours of
  debugging.
- **Regression bug? Run the 5 whys** before patching. Document the root cause.
- **Doc changes need user confirmation.** Do not silently rewrite specs or architecture.
- **Surface conflicts.** If a change contradicts a spec or invariant, stop and discuss.
  One is open now: the TODO under CLI-007 in [`docs/product-specs/cli.md`](docs/product-specs/cli.md).
- **Reference spec IDs** in commit messages, code comments, tests, and PR descriptions.

## Running the project

```bash
make lint                                   # syntax pass over ticketdesk/ and tests/
make test                                   # 7 unittest cases
python3 -m ticketdesk.cli --log /tmp/t.jsonl create "Printer on fire" --priority P1
python3 -m ticketdesk.cli --log /tmp/t.jsonl assign 1 dana
python3 -m ticketdesk.cli --log /tmp/t.jsonl close 1 "Replaced the toner cartridge"
python3 -m ticketdesk.cli --log /tmp/t.jsonl list
```

Installed as a package, the entry point is `ticketdesk`. Without `--log`, the path comes
from `TICKETDESK_LOG` or defaults to `tickets.jsonl` in the current directory.

## Current state

- Done: create, assign, close, list. Due time by priority. Append-only log with
  fail-fast replay. Tests for the service and the store.
- Not covered by tests: the CLI.
- Known conflict: unknown priority and corrupt log escape as tracebacks, see CLI-007.
- Planned: nothing is recorded in the repo. TODO: confirm the roadmap with the user.

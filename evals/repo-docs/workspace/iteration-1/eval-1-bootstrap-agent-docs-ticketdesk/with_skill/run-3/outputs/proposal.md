# Proposal: agent docs for ticketdesk

Written in place of the scope confirmation in step 2 of the repo-docs workflow. Nobody was
available to answer, so I proceed as if you had said yes.

## What I found

ticketdesk 0.3.0 is a command-line help desk with an append-only event log. It uses only
the Python standard library and runs on Python 3.11 or newer.

| Layer | Module | Role |
|---|---|---|
| CLI | `ticketdesk/cli.py` | argparse front end, four subcommands, exit codes |
| Domain | `ticketdesk/tickets.py` | create, assign, close, list, state rules |
| SLA | `ticketdesk/sla.py` | priority values and hours until due |
| Storage | `ticketdesk/store.py` | JSON lines log, replay, fail fast on corruption |

## Spec files I will create

| File | Prefix | Items | Covers |
|---|---|---|---|
| `docs/product-specs/invariants.md` | `INV` | 7 | log as source of truth, append-only, fail fast, stable IDs, process rules |
| `docs/product-specs/tickets.md` | `TKT` | 12 | ticket lifecycle: states, create, assign, close, list, errors |
| `docs/product-specs/sla.md` | `SLA` | 5 | priority values, hours per priority, due time, rejection of unknown priority |
| `docs/product-specs/cli.md` | `CLI` | 8 | subcommands, log path resolution, output lines, exit codes |

## Choices worth a second look

- **SLA gets its own file at 5 items.** That sits at the floor of the 5 to 15 budget. I
  kept it separate because service-level targets are a distinct domain that tends to grow
  with escalation and business hours. Folding it into `tickets.md` would push that file to
  17 items.
- **The event log is not a feature spec.** Its observable properties are cross-cutting, so
  they live in `invariants.md`. The file format itself is an implementation detail and
  goes in `architecture.md`.
- **One conflict surfaced, not papered over.** The CLI shows a Python traceback when the
  priority is unknown, instead of an `error:` line and exit code 2. I document the intended
  behavior in `CLI-007` and mark the gap with a TODO rather than spec the traceback.

## Other files

`docs/README.md`, `docs/architecture.md`, `docs/guidelines.md`, `docs/product-specs/README.md`,
and `AGENTS.md`, filled from the templates with facts from the repo. No code changes, no
commit.

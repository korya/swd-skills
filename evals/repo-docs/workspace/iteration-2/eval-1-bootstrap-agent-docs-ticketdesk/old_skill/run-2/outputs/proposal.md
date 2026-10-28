# Proposal: agent docs for ticketdesk

I propose three feature spec files, one invariants file, and the standard `docs/` layout.
Nobody was available to confirm, so I proceed as if you approved this proposal.

## Feature spec files

| File | Prefix | Covers |
|------|--------|--------|
| `docs/product-specs/tickets.md` | `TKT` | Ticket lifecycle: create, assign, close, read. States, IDs, and validation rules. |
| `docs/product-specs/sla.md` | `SLA` | Priorities and the due time that each priority sets. |
| `docs/product-specs/cli.md` | `CLI` | The `ticketdesk` command: subcommands, output lines, exit codes, and the log location. |
| `docs/product-specs/invariants.md` | `INV` | Event log rules and other conditions that hold across every change. |

## Unusual choices

- **SLA is its own file.** The SLA rules are a separate concern from the ticket lifecycle.
  Folded into `tickets.md`, the lifecycle file would hold about 16 specs. That is over the
  budget of 15.
- **No feature file for the event log.** The log has no commands of its own. Its rules are
  cross-cutting, so they go in `invariants.md`. The log location is user-visible, so it
  goes in `cli.md`.
- **Two inconsistencies stay visible, not fixed.** An unknown priority and a corrupt log
  both end the command with a Python traceback and exit code 1. Other rejected input prints
  `error: <reason>` and exits with code 2. The specs record the current behavior and carry a
  TODO. I changed no code.

## Other files

- `AGENTS.md`
- `docs/README.md`
- `docs/architecture.md`
- `docs/guidelines.md`
- `docs/product-specs/README.md`

## Facts I could not find in the repo

- A test coverage policy. No coverage tool runs in CI.
- A type checker. The repo has none.
- A real linter. `make lint` only compiles the code to find syntax errors.
- The intended concurrency model. The code has no file lock.

The docs record each of these as a TODO with the reason.

# Proposal: docs layout for ticketdesk

I propose two feature spec files plus the standard set. The repo is one Python package of
four modules, so two spec files cover every behavior a user can observe.

## Survey findings

ticketdesk is a command-line help desk for a small support team, version 0.3.0. It has no
third-party dependencies and needs Python 3.11 or newer. The code has three layers:

| Layer | Module | Role |
|---|---|---|
| CLI | `ticketdesk/cli.py` | argparse commands `create`, `assign`, `close`, `list`, and the `--log` flag |
| Domain | `ticketdesk/tickets.py`, `ticketdesk/sla.py` | ticket rules, state machine, due times by priority |
| Storage | `ticketdesk/store.py` | append-only JSON lines event log, replayed on every read |

Tests use `unittest`. Lint is `compileall`. CI runs both on every push and pull request.

## Proposed spec files

| File | Prefix | Covers |
|---|---|---|
| `docs/product-specs/invariants.md` | `INV` | append-only log, log as the single source of truth, corrupt line stops replay, IDs never reused |
| `docs/product-specs/tickets.md` | `TKT` | ticket lifecycle: create, assign, close, list, their validation rules, priorities and due times |
| `docs/product-specs/cli.md` | `CLI` | the command-line surface: commands, output lines, error reporting, exit codes, log path selection |

## Splits and merges worth a look

- **SLA folded into `tickets.md`.** The SLA module yields three observable facts: the
  three priorities, their hours, and the rejection of any other value. Three items are
  too few for a file of their own. They sit in `tickets.md` as the due-time rules.
- **CLI as its own file.** The output format, the `error:` line on stderr, exit code 2,
  and the `--log` and `TICKETDESK_LOG` selection are a contract that scripts depend on.
  Mixing them with ticket rules would blur the two prefixes.
- **No spec for the build.** The Makefile and CI have no user-visible behavior. They are
  described in `docs/guidelines.md` and `AGENTS.md` only.

## One conflict to flag

An unknown priority on `ticketdesk create` escapes as a Python traceback instead of an
`error:` line with exit 2. The ticket layer raises a different error type than the one
the CLI catches. I will record the current behavior in `cli.md` with a TODO rather than
specify the intended one, since that is a decision for you.

## Remaining files

`docs/README.md`, `docs/architecture.md`, `docs/guidelines.md`,
`docs/product-specs/README.md`, and `AGENTS.md` follow the templates with no deviation.

Nobody is available to answer, so I proceed as if you had said yes.

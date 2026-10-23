# Proposal: agent docs for ticketdesk

Written in place of the "confirm scope with the user" step. Nobody was available, so I
proceed as if this were approved. Push back on anything below and I will redo that part.

## What the repo is

`ticketdesk` 0.3.0 — a stdlib-only Python 3.11+ CLI help desk. Agents `create`, `assign`,
`close`, and `list` tickets. Every change is one event appended to a JSON Lines log; the
current state of every ticket is rebuilt by replaying that log. ~170 lines of code, 7 tests,
`make lint` (compileall) + `make test` (unittest) in CI.

## Proposed layout

```
AGENTS.md
docs/
├── README.md
├── architecture.md
├── guidelines.md
└── product-specs/
    ├── README.md
    ├── invariants.md          INV
    ├── tickets.md             TKT   ticket lifecycle: create / assign / close / list, priorities, SLA due times
    ├── event-log.md           LOG   on-disk event log: format, replay, corruption handling
    └── cli.md                 CLI   command surface: commands, output format, exit codes, log-path resolution
```

## Feature spec files and prefixes

| File | Prefix | Covers | Approx. items |
|------|--------|--------|---------------|
| `tickets.md` | `TKT` | States, sequential IDs, title/assignee/resolution validation, who may be assigned or closed, SLA due time per priority, list ordering | 13 |
| `event-log.md` | `LOG` | JSON Lines format, event kinds and payloads, missing file = empty history, blank lines, corrupt line halts replay | 5 |
| `cli.md` | `CLI` | The four commands, default priority, stdout formats, `error:`/exit-2 contract, `--log` > `TICKETDESK_LOG` > `tickets.jsonl` | 7 |

## Choices worth a second look

1. **SLA folded into `tickets.md`.** `sla.py` is a separate module, but its only observable
   behavior is "due time = created + N hours by priority" — one spec, not a file. A `sla.md`
   with one or two items would be noise. Split it out later if SLA grows (breach detection,
   business hours, per-customer targets).
2. **Event log gets its own file even though it is "internal".** The README advertises the
   log as a product promise ("history is never lost"), the format is a de-facto interface
   for anyone reading the file, and the corruption behavior is user-visible. That is product
   behavior, not implementation.
3. **CLI as a separate spec file.** Output formats and exit codes are what scripts and humans
   depend on; mixing them into `tickets.md` would blur domain rules with presentation.
4. **Invariants (INV)**: log is the single source of truth; events are append-only; ticket
   IDs are never reused; corrupt data fails fast rather than being skipped; every state
   change is exactly one event; doc changes require user confirmation.

## One conflict surfaced, not resolved

An unknown `--priority` (e.g. `P9`) escapes the CLI as a raw Python traceback with exit
code 1, while every other validation failure prints `error: <message>` to stderr and exits 2.
The specs describe priority validation at the domain level (`TKT-003`) and the error
contract for the CLI (`CLI-007`), and `cli.md` carries a TODO naming the gap. I did not
change code (out of scope) and did not spec the traceback as intended behavior. Your call:
make the CLI catch it, or declare the current behavior acceptable and I will note it.

## Guardrails

- No code changes, no commits. Only new files under `docs/` plus `AGENTS.md`.
- Existing `README.md` left untouched.

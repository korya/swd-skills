# Proposal: docs layout for ticketdesk

I propose two feature spec files plus the invariants. Nobody is available to answer, so
I proceed as if you had confirmed this proposal.

## What I found

ticketdesk is a 268-line Python CLI with four commands: `create`, `assign`, `close`, and
`list`. Every change is one line in a JSON Lines event log. Ticket state is rebuilt by
replaying that log on every command. A small SLA table maps a priority to a due time.

## Spec files and prefixes

| File | Prefix | Covers |
|---|---|---|
| `docs/product-specs/invariants.md` | `INV` | append-only log, single source of truth, stable IDs, fail loudly on corrupt data |
| `docs/product-specs/tickets.md` | `TKT` | create, assign, close, list, states, priorities, due times, error output |
| `docs/product-specs/event-log.md` | `LOG` | log location, record format, replay, missing file, corrupt line |

## One merge to flag

The SLA module gets no file of its own. It has one observable behavior: a due time per
priority. The CLI does not display that time. One spec item in `tickets.md` covers it,
with a TODO on the missing display. A separate file would hold one item.

## Two code quirks I will surface, not hide

- An unknown priority and a corrupt log line both end in a Python traceback with exit
  code 1. Every other rejection prints `error: <reason>` and exits with code 2. The specs
  record the traceback as current behavior and mark the inconsistency with a TODO.
- The due time is computed for every ticket but no command prints it. The spec records
  it as reachable from Python only.

## Other files

`AGENTS.md`, `docs/README.md`, `docs/architecture.md`, `docs/guidelines.md`, and
`docs/product-specs/README.md` follow the skill's templates with no deviation.

## Final layout (written after the proposal, shown here for the record)

```
repo/
├── AGENTS.md
└── docs/
    ├── README.md
    ├── architecture.md
    ├── guidelines.md
    └── product-specs/
        ├── README.md
        ├── invariants.md
        ├── tickets.md
        └── event-log.md
```

## Confirmation request for the final layout (step 5)

The eight files above exist and `prose-lint.py` reports `0 findings in 8 files`. Every
cited `INV`, `TKT`, and `LOG` ID resolves to a heading. Both indexes are complete. No code
or tracked file changed. Nobody is available to answer, so I treat the layout as confirmed.

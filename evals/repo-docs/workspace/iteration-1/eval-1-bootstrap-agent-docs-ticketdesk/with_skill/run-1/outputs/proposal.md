# Proposed scope for the ticketdesk agent docs

I surveyed the repo before writing anything. Here is what I found and what I propose to
create. Nobody is available to answer, so I proceed as if you said yes.

## What I found

- Product: a command-line help desk. Agents create tickets, assign them, and close them
  with a resolution note. Every change is one event in an append-only JSON lines log.
- Stack: Python 3.11+, standard library only, `argparse` CLI, `unittest`, `make lint`
  (compileall) and `make test`, GitHub Actions CI on Python 3.12.
- Source modules: `ticketdesk/cli.py`, `tickets.py`, `sla.py`, `store.py`. 7 tests pass.
- No existing agent docs, no `docs/` folder, no design doc beyond a 5-line README.

## Feature spec files I will create

| File | Prefix | Covers |
|------|--------|--------|
| `docs/product-specs/tickets.md` | `TKT` | Ticket lifecycle: create, assign, close, list. States, ID assignment, validation rules, SLA due time by priority. |
| `docs/product-specs/event-log.md` | `LOG` | The append-only event log: what is recorded, replay, the corrupt-line rule, where the log lives. |
| `docs/product-specs/cli.md` | `CLI` | The command surface: commands and arguments, output lines, error reporting, exit codes, log path selection. |

Plus the standard files: `docs/product-specs/invariants.md` (`INV`),
`docs/product-specs/README.md`, `docs/architecture.md`, `docs/guidelines.md`,
`docs/README.md`, and `AGENTS.md`.

## Unusual choices, flagged for you

1. **SLA folded into `tickets.md`.** `sla.py` is its own module, but it carries only three
   observable behaviors: the hours per priority, the due time, and the rejection of unknown
   priorities. Three items are below the 5-item floor for a spec file. I put them in
   `tickets.md` under the `TKT` prefix. If you expect SLA rules to grow (business hours,
   escalation), say so and I will split them out as `sla.md` with prefix `SLA`.
2. **The event log gets a spec file.** It is storage, which usually belongs in
   architecture. Here it is also user-visible: the log path is a CLI flag, the history is
   the product's promise in the README, and a corrupt line is a user-facing failure. The
   observable behavior goes in `event-log.md`. The design rationale goes in
   `architecture.md`.
3. **Invariants stay few.** I plan five: the log is the single source of truth, events are
   never edited or deleted, ticket IDs are never reused, corrupt data fails fast, and every
   event carries a timestamp. Everything else is feature-local and stays in the feature
   files as prose.

## Facts I could not find, and will mark as TODO

- No coverage target is stated anywhere. I will record "every module ships with tests" as
  the policy since that is what the repo does today, and mark the percentage as a TODO.
- No roadmap exists. The "current state" section of `AGENTS.md` will list what the code
  does and nothing about plans.

Reply with changes to granularity or prefixes. Otherwise I proceed in this order:
invariants, feature specs, specs README, architecture, guidelines, docs README, AGENTS.md.

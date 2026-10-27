# Proposal: agent docs for ticketdesk

Scope check before creating any files (skill step 2). Nobody is available to answer, so this
is written down and treated as approved.

## What I found

- **Product:** `ticketdesk` v0.3.0, a CLI help desk for a small support team. Tickets are
  created, assigned, and closed with a resolution note. Every change is one event appended to
  a JSON-lines log; ticket state is rebuilt by replaying the log.
- **Stack:** Python >= 3.11, standard library only (argparse, json, dataclasses, unittest).
  `make lint` (compileall) and `make test` (unittest discover); GitHub Actions runs both on
  Python 3.12. No existing docs beyond a 7-line README; no AGENTS.md, no `docs/`.
- **Layers:** `cli.py` (argparse front end) -> `tickets.py` (domain service, state derived by
  replay) -> `store.py` (append-only JSONL event store). `sla.py` is a pure lookup of due
  hours by priority.

## Feature spec files I will create

| File | Prefix | Covers | Est. specs |
|---|---|---|---|
| `docs/product-specs/tickets.md` | `TKT` | Ticket lifecycle: create, assign, close, lookup, listing, ID allocation, priorities and SLA due times | ~12 |
| `docs/product-specs/event-log.md` | `LOG` | The on-disk event log as a product surface: format, append-only, replay, corruption handling, missing file | ~7 |
| `docs/product-specs/cli.md` | `CLI` | Command-line contract: subcommands, `--log` / `TICKETDESK_LOG`, output lines, error reporting, exit codes | ~9 |

Plus the fixed layout: `docs/product-specs/invariants.md` (`INV`), `docs/product-specs/README.md`,
`docs/architecture.md`, `docs/guidelines.md`, `docs/README.md`, `AGENTS.md`.

## Choices worth flagging

1. **SLA folded into `tickets.md`, not its own file.** `sla.py` yields only three testable
   behaviours (hours per priority, due time = created + hours, unknown priority rejected).
   That is under the skill's 5-item floor for a spec file, and due time is a property of a
   ticket anyway. If SLA grows (escalation, breach reports), split it out as `sla.md` / `SLA`
   later; IDs in `tickets.md` would stay put (holes are allowed).
2. **The event log gets its own spec file.** It is tempting to call it "storage" and leave it
   to architecture, but the README sells "history is never lost" as a feature, the file path is
   user-chosen, and corruption behaviour is user-visible. That is product behaviour.
3. **Invariants (cross-cutting, `INV`):** log is the single source of truth; append-only;
   IDs never reused; fail fast on corruption; one command = one event; timestamps are
   assigned by the store, not the caller. Feature-local rules (e.g. "closed tickets cannot be
   assigned") stay in `tickets.md` as prose.
4. **One observed implementation gap, documented not fixed.** An unknown priority raises a
   `ValueError` that the CLI does not catch, so `ticketdesk create x --priority P9` prints a
   Python traceback instead of `error: ...` with exit 2. The spec will state the intended
   behaviour (uniform `error:` reporting) with a TODO naming the gap. No code is changed in
   this run.

## Proceeding as approved

Files are created in the skill's order: invariants -> feature specs -> product-specs README ->
architecture -> guidelines -> docs/README -> AGENTS.md. Nothing is committed.

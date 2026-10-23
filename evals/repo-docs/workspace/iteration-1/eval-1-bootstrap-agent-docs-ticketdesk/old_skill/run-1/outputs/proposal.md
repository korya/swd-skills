# Proposal: agent docs for ticketdesk

Written in place of the "confirm scope with the user" step (nobody available). Proceeding as if approved.

## What I found in the survey

- **Domain:** command-line help desk for a small support team. Tickets are created, assigned, closed; every change is one event in an append-only JSON-lines log, and ticket state is rebuilt by replaying it.
- **Stack:** Python >= 3.11, standard library only (argparse, json, dataclasses, unittest). Makefile wraps `compileall` (lint) and `unittest discover` (test). GitHub Actions runs both on Python 3.12. Version 0.3.0.
- **Layers:** `cli.py` (argparse, exit codes) -> `tickets.py` `TicketService` (domain rules) -> `store.py` `EventStore` (file I/O). `sla.py` is a pure priority -> due-time table used by the domain layer.

## Feature spec files I will create

| File | Prefix | Covers |
|------|--------|--------|
| `docs/product-specs/tickets.md` | `TKT` | Ticket lifecycle: create, assign, close, list; ID allocation; validation; priorities and SLA due times |
| `docs/product-specs/event-log.md` | `LOG` | The append-only log: one event per change, timestamps, replay, corrupt-line failure, file location |
| `docs/product-specs/cli.md` | `CLI` | Command surface: subcommands, arguments, output lines, exit codes, `--log` / `TICKETDESK_LOG` |

Plus `docs/product-specs/invariants.md` (`INV`), and the non-spec docs: `docs/architecture.md`, `docs/guidelines.md`, `docs/README.md`, `docs/product-specs/README.md`, `AGENTS.md`.

## Unusual choices

1. **SLA folded into `tickets.md`.** `sla.py` is its own module, but it yields only three or four testable behaviors (the priority list, the hours per priority, the default, rejection of unknowns). Below the 5-item floor for a file, and the behaviors are observable only through tickets. A separate `SLA` prefix can be split out later without renumbering `TKT` items (deletions leave holes).
2. **A `cli.md` spec.** The CLI is the product's only user surface, so output format and exit codes are product behavior, not implementation. It gets its own prefix.
3. **No `build-system` or `ci` spec.** No observable product behavior there; CI and Make targets are described in `architecture.md` and `guidelines.md`.

## Conflicts surfaced (not fixed; code is untouched)

- **Unknown priority error channel.** `TicketService.create` validates priority via `sla.due_at`, which raises `ValueError`, not `TicketError`. The CLI only catches `TicketError`, so `ticketdesk create x --priority P9` prints a Python traceback and exits 1, while every other validation failure prints `error: ...` and exits 2. The spec (`TKT`) states that the priority is rejected and no event is written, which is true today; `CLI-006` states the uniform `error:` / exit 2 contract and carries a TODO naming this divergence. Decide: fix the code (wrap in `TicketError`) or amend the spec.
- **Replay of an event for an unknown ticket id** (an `assigned` or `closed` line whose `id` was never `created`) raises a bare `KeyError`. Not specced; noted in `event-log.md` as a feature-local open question.

## Process rule placeholders I had to choose

- Coverage policy: the repo's README says "run `make test` before you push"; nothing states a percentage. I wrote "every behavior in a spec has at least one test; new logic ships with tests" rather than inventing a number.
- Lint today is `compileall` (a syntax pass, per the README). Guidelines say so plainly instead of pretending a linter exists.

## Final layout (shown for confirmation; proceeding as approved)

```
repo/
├── AGENTS.md                         112 lines  overview, stack, 30-second architecture, doc index, process rules, run commands
└── docs/
    ├── README.md                      57 lines  how docs/ is managed, spec format, when to update what
    ├── architecture.md                96 lines  three layers, assumptions, tech choices, v1 simplifications, migration paths
    ├── guidelines.md                  64 lines  lint/test policy, five-step planning checklist, 5-whys regression protocol
    └── product-specs/
        ├── README.md                  62 lines  format rules, prefix table, index
        ├── invariants.md    INV-001..008        source of truth, append-only, fail loud, stable ids, one change = one event, store-only I/O, stdlib only, doc confirmation
        ├── tickets.md       TKT-001..014        states, validation, ids, SLA due times, assign/close rules, listing + 2 prose contracts
        ├── event-log.md     LOG-001..008        line format, event shape, append semantics, missing file, blank lines, corrupt line, fresh read + 1 open question
        └── cli.md           CLI-001..010        subcommands, log path, per-command output, exit codes (TODO on CLI-008), int ids, entry points
```

Verification run: all relative links resolve; every cited `INV`/`TKT`/`LOG`/`CLI` ID exists; no duplicate IDs; no `**Testable:**` lines; no function/class/file names in spec bodies; `AGENTS.md` indexes every file under `docs/`; `product-specs/README.md` indexes every spec file. `git status` shows only `AGENTS.md` and `docs/` as untracked; no tracked file changed; `make test` still passes.

Deviations from the skill's definition of done, by necessity: the two user confirmations (scope, final layout) are recorded here instead of being answered by a person. Nothing committed.

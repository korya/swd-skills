# spec evals

Measures whether `/spec` writes a product spec a later skill can cite and a person can
read once. The fixture is the blueprint fixture: ticketdesk with agent docs, so the repo
already has a spec convention, invariants, and adjacent specs to respect.

## Layout

- `make_fixture.sh <dir>` delegates to `../blueprint/make_fixture.sh`.
- `evals.json` holds one eval in the skill-creator benchmark format.
- `check_run.py <run-dir>` grades the mechanical assertions.

## Traps in the fixture

| Trap | Tests |
|---|---|
| existing `docs/product-specs/README.md` with a prefix table and index | the repo's convention wins and both tables get updated |
| TKT-005 and TKT-013 already define due time and list order | amend without contradiction |
| INV-001 and INV-002, append-only log | overdue stays a derived state |
| `list` already has an output format (CLI-006) | the OVERDUE marker is specified against it |

## Running

Run with the skill-creator benchmark flow, old skill against new skill. Grade the prose
with `scripts/prose-lint.py`.

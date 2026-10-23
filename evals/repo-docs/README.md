# repo-docs evals

Measures whether `/repo-docs` produces agent docs a person can read once and an agent can
trust. The fixture is ticketdesk, a small CLI help desk with three natural feature areas
(tickets, SLA, event log) and one planted invariant: the event log is append-only and is
the single source of truth.

## Layout

- `make_fixture.sh <dir>` builds a disposable git repo at `<dir>` with one commit and no
  agent docs.
- `fixture/` is the project tree.
- `evals.json` holds one eval in the skill-creator benchmark format.
- `check_run.py <run-dir>` grades the mechanical assertions: files present, placeholders
  gone, ID format, cross-links, lint findings, untouched code.

## Traps in the fixture

| Trap | Tests |
|---|---|
| exact SLA hours and the 10-character resolution rule in code | specs match the code, not a guess |
| append-only JSON-lines log | the invariant is found and recorded as INV |
| no database, no web layer | the architecture doc does not invent one |
| templates full of `<placeholders>` and tip comments | every placeholder is replaced |
| nobody to confirm scope | the proposal is written out first, then followed |

## Running

Run with the skill-creator benchmark flow, old skill against new skill, three runs per
arm. Grade the mechanical assertions with `check_run.py` and the prose with
`scripts/prose-lint.py`.

# submit evals

Measures whether `/submit` produces commits and a PR description a person can read once.
The fixture is a small Python service with an uncommitted rework that has real trade-offs:
delivery success goes up, tail latency goes up, and heavy tenants get throttled.

## Layout

- `make_fixture.sh <dir> [fresh|existing-pr]` builds a disposable repo at `<dir>/repo`
  with a local bare `origin` at `<dir>/origin.git`. In `existing-pr` mode a feature branch
  with one pushed commit exists, and `<dir>/pr/` holds the stale PR title and body.
- `fixture/base/` is the initial commit. `fixture/change/` overlays the uncommitted work,
  including an untracked `.env`, a `scratch.py`, and an unrelated README typo fix.
- `evals.json` holds two evals in the skill-creator benchmark format.

## Traps in the fixture

| Trap | Tests |
|---|---|
| `.env` with a key, `scratch.py` | staging by filename, never `git add -A` |
| README typo fix | unrelated changes are separate commits |
| `docs/BENCHMARKS.md` with a regression in it | side effects, good and bad, with numbers |
| three staging tenants now throttled | who is affected, stated in the glance block |
| stale PR body claims the limiter is untouched | revalidation on re-invocation (5b) |

## Running

There is no GitHub in the sandbox, so the prompt tells the agent to write the PR title
and body to files instead of calling `gh`, and to stop at the CI phase. Run with the
skill-creator benchmark flow, old skill against new skill, three runs per arm. Grade the
prose assertions with `scripts/prose-lint.py` rather than by eye.

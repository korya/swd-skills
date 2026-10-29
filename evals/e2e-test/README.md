# e2e-test evals

Measures whether `/e2e-test` finds what is broken by using the product, not by reading
the code, and whether its report reads once. The fixture is ticketdesk with agent docs on
main and a branch that changes four behaviours. Three contradict the specs, and the PR
description presents all four as intended.

## Layout

- `make_fixture.sh <dir>` builds the repo at `<dir>` on branch `feature/cli-tidy`, with
  the base from `../blueprint/fixture` and the changes from `fixture/change/`.
- `evals.json` holds one eval in the skill-creator benchmark format.
- `check_run.py <run-dir>` grades the mechanical assertions.

## The four planted changes

| Change | Spec | Expected verdict |
|---|---|---|
| `close` accepts a 9-character note | TKT-010 says at least 10 | FAILURE |
| `assign` succeeds on a closed ticket | TKT-008 says refused | FAILURE |
| `list` drops the priority column | CLI-006 shows `[P1]` | FAILURE or UX gap |
| `--help` says "tikets" | none | UX gap |

The PR description claims all four are intended and that tests pass. A good run treats
the specs as the contract and reports the conflict.

## Running

Run with the skill-creator benchmark flow. Grade the prose with `scripts/prose-lint.py`.

## The evidence check

Assertion 14 checks that every quoted output came from the run. The grader compares each
block with the run's logs and transcript, and replays a doubtful block on a fresh copy of
the fixture. Earlier runs trimmed a repro and wrote the output they expected it to print.

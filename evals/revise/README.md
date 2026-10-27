# revise evals

Measures whether `/revise` judges review feedback instead of obeying it, and whether its
replies and report read once. The fixture is the acme-notify rework from `evals/submit`,
committed on a feature branch, with a six-finding review that needs six different answers.

## Layout

- `make_fixture.sh <dir>` builds `<dir>/repo` on branch `korya-retry-backoff`, a bare
  `<dir>/origin.git`, the PR body at `<dir>/pr/body.md`, and the review at
  `<dir>/review.md`. The code comes from `../submit/fixture`.
- `fixture/review.md` and `fixture/pr/body.md` are the texts the agent is shown.
- `evals.json` holds one eval in the skill-creator benchmark format.
- `check_run.py <run-dir>` grades the mechanical assertions.

## The six findings and the verdict each deserves

| ID | Finding | Verdict | Why |
|---|---|---|---|
| F1 | Retry-After date form raises ValueError | ACCEPT | real bug in the PR's own code |
| F2 | guard against negative rate | REJECT | theoretical: no writer produces the state |
| F3 | buckets are per process | DEFER | real, pre-existing, outside the PR's intent |
| F4 | docstring drift, plus a RetryPolicy hierarchy | PARTIAL | observation right, proposal oversized |
| F5 | move everything to asyncio | REJECT | preference and scope creep |
| F6 | cap 100 to 60, did product agree | NEEDS-INPUT | only the user knows |

## Running

No GitHub in the sandbox, so replies and the report go to files. Run with the skill-creator
benchmark flow, old skill against new skill. Grade the mechanical assertions with
`check_run.py` and the prose with `scripts/prose-lint.py`.

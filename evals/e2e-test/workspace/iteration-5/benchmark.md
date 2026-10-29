# Skill Benchmark: e2e-test, iteration 5

The skill with the claims rule, against the 16 earlier runs. The same grader scored all of
them and added assertion 15 for this iteration.

The change since iteration 4: `cases.md` says the PR's other claims are not evidence. An
unchecked claim is reported as unchecked and is never a premise. `report.md` lets a run
use the repo's own tests as diagnosis, never as a verdict. `writing.md` says an unchecked
claim is never a premise.

| | Runs | Checked the test claim | Drew a conclusion from it | Tokens per run, mean |
|---|---|---|---|---|
| Iterations 1 to 4 | 16 | 8 | 4 | 124k to 153k |
| With the claims rule (iteration 5) | 3 | 3 | 0 | 156.0k |

All three runs ran `make test`, saw 1 of 7 tests fail, and called the claim false. No run
let the test result set a verdict. Every quoted block still matches the run's evidence
log.

Runs 1 and 3 each fail assertion 10 once, on a FAILURE case with no most likely cause.
The score is 43 of 45.

One run installed the package with `pip install .`. That left untracked build files in the
product tree, though no tracked file changed.

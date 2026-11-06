# Skill Benchmark: blueprint, iteration 4

The cold read removes the major defects that a blind reviewer finds in a plan. It costs
about 119,000 tokens and 5.4 minutes per run. It does not move the 15 checks, which were
already at the ceiling.

**Evals**: 1, three runs per arm, both arms run in the same session on `claude-fable-5-1`.
`with_skill` is the skill with the cold-read step. `old_skill` is master at `3317167`. One
grader scored both arms.

The `with_skill` runs used the first brief, `evals/cold-read/briefs/paraphrase-first-a.txt`.
The brief that ships came later, see `evals/cold-read/workspace/iteration-1/benchmark.md`.

## Summary

| Metric | With the cold read | Master | Delta |
|--------|-------------------|--------|-------|
| Checks passed | 43 of 45 (96%) | 44 of 45 (98%) | -1 |
| Tokens per run, mean | 252,607 | 133,569 | +119,038 |
| of which the reader subagent | 99,077 | 0 | |
| Time per run, mean | 846 s | 525 s | +321 s |
| of which the reader subagent | 204 s | 0 | |
| Plan length, mean | 4,259 words | 3,638 words | +621 |

The three failed checks are unrelated to the cold read. Both `with_skill` failures are the
skim test, and both passages were already in the plan before the cold read. The `old_skill`
failure is a headline that never names the feature.

The token and time deltas overstate the cost in normal use. Each `with_skill` run also wrote
a record of the cold read for this eval: the prompt, the report, and a verdict table.

## What the cold read found

| Run | Findings | Blocker | Major | Minor | FIX | REJECT | ASK | Reader tokens | Reader time |
|-----|----------|---------|-------|-------|-----|--------|-----|---------------|-------------|
| 1 | 7 | 0 | 0 | 7 | 6 | 0 | 1 | 97,936 | 215 s |
| 2 | 5 | 0 | 0 | 5 | 4 | 0 | 1 | 101,066 | 212 s |
| 3 | 5 | 0 | 0 | 5 | 5 | 0 | 0 | 98,228 | 186 s |

The 17 findings fall into four groups:

- **Evidence that claimed more than the run showed.** A "working draft of all 8 cases" held
  6 tests. A "prototype of steps 2 to 5" skipped step 4. An output block left out a command.
- **Doc lines the change makes stale.** All three runs missed `AGENTS.md:47`.
- **Sign-off gaps.** A question asked approval for doc edits that had no proposed text.
  Three statements disagreed on which steps the sign-off gates.
- **Decisions left to the implementer.** The branch for `overdue`, the export of a new
  name, and which files to stage were not stated.

No author rejected a finding. Either every finding held, or the author defers to the
reader. The record does not separate the two.

## Blind residual review

A second reviewer, a fresh `claude-sonnet-5-5` session with the shipped brief, read each
plan without knowing its arm. One review per plan.

| Plan | Major findings, per run | Minor findings, per run |
|------|------------------------|------------------------|
| Master | 2, 0, 0 | 4, 8, 6 |
| With the cold read, before it ran | 3, 0, 1 | 5, 5, 7 |
| With the cold read, final | 0, 0, 0 | 9, 10, 6 |

The major findings went from 4 to 0 across the three plans. The minor findings did not
fall. A reviewer always finds some, and the plans grew by 7% to 14%.

## Limits

- Three runs per arm, one fixture, one review per plan in the residual table.
- The fixture is small and the author is strong. No run produced a Blocker to catch.
- A check for the cold read itself was added to `evals.json` after this iteration. The
  pass rates above cover the 15 older checks only.

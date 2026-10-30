# Skill Benchmark: spec

**Model**: claude-opus-5-5
**Date**: 2026-10-29
**Evals**: 1 (3 runs, one configuration)

## Summary

| Run | Score | Failed | Time | Tokens |
|---|---|---|---|---|
| 1 | 11 of 12 | 1 | 218.2 s | 101,180 |
| 2 | 12 of 12 | none | 194.9 s | 91,850 |
| 3 | 11 of 12 | 1 | 202.7 s | 93,755 |
| Total | 34 of 36 | | 205.3 s mean | 95,595 mean |

## Notes

This batch tests the first rule for the intro's first sentence. Step 4 says the first
sentence says what the feature does for its user. A definition comes after it, "even where
the repo's other specs open with one".

- **Assertion 11, the skim test.** All three runs pass it. Iterations 2 and 3 passed it in 1
  of 12 runs.
- **Assertion 1, the reason.** Runs 1 and 3 state the choice to create or amend with no
  reason. The first grading also failed run 2. A second pass found its reason in the
  transcript's Decisions section, so run 2 now passes.
- **A new file.** Runs 1 and 2 create `overdue.md`. Iterations 2 and 3 did so in 1 of 12
  runs.

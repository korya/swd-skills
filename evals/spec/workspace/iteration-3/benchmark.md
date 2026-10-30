# Skill Benchmark: spec

**Model**: <model-name>
**Date**: 2026-10-30T00:13:01Z
**Evals**: 1 (3 runs each per configuration)

## Summary

| Metric | With Skill | Old Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 92% ± 0% | 86% ± 5% | +0.06 |
| Time | 211.1s ± 38.1s | 210.0s ± 11.2s | +1.1s |
| Tokens | 92637 ± 4755 | 96228 ± 2689 | -3592 |
## Notes

This batch reruns iteration-2 with the same skills, fixture, and grader. Its purpose was to
check whether the skim test fails consistently.

- **Assertion 11, the skim test.** All six runs fail it. Over both batches, the old skill
  passes it in 1 of 6 runs and the cut skill in 0 of 6.
- **Both batches.** The old skill scores 65 of 72 and the cut skill 66 of 72.
- **The cause.** Every run opens its intro with a definition of "overdue". The fixture's own
  spec files open the same way, and the skill says the repo's convention wins.
- **A new file.** New run 2 is the only one of twelve runs that creates a spec file.

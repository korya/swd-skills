# Skill Benchmark: spec

**Model**: claude-opus-5-5
**Date**: 2026-10-29
**Evals**: 1 (3 runs, one configuration)

## Summary

| Run | Score | Failed | Time | Tokens |
|---|---|---|---|---|
| 1 | 12 of 12 | none | 239.3 s | 100,768 |
| 2 | 12 of 12 | none | 255.8 s | 95,492 |
| 3 | 12 of 12 | none | 201.4 s | 92,734 |
| Total | 36 of 36 | | 232.2 s mean | 96,331 mean |

## Notes

This batch keeps both sentences: the clause in step 4 and the reason in step 1. It is the
version this change ships.

- **Assertions 1 and 11.** All three runs pass both.
- **A new file.** No run creates one. All three amend `tickets.md` and `cli.md`.
- **Weak spots the grader noted.** None fails an assertion. Run 1 has a line break inside a
  sentence. Run 2 puts the goals at the criteria's heading level. Run 3 leaves its open
  questions under TKT-016 with no heading.

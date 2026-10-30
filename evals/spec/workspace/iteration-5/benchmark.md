# Skill Benchmark: spec

**Model**: claude-opus-5-5
**Date**: 2026-10-29
**Evals**: 1 (3 runs, one configuration)

## Summary

| Run | Score | Failed | Time | Tokens |
|---|---|---|---|---|
| 1 | 11 of 12 | 11 | 243.8 s | 97,406 |
| 2 | 12 of 12 | none | 206.9 s | 91,373 |
| 3 | 11 of 12 | 11 | 233.2 s | 97,631 |
| Total | 34 of 36 | | 228.0 s mean | 95,470 mean |

## Notes

This batch drops the clause "even where the repo's other specs open with one" from step 4.
It adds "Say which you chose, and why." to step 1.

- **Assertion 1, the reason.** All three runs give one.
- **Assertion 11, the skim test.** Runs 1 and 3 fail it again. They open with a definition,
  as the fixture's own specs do. Without the clause, the repo's convention wins.
- **A new file.** No run creates one. All three amend `tickets.md` and `cli.md`.

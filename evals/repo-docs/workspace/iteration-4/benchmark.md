# Skill Benchmark: repo-docs

**Model**: claude-fable-5-1
**Date**: 2026-10-29
**Evals**: 1 (3 runs, one configuration)

## Summary

| Run | Score | Failed | Time | Tokens |
|---|---|---|---|---|
| 1 | 13 of 14 | 9 | 465.7 s | 97,877 |
| 2 | 13 of 14 | 6 | 393.5 s | 92,429 |
| 3 | 14 of 14 | none | 394.5 s | 92,220 |
| Total | 40 of 42 | | 417.9 s mean | 94,175 mean |

## Notes

This batch runs the version that ships: the template change from iteration 3 plus the
step 3 rule in `SKILL.md`.

- **Assertion 14 passes in 3 of 3 runs**, 7 of 7 spec files. Every intro starts with the
  support agent: "A support agent runs `ticketdesk` from a shell to create, assign, close,
  and list tickets."
- **Run 1 fails assertion 9.** The specs README keeps the template's suffix example as
  `TKT-012A`, and the run's tickets spec ends at TKT-011. The template example is now
  `<XXX>-001A`, which resolves wherever a first criterion exists.
- **Run 2 fails assertion 6.** TKT-012 names the argparse module. The checker's word list
  does not hold that name, so the grader caught it and the checker did not.
- **The other 13 assertions** score 37 of 39, against 38 of 39 in iteration 3 and 36 of 39
  in iteration 2.

# Skill Benchmark: repo-docs

**Model**: claude-fable-5-1
**Date**: 2026-10-29
**Evals**: 1 (3 runs, one configuration)

## Summary

| Run | Score | Failed | Time | Tokens |
|---|---|---|---|---|
| 1 | 13 of 14 | 14 | 439.0 s | 103,087 |
| 2 | 14 of 14 | none | 404.7 s | 93,987 |
| 3 | 12 of 14 | 4, 14 | 580.0 s | 122,060 |
| Total | 39 of 42 | | 474.6 s mean | 106,378 mean |

## Notes

This batch tests the template change alone. The feature spec template and the specs README
ask for a first sentence that says what the feature does for its user. `SKILL.md` is the
1.3.0 file.

- **Assertion 14 is new.** It is the spec skim test: the first sentence of each feature
  spec starts with the user, not with a definition of the term. In iteration 2, 2 of 14
  spec files passed it, and no run passed it for every file.
- **Here 1 of 3 runs passes it.** Runs 1 and 3 still open a spec with a definition. The
  definition names the user but starts with the term: "The `ticketdesk` command is the one
  way a support agent works the help desk." The template alone moves 5 of 8 files.
- **Assertion 4 in run 3.** The run kept the docs README template's trigger row with
  `product-specs/<feature>.md` verbatim. The mechanical checker misses lowercase
  placeholders, and the grader read it as residue.
- **Model change.** Iteration 2 ran on claude-opus-5-5. This batch ran on claude-fable-5-1,
  so time and tokens are not comparable with iteration 2.

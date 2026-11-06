# Skill Benchmark: spec, iteration 7

The cold read finds real gaps in a spec, three of them product-level, and it doubles the
run. It does not move the 12 checks, which were already at the ceiling.

**Evals**: 1, three runs per arm, both arms run in the same session on `claude-fable-5-1`.
`with_skill` is the skill with the cold-read step and the shipped brief. `old_skill` is
master at `3317167`. One grader scored both arms.

## Summary

| Metric | With the cold read | Master | Delta |
|--------|-------------------|--------|-------|
| Checks passed | 35 of 36 (97%) | 36 of 36 (100%) | -1 |
| Tokens per run, mean | 227,671 | 107,828 | +119,843 |
| of which the reader subagent | 88,060 | 0 | |
| Time per run, mean | 753 s | 345 s | +408 s |
| of which the reader subagent | 181 s | 0 | |
| Words added to the specs, mean | 1,548 | 1,357 | +191 |
| Words per new criterion, per run | 59, 111, 113 | 56, 84, 55 | |

The one failed check is a teaser lead in `with_skill` run 3, "TODO: two assumptions need
the user." The line was in the spec before the cold read, so the cold read did not cause
it. `prose-lint.py` does not see a lead behind a `TODO:` prefix.

The token and time deltas overstate the cost in normal use. Each `with_skill` run also wrote
a record of the cold read for this eval: the prompt, the report, and a verdict table.

## What the cold read found

| Run | Findings | Blocker | Major | Minor | FIX | REJECT | ASK | Reader tokens | Reader time |
|-----|----------|---------|-------|-------|-----|--------|-----|---------------|-------------|
| 1 | 9 | 0 | 2 | 7 | 7 | 0 | 2 | 85,948 | 165 s |
| 2 | 13 | 0 | 0 | 13 | 12 | 0 | 1 | 91,213 | 193 s |
| 3 | 9 | 0 | 1 | 8 | 8 | 0 | 1 | 87,018 | 185 s |

The findings that changed the product contract:

- **Run 3 moved the marker.** The reader created a ticket titled "OVERDUE invoice from
  vendor". Its `list` line was the same as the line of an overdue ticket. The spec now puts
  the marker between the priority and the state.
- **Run 2 withdrew a claim.** The spec said a title cannot pass for the marker. The reader
  put a line break in a title and printed a false `OVERDUE` line.
- **All three runs named the clock.** No reader could say where "the current time" comes
  from. Each spec now states it or marks it open.
- **Runs 1, 2, and 3 fixed an intro that contradicted a criterion.** "Not closed when its
  due time passes" also fits a ticket closed late, which a criterion denies.

No author rejected a finding, the same as in blueprint iteration 4.

## Limits

- Three runs per arm, one fixture, no blind residual review for this skill.
- The specs grew. Two of three `with_skill` runs wrote criteria of about 110 words, where
  the skill asks for one to three sentences.
- A check for the cold read itself was added to `evals.json` after this iteration. The
  pass rates above cover the 12 older checks only.

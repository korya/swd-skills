# Skill Benchmark: revise

**Model**: <model-name>
**Date**: 2026-10-29T21:29:56Z
**Evals**: 1 (3 runs each per configuration)

## Summary

| Metric | With Skill | Old Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 100% ± 0% | 100% ± 0% | +0.00 |
| Time | 324.5s ± 40.6s | 315.0s ± 7.8s | +9.5s |
| Tokens | 110800 ± 5109 | 108856 ± 2757 | +1944 |
## Notes

The cut skill scores the same as the old one: 14 of 14 in all six runs. This eval no longer
separates the two arms, so a regression it cannot see stays possible.

- **Item 4 split.** Five runs, from both arms, split item 4 into ACCEPT for the docstring and
  REJECT for the hierarchy. One new run labelled it PARTIAL. Every run made the same one-line
  docstring fix and added no hierarchy.
- **Item 5.** All six runs DEFER the asyncio move with a ticket. The assertion allows it.
- **PR title.** The fixture has no PR title. Two old runs still wrote that the title "still
  covers the work". The other four said they could not check it.
- **Size.** The skill drops from 2,663 to 2,089 words, and SKILL.md from 6,681 to 4,731 bytes.
  Tokens per run change by 2%, within the spread.

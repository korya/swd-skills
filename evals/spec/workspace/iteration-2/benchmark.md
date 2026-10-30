# Skill Benchmark: spec

**Model**: <model-name>
**Date**: 2026-10-30T00:02:07Z
**Evals**: 1 (3 runs each per configuration)

## Summary

| Metric | With Skill | Old Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 92% ± 0% | 94% ± 5% | -0.03 |
| Time | 233.1s ± 24.9s | 216.2s ± 17.8s | +17.0s |
| Tokens | 99180 ± 8253 | 95483 ± 7884 | +3697 |
## Notes

The cut skill scores 33 of 36 against 34 of 36 for the old one. The gap is one run, on the
one assertion that fails in five of six runs.

- **Assertion 11, the skim test.** Five runs, from both arms, open the intro with a definition
  of "overdue", a status line, or the problem. Only old run 2 leads with what the feature
  does for a support agent. The cut did not touch the intro guidance in `format.md`.
- **Create or amend.** All six runs amend `tickets.md` and `cli.md`, and all six say why.
- **New criteria.** Old runs add 6, 8, and 5. New runs add 6, 6, and 7.
- **Invariants.** All six keep overdue derived and never logged. Only new run 3 cites INV-001
  and INV-002 by ID.
- **Size.** The skill drops from 1,267 to 1,126 words, and SKILL.md from 5,340 to 4,454 bytes.

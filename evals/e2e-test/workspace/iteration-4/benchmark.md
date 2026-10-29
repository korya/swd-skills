# Skill Benchmark: e2e-test, iteration 4

The skill with the evidence rule, against the 13 earlier runs. The same grader scored all
of them and checked every quoted block against the run's own logs.

The change since iteration 3: step 4 keeps an evidence log tagged by case. `report.md`
says the quoted output must come from exactly the steps shown, and a trimmed repro runs
again on fresh state before it is quoted. `writing.md` says quoted evidence is copied,
never written.

| | Runs | Runs with rewritten evidence | Assertions passed | Tokens per run, mean |
|---|---|---|---|---|
| 1.1.1 (iterations 1 and 2) | 5 | 2 | 38 of 39 in iteration 2 | 124.6k |
| The cut (iterations 2 and 3) | 6 | 4 | 77 of 78 | 123.8k |
| With the evidence rule (iteration 4) | 3 | 0 | 41 of 42 | 152.5k |

All 49 quoted blocks in iteration 4 match the run's evidence log. Two runs ran a trimmed
repro again before they quoted it. One run slipped and dirtied a shared log, logged the
slip, and quoted fresh runs instead.

The rule costs 23% more tokens than the cut and about 500 more words per report. Most of
the extra words are verbatim output blocks.

The failed assertion is run 1, assertion 10. Two FAILURE cases point at another case
instead of giving their own most likely cause.

The committed run files are the report, the evidence log, the transcript, the grading, and
the timing.

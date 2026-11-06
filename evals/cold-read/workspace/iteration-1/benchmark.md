# Cold-read benchmark, iteration 1

The shipped brief matches the naive control on recall and does not beat it. The brief finds
22 of 24 planted defects on the tuning plan and 18 of 18 on the held-out plan. The control
finds 23 of 24 and 18 of 18. The brief adds the request and the paraphrase at no cost in
recall.

**Runs**: 33 fresh headless reviewers on `claude-sonnet-5-5`, three per brief and plan, six
for the first variant on the tuning plan. Scored by hand against the tables in the README.

## Tuning plan, `plans/seeded-8.md`

| Brief | Runs | Defects found | Per run | S2, the design defect |
|---|---|---|---|---|
| `control.txt` | 3 | 23 of 24 | 8, 8, 7 | 3 of 3 |
| `paraphrase-first-a.txt` | 6 | 40 of 48 | 6, 6, 7, 7, 8, 6 | 3 of 6 |
| `paraphrase-first-b.txt` | 3 | 21 of 24 | 7, 7, 7 | 1 of 3 |
| `paraphrase-first-c.txt` | 3 | 22 of 24 | 7, 7, 8 | 1 of 3 |
| `no-paraphrase.txt` | 3 | 23 of 24 | 8, 8, 7 | 3 of 3 |
| `paraphrase-last.txt`, shipped | 3 | 22 of 24 | 8, 7, 7 | 3 of 3 |

## Held-out plan, `plans/seeded-6.md`

| Brief | Runs | Defects found |
|---|---|---|
| `control.txt` | 3 | 18 of 18 |
| `paraphrase-first-a.txt` | 3 | 18 of 18 |
| `paraphrase-first-b.txt` | 3 | 18 of 18 |
| `paraphrase-last.txt`, shipped | 3 | 18 of 18 |

The held-out plan does not separate the briefs. Every brief is at the ceiling on it.

## Cost per reviewer

| Brief | Runs | Cost, mean | Time, mean | Report, mean |
|---|---|---|---|---|
| `control.txt` | 6 | $0.25 | 98 s | 1,439 words |
| the three paraphrase-first briefs | 18 | $0.20 | 75 s | 997 words |
| `no-paraphrase.txt` | 3 | $0.20 | 47 s | 1,147 words |
| `paraphrase-last.txt`, shipped | 6 | $0.23 | 68 s | 1,262 words |

## Findings

- **A paraphrase before the review hides design defects.** The three paraphrase-first briefs
  found S2 in 5 of 12 runs, and two of those five were a passing mention. Every brief that
  reviews first found S2 as a finding, 9 of 9 runs. The reader restates the design, accepts
  it, and then checks only the details.
- **The paraphrase costs nothing at the end.** `paraphrase-last.txt` scores within one
  defect of `no-paraphrase.txt` and keeps the paragraph the author compares with the intent.
- **"Recompute every number and every example" helps S7.** The first variant found the
  arithmetic defect in 1 of 6 runs. The variants with that sentence found it in 8 of 12.
  The control found it in 2 of 3.
- **A strict evidence rule lowers recall.** The first variant reported about 9 findings per
  run and the control about 12. S2 sits near the bottom of the control's list.

## Limits

- One fixture, one model, three runs per cell. A difference of one defect is noise.
- The author of the briefs planted the defects and scored the reports.
- The tuning plan drove four revisions of the brief. Only the held-out plan is a fair test,
  and it is too easy to separate anything.
- The eval measures recall on planted defects. It does not measure the value of the
  paraphrase to the author, or the rate of false findings.

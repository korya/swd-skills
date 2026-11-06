# Cold-read benchmark, iteration 2

A brief that points the reader at the seam with the existing system finds no more than the
shipped brief. Every brief found every conflict with an existing spec. The reader's limit is
elsewhere: it reports about ten findings and then stops, so loud defects hide subtle ones. A
second read after the fixes caught the Blocker that one fix round introduced, 3 of 3. It
caught 2 of the 16 subtle defects that the first read had missed.

**Runs**: 28 headless sessions on `claude-sonnet-5-5`. Fifteen readers on `specs/seeded-9.patch`,
three on `specs/seeded-3.patch`, three authors, and seven second readers. Scored by hand
against the table in the README.

## Five briefs on the spec with nine planted defects

Three defects per class. D is a conflict with an existing spec, P a false claim about the
product, I a contradiction inside the draft. Three runs per brief.

| Brief | D, of 9 | P, of 9 | I, of 9 | Total, of 27 |
|---|---|---|---|---|
| `paraphrase-last.txt`, shipped | 9 | 6 | 3 | 18 |
| `seam-weighted.txt` | 9 | 6 | 5 | 20 |
| `seam-only.txt` | 9 | 7 | 3 | 19 |
| `product-probe.txt` | 9 | 9 | 3 | 21 |
| `paraphrase-last-plus-probe.txt` | 9 | 7 | 4 | 20 |

Every brief cost about $0.20 per run and took 60 to 110 seconds. The totals sit within
noise of each other at three runs per cell.

Five defects were found in every one of the 15 runs. They are D1, D2, D3, P2, and P3. I2
was found 14 times, P1 5 times, I3 4 times, and I1 never. The `product-probe.txt` brief
found P1 in 3 of 3 runs. The other four briefs found it in 2 of 12. That brief names "odd titles", which sits
close to P1.

## Crowding

The shipped brief read `specs/seeded-3.patch`, which holds only P1, I1, and I3.

| Defect | Among nine defects | Alone with two others |
|---|---|---|
| P1, a line break in a title forges an `OVERDUE` line | 0 of 3 | 3 of 3 |
| I3, "an assigned ticket always shows its state" | 0 of 3 | 2 of 3 |
| I1, the summary also fits a ticket closed late | 0 of 3 | 0 of 3 |

The number of findings per report does not show the crowding. Reports on the nine-defect
spec held 8 to 13 findings. Reports on the three-defect spec held 7 to 9. The real `/spec`
runs of iteration 7 held 9, 13, and 9. The Blocker count does separate them. Every read of
the nine-defect spec had 2 or 3, the three-defect spec had 0 or 1, and every real run had 0.

## The second read, end to end

Each chain starts from one first read with the shipped brief. An author session applies
"Use the result" from `assets/cold-read.md` and fixes the draft, see `author.sh`. Fresh
readers then read the fixed draft with the shipped brief.

| Chain | Author verdicts | Second read called | Planted defects left | Found by second reads |
|---|---|---|---|---|
| 1 | 10 FIX, 1 REJECT, 1 ASK | yes | P1, I1 | 0 of 6 |
| 2 | 11 FIX, 1 REJECT, 1 ASK | yes | I1 | 0 of 1 |
| 3 | 8 FIX, 0 REJECT, 1 ASK | yes | P1, I1, I3 | 2 of 9 |

The author of chain 1 broke the CLI-006 example while fixing it. The text says "when only
ticket 1 is overdue" above an output that shows two overdue tickets. All three second reads
of that draft reported it as a Blocker. The second readers spent most of their findings on
items the authors had moved to the open questions, such as `OVERDUE` replacing the state.

The author sessions were fresh Sonnet sessions with the reader's report, not the session
that wrote the draft. Two of them rejected a finding with a file and a line. No author in
the iteration-7 and iteration-4 skill runs rejected any finding. The fixed drafts grew by
8% to 13%.

A second read cost $0.24 and 76 seconds on average. The trigger, a Blocker with the verdict
FIX, fired in all three chains and would have fired in none of the six real skill runs.

## What changed in `assets/cold-read.md`

The brief did not change. Step 4 of "Use the result" is new. A Blocker with the verdict FIX
gets one more cold read after the fixes, and the loop stops there. Its reason is the fix
round, not the crowding. The crowding relief that the three-defect spec showed did not
survive a real fix round.

## Limits

- One fixture, one model, three runs per cell. A gap of one or two defects is noise.
- The author of the briefs planted the defects and scored the reports.
- I1 was never found in 25 opportunities. It may be a weak plant rather than a blind spot.
- The real authors of iteration 7 ran the product before writing, in 5 of 6 runs. The
  product-level finds of their cold reads were one step past where the author stopped. They
  were not cases the author never tried.

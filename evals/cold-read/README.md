# cold-read evals

Measures whether the brief in `assets/cold-read.md` makes a fresh reader find the defects
in a plan or a spec. The fixture is the blueprint fixture, ticketdesk with agent docs. Each plan is a
real `/blueprint` output with defects planted by hand, so the answer key is exact.

## Layout

- `plans/seeded-8.md` is the tuning plan with eight planted defects.
- `plans/seeded-6.md` is the held-out plan with six planted defects of other kinds.
- `briefs/paraphrase-last.txt` is the brief that ships. It is the text in `assets/cold-read.md`.
- `briefs/control.txt` is a naive prompt of three sentences. It is the bar to beat.
- `briefs/` also holds the rejected variants, kept so a rerun can reproduce the comparison.
- `specs/seeded-9.patch` is a real `/spec` output with nine planted defects, as a `git diff`
  against the fixture. `specs/seeded-3.patch` keeps three of them. `specs/plant.py` builds
  both from `specs/base.patch`.
- `run.sh <brief> <plan> <out-dir>` runs one fresh headless reviewer on a plan and saves
  `report.md`. `run-spec.sh <brief> <patch> <out-dir>` does the same on a spec.
- `author.sh <report> <patch> <out-dir>` runs one author session that applies "Use the
  result" to a spec and saves the fixed draft as `after.patch`.
- `workspace/iteration-N/` holds the reports and the benchmark.

## Planted defects

`plans/seeded-8.md`:

| ID | Defect | Found only by |
|---|---|---|
| S1 | The test plan uses pytest and cites `AGENTS.md:22-23` for it. The repo uses unittest. | reading the cited file |
| S2 | The CLI reads `time.time()`. The architecture puts time behind the store's clock. | a design judgment against `docs/architecture.md` |
| S3 | A second hours table, `OVERDUE_HOURS`, with P3 at 48. `sla.py` says 72. | reading `ticketdesk/sla.py` |
| S4 | The code uses `>=`. The plan's own spec text says "later than". | the document alone |
| S5 | The new spec ID `CLI-009` already exists. | reading `docs/product-specs/cli.md` |
| S6 | The plan says the subparsers are not marked required. `cli.py:14` marks them. | reading the code |
| S7 | The example in assumption A4 claims the order `[2, 1]`. The arithmetic gives `[1, 2]`. | recomputing the example |
| S8 | The sort key is `created_at`. The spec and the request say due time. | the document and the request |

`plans/seeded-6.md`:

| ID | Defect | Found only by |
|---|---|---|
| H1 | The formatter repeats the overdue rule in the CLI. The CLI holds no ticket rules. | a design judgment against `docs/architecture.md:36-38` |
| H2 | The plan reads `self.store._clock()`. The attribute is the public `clock`. | reading `ticketdesk/store.py` |
| H3 | The tie-break test moves the clock 12 hours. A tie needs 20. | recomputing the example |
| H4 | The spec text exits with code 1 on an empty result. The test plan and CLI-008 say 0. | the document and `cli.md` |
| H5 | The plan says `AGENTS.md:93` limits sign-off to product specs. It covers every doc. | reading the cited file |
| H6 | `is_overdue` has no closed check. The spec text and the tests require one. | the document alone |

`specs/seeded-9.patch`, three defects per class:

| ID | Defect | Found only by |
|---|---|---|
| D1 | CLI-012 skips a corrupt log line. INV-004 and LOG-007 forbid it. | reading `invariants.md` or `event-log.md` |
| D2 | CLI-010 prints a note to stderr on success. CLI-008 forbids it. | reading the rest of `cli.md` |
| D3 | CLI-006 puts overdue tickets first. TKT-013 and its own first sentence say ID order. | reading the existing text |
| P1 | "Every line with `OVERDUE` in the state position is one overdue ticket." A line break in a title forges one. | running the product |
| P2 | The example `ticketdesk overdue --log desk.jsonl`. The product takes `--log` only before the command. | running the product or reading `cli.py` |
| P3 | "The log stamps events in whole seconds." It stamps fractions. | running the product or reading `store.py` |
| I1 | "A ticket that was not closed by its due time shows as `OVERDUE`" also fits a ticket closed late. TKT-015 denies it. | the document alone |
| I2 | The TKT-019 example says a ticket created 80 hours ago was due 1 hour ago. 80 minus 72 is 8, and the order flips. | recomputing the example |
| I3 | "An `assigned` ticket always shows its state." TKT-016 says an assigned ticket can be overdue. | the document alone |

`specs/seeded-3.patch` holds P1, I1, and I3 only.

A report scores a defect when it names the defect as a finding. A mention inside another
finding scores too. Every plan also cites scratch scripts that are not in the fixture. Each
reviewer reports them. That finding is an artifact of the setup and is not scored.

## Running

```bash
evals/cold-read/run.sh evals/cold-read/briefs/paraphrase-last.txt \
  evals/cold-read/plans/seeded-8.md /tmp/cold-read-run-1
```

For a spec:

```bash
evals/cold-read/run-spec.sh evals/cold-read/briefs/paraphrase-last.txt \
  evals/cold-read/specs/seeded-9.patch /tmp/cold-read-spec-1
evals/cold-read/author.sh /tmp/cold-read-spec-1/report.md \
  evals/cold-read/specs/seeded-9.patch /tmp/cold-read-chain-1
evals/cold-read/run-spec.sh evals/cold-read/briefs/paraphrase-last.txt \
  /tmp/cold-read-chain-1/after.patch /tmp/cold-read-chain-1/read2
```

Run each brief three times on each document. Score the reports by hand against the tables
above. A change to the brief in `assets/cold-read.md` must not score below the control.
Plant at most about three subtle defects in one document. A reader reports about ten
findings and then stops, so loud defects hide the subtle ones, see iteration 2.

# Skill Benchmark: e2e-test, iteration 3

The shortened skill after one restored sentence, against the 1.1.1 runs of iteration 2. One
grader scored all nine runs on the same 13 assertions.

The change since iteration 2: step 2 names the three case sources again. They are the spec
criteria, each changed behavior with a happy path, an edge, and an error path, and the
blast radius.

| | 1.1.1 (iteration 2) | Shortened (iteration 2) | Shortened (iteration 3) |
|---|---|---|---|
| Assertions passed | 38 of 39 | 39 of 39 | 38 of 39 |
| Cases per run | 44, 36, 50 | 33, 36, 38 | 38, 51, 40 |
| Report words per run, mean | 2,560 | 2,468 | 2,756 |
| Tokens per run, mean | 124.6k | 118.4k | 129.1k |
| Time per run, mean | 402 s | 403 s | 491 s |

Every run found the four planted defects through the CLI, said no-go, and changed no
product file. Each failed assertion is a single run:

- **1.1.1, run 1.** The `--help` typo FAILURE has no most likely cause.
- **Iteration 3, run 1.** The run read `--help` before it wrote the case list.

The grader noted two problems the assertions do not check, in both versions:

- **Rewritten evidence.** At least four of nine reports show ticket IDs, paths, or `list` output
  that the run never produced, and do not say so.
- **The PR's test claim.** Four of nine runs ran `make test` and caught the false "All
  tests pass locally". None of the iteration-3 runs did.

The committed run files are the report, the transcript, the grading, and the timing. The
logs and scratch files the runs created stay out, because one of them is 32 MB.

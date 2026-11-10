# Drift benchmark, iteration 1

`/drift` finds every planted drift on the fixture and reports none on a clean one. As a
step inside `/repo-docs`, it removes the criteria no tester can check, at no extra time
once the reader runs on a smaller model.

**Runs**: headless `claude-sonnet-5-5` and `claude-haiku-5-5` sessions for the skill alone.
Five `/repo-docs` authors on `claude-fable-5-1` for the chain. One run per cell unless the
table says otherwise. Scored by hand against the README.

## The skill alone, on the planted fixture

| Reader | Runs | Plants found | False DRIFT | BLOCKED, OPEN | Cost | Time |
|---|---|---|---|---|---|---|
| Sonnet | 2 | 4 of 4, 4 of 4 | 1, 0 | correct | $0.48 | 140 s |
| Haiku | 2 | 4 of 4, 4 of 4 | 0, 0 | correct | $0.12 to $0.20 | 210 to 263 s |
| Sonnet, clean fixture | 1 | none to find | 0 | 2 BLOCKED, 1 OPEN | $0.47 | 139 s |

Every run also reported the undocumented `count` subcommand. The one false DRIFT scored
TKT-003 for a traceback that a TODO under CLI-007 already names. The OPEN rule in
`verdicts.md` now counts a TODO elsewhere in the spec set that names the criterion.

## `/repo-docs` followed by `/drift`

Each author wrote specs for ticketdesk from the code alone, with the agent docs removed.

| Run | Step in the skill | Total time | Drift reader | DRIFT | BLOCKED | Criteria, before and after |
|---|---|---|---|---|---|---|
| 1 | none, drift run afterwards | 5 min | Sonnet, headless | 1 | 4 | 29 |
| 2 | none, drift run afterwards | 5 min | Sonnet, headless | 0 | 2 | 29 |
| 3 | first version, sequential | 17 min | the author's model | 1 | 0 | 24 to 26 |
| 4 | drift in the background | 14 min | the author's model | 3 | 0 | 22 to 32 |
| 5 | background, smaller reader, UNCOVERED rule | 4.5 min | Sonnet | 0 | 0 | 21 to 22 |

The DRIFT and BLOCKED columns of runs 3 to 5 are what the author's own drift reported.

- **Without the step, false and untestable criteria shipped.** Run 1 claimed that exit
  status 1 has one source, and a corrupt log is a second. Runs 1 and 2 wrote 6 criteria
  about a due time and an assignee that no command shows.
- **With the step, BLOCKED went to 0 in all three runs.** The authors put the due-time
  table in `architecture.md` instead of a criterion.
- **A fix round can break a neighbour.** In run 3 the author changed TKT-012, and an
  independent drift then found TKT-015 in conflict with it. The step now ends with a
  reread of the changed criteria against each other.
- **UNCOVERED items inflated the spec.** In run 4 the author turned 6 of 8 into criteria,
  most of them crash paths. The event-log spec grew from 7 criteria to 15. The step now
  sends a crash, a traceback, or a mishandled input to the questions. Run 5 grew by 2%.
- **The reader's model sets the time.** The drift took 4 to 10 minutes on the author's
  model and 2.5 minutes on Sonnet. The author of run 5 chose Sonnet after reading the
  "Running as a subagent" section of `/drift`.

An independent drift on the final specs of run 5 agreed with the author's: 0 DRIFT, 0
BLOCKED, 1 OPEN.

## Limits

- One fixture, and one run per variant of the step. The timings are rough.
- Run 5 had no DRIFT to fix, so it did not exercise the fix path or the reread.
- The speed of run 5 needs a host that lets a skill choose a smaller model for a subagent.
- The planted drifts and the scoring are by the author of the skill.
- The skill-creator benchmark of `evals.json` with three runs per arm has not run yet.

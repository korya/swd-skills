# Verdicts: one per criterion

Loaded from `SKILL.md` step 3, before the case list, so every case is written with its
verdict rule in mind. There is no change under test, so the words of `/e2e-test` do not
fit. A mismatch is not a failure of a change. It is a gap between two things the project
keeps, and the user decides which one moves.

## The four verdicts

Every criterion ends in exactly one.

- **MATCH.** Every case derived from the criterion showed the promised outcome at the
  surface, this run.
- **DRIFT.** The product did something the criterion forbids, or lacked something it
  promises. One failed case makes the criterion DRIFT, however many passed.
- **BLOCKED.** No product surface lets you observe the behaviour, or the environment
  stopped the run. Name the observation that would settle it, such as "a command that
  prints the due time". A criterion you suspect is fine but could not observe is BLOCKED,
  never MATCH.
- **OPEN.** The criterion's own text carries a TODO or an unconfirmed assumption about
  the part you would test. A TODO elsewhere in the spec set that names this criterion
  counts too. Quote the TODO. The settled part of the criterion may still get cases, and a
  failed one makes it DRIFT.

## The one rule

A verdict never comes from reading code. Code, logs, and the repo's tests may explain a
DRIFT after the surface showed it, and the report may say so under "most likely cause".
They never turn a BLOCKED into a MATCH, and they never produce a DRIFT the surface did
not show.

## Evidence per verdict

- **DRIFT:** the exact command or action, the exact output, and the sentence of the
  criterion it contradicts, quoted. The output comes from the evidence log, produced by
  exactly the steps shown.
- **BLOCKED:** what was tried, and the observation that is missing.
- **OPEN:** the TODO, quoted, and the verdict of the settled part if it had cases.
- **MATCH:** the command run and what was observed, in one table cell. Enough for a
  reader to rerun it.

## Deriving cases from a criterion

A case is one scenario with an outcome you can state before running it. For most
criteria, three cases cover it: the documented flow, a boundary or empty state, and the
error path. Recompute every number and example in the criterion rather than trusting it.
When a case needs existing state, creating that state through the surface is part of the
case. When the product writes a file that the specs declare a product surface, reading
the file is part of the surface.

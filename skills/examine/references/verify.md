# Verify and sweep

Loaded from `SKILL.md` step 7. Candidates become findings only after this pass. The reviewer
who found a candidate is the worst-placed judge of it.

## Dedup first

Candidates that point at the same line or mechanism collapse into the one with the most
concrete failure scenario. A single root cause with many symptoms is one finding with a
`flow:` locator, not several findings.

## The verdict rubric, three states

- **CONFIRMED.** You can name the inputs or state that trigger it and the wrong output or
  behavior that results. Quote the line that proves it.
- **PLAUSIBLE.** The mechanism is real. The trigger is uncertain: timing, environment, data
  shape.
- **REFUTED.** Only when constructible from the code. The candidate is factually wrong, and
  you quote the actual line. Or it is provably impossible by a type, a constant, or an
  invariant, and you show it. Or this diff already handles it, and you cite the guard. Or it
  is pure style with no observable effect.

**PLAUSIBLE by default.** Do not refute a candidate for being "speculative" or "depends on
runtime state" when the state is realistic. Realistic but rare is what production is made
of. Refutation is a proof obligation, not a mood. Realistic states include:

- concurrency races
- nil or undefined on a rare but reachable path: an error handler, a cold cache, a missing
  optional field
- falsy zero treated as missing
- an off-by-one on a boundary the code does not exclude
- retry storms and partial failures
- a regex or allowlist slightly too broad

## Mechanics

- **Host has subagents:** one verifier per candidate. Give it only the diff, the relevant
  files, and the candidate. Withhold your reasoning, so it cannot anchor on it.
- **No subagents:** verify each candidate yourself in a deliberately adversarial re-read. Try
  to REFUTE it from the code. What survives is CONFIRMED or PLAUSIBLE. State in the report
  that verification was single-context.
- **Keep CONFIRMED and PLAUSIBLE.** They get a severity (impact) and carry their verdict into
  the report's `Verdict` field. REFUTED candidates move to the **Verified** section with the
  disproving citation. The check was work worth showing.
- Low candidates and Suggestions may skip verification. They are cheap for the author to
  decline.
- **Occam candidates** verify differently. The "failure scenario" is the concrete cost: what
  is duplicated, operated, or will be copied. A refutation is the constraint that justifies
  the complexity, cited.

## Gap sweep

After verification, make one more pass as a fresh reviewer holding the surviving list.
Re-read the diff and the enclosing functions looking only for defects not already listed. Do
not re-derive or re-confirm anything on the list. First passes tend to miss:

- moved or extracted code that dropped a guard or an anchor
- lock scope silently shrunk
- config or feature-flag defaults flipped
- setup and teardown asymmetry in tests
- predicate methods with side effects
- a default value evaluated once at definition time instead of per call

New candidates from the sweep go through the same verdict rubric. If nothing new turns up,
the sweep returns empty. Do not pad.

# Verify and sweep

Loaded from `SKILL.md` step 7. Candidates become findings only after this pass. The reviewer
who found a candidate is the worst judge of it.

## Dedup first

Candidates on the same line or mechanism merge into the one with the most concrete failure
scenario. One root cause with many symptoms is one finding with a `flow:` locator.

## The verdict rubric

- **CONFIRMED.** You can name the triggering input or state and the wrong result. Quote the
  line that proves it.
- **PLAUSIBLE.** The mechanism is real, but the trigger depends on timing, environment, or
  data shape.
- **REFUTED.** Only with proof from the code. The claim is factually wrong, or a type or
  invariant makes it impossible. Or the diff already guards it, or it has no observable
  effect. Quote the line.

**PLAUSIBLE is the default.** Never refute a candidate for being speculative when its state
is realistic. Races, rare error paths, cold caches, falsy zeros, and partial failures are
what production is made of.

## Mechanics

- **With subagents:** one verifier per candidate. Give it only the diff, the relevant files,
  and the candidate. Withhold your reasoning so it cannot anchor on it.
- **Without subagents:** try to refute each candidate yourself in an adversarial re-read.
  Say in the report that verification was single-context.
- CONFIRMED and PLAUSIBLE candidates keep their verdict into the report. REFUTED ones move
  to Verified with the disproving citation.
- Low candidates and Suggestions may skip verification.
- An Occam candidate's failure scenario is its concrete cost. Its refutation is the cited
  constraint that justifies the complexity.

## Gap sweep

Then make one pass as a fresh reviewer, looking only for defects not on the list. Look
hardest at what moved: code moved or extracted without its guard, a lock scope that shrank, a
default that flipped. New candidates go through the same rubric. An empty sweep is a valid
result. Do not pad.

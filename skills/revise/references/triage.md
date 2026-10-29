# Triage: cross-validation and verdicts

Loaded from `SKILL.md` step 2. Every finding is tested before it is believed.

## Decompose before judging

A finding is one claim plus one proposal that can be judged on its own. "This handler
ignores errors, and the whole module should use the Result pattern" is two findings with
two verdicts. Keep the reviewer's words on each, so the reply can quote what it answers.

## Cross-validate every claim

List what each finding asserts about the code's behavior, a requirement, a risk, or a
convention. Check each assertion:

- **Against the code on `HEAD`.** Read the lines the finding talks about. Run the
  two-minute experiment when behavior is disputed. Reviewers work from diffs and memory.
  The code is the arbiter.
- **Against the design and specs.** A finding that appeals to "the architecture" or "the
  requirements" gets the doc opened and the passage found, or the appeal is marked
  unfounded.
- **Against the repo's conventions.** Find the convention in the repo's docs or its
  dominant pattern, or drop the claim.
- **Against the PR's intent.** The description, the linked issue, or the plan defines what
  this PR is for. A finding can be correct and still belong to a different PR.

Record evidence per assertion: `file:line`, a quoted doc passage, or experiment output. A
load-bearing claim you cannot validate either way makes the finding NEEDS-INPUT. Prose with
no checkable claim is opinion. If argument quality is all a finding has, it is a REJECT
with the missing evidence named.

## The scope fence and the optimization test

Even a valid proposal is not automatically implemented. Ask, in order:

1. **Does the current code violate anything?** A guideline, a security or architectural
   constraint, a spec requirement, a correctness property. No violation means there is no
   defect, only a preference. REJECT or DEFER, never a code change.
2. **Is it this PR's problem?** Inside the stated intent, it is eligible. Outside, DEFER with
   a ticket draft, however real it is. Pre-existing issues the diff merely exposes are DEFER
   by default.
3. **Is the proposal the simplest fix?** If the observation is right but the proposal is
   oversized, that is PARTIAL. A pattern rewrite where a guard clause does, or an
   abstraction for one caller, are oversized. Fix the problem, decline the ceremony, say so.
4. **Is it practical or theoretical?** Optimizations for loads that do not exist, races that
   cannot occur in this deployment, generality nobody asked for: premature. REJECT with the
   reasoning, or DEFER with a ticket if the day may realistically come. Some guards are
   theoretical too. A guard for inputs the type system, the call graph, or a single trusted
   writer already excludes is one. A fallback that masks a failure the same path already
   surfaces is another. Failing loud there is correct. The carve-out is a trust boundary,
   where defensive code is required.

## NEEDS-INPUT and the counts

NEEDS-INPUT is a holding state, not a verdict. Use it when the decision needs knowledge
only the user has, such as priorities, product intent, or deployment reality. Batch the
questions, ask once, and wait.

A run that accepts everything or rejects everything is suspicious. Re-check whichever
direction came too easily.

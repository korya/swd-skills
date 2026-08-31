# Triage: cross-validation and verdicts

Loaded from `SKILL.md` step 2. This is where the skill earns its keep: the difference
between revising and obeying is that every finding is tested before it is believed.

## Decompose before judging

A finding is one claim-plus-proposal that can be judged on its own. Reviewers bundle:
"this handler ignores errors, and while you're at it the whole module should use the
Result pattern" is two findings with two verdicts. Split them; give each an ID; keep the
reviewer's original wording attached so the response can quote what it answers.

## Cross-validate every claim

Inside each finding, list what is being *asserted* — about the code's behavior, about a
requirement, about a risk, about a convention — and check each assertion:

- **Against the code on `HEAD`.** Read the actual lines the finding talks about; run the
  two-minute experiment when behavior is disputed. Reviewers work from diffs and memory;
  the code is the arbiter.
- **Against the design and specs.** A finding that appeals to "the architecture" or "the
  requirements" gets the doc opened and the passage found — or the appeal marked
  unfounded. Cite what you find, either way.
- **Against the repo's conventions.** "We don't do it this way here" is checkable:
  find the convention in the repo's docs or its dominant pattern, or drop the claim.
- **Against the PR's intent.** The description, linked issue, or plan defines what this
  PR is for. A finding can be entirely correct and still belong to a different PR.

Record evidence per assertion (`file:line`, quoted doc passage, experiment output).
A finding whose load-bearing claim cannot be validated either way is NEEDS-INPUT
territory, not a coin flip. Well-argued prose with no checkable claim is opinion —
weigh it as such and say so.

## The scope fence and the optimization test

Even a *valid* proposal is not automatically implemented. Ask, in order:

1. **Does the current code violate anything?** A guideline, a security or architectural
   constraint, a spec requirement, a correctness property. No violation → there is no
   defect, only a preference — REJECT or DEFER, never a code change.
2. **Is it this PR's problem?** Inside the stated intent → eligible. Outside → DEFER
   with a ticket draft, however real it is. Pre-existing issues the diff merely exposes
   are DEFER by default.
3. **Is the proposal the simplest fix?** We always want the simplest solution satisfying
   all constraints. If the observation is right but the proposal is oversized — a
   pattern rewrite where a guard clause does, an abstraction for one caller — that is
   PARTIAL: fix the problem, decline the ceremony, say so.
4. **Is it practical or theoretical?** Optimizations for loads that don't exist, races
   that can't occur in this deployment, generality nobody asked for: premature. REJECT
   with the reasoning, or DEFER with a ticket if the day may realistically come.

## Verdict discipline

- One verdict per finding: ACCEPT, PARTIAL, REJECT, or DEFER — each with its evidence
  and a one-paragraph justification a skeptical reviewer would accept as engaged-with.
- **NEEDS-INPUT is a holding state, not a verdict**: use it when the decision needs
  knowledge only the user has (priorities, product intent, deployment reality) or when
  validation genuinely came up empty. Batch the questions, ask once, wait. Guessing a
  verdict to avoid asking is how wrong changes get made politely.
- Well-argued is not a tiebreaker. If argument quality is the only thing a finding has
  going for it, the verdict is REJECT with the missing evidence named.
- Track verdict counts honestly; a run that accepts everything or rejects everything is
  suspicious — re-check whichever direction came too easily.

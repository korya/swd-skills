# The plan: counterfactual, structure, definition of done

Loaded from `SKILL.md` step 8.5. Covers the success-criteria counterfactual, the plan
document's structure, and the definition of done. The plan follows `../../assets/writing.md`
and passes `prose-lint.py` before it is presented.

## 8.5. Counterfactual: does the plan satisfy the success criteria?

Close the loop between the goal (step 1) and the plan about to be written. For each success
criterion stated in step 1, name the plan steps that satisfy it. Land on one of:

- **Confirmed.** Every criterion is satisfied by at least one plan step. Cite which.
- **Confirmed with gaps.** Some criteria need follow-up work or out-of-band steps. List them
  and surface them as open questions or out of scope.
- **Unconfirmed.** At least one criterion has no plan step that satisfies it. Stop. Either
  extend the plan or descope the criterion with the user's agreement.

A plan whose success criteria do not all map to plan steps is a list of activities, not a
plan.

## 9. Write the plan

The structure is an inverted pyramid:

1. **Headline.** At most three sentences, one fact each, that a reader with no context
   understands. What we are building. Why this approach over the obvious alternative. The
   single blocker or decision that stands in the way, if one exists. The word cap on
   sentences is not a reason to add a fourth.
2. **Approach summary.** Three to ten sentences of plain prose, not bullets. It gives the
   high-level design: the components it touches and how they interact, and what stays
   untouched. It names the one or two assumptions the whole approach stands on. It names the main
   trade-off that shaped it: what was given up and why. This is the go/no-go gate. A reader
   who finishes it either stops, because the approach is wrong for them, or accepts its
   shape. Then they check the details. High level, not a novel, and at most ten
   sentences. The full assumption list and the alternatives considered live in the
   sections below.
3. **Out of scope.** What we are explicitly not doing. It comes right after the approach so
   the boundary is read together with the shape, and to prevent scope drift later.
4. **Plan.** Ordered, concrete steps with file paths and the specific changes per step.
5. **Assumptions validated.** A bullet list with the evidence: `file:line` citation,
   experiment result, doc link.
6. **Test plan.** Unit, integration, e2e, manual. What each covers and which scenarios.
7. **Risks and mitigations.** What could still go wrong after the tests pass, and what we
   will do if it does.
8. **Open questions.** Anything the user still needs to decide before implementation. Last,
   so the reader arrives with the whole picture. A question that blocks the plan is also
   named in the headline.

The headline and the approach summary are written for a human skimming the plan, not for
the model executing it. Full sentences, named things, no shorthand or step numbers that only
make sense after reading the rest. The cryptic version of a plan is the one nobody can
review.

Keep the plan as long as it needs to be and no longer. A plan that nobody reads is worse
than one that is slightly too short.

## Definition of done

The skill is complete when all of these are true. Each item is answerable with evidence, not
a vibe.

- [ ] Problem statement restated: goal, constraints, non-goals, success criteria.
  Ambiguities resolved with the user, not invented.
- [ ] Hypothesis stated specifically enough to be falsifiable, with named files, APIs, and
  flows. A disconfirming observation is written down: what would prove the hypothesis
  itself wrong, not just its individual assumptions.
- [ ] Every load-bearing assumption carries an evidence tag: a `file:line` citation, a
  quoted doc passage, a script's output, or a query result. No bare "plausible" or
  "unverified" tag survives into the final plan.
- [ ] Spec cross-validation done. Each affected requirement is named, and the plan line that
  satisfies it is named. Invariants explicitly checked, or a documented deviation flagged
  for user sign-off.
- [ ] Architecture cross-validation done. Any deviation is called out, not silent.
- [ ] Project-conventions cross-validation done. Each universal category is enumerated with
  `file:line` citations inside the plan. Each bullet links to the plan step it shapes, or is
  marked "Doesn't constrain this plan" with a reason. The categories are root and
  per-component conventions, package manager, and build, test, and run entry points. They
  continue with test framework and mocking policy, lint and format, and migration tooling
  if schema is touched. They end with ports and URLs, async machinery if relevant, and reuse
  patterns. No defaults from training data, yours or the population's.
- [ ] Codebase conflict sweep performed: in-flight work, shadow duplication, caller-side
  drift if signatures or schemas change, and test-infrastructure gaps. Findings are
  reflected in the plan. File-existence and signature checks live in the assumption list,
  not here.
- [ ] Plan-against-success-criteria counterfactual recorded as **Confirmed**, **Confirmed
  with gaps** (gaps listed), or **Unconfirmed**. Unconfirmed means the plan is not ready.
- [ ] The plan document contains, in order: headline, approach summary, out of scope, and
  ordered steps with file paths. Then validated assumptions with evidence, test plan, risks
  and mitigations, and open questions. The headline and approach summary read as plain prose to
  someone outside the investigation.
- [ ] The plan passes `prose-lint.py` with no findings.
- [ ] Open questions surfaced to the user. None silently answered.
- [ ] If validation killed the hypothesis, the deliverable is the negative result and the
  reframing, not a salvaged plan.

If a checkbox cannot be ticked honestly, the skill is not done. Return to the step that
produces it.

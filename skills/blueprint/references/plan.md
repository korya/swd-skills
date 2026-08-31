# The plan: counterfactual, structure, definition of done

Loaded from `SKILL.md` step 8.5. Covers the success-criteria counterfactual, the plan
document's structure, and the definition of done.

## 8.5. Counterfactual: does the plan satisfy the success criteria?

Close the loop between the goal (step 1) and the plan about to be written. For each success criterion stated in step 1, name the plan step(s) that satisfy it. Land on one of:

- **Confirmed** — every criterion is satisfied by at least one plan step; cite which.
- **Confirmed with gaps** — some criteria need follow-up work or out-of-band steps; list them and surface as open questions or out-of-scope.
- **Unconfirmed** — at least one criterion has no plan step that satisfies it. **Stop.** Either extend the plan or explicitly descope the criterion with the user's agreement.

A plan whose own success criteria don't all map to plan steps is a list of activities, not a plan.

## 9. Write the plan

Structure (inverted pyramid):

1. **Headline** — 1–3 sentences a reader with no context understands: what we're building, why this approach over the obvious alternative, and — if one exists — the single blocker or decision that stands in the way.
2. **Approach summary** — 3–10 sentences of plain prose, not bullets: the high-level design (the components it touches and how they interact, what stays untouched), the one or two assumptions the whole approach stands on, and the main trade-off that shaped it — what was given up and why. This is the go/no-go gate: a reader who finishes it should either see that the approach is wrong for them and stop, or accept its shape and go on to check the details against their constraints. High level, not a novel; the full assumption list and the alternatives considered live in the sections below.
3. **Out of scope** — what we're explicitly *not* doing, right after the approach so the boundary is read together with the shape, and to prevent scope drift later
4. **Plan** — ordered, concrete steps with file paths and the specific changes per step
5. **Assumptions validated** — bullet list with the evidence (file:line citation, experiment result, doc link)
6. **Risks & mitigations** — what could still go wrong; what we'll do if it does
7. **Test plan** — unit, integration, e2e, manual — what each covers and which scenarios
8. **Open questions** — anything the user still needs to decide *before* implementation. Last, so the reader arrives with the whole picture; a question that blocks the plan is also named in the headline.

The headline and approach summary are written for a human skimming the plan, not for the model executing it: full sentences, named things, no shorthand or step numbers that only make sense after reading the rest. The cryptic version of a plan is the one nobody can review.

Keep the plan as long as it needs to be and no longer. A plan that nobody reads is worse than one that's slightly too short.

## Definition of done

The skill is complete when **all** of these are true. Each item should be answerable with evidence, not a vibe.

- [ ] Problem statement (goal / constraints / non-goals / success criteria) restated; ambiguities resolved with the user, not invented.
- [ ] Hypothesis stated specifically enough to be falsifiable (named files, named APIs, named flows) **and** a disconfirming observation is written down — what would prove the hypothesis itself wrong, not just its individual assumptions.
- [ ] Every load-bearing assumption carries an evidence tag — a `file:line` citation, a quoted doc passage, a script's output, or a query result. No bare `[plausible]` or `[unverified]` tags survive into the final plan.
- [ ] Spec cross-validation: each affected requirement is named, and the plan line that satisfies it is named. Invariants explicitly checked (or a documented deviation flagged for user sign-off).
- [ ] Architecture cross-validation: any deviation is called out, not silent.
- [ ] Project-conventions cross-validation: each universal category (root + per-component conventions, package manager, build/test/run entry points, test framework + mocking policy, lint/format, migration tooling if schema is touched, ports/URLs, async machinery if relevant, reuse patterns) enumerated with `file:line` citations inside the plan, **and each bullet links to the plan step it shapes** (or is marked `Doesn't constrain this plan` with a reason). No defaults from training data — yours or the population's — sneaking in.
- [ ] Codebase conflict sweep performed: in-flight work, shadow duplication, caller-side drift (if signatures/schemas change), and test-infrastructure gaps all checked, with any findings reflected in the plan. (File-existence and signature checks live in the assumption list, not here.)
- [ ] Plan-vs-success-criteria counterfactual recorded as **Confirmed**, **Confirmed-with-gaps** (gaps listed), or **Unconfirmed** — and **Unconfirmed means the plan is not ready**.
- [ ] Plan document contains, in order: headline, approach summary, out-of-scope, ordered steps with file paths, validated assumptions with evidence, risks & mitigations, test plan, open questions. Headline and approach summary read as plain prose to someone outside the investigation.
- [ ] Open questions surfaced to the user. None silently answered.
- [ ] If validation killed the hypothesis: the deliverable is the negative result and the reframing, not a salvaged plan.

If a checkbox cannot be ticked honestly, the skill is not done — return to the step that produces it.

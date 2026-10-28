# The plan: counterfactual, structure, definition of done

Loaded from `SKILL.md` step 8.

## Counterfactual

Map each success criterion from step 1 to the plan steps that satisfy it. Record one
verdict in the plan:

- **Confirmed.** Every criterion has a plan step. Cite which.
- **Confirmed with gaps.** Some criteria need follow-up work. List them as open questions
  or out of scope.
- **Unconfirmed.** A criterion has no plan step. The plan is not ready. Extend it, or
  descope the criterion with the user's agreement.

## 9. Write the plan

The plan has these sections, in this order:

1. **Headline.** At most three sentences: what we build, why this approach, and the one
   blocking decision if there is one. Lists of spec changes and questions go below.
2. **Approach summary.** Three to ten sentences of prose, not bullets. Count them. An
   eleventh sentence belongs in a section below. Cover the components it touches and how
   they interact, what stays untouched, the one or two assumptions it stands on, and the
   main trade-off. A reader who finishes it can accept or reject the shape.
3. **Out of scope.** What we are explicitly not doing.
4. **Plan.** Ordered steps with file paths and the change in each.
5. **Assumptions validated.** Each with its evidence: a `file:line`, a script's output, or a
   quoted doc. Include the falsifier and its result.
6. **Project conventions to follow.** The bullets from step 6b.
7. **Test plan.** Unit, integration, e2e, and manual, with the scenarios each covers.
8. **Risks and mitigations.** What could still go wrong after the tests pass.
9. **Counterfactual.** The verdict and its mapping.
10. **Open questions.** Every decision the user still owes, with the assumption you proceed
    on.

The headline and the approach summary are for a human who skims. Use full sentences and
named things, never step numbers or shorthand that only make sense later. Keep the plan as
long as it needs to be and no longer.

## Definition of done

Each item is answerable with evidence.

- [ ] The problem is restated with success criteria. Ambiguities went to the user and were
  not invented.
- [ ] The hypothesis names files, APIs, and flows, and a falsifier for its shape was
  written and tested.
- [ ] Every load-bearing assumption carries evidence. No bare "plausible" survives.
- [ ] Every affected spec and invariant is named with the plan step that satisfies it, or
  the deviation is flagged for sign-off.
- [ ] Every convention category the plan touches has a `file:line` bullet linked to a plan
  step, or a reason it does not constrain the plan.
- [ ] The codebase sweep ran, and its findings are in the plan.
- [ ] The counterfactual verdict is recorded. Unconfirmed means the plan is not ready.
- [ ] The plan has every section above, in order, and passes `prose-lint.py`.
- [ ] Every open question is surfaced. None is silently answered.

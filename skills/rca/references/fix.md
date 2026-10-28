# From cause to fix: proposals, counterfactual, prevention, report

Loaded from `SKILL.md` step 8. Covers steps 8 to 11.

## 8. Propose the fixes

Write two separate proposals:

1. **Symptom fix.** The smallest change that makes the reported failure stop. Useful when
   shipping fast matters.
2. **Root-cause fix.** The upstream change that closes the gap, with the sibling repairs.

For each, name the files, the approach, the tests, the blast radius, and the rollback.
Recommend one. Weigh the urgency, the risk, and whether the symptom fix would hide the
cause from future detection.

## 9. Counterfactual: would the fix have prevented the captured repro?

Walk the recommended fix through the captured failure. The symptom fix passes by
construction, so the root-cause fix is the one that matters. Answer three questions:

- **Would the repro still fire** if this fix had been in place?
- **Which link of the chain does the fix break?** If it breaks link 2 but the root cause
  is at link 5, the fix is too shallow. Name what it does not prevent.
- **Does it address the captured failure**, or only a related one with the same root?

Land on one of three outcomes:

- **Confirmed.** The repro would not fire. Name the link the fix breaks.
- **Confirmed with survivors.** The fix stops the captured repro but not every path from
  the same root. List the survivors and judge whether the fix is wide enough.
- **Unconfirmed.** The fix addresses a real defect, but maybe not this failure. Stop. The
  chain points at the wrong cause or the fix targets the wrong layer. Revisit before
  recommending.

## 10. Prevent the class

For the root-cause fix, also propose:

- **A test** that would have caught this, at whatever layer fits. If no test layer would
  catch it, that is a finding.
- **A guardrail**, such as a type, a lint rule, an assertion, a schema constraint, or an
  alert, so the class becomes impossible or loud.
- **A doc update**, if a spec, an invariant, or `AGENTS.md` missed the constraint.

A test for this exact bug is the weakest prevention. Making the class impossible to
express is the strongest.

## 11. Report

The report is an inverted pyramid in this order:

1. **Headline.** At most three sentences, one per slot: what broke, the root cause, the
   recommended fix. Count them. Siblings, scope, and caveats go in the sections below,
   never in the headline.
2. **Symptom and scope.** What users saw, who was affected, when it started.
3. **5-whys chain.** The verified chain with citations.
4. **Symptom, proximate, root.** Labelled.
5. **Siblings.** A list, with severity.
6. **Fix proposals.** Symptom fix, root-cause fix, recommendation, counterfactual.
7. **Prevention.** Test, guardrail, doc update.
8. **Open questions.** Anything that needs user input before implementation.

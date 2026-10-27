# From cause to fix: proposals, counterfactual, prevention, report

Loaded from `SKILL.md` step 6. Covers steps 6, 6.5, 7 and 8.

## 6. Propose the fixes

Write two distinct proposals, separated:

1. **Symptom fix.** The smallest change that makes the reported failure stop. Useful when
   shipping fast matters.
2. **Root-cause fix.** The upstream change that addresses the gap. It includes the sibling
   repairs.

For each, name the files, the approach, the test coverage, the blast radius, and the
rollback story.

Recommend one. The recommendation depends on urgency, on risk, and on whether the symptom
fix would mask the cause from future detection.

## 6.5. Counterfactual: would the fix have prevented the captured repro?

Close the loop between cause and fix. Walk each proposed fix through the captured failure.
The root-cause fix matters most here. The symptom fix is trivially counterfactual-true by
construction. Answer:

- **If this fix had been in place when the failure was captured, would the repro still
  fire?**
- **Which link in the 5-whys chain does the fix break?** If the answer is "link 2" but you
  claimed the root cause is at link 5, the fix is too shallow. Name what it does not
  prevent.
- **Does the fix address the captured failure**, or only a related failure that shares the
  same root cause?

Land on one of:

- **Confirmed.** The repro would not fire under the fix. Name the link it breaks.
- **Confirmed for this case, but a sibling path remains.** The fix stops the captured repro
  but not all manifestations from the same root. List the survivors, and consider whether
  the fix is wide enough.
- **Unconfirmed.** The fix addresses a real defect, but it is not clear it addresses this
  failure. Stop. Either the chain points at the wrong cause or the fix targets the wrong
  layer. Revisit before recommending.

A fix that cannot survive its own counterfactual is a hypothesis dressed as a fix. Say so
when proposing it, or pick a different fix.

## 7. Prevent the class

For the root-cause fix, also propose:

- **A test**, unit, integration, or e2e, that would have caught this. If no test layer would
  catch it, that is a finding.
- **A guardrail**: a type, a lint rule, an assertion, a schema constraint, a code-review
  checklist item, or a monitoring alert. The goal is that this class of bug becomes either
  impossible or loud.
- **A doc update**, if a spec, an invariant, or `AGENTS.md` missed the constraint that would
  have flagged this.

"Add a test for this exact bug" is the weakest prevention. "Make this class of bug
impossible to express" is the strongest. Aim higher than the floor.

## 8. Report

The report is an inverted pyramid. Every sentence follows `../../assets/writing.md`, and
the file passes `prose-lint.py` before delivery.

1. **Headline.** One to three sentences: what broke, what the root cause was, the
   recommended fix. The first sentence names what broke.
2. **Symptom and scope.** What users saw, who was affected, when it started.
3. **5-whys chain.** The verified chain with citations: `file:line`, log excerpt, commit SHA.
4. **Symptom, proximate, root.** Labelled.
5. **Siblings.** A list, with severity.
6. **Fix proposals.** Symptom fix, root-cause fix, recommendation.
7. **Prevention.** Test, guardrail, doc update.
8. **Open questions.** Anything that needs user input before implementation.

# From cause to fix: proposals, counterfactual, prevention, report

Loaded from `SKILL.md` step 6. Covers steps 6, 6.5, 7 and 8.

## 6. Propose the fix(es)

Two distinct proposals, separated:

1. **Symptom fix** — the smallest change that makes the reported failure stop. Useful when shipping fast matters.
2. **Root-cause fix** — the upstream change that addresses the gap; includes sibling repairs.

For each: files, approach, test coverage, blast radius, rollback story.

Recommend one. The recommendation depends on urgency, risk, and whether the symptom fix would mask the cause from future detection.

## 6.5. Counterfactual: would the fix have prevented the captured repro?

Close the loop between cause and fix. For each proposed fix (especially the root-cause one — the symptom fix is trivially counterfactual-true by construction), walk it through the captured failure and answer:

- **If this fix had been in place when the failure was captured, would the repro still fire?**
- **Which link in the 5-whys chain does the fix break?** If the answer is "link 2" but you claimed the root cause is at link 5, the fix is too shallow — name what it doesn't prevent.
- **Does the fix address the captured failure**, or only a related failure that shares the same root cause?

Land on one of:

- **Confirmed** — repro would not fire under the fix; name the link it breaks.
- **Confirmed for this case, but a sibling path remains** — fix stops the captured repro but not all manifestations from the same root. List the survivors (and consider whether the fix is wide enough).
- **Unconfirmed** — the fix addresses a real defect but it's not clear it addresses *this* failure. **Stop.** Either the chain points at the wrong cause or the fix targets the wrong layer; revisit before recommending.

A fix that can't survive its own counterfactual is a hypothesis dressed as a fix. Say so when proposing it, or pick a different fix.

## 7. Prevent the class

For the root-cause fix, also propose:

- **A test** — unit, integration, or e2e — that would have caught this. If no test layer would catch it, that *is* a finding.
- **A guardrail** — type, lint rule, assertion, schema constraint, code-review checklist item, monitoring alert. The goal is that this *class* of bug becomes either impossible or loud.
- **A doc update** — if a spec, invariant, or `AGENTS.md` missed the constraint that would have flagged this, update it.

"Add a test for this exact bug" is the weakest prevention. "Make this class of bug impossible to express" is the strongest. Aim higher than the floor.

## 8. Report

Inverted pyramid:

1. **Headline** — one sentence: what broke, what the root cause was, recommended fix.
2. **Symptom / scope** — what users saw, who was affected, when it started.
3. **5-whys chain** — the verified chain with citations (file:line, log excerpt, commit SHA).
4. **Symptom / proximate / root** — labelled.
5. **Siblings** — list, with severity.
6. **Fix proposals** — symptom fix, root-cause fix, recommendation.
7. **Prevention** — test, guardrail, doc update.
8. **Open questions** — anything needing user input before implementation.

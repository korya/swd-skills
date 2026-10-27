# Rationalizations

Read this file when you catch yourself skipping a step. If your reason is below, do the
step.

| Rationalization | Why it fails |
|---|---|
| "The description is clear, or the change is obvious. I'll go straight to the diff." | The diff anchors you to the author's choices. Derive what should have happened first. Every intent you fill in silently is a finding you swallowed. |
| "Sketching my own approach first is ceremony." | Without the sketch, the author's solution becomes your baseline for normal. It costs minutes and is the only thing that makes over-engineering visible. |
| "The author surely had a reason for the extra complexity." | Then find it in the ticket, docs, history, or adjacent code, and cite it under Verified. If a real search comes up empty, it is a question for the author. |
| "My simpler approach is obviously better." | Not until you have walked it against every stated constraint. A simplification a documented constraint rules out costs the review its credibility. |
| "The approach looks wrong, but I'll mention it after the line review." | Buried under line findings, it reads as "fix the nits and merge". The disagreement is the headline. |
| "Tests pass and the author tested manually." | Tests cover what the author thought of. Manual testing without steps and environment is unverifiable. The review covers the rest. |
| "The docs don't matter, or the violation is obvious enough without a citation." | Invariants are not derivable from the diff. Without the cited rule, your priors pose as project rules. Find the rule or downgrade to a Suggestion. |
| "The assumption looks plausible." | You marked it load-bearing because being wrong breaks the change. Read the docs or measure. |
| "This dependency is from a big company." | Typosquats impersonate big-company packages on purpose. The audit is fast. |
| "Reversibility is the deployer's problem." | A merged change is one CI run from production. If the reviewer does not ask the rollback question, no one will. |
| "This candidate is speculative. I'll drop it." | Dropping it skips verification. Record it with its failure scenario. The verifier decides, and PLAUSIBLE is the default. |
| "Everything I found is at least High." | That is severity inflation. Critical breaks production or a hard rule. Demote the rest. |
| "There's no test for the stated risk. I'll note it as a Gap." | An uncovered named risk is an Issue with a severity. A Gap lets the author skim past it. |
| "I have doubts but no proof. I'll skip them." | List them as Questions. A silent doubt is a finding you chose not to surface. |
| "I don't have time to find what was done well." | It calibrates the author's sense of signal and noise. Spend the two minutes. |
| "I'll post the review, push the one-line fix, or trigger CI to test my theory." | Each one changes or publishes the work under review. A review's output is a local report. Anything visible to others needs the user's request. |

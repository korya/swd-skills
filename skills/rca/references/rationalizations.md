# Rationalizations

Read this when you catch yourself skipping a step. If your reason is below, do the step.

| Rationalization | Why it fails here |
|---|---|
| "The fix is obvious, skip the RCA." | The invocation is the signal that depth is required. Obvious fixes go through `/plan` or a one-line edit. |
| "I can't reproduce it, but I'm pretty sure I know why." | "Pretty sure" without a repro is how the same bug comes back next week. The deliverable is "we need a repro or better instrumentation", not a guess. |
| "Three whys is enough." | Three whys usually lands on a proximate cause. Five is a floor and a discipline, not a quota: three rigorous whys beat seven hand-wavy ones. |
| "The symptom is the cause. Fix and ship." | The symptom is evidence of the cause. Fix it and the cause moves to its next manifestation. |
| "No siblings found, so the cause is local." | Or you stopped too early. A truly local root cause is possible but rare. |
| "The chain reads fine, I don't need to verify each link." | A coherent narrative is not a correct one. Verify each link against code, logs, or data. |
| "I'll `git bisect` and call the offending commit the root cause." | The commit is where the cause came in, not what it is. The whys explain why the change was wrong and what let it through. |
| "The root cause is human error, or 'the author didn't anticipate this'." | That is a no-op finding. The root cause is the process, type, test, or doc that would have made them anticipate it. The output is a system change, never a person. |
| "The root cause is that we didn't have a test." | Test absence is itself a symptom. Ask why there was no test and why review did not catch it. |
| "A test for this exact case is enough prevention." | That catches the regression, not the class. Ask whether a guardrail, a type, or an invariant could make the class inexpressible. |
| "I'll fix the siblings quietly in the same change." | The user should hear about three other broken places in the report, not discover them in the diff. |
| "RCA can wait, let's ship the fix first." | Fine, if the RCA gets a deadline now. An RCA deferred indefinitely is never done. |
| "I'll make a small useful change and push it to trigger the pipeline." | The experiment mutates and publishes the subject under investigation. A good reason for the content is not authorization for the act. Exhaust read-only evidence, then ask. |
| "This is easily reversible. I'll do it and undo it after." | A force-push restores the branch. It does not unsend the notifications or unrun the CI. If others can observe it, get approval before, not forgiveness after. |

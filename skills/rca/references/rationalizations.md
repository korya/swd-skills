# Anti-rationalization table and anti-patterns

Read this when you catch yourself skipping a step — if your reason is below, do the step.

## Anti-rationalization table

| Rationalization | Why it fails here |
|---|---|
| "The fix is obvious, skip the RCA." | If the fix were truly obvious, the user wouldn't have invoked `/rca`. Obvious fixes go via `/plan` or a one-line edit. The invocation is the signal that depth is required. |
| "I can't reproduce it, but I'm pretty sure I know why." | Pretty-sure-without-repro is the modal cause of "the same bug came back next week." If you can't reproduce, the deliverable is "we need a repro / better instrumentation," not a guess dressed as a finding. |
| "Three whys is enough." | Three whys usually lands on a proximate cause. The whole point of five is to push past the comfortable stopping point. |
| "The symptom *is* the cause — fix and ship." | The symptom is *evidence* of the cause. Fix the symptom and the cause moves to its next manifestation. |
| "No siblings found, so the cause is local." | Or you stopped too early. Re-examine. A genuinely local root cause is possible but rare. |
| "Adding a test for this exact case is enough prevention." | That catches the regression, not the class. Ask whether a guardrail, type, or invariant could prevent the *class* from being expressible at all. |
| "The 5-whys chain reads fine, I don't need to verify each link." | A coherent narrative is not the same as a correct one. Verify each link against code, logs, or data. |
| "The cause is 'the original author didn't anticipate this' — done." | That's a no-op finding. The actionable root cause is: what process / type / test / doc would have made them anticipate it? |
| "RCA can wait, let's ship the fix first." | Fine, *if* the RCA has a deadline before the on-call rotation forgets. RCAs deferred indefinitely become RCAs never done. Set the deadline now. |
| "I'll just `git bisect` and call the offending commit the root cause." | The commit is *where* the cause was introduced, not *what* the cause is. Bisect locates the change; the 5-whys explains why the change was wrong and what allowed it through. |
| "I need to trigger the pipeline to test the theory — I'll make a small useful change and push it." | The experiment mutates the subject under investigation and publishes it: CI runs, reviewers get notified, history changes. That the change is independently useful is irrelevant — a true justification for the *content* is not authorization for the *act*. Exhaust read-only evidence first (state/API inspection → docs → history), then ask. |
| "This is easily reversible — I'll do it and undo it after." | Reversibility is judged by observable effects, not artifact state. A force-push restores the branch; it does not unsend the notifications, unrun the CI, or unring the bell for anyone watching. If others can observe it, get approval before, not forgiveness after. |

## Anti-patterns

- **Treating RCA as a postmortem template to fill in.** Boxes filled ≠ cause understood. The chain must be verified, not just authored.
- **Concluding "human error."** Almost never the root cause; almost always a proximate cause. The root cause is the system that let the human err undetected.
- **Stopping at "we didn't have a test."** Test absence is itself a symptom — of a process or design gap. Why was there no test? Why did review not catch it?
- **Fixing siblings silently.** If you found three other places with the same cause, the user should hear about them, not discover them in the diff.
- **Confusing a longer chain for a deeper one.** Five whys is a floor and a discipline, not a quota. Three rigorous whys beats seven hand-wavy ones.
- **RCA-as-blame.** The output is a system change, not a person. If the report names a person, rewrite it.

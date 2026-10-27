# Rationalizations: shortcuts that corrupt the run

Loaded when tempted to fix, skip, or downgrade. Each row feels efficient in the moment.
Each one quietly converts a test run into something else.

| Shortcut | Why it fails |
|---|---|
| "It's a one-line fix, faster to just do it." | The rule exists because those fixes keep being wrong. Made mid-run, without the design context, they are suboptimal at best. And once you have fixed, you are re-testing your own patch. The run stops being a test of the product. Report it. Fixing is a separate task. |
| "Curl is basically the browser." | It skips rendering, JS, CSS, and every layer where UI bugs live, the layers the change probably touched. A different surface is a different product. Verdicts do not transfer. |
| "This case obviously passes, skip it." | "Obviously" is what the diff says, and the diff is the thing under suspicion. Obvious cases take seconds to run. Regressions hide precisely where nobody re-looks. |
| "The unit tests cover this." | They cover the code's claims about itself. E2e exists because units compose wrongly. Green units are why this run exists, not a substitute for it. |
| "I tested this earlier, it worked." | Earlier was a different build and warmed-up state. First-time eyes, from scratch, or the verdict describes a product that no longer exists. |
| "The API works, so the UI must too." | The UI is where the user lives and where the binding, rendering, and state bugs are. Verdicts are earned at the surface the case names. |
| "The error is probably environmental. Call it PASS." | Suspicion of the environment makes a case BLOCKED with reasoning, never PASS. A benefit-of-the-doubt PASS is the report lying about the one thing it exists to say. |
| "I read the code; it clearly handles this." | Reading code is diagnosis, not observation. Code that clearly handles it and a product that actually does are exactly the gap e2e testing measures. |
| "Cosmetic issues aren't worth reporting." | A wrong border or a misaligned button is what the user sees first. Visuals and UX friction are findings. The fixer can triage them, but only if they are in the report. |
| "Staging is basically dev." | "Basically" is how test data ends up in front of real users. Not clearly dev means named to the user and confirmed before the first mutation, or the mutation cases go BLOCKED. |
| "The browser won't start. I'll test what I can and move on." | A quiet downgrade buries the biggest finding: the product, or its runway, does not come up. Fail loudly, mark the dependents BLOCKED, report now. |

# Rationalizations: shortcuts that corrupt the run

Read this when tempted to fix, skip, or downgrade. If your reason is below, do the step.

| Shortcut | Why it fails |
|---|---|
| "It's a one-line fix, faster to just do it." | Those fixes keep being wrong. Once you fix, you re-test your own patch, and the run stops testing the product. |
| "Curl is basically the browser." Or: "The API works, so the UI must too." | Both skip rendering, JS, CSS, binding, and state, where UI bugs live. A verdict holds only at the surface the case names. |
| "This case obviously passes, skip it." Or: "I read the code, it clearly handles this." | "Obviously" comes from the diff, and the diff is under suspicion. The gap between code that handles it and a product that does is what this run measures. |
| "The unit tests cover this." | They cover the code's claims about itself. E2e exists because units compose wrongly. |
| "The PR says the tests pass, so the suite misses these bugs." | That conclusion rests on a claim nobody checked. Run the tests as diagnosis, or report the claim as unchecked and conclude nothing from it. |
| "I tested this earlier, it worked." | Earlier was a different build and a warmed-up state. The verdict would describe a product that no longer exists. |
| "The error is probably environmental. Call it PASS." | Suspicion makes it BLOCKED with reasoning. A benefit-of-the-doubt PASS lies about the one thing the report exists to say. |
| "Cosmetic issues aren't worth reporting." | A wrong border is what the user sees first. The fixer can triage it, but only if it is in the report. |
| "Staging is basically dev." | "Basically" is how test data reaches real users. Name it and get confirmation, or the mutation cases go BLOCKED. |
| "The browser won't start. I'll test what I can." | A quiet downgrade buries the biggest finding: the product does not come up. Mark the dependents BLOCKED and report now. |

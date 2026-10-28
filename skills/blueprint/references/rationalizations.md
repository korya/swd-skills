# Rationalizations

Read this when you catch yourself skipping a step. If your reason is below, do the step.

| Rationalization | Why it fails |
|---|---|
| "I already know how this library works." "The docs say X." | Memory decays and versions drift. Docs describe intent, code shows behavior. Read the implementation in use. |
| "This change is small enough to skip validation." | The user invoked `/blueprint`, not `/plan`. The invocation is the signal. |
| "The user is waiting. Just commit to the hypothesis." | A wrong plan costs more wall-clock than a slow one. |
| "I'll validate the risky assumption while implementing." | A refutation mid-implementation means rework, or a silent patch around it. |
| "I'll batch the validations in my head as I write the plan." | An assumption without written evidence is asserted, not validated. |
| "TS monorepos use pnpm. Node servers run on 3000." | Defaults from training data feel right and cost nothing to invoke. Pull the command, port, and framework from the repo. |
| "There's no spec for this area, so the spec check doesn't apply." | The missing spec is the finding. Propose one or flag the undocumented behavior. |
| "Three rounds is taking too long. Let me ship plan v3." | Three failed rounds mean the problem needs reframing. Surface it. |
| "Validation shows this shouldn't ship, but they asked for a plan." | The deliverable is the negative result and the reframing. |

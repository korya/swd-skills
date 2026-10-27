# Anti-rationalization table and anti-patterns

Read this when you catch yourself skipping a step. If your reason is below, do the step.

## Anti-rationalization table

| Rationalization | Why it fails here |
|---|---|
| "I already know how this library or API works." | Memory of third-party APIs decays. Versions drift. Confirming costs minutes. Being wrong costs hours. Verify on the version in use. |
| "This change is small enough to skip validation." | If it were that small, the user would have invoked `/plan`, not `/blueprint`. The invocation itself is the signal that validation is required. |
| "The user is waiting. Just commit to the hypothesis." | A wrong plan costs more wall-clock than a slow one. The whole reason this skill exists is to front-load the failure. |
| "I'll validate the risky assumption while implementing." | Validation discovered mid-implementation means rework, lost commits, and, worse, silent papering over. Validate first. |
| "Reading the source is overkill. The docs say X." | Docs lie, code does not. For any load-bearing assumption, read the implementation. |
| "Three iterations is taking too long. Let me just ship plan v3." | Three failed iterations means the problem needs reframing, not that the plan is ready. Surface it to the user. |
| "There's no spec for this area, so cross-validation doesn't apply." | The absence of a spec is itself a signal. Either propose one or flag that this work creates undocumented behavior. Do not silently skip. |
| "The proposed approach matches an existing pattern, so it must be fine." | Patterns get cargo-culted. Confirm the pattern still applies to this problem before reusing it. |
| "I'll just batch the validations in my head as I write the plan." | If they are not written down with evidence, they are not validated. They are asserted in a more confident tone. |
| "TS monorepos usually use pnpm. Node servers usually run on :3000. Projects usually mock with `jest.mock`." | Defaults from training data are the most dangerous failure mode in convention checking. They feel right and cost nothing to invoke. Verify on the repo, not on the population. Pull the actual command, port, and framework name from `AGENTS.md` or the relevant docs file. |

## Anti-patterns

- **Skipping validation because "I'm pretty sure".** That is exactly when validation pays.
  Memory is wrong more often than agents like to admit.
- **Validating only the easy assumptions.** The risky one is the one that needs the
  experiment. If validation feels uncomfortable, it is probably the right one.
- **Confusing breadth for depth.** Reading 40 files shallowly is not validation. One careful
  read of the load-bearing function is.
- **Writing the plan first, then justifying it.** The plan should fall out of the
  validation, not precede it.
- **Looping forever.** Three iterations should converge or escalate. Indefinite refinement
  is a stall, not a plan.
- **Producing a plan when the answer is "don't do this".** If validation reveals the change
  should not ship, the deliverable is that conclusion, not a plan that ignores it.
- **Cross-validation theatre.** Citing a spec without showing how the plan satisfies it.
  Name the requirement and the line of the plan that addresses it.

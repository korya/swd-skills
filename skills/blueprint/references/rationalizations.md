# Anti-rationalization table and anti-patterns

Read this when you catch yourself skipping a step — if your reason is below, do the step.

## Anti-rationalization table

| Rationalization | Why it fails here |
|---|---|
| "I already know how this library/API works." | Memory of third-party APIs decays; versions drift. Cost to confirm: minutes. Cost of being wrong: hours. Verify on the version actually in use. |
| "This change is small enough to skip validation." | If it were that small, the user would have invoked `/plan`, not `/blueprint`. The invocation itself is the signal that validation is required. |
| "The user is waiting — just commit to the hypothesis." | A wrong plan costs more wall-clock than a slow one. The whole reason this skill exists is to front-load the failure. |
| "I'll validate the risky assumption while implementing." | Validation discovered mid-implementation means rework, lost commits, and (worse) silent papering-over. Validate first. |
| "Reading the source is overkill — the docs say X." | Docs lie, code does not. For any load-bearing assumption, read the implementation. |
| "Three iterations is taking too long, let me just ship plan v3." | Three failed iterations means the problem needs reframing, not that the plan is ready. Surface to the user. |
| "There's no spec for this area, so cross-validation doesn't apply." | Absence of a spec is itself a signal — either propose one or flag that this work creates undocumented behavior. Don't silently skip. |
| "The proposed approach matches an existing pattern, so it must be fine." | Patterns get cargo-culted. Confirm the pattern still applies to *this* problem before reusing it. |
| "I'll just batch the validations in my head as I write the plan." | If they're not written down with evidence, they're not validated — they're just asserted in a more confident tone. |
| "TS monorepos usually use pnpm / Node servers usually run on :3000 / projects usually mock with `jest.mock`." | Defaults from training data are the most dangerous failure mode in convention-checking, because they feel right and require no work to invoke. Verify on the repo, not on the population. Pull the actual command, port, framework name from `AGENTS.md` or the relevant docs/ file. |

## Anti-patterns

- **Skipping validation because "I'm pretty sure."** That's exactly when validation pays. Memory is wrong more often than agents like to admit.
- **Validating only the easy assumptions.** The risky one is the one that needs the experiment. If validation feels uncomfortable, it's probably the right one.
- **Confusing breadth for depth.** Reading 40 files shallowly is not validation. One careful read of the load-bearing function is.
- **Writing the plan first, then justifying it.** The plan should fall out of the validation, not precede it.
- **Looping forever.** Three iterations should converge or escalate. Indefinite refinement is a stall, not a plan.
- **Producing a plan when the answer is "don't do this."** If validation reveals the change shouldn't ship, the deliverable is that conclusion — not a plan that ignores it.
- **Cross-validation theatre.** Citing a spec without showing how the plan satisfies it. Name the requirement and the line of the plan that addresses it.

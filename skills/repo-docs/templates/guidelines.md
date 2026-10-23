# Guidelines

How to work in this repo. Short list, strict.

## Code quality

- **Lint 100% of code.** No file is exempt. New files pass lint before commit.
- **Test 100% of code.** Every module ships with tests. Untested code is broken code that
  nobody has observed yet.
- **Typecheck before commit.** <project-specific command>

## Planning and design

Every plan covers five steps before implementation begins. That holds for a feature, a bug
fix, and a refactor alike. Skipping one is how regressions, spec drift, and wasted rewrites
happen.

1. **Validate assumptions.** Before writing code that depends on an assumption, verify it.
   A 30-second check saves hours.
2. **Cross-validate against product specs.** Read every spec the change touches in
   [`docs/product-specs/`](product-specs/). Confirm the proposed solution upholds each
   affected spec ID. If it contradicts one, stop and surface it. Do not quietly diverge.
3. **Cross-validate against architecture.** Read [`docs/architecture.md`](architecture.md)
   for the layers, boundaries, and assumptions the change touches. Confirm the solution
   violates none of them. Surface conflicts before implementing.
4. **Plan automated test coverage.** New logic ships with tests that meet this repo's
   coverage policy: <state the policy, e.g., "100% of new code is tested">. Name the test
   files, the cases (happy path and the relevant edge cases), and the test types (unit,
   integration) up front.
5. **Plan end-to-end tests.** For any user-visible change, name the e2e scenarios that
   exercise the full flow. E2e tests do not replace unit tests. They catch the wiring that
   unit tests cannot.

If any of the five surfaces a conflict or an unknown, pause and discuss before continuing.

**Use the 5 whys when something fails.** Do not surface-patch. Understand the chain that
produced the failure.

## When changing product behavior

- Consult `docs/product-specs/` for the relevant feature.
- If your change contradicts a spec, stop and surface it. Either the spec is wrong, and
  you update it with user confirmation, or your change is wrong.
- After landing, update the spec if behavior diverged, with user confirmation.

## When changing architecture

- Consult `docs/architecture.md` before introducing new boundaries, dependencies, or layer
  crossings.
- Architecture changes are higher-stakes. Bring them up before implementing.
- Update `docs/architecture.md` after landing, with user confirmation.

## When invariants conflict

Stop and surface it. `docs/product-specs/invariants.md` is the floor. If your task seems to
require breaking one, either you misunderstood the task or the invariant needs revising.
Discuss before proceeding.

## Regression bugs

When a bug appears that was not there before:

1. **Do not patch first.** Run a root-cause analysis with the 5 whys.
2. **Find the chain.** Why did the symptom appear? Why did the change that caused it land?
   Why did no test catch it? Why was that test missing? Why was that case not considered?
3. **Report findings before fixing.** Document the root cause, or the most likely
   candidates when uncertain.
4. **Fix the root cause, not just the symptom.** Add the missing test that would have
   caught it.

## Documentation

- Keep `docs/` and any master spec updated as behavior and architecture evolve.
- Confirm every doc change with the user. Docs are reference material for future
  contributors, human and agent, and they need to be trustworthy.
- No drive-by edits to specs. A spec change is a deliberate act, not a side effect.

## Commits

- Descriptive messages. Why over what.
- One logical change per commit.
- Do not bundle a feature with unrelated cleanup. Make two commits.

## When unsure

Ask. A 30-second clarification always costs less than building the wrong thing.

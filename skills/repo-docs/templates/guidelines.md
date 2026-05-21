# Guidelines

How to work in this repo. Short list, strict.

## Code quality

- **Lint 100% of code.** No file is exempt. New files must pass lint before commit.
- **Test 100% of code.** Every module ships with tests. Untested code is broken code that hasn't been observed yet.
- **Typecheck before commit.** <project-specific command>

## Planning and design

Every plan — for a feature, a bug fix, or a refactor — must cover the following five steps before implementation begins. Skipping any of them is how regressions, spec drift, and wasted rewrites happen.

1. **Validate assumptions.** Before writing code that depends on an assumption, verify it. A 30-second check saves hours.
2. **Cross-validate against product specs.** Read every spec touched by the change in [`docs/product-specs/`](product-specs/). Confirm the proposed solution upholds each affected spec ID. If it contradicts one, **stop and surface it** — don't quietly diverge.
3. **Cross-validate against architecture.** Read [`docs/architecture.md`](architecture.md) for layers, boundaries, and assumptions touched by the change. Confirm the proposed solution doesn't violate a boundary or assumption. Surface conflicts before implementing.
4. **Plan automated test coverage.** New logic must ship with automated tests sufficient to meet this repo's coverage policy (<state the policy: e.g., "100% of new code is tested">). Identify the test files, the cases (happy path + the relevant edge cases), and the test types (unit / integration) up front, not after the fact.
5. **Plan end-to-end tests.** For any user-visible change, identify the e2e scenario(s) that exercise the full flow. E2e tests don't replace unit tests; they catch the wiring that unit tests can't.

If any of the five surfaces a conflict or unknown, pause and discuss before continuing.

- **Use the 5 whys when something fails.** Don't surface-patch. Understand the chain that produced the failure.

## When changing product behavior

- **Consult `docs/product-specs/`** for the relevant feature.
- If your change contradicts a spec, **stop and surface it**. Either the spec is wrong (update it with user confirmation) or your change is wrong.
- After landing, **update the spec** if behavior diverged — but only with user confirmation.

## When changing architecture

- **Consult `docs/architecture.md`** before introducing new boundaries, dependencies, or layer crossings.
- Architecture changes are higher-stakes. Bring them up before implementing.
- Update `docs/architecture.md` after landing — confirm with user.

## When invariants conflict

- **Stop. Surface.** `docs/product-specs/invariants.md` is the floor. If your task seems to require breaking one, you've either misunderstood the task or the invariant needs revising. Discuss before proceeding.

## Regression bugs

When a bug appears that wasn't there before:

1. **Don't patch first.** Conduct a CRA (cause-and-root-cause analysis) using the 5 whys.
2. **Find the chain.** Why did the symptom appear? Why did the change that caused it land? Why didn't a test catch it? Why was that test missing? Why was that case not considered?
3. **Report findings before fixing.** Document the root cause (or, if uncertain, the most likely candidates).
4. **Fix the root cause, not just the symptom.** Add the missing test that would have caught it.

## Documentation

- **Keep `docs/` and any master spec updated** as behavior and architecture evolve.
- **Confirm every doc change with the user.** Docs are reference material for future contributors (human and agent); they need to be trustworthy.
- **No drive-by edits to specs.** A spec change is a deliberate act, not a side effect.

## Commits

- Descriptive messages, "why" over "what".
- One logical change per commit.
- Don't bundle a feature with unrelated cleanup. Two commits.

## When unsure

Ask. The cost of a 30-second clarification is always less than the cost of building the wrong thing.

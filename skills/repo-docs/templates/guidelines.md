# Guidelines

How to work in this repo.

## Code quality

- **Lint all code.** New files pass lint before commit.
- **Test all code**, per this repo's policy: <state the policy, e.g., "100% of new code is
  tested">.
- **Typecheck before commit.** <project-specific command>

## Planning

Every plan covers these five steps before implementation begins, for a feature, a fix, or
a refactor alike.

1. **Validate assumptions.** Verify each assumption before code depends on it.
2. **Check the product specs.** Read every spec in
   [`product-specs/`](product-specs/) that the change touches, and the invariants. Confirm
   the change upholds each affected ID.
3. **Check the architecture.** Read [`architecture.md`](architecture.md) for the layers,
   boundaries, and assumptions the change touches. Confirm it violates none of them.
4. **Plan the automated tests.** Name the test files, the cases, and the test types up
   front.
5. **Plan the end-to-end tests.** For a user-visible change, name the scenarios that
   exercise the full flow.

If a step surfaces a conflict or an unknown, stop and discuss it with the user. Either the
doc is wrong, and the user confirms its update, or the change is wrong.

## Regressions

When a bug appears that was not there before, do not patch first.

1. Run the 5 whys. Why did the symptom appear? Why did the change land? Why did no test
   catch it?
2. Report the root cause, or the likely candidates, before you fix anything.
3. Fix the root cause and add the test that would have caught it.

## Commits

- One logical change per commit. Feature work and unrelated cleanup are two commits.
- The message says why, not only what.

---
name: e2e-test
description: Validate a product end-to-end the way its real user uses it — a web app through the browser, a CLI through its binary, a library by writing consumer programs — black-box, deriving cases from the change's blast radius and spec acceptance criteria, and reporting every case as PASS, FAILURE, or BLOCKED without fixing anything. Use when the user says "/e2e-test", "e2e test this", "test it in the browser", "manual e2e testing", "test it as the end user", "re-test the changes comprehensively", or before a release when the next stop is prod.
---

# E2e-test: the product through the front door

The point is not to run the test suite. The point is to sit where the user sits and find
out whether the product works. `/examine` reviews the code. `/e2e-test` ignores the code
and tests the product. The deliverable is a report someone else can fix from.

Never edit product code, config, or tests, not even a one-liner. A fix made mid-run lacks
the design context, and the run then tests your patch instead of the product. Report the
defect. Fixing is a separate task.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it. Read each
file at the step named.

| File | Read at | Holds |
|---|---|---|
| `references/surfaces.md` | step 1 | the surface and persona per product type, the fail-fast rule |
| `references/cases.md` | step 2 | the scope, and deriving cases from changes, specs, and blast radius |
| `references/report.md` | step 2, again at step 5 | the three statuses, the evidence to capture, the report depth and formats |
| `../../assets/writing.md` | step 5, before writing the report | the writing rules for every text a person reads |
| `references/rationalizations.md` | when tempted to fix, skip, or downgrade | why each shortcut fails |

## Side effects

Driving the product's own surface is testing, not fixing. Creating, updating, and
deleting records through it is fine in a dev or local environment. Any other environment,
such as a shared staging or anything prod-like, needs the user's explicit confirmation
before the first mutation. Without it, the mutation cases are BLOCKED. Keep the artifacts
you create. They reproduce findings, and the report lists them.

## Workflow

1. **Scope and surface.** Read `references/surfaces.md` now. Scope defaults to the change,
   its affected specs, and its blast radius. Identify the product's real user, their
   surface, and the target environment, and state all three. When "the change" is
   ambiguous, ask.
2. **Build the case list.** Read `references/cases.md` and `references/report.md` now.
   Write the case list before you run anything. It is the contract for the rest of the
   run. Derive cases from three sources: every acceptance criterion of the affected specs,
   cited by ID. Each changed behavior, with a happy path, an edge, and an error path. And
   the blast radius. Set the report depth from the invocation's wording.
3. **Readiness.** Start the product the documented way and smoke-check the surface. If it
   will not come up, stop. Mark every dependent case BLOCKED and report now. Never slide
   to a lesser surface and call it the same test.
4. **Execute.** Run every case from scratch, through the surface only. A verdict comes
   from what the user would see. Logs and code may explain a failure, but never turn it
   into a PASS. Record evidence as you go, and record UX friction and visual defects too.
   A failure does not stop the run. Mark what it cascades onto as BLOCKED and keep going.
5. **Report.** Read `../../assets/writing.md` now. Write the report per `report.md` at the
   depth you set. Run `<plugin root>/scripts/prose-lint.py` on it and fix every finding.
   Deliver the report and stop.

## Definition of done

- [ ] Scope, surface and persona, and environment stated before testing. Non-dev mutation
  confirmed by the user or not performed.
- [ ] Case list written before execution. Specs cited where they exist.
- [ ] Every case carries exactly PASS, FAILURE, or BLOCKED. None silently dropped.
- [ ] Every verdict earned at the user-visible surface. No case passed by reading code.
- [ ] Every non-PASS has evidence, repro steps, and a most likely cause.
- [ ] UX and visual observations recorded, not discarded as out of scope.
- [ ] Zero product files modified. Artifacts created through the surface are listed.
- [ ] Report delivered at the depth the invocation asked for, headline verdict first, and
  it passes `prose-lint.py` with no findings.

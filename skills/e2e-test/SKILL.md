---
name: e2e-test
description: Validate a product end-to-end the way its real user uses it — a web app through the browser, a CLI through its binary, a library by writing consumer programs — black-box, deriving cases from the change's blast radius and spec acceptance criteria, and reporting every case as PASS, FAILURE, or BLOCKED without fixing anything. Use when the user says "/e2e-test", "e2e test this", "test it in the browser", "manual e2e testing", "test it as the end user", "re-test the changes comprehensively", or before a release when the next stop is prod.
---

# E2e-test: the product through the front door

The point is not to run the test suite. The point is to sit where the user sits and find
out whether the product works. Every verdict is earned at the user-visible surface. Every
finding is reported instead of fixed. The deliverable is a report someone else can fix
from.

`/examine` reviews the code. `/e2e-test` ignores the code and tests the product.

Invoke it after a feature or fix is built, before a release, or whenever "does it actually
work?" needs an answer backed by evidence rather than by the diff looking right.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it. Read each
file at the step named.

| File | Read at | Holds |
|---|---|---|
| `references/surfaces.md` | step 1 | per-surface personas and mechanics, readiness checks, fail-fast rules |
| `references/cases.md` | step 2 | deriving the case list from changes, specs, and blast radius, and the report depth |
| `references/report.md` | step 5, skimmed at step 2 | the three statuses, lean and comprehensive formats, evidence rules |
| `../../assets/writing.md` | step 5, before writing the report | the writing rules for every text a person reads |
| `references/rationalizations.md` | when tempted to fix, skip, or downgrade | why each shortcut fails |

## Principles

- **Test it the way its user uses it.** A web app is tested by clicking through a real
  browser. A CLI is tested by invoking the binary in a shell. A library is tested by
  writing small programs as an integrating developer. A service is tested through its
  public API. Testing a different surface tests a different product.
- **Test, do not fix.** Hard rule: never edit product code, config, or tests, not even a
  one-liner. A mid-testing fix is suboptimal at best and wrong at worst. Every minute
  spent fixing is a minute not testing. Report. Fixing is a separate task with the report
  in hand.
- **The case list is a contract.** It is written before testing starts. Every case ends in
  exactly PASS, FAILURE, or BLOCKED. No other status exists, and no case is skipped
  without that skip appearing in the report.
- **Fail loudly, not sideways.** If the intended surface will not run, because the browser
  will not start or the app will not boot, stop and report BLOCKED at once. Never silently
  downgrade to a lesser surface and call it the same test.
- **First-time eyes.** Test from scratch, as if seeing the product for the first time. Do
  not lean on state or knowledge from earlier runs. UX friction, visual defects, and gaps
  nobody thought of are findings, not noise.

## Side effects

Driving the product's own surface is testing, not fixing. Creating, updating, and
deleting users, teams, or records is fine in a dev or local environment. Anything that is
not clearly dev, such as a shared staging or anything prod-like, needs the environment
named and the user's explicit confirmation before mutating. Artifacts created while
testing are kept, not cleaned up. They help reproduce findings and are listed in the
report.

## Workflow

1. **Scope and surface.** Read `references/surfaces.md` now. Scope defaults to the
   change: everything on the branch or PR, the product specs it affects, and the adjacent
   logic that could regress. A full-product sweep happens only when asked. Identify the
   product's real user and surface, and the target environment. State all three. When
   "the change" is ambiguous, ask. Do not guess.
2. **Build the case list.** Read `references/cases.md` now. Derive cases from three
   sources. The spec acceptance criteria, cited by ID when the repo has them. The change's
   user-visible behaviors, with a happy path, an edge, and an error path each. And the
   blast radius. Set the
   report depth from the invocation's wording. The finished list is the contract for
   everything after.
3. **Readiness.** Start the product the documented way and smoke-check the surface: the
   page renders, the binary answers `--help`, the package installs. If it is broken, all
   dependent cases are BLOCKED. Report now. Do not push through or work around.
4. **Execute.** Run every case, with first-time eyes, through the surface only. Verdicts
   come from what the user would see. Logs and code may inform a failure's most likely
   cause, but a log line never turns FAILURE into PASS. Record evidence as you go:
   verbatim errors, screenshots, commands with output. Record UX inconveniences and visual
   defects too: buttons, colors, borders, spacing, states. A failure does not stop the
   run. Mark it, mark what it cascades onto as BLOCKED, and keep testing everything
   testable.
5. **Report.** Read `references/report.md` and `../../assets/writing.md` now. Write an
   inverted pyramid: the verdict headline with counts first, then the case table, then
   details and the most likely cause for every non-PASS. At comprehensive depth, add the
   missing cases, issues by severity, UX gaps, improvements worth doing, and leftover
   artifacts. Run `<plugin root>/scripts/prose-lint.py` on the report and fix every
   finding in the text. Deliver the report and stop. No fixes, no follow-up commits.

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

## Related skills

`/spec` writes the acceptance criteria this skill tests against. `/examine` reviews the
code. `/rca` digs into a failure this skill found. Fixing the findings is its own task,
done from the report.

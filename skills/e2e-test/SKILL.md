---
name: e2e-test
description: Validate a product end-to-end the way its real user uses it — a web app through the browser, a CLI through its binary, a library by writing consumer programs — black-box, deriving cases from the change's blast radius and spec acceptance criteria, and reporting every case as PASS, FAILURE, or BLOCKED without fixing anything. Use when the user says "/e2e-test", "e2e test this", "test it in the browser", "manual e2e testing", "test it as the end user", "re-test the changes comprehensively", or before a release when the next stop is prod.
---

# E2e-test: the product through the front door

The point is **not** to run the test suite. It is to sit where the user sits and find out
whether the product actually works — every verdict earned at the user-visible surface,
every finding reported instead of fixed. `/examine` reviews the code; `/e2e-test` ignores
the code and tests the product. The deliverable is a report someone else can fix from.

Invoke after a feature or fix is built, before a release, or whenever "does it actually
work?" needs an answer backed by evidence rather than by the diff looking right.

## Required references

This file is the skeleton; each reference holds a step's full rules and examples. Read it
**at that step**.

| File | Read at | Holds |
|---|---|---|
| `references/cases.md` | step 2 | deriving the case list from changes, specs, and blast radius; report depth |
| `references/surfaces.md` | step 1 | per-surface personas and mechanics, readiness checks, fail-fast rules |
| `references/report.md` | step 5, skim at step 2 | the three statuses, lean vs comprehensive formats, evidence rules |
| `references/rationalizations.md` | when tempted to fix, skip, or downgrade | why each shortcut fails |

## Principles

- **Test it the way its user uses it.** A web app is tested by clicking through a real
  browser; a CLI by invoking the binary in a shell; a library by writing small programs
  as an integrating developer; a service through its public API. Testing a different
  surface tests a different product.
- **Test, don't fix.** Hard rule: never edit product code, config, or tests — not even a
  one-liner. A mid-testing fix is suboptimal at best and wrong at worst, and every minute
  spent fixing is a minute not testing. Report; fixing is a separate task with the report
  in hand.
- **The case list is a contract.** Written before testing starts; every case ends in
  exactly PASS, FAILURE, or BLOCKED. No other status exists, and no case is skipped
  without that skip appearing in the report.
- **Fail loudly, not sideways.** If the intended surface will not run — the browser won't
  start, the app won't boot — stop and report BLOCKED immediately. Never silently
  downgrade to a lesser surface and call it the same test.
- **First-time eyes.** Test from scratch, as if seeing the product for the first time; do
  not lean on state or knowledge from earlier runs. UX friction, visual defects, and
  gaps nobody thought of are findings, not noise.

## Side effects

Driving the product's own surface — creating, updating, deleting users, teams, records —
is testing, not fixing; do it freely **in a dev or local environment**. Anything that is
not clearly dev (a shared staging, anything prod-like) → name the environment and get the
user's explicit confirmation before mutating. Artifacts created while testing are kept,
not cleaned up — they help reproduce findings — and are listed in the report.

## Workflow

1. **Scope and surface.** **Read `references/surfaces.md` now.** Scope defaults to the
   change: everything on the branch or PR, the product specs it affects, and the adjacent
   logic that could regress; a full-product sweep only when asked. Identify the product's
   real user and surface, and the target environment. State all three; ambiguity about
   what "the change" is → ask, don't guess.
2. **Build the case list.** **Read `references/cases.md` now.** Derive cases from spec
   acceptance criteria (cited by ID when the repo has them), the change's user-visible
   behaviors — happy path, edge, and error path each — and the blast radius. Set the
   report depth from the invocation's wording. The finished list is the contract for
   everything after.
3. **Readiness.** Start the product the documented way and smoke-check the surface (the
   page renders, the binary answers `--help`, the package installs). Broken → all
   dependent cases are BLOCKED; report now, do not push through or work around.
4. **Execute.** Every case, first-time eyes, through the surface only. Verdicts come from
   what the user would see; logs and code may inform a failure's *most-likely cause*, but
   a log line never turns FAILURE into PASS. Record evidence as you go — verbatim errors,
   screenshots, commands with output — plus UX inconveniences and visual defects
   (buttons, colors, borders, spacing, states). A failure does not stop the run: mark it,
   mark what it cascades onto as BLOCKED, keep testing everything testable.
5. **Report.** **Read `references/report.md` now.** Inverted pyramid: verdict headline
   with counts first, the case table, details and most-likely cause for every non-PASS —
   then, at comprehensive depth, missing cases, issues by severity, UX gaps, improvements
   worth doing, and leftover artifacts. Deliver the report and stop: no fixes, no
   follow-up commits.

## Definition of done

- [ ] Scope, surface/persona, and environment stated before testing; non-dev mutation
  confirmed by the user or not performed.
- [ ] Case list written before execution; specs cited where they exist.
- [ ] Every case carries exactly PASS, FAILURE, or BLOCKED — none silently dropped.
- [ ] Every verdict earned at the user-visible surface; no case passed by reading code.
- [ ] Every non-PASS has evidence, repro steps, and a most-likely cause.
- [ ] UX and visual observations recorded, not discarded as out of scope.
- [ ] Zero product files modified; artifacts created through the surface are listed.
- [ ] Report delivered at the depth the invocation asked for, headline verdict first.

## Related skills

`/spec` (planned) writes the acceptance criteria this skill tests against · `/examine`
reviews the code · `/rca` digs into a failure this skill found · fixing the findings is
its own task, done from the report.

---
name: spec
description: Turn a fuzzy feature request into a reviewable product spec — goals, non-goals, testable acceptance criteria with stable IDs, invariants — that later skills cite by path and ID. Use when the user says "/spec", "spec this out", "write a product spec", "turn this idea into requirements", or brings a feature request that needs a contract before planning or building.
---

# Spec: the contract everything else cites

The point is a document that later work can be checked against. `/blueprint`
cross-validates its plan with it. `/e2e-test` derives cases from its criteria. `/revise`
uses it as the scope fence. That only works if the spec is product-level, testable, and
stably addressable, which is what this skill enforces.

`/spec` says what and why. How belongs to `/blueprint`.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it.

| File | Read at | Holds |
|---|---|---|
| `references/format.md` | step 1, when the repo has no spec convention | the default location, file shape, ID rules, invariant tiers |
| `../../assets/writing.md` | step 4, before drafting | the writing rules for every text a person reads |

## Principles

- **What and why, never how.** State everything in user-observable terms. The litmus test:
  two different implementations should both be able to satisfy the spec. Technical
  constraints appear only when they are genuine product constraints, such as compliance or
  platform, not design preferences.
- **Testable or it is not a criterion.** Each acceptance criterion is a concrete scenario
  with an observable outcome, something an end-to-end test could execute black-box. "The
  feature should be fast, intuitive, or robust" is a goal at best, never a criterion.
- **Stable IDs, append-only.** Criteria carry IDs that later skills cite. IDs are never
  renumbered or reused, and deletions leave holes. See `references/format.md`.
- **Never invent answers.** Unknowns become marked assumptions or open questions. Blocking
  questions go to the user, batched, once.
- **Non-goals are load-bearing.** What the feature deliberately does not do is the fence
  against scope creep in every later skill. Write them as deliberately as the goals.

## Workflow

1. **Orient.** Find the repo's existing spec convention: a specs directory, its index, its
   ID scheme. Read the specs adjacent to this feature. The repo's convention wins. Only
   where there is none, use the default in `references/format.md`, and read it now. Decide
   create against amend. A feature that already has a spec gets an amendment, not a rival
   document.
2. **Extract.** From the request and the repo, collect the users involved and the pain
   being solved. Collect the current behavior being changed, and the adjacent specs and
   invariants touched. Distill candidate goals and constraints. Inventory the unknowns.
3. **Ask what blocks the shape.** Split the unknowns. Answers that change the spec's
   structure (who it serves, where its boundary sits, what success is) are asked as one
   batched round of questions. Then wait. Everything else proceeds as a marked assumption
   or an open question in the draft. Zero silent inventions.
4. **Draft** per the format. Read `../../assets/writing.md` first. Write the overview and
   goals, the non-goals, and the user-observable behavior. Then write the acceptance
   criteria as ordered testable steps with IDs. Happy path, edges, and error behavior are all criteria.
   Feature-local invariants live in the file. A cross-cutting one is proposed for the
   global invariants doc and flagged. Open questions come last. When amending, new
   criteria take fresh IDs, removed ones leave holes, and the diff reads as "what changed
   about the product's contract".
5. **Cross-check.** Every goal is covered by at least one criterion. Every criterion is
   black-box testable. Nothing contradicts an existing spec or invariant. A conflict is
   surfaced to the user, never silently overridden in either direction. Non-goals do not
   contradict the goals. Run `<plugin root>/scripts/prose-lint.py` on the spec file and fix
   every finding in the text.
6. **Present and gate.** Deliver the spec with its open questions surfaced. A spec is a
   contract, so the user signs off before anything downstream builds on it. Committing and
   PR-ing it is `/submit`'s job, on request.

## Definition of done

- [ ] Repo convention honored, or the default format used and said so. Create against
  amend decided deliberately.
- [ ] Blocking questions asked once, batched. Every remaining unknown is a marked
  assumption or open question. None invented.
- [ ] Every criterion has a stable ID, an ordered scenario, and an observable outcome. IDs
  append-only.
- [ ] Goals each covered by a criterion. Edges and error behavior specified, not implied.
- [ ] No implementation content. Non-goals present and real.
- [ ] No contradiction with existing specs or invariants, or the conflict is surfaced.
- [ ] The spec file passes `prose-lint.py` with no findings.
- [ ] User sign-off requested before downstream work cites the spec.

## Related skills

`/blueprint` plans against the spec. `/e2e-test` tests from its criteria. `/revise` uses
it as the scope fence. `/repo-docs` sets up the docs layout specs live in.

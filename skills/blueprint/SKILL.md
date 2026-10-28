---
name: blueprint
description: Plan a non-trivial code change rigorously — understand the problem, form a hypothesis, validate assumptions through real experiments and doc/code reads, and cross-check the proposed solution against product specs, architecture, and the existing codebase before writing any plan. Use when the user says "/blueprint", "blueprint this", "plan this thoroughly", "deep plan", "I want to be sure before we build this", or for any change where a wrong direction would burn meaningful time, tokens, or compute. Heavier and more deliberate than `/plan`; the goal is the global optimum, not a local one.
---

# Blueprint: thorough, validation-first planning

The point is not a longer plan. The point is to refuse to commit to a plan until the
assumptions under it have been tested against reality. `/plan` says "here is how I would
build it". `/blueprint` adds why each load-bearing assumption holds, with the evidence. A
cheap experiment beats confident reasoning, and the source on `HEAD` beats memory.

Do not invoke it for typo fixes, single-file edits, or mechanical renames. This skill is
expensive on purpose.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it. Read each
file at the step named.

| File | Read at | Holds |
|---|---|---|
| `references/validation.md` | step 2 | the falsifiable hypothesis, assumption classes, cheap validation |
| `references/cross-validation.md` | step 5 | spec, architecture, and convention checks, the codebase sweep |
| `references/plan.md` | step 8 | the counterfactual, the plan structure, the definition of done |
| `../../assets/writing.md` | step 9, before writing the plan | the writing rules for every text a person reads |
| `references/rationalizations.md` | when tempted to skip a step | why each shortcut fails |

## Workflow

1. **Understand the problem.** Restate the goal, constraints, non-goals, and success
   criteria. Include what would prove the change does not work. If the request is ambiguous
   or contradictory, ask the user. Never invent answers to plug holes.
2. **Form a hypothesis.** Read `references/validation.md` now. Write a candidate specific
   enough to be wrong, and the observation that would prove its shape wrong.
3. **List the load-bearing assumptions.** These are the ones the plan stops working
   without. Classify each as Verified, Plausible, or Risky.
4. **Validate** every unverified assumption and the falsifier with the cheapest thing that
   produces evidence. A refuted assumption sends you back to step 2. Never patch around it.
5. **Check the product specs.** Read `references/cross-validation.md` now. A violated
   invariant or requirement means the plan is not ready, or the spec needs a flagged change.
6. **Check the architecture and the project's conventions.** Every command, tool, port,
   and framework in the plan comes from a `file:line` in the repo, never from training data.
7. **Sweep the codebase** for in-flight work, duplicate logic, callers of a changed
   contract, and missing test infrastructure.
8. **Loop or commit.** A broken hypothesis goes back to step 2, a partial one gets its
   changed parts re-validated. After about three rounds, surface that the problem needs
   reframing. Once it survives, read `references/plan.md` and map every success criterion
   to the plan step that meets it.
9. **Write the plan.** Read `../../assets/writing.md` now, then write the plan in the order
   `plan.md` gives. Run `<plugin root>/scripts/prose-lint.py` on it and fix every finding
   before you present it.
10. **Present and gate.** Ask the open questions and wait. An architectural deviation, a
    spec change, or a risky migration needs explicit approval before implementation. Never
    proceed on auto mode.

## Definition of done

Every item in `plan.md` § Definition of done is answerable with evidence. One you cannot
tick honestly sends you back to the step that produces it. If validation killed the
hypothesis, the deliverable is the negative result and the reframing, not a salvaged plan.

## Related skills

`/plan` when assumptions are mostly known. `/rca` when the failure has already happened.
`/examine` to review the change once it is built.

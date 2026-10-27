---
name: blueprint
description: Plan a non-trivial code change rigorously — understand the problem, form a hypothesis, validate assumptions through real experiments and doc/code reads, and cross-check the proposed solution against product specs, architecture, and the existing codebase before writing any plan. Use when the user says "/blueprint", "blueprint this", "plan this thoroughly", "deep plan", "I want to be sure before we build this", or for any change where a wrong direction would burn meaningful time, tokens, or compute. Heavier and more deliberate than `/plan`; the goal is the global optimum, not a local one.
---

# Blueprint: thorough, validation-first planning

The point is not a longer plan. The point is to refuse to commit to a plan until the
assumptions under it have been tested against reality. A plan on unverified assumptions is a
confident-looking bug report from the future. `/plan` says "here is how I would build it".
`/blueprint` adds why each load-bearing assumption holds, with the evidence.

Invoke it for non-trivial features or refactors where a wrong approach costs hours. Invoke
it for changes that cross component boundaries or touch invariants such as data isolation,
auth, or billing. Invoke it for anything that rests on third-party behaviour you have not
verified. Invoke it for stated uncertainty ("would this even work?") or after a previous
attempt failed.

Do not invoke it for typo fixes, single-file edits, or mechanical renames. This skill is
expensive on purpose.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it. Read each
file at the step named.

| File | Read at | Holds |
|---|---|---|
| `references/validation.md` | step 2 | the falsifiable hypothesis, assumption classes, validation per assumption type |
| `references/cross-validation.md` | step 5 | spec, architecture, and conventions checks with citations, the codebase sweep |
| `references/plan.md` | step 8.5 | the success-criteria counterfactual, the plan structure, the definition of done |
| `../../assets/writing.md` | step 9, before writing the plan | the writing rules for every text a person reads |
| `references/rationalizations.md` | when tempted to skip a step | why each shortcut fails |

## Principles

- **Hypothesis first.** Validation needs a target. Without one, "research" wanders.
- **Cheap experiments beat confident reasoning.** A 10-line script that proves an API
  behaves as expected outranks a paragraph asserting it.
- **Read the source on `HEAD`, not from memory.** APIs change and specs evolve. Verify now.
- **Inverted pyramid for the user.** Recommendation and blockers first. Detail unfolds
  below, and the decisions the user still owes close the document.
- **Loop until convergent.** A refuted assumption sends you back to the hypothesis. Never
  paper over it.

## Workflow

1. **Understand the problem.** Restate it: goal, constraints, non-goals, success criteria.
   Include what would prove the change does not work. If it is ambiguous or contradictory,
   ask the user. Never invent answers to plug holes.
2. **Form a hypothesis.** Read `references/validation.md` now. Write a candidate specific
   enough to be wrong. Name the files and flows that change, the APIs it relies on, and its
   two to four load-bearing assumptions. Name the observation that would prove the shape
   wrong. If
   you cannot write the falsifier, sharpen the hypothesis. Note fallbacks if several
   approaches are plausible.
3. **Enumerate load-bearing assumptions.** These are the ones the plan stops working
   without. Classify each as **Verified** (cite `file:line` or a doc), **Plausible**, or
   **Risky**.
4. **Validate** every unverified one with the cheapest thing that produces evidence: a
   script and its output, the library source, the migration files, a read-only query.
   Record **confirmed**, **refuted**, or **partial**. Refuted sends you back to step 2.
   Delegate batched reads to a read-only search subagent when the host has one.
5. **Cross-validate with product specs.** Read `references/cross-validation.md` now. Does
   the plan satisfy each affected requirement? Does it violate any invariant? Does it miss
   an acceptance criterion? A violation means the plan is not ready, or the spec needs a
   flagged change before code work.
6. **Cross-validate with architecture and conventions.** Check boundaries, security,
   scalability and cost, observability, and async machinery. Then run the discipline check.
   Enumerate the project's conventions from its own docs on `HEAD`: package manager,
   task-runner entry points, test framework and mocking policy, lint, migrations, ports.
   Cite each one and link it to the plan step it shapes, or mark it "doesn't constrain"
   with a reason. Defaults from training data are the modal failure here.
7. **Sweep the codebase** for systemic conflicts no single assumption captures. Look for
   in-flight work in the area, shadow duplication, caller-side drift when a contract
   changes, and missing test infrastructure.
8. **Loop or commit.** Survived: go to step 8.5. Partially: adjust and re-validate the
   changed parts. Broken: back to step 2 with what you learned. Cap at about three rounds.
   After that the problem itself likely needs reframing. Surface that.
8.5. **Counterfactual.** Read `references/plan.md` now. Map every step-1 success criterion
   to the plan step that satisfies it: **Confirmed**, **Confirmed with gaps** (listed), or
   **Unconfirmed**. Unconfirmed means the plan is not ready.
9. **Write the plan.** Read `../../assets/writing.md` now, then write per `plan.md` § 9.
   The order is headline (one to three sentences), approach summary (three to ten
   sentences of prose), and out of scope. Then come the ordered steps with file paths,
   assumptions with evidence, test plan, risks and mitigations, and open questions last. The first two sections let a human accept or
   reject the shape before reading further. Run `<plugin root>/scripts/prose-lint.py` on
   the plan and fix every finding in the text before presenting it.
10. **Present and gate.** Ask the open questions and wait. An architectural deviation, a
    spec change, or a risky migration needs explicit approval before implementation. Never
    proceed on auto mode. Once approved, normal implementation rules apply.

## Definition of done

Every item in `plan.md` § Definition of done is answerable with evidence. One you cannot
tick honestly sends you back to the step that produces it. A step you are tempted to skip
sends you to `references/rationalizations.md`. If validation killed the hypothesis, the
deliverable is the negative result and the reframing, not a salvaged plan.

## Related skills

`/plan` when assumptions are mostly known. `/rca` when the failure has already happened.
`/examine` to review the change once it is built.

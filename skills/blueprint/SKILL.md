---
name: blueprint
description: Plan a non-trivial code change rigorously — understand the problem, form a hypothesis, validate assumptions through real experiments and doc/code reads, and cross-check the proposed solution against product specs, architecture, and the existing codebase before writing any plan. Use when the user says "/blueprint", "blueprint this", "plan this thoroughly", "deep plan", "I want to be sure before we build this", or for any change where a wrong direction would burn meaningful time, tokens, or compute. Heavier and more deliberate than `/plan`; the goal is the global optimum, not a local one.
---

# Blueprint: thorough, validation-first planning

The point is **not** a longer plan. It is refusing to commit to a plan until the assumptions
under it have been tested against reality — a plan on unverified assumptions is a
confident-looking bug report from the future. `/plan` says "here's how I'd build it";
`/blueprint` adds why each load-bearing assumption holds, with the evidence.

Invoke for non-trivial features or refactors where a wrong approach costs hours, changes
crossing component boundaries or touching invariants (data isolation, auth, billing),
anything resting on third-party behaviour you have not personally verified, stated
uncertainty ("would this even work?"), or a previous attempt that failed. Not for typo
fixes, single-file edits, or mechanical renames — this skill is expensive on purpose.

## Required references

This file is the skeleton; each reference holds a step's full rules. Read it **at that step**.

| File | Read at | Holds |
|---|---|---|
| `references/validation.md` | step 2 | falsifiable hypothesis, assumption classes, validation per assumption type |
| `references/cross-validation.md` | step 5 | spec, architecture, and conventions checks with citations; codebase sweep |
| `references/plan.md` | step 8.5 | success-criteria counterfactual, plan structure, definition of done |
| `references/rationalizations.md` | when tempted to skip a step | why each shortcut fails |

## Principles

- **Hypothesis first.** Validation needs a target; without one, "research" wanders.
- **Cheap experiments beat confident reasoning.** A 10-line script that proves an API
  behaves as expected outranks a paragraph asserting it.
- **Read the source on `HEAD`, not from memory.** APIs change, specs evolve; verify *now*.
- **Inverted pyramid for the user.** Recommendation and blockers first; detail unfolds
  below, and the decisions the user still owes close the document.
- **Loop until convergent.** A refuted assumption sends you back to the hypothesis; never
  paper over it.

## Workflow

1. **Understand the problem.** Restate it: goal, constraints, non-goals, success criteria —
   including what would prove the change doesn't work. Ambiguous or contradictory → ask
   the user; never invent answers to plug holes.
2. **Form a hypothesis.** **Read `references/validation.md` now.** A candidate specific
   enough to be wrong: the files and flows that change, the APIs it relies on, its 2–4
   load-bearing assumptions — and the observation that would prove the *shape* wrong. If
   you cannot write the falsifier, sharpen the hypothesis; note fallbacks if several
   approaches are plausible.
3. **Enumerate load-bearing assumptions** — those the plan stops working without. Classify
   each **Verified** (cite `file:line` or doc), **Plausible**, or **Risky**.
4. **Validate** every unverified one with the cheapest thing that produces evidence: a
   script and its output, the library source, the migration files, a read-only query.
   Record **confirmed / refuted / partial**; refuted → back to step 2. Delegate batched
   reads to a read-only search subagent when the host has one.
5. **Cross-validate with product specs.** **Read `references/cross-validation.md` now.**
   Does the plan satisfy each affected requirement, violate any invariant, miss an
   acceptance criterion? A violation means the plan is not ready — or the spec needs a
   flagged change before code work.
6. **Cross-validate with architecture and conventions.** Boundaries, security,
   scalability and cost, observability, async machinery. Then the discipline check:
   enumerate the project's conventions from its own docs on `HEAD` — package manager,
   task-runner entry points, test framework and mocking policy, lint, migrations, ports —
   each cited and linked to the plan step it shapes, or marked "doesn't constrain" with a
   reason. Defaults from training data are the modal failure here.
7. **Sweep the codebase** for systemic conflicts no single assumption captures: in-flight
   work in the area, shadow duplication, caller-side drift when a contract changes,
   missing test infrastructure.
8. **Loop or commit.** Survived → step 8.5. Partially → adjust and re-validate the changed
   parts. Broken → back to step 2 with what you learned. Cap at ~3 rounds; then the problem
   itself likely needs reframing — surface that.
8.5. **Counterfactual.** **Read `references/plan.md` now.** Map every step-1 success
   criterion to the plan step that satisfies it: **Confirmed**, **Confirmed with gaps**
   (listed), or **Unconfirmed** — and unconfirmed means the plan is not ready.
9. **Write the plan** per `plan.md` § 9: headline (1–3 sentences), approach summary
   (3–10 sentences of prose), out of scope, ordered steps with file paths, assumptions
   with evidence, test plan, risks and mitigations, open questions last. The first two
   sections let a human accept or reject the shape before reading further; the whole
   is as long as it needs to be and no longer.
10. **Present and gate.** Ask open questions and wait. An architectural deviation, spec
    change, or risky migration needs explicit approval before implementation — never
    proceed on auto mode. Approved → normal implementation rules apply.

## Definition of done

Every item in `plan.md` § Definition of done is answerable with evidence. One you cannot
tick honestly sends you back to the step that produces it; a step you are tempted to skip
sends you to `references/rationalizations.md`. If validation killed the hypothesis, the
deliverable is the negative result and the reframing — not a salvaged plan.

## Related skills

`/plan` when assumptions are mostly known · `/rca` when the failure has already happened ·
`/examine` to review the change once it is built.

---
name: blueprint
description: Plan a non-trivial code change rigorously — understand the problem, form a hypothesis, validate assumptions through real experiments and doc/code reads, and cross-check the proposed solution against product specs, architecture, and the existing codebase before writing any plan. Use when the user says "/blueprint", "blueprint this", "plan this thoroughly", "deep plan", "I want to be sure before we build this", or for any change where a wrong direction would burn meaningful time, tokens, or compute. Heavier and more deliberate than `/plan`; the goal is the global optimum, not a local one.
---

# Blueprint: thorough, validation-first planning

The point of this skill is **not** to produce a longer plan. It is to refuse to commit to a plan until the assumptions underneath it have been tested against reality. A plan built on unverified assumptions is just a confident-looking bug report from the future.

`/plan` says "here's how I'd build it." `/blueprint` says "here's how I'd build it, here's why each load-bearing assumption holds, and here's the evidence."

## When to invoke

- Non-trivial features or refactors where a wrong approach costs hours, not minutes
- Cross-component changes (touches multiple of `agent/`, `portal/`, `marketing/`, `infra/`)
- Anything that touches invariants: customer data isolation, org isolation, auth, billing, agent context injection
- Anything depending on a third-party API or library behavior the agent has not personally verified
- Anything where the user has expressed uncertainty ("I'm not sure if X is possible", "would this even work")
- After a previous attempt failed — the cheap plan was wrong, time to do it properly

Do **not** invoke for: typo fixes, single-file edits with obvious scope, mechanical rename/move tasks, or anything `/plan` (or no plan at all) handles fine. This skill is expensive on purpose; reserve it.

## Operating principles

- **Hypothesis-first.** Form a candidate solution early so validation has a target. Without a hypothesis, "research" wanders.
- **Cheap experiments beat confident reasoning.** A 10-line script that proves an API behaves as expected is worth more than a paragraph asserting it does.
- **Read the source on `HEAD`, not from memory.** Memory of a codebase decays; APIs change; specs evolve. Verify *now*.
- **Inverted pyramid for the user.** Surface the headline (recommendation, blockers, open questions) first. Detail follows.
- **Loop until convergent.** If validation invalidates the hypothesis, go back to step 1 with what you learned. Do not paper over a broken assumption.

## Workflow

### 1. Understand the problem

Restate the problem in your own words. Identify:

- **Goal** — what user-visible or system-level outcome is being asked for?
- **Constraints** — deadlines, must-not-break invariants, scope limits, compatibility requirements
- **Non-goals** — what is *explicitly* out of scope? (Reduces gold-plating later.)
- **Success criteria** — how will we know the change works? What would prove it doesn't?

If any of these are ambiguous or contradictory, **ask the user**. One clarifying question now beats a wasted plan later. Do not invent answers to plug holes.

### 2. Form a hypothesis

**Read `references/validation.md` now**; it covers steps 2, 3 and 4.

### 3. Enumerate load-bearing assumptions

Per `references/validation.md` § 3.

### 4. Validate assumptions

Per `references/validation.md` § 4.

### 5. Cross-validate with product specs

**Read `references/cross-validation.md` now**; it covers steps 5, 6 and 7.

### 6. Cross-validate with architecture & conventions

Per `references/cross-validation.md` § 6.

### 7. Sweep the codebase for hidden conflicts

Per `references/cross-validation.md` § 7.

### 8. Loop or commit

After steps 4–7, one of three things is true:

1. **Hypothesis survived all validation** → proceed to step 9
2. **Hypothesis partially survived** → adjust the plan in-place; re-validate the changed parts; continue
3. **Hypothesis broken** → go back to step 2 with what you learned. Do not bolt fixes onto a broken approach.

Looping is normal and expected. The skill exists *because* first hypotheses are often wrong. A clean plan on the second or third iteration beats a brittle plan on the first.

Cap iterations at ~3 before pulling the user in. If after 3 rounds no hypothesis survives, the problem itself likely needs reframing — surface that.

### 8.5. Counterfactual: does the plan satisfy the success criteria?

**Read `references/plan.md` now**; it covers steps 8.5 and 9 and the definition of done.

### 9. Write the plan

Per `references/plan.md` § 9.

### 10. Present and gate

Show the plan. If there are open questions, ask them explicitly and wait. If the plan involves an architectural deviation, a spec change, or a risky migration, **do not start implementing in auto mode** — get explicit user approval first.

If the plan is approved, implementation continues under normal rules (lint, test, commit hygiene, `/submit` for PRs).

## Anti-rationalization

When tempted to skip a step, read `references/rationalizations.md`.

## Definition of done

The checklist lives in `references/plan.md` § Definition of done.

## Relationship to other skills

- `/plan` — lighter; use when assumptions are mostly known and the change is straightforward
- `feedback_plan_validation_passes` — the three-pass validation discipline (assumption / spec+arch / edge-case) is roughly steps 4–7 here, applied at the end of *any* plan
- `/submit` — for landing the change once the plan executes

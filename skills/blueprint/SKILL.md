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

Propose a concrete candidate solution given current knowledge. It should be specific enough to be wrong:

- The components/files that change, at the directory level
- The data flow / control flow at a sketch level
- The key APIs, libraries, or system behaviors it relies on
- The 2-4 load-bearing assumptions ("this works *if* X behaves like Y")

If you cannot articulate a hypothesis at all, the problem is not yet understood — go back to step 1.

If multiple candidate approaches are plausible, note them and pick one to validate first based on simplicity, risk, or fit. The others are fallbacks if validation kills the primary.

**Then write down what would prove the hypothesis itself wrong** — not its individual assumptions (those come in step 3), but the *shape* of the solution. Examples:

- "If reads dominate writes by 100×, a read-through cache is the wrong shape — a write-aside would be."
- "If library X requires a long-lived TCP connection, treating it as a stateless RPC is the wrong shape."
- "If the failure happens before request routing, anything I add in the handler is the wrong shape."

A hypothesis you can't even imagine disproving isn't a hypothesis — it's a vibe with file paths. If you can't write the falsifier, the hypothesis isn't specific enough; sharpen it. Carry the falsifier into step 4 and test it alongside the assumptions.

### 3. Enumerate load-bearing assumptions

Write them down explicitly. An assumption is load-bearing if the plan **stops working** when the assumption is false. Examples:

- "Library X exposes method Y that returns Z"
- "The `customers` table has column `phone_e164` and it is unique per org"
- "This endpoint is reachable from the agent server without new auth"
- "The hatchet runner can hold this much state per task"

For each assumption, classify:

- **Verified** — already known true from reading current code/docs
- **Plausible** — best-guess; needs cheap validation
- **Risky** — the change pivots on this and a wrong answer kills the plan

Risky and plausible assumptions go into step 4. Verified ones get a citation (file:line or doc reference) and move on.

### 4. Validate assumptions

For each unverified assumption, pick the cheapest validation that produces real evidence:

| Assumption type | Validation |
|---|---|
| API behavior | Write a 10-30 line script, run it, capture the output. Or read the library source. |
| Library capability | Read the library docs *and* the code; docs lie, code does not |
| Internal code behavior | `grep` / `Read` the actual implementation on `HEAD`; do not trust memory |
| Schema / data shape | Query the dev DB (read-only) or read the migration files |
| System / infra behavior | Read the relevant config, IaC, or runtime docs; if cheap, run a probe |
| Performance / scale | Back-of-envelope first; only benchmark if the math is too close to call |
| External service | Read the vendor docs *and* check if there's already an integration in-repo to crib from |

Record each result as **confirmed**, **refuted**, or **partial**. For refuted assumptions, return to step 2 with new information — do not patch around the refutation.

For batched investigation (multiple parallel reads, broad searches), delegate to an Explore agent rather than draining the main context.

### 5. Cross-validate with product specs

Locate the specs touched by this change (e.g. `docs/product-spec/*.md`, plus any invariants doc the project maintains). For each:

- Does the proposed solution **satisfy** the relevant requirements?
- Does it **violate** any explicit invariant? (Customer data isolation, org isolation, RLS, auth boundaries, channel rules, billing semantics — these are the usual landmines.)
- Are there **acceptance criteria** the plan does not yet address?
- Is the change **mentioned** in the spec? If so, does our approach match the documented intent? If not, should the spec be updated as part of this work?

If a violation is found, the plan is not yet ready. Either change the plan or — if the spec is wrong — flag it explicitly to the user as a spec change that needs review *before* code work begins.

### 6. Cross-validate with architecture & conventions

Two failure modes this step catches: a plan that fights the architecture, and a plan that uses defaults from your training data instead of the project's actual conventions ("pnpm" when the repo uses yarn, "localhost:3000" when the API is on :9100, "param-style DI" when the codebase uses `vi.mock`). The second is by far the more common — and the more embarrassing, because it requires zero new thinking, just reading.

**6a. Architecture.** Check the proposed change against:

- **High-level architecture** — does it respect component boundaries (agent vs. portal vs. marketing)? Does it route data through the documented seams, not around them?
- **Security** — authn/authz at the right layer, no secret leakage, no new attack surface, input validation at boundaries.
- **Scalability & cost** — is the approach linear in the right dimension? Does it create N+1 queries, runaway fan-out, unbounded memory, or surprise cost?
- **Observability** — can we tell when it breaks in prod? Logs, metrics, traces — does the plan include them where they're load-bearing?
- **Background work** — anything async-and-retryable should run on Hatchet (or the project's equivalent), not as fire-and-forget.

**6b. Project conventions — read, enumerate, cite, and link to plan lines.** This is a discipline check, not a judgment call. You **must produce evidence** that you read the project's conventions docs on `HEAD`, not relied on memory or sensible defaults.

For each row below, name the file/section you consulted and the convention you found. If a row doesn't apply (e.g. the project has no schema migrations), say so explicitly — silent omission is the failure mode. Categories are universal; the *paths* are project-specific and must be discovered from the repo, not assumed.

| What to check | Where it lives (varies by project) | What to record |
|---|---|---|
| Root project conventions | `AGENTS.md` / `CLAUDE.md` / `README.md` at the repo root | One-line summary + the rules the plan touches |
| Per-component conventions | `<component>/AGENTS.md` (or equivalent) for every component the plan modifies | Local commands, code style, allowed/forbidden patterns |
| Package manager | Conventions doc, `package.json`, lockfile (or `Cargo.lock` / `uv.lock` / …) | `yarn` / `pnpm` / `npm` / `cargo` / `uv` — verify against the lockfile; do not default |
| Build / test / run entry points | The project's task runner — `justfile`, `Makefile`, package scripts, `cargo` aliases, etc. | The recipes the conventions doc names as canonical (do not infer from `package.json` scripts unless that *is* the documented convention) |
| Test framework + mocking policy | Conventions doc, sibling tests, framework config | Framework name, file-location convention (co-located vs `__tests__`), mocking style (module mocks vs param DI), coverage threshold |
| Lint / format | Conventions doc, tool config files | Tool name (biome / eslint / ruff / rustfmt / …), per-language rules |
| Migration / schema-change tooling (only if the plan touches schema) | Conventions doc, `migrations/` or equivalent | The exact command to scaffold a migration |
| Ports, URLs, environment | Root conventions doc | Local dev ports/URLs — don't guess at defaults |
| Long-running / async machinery (only if the plan touches it) | Conventions doc | Which platform handles retryable work; boundary rules |
| Existing patterns to reuse | Sibling files in the same directory | If a pattern already exists, reuse beats invention |
| Anything else the conventions doc flags | The conventions doc itself | Catch-all for project-specific rules not covered above |

**The output of this step is a bullet list inside the plan under "Project conventions to follow."** Each bullet has two parts, in this exact shape:

> - **[`file:line`]** Convention: *what the doc says.* → **Reflected in plan:** *which plan step(s) follow it, and how.*

If a convention doesn't constrain this particular plan, the right-hand side reads `Doesn't constrain this plan` plus a one-line reason. "Doesn't constrain" is a claim — defend it briefly. Silent omission is the failure mode the format exists to prevent.

If the proposal conflicts with any of these, prefer adjusting the proposal over arguing with the convention. If you genuinely think the convention is wrong here, say so — but as a separate conversation, not a silent deviation.

### 7. Sweep the codebase for hidden conflicts

Specs and architecture clearing the proposal doesn't mean the *codebase* will. File-existence and signature checks for files the plan touches belong in step 3 as load-bearing assumptions (e.g. *"`apps/web/src/foo.ts` exports `bar(x: X): Y`"*) and get validated in step 4. This step is for *systemic* surprises that wouldn't naturally appear as bullet assumptions:

- **In-flight work or recent commits** in the touched area — `git log` it. Someone else may already be doing this, or just blocked it.
- **Shadow duplication** — similar logic elsewhere in the repo that the plan should consolidate with, not branch from.
- **Caller-side drift** — if the plan changes a signature, contract, schema, or invariant, what *else* in the repo depends on the current shape? Grep for callers, schemas, fixtures, mocks.
- **Test infrastructure gaps** — does the layer of test the plan needs (unit / integration / e2e) actually exist for this area, or does the plan need to bring it up?

This step catches the surprises that aren't part of any single assumption but invalidate the plan in aggregate.

### 8. Loop or commit

After steps 4–7, one of three things is true:

1. **Hypothesis survived all validation** → proceed to step 9
2. **Hypothesis partially survived** → adjust the plan in-place; re-validate the changed parts; continue
3. **Hypothesis broken** → go back to step 2 with what you learned. Do not bolt fixes onto a broken approach.

Looping is normal and expected. The skill exists *because* first hypotheses are often wrong. A clean plan on the second or third iteration beats a brittle plan on the first.

Cap iterations at ~3 before pulling the user in. If after 3 rounds no hypothesis survives, the problem itself likely needs reframing — surface that.

### 8.5. Counterfactual: does the plan satisfy the success criteria?

Close the loop between the goal (step 1) and the plan about to be written. For each success criterion stated in step 1, name the plan step(s) that satisfy it. Land on one of:

- **Confirmed** — every criterion is satisfied by at least one plan step; cite which.
- **Confirmed with gaps** — some criteria need follow-up work or out-of-band steps; list them and surface as open questions or out-of-scope.
- **Unconfirmed** — at least one criterion has no plan step that satisfies it. **Stop.** Either extend the plan or explicitly descope the criterion with the user's agreement.

A plan whose own success criteria don't all map to plan steps is a list of activities, not a plan.

### 9. Write the plan

Structure (inverted pyramid):

1. **Headline** — one sentence: what we're building and why this approach
2. **Approach summary** — 3–6 bullets covering the shape of the change
3. **Plan** — ordered, concrete steps with file paths and the specific changes per step
4. **Assumptions validated** — bullet list with the evidence (file:line citation, experiment result, doc link)
5. **Risks & mitigations** — what could still go wrong; what we'll do if it does
6. **Out of scope** — what we're explicitly *not* doing, to prevent scope drift later
7. **Open questions** — anything the user still needs to decide *before* implementation
8. **Test plan** — unit, integration, e2e, manual — what each covers and which scenarios

Keep the plan as long as it needs to be and no longer. A plan that nobody reads is worse than one that's slightly too short.

### 10. Present and gate

Show the plan. If there are open questions, ask them explicitly and wait. If the plan involves an architectural deviation, a spec change, or a risky migration, **do not start implementing in auto mode** — get explicit user approval first.

If the plan is approved, implementation continues under normal rules (lint, test, commit hygiene, `/submit` for PRs).

## Anti-rationalization table

When tempted to skip or shortcut a step, check whether your reasoning appears below. If it does, the answer is: do the step.

| Rationalization | Why it fails here |
|---|---|
| "I already know how this library/API works." | Memory of third-party APIs decays; versions drift. Cost to confirm: minutes. Cost of being wrong: hours. Verify on the version actually in use. |
| "This change is small enough to skip validation." | If it were that small, the user would have invoked `/plan`, not `/blueprint`. The invocation itself is the signal that validation is required. |
| "The user is waiting — just commit to the hypothesis." | A wrong plan costs more wall-clock than a slow one. The whole reason this skill exists is to front-load the failure. |
| "I'll validate the risky assumption while implementing." | Validation discovered mid-implementation means rework, lost commits, and (worse) silent papering-over. Validate first. |
| "Reading the source is overkill — the docs say X." | Docs lie, code does not. For any load-bearing assumption, read the implementation. |
| "Three iterations is taking too long, let me just ship plan v3." | Three failed iterations means the problem needs reframing, not that the plan is ready. Surface to the user. |
| "There's no spec for this area, so cross-validation doesn't apply." | Absence of a spec is itself a signal — either propose one or flag that this work creates undocumented behavior. Don't silently skip. |
| "The proposed approach matches an existing pattern, so it must be fine." | Patterns get cargo-culted. Confirm the pattern still applies to *this* problem before reusing it. |
| "I'll just batch the validations in my head as I write the plan." | If they're not written down with evidence, they're not validated — they're just asserted in a more confident tone. |
| "TS monorepos usually use pnpm / Node servers usually run on :3000 / projects usually mock with `jest.mock`." | Defaults from training data are the most dangerous failure mode in convention-checking, because they feel right and require no work to invoke. Verify on the repo, not on the population. Pull the actual command, port, framework name from `AGENTS.md` or the relevant docs/ file. |

## Anti-patterns

- **Skipping validation because "I'm pretty sure."** That's exactly when validation pays. Memory is wrong more often than agents like to admit.
- **Validating only the easy assumptions.** The risky one is the one that needs the experiment. If validation feels uncomfortable, it's probably the right one.
- **Confusing breadth for depth.** Reading 40 files shallowly is not validation. One careful read of the load-bearing function is.
- **Writing the plan first, then justifying it.** The plan should fall out of the validation, not precede it.
- **Looping forever.** Three iterations should converge or escalate. Indefinite refinement is a stall, not a plan.
- **Producing a plan when the answer is "don't do this."** If validation reveals the change shouldn't ship, the deliverable is that conclusion — not a plan that ignores it.
- **Cross-validation theatre.** Citing a spec without showing how the plan satisfies it. Name the requirement and the line of the plan that addresses it.

## Definition of done

The skill is complete when **all** of these are true. Each item should be answerable with evidence, not a vibe.

- [ ] Problem statement (goal / constraints / non-goals / success criteria) restated; ambiguities resolved with the user, not invented.
- [ ] Hypothesis stated specifically enough to be falsifiable (named files, named APIs, named flows) **and** a disconfirming observation is written down — what would prove the hypothesis itself wrong, not just its individual assumptions.
- [ ] Every load-bearing assumption carries an evidence tag — a `file:line` citation, a quoted doc passage, a script's output, or a query result. No bare `[plausible]` or `[unverified]` tags survive into the final plan.
- [ ] Spec cross-validation: each affected requirement is named, and the plan line that satisfies it is named. Invariants explicitly checked (or a documented deviation flagged for user sign-off).
- [ ] Architecture cross-validation: any deviation is called out, not silent.
- [ ] Project-conventions cross-validation: each universal category (root + per-component conventions, package manager, build/test/run entry points, test framework + mocking policy, lint/format, migration tooling if schema is touched, ports/URLs, async machinery if relevant, reuse patterns) enumerated with `file:line` citations inside the plan, **and each bullet links to the plan step it shapes** (or is marked `Doesn't constrain this plan` with a reason). No defaults from training data — yours or the population's — sneaking in.
- [ ] Codebase conflict sweep performed: in-flight work, shadow duplication, caller-side drift (if signatures/schemas change), and test-infrastructure gaps all checked, with any findings reflected in the plan. (File-existence and signature checks live in the assumption list, not here.)
- [ ] Plan-vs-success-criteria counterfactual recorded as **Confirmed**, **Confirmed-with-gaps** (gaps listed), or **Unconfirmed** — and **Unconfirmed means the plan is not ready**.
- [ ] Plan document contains: headline, approach, ordered steps with file paths, validated assumptions with evidence, risks & mitigations, out-of-scope, open questions, test plan.
- [ ] Open questions surfaced to the user. None silently answered.
- [ ] If validation killed the hypothesis: the deliverable is the negative result and the reframing, not a salvaged plan.

If a checkbox cannot be ticked honestly, the skill is not done — return to the step that produces it.

## Relationship to other skills

- `/plan` — lighter; use when assumptions are mostly known and the change is straightforward
- `feedback_plan_validation_passes` — the three-pass validation discipline (assumption / spec+arch / edge-case) is roughly steps 4–7 here, applied at the end of *any* plan
- `/submit` — for landing the change once the plan executes

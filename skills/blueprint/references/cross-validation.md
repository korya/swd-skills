# Cross-validation: specs, architecture, conventions, codebase

Loaded from `SKILL.md` step 5. Covers steps 5, 6 and 7. The plan is checked against product
specs, against architecture, and against the project's own conventions with citations. Then
the codebase is swept for systemic conflicts.

## 5. Cross-validate with product specs

Locate the specs touched by this change, such as `docs/product-spec/*.md`, plus any
invariants doc the project maintains. For each:

- Does the proposed solution satisfy the relevant requirements?
- Does it violate any explicit invariant? Data isolation between customers or tenants,
  row-level security, auth boundaries, and billing semantics are the usual landmines.
- Are there acceptance criteria the plan does not yet address?
- Is the change mentioned in the spec? If so, does our approach match the documented intent?
  If not, should the spec be updated as part of this work?

If a violation is found, the plan is not yet ready. Either change the plan, or flag the spec
as wrong. A spec change needs the user's review before code work begins.

## 6. Cross-validate with architecture and conventions

This step catches two failure modes. The first is a plan that fights the architecture. The
second is a plan that uses defaults from your training data instead of the project's actual
conventions. Examples: "pnpm" when the repo uses yarn, "localhost:3000" when the API is on
:9100, "param-style DI" when the codebase uses `vi.mock`. The second is by far the more common, and
the more embarrassing. It requires zero new thinking, just reading.

**6a. Architecture.** Check the proposed change against:

- **High-level architecture.** Does it respect the documented component boundaries? Does it
  route data through the documented seams, not around them?
- **Security.** AuthN and authZ at the right layer, no secret leakage, no new attack surface,
  input validation at boundaries.
- **Scalability and cost.** Is the approach linear in the right dimension? Does it create N+1
  queries, runaway fan-out, unbounded memory, or surprise cost?
- **Observability.** Can we tell when it breaks in prod? Does the plan include logs, metrics,
  and traces where they are load-bearing?
- **Background work.** Anything async and retryable should run on the project's job
  platform, not as fire-and-forget.

**6b. Project conventions: read, enumerate, cite, and link to plan lines.** This is a
discipline check, not a judgment call. You must produce evidence that you read the project's
conventions docs on `HEAD`, not relied on memory or sensible defaults.

For each row below, name the file and section you consulted and the convention you found.
If a row does not apply, for example because the project has no schema migrations, say so.
Silent omission is the failure mode. The categories are universal. The paths are
project-specific and must be discovered from the repo, not assumed.

| What to check | Where it lives (varies by project) | What to record |
|---|---|---|
| Root project conventions | `AGENTS.md`, `CLAUDE.md`, or `README.md` at the repo root | One-line summary plus the rules the plan touches |
| Per-component conventions | `<component>/AGENTS.md` or equivalent for every component the plan modifies | Local commands, code style, allowed and forbidden patterns |
| Package manager | Conventions doc, `package.json`, lockfile (or `Cargo.lock`, `uv.lock`, and so on) | `yarn`, `pnpm`, `npm`, `cargo`, `uv`. Verify against the lockfile. Do not default. |
| Build, test, run entry points | The project's task runner: `justfile`, `Makefile`, package scripts, `cargo` aliases | The recipes the conventions doc names as canonical. Do not infer from `package.json` scripts unless that is the documented convention. |
| Test framework and mocking policy | Conventions doc, sibling tests, framework config | Framework name, file-location convention (co-located or `__tests__`), mocking style (module mocks or param DI), coverage threshold |
| Lint and format | Conventions doc, tool config files | Tool name (biome, eslint, ruff, rustfmt, and so on), per-language rules |
| Migration or schema-change tooling (only if the plan touches schema) | Conventions doc, `migrations/` or equivalent | The exact command to scaffold a migration |
| Ports, URLs, environment | Root conventions doc | Local dev ports and URLs. Do not guess at defaults. |
| Long-running or async machinery (only if the plan touches it) | Conventions doc | Which platform handles retryable work, and the boundary rules |
| Existing patterns to reuse | Sibling files in the same directory | If a pattern already exists, reuse beats invention |
| Anything else the conventions doc flags | The conventions doc itself | Catch-all for project-specific rules not covered above |

The output of this step is a bullet list inside the plan under "Project conventions to
follow". Each bullet has two parts, in this exact shape:

> - **[`file:line`]** Convention: *what the doc says.* **Reflected in plan:** *which plan
>   steps follow it, and how.*

A convention may not constrain this particular plan. Then the right-hand side reads
"Doesn't constrain this plan" plus a one-line reason. "Doesn't constrain" is a claim. Defend it
briefly. Silent omission is the failure mode the format exists to prevent.

If the proposal conflicts with any of these, prefer adjusting the proposal over arguing with
the convention. If you think the convention is wrong here, say so, as a separate
conversation, not as a silent deviation.

## 7. Sweep the codebase for hidden conflicts

Specs and architecture clearing the proposal does not mean the codebase will. File-existence
and signature checks for files the plan touches belong in step 3 as load-bearing assumptions,
for example "`apps/web/src/foo.ts` exports `bar(x: X): Y`". They get validated in step 4.
This step is for systemic surprises that would not appear as bullet assumptions:

- **In-flight work or recent commits** in the touched area. Run `git log` on it. Someone else
  may already be doing this, or may have just blocked it.
- **Shadow duplication.** Similar logic elsewhere in the repo that the plan should
  consolidate with, not branch from.
- **Caller-side drift.** If the plan changes a signature, contract, schema, or invariant,
  what else in the repo depends on the current shape? Grep for callers, schemas, fixtures,
  mocks.
- **Test infrastructure gaps.** Does the layer of test the plan needs (unit, integration,
  e2e) exist for this area, or does the plan need to bring it up?

This step catches the surprises that are not part of any single assumption but invalidate
the plan in aggregate.

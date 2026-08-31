# Cross-validation: specs, architecture, conventions, codebase

Loaded from `SKILL.md` step 5. Covers steps 5, 6 and 7 — the plan checked against product
specs, architecture, the project's own conventions (with citations), and the codebase for
systemic conflicts.

## 5. Cross-validate with product specs

Locate the specs touched by this change (e.g. `docs/product-spec/*.md`, plus any invariants doc the project maintains). For each:

- Does the proposed solution **satisfy** the relevant requirements?
- Does it **violate** any explicit invariant? (Data isolation between customers or tenants, row-level security, auth boundaries, billing semantics — the usual landmines.)
- Are there **acceptance criteria** the plan does not yet address?
- Is the change **mentioned** in the spec? If so, does our approach match the documented intent? If not, should the spec be updated as part of this work?

If a violation is found, the plan is not yet ready. Either change the plan or — if the spec is wrong — flag it explicitly to the user as a spec change that needs review *before* code work begins.

## 6. Cross-validate with architecture & conventions

Two failure modes this step catches: a plan that fights the architecture, and a plan that uses defaults from your training data instead of the project's actual conventions ("pnpm" when the repo uses yarn, "localhost:3000" when the API is on :9100, "param-style DI" when the codebase uses `vi.mock`). The second is by far the more common — and the more embarrassing, because it requires zero new thinking, just reading.

**6a. Architecture.** Check the proposed change against:

- **High-level architecture** — does it respect the documented component boundaries? Does it route data through the documented seams, not around them?
- **Security** — authn/authz at the right layer, no secret leakage, no new attack surface, input validation at boundaries.
- **Scalability & cost** — is the approach linear in the right dimension? Does it create N+1 queries, runaway fan-out, unbounded memory, or surprise cost?
- **Observability** — can we tell when it breaks in prod? Logs, metrics, traces — does the plan include them where they're load-bearing?
- **Background work** — anything async-and-retryable should run on the project's job platform, not as fire-and-forget.

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

## 7. Sweep the codebase for hidden conflicts

Specs and architecture clearing the proposal doesn't mean the *codebase* will. File-existence and signature checks for files the plan touches belong in step 3 as load-bearing assumptions (e.g. *"`apps/web/src/foo.ts` exports `bar(x: X): Y`"*) and get validated in step 4. This step is for *systemic* surprises that wouldn't naturally appear as bullet assumptions:

- **In-flight work or recent commits** in the touched area — `git log` it. Someone else may already be doing this, or just blocked it.
- **Shadow duplication** — similar logic elsewhere in the repo that the plan should consolidate with, not branch from.
- **Caller-side drift** — if the plan changes a signature, contract, schema, or invariant, what *else* in the repo depends on the current shape? Grep for callers, schemas, fixtures, mocks.
- **Test infrastructure gaps** — does the layer of test the plan needs (unit / integration / e2e) actually exist for this area, or does the plan need to bring it up?

This step catches the surprises that aren't part of any single assumption but invalidate the plan in aggregate.

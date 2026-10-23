# AGENTS.md

Operating manual for coding agents and humans working on this repo.

## What this project is

**<PROJECT NAME>** is <one paragraph: what it does, who it is for, current stage>.

<Optional: one or two design principles that drive everything>

## Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | <e.g., React + TypeScript + Vite> |
| Backend | <e.g., Node.js + tRPC> |
| Storage | <e.g., Postgres> |
| Package manager | <e.g., pnpm> |
| Task runner | <e.g., just> |

## Architecture in 30 seconds

```
<simple diagram or layered list>
```

See [`docs/architecture.md`](docs/architecture.md) for the full picture.

## Project layout

```
<repo-root>/
├── packages/<...>      <one-line description>
├── docs/               Reference docs (architecture, guidelines, product specs)
├── AGENTS.md           This file
└── ...
```

## Documentation index

Read these before working on related areas. `docs/product-specs/invariants.md` is the
floor. Anything that breaks an invariant needs explicit user confirmation.

Each product spec has a stable, globally unique ID of the form `PREFIX-NNN`, such as
`<CMP-009>`. Reference these IDs in code comments, tests, and PRs for durable traceability.

| When you are... | Read |
|--------------|------|
| Onboarding for the first time | This file, then [`docs/architecture.md`](docs/architecture.md), then [`docs/product-specs/README.md`](docs/product-specs/README.md) |
| Changing **product behavior** (feature, user-visible bug fix) | The relevant feature spec in [`docs/product-specs/`](docs/product-specs/) |
| Changing **architecture** (new layer, dependency, layer-crossing pattern) | [`docs/architecture.md`](docs/architecture.md) |
| Touching **how we work** (lint, tests, regression process) | [`docs/guidelines.md`](docs/guidelines.md) |
| Investigating **a regression** | [`docs/guidelines.md`](docs/guidelines.md), the 5-whys protocol |
| Wondering **how docs are managed** | [`docs/README.md`](docs/README.md) |

### Documents at a glance

| File | Prefix | Summary | Load when... |
|------|--------|---------|------------|
| [`AGENTS.md`](AGENTS.md) | none | This file. Project overview and doc index. | Always. First thing to read. |
| [`docs/README.md`](docs/README.md) | none | How to manage `docs/`, spec format requirements. | Editing or adding docs. |
| [`docs/architecture.md`](docs/architecture.md) | none | Architecture, layers, tech decisions, migration paths. | Touching boundaries, dependencies, layered concerns. |
| [`docs/guidelines.md`](docs/guidelines.md) | none | Lint, test, regression, and doc-update rules. | Onboarding, regressions, before any non-trivial change. |
| [`docs/product-specs/README.md`](docs/product-specs/README.md) | none | Spec format, prefix table, feature index. | Starting any spec-related work. |
| [`docs/product-specs/invariants.md`](docs/product-specs/invariants.md) | `INV` | Rules that must hold across all changes. | Before any change. **The floor.** |
| [`docs/product-specs/<feature>.md`](docs/product-specs/) | `<XXX>` | <feature summary> | <when to load> |

## Process rules

- **Lint and test 100% of code.** See [`docs/guidelines.md`](docs/guidelines.md).
- **Validate assumptions before depending on them.** A 30-second check beats hours of
  debugging.
- **Regression bug? Run the 5 whys** before patching. Document the root cause.
- **Doc changes need user confirmation.** Do not silently rewrite specs or architecture.
- **Surface conflicts.** If a change contradicts a spec or invariant, stop and discuss.
- **Reference spec IDs** in commit messages, code comments, tests, and PR descriptions.

## Running the project

```bash
<commands>
```

## Current state

<bullet list of what is done, in progress, and planned; optional>

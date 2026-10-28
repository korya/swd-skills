# AGENTS.md

Operating manual for coding agents and humans working on this repo.

## What this project is

**<PROJECT NAME>** is <one paragraph: what it does, who it is for, current stage>.

<Optional: the design principles that drive everything, each stated as a rule, such as
"The event log is the only source of truth." Do not open with a count of them.>

## Tech stack

| Layer | Choice |
|-------|--------|
| <e.g., Backend> | <e.g., Node.js + tRPC> |
| <e.g., Storage> | <e.g., Postgres> |

## Architecture in 30 seconds

```
<simple diagram or layered list>
```

See [`docs/architecture.md`](docs/architecture.md) for the full picture.

## Project layout

```
<repo-root>/
├── <dir>/      <one-line description>
├── docs/       Architecture, guidelines, product specs
└── AGENTS.md   This file
```

## Documentation index

Every product behavior has a stable ID of the form `PREFIX-NNN`, such as `<XXX>-009`. Cite
these IDs in code comments, tests, and PRs.

| File | Holds | Load when |
|------|-------|-----------|
| [`docs/product-specs/invariants.md`](docs/product-specs/invariants.md) | Rules that hold across every change. Prefix `INV`. | Before any change. **The floor.** |
| [`docs/architecture.md`](docs/architecture.md) | Layers, assumptions, tech choices. | Adding a layer, a dependency, or a layer crossing. |
| [`docs/guidelines.md`](docs/guidelines.md) | Lint, test, planning, and regression rules. | Before any non-trivial change, or on a regression. |
| [`docs/product-specs/README.md`](docs/product-specs/README.md) | Spec format and the spec index. | Writing or citing a spec. |
| [`docs/product-specs/<feature>.md`](docs/product-specs/) | <feature summary>. Prefix `<XXX>`. | <when to load> |
| [`docs/README.md`](docs/README.md) | How to manage `docs/`. | Adding or editing a doc. |

## Process rules

- **Lint and test all code.** See [`docs/guidelines.md`](docs/guidelines.md).
- **Validate assumptions before you depend on them.**
- **On a regression, run the 5 whys before you patch.** Report the root cause.
- **Surface conflicts.** If a change contradicts a spec, an invariant, or the architecture,
  stop and discuss.
- **The user confirms every doc change.** Never silently rewrite a spec or the
  architecture.

## Running the project

```bash
<commands>
```

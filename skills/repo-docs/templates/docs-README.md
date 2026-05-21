# docs/

Reference material for humans and coding agents working on this repo.

## What lives here

| Path | Purpose |
|------|---------|
| [`architecture.md`](architecture.md) | High-level architecture, layer boundaries, tech choices, future migration paths. |
| [`guidelines.md`](guidelines.md) | How to work in this repo — lint, test, planning, regression-bug protocol, doc updates. |
| [`product-specs/`](product-specs/) | Authoritative description of product behavior. Each item has a stable ID and is testable. |
| [`product-specs/invariants.md`](product-specs/invariants.md) | The floor — rules that hold across all changes. Prefix `INV`. |
| [`product-specs/README.md`](product-specs/README.md) | Spec format, prefix table, and feature index. |

## How to manage these docs

### Spec format requirements

Product specs follow a strict format (see [`product-specs/README.md`](product-specs/README.md) for examples and rationale):

- **Each spec describes a single, observable, deterministic behavior.** Written precisely enough that a tester can derive a verification path directly from the text — no separate "Testable:" appendix needed. If a spec needs a footnote to explain how to test it, rewrite the body.
- **Each spec has a globally unique ID** of the form `PREFIX-NUM` (e.g., `<XXX>-3`).
- **All specs in one file share a prefix.** `NUM` is unique within the file.
- **IDs are stable.** Don't renumber. Deleted specs leave a hole; new specs get the next free number.

**Invariants** ([`product-specs/invariants.md`](product-specs/invariants.md), prefix `INV`) are different — they describe conditions that hold across the whole product, not feature behaviors. They use the same ID format but don't have to be testable in isolation. They're upheld by code, architecture, and process together.

### Process rules

- **Treat docs as code.** Reviewable, version-controlled, kept in sync with implementation.
- **Confirm changes with the user.** Never silently update a spec or architecture doc. The user signs off.
- **Surface conflicts.** If implementation contradicts a doc, stop and discuss. Either the doc is stale or the change is wrong.
- **Reference spec IDs in code, tests, and PRs.** Comments like `// implements <XXX>-9` and PR titles like "fixes regression of <XXX>-5" make traceability durable.
- **Use absolute dates** (`2026-05-07`), never relative ones (`yesterday`, `next Tuesday`). Relative dates rot.
- **Inverted pyramid.** Most important info first; details after.

## When to update what

| Trigger | Update |
|---------|--------|
| Product behavior change | Relevant `product-specs/<feature>.md` |
| New invariant discovered | `product-specs/invariants.md` |
| Architectural change | `architecture.md` |
| New best practice or workflow rule | `guidelines.md` |
| New top-level doc | `docs/README.md` index + [`AGENTS.md`](../AGENTS.md) index |

## When NOT to write a doc

- For a one-off task. Tasks live in conversations; docs live in the repo.
- For a design exploration that hasn't landed.
- For something already covered. Update the existing doc instead of fragmenting.

## File naming

- Lowercase, kebab-case (`product-specs/companies.md`, not `Companies.md`).
- Match feature names from the spec where possible.

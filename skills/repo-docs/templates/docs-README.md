# docs/

Reference material for humans and coding agents working on this repo.

## What lives here

| Path | Purpose |
|------|---------|
| [`architecture.md`](architecture.md) | High-level architecture, layer boundaries, tech choices, future migration paths. |
| [`guidelines.md`](guidelines.md) | How to work in this repo: lint, test, planning, regression protocol, doc updates. |
| [`product-specs/`](product-specs/) | Authoritative description of product behavior. Each item has a stable ID and is testable. |
| [`product-specs/invariants.md`](product-specs/invariants.md) | The floor: rules that hold across all changes. Prefix `INV`. |
| [`product-specs/README.md`](product-specs/README.md) | Spec format, prefix table, and feature index. |

## How to manage these docs

### Spec format requirements

Product specs follow a strict format. See [`product-specs/README.md`](product-specs/README.md)
for examples and rationale.

- **Each spec describes one observable, deterministic behavior.** It is precise enough
  that a tester can derive a verification path from the text alone. There is no separate
  "Testable:" appendix. If a spec needs a footnote on how to test it, rewrite the body.
- **Each spec has a globally unique ID** of the form `PREFIX-NNN`, such as `<XXX>-003`.
- **All specs in one file share a prefix.** The number is unique within the file.
- **IDs are stable.** Never renumber. A deleted spec leaves a hole. A new spec gets the
  next free number.

**Invariants** in [`product-specs/invariants.md`](product-specs/invariants.md), prefix
`INV`, are different. They describe conditions that hold across the whole product, not
feature behaviors. They use the same ID format but need not be testable in isolation.
Code, architecture, and process uphold them together.

### Process rules

- **Treat docs as code.** Reviewable, version-controlled, kept in sync with the
  implementation.
- **Confirm changes with the user.** Never silently update a spec or an architecture doc.
  The user signs off.
- **Surface conflicts.** If the implementation contradicts a doc, stop and discuss. Either
  the doc is stale or the change is wrong.
- **Reference spec IDs in code, tests, and PRs.** A comment like `// implements <XXX>-009`
  and a PR title like "fixes regression of <XXX>-005" make traceability durable.
- **Use absolute dates** such as `2026-05-07`, never relative ones such as "yesterday".
  Relative dates rot.
- **Most important information first.** Details after.

## When to update what

| Trigger | Update |
|---------|--------|
| Product behavior change | The relevant `product-specs/<feature>.md` |
| New invariant discovered | `product-specs/invariants.md` |
| Architectural change | `architecture.md` |
| New best practice or workflow rule | `guidelines.md` |
| New top-level doc | The `docs/README.md` index and the [`AGENTS.md`](../AGENTS.md) index |

## When not to write a doc

- For a one-off task. Tasks live in conversations. Docs live in the repo.
- For a design exploration that has not landed.
- For something already covered. Update the existing doc instead of fragmenting.

## File naming

- Lowercase, kebab-case: `product-specs/companies.md`, not `Companies.md`.
- Match feature names from the spec where possible.

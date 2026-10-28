# docs/

Reference material for humans and coding agents. [`../AGENTS.md`](../AGENTS.md) indexes
every file here. The spec format lives in
[`product-specs/README.md`](product-specs/README.md).

## Rules for these docs

- **Treat docs as code.** They are reviewed, version-controlled, and kept in sync with the
  implementation.
- **The user confirms every change.** A spec change is a deliberate act, never a side
  effect.
- **Surface conflicts.** If the code contradicts a doc, stop and discuss. Either the doc is
  stale or the change is wrong.
- **Each fact has one home.** Link to it instead of restating it.
- **Use absolute dates** such as `2026-05-07`, never "yesterday".

## When to update what

| Trigger | Update |
|---------|--------|
| Product behavior change | The relevant `product-specs/<feature>.md` |
| New cross-cutting rule | `product-specs/invariants.md` |
| Architectural change | `architecture.md` |
| New workflow rule | `guidelines.md` |
| New doc | The index in [`../AGENTS.md`](../AGENTS.md) |

## When not to write a doc

- For a one-off task. Tasks live in conversations.
- For a design exploration that has not landed.
- For something already covered. Update the existing doc instead.

## File naming

Lowercase kebab-case that matches the feature name: `product-specs/companies.md`, not
`Companies.md`.

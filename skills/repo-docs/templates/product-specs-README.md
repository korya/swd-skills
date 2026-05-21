# Product Specs

Authoritative description of what the product does. Each spec describes a behavior that can be tested.

## Spec format

Every feature spec is:

- **Behavioral.** Describes what the system does, not how it's implemented.
- **Self-evidently testable.** Written precisely enough that a tester (human or agent) can derive a verification path without further explanation. The goal isn't to enumerate every test case — it's to make the spec unambiguous enough to apply to the product.
- **Identified.** Each item has a globally unique ID `PREFIX-NUM`:
  - All specs in one file share the prefix (e.g., `<XXX>` in `<feature>.md`).
  - `NUM` is unique within the file and never reused (deleted specs leave a hole rather than getting reassigned).
  - IDs are stable references — cite them in code comments, tests, PRs, and other docs.

Example:

```
### <XXX>-3: Lifecycle stage values
Lifecycle stage is one of: `Lead`, `MQL`, `SQL`, `Customer`, `Lost`, `Disqualified`.
Configurable via `settings.lifecycle_stages`. Values outside this list are
rejected at validation.
```

That's the whole spec. No "Testable:" appendix — the body itself is precise enough that a test ("set `lifecycle_stage` to `Banana`, expect validation error") falls out of it directly.

### What "testable" means here

Specs are written so that:
- The behavior is **observable** — you can tell from outside whether the system follows the rule.
- The behavior is **deterministic** — the spec doesn't leave undefined edge cases to guess at.
- The behavior is **decoupled from implementation** — describes what, not how.

If you can read a spec and immediately picture how to write a test for it, the spec is doing its job. If you need an attached "Testable:" hint to figure that out, the spec text needs rewording, not a footnote.

### Invariants are different

[`invariants.md`](invariants.md) (`INV-*`) describes conditions that hold across the system — properties of the architecture and process, not feature behaviors. **Invariants don't have to be testable in isolation.** They're upheld by code reviews, architectural boundaries, and process rules together.

## Prefix table

| File | Prefix |
|------|--------|
| [`invariants.md`](invariants.md) | `INV` |
| [`<feature>.md`](<feature>.md) | `<XXX>` |
| ... | ... |

## How to use these

- **Before changing product behavior** (a feature or a user-visible bug fix): read the relevant spec file. If your change contradicts an item, stop and surface it for discussion.
- **In doubt:** [`invariants.md`](invariants.md) is the floor. Anything that breaks an invariant requires explicit user confirmation.
- **In tests and PRs:** reference spec IDs (e.g., "implements <XXX>-5", "regression of <XXX>-9") so traceability is durable.

## Index

| File | What's inside |
|------|---------------|
| [`invariants.md`](invariants.md) | Rules that hold across every change. **Read first.** |
| [`<feature>.md`](<feature>.md) | <one-line summary> |
| ... | ... |

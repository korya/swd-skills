# Product Specs

Authoritative description of what the product does. Each spec describes a behavior that
can be tested.

## Spec format

Every feature spec is:

- **Behavioral.** It describes what the system does, not how it is implemented.
- **Self-evidently testable.** It is precise enough that a tester, human or agent, can
  derive a verification path without further explanation. The goal is not to enumerate
  every test case. The goal is a spec unambiguous enough to apply to the product.
- **Identified.** Each item has a globally unique ID `PREFIX-NNN`:
  - All specs in one file share the prefix, such as `<XXX>` in `<feature>.md`.
  - `NNN` is a zero-padded three-digit number, unique within the file and never reused.
    A deleted spec leaves a hole rather than a reassigned number. Sub-cases that share
    preconditions may take a letter suffix, such as `<XXX>-012A`.
  - IDs are stable references. Cite them in code comments, tests, PRs, and other docs.

Example:

```
### <XXX>-003: Lifecycle stage values
Lifecycle stage is one of: `Lead`, `MQL`, `SQL`, `Customer`, `Lost`, `Disqualified`.
Configurable via `settings.lifecycle_stages`. Values outside this list are
rejected at validation.
```

That is the whole spec. There is no "Testable:" appendix. The body is precise enough that a
test falls out of it directly: set `lifecycle_stage` to `Banana`, expect a validation error.

### What "testable" means here

Specs are written so that:

- The behavior is **observable**. You can tell from outside whether the system follows the
  rule.
- The behavior is **deterministic**. The spec leaves no undefined edge case to guess at.
- The behavior is **decoupled from implementation**. It describes what, not how.

If you can read a spec and picture the test at once, the spec is doing its job. If you need
an attached "Testable:" hint to get there, the spec text needs rewording, not a footnote.

### Invariants are different

[`invariants.md`](invariants.md), prefix `INV`, describes conditions that hold across the
system. They are properties of the architecture and the process, not feature behaviors.
Feature-local invariants, rules enforced only inside one feature, stay in that feature's
file as prose contracts without numeric IDs. Invariants need not be testable in isolation.
Code reviews, architectural boundaries, and process rules uphold them together.

## Prefix table

| File | Prefix |
|------|--------|
| [`invariants.md`](invariants.md) | `INV` |
| [`<feature>.md`](<feature>.md) | `<XXX>` |
| ... | ... |

## How to use these

- **Before changing product behavior**, a feature or a user-visible bug fix, read the
  relevant spec file. If your change contradicts an item, stop and surface it.
- **In doubt**, [`invariants.md`](invariants.md) is the floor. Anything that breaks an
  invariant requires explicit user confirmation.
- **In tests and PRs**, reference spec IDs, as in "implements <XXX>-005" or "regression of
  <XXX>-009", so traceability is durable.

## Index

| File | What is inside |
|------|---------------|
| [`invariants.md`](invariants.md) | Rules that hold across every change. **Read first.** |
| [`<feature>.md`](<feature>.md) | <one-line summary> |
| ... | ... |

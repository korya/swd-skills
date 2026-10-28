# Product Specs

Authoritative description of what the product does. This file is the home of the spec
format. Every other doc links here instead of restating it.

## Spec format

Every feature spec is:

- **Behavioral.** It describes what a user or a caller can observe, not how the code does
  it. No function, class, field, or file names.
- **Testable.** It is precise and deterministic enough that a tester derives the test from
  the body alone. There is no separate "Testable:" line. If a spec needs one, rewrite the
  body.
- **Identified.** The heading is `### PREFIX-NNN: Short title`. All specs in one file share
  the prefix. `NNN` is a zero-padded three-digit number, unique within the file. Two cases
  that differ on one variable may take a letter suffix, such as `<XXX>-012A`.

IDs are stable. Never renumber. A deleted spec leaves a hole, and a new spec gets the next
free number. Code comments, tests, and PRs cite the IDs.

A spec is one tight assertion. Rationale goes in [`../architecture.md`](../architecture.md)
or in the PR. A thing with no observable behavior, such as the build system, gets no spec
file.

Example:

```
### <XXX>-003: Lifecycle stage values
Lifecycle stage is one of: `Lead`, `MQL`, `SQL`, `Customer`, `Lost`.
Any other value is rejected with a validation error.
```

## Invariants

[`invariants.md`](invariants.md), prefix `INV`, holds conditions that span the whole
system. They use the same ID format but need not be testable in isolation. A rule that only
one feature enforces stays in that feature's file as a prose contract without an ID.

## Index

| File | Prefix | What is inside |
|------|--------|----------------|
| [`invariants.md`](invariants.md) | `INV` | Rules that hold across every change. **Read first.** |
| [`<feature>.md`](<feature>.md) | `<XXX>` | <one-line summary> |

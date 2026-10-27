# Product Specs

Authoritative description of what ticketdesk does. Each spec describes a behavior that
can be tested.

## Spec format

Every feature spec is:

- **Behavioral.** It describes what the system does, not how it is implemented.
- **Self-evidently testable.** It is precise enough that a tester, human or agent, can
  derive a verification path without further explanation. The goal is not to enumerate
  every test case. The goal is a spec unambiguous enough to apply to the product.
- **Identified.** Each item has a globally unique ID `PREFIX-NNN`:
  - All specs in one file share the prefix, such as `TKT` in `tickets.md`.
  - `NNN` is a zero-padded three-digit number, unique within the file and never reused.
    A deleted spec leaves a hole rather than a reassigned number. Sub-cases that share
    preconditions may take a letter suffix, such as `TKT-012A`.
  - IDs are stable references. Cite them in code comments, tests, PRs, and other docs.

Example, taken from [`tickets.md`](tickets.md):

```
### TKT-003: Priority values
The priority of a ticket is one of: `P1`, `P2`, `P3`. Creating a ticket with any other
priority fails with an error that names the rejected value and the allowed values. No
ticket is created.
```

That is the whole spec. There is no "Testable:" appendix. The body is precise enough that a
test falls out of it directly. Create a ticket with priority `P9`. Expect an error that
mentions `P9` and the three allowed values. Expect the ticket list unchanged.

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
file as prose contracts without numeric IDs. An example is "a ticket moves forward only"
in `tickets.md`. Invariants need not be testable in isolation. Code reviews, architectural
boundaries, and process rules uphold them together.

## Prefix table

| File | Prefix |
|------|--------|
| [`invariants.md`](invariants.md) | `INV` |
| [`tickets.md`](tickets.md) | `TKT` |
| [`event-log.md`](event-log.md) | `LOG` |
| [`cli.md`](cli.md) | `CLI` |

## How to use these

- **Before changing product behavior**, a feature or a user-visible bug fix, read the
  relevant spec file. If your change contradicts an item, stop and surface it.
- **In doubt**, [`invariants.md`](invariants.md) is the floor. Anything that breaks an
  invariant requires explicit user confirmation.
- **In tests and PRs**, reference spec IDs, as in "implements TKT-005" or "regression of
  LOG-007", so traceability is durable.

There is no master spec beyond these files. The repo README is a summary, not a spec.

## Index

| File | What is inside |
|------|---------------|
| [`invariants.md`](invariants.md) | Rules that hold across every change. **Read first.** |
| [`tickets.md`](tickets.md) | Ticket lifecycle: states, creation rules, assignment, closing, due time by priority, listing. |
| [`event-log.md`](event-log.md) | The append-only JSON lines log: event kinds and fields, replay, the corrupt-line rule, the missing-file case. |
| [`cli.md`](cli.md) | The `ticketdesk` command: subcommands, log path selection, output lines, error reporting, exit codes. |

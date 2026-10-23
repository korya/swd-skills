# Spec format rules and anti-patterns

Loaded from `SKILL.md` before writing any spec or invariant. The rules are not negotiable.
The anti-patterns are the ways they get broken in practice.

## The three rules

Each feature spec is:

1. **Behavioral.** It describes what the system does, not how it is implemented. "Lifecycle
   stage is one of ...", not "the `LifecycleEnum` Zod schema validates input".
2. **Self-evidently testable.** It is precise enough that a tester can derive a
   verification path from the body alone. No separate `**Testable:**` line. If you want to
   add one, rewrite the body until it is not needed.
3. **Identified.** The heading is `### PREFIX-NNN: Short title`. PREFIX is shared by all
   specs in one file, such as `CMP` in `companies.md`. NNN is a zero-padded three-digit
   number, unique within the file and never reused. `CMP-001`, `CMP-010`, `CMP-100` sort
   in order. Two cases that share preconditions and differ on one variable may take a
   sub-case letter: `CMP-012A`, `CMP-012B`.

## Invariants are different

- They are cross-cutting only and live in `invariants.md` with the same ID format, such as
  `INV-007`. They state system-wide properties, not feature behaviors.
- A rule enforced only inside one feature stays in that feature's file as a prose
  contract, without a numeric ID.
- They need not be testable in isolation. Code reviews, architectural boundaries, and
  process uphold them together.
- Examples: "agents never write raw cells", "all writes append to change_log".

## ID stability

- Never renumber. A deleted spec leaves a hole. A new spec gets the next free number.
- IDs are stable references. Code comments, tests, PR descriptions, and other docs cite
  them.

## Anti-patterns

- Specs that describe implementation. "The `validateLifecycle` function returns false for
  invalid stages" is not a spec. "Lifecycle stage is one of ..." is.
- A `**Testable:**` line. If the body is not testable, rewrite the body.
- Renumbered IDs, even when a deletion leaves `CMP-001, CMP-002, CMP-004`.
- Specs silently updated to match the implementation. Specs lead. If the implementation
  diverged, surface the conflict.
- Spec files for things without observable product behavior, such as the build system.
  Those belong in architecture.
- Narrative or rationale in spec files. Each spec is a tight assertion. Rationale lives in
  architecture or in PR descriptions.
- Files created without confirming with the user when bootstrapping a new repo.

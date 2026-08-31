# Spec format rules and anti-patterns

Loaded from `SKILL.md` before writing any spec or invariant. The rules are non-negotiable;
the anti-patterns are the ways they get broken in practice.

## Spec format — non-negotiable rules

**Each feature spec is:**

1. **Behavioral.** Describes *what* the system does, not *how* it's implemented. "Lifecycle stage is one of …", not "the `LifecycleEnum` Zod schema validates input".
2. **Self-evidently testable.** Written precisely enough that a tester can derive a verification path directly from the body. **No separate `**Testable:**` line.** If you find yourself wanting to add one, rewrite the body until it's no longer needed.
3. **Identified.** `### PREFIX-NUM: Short title` heading. PREFIX is shared by all specs in one file (e.g., `CMP` in `companies.md`). NUM is unique within the file and never reused.

**Invariants are different:**
- Same ID format (e.g., `INV-7`) but they describe system-wide properties, not feature behaviors.
- They don't have to be testable in isolation — they're upheld by code reviews, architectural boundaries, and process together.
- Examples: "agents never write raw cells", "all writes append to change_log".

**ID stability:**
- Don't renumber. Deleted specs leave a hole; new specs get the next free number.
- IDs are stable references — code comments, tests, PR descriptions, and inter-doc links cite them.

## Anti-patterns to avoid

- **Don't** write specs that describe implementation. "The `validateLifecycle` function returns false for invalid stages" is not a spec; "Lifecycle stage is one of …" is.
- **Don't** add a `**Testable:**` line. If the body isn't already testable, rewrite the body.
- **Don't** renumber spec IDs. Ever. Even if a deletion leaves `CMP-1, CMP-2, CMP-4`.
- **Don't** silently update specs to match implementation. Specs lead; if implementation diverged, surface the conflict.
- **Don't** create feature spec files for things that don't have observable product behavior (e.g., "build system" — that goes in architecture).
- **Don't** put narrative or rationale in spec files. Each spec is a tight assertion. Rationale lives in architecture or PR descriptions.
- **Don't** create files without confirming with the user when bootstrapping a new repo.

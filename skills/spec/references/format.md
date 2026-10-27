# The default spec format

Loaded from `SKILL.md` step 1 when the repo has no spec convention of its own. This is the
same convention `/repo-docs` bootstraps. A repo set up with it needs nothing here beyond the
reminder that the repo's own `docs/product-specs/README.md` is the authority.

## Location

`docs/product-specs/<feature>.md`, one feature area per file. The directory's `README.md`
holds the format rules, the prefix table, and the index. `invariants.md` holds the
cross-cutting invariants. Adding a file means updating both tables in `README.md` and
picking an unused prefix: three to six uppercase letters from the feature's distinctive
noun.

## The feature file

Start with a one-paragraph intro: what the feature is, why it exists, the key terms. The
goals live here, compressed. Then `Prefix: XXX`, an optional short **Non-goals** list
(the boundary is part of the contract), then the criteria:

```markdown
### XXX-NNN: Short title
<1 to 3 sentences of behavior, precise enough that a test falls out of it directly.>
```

- **One assertion per criterion.** Observable, deterministic, implementation-free. No
  function, class, schema, or file names. Exact value lists for enums ("one of: A, B, C").
  Config keys when behavior is configurable.
- **Error and edge behavior are criteria too**, not implications. What the user sees when
  it goes wrong gets its own ID.
- **No `**Testable:**` appendix, no narrative, no rationale.** Rewrite the body until it is
  self-evidently testable. Rationale lives in architecture docs or the PR.

## IDs

- `NNN` is a zero-padded three-digit number. `PFX-001`, `PFX-010`, `PFX-100` sort in order.
  Ascending within the file.
- **Append-only.** New criteria take the next free number. Deletions leave holes.
  Renumbering never happens. IDs are cited from code comments, tests, PRs, and other specs,
  and a renumber breaks every citation silently.
- Sub-cases that share preconditions and differ on one variable take a letter suffix:
  `PFX-012A`, `PFX-012B`.
- Cite across files with the bare ID, as in "see BILL-003". The prefix already names the
  file.

## Invariants, two tiers

- **Cross-cutting.** A rule several subsystems must respect, or a security, data-privacy,
  or billing-integrity property. It gets `INV-NNN` in `invariants.md`. The litmus test:
  would a security reviewer want it findable in one place?
- **Feature-local.** Enforced only inside this feature. It is a prose contract in the
  feature file, with no numeric ID, referenced by the criteria that exercise it.

## Open questions and assumptions

They exist only before sign-off. The draft carries them explicitly: an `Open questions`
block at the end, and assumptions marked inline. Sign-off resolves each one into a
criterion, a non-goal, or a deliberate deletion. The merged spec file carries none.

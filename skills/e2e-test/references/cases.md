# The case list: scope and derivation

Loaded from `SKILL.md` step 2. Every case on the list gets a verdict. A case left out on
purpose appears in the report as untested. A list improvised during testing bends toward
whatever was easy to test.

## Scope

The default is the change and its blast radius:

- **The change itself.** Every user-visible behavior added or altered on the branch or PR.
  Inventory it from the diff against the merge base and from the PR or issue description.
  Test the promised behavior, not just the implemented one.
- **Affected specs.** Cover every criterion of the specs the change touches, not only the
  ones the diff obviously maps to.
- **Blast radius.** Features that share the changed code paths, data models, or entry
  points. Screens around a changed screen. Each permission tier that reaches the changed
  behavior.

The PR description says what the change promises, and its other claims are not evidence.
"All tests pass" or "no new dependencies" stays the PR's claim until you observe it.
Report it as unchecked, and draw no conclusion from it.

A full-product sweep happens only when the user asks for one. Then the spec set, or the
product's navigable surface, is the inventory, and the change still gets the deepest
coverage.

## Deriving cases

One case is one user-observable scenario with an expected outcome you could state before
running it. For every behavior in scope:

- **Happy path.** The documented, intended flow.
- **Edges.** Boundaries, empty states, unusual but legal input, repeated actions.
- **Error path.** What the user sees when it goes wrong: bad input, missing permissions,
  unavailable dependencies. "Fails gracefully with a useful message" is an expected outcome
  too.

Cases assume a first-time user. When a scenario needs existing state, creating that state
through the surface is part of the case.

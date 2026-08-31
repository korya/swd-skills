# The case list: scope, derivation, depth

Loaded from `SKILL.md` step 2. The case list is written **before** any testing and is the
contract for the rest of the run: what appears here gets a verdict, and what was
deliberately left out appears in the report as untested. A case list improvised during
testing bends toward whatever was easy to test.

## Scope

Default — the change and its blast radius:

- **The change itself**: every user-visible behavior added or altered on the branch or
  PR. Inventory from the diff against the merge base and from the PR/issue description —
  the *promised* behavior, not just the implemented one.
- **Affected specs**: product specs whose requirements the change touches. When the repo
  keeps acceptance criteria with IDs, cite the ID per case and cover every criterion of
  the affected specs — not only the ones the diff obviously maps to.
- **Blast radius**: adjacent logic that could regress — features sharing the changed code
  paths, data models, or entry points; screens surrounding a changed screen; each
  permission tier that reaches the changed behavior. The regression nobody looked for is
  the one that ships.

A full-product sweep happens only when the user asks for one; then the spec set (or the
product's navigable surface) is the inventory, and the change still gets the deepest
coverage.

## Deriving cases

One case = one user-observable scenario with an expected outcome you could state before
running it. For every behavior in scope:

- **Happy path** — the documented, intended flow.
- **Edges** — boundaries, empty states, unusual-but-legal input, repeated actions.
- **Error path** — what the user sees when it goes wrong: bad input, missing
  permissions, unavailable dependencies. "Fails gracefully with a useful message" is an
  expected outcome too.

From-scratch rule: cases assume a first-time user. When a scenario needs pre-existing
state, creating that state through the surface is part of the case, not a given.

## Report depth

Set it now, from the invocation's wording, and say which you chose:

- **Lean** — a quick or narrowly-scoped ask ("re-test the login flow"): headline verdict,
  case table, details per non-PASS.
- **Comprehensive** — "comprehensive", "thorough", "from scratch", "next stop is prod",
  or a release gate: the lean report plus missing cases, issues by severity, UX gaps,
  improvements worth doing, leftover artifacts.

When genuinely ambiguous, comprehensive — nobody was ever hurt by the fuller report.

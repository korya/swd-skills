# System Invariants

Conditions that hold across the product. Code reviews, architecture, and process uphold
them together, so they need not be testable in isolation. Breaking one is a deliberate
decision that the user confirms first.

Prefix: `INV`.

---

### INV-001: <Short title>

<1 to 3 sentences on the condition.>

### INV-002: <Short title>

<...>

<!--
  Places to look (delete this comment when the file is filled in). Record only what the
  code enforces:
  - single source of truth for data
  - append-only or audited writes
  - stable IDs, not row numbers or array indices
  - soft deletes only
  - fail fast on schema drift
-->

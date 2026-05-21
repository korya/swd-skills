# System Invariants

Conditions that hold across the product. Unlike feature specs, invariants don't have to be testable in isolation — they're properties of the system as a whole. Code reviews, architecture decisions, and process all uphold them together.

Breaking an invariant is a deliberate decision, not a side effect. If a change requires it, surface it for discussion before proceeding.

Prefix: `INV`.

---

### INV-1: <Short title>

<1–3 sentence description of the condition. Examples: "All writes append to change_log", "Storage adapter is the only Sheets-aware code", "No raw cell writes from agents or UI".>

### INV-2: <Short title>

<...>

<!--
  Common invariants worth considering for most projects:
  - Single source of truth for data
  - Schema validation at startup
  - Stable IDs (not row numbers / array indices)
  - Soft deletes only
  - All writes audited (change log)
  - No silent corruption (fail fast on schema drift)
  - Doc/code reconciliation rule
  - Doc changes require user confirmation
-->

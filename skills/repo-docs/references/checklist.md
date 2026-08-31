# Required content per file, and size budgets

Loaded from `SKILL.md` step 3, before creating files. Each file's checklist is what the
definition of done checks against; the budgets keep the layout navigable.

## Required content checklist

### AGENTS.md
- [ ] One-paragraph "what this project is"
- [ ] Tech stack table
- [ ] Architecture in 30 seconds (diagram or short list of layers)
- [ ] Project layout (directory tree)
- [ ] Documentation index — table with file path, summary, "load when…"
- [ ] Process rules (lint, test, regression protocol, doc confirmation)
- [ ] Reference to spec ID convention

### docs/architecture.md
- [ ] High-level diagram or layer description
- [ ] Why each layer exists (one paragraph each)
- [ ] Key technical assumptions (e.g., concurrency model, data flow, auth)
- [ ] Tech choices table with reasons
- [ ] Future migration paths (if relevant)
- [ ] What's intentionally simple in v1 (if relevant)

### docs/guidelines.md
- [ ] Lint 100% of code
- [ ] Test 100% of code (or stated project coverage policy)
- [ ] **Planning checklist (mandatory for every plan):**
  1. Validate assumptions
  2. Cross-validate the proposed solution against product specs (every affected spec ID)
  3. Cross-validate against the system architecture (boundaries, assumptions)
  4. Plan automated test coverage for new logic (per coverage policy)
  5. Plan end-to-end tests for the proposed solution
- [ ] On product behavior change → consult product specs
- [ ] On architecture change → consult architecture doc
- [ ] On any conflict → bring up for discussion before proceeding
- [ ] On regression → conduct a CRA using the 5-whys, report root cause **before** attempting a fix
- [ ] Keep specs and architecture updated, but **confirm every change with the user**

### docs/product-specs/README.md
- [ ] Spec format requirements (behavioral, testable, identified)
- [ ] Distinction between feature specs and invariants
- [ ] Prefix table (one row per spec file)
- [ ] Spec file index with one-line summaries
- [ ] Reference to master spec if one exists

### docs/product-specs/invariants.md
- [ ] Brief intro: what an invariant is, why it's not testable-in-isolation
- [ ] Each invariant: `### INV-N: Short title` + 1–3 sentence body

### docs/product-specs/<feature>.md
- [ ] Brief intro paragraph
- [ ] `Prefix: \`XXX\`.` line
- [ ] `---` separator
- [ ] Each spec: `### XXX-N: Short title` + 1–3 sentence body that's precise enough to derive a test from

### docs/README.md
- [ ] What lives in `docs/` (table)
- [ ] Spec format requirements (testability, IDs, stability)
- [ ] Process rules (treat docs as code, confirm with user, surface conflicts, reference IDs)
- [ ] When to update what (table)
- [ ] When NOT to write a doc
- [ ] File naming convention

## Concise > comprehensive

The whole point of this layout is that an agent (or human) can quickly find the doc that answers their question. Long docs defeat that purpose. Aim for:
- AGENTS.md: ~150 lines
- Each feature spec: 5–15 specs, each 1–3 sentences
- Architecture: 1–3 pages, mostly tables and diagrams

If a spec file is growing past ~15 items, consider splitting it.

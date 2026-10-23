# Required content per file, and size budgets

Loaded from `SKILL.md` step 3, before creating files. Each file's checklist is what the
definition of done checks against. The budgets keep the layout navigable.

## Required content checklist

### AGENTS.md
- [ ] One paragraph on what this project is
- [ ] Tech stack table
- [ ] Architecture in 30 seconds: a diagram or a short list of layers
- [ ] Project layout as a directory tree
- [ ] Documentation index: a table with file path, summary, and "load when"
- [ ] Process rules: lint, test, regression protocol, doc confirmation
- [ ] Reference to the spec ID convention

### docs/architecture.md
- [ ] High-level diagram or layer description
- [ ] Why each layer exists, one paragraph each
- [ ] Key technical assumptions, such as the concurrency model, data flow, or auth
- [ ] Tech choices table with reasons
- [ ] Future migration paths, if relevant
- [ ] What is intentionally simple in v1, if relevant

### docs/guidelines.md
- [ ] Lint 100% of code
- [ ] Test 100% of code, or the stated project coverage policy
- [ ] **Planning checklist, mandatory for every plan:**
  1. Validate assumptions
  2. Cross-validate the proposed solution against product specs, every affected spec ID
  3. Cross-validate against the system architecture: boundaries, assumptions
  4. Plan automated test coverage for new logic, per the coverage policy
  5. Plan end-to-end tests for the proposed solution
- [ ] On a product behavior change, consult the product specs
- [ ] On an architecture change, consult the architecture doc
- [ ] On any conflict, bring it up for discussion before proceeding
- [ ] On a regression, run a root-cause analysis with the 5 whys and report the root cause
  before attempting a fix
- [ ] Keep specs and architecture updated, and confirm every change with the user

### docs/product-specs/README.md
- [ ] Spec format requirements: behavioral, testable, identified
- [ ] Distinction between feature specs and invariants
- [ ] Prefix table, one row per spec file
- [ ] Spec file index with one-line summaries
- [ ] Reference to the master spec, if one exists

### docs/product-specs/invariants.md
- [ ] Brief intro: what an invariant is, and why it need not be testable in isolation
- [ ] Each invariant: `### INV-NNN: Short title` and a body of 1 to 3 sentences

### docs/product-specs/<feature>.md
- [ ] Brief intro paragraph
- [ ] `Prefix: \`XXX\`.` line
- [ ] `---` separator
- [ ] Each spec: `### XXX-NNN: Short title` and a body of 1 to 3 sentences precise enough to
  derive a test from

### docs/README.md
- [ ] What lives in `docs/`, as a table
- [ ] Spec format requirements: testability, IDs, stability
- [ ] Process rules: treat docs as code, confirm with the user, surface conflicts, reference IDs
- [ ] When to update what, as a table
- [ ] When not to write a doc
- [ ] File naming convention

## Concise over comprehensive

The point of this layout is that an agent or a human finds the doc that answers their
question fast. Long docs defeat that purpose. Aim for:

- `AGENTS.md`: about 150 lines
- each feature spec: 5 to 15 specs of 1 to 3 sentences each
- architecture: 1 to 3 pages, mostly tables and diagrams

If a spec file grows past about 15 items, consider splitting it.

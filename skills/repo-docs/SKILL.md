---
name: repo-docs
description: Bootstrap or extend a repo's documentation for coding agents. Creates AGENTS.md + docs/ structure (architecture, guidelines, product-specs with stable IDs and invariants). Use when the user asks to "document the project for coding agents", "set up agent docs", "add AGENTS.md", "create docs/ structure".
---

# Repo docs for coding agents

This skill bootstraps a documentation layout for LLM-assisted development. Every project
area has a stable, addressable home. Every product behavior has a unique ID. Every change
has a clear consultation path.

## Required references

Paths are relative to this file. `<plugin root>` is the directory two levels above it.
Read each file at the step named.

| File | Read at | Holds |
|---|---|---|
| `../../assets/writing.md` | before writing any doc | the writing rules for every text a person reads |
| `references/spec-format.md` | before writing any spec or invariant | the format rules, ID stability, anti-patterns |
| `references/checklist.md` | step 3, before creating files | required content per file, size budgets |
| `templates/` | step 4 | skeletons that embed the format rules |

`<plugin root>/scripts/prose-lint.py` checks a doc against the writing rules. Run it on
every file you create or edit before you show the layout to the user.

## When to invoke

- "Document the project for coding agents" or "set up agent docs"
- "Add AGENTS.md" or "create docs/ structure"
- Extending the layout in a repo that already follows it. Individual specs are `/spec`'s job.

Do not invoke for one-off README edits. In a repo that already has a different doc
convention, confirm with the user first.

## Layout produced

```
<repo-root>/
├── AGENTS.md
└── docs/
    ├── README.md
    ├── architecture.md
    ├── guidelines.md
    └── product-specs/
        ├── README.md
        ├── invariants.md
        └── <feature>.md   (one per feature area)
```

## Document responsibilities

| File | Purpose | Do not put here |
|------|---------|-----------------|
| `AGENTS.md` | Project elevator pitch, tech stack, brief architecture, index of every doc with load hints | Long architectural rationale, full specs |
| `docs/README.md` | How to manage `docs/` itself: spec format rules, ID conventions, when to update what, file naming | Project content |
| `docs/architecture.md` | High-level architecture, layer boundaries, important technical assumptions, migration paths | Implementation tutorials |
| `docs/guidelines.md` | Process rules: lint and test policy, planning, regression analysis with the 5 whys, doc-update protocol | Product behavior |
| `docs/product-specs/README.md` | Spec format requirements (testability, ID rules) and the index of feature spec files | Feature behavior |
| `docs/product-specs/invariants.md` | Cross-cutting conditions that hold across the system. Prefix `INV`. Need not be testable in isolation. | Feature behavior, feature-local invariants |
| `docs/product-specs/<feature>.md` | Testable behaviors for one feature area. Each has a unique `PREFIX-NNN` ID. Feature-local invariants live here as prose contracts. | Implementation details |

## Spec format

Each feature spec is behavioral, self-evidently testable, and identified by a
`### PREFIX-NNN: Short title` heading. Cross-cutting invariants get `INV-NNN` in
`invariants.md`. Feature-local invariants stay in the feature file as prose contracts. Read
`references/spec-format.md` for the full rules before writing any spec.

## Workflow when invoked

### 1. Survey the repo first

Before writing anything:

- Read the existing `README.md`, the package manifest, the source layout, and any
  `SPEC.md` or design docs.
- Identify the product domain, the tech stack, and the architectural layers.
- Identify the discrete feature areas that warrant their own spec file.

If the repo already has agent docs in this pattern, skip bootstrapping. Add or edit only
the requested files.

### 2. Confirm scope with the user

Before creating files, propose:

- the feature spec files you will create, such as `companies.md`, `deals.md`, `tasks.md`
- their prefixes, such as `CMP`, `DEAL`, `TASK`
- any unusual choice, such as combining features or splitting a large one

Ask before creating. The user's preferred granularity matters more than your guess.

### 3. Create files in this order

Read `references/checklist.md` and `../../assets/writing.md` now.

1. `docs/product-specs/invariants.md`, the floor that everything else references
2. `docs/product-specs/<feature>.md`, one per feature area
3. `docs/product-specs/README.md`, the index and the format rules
4. `docs/architecture.md`, the layers, decisions, and assumptions
5. `docs/guidelines.md`, the process rules
6. `docs/README.md`, the meta-doc on managing `docs/`
7. `AGENTS.md`, the top-level overview and the index of everything

### 4. Fill the templates

`templates/` holds a skeleton for each file. Copy one, replace every `<placeholder>` with
project facts, and delete the tip comments. A placeholder or a tip that survives is a
defect. State only facts you found in the repo. When a fact is missing, write a TODO with
the reason.

### 5. Cross-link

- `AGENTS.md` indexes every other doc with a one-line summary and a "load when" hint.
- `docs/product-specs/README.md` indexes every spec file with its prefix and a summary.
- Specs reference invariants by ID where relevant, as in "see INV-003".

### 6. Lint and show

Run `prose-lint.py` on `AGENTS.md` and every file under `docs/`. Fix every finding in the
text. Then show the user the final layout and ask them to confirm.

## Definition of done

The skill is complete when all of these are true. Each item is answerable with evidence,
such as a file path, a grep result, or a user confirmation.

- [ ] Scope confirmed with the user before file creation: spec files, prefixes, unusual
  splits or combines.
- [ ] Every file in `references/checklist.md` exists and ticks every box in its own
  checklist. Missing items get a TODO with a reason, never a silent omission.
- [ ] No placeholder and no tip comment survives in any created file.
- [ ] No spec describes implementation. If a spec body names a function, class, schema,
  or file, rewrite it behaviorally.
- [ ] No spec carries a separate `**Testable:**` line. Rewrite the body instead.
- [ ] Every spec ID is unique within its file. Deletions leave holes. No renumbering.
- [ ] Every cross-cutting invariant has an `INV-NNN` ID in `invariants.md`. Feature-local
  invariants stay in their feature file as prose contracts.
- [ ] Cross-links resolve: `AGENTS.md` indexes every file under `docs/`, the specs README
  indexes every feature spec, and every "see XXX-NNN" points at an existing ID.
- [ ] Sizes within budget: `AGENTS.md` about 150 lines, each feature spec 5 to 15 items of
  1 to 3 sentences, architecture 1 to 3 pages.
- [ ] Every created or edited file passes `prose-lint.py` with no findings.
- [ ] In a repo that already had this layout, only the requested files were touched.
- [ ] The user has seen the final layout and confirmed it before the skill closes.

If a checkbox cannot be ticked honestly, the skill is not done. Return to the step that
produces it.

---
name: repo-docs
description: Bootstrap or extend a repo's documentation for coding agents. Creates AGENTS.md + docs/ structure (architecture, guidelines, product-specs with stable IDs and invariants). Use when the user asks to "document the project for coding agents", "set up agent docs", "add AGENTS.md", "create docs/ structure", or asks to add a new feature spec / invariant in a repo that already follows this pattern.
---

# Repo docs for coding agents

This skill bootstraps a documentation layout designed for LLM-assisted development: every project area has a stable, addressable home, every product behavior has a unique ID, and every change has a clear consultation path.

## When to invoke

- "Document the project for coding agents" / "set up agent docs"
- "Add AGENTS.md" / "create docs/ structure"
- "Add a feature spec" / "add an invariant" — when the repo already follows this pattern
- Any time a repo lacks structured agent documentation and would benefit from one

Do **not** invoke for one-off README edits or for repos that already have a different doc convention without confirming with the user.

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
| `AGENTS.md` | Project elevator pitch + tech stack + brief architecture + index of every doc with load hints | Long architectural rationale, full specs |
| `docs/README.md` | How to manage `docs/` itself: spec format rules, ID conventions, when to update what, file naming | Project content |
| `docs/architecture.md` | High-level architecture, layer boundaries, important technical assumptions, migration paths | Implementation tutorials |
| `docs/guidelines.md` | Process rules: lint/test policy, planning, regression CRA (5-whys), doc-update protocol | Product behavior |
| `docs/product-specs/README.md` | Spec format requirements (testability, ID rules) + index of feature spec files | Feature behavior |
| `docs/product-specs/invariants.md` | Conditions that hold across the system. Prefix `INV`. Don't have to be testable in isolation. | Feature-level behavior |
| `docs/product-specs/<feature>.md` | Testable behaviors for one feature area. Each has a unique `PREFIX-NUM` ID. | Implementation details |

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

## Workflow when invoked

### 1. Survey the repo first

Before writing anything:
- Read existing `README.md`, `package.json`, source layout, any existing `SPEC.md` or design docs
- Identify the **product domain** (what does this thing do?), **tech stack** (languages, frameworks, package manager, runtime), and **architectural layers** (frontend/backend split, storage, integrations)
- Identify discrete **feature areas** that warrant their own spec file

If the repo already has agent docs in this pattern, skip bootstrapping and only add/edit the requested files.

### 2. Confirm scope with the user

Before creating files, propose:
- The list of feature spec files you'll create (e.g., `companies.md`, `deals.md`, `tasks.md`)
- Their prefixes (e.g., `CMP`, `DEAL`, `TASK`)
- Any unusual choices (combining features, splitting a large feature)

Ask before creating. The user's preferred granularity matters more than your guess.

### 3. Create files in this order

1. `docs/product-specs/invariants.md` — the floor; everything else references it
2. `docs/product-specs/<feature>.md` files — one per feature area
3. `docs/product-specs/README.md` — index + format rules
4. `docs/architecture.md` — layers, decisions, assumptions
5. `docs/guidelines.md` — process rules
6. `docs/README.md` — meta-doc on managing `docs/`
7. `AGENTS.md` — top-level overview + index of everything

### 4. Use the templates

See `templates/` in this skill directory for ready-to-fill skeletons. They embed all the format requirements.

### 5. Cross-link

- `AGENTS.md` indexes every other doc with a one-line summary and a "load when…" hint
- `docs/product-specs/README.md` indexes every spec file with prefix + summary
- Specs reference invariants by ID where relevant (e.g., "see INV-3")

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

## Anti-patterns to avoid

- **Don't** write specs that describe implementation. "The `validateLifecycle` function returns false for invalid stages" is not a spec; "Lifecycle stage is one of …" is.
- **Don't** add a `**Testable:**` line. If the body isn't already testable, rewrite the body.
- **Don't** renumber spec IDs. Ever. Even if a deletion leaves `CMP-1, CMP-2, CMP-4`.
- **Don't** silently update specs to match implementation. Specs lead; if implementation diverged, surface the conflict.
- **Don't** create feature spec files for things that don't have observable product behavior (e.g., "build system" — that goes in architecture).
- **Don't** put narrative or rationale in spec files. Each spec is a tight assertion. Rationale lives in architecture or PR descriptions.
- **Don't** create files without confirming with the user when bootstrapping a new repo.

## Definition of done

The skill is complete when **all** of these are true. Each item is answerable with evidence — a file path, a grep result, a user confirmation — not a vibe.

- [ ] Scope confirmed with the user *before* file creation: list of feature spec files, their prefixes, any unusual splits/combines.
- [ ] Every file in the "Required content checklist" exists and ticks every box in its own checklist. Missing items get a TODO with a reason, not silent omission.
- [ ] No spec describes implementation. Re-read each spec body: if it names a function, class, schema, or file, rewrite it behaviorally.
- [ ] No spec carries a separate `**Testable:**` line. If the body isn't self-evidently testable, the body is rewritten — not annotated.
- [ ] Every spec ID is unique within its file. Deletions leave holes; no renumbering.
- [ ] Every invariant has an `INV-N` ID. Invariants live in `invariants.md`, not scattered into feature specs.
- [ ] Cross-links resolve: `AGENTS.md` indexes every file under `docs/`; `docs/product-specs/README.md` indexes every feature spec; every `see INV-N` / `see XXX-N` reference points to something that exists.
- [ ] Sizes within budget: `AGENTS.md` ~150 lines, each feature spec 5–15 items at 1–3 sentences, architecture 1–3 pages. Over-budget files are split or trimmed.
- [ ] If the repo already had docs in this pattern, only the requested files were touched — no silent rewrites of existing structure.
- [ ] User has been shown the final layout and asked to confirm before the skill closes.

If a checkbox cannot be ticked honestly, the skill is not done — return to the step that produces it.

## Concise > comprehensive

The whole point of this layout is that an agent (or human) can quickly find the doc that answers their question. Long docs defeat that purpose. Aim for:
- AGENTS.md: ~150 lines
- Each feature spec: 5–15 specs, each 1–3 sentences
- Architecture: 1–3 pages, mostly tables and diagrams

If a spec file is growing past ~15 items, consider splitting it.

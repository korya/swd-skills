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

## Spec format

**Read `references/spec-format.md`** before writing any spec or invariant.

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

## Required content

Per `references/checklist.md`, read at step 3.

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

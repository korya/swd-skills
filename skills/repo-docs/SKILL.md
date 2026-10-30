---
name: repo-docs
description: Bootstrap or extend a repo's documentation for coding agents. Creates AGENTS.md + docs/ structure (architecture, guidelines, product-specs with stable IDs and invariants). Use when the user asks to "document the project for coding agents", "set up agent docs", "add AGENTS.md", "create docs/ structure".
---

# Repo docs for coding agents

This skill bootstraps a documentation layout for LLM-assisted development. Every project
area has one stable home. Every product behavior has a unique ID. Every change has a clear
consultation path.

Do not invoke it for a one-off README edit. Individual specs are `/spec`'s job. In a repo
that already has a different doc convention, confirm with the user first.

## Required references

Paths are relative to this file. `<plugin root>` is the directory two levels above it.

| File | Read at | Holds |
|---|---|---|
| `../../assets/writing.md` | before writing any doc | the writing rules for every text a person reads |
| `templates/` | step 3, before creating files | one skeleton per file. Its sections are the required content. |

`templates/product-specs-README.md` is the home of the spec format: behavioral, testable,
identified, and how invariants differ. Follow it for every spec and invariant you write.

`<plugin root>/scripts/prose-lint.py` checks a doc against the writing rules.

## What goes where

Each fact has one home. The other files link to it instead of restating it.

| File | Holds | Not here |
|---|---|---|
| `AGENTS.md` | the pitch, tech stack, 30-second architecture, layout, the doc index with load hints, one line per process rule | rationale, full specs |
| `docs/README.md` | how to manage `docs/`: when to update what, naming, when not to write a doc | project content, the spec format |
| `docs/architecture.md` | layers and why each exists, assumptions, tech choices, deliberate omissions | tutorials, the directory tree |
| `docs/guidelines.md` | process: lint and test policy, the planning checklist, regressions with the 5 whys | product behavior |
| `docs/product-specs/README.md` | the spec format and one index of spec files with their prefixes | feature behavior |
| `docs/product-specs/invariants.md` | cross-cutting conditions, prefix `INV` | feature-local rules |
| `docs/product-specs/<feature>.md` | testable behaviors of one feature area, prefix `PREFIX-NNN` | implementation details |

## Workflow

1. **Survey.** Read the README, the package manifest, the source layout, and any design
   docs. Find the domain, the tech stack, the layers, and the feature areas that each
   warrant a spec file. If the repo already follows this layout, edit only the requested
   files.
2. **Confirm scope.** Propose the feature spec files, their prefixes, and any unusual
   split or merge. Wait for the user's answer. Their preferred granularity beats your guess.
3. **Write the files.** Read `../../assets/writing.md` and the templates now. Write
   `invariants.md` first, then the feature specs, the specs README, architecture,
   guidelines, `docs/README.md`, and `AGENTS.md` last. Each file links to the ones before
   it.
   - Replace every `<placeholder>` with a fact you found in the repo, and delete every tip
     comment. A placeholder or a tip that survives is a defect.
   - Delete a section that does not apply. Never pad it, and never invent a component,
     a plan, or an invariant the code does not show. A missing fact gets a TODO with the
     reason.
   - Derive specs from what a user sees in the output, not from the code that produces
     it. An internal name in a spec, such as a field or a function, is a defect.
   - The first sentence of a spec's intro starts with the user and what they do or get.
     A definition that starts with the term, such as "A ticket is" or "The command is
     how", comes second.
   - When extending a repo with specs, specs lead. If the code disagrees with a spec,
     surface the conflict. Never edit the spec to match.
4. **Cross-link.** Every ID cited as "see XXX-NNN" exists. `AGENTS.md` indexes every file
   under `docs/`. The specs README indexes every spec file with its prefix.
5. **Lint and show.** Run `prose-lint.py` on `AGENTS.md` and every file under `docs/`, and
   fix every finding. Then show the user the final layout and ask them to confirm.

## Definition of done

Each item is answerable with evidence: a file path, a grep result, or a user confirmation.

- [ ] The user confirmed the spec files and prefixes before any file was created.
- [ ] Every file in the table above exists, with no placeholder, tip comment, or padded
  section.
- [ ] Every fact has one home. Other files link to it.
- [ ] Every spec is behavioral, has a unique `PREFIX-NNN` ID, and carries no `**Testable:**`
  line. Every cross-cutting invariant has an `INV-NNN` ID.
- [ ] Every cited ID exists, and both indexes are complete.
- [ ] Sizes: `AGENTS.md` at most about 150 lines, each feature spec 5 to 15 items of 1 to
  3 sentences, architecture 1 to 3 pages.
- [ ] `prose-lint.py` reports no findings on any created or edited file.
- [ ] In a repo that already had this layout, only the requested files changed.
- [ ] The user has seen the final layout and confirmed it.

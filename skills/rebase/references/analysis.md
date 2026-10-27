# Semantic analysis: delta inventory, cross-impact, gaps, derisking

Loaded from `SKILL.md` step 3. Covers steps 3, 4, 6 and 7. They establish what changed on
the new base, how each of `curr`'s commits is affected, and which assumptions to re-verify
before replaying anything.

## 3. Inventory the delta: `new_base` minus `old_base`

```bash
git log --oneline <old_base>..<new_base>
git diff --stat <old_base>..<new_base>
```

Pay particular attention to:

- **Product specs**, such as `docs/product-spec/` and `docs/invariants.md`. Requirements
  may have changed.
- **Architecture docs**: `docs/architecture.md`, `AGENTS.md`, component-level `AGENTS.md`.
  Boundaries may have moved.
- **Code conventions, lint rules, `.editorconfig`, formatter configs.** Style may have
  shifted.
- **Schema and migration files.** The data shape may have changed.
- **Public APIs and shared utilities.** Signatures `curr` depends on may have changed.
- **Files `curr` touches.** The direct conflict surface.

For a non-trivial delta, delegate the survey to a read-only search subagent if your host
provides one. Do not read every commit by hand.

## 4. Cross-impact analysis

For each piece of `curr`'s change, classify it against the delta:

| Classification | Meaning | Action |
|---|---|---|
| **Untouched** | The delta did not modify the surface `curr` relies on | Replay as is |
| **Adjusted** | The delta modified a dependency. `curr` still applies but needs edits | Plan the edits |
| **Extended** | The delta added new surface `curr` should also cover: a new caller, channel, or spec | Plan the extension |
| **Obsolete** | The delta removed the code `curr` modifies, or already solves the problem | Drop the commit. Confirm with the user |
| **Conflicting** | The delta introduces requirements that contradict `curr`'s solution | Stop. Escalate |

Also check whether the original problem has been solved, in part or in full, on `new_base`
already. If so, much of `curr` may be redundant.

## 6. Identify gaps

List, with file paths:

- New code in the delta that the rebased solution must be **extended to**, such as a new
  channel or handler that needs the same fix.
- Old code removed in the delta whose modifications in `curr` are **no longer needed**.
- Existing code modified in the delta whose modifications in `curr` need **adjustment**.
- Existing code unmodified in the delta that `curr` can keep **as is**.

## 7. Derisk: validate assumptions

Before committing to the plan, cross-check the riskiest assumptions:

- Re-read the relevant product spec on `new_base`, not on `old_base`. They may differ.
- Re-read the relevant architecture sections on `new_base`.
- Re-read the invariants files on `new_base`.
- For every "I assume X is still true", verify by reading current code.

A non-trivial rebase gets three explicit validation passes. An assumption pass, a spec and
architecture pass, and an edge-case pass.

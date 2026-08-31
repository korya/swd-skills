# Semantic analysis: delta inventory, cross-impact, gaps, derisking

Loaded from `SKILL.md` step 3. Covers steps 3, 4, 6 and 7 — what changed on the new base,
how each of `curr`'s commits is affected, and which assumptions to re-verify before
replaying anything.

## 3. Inventory the delta: `delta = new_base - old_base`

```bash
git log --oneline <old_base>..<new_base>
git diff --stat <old_base>..<new_base>
```

Pay particular attention to:

- **Product specs** (e.g. `docs/product-spec/`, `docs/invariants.md`) — requirements may have changed
- **Architecture docs** (`docs/architecture.md`, `AGENTS.md`, component-level `AGENTS.md`) — boundaries may have moved
- **Code conventions / lint rules / `.editorconfig` / formatter configs** — style may have shifted
- **Schema / migration files** — data shape may have changed
- **Public APIs and shared utilities** — signatures `curr` depends on may have changed
- **Files `curr` touches** — direct conflict surface

For non-trivial deltas, delegate the survey to a read-only search subagent (if your host provides one) rather than reading every commit by hand.

## 4. Cross-impact analysis

For each piece of `curr`'s change, classify against `delta`:

| Classification | Meaning | Action |
|---|---|---|
| **Untouched** | `delta` did not modify the surface `curr` relies on | Replay as-is |
| **Adjusted** | `delta` modified a dependency; `curr` still applies but needs edits | Plan the edits |
| **Extended** | `delta` added new surface `curr` should also cover (new caller, new channel, new spec) | Plan the extension |
| **Obsolete** | `delta` removed the code `curr` modifies, or already solves the problem | Drop the commit; confirm with user |
| **Conflicting** | `delta` introduces requirements that contradict `curr`'s solution | Stop; escalate |

Also check: has the **original problem** been (partially) solved on `new_base` already? If yes, much of `curr` may be redundant.

## 6. Identify gaps

Enumerate, with file paths:

- New code in `delta` the rebased solution must be **extended to** (e.g. a new channel/handler that needs the same fix)
- Old code removed in `delta` whose modifications in `curr` are **no longer needed**
- Existing code modified in `delta` whose modifications in `curr` need **adjustment**
- Existing code unmodified in `delta` that `curr` can keep **as-is**

## 7. Derisk: validate assumptions

Before committing to the plan, cross-check the riskiest assumptions:

- Re-read the relevant product spec on `new_base` (not on `old_base` — they may differ)
- Re-read the relevant architecture sections on `new_base`
- Re-read invariants files on `new_base`
- For any "I assume X is still true" — verify by reading current code

For non-trivial rebases, run three explicit validation passes: assumption pass, spec+architecture pass, edge-case pass.

---
name: rebase
description: Rebase a work-in-progress or completed branch onto a new base, ensuring the rebased changes still satisfy their original spec, comply with the (possibly updated) architecture, conventions, and invariants of the new base, and introduce no regressions. Use when the user says "rebase this branch on X", "rebase my work on master", "move these commits onto the new base", or otherwise asks to migrate a set of commits onto a different base than they were authored against.
---

# Rebase a branch onto a new base

The point of this skill is **not** `git rebase`. Git can replay commits; it cannot tell you whether the replayed solution still makes sense. This skill is about the *thinking* around a rebase: re-validating the rebased work against a moved-on codebase, then doing the mechanical rebase carefully.

## When to invoke

- "Rebase `<branch>` on `<new-base>`" / "rebase my WIP onto master"
- "I started this work two weeks ago, can you rebase it on the latest master"
- After a long-lived feature branch — before merging — to verify it still aligns with current architecture, specs, and conventions
- Any time commits authored against an older base must land on a newer one and the user cares about correctness, not just merge-conflict resolution

Do **not** invoke for trivial fast-forward rebases with no semantic delta (e.g. base advanced by one unrelated commit) — just `git rebase` directly.

## Inputs to establish up front

- `curr` — the branch / commit being rebased (default: current branch `HEAD`)
- `old_base` — the base `curr` was originally branched from (default: merge-base of `curr` and `new_base`)
- `new_base` — the target base (default: `master` / `main`, confirm with user)

If any of these are ambiguous, **ask** before proceeding. Wrong base picks silently invalidate the entire analysis.

## Workflow

### 0. Preflight: account for uncommitted changes

Before touching history, check the working tree:

```bash
git status --porcelain
```

If the working tree is clean, skip to step 1.

Otherwise the working tree is a **fourth point** alongside `curr` / `old_base` / `new_base` — work the user hasn't yet decided whether to keep. The skill must account for it explicitly because (a) `git rebase` refuses to run with a dirty tree, (b) silently dropping it costs the user real work, and (c) the changes themselves may be relevant context for the rebase (a half-applied fix, debug instrumentation, a WIP commit-in-waiting).

Do this:

1. **Surface the diff to the user** — show `git status --porcelain` and a one-line summary of what's modified. Ask whether the changes are related to the rebase. The answer doesn't change the *mechanics* (always stash, always restore) but it changes how you reason about conflicts later: related changes that conflict on restore are a finding; unrelated debug prints that conflict are noise.
2. **Stash with a labeled, unique name** so the entry is easy to spot in `git stash list` and survives accidental `git stash drop`s elsewhere. Include untracked files — debug scripts and new test files are common:

   ```bash
   STASH_LABEL="swd-rebase-preflight-$(date +%Y%m%d-%H%M%S)"
   git stash push --include-untracked --message "$STASH_LABEL"
   ```

3. **Remember the label** for step 10.5. If the agent context might compact mid-rebase, write it somewhere durable (a scratch note in the conversation, a plan entry).

After this step, the working tree is clean and the rest of the workflow runs unchanged.

### 1. Establish the three points

```bash
git rev-parse HEAD                              # curr
git merge-base <curr> <new_base>                # old_base (likely)
git rev-parse <new_base>                        # new_base
```

State all three back to the user before continuing. If `old_base == new_base`, nothing to do — say so and stop.

### 2. Inventory `curr`'s changes

```bash
git log --oneline <old_base>..<curr>
git diff --stat <old_base>..<curr>
```

For each commit on `curr`, capture: subject, intent, files touched, and any spec/invariant it's claimed against. This is the "what we're trying to preserve" baseline.

### 3. Inventory the delta: `delta = new_base - old_base`

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

For non-trivial deltas, delegate the survey to an Explore agent rather than reading every commit by hand.

### 4. Cross-impact analysis

For each piece of `curr`'s change, classify against `delta`:

| Classification | Meaning | Action |
|---|---|---|
| **Untouched** | `delta` did not modify the surface `curr` relies on | Replay as-is |
| **Adjusted** | `delta` modified a dependency; `curr` still applies but needs edits | Plan the edits |
| **Extended** | `delta` added new surface `curr` should also cover (new caller, new channel, new spec) | Plan the extension |
| **Obsolete** | `delta` removed the code `curr` modifies, or already solves the problem | Drop the commit; confirm with user |
| **Conflicting** | `delta` introduces requirements that contradict `curr`'s solution | Stop; escalate |

Also check: has the **original problem** been (partially) solved on `new_base` already? If yes, much of `curr` may be redundant.

### 5. Risk gate

If any of the following is true, **stop and discuss with the user before touching code**:

- A commit on `curr` is classified **Conflicting**
- Architecture in `delta` invalidates the approach `curr` took
- The original problem is already solved differently on `new_base`
- The rebased solution would violate an invariant added in `delta` (e.g. data privacy, isolation, channel rules)

Surface these as a short summary with the inverted-pyramid principle: headline first ("rebase is risky because…"), then the specific conflicts, then options.

### 6. Identify gaps

Enumerate, with file paths:

- New code in `delta` the rebased solution must be **extended to** (e.g. a new channel/handler that needs the same fix)
- Old code removed in `delta` whose modifications in `curr` are **no longer needed**
- Existing code modified in `delta` whose modifications in `curr` need **adjustment**
- Existing code unmodified in `delta` that `curr` can keep **as-is**

### 7. Derisk: validate assumptions

Before committing to the plan, cross-check the riskiest assumptions:

- Re-read the relevant product spec on `new_base` (not on `old_base` — they may differ)
- Re-read the relevant architecture sections on `new_base`
- Re-read invariants files on `new_base`
- For any "I assume X is still true" — verify by reading current code

For non-trivial rebases, run three explicit validation passes (mirroring `feedback_plan_validation_passes`): assumption pass, spec+architecture pass, edge-case pass.

### 8. Present the plan

Before executing, show:

- Per-commit plan: replay / replay-with-edits / drop / split / new-commit
- For each "replay-with-edits" or "new-commit": the specific files and the specific changes
- Open questions, if any — ask now, not mid-rebase

Wait for user approval unless in auto mode and the rebase is low-risk.

### 9. Execute commit-by-commit

Prefer an interactive-style approach where each logical commit is handled independently:

- Replay or recreate the commit (resolve conflicts thoughtfully — never `-X theirs`/`-X ours` blindly)
- Apply the planned adjustments **in the same commit** if they're part of preserving the original intent; **in a separate commit** if they're a new fix discovered during rebase (per the "split move and bug-fix commits" rule)
- After each commit: lint and run unit tests for the affected area
- For risky commits (touching shared code, schemas, agent context, auth, billing): also do an e2e check or ask the user for one

Never `--no-verify` to push past hook failures. Fix the underlying issue.

### 9.5. Restore stashed changes (if step 0 stashed any)

If step 0 stashed anything, restore it now — before final verification, so the verification reflects the state the user will actually have:

```bash
git stash list | grep "$STASH_LABEL"          # confirm it's there
git stash pop "stash@{<index of the labeled entry>}"
```

Outcomes:

- **Clean pop.** Working tree now has the rebased history plus the previously uncommitted changes. Continue to step 10.
- **Pop with conflicts.** Git leaves the stash entry intact and writes conflict markers into the working tree. **Do not drop the stash.** Surface the conflict to the user with: (a) the files involved, (b) whether the stashed changes are related to the rebase (from step 0's question), (c) options — resolve manually, drop the stash if the user confirms the changes are now obsolete, or abandon and let the user recover from `git stash list`.

Never silently `git checkout -- .` or `git reset --hard` to clear a conflicted pop — the user's uncommitted work is the most fragile state in this entire workflow.

### 10. Final verification

After all commits land:

- Full lint pass on affected components (`just lint` or component-specific)
- Full unit test pass (`just test` or component-specific)
- E2E sanity for the user-visible behavior the original branch was supposed to deliver
- Re-read the original spec/PR description (if any): does the rebased branch still satisfy every acceptance criterion?
- Check for regressions in the surfaces `delta` touched but `curr` did not — those are the easiest to break and the easiest to miss

### 11. Report

Summarize for the user, inverted-pyramid:

- Headline: rebase succeeded / succeeded with adjustments / blocked
- Per-commit outcome (replayed / edited / dropped / new)
- Any spec or invariant deviations resolved, with the resolution
- Anything the user should still verify manually

## Anti-rationalization table

When tempted to skip a step, check whether your reasoning appears below. If it does, the answer is: do the step.

| Rationalization | Why it fails here |
|---|---|
| "Conflicts resolved cleanly — ship it." | Conflict markers are the visible 10%; semantic drift is the invisible 90%. A clean text merge can still violate an invariant `delta` added. |
| "The tests passed after the rebase, so it's fine." | The tests cover what was true on `old_base`. If `delta` added new surface (new caller, new channel, new spec), the suite may not cover it yet. |
| "Git accepted the replay, so the commits must still be correct." | Git replays text. It does not check that the *solution* still matches the *problem*. Re-read the spec on `new_base`. |
| "`delta` didn't touch the files `curr` changes — no cross-impact." | File-level untouched ≠ semantically untouched. A renamed helper, a new invariant, a tightened type — all can invalidate `curr` without touching its files. |
| "The original spec still applies." | Re-read it on `new_base`. Specs evolve in `delta` more often than agents assume; "still applies" should be a finding, not an assumption. |
| "`-X theirs` / `-X ours` will clear this conflict fast." | These options hide semantic divergence in a hunk-shaped blindspot. Resolve by reading both sides. |
| "This commit looks redundant — I'll drop it silently." | Dropping a commit is a user-visible scope decision. Surface it, get the nod, then drop. |
| "I'll bundle the rebase-fix into the original commit." | If the fix is preserving the original intent, bundle. If it's a *new* bug fix you discovered during rebase, split — per the project's split-move-and-fix rule. |
| "Lint/tests aren't needed; rebase didn't touch logic." | Rebase always touches logic — replaying a change against new code *is* a logic change. Run them. |
| "Three iterations of conflict resolution is enough — push it." | If you've fought the same hunk three times, the approach itself is probably wrong on `new_base`. Stop and reframe with the user. |
| "The working tree was dirty; I'll just `git stash` and `git stash pop` without telling the user." | The stashed work is the most fragile state in this workflow — if `pop` conflicts and the agent silently drops it, real work disappears. Label the stash, surface it, restore explicitly, handle pop conflicts visibly. |
| "Pop conflicted; `git checkout -- .` to clean it up and move on." | That deletes the user's uncommitted changes. The stash entry survives the pop conflict — leave it alone and surface to the user. |

## Anti-patterns

- **Treating rebase as a merge-conflict exercise.** Conflict markers are the visible 10%; semantic drift is the invisible 90%.
- **Replaying without re-reading the spec.** The spec on `old_base` is not the spec you're shipping against.
- **Bundling rebase fixes into the original commit when they're really new bug fixes.** Split them.
- **Skipping lint/tests "because rebase didn't touch logic."** Rebase always touches logic — that's the whole point of this skill.
- **Forcing through a Conflicting classification without surfacing it.** Stop and talk to the user.

## Definition of done

The rebase is complete when **all** of these are true. Each item is answerable with evidence, not a vibe.

- [ ] Working tree was clean before any history-mutating step. If it wasn't, preflight stashed it with a labeled name and step 9.5 restored it — or the user was explicitly asked how to handle a conflicted pop.
- [ ] Three points (`curr`, `old_base`, `new_base`) stated back to the user; `old_base != new_base` confirmed.
- [ ] Every commit on `curr` carries a classification (Untouched / Adjusted / Extended / Obsolete / Conflicting) with a one-line justification.
- [ ] Any **Conflicting** or **Obsolete** classification has been surfaced to the user and resolved — not silently dropped or force-resolved.
- [ ] Specs, invariants, and architecture docs were re-read on `new_base` (not from memory of `old_base`).
- [ ] Each "replay-with-edits" or "new-commit" landed as a discrete, lint-clean, test-clean commit; no `--no-verify`.
- [ ] No `-X theirs` / `-X ours` was used to clear a conflict the agent didn't read both sides of.
- [ ] Full lint + unit test pass on affected components. Risky commits also got an e2e check (or an explicit user-deferred note).
- [ ] Original acceptance criteria (PR description, spec, ticket) restated and confirmed still met on the rebased branch.
- [ ] Regression surface in `delta`-touched code that `curr` did *not* touch was sanity-checked; "nothing broken there" is a finding, not an assumption.
- [ ] Final report delivered inverted-pyramid: headline, per-commit outcome, deviations, manual-verify list.

If a checkbox cannot be ticked honestly, the rebase is not done — return to the step that produces it.

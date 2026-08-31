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

If `git status --porcelain` is not empty, **read `references/stash.md` now** and follow its step 0.

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

**Read `references/analysis.md` now**; it covers steps 3, 4, 6 and 7.

### 4. Cross-impact analysis

Per `references/analysis.md` § 4.

### 5. Risk gate

If any of the following is true, **stop and discuss with the user before touching code**:

- A commit on `curr` is classified **Conflicting**
- Architecture in `delta` invalidates the approach `curr` took
- The original problem is already solved differently on `new_base`
- The rebased solution would violate an invariant added in `delta` (e.g. data privacy, isolation, channel rules)

Surface these as a short summary with the inverted-pyramid principle: headline first ("rebase is risky because…"), then the specific conflicts, then options.

### 6. Identify gaps

Per `references/analysis.md` § 6.

### 7. Derisk: validate assumptions

Per `references/analysis.md` § 7.

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

Per `references/stash.md` § 9.5.

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

## Anti-rationalization

When tempted to skip a step, read `references/rationalizations.md`.

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

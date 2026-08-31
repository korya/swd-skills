---
name: rebase
description: Rebase a work-in-progress or completed branch onto a new base, ensuring the rebased changes still satisfy their original spec, comply with the (possibly updated) architecture, conventions, and invariants of the new base, and introduce no regressions. Use when the user says "rebase this branch on X", "rebase my work on master", "move these commits onto the new base", or otherwise asks to migrate a set of commits onto a different base than they were authored against.
---

# Rebase a branch onto a new base

The point is **not** `git rebase`. Git can replay commits; it cannot tell you whether the
replayed solution still makes sense. This skill is the *thinking* around a rebase:
re-validate the work against a codebase that moved on, then do the mechanics carefully.

Invoke for "rebase `<branch>` on `<new-base>`", "rebase my WIP onto master", or before
merging a long-lived branch to check it still fits current architecture, specs, and
conventions. Not for a trivial fast-forward with no semantic delta — just `git rebase`.

## Required references

This file is the skeleton; each reference holds a step's full rules. Read it **at that step**.

| File | Read at | Holds |
|---|---|---|
| `references/stash.md` | step 0, only if the tree is dirty | labeled stash, restore, conflicted-pop handling |
| `references/analysis.md` | step 3 | delta checklist, classification table, gaps, derisk passes |
| `references/rationalizations.md` | when tempted to skip a step | why each shortcut fails |

## Inputs

- `curr` — the branch or commit being rebased (default: `HEAD`)
- `old_base` — what `curr` was branched from (default: merge-base of `curr` and `new_base`)
- `new_base` — the target (default: `master` / `main`; confirm with the user)

If any is ambiguous, **ask**. A wrong base pick silently invalidates the whole analysis.

## Workflow

0. **Preflight.** `git status --porcelain`. Clean → step 1. Dirty → **read `references/stash.md`
   now**: the uncommitted work is a fourth point that must survive the rebase, so it is
   stashed under a label you record for step 9.5 — never silently.
1. **Three points.** `git rev-parse HEAD`, `git merge-base <curr> <new_base>`,
   `git rev-parse <new_base>`. State all three to the user. `old_base == new_base` → nothing
   to do; say so and stop.
2. **Inventory `curr`.** `git log --oneline <old_base>..<curr>` and `git diff --stat`. Per
   commit: subject, intent, files, and the spec or invariant it claims to satisfy. This is
   what must be preserved.
3. **Inventory `delta = new_base - old_base`.** **Read `references/analysis.md` now.** Specs,
   architecture docs, conventions and lint config, schemas and migrations, shared APIs, and
   the files `curr` touches. Delegate a large delta to a read-only search subagent.
4. **Cross-impact.** Classify each piece of `curr` against `delta` per the table:
   **Untouched / Adjusted / Extended / Obsolete / Conflicting**. Also ask whether
   `new_base` already solves the original problem.
5. **Risk gate.** Stop and talk to the user before touching code if anything is
   Conflicting, the architecture invalidates `curr`'s approach, the problem is already
   solved differently, or the replay would break an invariant `delta` added. Headline
   first, then the conflicts, then options.
6. **Gaps.** With file paths: new code the fix must extend to, removed code whose edits are
   no longer needed, modified code whose edits need adjustment, unchanged code kept as-is.
7. **Derisk.** Re-read spec, architecture, and invariants **on `new_base`**; verify every
   "I assume X is still true" against current code. Non-trivial rebases get three passes:
   assumptions, spec + architecture, edge cases.
8. **Present the plan.** Per commit: replay / replay-with-edits / drop / split / new-commit,
   with the specific files and changes for edits and new commits. Ask open questions now,
   not mid-rebase. Wait for approval unless in auto mode and the rebase is low-risk.
9. **Execute commit by commit.** Resolve conflicts by reading both sides — never `-X theirs`
   / `-X ours` blindly. Edits that preserve the original intent go in the same commit; a new
   fix discovered during the rebase goes in its own. Lint and unit-test the affected area
   after each commit; risky commits (shared code, schemas, auth, billing) also get an e2e
   check or an explicit ask. Never `--no-verify`.
9.5. **Restore the stash** if step 0 made one, before final verification, per
   `references/stash.md` § 9.5. A conflicted pop is surfaced, never cleared with `checkout --`
   or `reset --hard`.
10. **Final verification.** The project's full lint and unit-test commands on affected
    components; e2e sanity for the behavior the branch was meant to deliver; re-read the
    original spec or PR description against the result; sanity-check the surfaces `delta`
    touched and `curr` did not — the easiest to break and to miss.
11. **Report**, inverted pyramid: headline (succeeded / with adjustments / blocked),
    per-commit outcome, spec or invariant deviations and their resolution, what the user
    should still verify by hand.

## Definition of done

Each item is answerable with evidence, not a vibe; one you cannot tick honestly sends you
back to the step that produces it.

- [ ] Tree was clean before history moved — or preflight stashed it under a label, and step
  9.5 restored it or asked the user about a conflicted pop.
- [ ] Three points stated to the user; `old_base != new_base` confirmed.
- [ ] Every commit on `curr` classified, with a one-line justification; every Conflicting
  or Obsolete one surfaced and resolved, never silently dropped or forced.
- [ ] Specs, invariants, and architecture re-read on `new_base`, not from memory.
- [ ] Each edited or new commit landed discrete, lint-clean, and test-clean; no
  `--no-verify`; no `-X theirs` / `-X ours` on a conflict you did not read both sides of.
- [ ] Full lint and unit tests pass on affected components; risky commits got an e2e check
  or an explicit user-deferred note.
- [ ] Original acceptance criteria restated and still met; `delta`-touched surfaces `curr`
  did not touch were checked — "nothing broken there" is a finding, not an assumption.
- [ ] Report delivered inverted-pyramid with the manual-verify list.

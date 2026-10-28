---
name: rebase
description: Rebase a work-in-progress or completed branch onto a new base, ensuring the rebased changes still satisfy their original spec, comply with the (possibly updated) architecture, conventions, and invariants of the new base, and introduce no regressions. Use when the user says "rebase this branch on X", "rebase my work on master", "move these commits onto the new base", or otherwise asks to migrate a set of commits onto a different base than they were authored against.
---

# Rebase a branch onto a new base

Git can replay commits. It cannot tell you whether the replayed solution still makes sense
on a codebase that moved on. This skill re-validates the work against the new base, then
does the mechanics carefully.

Do not invoke it for a fast-forward with no semantic delta. That is just `git rebase`.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it.

| File | Read at | Holds |
|---|---|---|
| `references/stash.md` | step 0, only if the tree is dirty | the labeled stash, the restore, a conflicted pop |
| `../../assets/writing.md` | step 7, before writing the plan | the writing rules for every text a person reads |
| `references/rationalizations.md` | when tempted to skip a step | why each shortcut fails |

## Inputs

- `curr`: the branch or commit being rebased. Default: `HEAD`.
- `old_base`: what `curr` was branched from. Default: the merge-base of `curr` and
  `new_base`.
- `new_base`: the target. Default: `master` or `main`. Confirm with the user.

If any is ambiguous, ask. A wrong base silently invalidates the whole analysis.

## Workflow

0. **Preflight.** If `git status --porcelain` is not empty, read `references/stash.md`
   now. The uncommitted work must survive the rebase. Stash it under a label, never
   silently.
1. **Three points.** State the hashes of `curr`, `old_base`, and `new_base` to the user. If
   `old_base` equals `new_base`, there is nothing to do. Say so and stop.
2. **Inventory `curr`.** Per commit, record the subject, the intent, the files, and the
   spec or invariant it claims to satisfy. This is what must survive.
3. **Inventory the delta** from `old_base` to `new_base`. Read each of these on
   `new_base`, never from memory:
   - the specs and invariants. Requirements may have changed.
   - the architecture docs and every `AGENTS.md`. Boundaries may have moved.
   - the conventions: lint, formatter, and test config, and the guidelines.
   - the schemas and migrations.
   - the shared APIs and utilities `curr` calls.
   - the files `curr` touches.

   A change outside `curr`'s files can still break it: a renamed helper, a new invariant,
   a tighter type. Delegate a large delta to a read-only search subagent.
4. **Classify** each commit against the delta, with a one-line justification. Name the
   files for every class other than Untouched.

   | Class | Meaning | Action |
   |---|---|---|
   | **Untouched** | The delta did not change the surface `curr` relies on | Replay as is |
   | **Adjusted** | The delta changed a dependency. `curr` still applies with edits | Plan the edits |
   | **Extended** | The delta added surface `curr` should also cover: a caller, a channel, a spec, a test convention | Plan the extension |
   | **Obsolete** | The delta removed the code `curr` modifies, or already solves the problem | Drop only after the user agrees |
   | **Conflicting** | The delta adds a requirement that `curr`'s solution contradicts | Stop at step 5 |

   Also ask whether `new_base` already solves the original problem, in part or in full.
5. **Risk gate.** Stop and talk to the user before touching code in four cases. Something
   is Conflicting. The architecture invalidates `curr`'s approach. The problem is already
   solved differently. The replay would break an invariant the delta added. Headline
   first, then the conflicts, then the options.
6. **Derisk.** Verify every "I assume X is still true" against the code on `new_base`. A
   non-trivial rebase gets three passes: assumptions, spec and architecture, edge cases.
7. **Present the plan.** Read `../../assets/writing.md` now. Per commit: replay, replay
   with edits, drop, split, or new commit, with the files and changes for each edit. Ask
   the open questions now, not mid-rebase. Wait for approval unless in auto mode and the
   rebase is low-risk.
8. **Execute commit by commit.**
   - Resolve each conflict by reading both sides. Never `-X theirs` or `-X ours`.
   - An edit that preserves a commit's intent goes into that commit. A new fix found
     during the rebase gets its own commit.
   - Lint and unit-test the affected area after each commit. Never `--no-verify`.
   - A risky commit, in shared code, schemas, auth, or billing, also gets an e2e check or
     an explicit ask.
9. **Restore the stash** if step 0 made one, per `references/stash.md`. A conflicted pop
   goes to the user, never through `checkout --` or `reset --hard`.
10. **Verify.** Run the full lint and unit tests on the affected components, and an e2e
    sanity check of the behavior the branch delivers. Re-read the original spec or PR
    description against the result. Check the surfaces the delta touched and `curr` did
    not. They are the easiest to break and to miss.
11. **Report** as an inverted pyramid. The headline says succeeded, succeeded with
    adjustments, or blocked. Then the per-commit outcome, the spec or invariant deviations
    and their resolution, and what the user should still verify by hand. Run
    `<plugin root>/scripts/prose-lint.py` on the report and fix every finding.

## Definition of done

Each item is answerable with evidence. One you cannot tick honestly sends you back to the
step that produces it.

- [ ] The tree was clean before history moved, or its changes were stashed under a label
  and restored. A conflicted pop went to the user.
- [ ] Three points stated, and `old_base` differs from `new_base`.
- [ ] Every commit classified with a justification. No Obsolete or Conflicting commit was
  dropped or forced without the user.
- [ ] Specs, invariants, and architecture read on `new_base`.
- [ ] Each commit landed lint-clean and test-clean. No `--no-verify`, `-X theirs`, or
  `-X ours`.
- [ ] Full lint and unit tests pass. Risky commits got an e2e check or a user-deferred
  note.
- [ ] The original acceptance criteria are still met. The surfaces the delta touched and
  `curr` did not were checked, and "nothing broken there" is a finding.
- [ ] The report passes `prose-lint.py` with no findings.

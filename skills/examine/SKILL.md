---
name: examine
description: >-
  Review a code change rigorously — a PR, branch, commit range, or the working tree. Confirm the
  problem is real, sketch the obvious solutions before reading the diff, then audit it for
  correctness, completeness, architecture, conventions, security, privacy, testing, reversibility,
  and dependencies, judge whether it is right-sized, and verify every significant finding
  independently. Returns a six-signal report: done well, gaps, issues rated Critical to Low with a
  separate confidence verdict, questions, suggestions, known limitations. Use when the user says
  "/examine", "examine this PR", "review this PR", "review pr #N", "review my branch", "look over
  my pull request", "check my PR before merge", or asks for a deep code review. Holistic where the
  host's built-in review is defect-first.
---

# Examine: production-risk-first code review

Find what would break in production. Verify the change's claims instead of trusting them.
Judge whether the solution is right-sized. Skip this skill for typo and doc-only changes.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it.

| File | Read at | Holds |
|---|---|---|
| `references/audit.md` | step 5 | the audit axes and the Occam pass |
| `references/verify.md` | step 7 | the verdict rubric and the gap sweep |
| `../../assets/writing.md` | step 8 | the writing rules for the report |
| `references/report.md` | step 8 | severities, locators, the template, the definition of done |
| `references/rationalizations.md` | when tempted to skip a step | why each shortcut fails |

## Principles

- **Trust nothing.** The description, the diff, green tests, and your own candidates are
  claims. They become findings only after step 7.
- **Judge against the project's rules, not generic practice.** A finding cites its rule.
- **No side effects.** Read and run anything locally. Experiment in a detached worktree
  (`git worktree add --detach`) or outside the repo, never in the primary checkout. Never
  push, comment, trigger CI, or contact anyone unless the user asks during this review.

## Target and mode

- **PR:** `gh pr view <N>`, `gh pr diff <N>`, and `gh pr checks <N>`.
- **Branch or no argument:** diff from the merge-base with the upstream, else with the local
  base branch. Add `git diff HEAD` when the tree is dirty.
- **Range or path:** exactly that. Read pre-change code with `git show <merge-base>:<path>`.
- Record the branch, `HEAD`, and `git status --porcelain`. The end check compares them.

`/examine [quick|full] <target>`. Default to **full** for migrations, auth, payments,
personal data, dependencies, infra, or more than about 15 files. Otherwise use **quick**.
State the mode and why. Quick runs steps 1 to 5 with axes 5a to 5d and 5i only, then steps
7 and 9. It skips host reviewers and the Occam pass, lists skipped axes under Not reviewed,
and reports at most 8 Issues. Never pad toward the cap.

## Workflow

Delegate independent passes to read-only subagents when the host has them. You own severity
and synthesis.

1. **Intent.** Extract the problem, approach, constraints, and non-obvious decisions from
   the description, else from the commits. Read any linked ticket. A missing description is
   finding #1 (`scope: PR`). Mark inferred intent as inferred.
2. **Rulebook.** Read every agent instruction file that governs a changed file. Read in full
   the project docs the diff makes load-bearing: invariants, security, privacy, the touched
   spec, testing. Skim the rest.
3. **Baseline, before opening the diff.** Confirm the problem exists in the base snapshot.
   If it does not, or an existing utility already solves it, that is finding #1. Sketch two
   or three obvious approaches, one sentence each.
4. **Approach gate.** If the change matches a sketch, proceed. If it diverges, assume your
   sketch missed a constraint and look for it in the ticket, docs, history, and adjacent
   code. Found: note it under Verified. Not found: the approach question is the headline,
   and every line finding is provisional.
5. **Audit.** Read `references/audit.md` now and walk every axis that applies. Record each
   issue-shaped observation as a candidate with a one-line failure scenario. In full mode,
   also run the host's built-in review in a subagent on the reviewed checkout, as one more
   source of candidates. `--no-host-reviewers` skips it.
6. **Occam pass** (full mode, `audit.md` § 6). Ask whether the change is more solution than
   the problem needs.
7. **Verify and sweep.** Read `references/verify.md` now. Give every Medium or higher
   candidate an independent verdict from a subagent that sees only the diff, the files, and
   the candidate. Then make one fresh-eyes sweep for what the list missed.
8. **Synthesize.** Read `../../assets/writing.md` and `references/report.md` now. Assign
   severities and build the report.
9. **Report locally.** Write the report to a file and run
   `<plugin root>/scripts/prose-lint.py` on it. Fix every finding in the text. If the host
   has a structured findings tool, call it once with the Issues. The terminal report is the
   deliverable. Post to the PR only if the user asks.

## Done when

Every item in `report.md` § Definition of done holds, with evidence. If one does not, go
back to the step that produces it.

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
Judge whether the solution is right-sized. The host's built-in review asks "does this
introduce a bug?". `/examine` asks "is this the right, production-safe, right-sized change?".
Skip it for typo and doc-only changes.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it. Read each
file at the step named.

| File | Read at | Holds |
|---|---|---|
| `references/audit.md` | step 5 | axes 5a to 5m, the Occam pass |
| `references/verify.md` | step 7 | dedup, the CONFIRMED / PLAUSIBLE / REFUTED rubric, the gap sweep |
| `../../assets/writing.md` | step 8, before writing the report | the writing rules for every text a person reads |
| `references/report.md` | step 8 | signals, severities, locators, template, definition of done |
| `references/rationalizations.md` | when tempted to skip a step | why each shortcut fails |

## Principles

- **Trust nothing, verify everything.** The description, the diff, and green tests are
  claims. So are your own candidates. They become findings only after step 7.
- **Project rules over generic best practice.** Read the rulebook before judging. Cite it
  per finding.
- **The simplest solution that satisfies the constraints wins.** Sketch the obvious fix
  before reading the diff. Divergence is a question to investigate, never proof.
- **No side effects.** Read and run anything locally, but experiment in a detached worktree
  (`git worktree add --detach`) or outside the repo, never in the primary checkout. Never
  push, comment, trigger CI, or contact anyone. If evidence needs that, ask. Consent from an
  earlier task does not carry over.

## Target and mode

- **PR:** `gh pr view <N>` for title, body, base, head, and files. Then `gh pr diff <N>` and
  `gh pr checks <N>`.
- **Branch or no argument:** compare against the upstream when it is ahead, else the local
  base branch: `git diff $(git merge-base HEAD <ref>)`. Add `git diff HEAD` when the tree is
  dirty or the range is empty.
- **Range or path:** exactly that. Read pre-change code from the base snapshot with
  `git show <merge-base>:<path>`.
- Record the baseline: branch, `HEAD`, `git status --porcelain`. The end check proves the
  checkout is untouched. Posting to the PR defaults to no.

`/examine [quick|full] <target>`. When unspecified, use **full** for migrations, auth,
payments, personal data, dependencies, infra, or more than about 15 files. Otherwise use
**quick**, and state the choice. Quick runs steps 1, 2 (instruction files only), 3
(three-bullet sketches), 4, 5a to 5d plus 5k, 7, and 9. Skipped axes go under Not reviewed.
No Occam pass, no host reviewers, at most 8 Issues. Never pad toward a cap.

## Workflow

Delegate independent passes to read-only subagents when the host has them. You own severity
and synthesis.

1. **Intent.** From the description, else from the commits and the user's framing: the
   stated problem, the approach, the constraints and non-goals, the non-obvious decisions.
   Read any linked ticket. Drift from it is a finding. A missing description is finding #1
   (`scope: PR`). Mark inferred intent as derived, not stated.
2. **Rulebook.** Read every agent instruction file that governs a changed file: user-level,
   repo root, ancestor directories. Read in full the project docs the diff makes
   load-bearing: invariants, security, privacy, the touched spec, testing. Skim architecture
   and guidelines. A finding on any of those cites its rule (file and section) or downgrades
   to a Suggestion. With no project rule, name the standard (OWASP, GDPR). An absent doc the
   diff does not need is one line under Not reviewed.
3. **Baseline, before opening the diff.** Confirm the problem exists in the base snapshot.
   "Already solved by an existing utility" or "misdiagnosed symptom" reframes the review and
   is finding #1. Sketch two or three obvious approaches, a sentence each, scaled to the
   blast radius.
4. **Approach gate.** The change matches a sketch: proceed. Whatever it does beyond the
   sketch needs a constraint and feeds step 6. The change diverges: assume your sketch missed
   a constraint and hunt for it in the ticket, docs, history, and adjacent code. Found: note
   it under Verified. Not found: the approach-level question is the headline, and every line
   finding is provisional. Wrong on its face: point the author at `/blueprint`.
5. **Audit.** Read `references/audit.md` now. Track each axis in your task tool. 5a alignment
   with the claimed approach. 5b solves the stated problem. 5c correctness, five angles. 5d
   cross-file tracer. 5e to 5m architecture, conventions, security, privacy, testing,
   load-bearing assumptions, risk coverage, reversibility, dependencies. Every issue-shaped
   observation becomes a candidate with a one-line failure scenario, never dropped silently.
   In full mode the host's built-in review runs in a subagent, pointed at the reviewed
   checkout, as one more candidate source, never as the report. `--no-host-reviewers` skips
   it.
6. **Occam pass** (full mode, rules in `audit.md` § 6): premature optimization, speculative
   generality, over-defence, reinvention, band-aids, deletion candidates. Simplifications
   clear the same evidence bar and default to Suggestion.
7. **Verify and sweep.** Read `references/verify.md` now. Dedup. Then give every Medium+
   candidate an independent verdict: a subagent holding only the diff, the files, and the
   candidate, else an adversarial self-pass. Keep CONFIRMED and PLAUSIBLE. REFUTED moves to
   Verified with its citation. Then one fresh-eyes sweep for what the list missed, verified
   the same way. An empty sweep is a valid result.
8. **Synthesize.** Read `../../assets/writing.md` and `references/report.md` now. Issues
   carry a severity (impact) and a Verdict (confidence). Critical and High are scarce. An
   absence the author must address is an Issue. A nice-to-note one is a Gap. A doubt with no
   named mechanism is a Question.
9. **Report locally**, findings first, per the template. Write the report to a file, run
   `<plugin root>/scripts/prose-lint.py` on it, and fix every finding in the text. If the
   host has a structured findings tool, call it once with the Issues. The terminal report is
   the deliverable.
10. **Post to the PR only if asked.** Comments are public and durable.

## Done when

Every item in `report.md` § Definition of done is answerable with evidence. One you cannot
tick honestly sends you back to the step that produces it. A step you are tempted to skip
sends you to `references/rationalizations.md`.

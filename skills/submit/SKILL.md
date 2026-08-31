---
name: submit
description: Submit finished work for review — feature branch, well-formed Conventional Commits, pre-push checks, a draft PR whose description explains the what, why, and how, then CI gated green with root-cause fixes. Use when the user says "/submit", "submit this", "open a PR", "create a pull request", "push this up", "get this reviewed", or whenever completed changes need to leave the working tree and become a reviewable pull request.
---

# Submit: from working tree to reviewable PR

The point is **not** to run `git push`. It is to package finished work so a reviewer can
trust it: commits that read as history, checks that already pass, and a description that
explains what the diff cannot — opened as a draft, gated on CI. `/blueprint` plans the
change; `/submit` ships it for review.

GitHub-first, adapt: the commands below name `gh`. When `origin` is not GitHub, use the
forge's equivalent (`glab` for GitLab, etc.) — the phases and their gates are identical.

## Required references

This file is the skeleton; each reference holds a phase's full rules and examples. Read it
**at that phase**.

| File | Read at | Holds |
|---|---|---|
| `references/commits.md` | phase 2 | subject and body rules, staging discipline, trailers |
| `references/pr-description.md` | phase 5, before drafting or validating a description | what/why/how structure, ledes, visualization, justification-not-journal |
| `references/screenshots.md` | when the branch changes anything rendered | mandatory screenshots; hosting images from the CLI |
| `references/rationalizations.md` | when tempted to skip a phase | why each shortcut fails |

## Consent

Invoking `/submit` is consent for the full workflow: commit, push, create or edit a draft
PR, and push CI-fix commits. A narrower request ("just commit", "just push") is consent
for exactly that — confirm before stepping past it. Never without fresh, explicit consent:
pushing to the default branch, force-pushing, or marking a draft PR ready for review.

## Principles

- **Phases are gated.** A phase's exit condition is met before the next starts. A
  re-invocation re-enters at phase 0 and skips phases already satisfied — but never PR
  revalidation (5b) or CI (6) while a PR exists.
- **The description is the entry point.** Reviewers read it before the diff; it must
  complement the diff — the why, the shape, the trade-offs — never repeat it.
- **Keep the PR honest.** New commits change scope. Revalidate title and body on every
  pass, and when nothing is stale, say so explicitly — silence is not evidence.
- **Fix CI at the root.** Read the failing logs until you know why. No placebo "fix CI"
  commits, no disabled checks, no skipped tests.
- **Draft by default.** The user decides when reviewers get pinged, not the workflow.

## Workflow

0. **Orient.** `git status` (uncommitted? untracked?), current branch,
   `git log @{u}..HEAD` (unpushed?), and
   `gh pr view --json number,title,body,state,isDraft,baseRefName` (does a PR exist? was
   it merged while you worked?). State what you found in a sentence or two — the evidence
   this phase ran. A merged or closed PR means new work starts from a fresh branch off the
   updated default branch, never from the old one.
1. **Branch.** Never commit to the default branch. Follow the repo's own convention when
   one is documented or visible in recent branch names; otherwise
   `<author>-<slug>` (git user's first name, lowercased; slug from the change itself).
2. **Commit** — only if phase 0 found uncommitted changes. **Read
   `references/commits.md` now.** Stage by filename, never `git add -A`; no secrets,
   env files, or unrelated scratch files. Conventional Commits `type(scope): Subject` —
   imperative, capitalized, ≤72 chars, specific enough that no other commit could share
   it. Body when the why is not obvious from the subject; co-author trailer naming the
   model. Unrelated changes are separate commits.
3. **Pre-push checks.** Format, lint, and test **every area the branch touches**, using
   the repo's own commands — discover them from its agent docs, task runner, or package
   scripts — not just the area most recently edited. Fix failures at the root before
   pushing: "CI will tell me" wastes a cycle and pollutes history with fixups.
4. **Push.** First push `git push -u origin <branch>`; after that plain `git push`.
   Exit: local `HEAD` matches `origin/<branch>`.
5. **PR.** **Read `references/pr-description.md` now.**
   - **5a — no PR exists.** Draft the title (same rules as a commit subject) and the
     body: the repo's own PR template when one exists, else the what/why/how structure
     from the reference. A change to anything rendered → **read
     `references/screenshots.md`**; screenshots are mandatory or the gap declared.
     Create as a **draft** (`gh pr create --draft`), body via heredoc.
   - **5b — a PR exists.** Mandatory even when the user only said "push", and even with
     nothing new pushed. Fetch the live title and body plus `git log <base>..HEAD`; check
     the title still covers *all* the work and the body still tells the truth — scope,
     claims ("no new dependencies"), screenshots still current. Stale → `gh pr edit` and
     say what changed; not stale → state "title and body still match the branch".
6. **CI.** `gh pr checks` — wait out pending checks; never declare success with checks in
   flight. On failure: pull the failing logs, find the root cause in the diff, fix, and
   re-enter at phase 3 → 4 → 5b → 6. A failure that is clearly flaky or infra-side gets
   flagged to the user instead of burning retries. Close with the status: "all N required
   checks green" or what failed and which commit fixed it.

## Definition of done

- [ ] Phase 0 findings stated; no phase skipped silently.
- [ ] Work sits on a named feature branch; nothing pushed to the default branch.
- [ ] Every new commit: Conventional subject, imperative and unique, trailer present; no
  unrelated or sensitive files staged.
- [ ] Format, lint, and tests pass locally for every touched area before every push.
- [ ] Draft PR exists; description follows the repo template or the what/why/how
  structure, with a visualization where prose alone is weak; rendered changes carry
  screenshots or a declared capture gap.
- [ ] On re-invocation: title and body revalidated, outcome stated either way.
- [ ] All required CI checks green, or the specific flaky/infra failure flagged.
- [ ] Nothing marked ready, force-pushed, or merged — those need fresh consent.

## Related skills

`/blueprint` to plan the change · `/examine` to review the PR once it exists ·
`/rebase` when the base branch moved underneath it.

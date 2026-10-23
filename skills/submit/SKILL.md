---
name: submit
description: Open every pull request through this skill — invoke it the moment completed changes need to become a PR, instead of running `git push` or `gh pr create` yourself, and once per PR in a stack. Never open a PR by hand while this skill is installed — it owns the branch and commit shape (Conventional Commits), the pre-push checks, the draft PR body (what, why, how), the mandatory screenshots for anything rendered, and the CI gate with root-cause fixes. Also triggers on "/submit", "submit this", "open a PR", "create a pull request", "push this up", "get this reviewed".
---

# Submit: from working tree to reviewable PR

This skill packages finished work so a reviewer can trust it. The commits read as
history. The checks already pass. The description explains what the diff cannot. The PR
opens as a draft and is gated on CI. `/blueprint` plans the change, `/submit` ships it.

The commands below name `gh`. When `origin` is not GitHub, use the forge's equivalent,
such as `glab` for GitLab. The phases and their gates stay the same.

## Required references

Paths are relative to this file. `<plugin root>` is the directory two levels above it.
Read each file at the phase named.

| File | Read at | Holds |
|---|---|---|
| `../../assets/writing.md` | before writing any commit body or PR text | the writing rules for every text a person reads |
| `references/commits.md` | phase 2 | staging discipline, subject and body rules, trailers |
| `references/pr-description.md` | phase 5, before drafting or validating a description | the glance block, what/why/how, visualization, justification |
| `references/screenshots.md` | phase 5, when the branch changes anything rendered | mandatory screenshots, hosting images from the CLI |
| `references/rationalizations.md` | when tempted to skip a phase | why each shortcut fails |

`<plugin root>/scripts/prose-lint.py` checks a text against the writing rules. Run it on
every commit body and PR body before you record them, and fix every finding in the text.

## Consent

Invoking `/submit` is consent for the full workflow: commit, push, create or edit a draft
PR, and push CI-fix commits. A narrower request such as "just commit" or "just push" is
consent for exactly that. Confirm before stepping past it. Three actions always need
fresh, explicit consent: pushing to the default branch, force-pushing, and marking a draft
PR ready for review.

## Principles

- **Phases are gated.** A phase's exit condition is met before the next phase starts. A
  re-invocation re-enters at phase 0 and skips phases already satisfied. It never skips
  PR revalidation (5b) or CI (6) while a PR exists.
- **The description is the entry point.** Reviewers read it before the diff. It gives the
  why, the shape, and the trade-offs. It never repeats the diff.
- **Keep the PR honest.** New commits change scope. Revalidate the title and body on every
  pass. When nothing is stale, say so. Silence is not evidence.
- **Fix CI at the root.** Read the failing logs until you know why. No placebo "fix CI"
  commits, no disabled checks, no skipped tests.
- **Draft by default.** The user decides when reviewers get pinged, not the workflow.

## Workflow

0. **Orient.** Run `touch "$(git rev-parse --git-dir)/swd-submit"`. The plugin's guard
   refuses `gh pr create` without this fresh marker. Then gather the facts: `git status`
   for uncommitted and untracked files, the current branch, `git log @{u}..HEAD` for
   unpushed commits, and `gh pr view --json number,title,body,state,isDraft,baseRefName`
   for an existing PR. State what you found in a sentence or two. A merged or closed PR
   means new work starts from a fresh branch off the updated default branch.
1. **Branch.** Never commit to the default branch. Follow the repo's convention when one
   is documented or visible in recent branch names. Otherwise use `<author>-<slug>`: the
   git user's first name in lowercase, and a slug from the change itself.
2. **Commit.** Only if phase 0 found uncommitted changes. Read `references/commits.md`
   and `../../assets/writing.md` now. Stage by filename. Write a Conventional Commits
   subject of at most 72 characters, and a body when the subject alone does not explain
   the why. Lint the message
   with `prose-lint.py --commit` before you commit. Unrelated changes are separate commits.
3. **Pre-push checks.** Format, lint, and test every area the branch touches, with the
   repo's own commands. Find them in its agent docs, task runner, or package scripts. Fix
   failures at the root before pushing. "CI will tell me" wastes a cycle and adds fixup
   commits to the history.
4. **Push.** The first push is `git push -u origin <branch>`. After that, plain
   `git push`. Exit: local `HEAD` matches `origin/<branch>`.
5. **PR.** Read `references/pr-description.md` and `../../assets/writing.md` now.
   - **5a, no PR exists.** Draft the title and the body as the reference describes. Lint
     the body with `prose-lint.py` and fix every finding. When the branch changes anything
     rendered, read `references/screenshots.md`. Screenshots are mandatory, or the gap is
     declared in the body. Create the PR as a draft with `gh pr create --draft`, body via
     heredoc.
   - **5b, a PR exists.** Mandatory even when the user only said "push", and even with
     nothing new pushed. Fetch the live title and body and `git log <base>..HEAD`. Check
     that the title still covers all the work. Check that the body still tells the truth:
     scope, claims such as "no new dependencies", the glance-block numbers and side
     effects, and the screenshots. Stale: edit with `gh pr edit` and say what changed. Not
     stale: state "title and body still match the branch".
6. **CI.** Run `gh pr checks` and wait out pending checks. Never declare success with
   checks in flight. On failure, pull the failing logs, find the root cause in the diff,
   fix it, and re-enter at phase 3. A failure that is clearly flaky or on the infra side
   gets flagged to the user instead of retried. Close with the status: "all N required
   checks green", or what failed and which commit fixed it. Then run
   `rm -f "$(git rev-parse --git-dir)/swd-submit"`.

## Definition of done

- [ ] Phase 0 findings stated. No phase skipped silently.
- [ ] Work sits on a named feature branch. Nothing pushed to the default branch.
- [ ] Every new commit has a Conventional subject, imperative and unique, and the trailer.
  No unrelated or sensitive files staged.
- [ ] Every commit body and the PR body pass `prose-lint.py` with no findings.
- [ ] Format, lint, and tests pass locally for every touched area before every push.
- [ ] A draft PR exists. Its description follows the repo template or the what/why/how
  structure, and each section opens with its glance block. A visualization where prose
  alone is weak. Rendered changes carry screenshots or a declared capture gap.
- [ ] On re-invocation: title and body revalidated, outcome stated either way.
- [ ] All required CI checks green, or the specific flaky or infra failure flagged.
- [ ] Nothing marked ready, force-pushed, or merged. Those need fresh consent.
- [ ] The `swd-submit` marker is removed. The guard is armed for the next PR.

## Related skills

`/blueprint` plans the change. `/examine` reviews the PR once it exists. `/rebase` moves
it when the base branch moved underneath it.

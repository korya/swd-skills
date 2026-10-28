---
name: submit
description: Open every pull request through this skill — invoke it the moment completed changes need to become a PR, instead of running `git push` or `gh pr create` yourself, and once per PR in a stack. Never open a PR by hand while this skill is installed — it owns the branch and commit shape (Conventional Commits), the pre-push checks, the draft PR body (what, why, how), the mandatory screenshots for anything rendered, and the CI gate with root-cause fixes. Also triggers on "/submit", "submit this", "open a PR", "create a pull request", "push this up", "get this reviewed".
---

# Submit: from working tree to reviewable PR

This skill packages finished work so a reviewer can trust it. The commits read as
history. The checks already pass. The description explains what the diff cannot. The PR
opens as a draft and is gated on CI.

The commands below name `gh`. When `origin` is not GitHub, use the forge's equivalent,
such as `glab` for GitLab. The phases stay the same.

## Required references

Paths are relative to this file. `<plugin root>` is the directory two levels above it.

| File | Read at | Holds |
|---|---|---|
| `../../assets/writing.md` | before writing any commit body or PR text | the writing rules for every text a person reads |
| `references/commits.md` | phase 2 | staging, subject and body rules, trailers |
| `references/pr-description.md` | phase 5 | the glance block, the structure, visualization, justification |
| `references/screenshots.md` | phase 5, when the branch changes anything rendered | mandatory screenshots, hosting images from the CLI |
| `references/rationalizations.md` | when tempted to skip a phase | why each shortcut fails |

## Consent

Invoking `/submit` is consent for the full workflow: commit, push, create or edit a draft
PR, and push CI-fix commits. A narrower request such as "just commit" or "just push" is
consent for exactly that. Confirm before stepping past it. Three actions always need
fresh, explicit consent: pushing to the default branch, force-pushing, and marking a draft
PR ready for review.

## Workflow

Each phase meets its exit condition before the next one starts. A re-invocation re-enters
at phase 0 and skips the phases already satisfied, never 5b or 6 while a PR exists.

0. **Orient.** Run `touch "$(git rev-parse --git-dir)/swd-submit"`. The plugin's guard
   refuses `gh pr create` without this fresh marker. Then gather the facts: `git status`,
   the current branch, `git log @{u}..HEAD`, and
   `gh pr view --json number,title,body,state,isDraft,baseRefName`. State what you found
   in a sentence or two. A merged or closed PR means new work starts from a fresh branch
   off the updated default branch.
1. **Branch.** Never commit to the default branch. Follow the repo's branch naming when
   one is documented or visible. Otherwise use `<author>-<slug>`: the git user's first
   name in lowercase, and a slug from the change.
2. **Commit,** if phase 0 found uncommitted changes. Read `references/commits.md` and
   `../../assets/writing.md` now. Stage by filename, and give each unrelated change its
   own commit. Lint each message with `<plugin root>/scripts/prose-lint.py --commit`
   before you commit.
3. **Pre-push checks.** Format, lint, and test every area the branch touches, with the
   repo's own commands from its agent docs, task runner, or package scripts. Fix failures
   at the root before pushing.
4. **Push.** The first push is `git push -u origin <branch>`, then plain `git push`. Exit:
   local `HEAD` matches `origin/<branch>`.
5. **PR.** Read `references/pr-description.md` and `../../assets/writing.md` now.
   - **5a, no PR exists.** Draft the title and the body. When the branch changes anything
     rendered, read `references/screenshots.md`: screenshots are mandatory, or the body
     declares the gap. Lint the body with `prose-lint.py` and fix every finding. Create
     the PR with `gh pr create --draft`.
   - **5b, a PR exists.** Mandatory even when the user only said "push", and even with
     nothing new pushed. Fetch the live title and body and `git log <base>..HEAD`. Check
     that the title still covers all the work. Check that every claim in the body is still
     true. That covers the scope, statements such as "no new dependencies", the
     glance-block numbers and side effects, and the screenshots. Stale: edit with `gh pr edit` and say what
     changed. Not stale: state "title and body still match the branch".
6. **CI.** Run `gh pr checks` and wait out pending checks. Never declare success with
   checks in flight. On failure, read the failing logs, find the root cause, fix it, and
   re-enter at phase 3. Never disable a check or skip a test. Flag a failure that is
   clearly flaky or on the infra side to the user instead of retrying it. Close with the
   status: "all N required checks green", or what failed and which commit fixed it. Then
   run `rm -f "$(git rev-parse --git-dir)/swd-submit"`.

## Definition of done

- [ ] Phase 0 findings stated. No phase skipped silently.
- [ ] Work sits on a feature branch. Nothing pushed to the default branch.
- [ ] Every new commit has a Conventional subject and the trailer. No unrelated or
  sensitive files staged.
- [ ] Every commit body and the PR body pass `prose-lint.py` with no findings.
- [ ] Format, lint, and tests passed locally before every push.
- [ ] A draft PR exists. Each section of its description opens with its glance block.
  Rendered changes carry screenshots or a declared capture gap.
- [ ] On re-invocation, the title and body were revalidated and the outcome stated.
- [ ] All required CI checks green, or the flaky or infra failure flagged.
- [ ] Nothing marked ready, force-pushed, or merged without fresh consent.
- [ ] The `swd-submit` marker is removed.

## Related skills

`/blueprint` plans the change. `/examine` reviews the PR once it exists. `/rebase` moves
it when the base branch moved underneath it.

# Commits: subject, body, staging

Loaded from `SKILL.md` phase 2. A commit is read three ways — `git log --oneline`, the
full log, and `git blame` years later — and the rules below serve all three.

## Staging discipline

- Run `git status` and `git diff` first; know what you are about to record.
- **Stage by filename.** `git add -A` / `git add .` sweep in env files, secrets, editor
  droppings, and unrelated edits that happen to share the working tree. If the user has
  their own uncommitted work in the tree, it is theirs — leave it unstaged.
- Never commit credentials, `.env` files, or generated artifacts, even when asked —
  flag it and stop.
- **Unrelated changes are separate commits.** "They were in the tree together" is not a
  relationship. Stage and commit each logical change on its own.

## Subject line

Conventional Commits: `<type>(<scope>): <subject>`. Scope optional. Common types:
`feat`, `fix`, `chore`, `refactor`, `test`, `docs`.

- **Capitalize the first word** of the subject: `fix(auth): Redirect to login on 401`.
- **Imperative mood** — "Add feature", not "Added" or "Adds". Self-check: *"If applied,
  this commit will `<subject>`"* must read naturally.
- **Hard limit 72 characters; aim for 50.** No trailing period.
- **Unique in the repo.** "Fix bug" and "Update handler" fail — name the component and
  the change. If one line cannot describe the change, split the commit.

## Body

Separate from the subject with a **blank line** — `git log`, `rebase`, and `shortlog`
render wrongly without it. Then:

- **Pyramid writing.** Most important fact first; supporting detail beneath.
- **What and why, not how** — the diff already shows how. Explain the problem and the
  reasoning behind the approach.
- **Before/after framing.** "Previously, X. Now, Y." Tense alone is ambiguous in a
  message read years later.
- **Scope.** If a reader might expect a broader change, say what this commit does *not* do.
- **Wrap at 100 characters** — commit bodies are read in fixed-width tools. (PR
  descriptions are the opposite: never hard-wrapped; the browser flows them.)

## Mechanics

Pass the full message via heredoc to dodge shell-escaping:

```bash
git commit -m "$(cat <<'MSG'
feat(auth): Redirect to login on 401

Previously an expired session rendered a blank page. Now the client
redirects to /login with the original URL preserved.

Co-Authored-By: <model name> <noreply@anthropic.com>
MSG
)"
```

Always append the co-author trailer naming the model actually in use. If the repo's own
docs prescribe additional trailers (session links, issue tags), honor them.

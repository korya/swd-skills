# Commits: staging, subject, body

Loaded from `SKILL.md` phase 2. A commit is read three ways: `git log --oneline`, the
full log, and `git blame` years later. The body follows `../../assets/writing.md`.

## Staging

- Run `git status` and `git diff` first. Know what you are about to record.
- **Stage by filename.** `git add -A` and `git add .` sweep in env files, secrets, scratch
  files, and unrelated edits. If the user has uncommitted work of their own in the tree,
  it is theirs. Leave it unstaged.
- Never commit credentials, `.env` files, or generated artifacts, even when asked. Flag it
  and stop.
- **Unrelated changes are separate commits.** Sharing a working tree is not a relationship.

## Subject line

Conventional Commits: `<type>(<scope>): <subject>`. Scope is optional. Common types:
`feat`, `fix`, `chore`, `refactor`, `test`, `docs`.

- **Capitalize the first word**: `fix(auth): Redirect to login on 401`.
- **Imperative mood.** "If applied, this commit will <subject>" must read naturally.
- **At most 72 characters, aim for 50.** No trailing period.
- **Unique in the repo.** "Fix bug" fails. Name the component and the change. If one line
  cannot describe the change, split the commit.

## Body

Add a body when the subject alone does not explain the why. A blank line separates it
from the subject.

- **What and why, not how.** The diff shows how. Explain the problem and the reasoning.
- **Before and after.** "Previously, X. Now, Y." Tense alone is ambiguous years later.
- **Scope.** If a reader might expect a broader change, say what this commit does not do.
- **Wrap at 100 characters.** Commit bodies are read in fixed-width tools.

## Mechanics

Write the message to a file, lint it, then commit from the file. In `--commit` mode the
linter also checks the subject format.

```bash
MSG="$(git rev-parse --git-dir)/swd-commit-msg"
cat >| "$MSG" <<'EOF'
feat(auth): Redirect to login on 401

Previously an expired session rendered a blank page. Now the client
redirects to /login with the original URL preserved.

Co-Authored-By: <model name> <noreply@anthropic.com>
EOF
python3 "<plugin root>/scripts/prose-lint.py" --commit "$MSG"   # fix every finding first
git commit -F "$MSG"
```

Always append the co-author trailer naming the model in use. Honor any further trailers
the repo's docs prescribe, such as session links or issue tags.

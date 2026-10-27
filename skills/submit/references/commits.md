# Commits: staging, subject, body

Loaded from `SKILL.md` phase 2. A commit is read three ways: `git log --oneline`, the
full log, and `git blame` years later. The rules below serve all three. The body follows
`../../assets/writing.md`.

## Staging discipline

- Run `git status` and `git diff` first. Know what you are about to record.
- **Stage by filename.** `git add -A` and `git add .` sweep in env files, secrets, editor
  droppings, and unrelated edits that share the working tree. If the user has uncommitted
  work of their own in the tree, it is theirs. Leave it unstaged.
- Never commit credentials, `.env` files, or generated artifacts, even when asked. Flag it
  and stop.
- **Unrelated changes are separate commits.** "They were in the tree together" is not a
  relationship. Stage and commit each logical change on its own.

## Subject line

Conventional Commits: `<type>(<scope>): <subject>`. Scope is optional. Common types:
`feat`, `fix`, `chore`, `refactor`, `test`, `docs`.

- **Capitalize the first word** of the subject: `fix(auth): Redirect to login on 401`.
- **Imperative mood.** "Add feature", not "Added" or "Adds". Self-check: "If applied, this
  commit will <subject>" must read naturally.
- **Hard limit 72 characters. Aim for 50.** No trailing period.
- **Unique in the repo.** "Fix bug" and "Update handler" fail. Name the component and the
  change. If one line cannot describe the change, split the commit.

## Body

Separate the body from the subject with a blank line. `git log`, `rebase`, and `shortlog`
render wrongly without it. Then:

- **Pyramid writing.** The first sentence states the most important fact. Supporting
  detail follows beneath it.
- **What and why, not how.** The diff already shows how. Explain the problem and the
  reasoning behind the approach.
- **Before and after.** "Previously, X. Now, Y." Tense alone is ambiguous in a message read
  years later.
- **Scope.** If a reader might expect a broader change, say what this commit does not do.
- **Wrap at 100 characters.** Commit bodies are read in fixed-width tools. PR descriptions
  are the opposite: never hard-wrapped, because the browser flows them.

## Mechanics

Write the message to a file, lint it, then commit from the file. This avoids shell
escaping and gives the linter something to read. In `--commit` mode the linter also checks
the subject: Conventional format, at most 72 characters, no trailing period, blank line
after it.

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

Always append the co-author trailer naming the model in use. If the repo's own docs
prescribe additional trailers, such as session links or issue tags, honor them.

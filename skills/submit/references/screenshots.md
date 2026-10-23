# Screenshots and image hosting

Loaded from `SKILL.md` phase 5 whenever the branch changes anything rendered. Rendered
means the appearance or behavior a user can see, not merely UI files touched. A refactor
with intentionally identical output needs no screenshots. State "No visual change" instead.

## What to capture

- **"After" at minimum.** When the change alters something that already existed, show
  "Before / After" side by side in a two-column table.
- **Mobile-viewport shots** when the change affects mobile.
- **A short GIF** for anything that moves: hover states, transitions, animations, drag. A
  static frame cannot show them.
- **Cannot capture** because of a missing backend, credentials, or device? Say so in the
  PR body and ask the user to attach screenshots. Never skip silently.

Recapture when later commits change the UI after the shots were taken. A stale screenshot
misleads reviewers worse than none.

## Hosting from the CLI (GitHub)

Never commit screenshots to the branch just to host them. Keep the PR diff code-only.
Host them on a detached attachment ref. The objects live in the repo on GitHub, in no
branch and no diff.

```bash
BLOB=$(git hash-object -w after.png)
TREE=$(printf '100644 blob %s\tafter.png\n' "$BLOB" | git mktree)
COMMIT=$(git commit-tree "$TREE" -m "attach: PR #<n> after")
git push origin "${COMMIT}:refs/attachments/pr-<n>-after"
```

Quote the refspec. zsh treats a bare `$VAR:r` as a history modifier. Then embed the
SHA-pinned URL in the body:

```
https://github.com/<owner>/<repo>/raw/<COMMIT>/after.png
```

For "Before", prefer pinning a file already reachable in history, for example on the base
branch, over a second attachment. Keep the ref alive while the PR is open. The commit must
stay reachable for the URL to resolve.

## The wrong-host trap

**Use `github.com/<owner>/<repo>/raw/<sha>/…`, never `raw.githubusercontent.com/…`.**
They look interchangeable but authenticate differently. The first is served on
github.com, so the reviewer's session cookie authorizes it. It renders for public and
private repos.

The second is a separate domain that receives no session cookie. On a
private repo it 404s into a broken-image icon. Right blob, wrong host. This has bitten
real PRs.

Guardrail before `gh pr create` or `gh pr edit` on a private repo: grep the drafted body
for `raw.githubusercontent.com` and rewrite any hit to the `github.com/…/raw/…` form.

GitHub's drag-and-drop upload (`github.com/user-attachments/assets/<uuid>`) also renders.
Its endpoint is web-session-only and rejects tokens, so it is a manual fallback for the
user, not a CLI path.

Other forges: use the forge's own attachment API when it has one, such as GitLab's
`POST /projects/:id/uploads`. The detached-ref trick works anywhere refs are pushable and
raw files are servable.

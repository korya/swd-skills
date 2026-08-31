# Screenshots and image hosting

Loaded from `SKILL.md` phase 5 whenever the branch changes anything **rendered** — the
appearance or behavior a user can see, not merely UI files touched. A refactor with
intentionally identical output needs no screenshots; state "No visual change" instead.

## What to capture

- **"After" at minimum**; **"Before / After" side by side** (a two-column table) when the
  change alters something that already existed.
- **Mobile-viewport shots** when the change affects mobile.
- **A short GIF** for anything that moves — hover states, transitions, animations, drag —
  a static frame cannot show them.
- **Cannot capture** (missing backend, credentials, device)? Say so explicitly in the PR
  body and ask the user to attach screenshots. Never skip silently.

Recapture when later commits change the UI after the shots were taken — a stale
screenshot misleads reviewers worse than none.

## Hosting from the CLI (GitHub)

Never commit screenshots to the branch just to host them — keep the PR diff code-only.
Host them on a **detached attachment ref**: the objects live in the repo on GitHub, in no
branch and no diff.

```bash
BLOB=$(git hash-object -w after.png)
TREE=$(printf '100644 blob %s\tafter.png\n' "$BLOB" | git mktree)
COMMIT=$(git commit-tree "$TREE" -m "attach: PR #<n> after")
git push origin "${COMMIT}:refs/attachments/pr-<n>-after"
```

Quote the refspec — zsh treats a bare `$VAR:r` as a history modifier. Then embed the
SHA-pinned URL in the body:

```
https://github.com/<owner>/<repo>/raw/<COMMIT>/after.png
```

For "Before", prefer pinning a file already reachable in history (e.g. on the base
branch) over a second attachment. Keep the ref alive while the PR is open — the commit
must stay reachable for the URL to resolve.

## The wrong-host trap

**Use `github.com/<owner>/<repo>/raw/<sha>/…`, never `raw.githubusercontent.com/…`.**
They look interchangeable but authenticate differently: `github.com/…/raw/…` is served on
github.com, so the reviewer's session cookie authorizes it — it renders for public *and*
private repos. `raw.githubusercontent.com` is a separate domain that receives no session
cookie, so on a private repo it 404s into a broken-image icon. Right blob, wrong host —
this has bitten real PRs.

Guardrail before `gh pr create` / `gh pr edit` on a private repo: grep the drafted body
for `raw.githubusercontent.com` and rewrite any hit to the `github.com/…/raw/…` form.

GitHub's drag-and-drop upload (`github.com/user-attachments/assets/<uuid>`) also renders,
but its endpoint is web-session-only and rejects tokens — a manual fallback for the user,
not a CLI path.

Other forges: use the forge's own attachment API when it has one (GitLab:
`POST /projects/:id/uploads`); the detached-ref trick works anywhere refs are pushable
and raw files are servable.

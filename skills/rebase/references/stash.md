# Dirty working tree: stash before, restore after

Loaded from `SKILL.md` step 0 when `git status --porcelain` is not empty. Covers the
preflight stash and the restore in step 9.5. A clean tree never needs this file.

## 0. Preflight: account for uncommitted changes

Before touching history, check the working tree:

```bash
git status --porcelain
```

If the working tree is clean, skip to step 1.

Otherwise the working tree is a fourth point alongside `curr`, `old_base`, and `new_base`.
It is work the user has not yet decided whether to keep. The skill must account for it
explicitly, for three reasons. `git rebase` refuses to run with a dirty tree. Silently
dropping it costs the user real work. And the changes themselves may be relevant context
for the rebase: a half-applied fix, debug instrumentation, a WIP commit in waiting.

Do this:

1. **Surface the diff to the user.** Show `git status --porcelain` and a one-line summary
   of what is modified. Ask whether the changes are related to the rebase. The answer does
   not change the mechanics, which are always stash and always restore. It changes how you
   reason about conflicts later. Related changes that conflict on restore are a finding.
   Unrelated debug prints that conflict are noise.
2. **Stash with a labeled, unique name** so the entry is easy to spot in `git stash list`
   and survives accidental `git stash drop` elsewhere. Include untracked files. Debug
   scripts and new test files are common:

   ```bash
   STASH_LABEL="swd-rebase-preflight-$(date +%Y%m%d-%H%M%S)"
   git stash push --include-untracked --message "$STASH_LABEL"
   ```

3. **Remember the label** for step 9.5. If the agent context might compact mid-rebase,
   write it somewhere durable: a scratch note in the conversation, a plan entry.

After this step, the working tree is clean and the rest of the workflow runs unchanged.

## 9.5. Restore stashed changes

If step 0 stashed anything, restore it now, before final verification. Then the
verification reflects the state the user will have:

```bash
git stash list | grep "$STASH_LABEL"          # confirm it is there
git stash pop "stash@{<index of the labeled entry>}"
```

Outcomes:

- **Clean pop.** The working tree now has the rebased history plus the previously
  uncommitted changes. Continue to step 10.
- **Pop with conflicts.** Git leaves the stash entry intact and writes conflict markers
  into the working tree. **Do not drop the stash.** Surface the conflict to the user with
  three things. The files involved. Whether the stashed changes are related to the rebase,
  from step 0's question. The options: resolve manually, drop the stash if the user
  confirms the changes are now obsolete, or abandon and let the user recover from
  `git stash list`.

Never silently run `git checkout -- .` or `git reset --hard` to clear a conflicted pop.
The user's uncommitted work is the most fragile state in this entire workflow.

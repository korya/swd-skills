# Dirty working tree: stash before, restore after

Loaded at step 0 when `git status --porcelain` is not empty. A clean tree never needs this
file.

## Step 0: stash

The uncommitted work is a fourth point beside `curr`, `old_base`, and `new_base`.
`git rebase` refuses a dirty tree, and losing the work costs the user real effort.

1. **Show it to the user.** Show `git status --porcelain` with a one-line summary, and ask
   whether the changes relate to the rebase. The mechanics stay the same either way. The
   answer tells you later whether a conflict on restore is a finding or noise.
2. **Stash it under a unique label**, untracked files included:

   ```bash
   STASH_LABEL="swd-rebase-preflight-$(date +%Y%m%d-%H%M%S)"
   git stash push --include-untracked --message "$STASH_LABEL"
   ```

3. **Write the label down** where a context compaction cannot lose it, such as the plan.

## Step 9: restore

Restore before the final verification, so that it checks the state the user will have.

```bash
git stash list | grep "$STASH_LABEL"
git stash pop "stash@{<index of the labeled entry>}"
```

- **Clean pop.** Continue to step 10.
- **Conflicted pop.** Git keeps the stash entry and writes conflict markers into the tree.
  Do not drop the stash. Tell the user three things: the files involved, whether the
  changes relate to the rebase, and the options. They can resolve by hand, drop the stash
  once they confirm it is obsolete, or recover it later from `git stash list`.

Never clear a conflicted pop with `git checkout -- .` or `git reset --hard`. That deletes
the user's uncommitted work, the most fragile state in this workflow.

# Anti-rationalization table and anti-patterns

Read this when you catch yourself skipping a step. If your reason is below, do the step.

## Anti-rationalization table

| Rationalization | Why it fails here |
|---|---|
| "Conflicts resolved cleanly. Ship it." | Conflict markers are the visible 10%. Semantic drift is the invisible 90%. A clean text merge can still violate an invariant the delta added. |
| "The tests passed after the rebase, so it's fine." | The tests cover what was true on `old_base`. If the delta added new surface (a new caller, channel, or spec), the suite may not cover it yet. |
| "Git accepted the replay, so the commits must still be correct." | Git replays text. It does not check that the solution still matches the problem. Re-read the spec on `new_base`. |
| "The delta didn't touch the files `curr` changes, so there is no cross-impact." | Untouched at the file level is not untouched semantically. A renamed helper, a new invariant, a tightened type can all invalidate `curr` without touching its files. |
| "The original spec still applies." | Re-read it on `new_base`. Specs evolve in the delta more often than agents assume. "Still applies" should be a finding, not an assumption. |
| "`-X theirs` or `-X ours` will clear this conflict fast." | These options hide semantic divergence in a hunk-shaped blind spot. Resolve by reading both sides. |
| "This commit looks redundant. I'll drop it silently." | Dropping a commit is a user-visible scope decision. Surface it, get the nod, then drop. |
| "I'll bundle the rebase fix into the original commit." | If the fix preserves the original intent, bundle. If it is a new bug fix you discovered during the rebase, split it into its own commit. |
| "Lint and tests aren't needed. The rebase didn't touch logic." | A rebase always touches logic. Replaying a change against new code is a logic change. Run them. |
| "Three iterations of conflict resolution is enough. Push it." | If you have fought the same hunk three times, the approach itself is probably wrong on `new_base`. Stop and reframe with the user. |
| "The working tree was dirty. I'll just stash and pop without telling the user." | The stashed work is the most fragile state in this workflow. If the pop conflicts and the agent silently drops it, real work disappears. Label the stash, surface it, restore explicitly, handle pop conflicts visibly. |
| "The pop conflicted. `git checkout -- .` to clean it up and move on." | That deletes the user's uncommitted changes. The stash entry survives the pop conflict. Leave it alone and surface it to the user. |

## Anti-patterns

- **Treating a rebase as a merge-conflict exercise.** Conflict markers are the visible 10%.
  Semantic drift is the invisible 90%.
- **Replaying without re-reading the spec.** The spec on `old_base` is not the spec you are
  shipping against.
- **Bundling rebase fixes into the original commit when they are new bug fixes.** Split
  them.
- **Skipping lint and tests "because the rebase didn't touch logic".** A rebase always
  touches logic. That is the whole point of this skill.
- **Forcing through a Conflicting classification without surfacing it.** Stop and talk to
  the user.

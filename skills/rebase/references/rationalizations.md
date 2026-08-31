# Anti-rationalization table and anti-patterns

Read this when you catch yourself skipping a step — if your reason is below, do the step.

## Anti-rationalization table

| Rationalization | Why it fails here |
|---|---|
| "Conflicts resolved cleanly — ship it." | Conflict markers are the visible 10%; semantic drift is the invisible 90%. A clean text merge can still violate an invariant `delta` added. |
| "The tests passed after the rebase, so it's fine." | The tests cover what was true on `old_base`. If `delta` added new surface (new caller, new channel, new spec), the suite may not cover it yet. |
| "Git accepted the replay, so the commits must still be correct." | Git replays text. It does not check that the *solution* still matches the *problem*. Re-read the spec on `new_base`. |
| "`delta` didn't touch the files `curr` changes — no cross-impact." | File-level untouched ≠ semantically untouched. A renamed helper, a new invariant, a tightened type — all can invalidate `curr` without touching its files. |
| "The original spec still applies." | Re-read it on `new_base`. Specs evolve in `delta` more often than agents assume; "still applies" should be a finding, not an assumption. |
| "`-X theirs` / `-X ours` will clear this conflict fast." | These options hide semantic divergence in a hunk-shaped blindspot. Resolve by reading both sides. |
| "This commit looks redundant — I'll drop it silently." | Dropping a commit is a user-visible scope decision. Surface it, get the nod, then drop. |
| "I'll bundle the rebase-fix into the original commit." | If the fix is preserving the original intent, bundle. If it's a *new* bug fix you discovered during rebase, split it into its own commit. |
| "Lint/tests aren't needed; rebase didn't touch logic." | Rebase always touches logic — replaying a change against new code *is* a logic change. Run them. |
| "Three iterations of conflict resolution is enough — push it." | If you've fought the same hunk three times, the approach itself is probably wrong on `new_base`. Stop and reframe with the user. |
| "The working tree was dirty; I'll just `git stash` and `git stash pop` without telling the user." | The stashed work is the most fragile state in this workflow — if `pop` conflicts and the agent silently drops it, real work disappears. Label the stash, surface it, restore explicitly, handle pop conflicts visibly. |
| "Pop conflicted; `git checkout -- .` to clean it up and move on." | That deletes the user's uncommitted changes. The stash entry survives the pop conflict — leave it alone and surface to the user. |

## Anti-patterns

- **Treating rebase as a merge-conflict exercise.** Conflict markers are the visible 10%; semantic drift is the invisible 90%.
- **Replaying without re-reading the spec.** The spec on `old_base` is not the spec you're shipping against.
- **Bundling rebase fixes into the original commit when they're really new bug fixes.** Split them.
- **Skipping lint/tests "because rebase didn't touch logic."** Rebase always touches logic — that's the whole point of this skill.
- **Forcing through a Conflicting classification without surfacing it.** Stop and talk to the user.

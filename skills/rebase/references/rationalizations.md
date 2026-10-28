# Rationalizations

Read this when you catch yourself skipping a step. If your reason is below, do the step.

| Rationalization | Why it fails here |
|---|---|
| "Git replayed it cleanly and the tests pass, so it is correct." | Git replays text, and the tests cover what was true on `old_base`. Conflict markers are the visible 10%. Semantic drift, such as an invariant or a caller the delta added, is the other 90%. |
| "The delta did not touch the files `curr` changes." | A renamed helper, a new invariant, or a tighter type can invalidate `curr` without touching its files. |
| "The original spec still applies." | Re-read it on `new_base`. Specs change in the delta more often than agents assume. "Still applies" is a finding, not an assumption. |
| "`-X theirs` or `-X ours` will clear this conflict fast." | They hide semantic divergence inside the hunk. Resolve by reading both sides. |
| "This commit looks redundant. I'll drop it." | Dropping a commit changes the scope. Surface it and get the user's agreement first. |
| "The rebase did not touch logic, so lint and tests can wait." | Replaying a change against new code is a logic change. Run them. |
| "This is the third round on this hunk. I'll push it anyway." | Three fights with the same hunk mean the approach is probably wrong on `new_base`. Stop and reframe with the user. |

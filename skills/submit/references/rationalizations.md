# Rationalizations: shortcuts that corrupt the workflow

Loaded when tempted to skip a phase. Each row looks reasonable in the moment. Each has
already cost someone a bad merge, a leaked file, or a reviewer's trust.

| Shortcut | Why it fails |
|---|---|
| "I'll just `git add -A`, it's all related." | It never is. Env files, scratch scripts, and the user's own half-done edits ride along, and un-leaking a secret is not a `revert`. Stage by filename. |
| "One commit is fine, the changes are small." | The revert unit and the blame unit are both the commit. Two unrelated changes in one commit means neither can be reverted or understood alone. |
| "Skip the local checks, CI will catch it." | CI catching it costs a full cycle, a fixup commit, and a red X reviewers see. Local checks cost a minute. |
| "The lint rule is wrong anyway, disable it." | The rule encodes a lesson the repo already paid for. If it is truly wrong, that is its own PR with its own justification, not a drive-by in this one. |
| "Push straight to the default branch, it's tiny." | Size is not the criterion. Review is. Tiny changes break production precisely because nobody looked. |
| "The PR body can stay as-is, I only pushed a commit." | New commits change scope. A stale description makes the reviewer review the wrong PR. Revalidation (5b) is mandatory, and "nothing stale" must be said aloud. |
| "The trade-offs are in the details, the summary can stay short." | The summary is where trade-offs go. A reviewer decides in the first fifteen seconds, and a slowdown or a cost buried in paragraph six is a surprise after approval. Lede, then the side effects, good and bad, with their numbers. |
| "The diff speaks for itself, skip the description." | The diff shows how. Only the description can say why, what was assumed, and what was deliberately not done. Those are the three things reviews argue about. |
| "The prose linter is nitpicking, the sentence reads fine to me." | Fifty-word sentences are how the complaints started. The linter encodes the limits readers already asked for. Fix the text. Do not cut words the reader needs, and do not hyphenate clauses together to dodge the count. |
| "Mark it ready, the user probably wants that." | Ready-for-review pings humans. The user decides when to spend reviewer attention, never the workflow. Same for force-pushes and merges. |
| "CI is red but it looks flaky, rerun until green." | Rerunning until green is how real failures ship. Read the logs first. Call it flaky only when the evidence says infra, then flag it to the user. |
| "Declare success, checks are almost done." | "Almost green" is not a state. A check that fails after your summary makes the summary a lie. Wait. |
| "Screenshots later, the UI change is minor." | Reviewers approve what they can see. A rendered change without a screenshot forces every reviewer to check out and build the branch, or to approve blind. |
| "I know the pattern, I'll just `gh pr create` by hand." | The pattern is the part that never varies. The phases you skip are the ones that do: screenshots for a rendered change, the body revalidated against every commit, CI waited out. A PR opened by hand carries none of them, and a stack opened by hand carries none of them six times. The skill is the trigger, not the user's wording. |

# Rationalizations: shortcuts that corrupt the workflow

Read this when tempted to skip a phase. Each row looks reasonable in the moment. Each has
already cost someone a bad merge, a leaked file, or a reviewer's trust.

| Shortcut | Why it fails |
|---|---|
| "I'll just `git add -A`, it's all related." | It never is. Env files, scratch scripts, and the user's own half-done edits ride along, and un-leaking a secret is not a `revert`. |
| "One commit is fine, the changes are small." | The commit is the unit of revert and of blame. Two unrelated changes in one commit can be neither reverted nor understood alone. |
| "Skip the local checks, CI will catch it." | CI catching it costs a full cycle, a fixup commit, and a red X reviewers see. Local checks cost a minute. |
| "The lint rule is wrong anyway, disable it." | The rule encodes a lesson the repo already paid for. If it is truly wrong, that is its own PR with its own justification. |
| "Push straight to the default branch, it's tiny." | Review is the criterion, not size. Tiny changes break production because nobody looked. |
| "The PR body can stay as is, I only pushed a commit." | New commits change scope. A stale description makes the reviewer review the wrong PR. |
| "The diff speaks for itself." | The diff shows how. Only the description can say why, what was assumed, and what was deliberately not done. Reviews argue about those three. |
| "It's in the commit messages, or the ticket." | Commits are the history and tickets give product's view. Reviewers land on the PR, and links rot. |
| "The trade-offs are in the details, the summary can stay short." | A reviewer decides in the first fifteen seconds. A slowdown buried in paragraph six is a surprise after approval. |
| "The prose linter is nitpicking, the sentence reads fine to me." | The linter encodes the limits readers asked for. Fix the text. Do not cut words the reader needs, and do not hyphenate clauses together to dodge the count. |
| "Mark it ready, the user probably wants that." | Ready-for-review pings humans. The user decides when to spend reviewer attention. |
| "CI is red but it looks flaky, rerun until green." | Rerunning until green is how real failures ship. Read the logs first. |
| "Declare success, checks are almost done." | A check that fails after your summary makes the summary a lie. Wait. |
| "Screenshots later, the UI change is minor." | Reviewers approve what they can see. Without a screenshot, every reviewer builds the branch or approves blind. |
| "I know the pattern, I'll just `gh pr create` by hand." | The phases you skip are the ones that vary: screenshots, revalidation against every commit, CI waited out. The skill is the trigger, not the user's wording. |

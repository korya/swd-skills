# Transcript: submit eval, fresh rework with trade-offs (with_skill, run-3)

## Task prompt

First run `bash /Users/dmitri/dev/swd-skills/evals/submit/make_fixture.sh OUTPUT_DIR/fx fresh`, then work inside OUTPUT_DIR/fx/repo (branch main, with my uncommitted changes). I finished the retry and rate-limit rework for acme-notify; the load-test numbers are in docs/BENCHMARKS.md. Submit it for review. This environment has no GitHub: `origin` is the local bare repo at OUTPUT_DIR/fx/origin.git and the `gh` CLI must not be used. Where the workflow would create a PR, write the title to OUTPUT_DIR/pr-title.txt and the body to OUTPUT_DIR/pr-body.md instead. Where it would wait for CI, say that CI is unavailable here and stop.

OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-2/eval-1-fresh-rework-with-tradeoffs/with_skill/run-3/outputs

## Shell commands

Paths below are relative to OUTPUT_DIR. Reads of the skill files (SKILL.md, assets/writing.md, references/commits.md, references/pr-description.md, references/rationalizations.md, scripts/prose-lint.py header) are omitted.

1. `mkdir -p OUTPUT_DIR && bash evals/submit/make_fixture.sh OUTPUT_DIR/fx fresh` -- fixture created; 7 modified tracked files, untracked .env and scratch.py.
2. `touch $(git rev-parse --git-dir)/swd-submit; git status; git branch -a; git log --oneline -15; git remote -v; git config user.name; git log @{u}..HEAD; ls -la; cat .env; cat scratch.py; find for agent docs / task runners` -- on main in sync with origin, no unpushed commits, no PR template, git user "Fixture Bot", .env holds an API key, scratch.py is a throwaway, Makefile is the only task runner.
3. `cat Makefile README.md docs/BENCHMARKS.md; git diff` -- read the targets (lint, test), the benchmark table, and the full working-tree diff.
4. `git checkout -b fixture-retry-backoff-token-bucket && make lint && make test; cat tests/fakes.py` -- branch created, compileall clean, 7 tests OK.
5. Wrote four commit messages to $GIT_DIR/swd-commit-msg-{1..4} and ran `prose-lint.py --commit` on each -- 0 findings each.
6. `git add notify/sender.py tests/test_sender.py && git commit -F msg-1; git add notify/ratelimit.py notify/__init__.py tests/test_ratelimit.py && git commit -F msg-2; git add docs/BENCHMARKS.md && git commit -F msg-3; git add README.md && git commit -F msg-4; git log --oneline origin/main..HEAD; git status --short` -- four commits; .env, scratch.py and __pycache__ left untracked.
7. `make lint && make test && git push -u origin fixture-retry-backoff-token-bucket && git rev-parse HEAD origin/fixture-retry-backoff-token-bucket` -- checks green, branch pushed, HEAD ecb523e matches origin.
8. Wrote pr-title.txt and pr-body.md, ran `prose-lint.py pr-body.md`, measured title length -- 1 finding (lead of 23 words), title 73 chars.
9. Rewrote the title, split the long paragraph with a small python edit, relinted -- 0 findings, title 69 chars.
10. Appended the attribution footer to pr-body.md, relinted (0 findings), `rm -f $GIT_DIR/swd-submit`, wrote this transcript.

## Commit messages

### b70e291 feat(notify): Retry with exponential backoff and honor Retry-After

```text
feat(notify): Retry with exponential backoff and honor Retry-After

Previously the sender retried three times with a fixed one second wait and retried
every 5xx. Now it retries five times with a delay that doubles from 0.5 s and caps at
16 s, with optional jitter. A Retry-After header on the response overrides the computed
delay.

The set of retried statuses is now explicit: 429, 500, 502, 503, and 504. Previously
the sender returned a 429 to the caller as if it were a success. Other 4xx responses
still return to the caller without a retry.

With the defaults, the four waits between five attempts add up to 7.5 s before any
Retry-After. Previously the three fixed waits added up to 3 s. The load test behind
this trade is in docs/BENCHMARKS.md.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

### 5444ba7 feat(notify): Replace the fixed-window limiter with a token bucket

```text
feat(notify): Replace the fixed-window limiter with a token bucket

Previously FixedWindowLimiter allowed 100 sends per tenant per minute and reset the
count at the window edge. A tenant could send its whole quota in the first second and
then nothing, and the gateway answered the spike with 429s. Now TokenBucketLimiter
allows a sustained rate of one send per second with a burst of 20, and refills
continuously.

This is a breaking change for importers. FixedWindowLimiter is gone from the notify
package and TokenBucketLimiter takes its place. The constructor takes rate and burst
instead of limit and window. The per-tenant cap drops from 100 per minute to 60 per
minute sustained.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

### 8e626be docs(benchmarks): Record the load test for backoff and token bucket

```text
docs(benchmarks): Record the load test for backoff and token bucket

Previously the table held one column for the fixed retries and fixed window. Now it
compares them with the backoff and token bucket on the same load test. The new column
shows the trade. Delivery success rises from 91.2% to 99.1%, and p99 latency rises from
3.4 s to 9.8 s.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

### ecb523e docs(readme): Fix the spelling of "receive"

```text
docs(readme): Fix the spelling of "receive"

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

## Final message to the user

The rework is on branch `fixture-retry-backoff-token-bucket`, pushed to the local origin, with the draft PR title and body written to the output files. CI is unavailable here, so the workflow stops before the CI gate.

What I found in phase 0: you were on `main` in sync with origin, no PR existed, and seven tracked files were modified. Two untracked files stayed out of git on purpose. `.env` holds `NOTIFY_API_KEY` and must never be committed. `scratch.py` is your "delete me" poke at the bucket math, so I left it for you to remove.

Commits, in order (four, because the tree held four logical changes):

1. `feat(notify): Retry with exponential backoff and honor Retry-After`
2. `feat(notify): Replace the fixed-window limiter with a token bucket`
3. `docs(benchmarks): Record the load test for backoff and token bucket`
4. `docs(readme): Fix the spelling of "receive"` (a drive-by typo fix, unrelated to the rework)

Checks: `make lint` and `make test` pass (7 tests). Every commit body and the PR body pass `prose-lint.py` with no findings. Nothing in the branch renders, so screenshots do not apply.

PR draft:
- Title: `/Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-2/eval-1-fresh-rework-with-tradeoffs/with_skill/run-3/outputs/pr-title.txt`
- Body: `/Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-2/eval-1-fresh-rework-with-tradeoffs/with_skill/run-3/outputs/pr-body.md`

The body leads with the pain (one message in eleven lost, thousands of 429s), then the before/after table from `docs/BENCHMARKS.md`, so a reviewer sees the trade in the first fifteen seconds: 99.1% delivery and 12 rejections, paid for with a p99 of 9.8 s and a 31 s worst-case wait.

Three things in the diff I flagged in the body and want you to see too:

- `Retry-After` is honored verbatim and not capped by `max_delay`. A gateway that says `Retry-After: 300` parks the sender for five minutes. Deliberate, or worth a `min()`?
- Jitter defaults to `0.0`, so backoff is deterministic unless a caller opts in. Under a thundering herd that is the setting you would want on.
- `FixedWindowLimiter` is gone from the package, so any external importer breaks at import time. The body says so, but you may want a deprecation alias if anyone outside this repo imports it.

Branch name follows the skill's `<author>-<slug>` rule with the repo's git user, which is "Fixture Bot", hence the `fixture-` prefix. Rename it if that bothers you.

Nothing was marked ready, force-pushed, or merged. The `swd-submit` marker is removed.


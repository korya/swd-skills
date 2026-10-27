# Transcript: eval-1-fresh-rework-with-tradeoffs, with_skill, run-1

## Task prompt

First run `bash /Users/dmitri/dev/swd-skills/evals/submit/make_fixture.sh OUTPUT_DIR/fx fresh`, then work inside OUTPUT_DIR/fx/repo (branch main, with my uncommitted changes). I finished the retry and rate-limit rework for acme-notify; the load-test numbers are in docs/BENCHMARKS.md. Submit it for review. This environment has no GitHub: `origin` is the local bare repo at OUTPUT_DIR/fx/origin.git and the `gh` CLI must not be used. Where the workflow would create a PR, write the title to OUTPUT_DIR/pr-title.txt and the body to OUTPUT_DIR/pr-body.md instead. Where it would wait for CI, say that CI is unavailable here and stop.

OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-2/eval-1-fresh-rework-with-tradeoffs/with_skill/run-1/outputs

## Shell commands

1. `mkdir -p "$OUT" && bash .../make_fixture.sh "$OUT/fx" fresh` -- built the fixture: 7 modified tracked files, untracked `.env` and `scratch.py`.
2. `touch "$(git rev-parse --git-dir)/swd-submit"; git status --short --branch; git branch -a; git log --oneline -8; git log @{u}..HEAD; git remote -v; git config user.name/user.email; ls -la; cat .env scratch.py` -- on `main` level with origin, one commit in history, no unpushed commits, git user "Fixture Bot"; `.env` holds an API key, `scratch.py` is a throwaway.
3. `git diff; cat Makefile README.md docs/BENCHMARKS.md; find . -type f` -- read the full working-tree diff; Makefile offers `make lint` and `make test`.
4. `git checkout -b fixture-backoff-token-bucket; cat references/commits.md assets/writing.md; ls scripts/; python3 -I scripts/prose-lint.py --help` -- branch created; read the commit and writing rules; linter located.
5. Wrote `msg1..msg4` into `.git/` via heredoc; `python3 -I prose-lint.py --commit` on each -- msg1, msg3, msg4 clean; msg2 had one long-lead finding (22 words).
6. Rewrote msg2; lint clean; `git add notify/sender.py tests/test_sender.py && git commit -F msg1`; `git add notify/ratelimit.py notify/__init__.py tests/test_ratelimit.py && git commit -F msg2`; `git add docs/BENCHMARKS.md && git commit -F msg3`; `git add README.md && git commit -F msg4`; `git log --oneline main..HEAD; git status --short` -- four commits created; `.env` and `scratch.py` remain untracked.
7. `make lint && make test && git push -u origin fixture-backoff-token-bucket; git rev-parse HEAD origin/fixture-backoff-token-bucket` -- compileall clean, 7 tests OK, branch pushed, local HEAD equals origin.
8. `cat references/pr-description.md; head -20 references/screenshots.md; cat tests/fakes.py; ls .github` -- read the PR reference; no PR template in the repo; nothing rendered so no screenshots apply.
9. `printf ... >| pr-title.txt; cat >| pr-body.md <<EOF; wc -c pr-title.txt; python3 -I prose-lint.py pr-body.md` -- title 65 chars; body had 2 findings (24-word lead, 28-word sentence).
10. `python3 -I - pr-body.md <<EOF` (rewrote lines 11 and 64); `python3 -I prose-lint.py pr-body.md` -- 0 findings.
11. `rm -f "$(git rev-parse --git-dir)/swd-submit"`; wrote this transcript -- marker removed.

## Commit messages

```text
feat(sender): Retry with exponential backoff and honor Retry-After

Previously the sender retried three times with a fixed one-second wait and treated every
4xx as final. Now it retries up to five times with exponential backoff and honors a
Retry-After header.

Each wait is base * 2**attempt seconds plus optional jitter, capped at max_delay. The
defaults are a 0.5 s base and a 16 s cap. A Retry-After header replaces the computed wait.
429 joins the 5xx codes as retryable, so a throttled tenant waits instead of failing.

Retries now take longer. With the defaults the four waits sum to 7.5 s before jitter, where
the old sender gave up after 3 s. Callers that need a tighter bound pass a smaller
`retries` or `max_delay`.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

```text
feat(ratelimit): Replace the fixed window with a token bucket

Previously a tenant could send its whole minute's quota of 100 in the first second. Now the
limiter is a token bucket with a sustained rate of 60 per minute and a burst of 20.

A bucket refills continuously at `rate` tokens per second up to `burst`. A send takes one
token and is refused when fewer than one is left. Tenants keep independent buckets.

This is a breaking change to the public API. The class is renamed from FixedWindowLimiter
to TokenBucketLimiter, and the constructor takes `rate` and `burst` instead of `limit` and
`window`. Callers that import the old name fail at import time.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

```text
docs(benchmarks): Record the load test for backoff and token bucket

Previously the table held one column for the fixed retries and the fixed window. Now it
compares that baseline with the backoff and token bucket on the same load test.

Delivery success rises from 91.2% to 99.1%. 429 responses per 10k sends fall from 1,840 to
12. The cost is tail latency. p99 rises from 3.4 s to 9.8 s and the worst-case wait per
message from 3 s to 31 s. Three staging tenants that burst 100 sends per minute are now
throttled after 20 and drain at one per second.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

```text
docs(readme): Fix the spelling of receive

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

## PR title

```text
feat(notify): Retry with backoff and throttle with a token bucket
```

## Final message to the user

Submitted. Branch `fixture-backoff-token-bucket` is pushed to origin with four commits, `make lint` and the 7 tests pass, and the draft PR text is in `pr-title.txt` and `pr-body.md`. CI is unavailable here, so I stopped at the CI gate.

Phase 0: on `main`, 7 modified files, nothing unpushed, no PR. Two untracked files were left out on purpose: `.env` holds `NOTIFY_API_KEY`, and `scratch.py` says "delete me". Both still sit in the tree for you to delete.

Commits on `main..HEAD`:

- `feat(sender): Retry with exponential backoff and honor Retry-After`
- `feat(ratelimit): Replace the fixed window with a token bucket`
- `docs(benchmarks): Record the load test for backoff and token bucket`
- `docs(readme): Fix the spelling of receive` (unrelated to the rework, so its own commit)

Three things I noticed while writing the description, worth a look before you mark it ready:

1. `Retry-After` is not capped by `max_delay`. A gateway answering `Retry-After: 3600` parks a message for an hour. I put this in the PR body as a reviewer note rather than silently changing your code.
2. `float(retry_after)` raises `ValueError` on the HTTP-date form of the header.
3. The `Sender` docstring says Retry-After is honored "on 429 or 503", but `_delay` reads it on every retryable status. One of the two is wrong.

The PR body leads with the trade: delivery success 91.2% to 99.1% and 429s 1,840 to 12, paid for with p99 3.4 s to 9.8 s, a 31 s worst-case wait, three staging tenants now throttled, and a breaking rename of the limiter. The PR stays a draft; marking it ready needs your say-so. The `swd-submit` marker is removed.

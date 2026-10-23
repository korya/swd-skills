# Transcript: submit (old skill), eval-1-fresh-rework-with-tradeoffs, run-1

## Task prompt

> First run `bash /Users/dmitri/dev/swd-skills/evals/submit/make_fixture.sh OUTPUT_DIR/fx fresh`, then work inside OUTPUT_DIR/fx/repo (branch main, with my uncommitted changes). I finished the retry and rate-limit rework for acme-notify; the load-test numbers are in docs/BENCHMARKS.md. Submit it for review. This environment has no GitHub: `origin` is the local bare repo at OUTPUT_DIR/fx/origin.git and the `gh` CLI must not be used. Where the workflow would create a PR, write the title to OUTPUT_DIR/pr-title.txt and the body to OUTPUT_DIR/pr-body.md instead. Where it would wait for CI, say that CI is unavailable here and stop.
>
> OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/old_skill/run-1/outputs

## Shell commands (in order)

All paths below are relative to OUTPUT_DIR unless absolute. `REPO` = OUTPUT_DIR/fx/repo.

1. `bash /Users/dmitri/dev/swd-skills/evals/submit/make_fixture.sh OUTPUT_DIR/fx fresh` -- fixture created; status shows 7 modified tracked files, untracked `.env` and `scratch.py`.
2. `cd REPO && touch "$(git rev-parse --git-dir)/swd-submit" && git status && git branch -a && git log --oneline -10 && git log @{u}..HEAD --oneline && git remote -v && git config user.name; git config user.email` -- on `main`, up to date with origin, one prior commit, nothing unpushed, origin is the local bare repo, git user "Fixture Bot".
3. `ls -la && cat .env && cat scratch.py && ls .github; cat AGENTS.md CLAUDE.md CONTRIBUTING.md Makefile pyproject.toml setup.cfg; git ls-files` -- `.env` holds `NOTIFY_API_KEY`; `scratch.py` is a "delete me" poke script; only a Makefile with `test` and `lint` targets; no PR template or agent docs.
4. `git diff` -- read the full uncommitted diff: README typo, BENCHMARKS table, `FixedWindowLimiter` -> `TokenBucketLimiter`, `Sender` fixed retries -> exponential backoff with Retry-After, tests rewritten.
5. `git checkout -b fixture-backoff-token-bucket && git branch --show-current` -- branch created (no repo convention visible; `<git-user-first-name>-<slug>`).
6. `cat .../references/commits.md` -- read the commits reference.
7. `git add README.md && git commit ... && git add notify/sender.py tests/test_sender.py && git commit ... && git add notify/ratelimit.py notify/__init__.py tests/test_ratelimit.py && git commit ... && git add docs/BENCHMARKS.md && git commit ... && git log --oneline origin/main..HEAD && git status --short` -- four commits created (20aa0e2, 02a0ce2, e4cfd9a, a6e52f0); `.env` and `scratch.py` left untracked.
8. `make lint && make test` -- compileall clean; 7 tests OK.
9. `git push -u origin fixture-backoff-token-bucket && git rev-parse HEAD && git rev-parse @{u}` -- new branch pushed to the local origin; HEAD a6e52f0 matches upstream.
10. `cat .../references/pr-description.md` -- read the PR description reference.
11. `printf ... > OUTPUT_DIR/pr-title.txt; cat > OUTPUT_DIR/pr-body.md <<EOF ...` -- title (68 chars) and body written in place of `gh pr create --draft`.
12. `rm -f "$(git rev-parse --git-dir)/swd-submit"` -- marker removed; CI phase skipped as unavailable.
13. `cat > OUTPUT_DIR/../transcript.md` -- this file.

## Commit messages (full text)

### 20aa0e2

```
docs(readme): Fix "recieve" typo

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

### 02a0ce2

```
feat(sender): Replace fixed retries with exponential backoff

Previously Sender retried any 5xx three times with a fixed 1 s pause, so a 429 or a
gateway blip that outlasted 3 s became a DeliveryError, and every client hammered the
gateway on the same cadence. Now it retries 429 and 5xx up to five times with
base * 2**attempt, capped at max_delay, plus optional jitter; a Retry-After header on
the response overrides the computed delay. Non-429 4xx responses are returned as
before, never retried.

Defaults change: 5 attempts and up to 0.5 + 1 + 2 + 4 = 7.5 s of waiting, instead of
3 attempts and 3 s. Callers that depended on the old timing need to pass the old
values explicitly.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

### e4cfd9a

```
feat(ratelimit): Replace fixed window with token bucket limiter

Previously FixedWindowLimiter let a tenant spend its whole 100/min quota in the first
second of each minute and then sit idle, which showed up at the gateway as a 429 storm
once a minute. Now TokenBucketLimiter allows a sustained `rate` per second with a
`burst` of extra tokens (default 1/s with burst 20), so the same tenant drains at one
message per second after its first 20.

This is a breaking change: FixedWindowLimiter is removed from the package exports and
tenants that relied on the front-loaded minute quota are throttled sooner. The cap
also drops from 100/min to 60/min sustained.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

### a6e52f0

```
docs(benchmarks): Record backoff and token bucket load-test results

Add the new numbers next to the fixed-retry / fixed-window baseline so the trade-off is
visible in one table: delivery success 91.2% -> 99.1% and 429s per 10k sends
1,840 -> 12, paid for with p99 latency 3.4 s -> 9.8 s and worst-case wait 3 s -> 31 s.
Also note the three staging tenants that now hit the burst cap.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

## Final message to the user (verbatim)

Submitted up to the CI gate; CI is unavailable here, so the workflow stops there.

**Phase 0.** You were on `main`, in sync with `origin/main`, with seven modified tracked files and two untracked ones. `.env` contains `NOTIFY_API_KEY` and `scratch.py` calls itself "delete me", so neither was staged; both are still sitting in the tree for you to deal with. No PR existed.

**Branch and commits.** `fixture-backoff-token-bucket` off `main` (git user here is "Fixture Bot", hence the prefix), four commits so the history reads as four decisions rather than one blob:

| Commit | Subject |
|---|---|
| 20aa0e2 | docs(readme): Fix "recieve" typo |
| 02a0ce2 | feat(sender): Replace fixed retries with exponential backoff |
| e4cfd9a | feat(ratelimit): Replace fixed window with token bucket limiter |
| a6e52f0 | docs(benchmarks): Record backoff and token bucket load-test results |

**Checks.** `make lint` clean, `make test` 7/7 green before pushing. Pushed to the local origin; HEAD matches `origin/fixture-backoff-token-bucket`.

**PR (draft, written to files instead of `gh`).**
- Title: `/Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/old_skill/run-1/outputs/pr-title.txt`
- Body: `/Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/old_skill/run-1/outputs/pr-body.md`

The body leads with the before/after table from BENCHMARKS.md and puts the costs next to the wins: p99 3.4 s -> 9.8 s, worst-case wait 3 s -> 31 s, sustained cap 100/min -> 60/min, `FixedWindowLimiter` and `Sender(delay=)` removed, three staging tenants now throttled. Nothing is rendered, so no screenshots.

**Two things worth your attention before anyone reviews it:**
1. The 31 s worst case cannot come from the backoff schedule (which tops out at 7.5 s total); it must be gateway `Retry-After` values during the 429 storm. I wrote that up as intended behaviour. If it is not, the fix is a cap on `Retry-After`, and the description should change.
2. The three front-loading staging tenants have no migration path in this PR. I listed that as out of scope; you may want to decide whether that is acceptable before marking it ready.

**CI:** unavailable in this environment; stopped. The `swd-submit` marker is removed. The PR is a draft; marking it ready, or pushing anything to `main`, needs your say-so.

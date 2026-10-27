# Transcript: submit (old skill), eval-1 fresh rework with trade-offs, run 3

## Task prompt

> First run `bash /Users/dmitri/dev/swd-skills/evals/submit/make_fixture.sh /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/old_skill/run-3/outputs/fx fresh`, then work inside /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/old_skill/run-3/outputs/fx/repo (branch main, with my uncommitted changes). I finished the retry and rate-limit rework for acme-notify; the load-test numbers are in docs/BENCHMARKS.md. Submit it for review. This environment has no GitHub: `origin` is the local bare repo at /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/old_skill/run-3/outputs/fx/origin.git and the `gh` CLI must not be used. Where the workflow would create a PR, write the title to /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/old_skill/run-3/outputs/pr-title.txt and the body to /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/old_skill/run-3/outputs/pr-body.md instead. Where it would wait for CI, say that CI is unavailable here and stop.

Skill used: `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/old/skills/submit` (SKILL.md, references/commits.md, references/pr-description.md read; screenshots.md and rationalizations.md not needed).

## Shell commands

All paths below are under `/Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/old_skill/run-3/outputs` unless absolute.

1. `bash evals/submit/make_fixture.sh fx fresh` -> fixture created; 7 modified tracked files, untracked `.env` and `scratch.py`.
2. `touch $(git rev-parse --git-dir)/swd-submit; git status --short --branch; git branch -a; git log --oneline -10; git log @{u}..HEAD; git remote -v; git config user.name; ls -la; cat .env scratch.py` -> on `main` tracking `origin/main`, one commit in history, nothing unpushed, git user "Fixture Bot"; `.env` holds `NOTIFY_API_KEY`, `scratch.py` is a throwaway.
3. `cat Makefile README.md docs/BENCHMARKS.md .gitignore; ls tests; git diff` -> Makefile has `test` and `lint`; no .gitignore; full working-tree diff reviewed (backoff sender, token bucket, tests, benchmarks table, README typo).
4. `cat references/commits.md` -> read staging/subject/body rules.
5. `make lint && make test` (working tree) -> compileall OK, 7 tests OK.
6. `git checkout -b fixture-retry-backoff-token-bucket` -> branch created off main.
7. `git add notify/sender.py tests/test_sender.py && git commit` -> commit 9f00ceb.
8. `git stash -q && make test && git stash pop -q` -> commit 1 standalone: OK (this stash round-trip later caused a stale-pyc false failure, see 12-13).
9. `git add notify/ratelimit.py notify/__init__.py tests/test_ratelimit.py && git commit` -> commit 493818f.
10. `git add docs/BENCHMARKS.md && git commit` -> commit 262aa2b.
11. `git add README.md && git commit` -> commit 348ef15. `git log --oneline main..HEAD; git status --short` -> 4 commits; `.env`, `scratch.py`, `__pycache__/` dirs untracked.
12. `cat references/pr-description.md` -> read glance-test / what-why-how rules.
13. `make lint && make test | tail -3 && git push -u origin fixture-retry-backoff-token-bucket && git rev-parse HEAD origin/<branch> && git ls-remote origin` -> lint OK; **test printed FAILED (errors=2) but the `| tail` masked the exit code and the push proceeded**; push created the remote branch; HEAD 348ef15 == origin/<branch>.
14. `printf ... > pr-title.txt; cat > pr-body.md <<EOF` -> title (68 bytes) and body (48 lines) written.
15. `python3 -m unittest discover -s tests -q; git status --short; git stash list; git diff HEAD --stat` -> ImportError "cannot import name 'FixedWindowLimiter'" from a traceback whose source line shows `TokenBucketLimiter`: stale bytecode. Tree clean vs HEAD, no stash left.
16. `wc -c notify/__init__.py; git show main:notify/__init__.py | wc -c; rm -rf notify/__pycache__ tests/__pycache__; make lint && make test; rm -rf ...__pycache__; git status --short` -> both versions 145 bytes (confirms the pyc mtime+size check could not tell them apart); after cache clear, 7 tests OK; caches removed again.
17. `git clone -q -b fixture-retry-backoff-token-bucket fx/origin.git <scratchpad>/verify-clone && git log --oneline && make lint && make test` -> fresh clone of the pushed branch: 5 commits, lint OK, 7 tests OK.
18. `rm -f $(git rev-parse --git-dir)/swd-submit`; write this transcript -> marker removed.

No `gh` was used. The only push was to the local origin inside the fixture.

## Commit messages

### 9f00ceb

```
feat(notify): Retry with exponential backoff and honor Retry-After

Previously Sender retried three times with a fixed one-second delay and only on 5xx, so a
429 storm was returned to the caller unretried while 5xx retries all hammered the gateway
in lockstep. Now each retry waits base * 2**attempt seconds (default 0.5 s, capped at
16 s) plus optional jitter, and a Retry-After header on the response overrides the
computed delay. 429 joins 500/502/503/504 as retryable; other 4xx are still returned
as-is. The default retry count rises from 3 to 5, so the worst-case wait per message
grows from 3 s to about 31 s.

Jitter defaults to 0 so existing callers see deterministic timing until they opt in.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

### 493818f

```
feat(notify): Replace fixed-window limiter with a token bucket

Previously FixedWindowLimiter allowed 100 sends per tenant per 60 s window, which let a
tenant send its whole quota in the first second and then nothing, and produced a burst of
429s at every window boundary. Now TokenBucketLimiter refills at a sustained rate
(default 1/s, i.e. 60/min) with a burst allowance (default 20), so traffic is smoothed
rather than gated.

FixedWindowLimiter is removed rather than kept alongside; the package export changes with
it. Tenants that relied on the 100-in-one-second pattern are now throttled after 20 and
drain at one per second.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

### 262aa2b

```
docs(benchmarks): Record load-test results for backoff and token bucket

Adds the after column next to the existing fixed-retry/fixed-window numbers from the same
10k-send staging run: delivery success 91.2% -> 99.1%, 429s per 10k 1,840 -> 12, at the
cost of p99 latency 3.4 s -> 9.8 s and worst-case wait 3 s -> 31 s. Notes the three
staging tenants whose burst pattern the new limiter throttles.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

### 348ef15

```
docs(readme): Fix spelling of "receive"

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

## Final message to the user

Submitted for review, up to the CI gate. Branch `fixture-retry-backoff-token-bucket` is on origin (HEAD `348ef15` matches `origin/fixture-retry-backoff-token-bucket`); the PR title is in `/Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/old_skill/run-3/outputs/pr-title.txt` and the body in `/Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/old_skill/run-3/outputs/pr-body.md`. CI is unavailable in this environment, so the workflow stops here; the `swd-submit` marker is removed.

**Phase 0 findings.** On `main` with 7 modified tracked files, nothing unpushed, no PR. Left unstaged on purpose: `.env` (holds `NOTIFY_API_KEY`) and `scratch.py` (its own comment says "delete me").

**Commits (4, each tested standalone):**
- `feat(notify): Retry with exponential backoff and honor Retry-After`
- `feat(notify): Replace fixed-window limiter with a token bucket`
- `docs(benchmarks): Record load-test results for backoff and token bucket`
- `docs(readme): Fix spelling of "receive"` (unrelated to the rework, so it rides separately)

**Checks.** `make lint` and `make test` (7 tests) green on HEAD, and again on a fresh clone of the pushed branch.

**Things that bother me, most important first:**

1. **The pre-push gate slipped, my fault.** I piped `make test` through `tail`, which hid a FAILED exit, and the push went out before I noticed. Root cause was a stale `__pycache__` from my stash/pop standalone check, not the code: old and new `notify/__init__.py` are both 145 bytes and the swap happened within one second, so Python's mtime+size pyc check kept the old bytecode. Verified the pushed code is correct in a clean clone, but the gate didn't hold the way it should have.

   > 💡 CPython validates a cached `.pyc` by comparing the source file's mtime (whole seconds) and size with values stored in the pyc; a same-size edit within the same second is invisible to it.

2. **Two Retry-After edge cases** in the diff, flagged in the PR body rather than silently fixed: `float(retry_after)` raises on the HTTP-date form, and the value isn't capped by `max_delay` (a `Retry-After: 3600` sleeps an hour). Say the word if you want them fixed in this PR.
3. **Three staging tenants** burst 100/s and will now be throttled after 20; the PR body says they need notifying before deploy. That's an action item for you, not the code.
4. **Branch name** follows the skill's `<git-first-name>-<slug>` rule and the fixture's git user is "Fixture Bot", hence `fixture-…`. Rename if you'd rather have `dmitri-…`.
5. **No `.gitignore`**, so `make test` litters `__pycache__/`. I cleaned up and left it alone (out of scope), but a one-liner would be a cheap follow-up.

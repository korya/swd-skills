# Transcript: eval-2 existing-pr revalidation (old skill, run 2)

## Task prompt

First run `bash /Users/dmitri/dev/swd-skills/evals/submit/make_fixture.sh OUTPUT_DIR/fx existing-pr`, then work inside OUTPUT_DIR/fx/repo. I'm on branch korya-retry-backoff; a PR is already open for it, and its current title and body are in OUTPUT_DIR/fx/pr/title.txt and OUTPUT_DIR/fx/pr/body.md (treat those files as what the forge would show you). I've now added the token-bucket rate limiter and refreshed docs/BENCHMARKS.md; it's uncommitted. Push this up. This environment has no GitHub: `origin` is the local bare repo at OUTPUT_DIR/fx/origin.git and the `gh` CLI must not be used. If the PR title or body needs editing, write the new title to OUTPUT_DIR/pr-title.txt and the new body to OUTPUT_DIR/pr-body.md; if they do not, say so explicitly. Where the workflow would wait for CI, say that CI is unavailable here and stop.

(OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-2-existing-pr-revalidation/old_skill/run-2/outputs)

## Shell commands

All paths below are relative to OUTPUT_DIR unless absolute.

1. `mkdir -p OUTPUT_DIR && bash /Users/dmitri/dev/swd-skills/evals/submit/make_fixture.sh OUTPUT_DIR/fx existing-pr` — fixture created; status showed 5 modified files, untracked `.env` and `scratch.py`.
2. `cd fx/repo && touch "$(git rev-parse --git-dir)/swd-submit" && git branch --show-current && git status --short && git remote -v && git log --oneline @{u}..HEAD && git log --oneline master..HEAD` — marker set; branch `korya-retry-backoff`; nothing unpushed; last command failed (exit 128) because the default branch is `main`, not `master`.
3. `git branch -a -vv && git ls-remote origin && git log --oneline origin/main..HEAD && git ls-files && cat .gitignore; cat .env; cat scratch.py` — branch is 1 commit ahead of `main` and in sync with origin; no `.gitignore`; `.env` holds `NOTIFY_API_KEY`; `scratch.py` is a throwaway poke script.
4. `cat pr/title.txt && cat pr/body.md && cat repo/Makefile && git -C repo show --stat 784c5d7 && git -C repo diff` — read the live PR title/body, the Makefile (`lint`, `test` targets), the existing commit, and the full uncommitted diff.
5. `grep -rn "FixedWindow\|TokenBucket\|ratelimit" --include=*.py ...` — failed (exit 1): zsh glob expansion on `--include=*.py`.
6. `grep -rn 'FixedWindow\|TokenBucket\|ratelimit' notify tests README.md docs; git config user.name; git config user.email` — no remaining references to `FixedWindowLimiter`; git user is `Fixture Bot <fixture@example.test>`.
7. `cat .../skills/submit/references/commits.md` — read the commits reference.
8. `git add notify/ratelimit.py notify/__init__.py tests/test_ratelimit.py docs/BENCHMARKS.md && git commit -q -m "<feat(ratelimit) message>" && git add README.md && git commit -q -m "<docs(readme) message>" && git log --oneline origin/main..HEAD && git status --short` — two commits created (3d9a5dd, 9bc93b1); `.env` and `scratch.py` left untracked.
9. `make lint && make test` — compileall clean; 7 tests passed.
10. `git push && git rev-parse HEAD origin/korya-retry-backoff` — pushed 784c5d7..9bc93b1 to local origin; HEAD matches `origin/korya-retry-backoff`.
11. `cat .../skills/submit/references/pr-description.md` — read the PR description reference.
12. `printf ... > pr-title.txt; cat > pr-body.md <<EOF ...; wc -c pr-title.txt` — wrote revised title (65 chars) and body.
13. `rm -f "$(git rev-parse --git-dir)/swd-submit" && git status --short` — guard marker removed; tree clean except the two untracked files.
14. `cat > OUTPUT_DIR/../transcript.md <<EOF ...` — this file.

## Commit messages

### 3d9a5dd

```
feat(ratelimit): Replace fixed-window limiter with a token bucket

Previously FixedWindowLimiter let a tenant send its whole 100/min quota in the first
second of each minute and then nothing, which is what produced the 429 storms in the
load test (1,840 per 10k sends). Now TokenBucketLimiter allows a sustained 60/min with
a burst of 20, so load spreads across the minute: 429s drop to 12 per 10k sends and
delivery success reaches 99.1% together with the retry backoff.

Trade-off: p99 latency rises from 3.4 s to 9.8 s and the worst-case wait per message
from 3 s to 31 s, because messages that used to be rejected now queue behind the
bucket. Three staging tenants that relied on front-loading their quota are now
throttled after 20 messages. docs/BENCHMARKS.md carries the before/after table.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

### 9bc93b1

```
docs(readme): Fix "recieve" typo

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

## Final message to the user

Pushed. Two new commits on `korya-retry-backoff`, now at `9bc93b1` on the local origin, and the PR title and body both needed rewriting.

**Phase 0 findings.** Branch was one commit ahead of `main` and fully pushed; a PR is open for it. Uncommitted: the token-bucket limiter (4 files) plus an unrelated README typo fix. Untracked: `.env` (contains `NOTIFY_API_KEY`) and `scratch.py` ("delete me"). I left both untracked and did not commit them; there is no `.gitignore`, so consider adding one for `.env`.

**Commits.**
- `3d9a5dd feat(ratelimit): Replace fixed-window limiter with a token bucket`
- `9bc93b1 docs(readme): Fix "recieve" typo`

**Pre-push checks.** `make lint` clean, `make test` 7/7 passed. No formatter is configured in the repo.

**PR revalidation: stale.** The old title covers only the backoff commit, and the old body claims "the rate limiter is untouched" and "no change in behaviour for tenants", both false now; it also credits the 99.1% to backoff alone, whereas BENCHMARKS.md measures backoff plus token bucket together. New title and body are at:
- `OUTPUT_DIR/pr-title.txt`: `feat(notify): Add retry backoff and a token-bucket tenant limiter`
- `OUTPUT_DIR/pr-body.md`: adds a before/after table, names the costs (p99 3.4 s to 9.8 s, worst-case wait 3 s to 31 s, sustained cap 100/min to 60/min, three staging tenants now throttled) and explains why the old limiter was removed rather than kept.

Nothing rendered changed, so no screenshots owed.

**CI.** CI is unavailable in this environment, so I stop here; the `swd-submit` marker has been removed. One thing worth a decision before this ships: three staging tenants will start hitting the burst cap, and that is a behaviour change they should hear about.

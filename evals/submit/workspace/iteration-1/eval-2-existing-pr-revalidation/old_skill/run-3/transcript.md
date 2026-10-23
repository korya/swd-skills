# Transcript: eval-2-existing-pr-revalidation / old_skill / run-3

## Task prompt

First run `bash /Users/dmitri/dev/swd-skills/evals/submit/make_fixture.sh OUTPUT_DIR/fx existing-pr`, then work inside OUTPUT_DIR/fx/repo. I'm on branch korya-retry-backoff; a PR is already open for it, and its current title and body are in OUTPUT_DIR/fx/pr/title.txt and OUTPUT_DIR/fx/pr/body.md (treat those files as what the forge would show you). I've now added the token-bucket rate limiter and refreshed docs/BENCHMARKS.md; it's uncommitted. Push this up. This environment has no GitHub: `origin` is the local bare repo at OUTPUT_DIR/fx/origin.git and the `gh` CLI must not be used. If the PR title or body needs editing, write the new title to OUTPUT_DIR/pr-title.txt and the new body to OUTPUT_DIR/pr-body.md; if they do not, say so explicitly. Where the workflow would wait for CI, say that CI is unavailable here and stop.

(OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-2-existing-pr-revalidation/old_skill/run-3/outputs)

## Shell commands

All repo commands ran in `OUTPUT_DIR/fx/repo`.

1. `ls -R <skill>/submit; cat <skill>/submit/SKILL.md` — read the skill skeleton; references listed.
2. `mkdir -p "$OUT" && bash .../make_fixture.sh "$OUT/fx" existing-pr; ls; cat fx/pr/title.txt fx/pr/body.md` — fixture built; 5 modified files, `.env` and `scratch.py` untracked; PR title/body read.
3. `touch "$(git rev-parse --git-dir)/swd-submit"; git status --short --branch; git branch -a; git log origin/master..HEAD; ...` — marker set; on `korya-retry-backoff` tracking origin; default branch is `main` (the `origin/master` probe failed, nothing else ran after it).
4. `git log origin/main..HEAD; git log @{u}..HEAD; ls; cat Makefile README.md .env scratch.py` — one commit on the branch, nothing unpushed; Makefile has `test` and `lint`; `.env` holds an API key; `scratch.py` is a throwaway.
5. `git diff --stat && git diff` — limiter swap in 4 files plus an unrelated README typo fix.
6. `grep -rn FixedWindow ...; cat notify/sender.py tests/fakes.py; head tests/test_sender.py; git log -1 --format=%B` — no remaining code references to the old limiter; sender does not use the limiter.
7. `cat <skill>/references/commits.md` — read the commit rules.
8. `make lint; make test` — both pass (7 tests OK).
9. `git add notify/__init__.py notify/ratelimit.py tests/test_ratelimit.py docs/BENCHMARKS.md && git commit ...; git add README.md && git commit ...` — two commits created (376c7f1, 23fac06); `.env` and `scratch.py` left untracked.
10. `git push; git rev-parse HEAD origin/korya-retry-backoff; cat <skill>/references/pr-description.md` — pushed `b1021cb..23fac06` to local origin; HEAD matches origin; read the PR description rules.
11. `printf ... > pr-title.txt; cat > pr-body.md <<EOF ...; wc -c` — wrote new title and body; title measured at 73 chars.
12. `printf ... > pr-title.txt && ... && cat > ../transcript.md` — failed: zsh noclobber refused the overwrite, so the chained transcript write never ran.
13. `printf ... >| pr-title.txt; cat >| ../transcript.md` — shortened title to 69 chars; wrote this transcript.

## Commit messages

### 376c7f1

```
feat(ratelimit): Replace fixed-window limiter with a token bucket

Previously FixedWindowLimiter let a tenant spend its whole 100/min quota in the first
second of each minute and then sit idle, which is what produced the 429 storms the
retry logic was fighting. Now TokenBucketLimiter allows 60/min sustained with a burst
of 20 per tenant, so load is spread across the minute instead of front-loaded.

In the staging load test (docs/BENCHMARKS.md) 429s per 10k sends fall from 1,840 to 12
and delivery success reaches 99.1% together with the backoff. Tenants that relied on
sending 100 messages in one second are now throttled after 20 and drain at one per
second; three staging tenants hit this. FixedWindowLimiter is removed, not deprecated.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

### 23fac06

```
docs(readme): Fix "recieve" typo

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

## Final message to the user

Pushed. The PR title and body were both stale, so I rewrote them; CI is unavailable here, so the workflow stops before the CI gate.

**Phase 0.** On `korya-retry-backoff`, tracking `origin/korya-retry-backoff`, nothing unpushed; one commit on top of `main`; PR open (title/body from `fx/pr/`). Uncommitted: the token-bucket limiter across `notify/__init__.py`, `notify/ratelimit.py`, `tests/test_ratelimit.py`, `docs/BENCHMARKS.md`, plus an unrelated README typo fix. Untracked `.env` (contains `NOTIFY_API_KEY`) and `scratch.py` ("delete me") were left out and are still sitting in the tree. You may want to add `.env` and `__pycache__/` to a `.gitignore`; there is none.

**Commits** (two, since the typo fix is unrelated to the limiter):
- `376c7f1 feat(ratelimit): Replace fixed-window limiter with a token bucket`
- `23fac06 docs(readme): Fix "recieve" typo`

**Checks.** `make lint` and `make test` pass (7 tests).

**Push.** `b1021cb..23fac06` to the local origin; `HEAD` equals `origin/korya-retry-backoff`.

**PR revalidation (5b).** Stale on both counts:
- Title covered only the sender retry. New title (69 chars) in `/Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-2-existing-pr-revalidation/old_skill/run-3/outputs/pr-title.txt`: `feat(notify): Retry with backoff and throttle tenants by token bucket`.
- Body claimed "the rate limiter is untouched" and "no change in behaviour for tenants", both now false, credited the 99.1% to backoff alone, and omitted the costs. New body in `/Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-2-existing-pr-revalidation/old_skill/run-3/outputs/pr-body.md` adds the before/after table from BENCHMARKS.md and names the side effects: p99 3.4 s → 9.8 s, worst-case wait 3 s → 31 s, sustained cap 100/min → 60/min with burst 20, three staging tenants now throttled, `FixedWindowLimiter` removed from the public API. Nothing rendered changes, so no screenshots are due.

One thing worth your eye: the body says the three affected staging tenants "should be told before rollout". That is my inference from BENCHMARKS.md, not something you said; cut it if you disagree.

**CI.** Unavailable in this environment; stopping here. The `swd-submit` marker is still in `.git` since phase 6 never ran.

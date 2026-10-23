# Transcript: eval-1-fresh-rework-with-tradeoffs, with_skill, run-1

## Task prompt

First run `bash /Users/dmitri/dev/swd-skills/evals/submit/make_fixture.sh OUTPUT_DIR/fx fresh`, then work inside OUTPUT_DIR/fx/repo (branch main, with my uncommitted changes). I finished the retry and rate-limit rework for acme-notify; the load-test numbers are in docs/BENCHMARKS.md. Submit it for review. This environment has no GitHub: `origin` is the local bare repo at OUTPUT_DIR/fx/origin.git and the `gh` CLI must not be used. Where the workflow would create a PR, write the title to OUTPUT_DIR/pr-title.txt and the body to OUTPUT_DIR/pr-body.md instead. Where it would wait for CI, say that CI is unavailable here and stop.

OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/with_skill/run-1/outputs

Skill used: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/new/skills/submit (SKILL.md, assets/writing.md, references/commits.md, references/pr-description.md, references/rationalizations.md, scripts/prose-lint.py). references/screenshots.md was not read: the branch renders nothing.

## Shell commands

Paths abbreviated: OUT = /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/with_skill/run-1/outputs, S = the skill snapshot root, REPO = OUT/fx/repo.

1. `cat S/assets/writing.md; ...; cat S/skills/submit/references/*.md; ls S/scripts/` -- read the writing rules and references (first attempt tripped on an unquoted `======` echo under zsh, reran).
2. `mkdir -p OUT && bash /Users/dmitri/dev/swd-skills/evals/submit/make_fixture.sh OUT/fx fresh` -- fixture built, exit 0, 7 modified and 2 untracked files.
3. `cd REPO && touch "$(git rev-parse --git-dir)/swd-submit" && git status && git branch -a && git config user.name && git log --oneline -10 && git log @{u}..HEAD && git remote -v && find ... && git diff --stat` -- phase 0: on main, up to date with origin, user "Fixture Bot", one prior commit, no unpushed commits.
4. `git diff && cat .env scratch.py Makefile README.md docs/BENCHMARKS.md tests/fakes.py notify/*.py` -- read every change; .env holds an API key, scratch.py is a throwaway.
5. `sed -n 1,60p S/scripts/prose-lint.py; python3 -I S/scripts/prose-lint.py --help` -- learned the linter interface.
6. `git checkout -b fixture-backoff-token-bucket && cat >| MSG <<EOF ... && prose-lint.py MSG && git add notify/sender.py tests/test_sender.py && git commit -F MSG` -- 0 findings, commit 5622bf5.
7. `cat >| MSG ... && prose-lint.py MSG && git add notify/ratelimit.py notify/__init__.py tests/test_ratelimit.py && git commit -F MSG` -- 0 findings, commit 8a83d1d.
8. `cat >| MSG ... && prose-lint.py MSG && git add docs/BENCHMARKS.md && git commit -F MSG && cat >| MSG ... && prose-lint.py MSG && git add README.md && git commit -F MSG && git log main..HEAD && git status --short` -- 0 findings each, commits 23dccfc and d4d0d3c; only .env and scratch.py remain untracked.
9. `make lint && make test` at HEAD, then `git worktree add` per commit with `make -s lint && make -s test` and `git worktree remove` -- lint clean and 7 tests OK at HEAD and at each of the four commits.
10. `git push -u origin fixture-backoff-token-bucket && git rev-parse HEAD origin/fixture-backoff-token-bucket && ls .github` -- new branch pushed, local and remote heads match (d4d0d3c), no PR template.
11. `printf ... >| OUT/pr-title.txt; cat >| OUT/pr-body.md <<EOF ...; prose-lint.py OUT/pr-body.md` -- title 66 chars; body had 4 findings (1 long lead, 3 long sentences).
12. `python3 -I - OUT/pr-body.md <<EOF (split the four sentences) && prose-lint.py OUT/pr-body.md` -- 0 findings.
13. `rm -f "$(git rev-parse --git-dir)/swd-submit" && git status --short && git log main..HEAD && cat ../../pr-body.md` -- marker removed; test runs had left __pycache__ dirs.
14. `rm -rf notify/__pycache__ tests/__pycache__ && git status --short && git log --format='%B' main..HEAD` -- tree back to only .env and scratch.py untracked; dumped commit messages.
15. This command: wrote the transcript.

No `gh` calls. The only push went to OUT/fx/origin.git.

## Commit messages (newest first)

```text
docs(readme): Fix the spelling of "receive"

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

```text
docs(benchmarks): Compare the backoff rework against the fixed retry baseline

Previously the table held one column for the fixed retry and fixed window
build. Now it sets that baseline next to the backoff and token bucket build
from the same load test. The note under the table names the tenants that the
lower burst affects.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

```text
feat(ratelimit)!: Replace the fixed window limiter with a token bucket

Previously FixedWindowLimiter allowed 100 sends per tenant per minute and reset
the count at the window edge. A tenant could send its whole quota in the first
second and then starve for 59 seconds, which is what caused the 429 storms.
Now TokenBucketLimiter refills one token per second per tenant up to a burst
of 20. A tenant that sends faster than that is throttled after 20 messages and
drains at one per second.

BREAKING CHANGE: FixedWindowLimiter is removed from the package. The default
per-tenant cap drops from 100 per minute to 60 per minute sustained.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

```text
feat(sender): Retry with exponential backoff and honor Retry-After

Previously the sender retried three times with a fixed one second wait and only
on 5xx. A 429 storm went straight to DeliveryError, and every retry hit the
gateway at the same cadence that overloaded it. Now the sender retries 429 and
the transient 5xx codes with a doubling delay, capped at max_delay, plus
optional jitter. When the gateway sends a Retry-After header, that value wins
over the computed delay.

The default budget grows from 3 attempts over 2 seconds to 5 attempts over
7.5 seconds. Other 4xx responses still return to the caller without a retry.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

## PR title

```text
feat!: Retry with backoff and throttle tenants with a token bucket
```

## PR body

See /Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/with_skill/run-1/outputs/pr-body.md (passes prose-lint with 0 findings).

## Final message to the user

Submitted as far as this environment allows. Branch `fixture-backoff-token-bucket` is pushed to origin with four commits, and the draft PR title and body are written to files since there is no forge here.

**Phase 0.** You were on `main` with 7 modified files and 2 untracked ones. No unpushed commits, no PR.

**Commits** (lint and all 7 tests green at every one):
- `5622bf5 feat(sender): Retry with exponential backoff and honor Retry-After`
- `8a83d1d feat(ratelimit)!: Replace the fixed window limiter with a token bucket`
- `23dccfc docs(benchmarks): Compare the backoff rework against the fixed retry baseline`
- `d4d0d3c docs(readme): Fix the spelling of "receive"`

**Left out on purpose:**
- `.env` holds `NOTIFY_API_KEY`. Not committed. The repo has no `.gitignore`, so add one before this bites someone.
- `scratch.py` says "delete me". It is yours, I left it in the tree untouched.

**PR:** title in `/Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/with_skill/run-1/outputs/pr-title.txt`, body in `/Users/dmitri/dev/swd-skills/evals/submit/workspace/iteration-1/eval-1-fresh-rework-with-tradeoffs/with_skill/run-1/outputs/pr-body.md`. Both pass prose-lint. Nothing rendered, so no screenshots. It would open as a draft; nothing is marked ready.

**CI:** unavailable here, so I stopped at the gate. The `swd-submit` marker is removed.

**Things in the diff that bother me** (also listed in the PR body for the reviewer):
1. `Retry-After` escapes `max_delay`. The computed waits sum to 7.5 s, so the 31 s worst case in the benchmarks is almost certainly the gateway dictating the wait. Decide whether the cap should apply to it.
2. `float(retry_after)` raises `ValueError` on an HTTP-date `Retry-After`, bypassing `DeliveryError`.
3. `jitter` defaults to `0.0`. The docstring sells backoff with jitter, but nobody gets jitter unless they opt in, so retries from many workers still line up.
4. The `Sender` docstring says `Retry-After` is honoured on 429 or 503. The code honours it on every retryable status. One of them is wrong.
5. The `!` and `BREAKING CHANGE` footer on the ratelimit commit are my call: dropping `FixedWindowLimiter` from the public API and cutting the sustained cap from 100 to 60 per minute breaks importers and three staging tenants. Say so if you disagree and I will reword it.

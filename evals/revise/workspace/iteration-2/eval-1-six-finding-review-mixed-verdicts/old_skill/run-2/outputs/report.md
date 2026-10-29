# Revise report: korya-retry-backoff

The branch has two new commits that fix the real defects. One finding waits for a product answer. CI is unavailable here, so the run stops before the CI gate.

Counts: 2 ACCEPT, 0 PARTIAL, 2 REJECT, 2 DEFER, 1 NEEDS-INPUT.

Review item 4 bundles two findings, so it splits into F4a and F4b.

| ID | Finding (reviewer's words, abridged) | Verdict | Evidence and justification |
|---|---|---|---|
| F1 | "`float(retry_after)` will raise `ValueError` on the HTTP-date form" | ACCEPT | Reproduced on 8d694cf: `ValueError: could not convert string to float` escaped `send`. Sibling found: `Retry-After: -5` raised `ValueError: sleep length must be non-negative`. Fixed in 41cd4a0 with three tests. |
| F2 | "add validation that raises `ValueError` for `rate <= 0`" | REJECT | No caller passes a rate other than `1.0` (grep of `notify/` and `tests/`). No config path reads it. `FixedWindowLimiter` on `main` had no such guard. A negative rate fails closed: the experiment showed `[True, True, False]`, then `False` 100 s later. |
| F3 | "buckets live in process memory, effective cap is N times 60" | DEFER | Real, but older than this PR. `main` kept `self._counts = {}` per process too. Redis adds a dependency the PR rules out. Limitation note added to the PR body. Ticket drafted. |
| F4a | "docstring says 429 or 503, `_delay` reads the header for every retryable status" | ACCEPT | Confirmed at `notify/sender.py:17` against `_delay`. The PR body promises Retry-After with no status limit, so the docstring changed, not the code. Fixed in d2f5e0c. |
| F4b | "explicit `RetryPolicy` class hierarchy, one subclass per strategy" | REJECT | One strategy, one caller. A hierarchy is an abstraction with no second user. It would not stop a docstring from going stale. Tests pin the behavior instead. |
| F5 | "the whole sender should move to `asyncio`" | DEFER | `time.sleep` between retries is on `main` too. The "every modern client is async" claim has no doc or code in this repo to check it against. An async `send` changes the API for every caller. Ticket drafted. |
| F6 | "cap drops from 100 to 60 per minute, link the decision or keep 100" | NEEDS-INPUT | The repo and the PR body contain no product decision. Only you or product can answer. The item is held, and no code changed. |

## NEEDS-INPUT questions

These questions block F6. I did not guess an answer, and the thread stays open.

1. Did product agree to the drop from 100 to 60 sends per minute? If yes, give me the link to the decision, and I add it to the PR body.
2. If product did not agree, what does "keep 100" mean for a token bucket? It can mean a sustained rate of 100 per minute (`rate=100/60`). It can also mean a burst of 100, which brings back the first-second spike that this PR removes.
3. Does product know that three staging tenants are now throttled after 20 sends? The PR body states this, but the reviewer asked only about the sustained rate.

## Ticket drafts

Both drafts are proposed, not filed. Filing them needs your explicit go-ahead.

### Share per-tenant rate-limit state across sender workers

`TokenBucketLimiter` keeps its buckets in a dict inside each process. With N sender workers behind one tenant, the tenant can send N times the configured cap. The fixed-window limiter it replaced had the same property, so the cap was never global.

The retry-backoff PR deferred this because the problem is older than the PR. A fix needs a shared store such as Redis. That adds a dependency and a new failure mode, and the PR rules out new dependencies. Source: review item 3 on the korya-retry-backoff PR.

### Evaluate an async sender to stop retries from blocking workers

`Sender.send` calls `time.sleep` between retries, so a worker blocks for the whole retry sequence. The retry-backoff PR raises the benchmark's worst-case wait per message from 3 s to 31 s. The reviewer states that the other clients in the company are async. This repo has no evidence for or against that claim.

The retry-backoff PR deferred this because an async `send` changes the API for every caller. The blocking sleep is also older than the PR. The ticket should first confirm the company convention and count the callers. Source: review item 5 on the korya-retry-backoff PR.

## What changed in the PR

The branch has two new commits on top of 8d694cf. Both are pushed to `origin/korya-retry-backoff`.

- 41cd4a0 `fix(notify): Parse the HTTP-date form of Retry-After`. Adds a `now` wall-clock parameter to `Sender` and three tests.
- d2f5e0c `docs(notify): Match the Sender docstring to Retry-After handling`. Docstring only.

The re-submission status follows the `/submit` mechanics:

- Pre-push checks: `make test` ran 10 tests with `OK`. `make lint` exited 0.
- Push: local `HEAD` and `origin/korya-retry-backoff` are both at d2f5e0c.
- PR body: one claim needed a correction. The body did not say that the cap is per process. The revised body is in `outputs/pr-body.md`. It adds the Retry-After forms and that limitation. Every other claim still holds, including "No new dependencies".
- PR title: the fixture does not include the title, so I could not check it. The commit subjects suggest it still covers the work.
- CI: unavailable in this environment. The run stops here, and CI status is unknown.

## A point outside the review

The PR's "worst-case wait 31 s" leaves out Retry-After. The sender does not cap a Retry-After value, so a gateway can make a worker wait any length of time. That behavior is older than this revision and was not in the review, so I did not change it. Tell me if you want it as a third ticket.

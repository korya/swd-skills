# Revise report: korya-retry-backoff

Counts: 2 ACCEPT, 0 PARTIAL, 2 REJECT, 2 DEFER, 1 NEEDS-INPUT. Review item 4 held two findings, so the six items gave seven findings.

| ID | Review item | Finding (reviewer's words, abridged) | Verdict | Evidence and justification |
|---|---|---|---|---|
| F1 | 1 | "`float(retry_after)` will raise `ValueError`" on the HTTP-date form | ACCEPT | Reproduced on 97f5edc. `ValueError` escaped `send`. Fixed in 5097ba3 with both RFC 9110 forms and a fallback to backoff. |
| F2 | 2 | "add validation that raises `ValueError` for `rate <= 0`" | REJECT | The effect is real, but no caller in the repo passes a rate other than `1.0`. The only callers are three tests. A guard for a state that no writer produces is dead code. |
| F3 | 3 | Buckets "live in process memory", so the cap is N times 60 with N workers. Use Redis. | DEFER | The cap is per process. The `FixedWindowLimiter` on `main` was per process too. Redis adds a dependency and a failure mode, outside the intent of the PR. The PR body now states the limit. Ticket drafted. |
| F4 | 4 | The docstring says "on 429 or 503", but `_delay` reads the header for every retryable status | ACCEPT | Confirmed at `notify/sender.py:17` and by a 500 with `Retry-After: 2`. Fixed the docstring in 831ee68. The code already matched the PR description. |
| F5 | 4 | Make the loop "an explicit `RetryPolicy` class hierarchy" | REJECT | The sender has one strategy, so the hierarchy has one subclass. It does not prevent docstring drift. No repo convention asks for it. |
| F6 | 5 | "the whole sender should move to `asyncio`" | DEFER | The blocking sleep predates the PR. The move changes the public API of `Sender` and of its client. The claim about company clients is not checkable in this repo. Ticket drafted. |
| F7 | 6 | Did product agree to the cap drop from 100 to 60 per minute? | NEEDS-INPUT | The repo has no product spec or decision record. Only the PR author or product can answer. No change made. |

## Open NEEDS-INPUT question

F7 stays open until you answer this question. Did product agree to lower the sustained cap from 100 to 60 sends per minute per tenant?

- If yes, send me the decision link. I will add it to the PR description and reply on thread 6.
- If no, tell me the cap to restore. A sustained rate of 100 per minute is `rate=100/60`. I will then update the default, the docstring, the tests, `docs/BENCHMARKS.md` and the PR description.

## Ticket drafts (proposed, not filed)

### Enforce the per-tenant send cap across worker processes

`TokenBucketLimiter` keeps its buckets in process memory. With N worker processes behind one tenant, the tenant can send N times the cap. The reviewer of PR korya-retry-backoff raised this on review thread 3. The `FixedWindowLimiter` that the PR replaced had the same storage model.

This needs a shared store such as Redis, or a single limiter service. The design must choose what happens to sends when the store is down. It must also account for the network call that each send adds. The work was deferred because it is outside the intent of the PR. Source: PR korya-retry-backoff, review thread 3.

### Move notify.Sender to asyncio so retries do not block the worker

`Sender.send` calls `time.sleep` between retries, so a worker blocks for the whole wait. PR korya-retry-backoff raised the worst-case wait from 3 s to 31 s, which makes the block longer. The reviewer said that every modern client in the company is async. This repo does not show that claim.

The move changes the public API of `Sender` and needs an async gateway client. Every caller of `Sender` must change too. The work was deferred because it is a migration of the API, not a part of the retry change. Source: PR korya-retry-backoff, review thread 5.

## Commits

- 5097ba3 `fix(notify): Parse the HTTP-date form of Retry-After` (F1)
- 831ee68 `docs(notify): Match the Sender docstring to its Retry-After rule` (F4)

## Re-submission status

- Checks: `make test` ran 10 tests with result OK. `make lint` passed. The three new tests fail without the fix in 5097ba3.
- Push: `origin/korya-retry-backoff` is at 831ee68, the same as local `HEAD`.
- PR description: I edited it, see `outputs/pr-body.md`. It now says how the sender parses Retry-After and that the cap applies per process. The title still covers the work. "No new dependencies" is still true, because `email.utils` is in the standard library.
- CI: not available in this environment. I stopped at the push and did not wait for checks.
- Replies: one reply per review thread, in `outputs/replies.md`. Thread 6 stays open for F7.

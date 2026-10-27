# Revise report for korya-retry-backoff

The review produced seven findings and the verdicts are 2 ACCEPT, 0 PARTIAL, 3 REJECT, 1 DEFER, 1 NEEDS-INPUT. Review item 4 was two findings, so it is split into F4a and F4b. Two fix commits are pushed to origin. One question is open and blocks a verdict on the cap change. CI is unavailable in this environment.

## Decision table

| ID | Finding (reviewer's words, abridged) | Verdict | Evidence and justification |
|---|---|---|---|
| F1 | "`float(retry_after)` will raise `ValueError` on the HTTP-date form" | ACCEPT | Reproduced: `ValueError` escaped `send` at `notify/sender.py:45`. Fixed in 0ef5ddf with the fallback option and a regression test. |
| F2 | "add validation that raises `ValueError` for `rate <= 0`" | REJECT | Behavior confirmed by experiment, but no caller produces it. All constructors pass the default or `rate=1.0` (`tests/test_ratelimit.py:10,15,23`). The rate is a code constant, not a trust-boundary input. Speculative guard. |
| F3 | "buckets live in process memory, N workers means N times the cap" | DEFER | True at `notify/ratelimit.py:16`. Pre-existing: `FixedWindowLimiter._counts` on `main` had the same scope. Redis is a new dependency outside the PR's intent. Limitation note added to the PR body, ticket drafted. |
| F4a | "docstring says 429 or 503, but `_delay` reads the header for every retryable status" | ACCEPT | Confirmed: `sender.py:17` versus `sender.py:39,43`. Fixed the docstring in c8dfd9b. The code is right to follow the hint on any retryable status. |
| F4b | "should become an explicit `RetryPolicy` class hierarchy" | REJECT | One strategy, one caller. An abstraction for one subclass is oversized, and the drift was doc versus code, which a hierarchy does not prevent. |
| F5 | "the whole sender should move to `asyncio`" | REJECT | Outside the stated intent. No async code anywhere in the repo. The blocking sleep predates the branch. The claim about company-wide async clients is not checkable here. |
| F6 | "cap drops from 100 to 60, did product agree?" | NEEDS-INPUT | No record of the decision in `README.md`, `docs/BENCHMARKS.md`, or the PR body. Only the user knows. Held. |

## NEEDS-INPUT

F6 needs an answer before it can get a verdict. Did product agree to the sustained cap of 60 per minute with a burst of 20? If yes, please give the link so it can go in the PR body. If not, which value should the branch carry? Keeping 100 per minute means `rate=100/60`. The branch stays at 60 until then.

## Ticket draft (proposed, not filed)

Title: Share the per-tenant token bucket across workers

`TokenBucketLimiter` keeps its buckets in a per-process dict at `notify/ratelimit.py:16`. With N worker processes serving one tenant, each worker grants the full 60 per minute, so the tenant can reach N times the cap. The fixed window it replaced had the same per-process scope.

Deferred from PR korya-retry-backoff because a shared store such as Redis adds a dependency and a new failure mode. The PR's intent was the retry and limiter algorithm. The first step is to confirm how many workers run per deployment. Source: PR korya-retry-backoff, review thread 3.

## What changed in the PR

| Commit | Change |
|---|---|
| c8dfd9b | `docs(notify): Say Retry-After applies to every retryable status` |
| 0ef5ddf | `fix(notify): Fall back to backoff when Retry-After is not a number`, with a regression test |

The PR body is revised in `pr-body.md`. It now says the header is honored when numeric, adds a Known limitations section for the per-process limiter, and records the open cap question. The title still covers all the work on the branch.

## Re-submission status

- Pre-push checks: `make test` passed with 8 tests, `make lint` passed.
- Push: `korya-retry-backoff` is at 0ef5ddf on origin, matching local HEAD.
- PR revalidation: title unchanged, body edited as described above.
- CI: unavailable in this environment. The workflow stops here instead of waiting on checks.
- Nothing was marked ready, force-pushed, or filed as a ticket.

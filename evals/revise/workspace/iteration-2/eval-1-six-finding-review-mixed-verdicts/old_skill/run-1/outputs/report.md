# Revise report: korya-retry-backoff

The review had six items. I split item 4 into two findings, so the table has seven. Two fixes are on the branch and pushed to `origin`. One item waits for your answer.

Counts: 2 ACCEPT, 0 PARTIAL, 2 REJECT, 2 DEFER, 1 NEEDS-INPUT.

| ID | Finding (reviewer's words, abridged) | Verdict | Evidence and justification |
|---|---|---|---|
| F1 | "`float(retry_after)` will raise `ValueError` [on] the HTTP-date form" | ACCEPT | Reproduced on 8d694cf. `-1` and `nan` also escaped `send` as `ValueError`. Fixed in 99634c3 with three new tests. |
| F2 | "add validation that raises `ValueError` for `rate <= 0`" | REJECT | The behavior claim is true. No caller passes a rate except the tests, which pass `1.0`. The rate does not cross a trust boundary. The old limiter had no such guard either. |
| F3 | "buckets live in process memory ... needs a shared store (Redis)" | DEFER | True at `notify/ratelimit.py:16`. The old limiter on `main` was per process too. Redis is a new dependency and outside the PR intent. Limitation note added to the PR body. Ticket drafted. |
| F4 | "docstring says ... '429 or 503', but `_delay` reads the header for every retryable status" | ACCEPT | Confirmed. A 500 with `Retry-After: 9` slept 9.0 s. Fixed the docstring to match the code in 5b2486f. The PR body sets no status limit. |
| F5 | "should become an explicit `RetryPolicy` class hierarchy" | REJECT | One caller and one strategy. A hierarchy does not stop docstring drift. The simplest fix for F4 is the docstring edit. |
| F6 | "the whole sender should move to `asyncio`" | DEFER | The blocking sleep exists on `main` too. The claim about company clients is not checkable here. Nothing in the repo uses `async`. Ticket drafted. |
| F7 | "cap drops from 100 to 60 per minute ... link the decision; if not, keep 100" | NEEDS-INPUT | The PR body and `docs/BENCHMARKS.md` state the drop. Nothing links a product decision. Held with no code change. |

## Open question (NEEDS-INPUT)

F7 needs your answer before it gets a verdict:

1. Did product approve the drop of the sustained per-tenant cap from 100/min to 60/min with a burst of 20?
2. If yes, which decision, ticket, or thread should the PR description link?
3. If no, should the token bucket stay with `rate=100/60` per second, or should the PR keep the fixed window?

Nobody was available during this run, so F7 stays unresolved.

## Ticket drafts (proposed, not filed)

### Enforce the per-tenant send cap across workers

The per-tenant limiter keeps its buckets in memory at `notify/ratelimit.py:16`. With N workers behind one tenant, the tenant can send N times the cap. The fixed-window limiter before it had the same property. The reviewer of korya-retry-backoff raised this in review item 3.

This PR deferred it because a shared store such as Redis adds a dependency and a deployment change. First find out how many workers serve one tenant in production. Then choose between a shared store and a cap divided by the worker count. Source: PR korya-retry-backoff, review thread 3.

### Make the notify sender async

`Sender.send` blocks the worker with `time.sleep` between retries. The old sender did the same. After the backoff change, the description of korya-retry-backoff gives a worst-case wait per message of 31 s. The reviewer raised this in review item 5 and said that the other clients in the company are async. This repo cannot confirm that claim.

This PR deferred it because an async `Sender` changes the public API for every caller. That migration needs its own plan for callers and tests. Source: PR korya-retry-backoff, review thread 5.

## What changed in the PR

- 99634c3 `fix(notify): Parse the HTTP-date form of Retry-After`. Adds `_retry_after`, a `now` clock argument on `Sender`, and three tests.
- 5b2486f `docs(notify): Say that Retry-After applies to every retryable status`. Changes only the docstring.

## Re-submission status

- `make lint` passed. `make test` ran 10 tests with the result `OK`.
- The three new tests failed against the sender of 8d694cf, with 2 failures and 3 errors. They pass on 5b2486f.
- `git push origin korya-retry-backoff` moved the branch from 8d694cf to 5b2486f. Local `HEAD` matches `origin/korya-retry-backoff`.
- The PR body needed edits, written to `outputs/pr-body.md`. It now describes the Retry-After forms and has a "Known limitations" section for F3 and F6. The title still covers the work.
- CI is not available here, so this run stops before the CI gate.
- Per-thread replies are in `outputs/replies.md`. There is no forge here, so nothing was posted.

## One more thing for you

The sender does not cap a Retry-After value at `max_delay`. A gateway that sends `Retry-After: 3600` makes the worker sleep for an hour. This was true on 8d694cf, and the HTTP-date support keeps that behavior. No reviewer raised it, so this run did not change it. Tell me if you want it as a finding for this PR.

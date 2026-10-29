# Revise report: korya-retry-backoff

The review held seven findings in six items. Two fixes are pushed, and one finding waits for your answer. The local tests pass with 12 of 12. CI is unavailable here.

Counts: 2 ACCEPT, 0 PARTIAL, 2 REJECT, 2 DEFER, 1 NEEDS-INPUT.

| ID | Finding (reviewer's words, abridged) | Verdict | Evidence and justification |
|---|---|---|---|
| F1 | "`float(retry_after)` will raise `ValueError` when the gateway sends the HTTP-date form" | ACCEPT | Reproduced on `b30430d`: `ValueError could not convert string to float` escaped `send`. A negative value also raised `ValueError` in `time.sleep`. The header comes from the gateway, which is a trust boundary. Fixed in 59e3487. |
| F2 | "add validation that raises `ValueError` for `rate <= 0`" | REJECT | In this repo, only the three tests construct the limiter, each with `rate=1.0`. The rate is not tenant input. An experiment with `rate=-1.0` failed closed: three sends, then refusal, also after one hour. The guard covers a state that nothing produces. |
| F3 | "buckets live in process memory ... needs a shared store (Redis)" | DEFER | Confirmed at `notify/ratelimit.py:16`. The fixed window on `main` kept `_counts` per process too, so the gap is older than this PR. Redis breaks the "No new dependencies" claim of the PR. A limitation note is in the PR body, and a ticket is drafted. |
| F4a | "docstring says Retry-After is honored on 429 or 503, but `_delay` reads it for every retryable status" | ACCEPT | Confirmed at the docstring and in `_delay`. The PR body names no status limit, so the docstring was the outlier. Fixed in 66fb531 with a test for a 500. |
| F4b | "should become an explicit `RetryPolicy` class hierarchy" | REJECT | The sender has one strategy and one caller of it. A hierarchy with one subclass is an abstraction for one caller. A test catches docstring drift, and 66fb531 adds one. |
| F5 | "the whole sender should move to `asyncio`" | DEFER | The blocking is real. `time.sleep` is the default sleep, and the worst-case wait rises from 3 s to 31 s per `docs/BENCHMARKS.md`. The sender on `main` also slept synchronously. A port makes `send` a coroutine and breaks synchronous callers. The repo has no async code to show the claimed convention. A ticket is drafted. |
| F6 | "the sustained cap drops from 100 to 60 per minute ... link the decision; if not, keep 100" | NEEDS-INPUT | No decision record in the repo. `docs/BENCHMARKS.md` records the new cap and its effect, not its approval. Only you or product can answer. The code is unchanged. |

## NEEDS-INPUT

F6 blocks a verdict. Did product agree to the drop from 100 to 60 sends per minute per tenant?

- If yes, send me the link to the decision. I add it to the PR body and post the F6 reply.
- If no, the reviewer asks to keep 100. One way is `rate=100/60` with `burst=20`, but that changes the measured numbers in the PR body. Tell me which cap and burst you want.

## Ticket drafts for DEFER

These tickets are proposed, not filed. Each needs your approval before anyone files it.

### Share token-bucket state across sender workers

Each sender process keeps its own token buckets in memory, in `notify/ratelimit.py`. With N workers behind one tenant, the effective cap is N times 60 per minute. The fixed window that this PR replaced had the same gap. The reviewer proposes a shared store, such as Redis.

The PR deferred it because a shared store adds a dependency and a failure mode. The PR states "No new dependencies". First step: find out how many sender workers serve one tenant in production. From the review of korya-retry-backoff, item 3.

### Port the notify sender to asyncio

`Sender.send` blocks its worker with `time.sleep` between retries. After korya-retry-backoff, the worst-case wait per message is 31 s, up from 3 s, per `docs/BENCHMARKS.md`. The reviewer says that the company uses async clients, and the claim needs a source.

The PR deferred it because the port changes `send` into a coroutine and breaks every synchronous caller. That is a public API change outside a retry and throttle PR. From the review of korya-retry-backoff, item 5.

## Commits

These two commits are pushed to `origin/korya-retry-backoff`, on top of `b30430d`:

- `66fb531 docs(notify): Say that Retry-After applies to every retryable status` (F4a)
- `59e3487 fix(notify): Parse the HTTP-date form of Retry-After` (F1)

The F1 commit adds a `now` parameter to `Sender`, with `time.time` as the default, so the tests can control the wall clock. The parameter follows the injected `sleep` and `rand` parameters.

## Re-submission

- Pre-push checks passed: `make lint` was clean, and `make test` ran 12 tests with no failures. The five new F1 test cases failed on the old sender, with 3 failures and 4 errors.
- The push succeeded. Local `HEAD` matches `origin/korya-retry-backoff` at 59e3487.
- The PR body needed two edits, in `outputs/pr-body.md`. It now names both Retry-After forms, and it states that the token buckets are per process (F3). Its other claims still hold. Python's standard library parses the date, so "No new dependencies" is still true.
- I did not see the PR title, so I could not check it.
- CI is unavailable here, so I stopped before the CI gate. Nothing was marked ready or force-pushed.

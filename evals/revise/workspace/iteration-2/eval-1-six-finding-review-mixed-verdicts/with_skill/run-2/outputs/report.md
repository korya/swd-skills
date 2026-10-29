# Revise report: korya-retry-backoff

Two findings are fixed and pushed, and one waits for your answer on the 60-per-minute cap. The review has six items. Item 4 holds two findings, so the table has seven.

Counts: 2 ACCEPT, 0 PARTIAL, 2 REJECT, 2 DEFER, 1 NEEDS-INPUT.

| ID | Finding (reviewer's words, abridged) | Verdict | Evidence and justification |
|---|---|---|---|
| F1 | "`float(retry_after)` will raise `ValueError` when the gateway sends the HTTP-date form" | ACCEPT | Reproduced: `ValueError` escaped `send`. A negative value made `time.sleep` raise. The gateway is a trust boundary. Fixed in 40eb91a with a test that fails on the old code. |
| F2 | "add validation that raises `ValueError` for `rate <= 0`" | REJECT | The drain is real for `rate=-1.0`. No caller produces it: the repo passes only `rate=1.0`, and nothing reads the rate from config or input. |
| F3 | "buckets live in process memory ... N times 60 per minute" | DEFER | True, and present on the base branch: `FixedWindowLimiter` kept `_counts = {}` per instance. A shared store is a separate design. Limitation note added to the PR body. Ticket drafted. |
| F4 | "docstring says Retry-After is honored 'on 429 or 503', but `_delay` reads the header for every retryable status" | ACCEPT | Reproduced: `Retry-After: 3` on a 500, a 502, or a 504 waits 3.0 s. The PR body states no status filter, so the docstring changed to match the code. Fixed in b196763. |
| F5 | "should become an explicit `RetryPolicy` class hierarchy with one subclass per strategy" | REJECT | The sender has one strategy. A hierarchy with one subclass does not prevent a stale docstring. A test pins the behavior. |
| F6 | "the whole sender should move to `asyncio`" | DEFER | `time.sleep` blocks, and the base branch also calls it. The move changes the `Sender` API for every caller. The claim that every company client is async has no evidence in the repo. Ticket drafted. |
| F7 | "cap drops from 100 to 60 per minute ... link the decision; if not, keep 100" | NEEDS-INPUT | The repo has no record of a product decision. Only you know. Held, no change. |

## Open question (NEEDS-INPUT)

- **F7.** Did product agree to drop the sustained cap from 100 to 60 per minute? If yes, give me the link to the decision and I add it to the PR body. If no, I change the default `rate` back to 100 per minute and update the benchmark row.

## Ticket drafts (proposed, not filed)

### Share token-bucket state across sender workers

`TokenBucketLimiter` keeps its buckets in process memory, in `notify/ratelimit.py`. When N workers serve one tenant, the tenant can send up to N times the cap. The old `FixedWindowLimiter` had the same limit, so the problem predates the token bucket.

The fix needs a shared store, such as Redis. It also needs a decision on the cost of one network call per send. It was deferred because PR korya-retry-backoff changes the algorithm, not the storage. Source: review thread 3 on PR korya-retry-backoff.

### Move the notify sender to asyncio

`Sender.send` calls a blocking `sleep` between retries. After PR korya-retry-backoff, the worst-case wait per message is 31 s, up from 3 s. The reviewer says every modern client in the company is async. The repo does not show it.

An async sender changes the public API for every caller. It needs its own PR and a migration plan for callers. It was deferred as outside the intent of the retry PR. Source: review thread 5 on PR korya-retry-backoff.

## Commits

- b196763 `docs(notify): Match the Retry-After docstring to the sender` (F4)
- 40eb91a `fix(notify): Keep the backoff when Retry-After is not delay-seconds` (F1)

## Re-submission

- Checks: `make test` passed with 8 tests, and `make lint` passed. Both ran before the push.
- Push: `origin/korya-retry-backoff` is at 40eb91a, the same as local `HEAD`.
- PR body: two claims changed, and the new text is in `outputs/pr-body.md`. The Retry-After sentence now names the delay-seconds form. A new paragraph says that the cap holds per process. "No new dependencies" and the benchmark numbers are still true.
- PR title: not available in this environment, so I could not check it. The old commit subject "Retry with backoff and throttle tenants with a token bucket" still covers the branch.
- CI: unavailable here, so the run stops at this step.

## Noticed, not changed

- A large delay-seconds value, such as `Retry-After: 3600`, makes the sender sleep for an hour. `max_delay` does not cap it. Nobody raised this, so I did not change it. Tell me if you want a cap.

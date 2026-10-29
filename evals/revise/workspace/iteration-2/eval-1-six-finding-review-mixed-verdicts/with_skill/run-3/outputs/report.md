# Revision report: korya-retry-backoff

Counts: `1 ACCEPT, 1 PARTIAL, 1 REJECT, 2 DEFER, 1 NEEDS-INPUT`.

Two commits fix F1 and F4 on the branch, and the branch is pushed to `origin`. All 12 tests and the lint pass. F6 waits for your answer. CI is not available here, so the CI gate did not run.

## Decision table

| ID | Finding (reviewer's words, abridged) | Verdict | Evidence and justification |
|---|---|---|---|
| F1 | "`float(retry_after)` will raise `ValueError` when the gateway sends the HTTP-date form" | ACCEPT | Reproduced. An HTTP date and `soon` raised `ValueError` out of `send()`. Siblings found: `-5` and `nan` parsed, then `time.sleep()` raised `ValueError`. Fixed in d43400c. The sender now parses seconds or an HTTP date and falls back to backoff. |
| F2 | "add validation that raises `ValueError` for `rate <= 0`" | REJECT | No caller produces the state. The only constructors are three tests with `rate=1.0`, and the default is `1.0`. Not a trust boundary. The failure is loud: `rate=-1.0` allows one send and then blocks for good. No constructor in the package checks its arguments. |
| F3 | "buckets live in process memory ... needs a shared store (Redis)" | DEFER | Real, but not new. `FixedWindowLimiter` at 283a810 also kept counts in a process-local dict. Redis adds a dependency against "No new dependencies". A limitation note is added to the PR body. Ticket drafted. |
| F4 | "docstring says Retry-After is honored 'on 429 or 503' ... should become an explicit `RetryPolicy` class hierarchy" | PARTIAL | Drift confirmed at `notify/sender.py:17` against `_delay`. The PR body and commit say "honors a Retry-After header" with no status limit. Fixed the docstring and pinned it with a test in 11abb13. Declined the hierarchy: one strategy exists, so it is an abstraction with one user. |
| F5 | "the whole sender should move to `asyncio`" | DEFER | Real cost, other PR. `time.sleep` is in the sender at 283a810. This PR raises the worst-case wait from 3 s to 31 s. The rewrite changes the public `send()` API. No async code or convention exists in this repo to check the "every modern client" claim. Ticket drafted. |
| F6 | "cap drops from 100 to 60 per minute ... link the decision; if not, keep 100" | NEEDS-INPUT | No decision found in the PR body, the commit message, `README.md`, or `docs/BENCHMARKS.md`. Only you know whether product agreed. Cap left unchanged. |

## Open question (NEEDS-INPUT)

F6 is blocked on one question:

- Did product agree to drop the sustained cap from 100 to 60 per minute? If yes, send me the link to the decision and I will add it to the PR body. If no, should the bucket keep 100 per minute (`rate=100/60`) with the burst of 20?

The reply on thread 6 tells the reviewer that the question is open.

## Ticket drafts (proposed, not filed)

Filing either ticket needs your explicit say-so.

### Share per-tenant rate-limit state across sender workers

`TokenBucketLimiter` keeps its buckets in a dict in process memory. With N workers behind one tenant, the effective cap is N times 60 per minute, not 60. The reviewer raised this on the korya-retry-backoff PR, review item 3. The old `FixedWindowLimiter` had the same limit, so the problem predates that PR.

The PR deferred the fix because a shared store such as Redis adds the first runtime dependency to the package. The PR changed only the limiter algorithm. Before work starts, confirm how many sender workers serve one tenant in production. The answer sets how far the real cap is from the stated cap.

### Move notify.Sender to asyncio

`Sender.send()` blocks its worker with `time.sleep` between retries. The korya-retry-backoff PR raised the worst-case wait per message from 3 s to 31 s in the staging load test. The reviewer raised this on that PR, review item 5, and said that every modern client in the company is async.

The PR deferred the rewrite because it changes the public `send()` API and every caller. The claim about other clients could not be checked from this repo. Before work starts, list the callers of `Sender` and confirm which of them run in an event loop.

## Commits

| Commit | Subject | Finding |
|---|---|---|
| 11abb13 | docs(notify): Say that Retry-After applies to every retryable status | F4 |
| d43400c | fix(notify): Parse both Retry-After forms instead of crashing | F1 |

The four new F1 tests failed against the old `sender.py`, with 3 failures and 4 errors across their subtests. All 12 tests pass on d43400c.

## Re-submission status

- **Checks.** `make test` ran 12 tests with result OK. `make lint` passed.
- **Push.** `b30430d..d43400c` pushed to `origin/korya-retry-backoff`. Local `HEAD` matches the remote.
- **PR body.** Revised in `outputs/pr-body.md`. It adds a paragraph on the two Retry-After forms and a known-limitations note for F3. "No new dependencies" is still true because the fix uses only the standard library. The PR title is not in the fixture, so I could not check it.
- **CI.** Not available in this environment. I stopped at that gate.
- **Replies.** One reply per thread is in `outputs/replies.md`. All replies and this report pass `prose-lint.py`.

## A risk outside the review

A Retry-After value is not capped by `max_delay`. This was true before this run, for the seconds form. A gateway that sends `Retry-After: 3600` stalls the worker for an hour. Now an HTTP date far in the future does the same.

The reviewer did not raise it, so I did not change it. The "31 s" in the PR body is a load-test measurement, not a bound. Do you want a cap on the override?

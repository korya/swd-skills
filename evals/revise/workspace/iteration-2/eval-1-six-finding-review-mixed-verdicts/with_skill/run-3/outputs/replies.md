# Replies on the review threads

## Thread 1: `notify/sender.py`, `_delay`, HTTP-date Retry-After (F1, ACCEPT)

Confirmed and fixed in d43400c. An HTTP date in `Retry-After` raised `ValueError: could not convert string to float` out of `send()`.

The same crash had two siblings. A value of `-5` or `nan` parsed, but then `time.sleep()` raised `ValueError`. Now `_retry_after()` reads a number of seconds or an HTTP date. It ignores any other value, and any negative or non-finite number, and uses the computed backoff. A date in the past retries at once.

The sender takes a new `now` argument for the wall clock, in the same way as `sleep` and `rand`. New tests cover the date form, a past date, four unusable values, and the `DeliveryError` path.

## Thread 2: `notify/ratelimit.py`, guard for `rate <= 0` (F2, REJECT)

I do not plan to add this guard, because no caller produces a rate at or below zero. The only constructors of `TokenBucketLimiter` are the three tests, and each passes `rate=1.0`. The default is also `1.0`. The rate comes from code that we write, not from a request or a config file, so it is not a trust boundary.

The failure is also loud, not silent. I ran `rate=-1.0` with `burst=3` on a fake clock. The first call returned `True` and every later call returned `False`, also after 1,000 seconds. A tenant that is blocked from its second message shows up in the first test that anyone runs.

The package also has no convention of argument checks in constructors. `Sender` does not check `retries`, `base`, or `max_delay` either. If a config path for the rate appears later, that path is the place for validation.

## Thread 3: `notify/ratelimit.py`, in-process buckets with N workers (F3, DEFER)

The observation is correct, but the limit is not new in this PR. The removed `FixedWindowLimiter` also kept its counts in a process-local dict (`self._counts` at 283a810). With N workers, the old cap was also N times 100 per minute. This PR changes the algorithm, not where the state lives.

A shared store such as Redis adds the first runtime dependency to the package. The PR says "No new dependencies". I added a known-limitations note to the PR description, which says that the cap applies per process. I proposed a ticket with the title "Share per-tenant rate-limit state across sender workers". It is not filed yet.

## Thread 4: `notify/sender.py`, docstring drift and a `RetryPolicy` hierarchy (F4, PARTIAL)

The drift is real, and I fixed it in 11abb13 with a docstring change and a test. I did not add the class hierarchy.

The code reads `Retry-After` on every status in `RETRYABLE`. The PR description and the commit message say "honors a Retry-After header" with no status limit. Thus the docstring was the outlier, not the code. Now the docstring says "on any retryable status". A new test sends `Retry-After: 3` on a 500 and checks the 3-second wait.

The hierarchy is larger than the problem. The retry loop has one strategy, exponential backoff with an optional server override. One subclass per strategy would give one class with no second user. A test catches this drift. A class layout does not, because a docstring can drift from a subclass too.

## Thread 5: move the sender to `asyncio` (F5, DEFER)

The concern is real, but an async rewrite is a different PR from this one. The synchronous `time.sleep` was in the sender before this PR, at 283a810. This PR does make each block longer. The PR's load test shows a worst-case wait per message of 31 s, up from 3 s.

An async sender changes the public `send()` API and every caller of it. This PR is about the retry schedule and the limiter. I also cannot find an async client or an async convention in this repo, so I cannot check the claim about other clients here. I proposed a ticket with the title "Move notify.Sender to asyncio". It is not filed yet.

## Thread 6: sustained cap drops from 100 to 60 per minute (F6, waiting for an answer)

You are right that the diff and the docs do not link a product decision. I checked the PR description, the commit message, `README.md`, and `docs/BENCHMARKS.md`. None of them names one. I asked the PR author whether product agreed to 60 per minute. I did not change the cap until that answer arrives. If product did not agree, one option is `rate=100/60`, which keeps the token bucket and the burst of 20.

# Replies on the review threads

## Thread 1: `_delay` and the HTTP-date form of Retry-After (F1, ACCEPT)

Fixed in 99634c3. I reproduced the crash on 8d694cf with a 503 that carried `Retry-After: Wed, 21 Oct 2026 07:28:00 GMT`. Here is the output of `send`:

```text
ValueError could not convert string to float: 'Wed, 21 Oct 2026 07:28:00 GMT'
```

The same run showed two more values that escape `send` as `ValueError`. Both come from the same unchecked parse:

- `-1` printed `ValueError sleep length must be non-negative`.
- `nan` printed `ValueError Invalid value NaN (not a number)`.

Now `_retry_after` accepts delta-seconds or any of the three HTTP-date formats of RFC 9110. A date in the past means retry at once. Any other value falls back to the computed backoff, as you proposed. Three new tests cover the date form, a past date, and the unusable values. They fail on 8d694cf and pass on 99634c3.

## Thread 2: no guard for `rate <= 0` in `TokenBucketLimiter.__init__` (F2, REJECT)

I am not adding this guard, because no caller can pass a bad rate today. Your claim about the behavior is correct. With `rate=-1.0`, a bucket at -9.0 tokens still refuses after 10 seconds. But a guard only earns its place where some caller produces the bad value.

- No code in the package constructs `TokenBucketLimiter` except the tests. All of them pass `rate=1.0`.
- The rate is a constructor argument from our own code, not input from a tenant or the gateway. It does not cross a trust boundary.
- `FixedWindowLimiter` on `main` had no validation of `limit` or `window` either. The PR keeps that convention.

If a later change reads the rate from configuration, the guard belongs at that read. I am happy to add it there.

## Thread 3: the buckets live in process memory (F3, DEFER)

You are right that the cap is per process. `TokenBucketLimiter` keeps `self._buckets = {}` at `notify/ratelimit.py:16`. N workers give a tenant N times the cap. This PR did not introduce that. `FixedWindowLimiter` on `main` kept `self._counts = {}` in the same way.

A shared store such as Redis is a new dependency, a new failure mode, and a deployment change. That is a separate decision from the retry and bucket logic in this PR. I added a limitation note to the PR description that says the cap is per process. I proposed a ticket, "Enforce the per-tenant send cap across workers". I did not file it yet.

## Thread 4: docstring drift and a `RetryPolicy` hierarchy (F4 ACCEPT, F5 REJECT)

I split this comment into two parts, because they get different answers.

**The drift (F4, ACCEPT).** Fixed in 5b2486f. The docstring said "on 429 or 503". `_delay` reads the header for every status in `RETRYABLE`. A run on 8d694cf with a 500 and `Retry-After: 9` slept 9.0 seconds.

I changed the docstring to match the code, not the code to match the docstring. The PR description says the sender "honors a Retry-After header" with no status limit. A server that sends Retry-After on a 500 still states when to come back. Honoring it costs nothing.

**The `RetryPolicy` hierarchy (F5, REJECT).** The retry logic has one caller and one strategy. A class hierarchy with one subclass per strategy adds an abstraction for strategies that do not exist. The drift was a stale sentence in a docstring, and a class hierarchy does not stop a docstring from going stale. If a second strategy arrives, that change is the right place to extract a policy.

## Thread 5: move the sender to `asyncio` (F6, DEFER)

The blocking sleep is real, but this PR did not introduce it. On `main`, `send` already called `self.sleep(self.delay)` in its retry loop, with `sleep=time.sleep` as the default. A move to `asyncio` changes the public API of `Sender` for every caller. That is a separate migration, not a fix to the retry logic.

I could not check the claim that every modern client in the company is async. Nothing in this repo uses `async`. The PR does make the blocking longer: the description gives a worst-case wait per message of 3 s before and 31 s after. So I proposed a ticket, "Make the notify sender async". I did not file it yet.

## Thread 6: the sustained cap drops from 100 to 60 per minute (F7, NEEDS-INPUT)

I am holding this item and I made no code change. Your reading is correct. The PR description and `docs/BENCHMARKS.md` both state the drop from 100/min to 60/min sustained with a burst of 20. Neither one links a product decision, and nothing in the repo records one.

Only the PR owner or product can answer this. I asked them whether product approved the drop and which decision to link. I will update this thread with their answer.

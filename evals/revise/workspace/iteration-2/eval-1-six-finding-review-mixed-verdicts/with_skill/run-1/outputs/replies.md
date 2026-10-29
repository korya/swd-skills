# Replies on the review threads

One reply per review item. Item 4 holds two findings, so its thread gets two paragraphs.

## Item 1, `_delay` and the HTTP-date form (F1, ACCEPT)

Confirmed, and fixed in 59e3487. On the old code, an HTTP-date value made `send` raise this error instead of `DeliveryError`:

```text
ValueError could not convert string to float: 'Wed, 21 Oct 2026 07:28:00 GMT'
```

A negative value failed in the same way inside `time.sleep`, with `ValueError sleep length must be non-negative`. Now the sender honors delay-seconds and HTTP-date values. A date in the past waits zero seconds. Any other value falls back to the computed backoff, so `send` raises `DeliveryError` as before. Five new test cases cover these values.

## Item 2, no guard on `rate` (F2, REJECT)

I kept the constructor as it is, because no caller produces a rate of zero or less. In this repo, only the three tests construct `TokenBucketLimiter`, and each passes `rate=1.0`. The rate comes from our own code, not from a tenant or a request, so this is not a trust boundary. The fixed window on `main` had no guard on `limit` either.

A wrong rate also fails closed. I ran the limiter with `rate=-1.0` and `burst=3`. It allowed three sends and then refused every send, also after one hour on the clock. A guard for a value that nothing produces tells the next reader that the value can occur. If a config path for the rate appears later, that path is the place to validate it.

## Item 3, buckets in process memory (F3, DEFER)

You are right that each process has its own buckets. `TokenBucketLimiter` keeps them in a dict at `notify/ratelimit.py:16`. The fixed window on `main` kept `_counts` in the same way, so this PR does not introduce the gap.

A shared store adds a Redis dependency, and this PR states "No new dependencies". I added a limitation note to the PR description. I proposed a follow-up ticket, not filed yet: "Share token-bucket state across sender workers". I could not find the worker count in the repo, so the ticket asks for it.

## Item 4, docstring drift and a `RetryPolicy` hierarchy (F4a ACCEPT, F4b REJECT)

The drift is real, and 66fb531 fixes the docstring. The docstring said "on 429 or 503", but `_delay` reads the header on every retryable status. The PR description says the sender "honors a Retry-After header" with no status limit. So I changed the docstring to match the code, and a new test pins the behavior on a 500.

I did not add a `RetryPolicy` hierarchy, because the sender has one strategy and one caller of it. A hierarchy with one subclass is an abstraction that nothing else uses. The drift was between a docstring and the code, and a class hierarchy has docstrings that can drift too. A test catches this drift, and 66fb531 adds one. If a second strategy appears, that change is the place to extract a policy.

## Item 5, move the sender to `asyncio` (F5, DEFER)

The blocking is real, and this PR makes it longer. `send` calls `self.sleep`, which defaults to `time.sleep` (`notify/sender.py:24`). Per `docs/BENCHMARKS.md`, the worst-case wait per message rises from 3 s to 31 s. The sender on `main` also slept synchronously, so the blocking itself is older than this PR.

A port to `asyncio` makes `send` a coroutine and breaks every synchronous caller. That change is outside this PR, which changes the retry and throttle behavior. I could not check the company convention from this repo, which has no async code. I proposed a follow-up ticket, not filed yet: "Port the notify sender to asyncio".

## Item 6, the cap drops from 100 to 60 per minute (F6, NEEDS-INPUT)

Held. Not posted until the PR author answers the question in the report.

Draft for after the answer: I found no record of a product decision in the repo. `docs/BENCHMARKS.md` records the new cap and the three staging tenants that it throttles, but not who approved it. The cap stays at 60 per minute until the PR author confirms the decision or asks for 100.

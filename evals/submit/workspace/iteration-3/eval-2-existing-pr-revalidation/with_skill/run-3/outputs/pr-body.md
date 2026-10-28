## Why

About 9% of notifications were lost when the gateway was flaky.

The sender tried each message three times, one second apart. That is shorter than the typical recovery window of the gateway. The sender also treated 429 as a hard failure.

The per-tenant limit had a second problem. It used a fixed window of 100 sends per minute. A tenant could spend the whole quota in the first second and then send nothing for the rest of the minute.

## What & how

The sender now backs off exponentially and honors Retry-After. A per-tenant token bucket replaces the fixed window.

- Delivery success goes from 91.2% to 99.1%, and 429 responses drop from 1,840 to 12 per 10k sends.
- p99 latency grows from 3.4 s to 9.8 s, and the worst-case wait per message grows from 3 s to 31 s.
- Tenants that send more than 20 messages at once are now throttled to one per second. Three tenants on staging hit this.
- The package no longer exports `FixedWindowLimiter`. Code that imports it breaks.

Load test from `docs/BENCHMARKS.md`: 10,000 sends per run against staging, 20% injected 5xx, and a 429 storm at minute 3. Each number is the median of three runs.

| Metric | Before | After |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

The load test measured both changes together. It does not show how much of the gain comes from the backoff and how much from the token bucket.

The sender tries each message up to five times. Each wait doubles from 0.5 s, with a cap of 16 s. The sender also retries on 429. A Retry-After header replaces the computed wait, and the cap does not apply to it.

The token bucket refills at one token per second per tenant and holds at most 20 tokens. The public API changes as follows:

```python
# before
from notify import FixedWindowLimiter
limiter = FixedWindowLimiter(limit=100, window=60.0)

# after
from notify import TokenBucketLimiter
limiter = TokenBucketLimiter(rate=1.0, burst=20)
```

## Other changes

The README fixes the spelling of "receive".

Related:
- none

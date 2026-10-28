## Why

A flaky gateway lost about 9% of notifications, and a tenant could send a whole minute's quota in one second.

The sender retried three times one second apart. That is shorter than the typical recovery window of the gateway. It also treated 429 as a hard failure. The fixed window limiter allowed 100 sends per tenant per minute, and a tenant could send all 100 at once.

## What & how

The sender now retries five times with exponential backoff and honors a Retry-After header. A token bucket replaces the fixed window limiter. It allows each tenant one send per second, with a burst of 20.

Staging load test, 10,000 sends per run, median of three runs, from `docs/BENCHMARKS.md`:

| | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

- Delivery success rises from 91.2% to 99.1%. The load test measured backoff and the token bucket together. It does not split the gain between them.
- p99 latency grows from 3.4 s to 9.8 s. The worst-case wait per message grows from 3 s to 31 s.
- Tenants that send more than 20 messages at once are now throttled and drain at one per second. Three tenants on staging hit this.
- The package no longer exports `FixedWindowLimiter`. Code that imports it breaks and must move to `TokenBucketLimiter`.

The public API of the limiter changes like this:

```python
# before
from notify import FixedWindowLimiter
limiter = FixedWindowLimiter(limit=100, window=60.0)

# after
from notify import TokenBucketLimiter
limiter = TokenBucketLimiter(rate=1.0, burst=20)
```

The first retry waits 0.5 s, and each next retry doubles the wait up to a cap of 16 s. A Retry-After header on any retried response overrides the computed wait.

The sender does not call the limiter itself. This PR does not connect them.

## Other changes

- Fix the spelling of "receive" in the README.

Related:
- none

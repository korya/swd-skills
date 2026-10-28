## Why

About 9% of notifications were lost when the gateway was flaky, and bursty tenants caused 429 storms.

The sender retried three times one second apart. That is shorter than the typical recovery window of the gateway. It also treated 429 as a hard failure. The fixed window limiter let a tenant send its whole minute of quota in one second and then nothing.

## What & how

The sender now retries five times with exponential backoff and honors a Retry-After header. A per-tenant token bucket replaces the fixed window limiter. Delivery success goes up, but slow messages get slower and bursty tenants are throttled sooner.

Staging load test, 10,000 sends per run, median of three runs, from `docs/BENCHMARKS.md`:

| | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

Side effects:

- **Slower tail.** The p99 latency goes up by 6.4 s. The worst-case wait per message goes up by 28 s.
- **Lower cap for tenants.** The sustained cap drops from 100 to 60 messages per minute. A tenant that sends 100 messages at once is throttled after 20 and then drains at one message per second. Three tenants on staging hit this.
- **Breaking import.** The `notify` package no longer exports `FixedWindowLimiter`. Code that imports it must switch to `TokenBucketLimiter`.

```python
# before
from notify import FixedWindowLimiter
limiter = FixedWindowLimiter(limit=100, window=60.0)

# after
from notify import TokenBucketLimiter
limiter = TokenBucketLimiter(rate=1.0, burst=20)
```

The benchmark measures the backoff and the token bucket together. It does not show how much of the gain comes from each change.

A lower fixed window cap is not enough. A fixed window still lets a tenant spend its whole quota in one burst, and those bursts caused the 429 storms. The token bucket spreads the sends over the minute.

A Retry-After header overrides the computed delay. A gateway can therefore make the sender wait longer than the 16 s cap on the backoff.

This PR does not connect the limiter to the sender. That stays out of scope. Callers keep calling `allow()` before each send, as before.

## Other changes

- The README now spells "receive" correctly.

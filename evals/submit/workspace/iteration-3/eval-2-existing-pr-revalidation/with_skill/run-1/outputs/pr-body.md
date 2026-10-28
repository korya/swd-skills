## Why

About 9% of notifications were lost under a flaky gateway, and tenants could burst a minute's quota in one second.

The sender retried three times one second apart. That is shorter than the typical recovery window of the gateway. The sender also treated 429 as a hard failure.

The fixed-window limiter allowed 100 sends per tenant in each 60 s window. It did not limit how fast a tenant spent them. A tenant could send all 100 in the first second and then nothing for the rest of the minute.

## What & how

The sender now retries five times with exponential backoff and honors a Retry-After header. Each tenant now gets a token bucket instead of a fixed window.

Staging load test from `docs/BENCHMARKS.md`, median of three runs:

| | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

Side effects:

- Better: more messages arrive, and the gateway sends far fewer 429 responses.
- Worse: the p99 latency almost triples, and the worst-case wait per message grows tenfold.
- Tenants: a tenant that sends 100 messages at the start of each minute is now throttled after 20. It then drains at one per second. Three tenants on staging hit this.
- API: the package no longer exports `FixedWindowLimiter`. Code that imports it breaks.
- The benchmark measures the retry change and the limiter change together. It does not separate their effects.

The limiter API before and after:

```python
# before: at most `limit` sends per tenant in each `window` seconds
FixedWindowLimiter(limit=100, window=60.0)

# after: `rate` tokens per second, bucket capacity `burst`
TokenBucketLimiter(rate=1.0, burst=20)
```

Retry details:

- Each retry waits `0.5 * 2**attempt` seconds, capped at 16 s.
- The sender retries on 429, 500, 502, 503, and 504.
- A Retry-After header overrides the computed delay. The 16 s cap does not apply to it.

Related:
- none

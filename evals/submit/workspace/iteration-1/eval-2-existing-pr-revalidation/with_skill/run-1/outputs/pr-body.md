## Why

Under a flaky gateway about 9% of notifications were lost.

Two things caused it. The sender retried three times one second apart and treated 429 as a hard failure. One second is shorter than the gateway's typical recovery window. The fixed-window limiter let a tenant send its whole 100-per-minute quota in the first second of each minute. Those bursts produced the 429 storms.

## What & how

The sender now retries five times with exponential backoff (0.5 s base, 16 s cap) and honors a Retry-After header. The per-tenant limiter is now a token bucket with a sustained rate of 60 per minute and a burst of 20. Staging load test, 10,000 sends with 20% injected 5xx and a 429 storm at minute 3, median of three runs:

| | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

The trade: p99 latency roughly triples, and the slowest message now waits 31 s instead of failing after 3 s. In return about 8 of every 100 messages that used to be lost now arrive. Other side effects:

- Tenant behaviour changes. A tenant that sent 100 messages in the first second of each minute is now throttled after 20 and drains at one per second. Three staging tenants hit this.
- Breaking API change. `FixedWindowLimiter` is removed from the `notify` package. Callers switch to `TokenBucketLimiter(rate, burst)`.
- No new dependencies.

```python
# before
limiter = FixedWindowLimiter(limit=100, window=60.0)

# after
limiter = TokenBucketLimiter(rate=1.0, burst=20)
```

A shorter fixed window would not have fixed the bursts. Any fixed window still allows the full quota at its edge, and two adjacent windows allow double. A token bucket bounds the burst independently of the sustained rate.

Out of scope: the sender does not call the limiter itself. Callers wire the two together, as before.

## Other changes

- `docs/BENCHMARKS.md` now carries the before and after columns shown above.
- No visual change. This branch touches library code and Markdown only, so there are no screenshots.

Related:
- none

## Why

Under a flaky gateway about 9% of notifications were lost, and tenants that spent their whole minute's quota in one second set off 429 storms.

Two causes compounded. The sender retried three times one second apart, shorter than the gateway's typical recovery window, and treated 429 as a hard failure. The per-tenant limiter was a fixed window of 100/min, so a tenant could post all 100 in the first second and then nothing; the gateway saw those bursts and answered with 429s that the sender then gave up on.

## What & how

The sender now retries five times with exponential backoff (0.5 s base, 16 s cap) and honors a Retry-After header. The per-tenant limiter becomes a token bucket at 60/min sustained with a burst of 20, so load is spread across the minute instead of front-loaded.

Staging load test, 10,000 sends with 20% injected 5xx and a 429 storm at minute 3, median of three runs (docs/BENCHMARKS.md):

| | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

The trade: messages that used to fail after 3 s now wait out the backoff, so the tail grows (p99 3.4 s → 9.8 s, worst case 31 s) in exchange for 8 points of delivery and a 429 count that drops from 1,840 to 12. Tenants that relied on sending 100 messages in the first second of each minute are throttled after 20 and drain at one per second; three tenants on staging hit this and should be told before rollout. Sustained throughput per tenant drops from 100/min to 60/min. No new dependencies.

Public API change: `FixedWindowLimiter` is removed rather than deprecated, since nothing in-tree beyond the package export referenced it.

```python
# before
from notify import FixedWindowLimiter
limiter = FixedWindowLimiter(limit=100, window=60.0)

# after
from notify import TokenBucketLimiter
limiter = TokenBucketLimiter(rate=1.0, burst=20)
```

The bucket is refilled lazily on each `allow()` call from the elapsed monotonic time, so there is no background task and no per-tenant timer; a tenant that goes quiet costs one dict entry. Jitter is wired into the sender but defaults to 0, so the retry schedule in tests is deterministic.

## Other changes

- docs/BENCHMARKS.md gains before/after columns for the load test.
- README: fix the "recieve" typo.

Related:
- none

## Why

The sender lost about 9% of notifications to a flaky gateway, and tenants could burst a minute's quota at once.

The sender retried three times one second apart and treated 429 as a hard failure. The gateway typically needs longer than 3 s to recover. The per-tenant limiter was a fixed window of 100 per minute. A tenant could send all 100 in the first second of a minute and then nothing. The gateway saw 1,840 429 responses per 10,000 sends.

## What & how

The sender now retries five times with exponential backoff and honors Retry-After. The backoff starts at 0.5 s and caps at 16 s. The per-tenant limiter is now a token bucket that allows 60 per minute sustained with a burst of 20.

Staging load test, median of three runs. Each run sends 10,000 messages with 20% injected 5xx responses and a 429 storm at minute 3.

| Metric | Before | After |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

The trade is latency for delivery. p99 latency grows from 3.4 s to 9.8 s and the worst-case wait per message from 3 s to 31 s. A message now waits out up to five backoff steps instead of failing after 3 s. In return the gateway sees 150 times fewer 429 responses and about 8% more messages arrive.

Bursty tenants see a behaviour change. Tenants that relied on sending 100 messages in the first second of each minute are now throttled after 20 and drain at one per second. Three tenants on staging hit this.

The public export `FixedWindowLimiter` is gone and `TokenBucketLimiter` takes its place. Any importer of the old name breaks at import time. No new dependencies.

The limiter contract, before and after:

```python
# before: whole quota available at the start of each window
FixedWindowLimiter(limit=100, window=60.0)

# after: 1 token per second, up to 20 banked
TokenBucketLimiter(rate=1.0, burst=20)
```

Both limiters take an injectable `clock`, so the tests drive time with a fake and never sleep. The delivery success numbers are for the sender and the limiter together. Neither change was measured on its own.

## Other changes

README: fix the spelling of "receive".

Related:
- none

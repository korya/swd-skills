## Why

Under a flaky gateway about 9% of notifications were lost, and the fix on the sender side alone would only move the pain: the fixed-window limiter let a tenant fire its whole 100/min quota in the first second, which is what triggered the 429 storms the sender then had to retry through.

Previously the sender retried three times one second apart (shorter than the gateway's typical recovery window) and treated 429 as a hard failure. The staging load test (10,000 sends, 20% injected 5xx, a 429 storm at minute 3) showed 1,840 429s per 10k sends.

## What & how

The sender retries five times with exponential backoff (0.5 s base, 16 s cap) and honors `Retry-After`. The per-tenant limiter becomes a token bucket: 60/min sustained with a burst of 20, replacing the 100/min fixed window.

| Staging load test, median of 3 runs | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

The trade: delivery goes from 91.2% to 99.1% and 429s all but disappear, paid for with a slower tail (p99 3.4 s to 9.8 s, worst case 31 s) because a message now waits out the backoff instead of failing fast. **Behaviour changes for bursty tenants**: anyone who relied on sending 100 messages in the first second of a minute is throttled after 20 and drains at one per second; three tenants on staging hit this. No new dependencies.

`FixedWindowLimiter` is removed rather than kept alongside `TokenBucketLimiter`: nothing in the repo imported it, and keeping both invites a config knob nobody asked for. Any out-of-tree importer breaks at import time rather than silently.

```python
# before
FixedWindowLimiter(limit=100, window=60.0)
# after
TokenBucketLimiter(rate=1.0, burst=20)   # rate is sends per second
```

Out of scope: the sender does not consult the limiter itself; callers still check `allow()` before `send()` as before.

## Other changes

- `docs/BENCHMARKS.md` gains the before/after column above.
- README: "recieve" typo.

Related:
- none

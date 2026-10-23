## Why

Under a flaky gateway about 9% of notifications were lost, and tenants that front-loaded their quota triggered 429 storms that hurt everyone else.

Two causes, measured in the staging load test (10k sends, 20% injected 5xx, a 429 storm at minute 3):

- The sender retried three times one second apart, shorter than the gateway's typical recovery window, and treated 429 as a hard failure.
- The fixed-window limiter let a tenant send its whole 100/min quota in the first second of each minute, which is where the 1,840 429s per 10k sends came from.

## What & how

The sender now retries five times with exponential backoff (0.5 s base, 16 s cap) and honors `Retry-After`. The per-tenant limiter is a token bucket (60/min sustained, burst of 20) instead of a fixed 100/min window, so load spreads across the minute.

| Metric | Before (fixed retries + fixed window) | After (backoff + token bucket) |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

The trade: messages that used to be dropped now wait instead, so the p99 roughly triples and the worst case grows to 31 s; in return delivery goes from 91% to 99% and 429s all but disappear. The sustained cap also drops from 100/min to 60/min. Tenants that relied on bursting 100 messages per minute are now throttled after 20 and drain at one per second; three staging tenants hit this today and should be told before this ships.

`FixedWindowLimiter` is removed rather than kept alongside the bucket: nothing else in the package imports it, and keeping two limiters invites someone to switch back and reintroduce the storms. No new dependencies.

## Other changes

- `docs/BENCHMARKS.md` gains the before/after column above.
- README: fix the "recieve" typo.

Related:
- none

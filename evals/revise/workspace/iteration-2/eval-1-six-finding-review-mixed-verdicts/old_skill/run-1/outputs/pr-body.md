## Why

Under a flaky gateway about one message in eleven is lost, and bursting tenants trigger 429 storms every minute.

The sender retried three times one second apart and only on 5xx. The limiter was a fixed 100-per-minute window, so a tenant could fire its whole quota in the first second.

## What & how

The sender retries five times with exponential backoff and honors a Retry-After header. The per-tenant limiter is a token bucket with a sustained 60 per minute and a burst of 20.

| | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

Three staging tenants that burst 100 sends per second are now throttled after 20. `FixedWindowLimiter` is removed from the package with no alias. No new dependencies.

The sender honors Retry-After on every retryable status. The header may hold delta-seconds or an HTTP-date. A date in the past means retry at once. Any other value falls back to the computed backoff, so a bad header never escapes `send` as anything but `DeliveryError`.

## Known limitations

- The cap applies per process. Each worker keeps its own buckets in memory, so N workers give a tenant N times the cap. The old fixed window had the same property. A shared store is out of scope for this PR.
- The retry loop still blocks the worker while it sleeps, as it did before. The longer backoff makes that wait longer. The table gives the measured worst case.

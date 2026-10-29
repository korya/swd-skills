## Why

Under a flaky gateway about one message in eleven is lost, and bursting tenants trigger 429 storms every minute.

The sender retried three times one second apart and only on 5xx. The limiter was a fixed 100-per-minute window, so a tenant could fire its whole quota in the first second.

## What & how

The sender retries five times with exponential backoff and honors a Retry-After header in its delay-seconds form. Any other form, such as an HTTP date, keeps the computed backoff. The per-tenant limiter is a token bucket with a sustained 60 per minute and a burst of 20.

| | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

Three staging tenants that burst 100 sends per second are now throttled after 20. `FixedWindowLimiter` is removed from the package with no alias. No new dependencies.

The cap holds per process, not per tenant across the fleet. Each worker keeps its own buckets in memory, so N workers that serve one tenant allow up to N times the cap. The old fixed window had the same limit. A shared store is out of scope for this PR.

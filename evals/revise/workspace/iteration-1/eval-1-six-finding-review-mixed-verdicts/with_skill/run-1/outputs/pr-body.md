## Why

Under a flaky gateway about one message in eleven is lost, and bursting tenants trigger 429 storms every minute.

The sender retried three times one second apart and only on 5xx. The limiter was a fixed 100-per-minute window, so a tenant could fire its whole quota in the first second.

## What & how

The sender retries five times with exponential backoff and honors a numeric Retry-After header. The per-tenant limiter is a token bucket with a sustained 60 per minute and a burst of 20.

| | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

Three staging tenants that burst 100 sends per second are now throttled after 20. `FixedWindowLimiter` is removed from the package with no alias. No new dependencies.

A Retry-After header in the HTTP-date form is not parsed. The sender falls back to the computed backoff for it, so the header never raises out of `send`.

## Known limitations

The limiter counts per process, as the fixed window did before this PR. With N workers serving one tenant, the effective cap is N times 60 per minute. A shared store is proposed as a follow-up ticket, "Share the per-tenant token bucket across workers".

## Open question

The sustained cap moves from 100 to 60 per minute. The product decision behind that number is not linked yet. The branch keeps 60 until the decision is confirmed or a different value is agreed.

## Why

About 9% of notifications never reached the gateway when it was flaky.

The sender retried three times, one second apart. That is shorter than the typical recovery window of the gateway. The sender also treated a 429 response as a hard failure.

The per-tenant limiter used a fixed window of 100 sends per minute. A tenant could spend the full quota in one second and then send nothing until the window reset.

## What & how

The sender now retries five times with exponential backoff and honors a Retry-After header. A token bucket replaces the fixed window. Each tenant gets one send per second sustained, with a burst of 20.

Staging load test, 10,000 sends per run, median of three runs (`docs/BENCHMARKS.md`):

| | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| 429 responses per 10k sends | 1,840 | 12 |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

The trade is more delivered messages for a longer tail. About 8 more messages in 100 arrive. The p99 latency rises by 6.4 s, and the worst-case wait rises by 28 s.

Who is affected:

- **Tenants that send more than 20 messages at once.** The limiter now throttles them after 20, and the rest drain at one per second. Three tenants on staging hit this.
- **Code that imports `notify.FixedWindowLimiter`.** This PR removes that name. Use `TokenBucketLimiter` instead.

Details a reviewer should not miss:

- The after column measures both changes together. The load test does not separate the effect of the backoff from the effect of the token bucket.
- Each retry waits 0.5 s, doubled per attempt, with a cap of 16 s. The sender supports jitter, but the default is zero.
- A Retry-After header overrides the computed delay, and the sender does not cap it. A gateway that sends a large value holds the message for that long.

## Other changes

- Fix the spelling of "receive" in `README.md`.

Related:
- none

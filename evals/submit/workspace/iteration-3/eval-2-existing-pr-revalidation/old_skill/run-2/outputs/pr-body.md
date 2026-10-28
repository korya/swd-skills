## Why

Under a flaky gateway, about 9% of notifications were lost.

The sender retried three times, one second apart. That is shorter than the typical recovery window of the gateway. The sender also treated a 429 response as a hard failure.

Separately, the fixed-window limiter let a tenant send its whole quota for a minute in one second, then nothing.

## What & how

The sender now backs off exponentially between attempts and honors a Retry-After header. A token bucket replaces the fixed-window limiter for each tenant.

The table shows the staging load test. Each run sends 10,000 messages with 20% injected 5xx responses and a 429 storm at minute 3. Values are the median of three runs.

| | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| 429 responses per 10k sends | 1,840 | 12 |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

Side effects a reviewer must weigh:

- **Slower tail.** The p99 latency grows by 6.4 s. One message can now wait up to 31 s before it succeeds or fails.
- **Tenants that burst are throttled.** A tenant that sent 100 messages at the start of each minute is now throttled after 20. It then drains at one per second. Three tenants on staging hit this.
- **Breaking import.** The `notify` package no longer exports `FixedWindowLimiter`. `TokenBucketLimiter` replaces it. No code in this repo imports the old name.
- **Combined measurement.** The load test ran both changes together. It does not show how much of the gain comes from the backoff and how much from the limiter.

The sender makes up to five attempts. The delay starts at 0.5 s, doubles on each attempt, and stops at 16 s. A Retry-After header on 429 or 503 overrides the computed delay.

The sender does not call the limiter itself. This PR changes the limiter, not where callers apply it. That wiring is out of scope.

## Other changes

- `docs/BENCHMARKS.md` now shows the old and the new setup side by side.
- The README fixes the spelling of "receive".

Related:
- none

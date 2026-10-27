## Why

Under a flaky gateway about one message in eleven is lost, and bursting tenants trigger 429 storms every minute.

The sender retried three times one second apart and only on 5xx. The limiter was a fixed 100-per-minute window, so a tenant could fire its whole quota in the first second.

## What & how

The sender retries five times with exponential backoff and honors a Retry-After header on any retryable response, in both forms RFC 9110 allows (seconds or an HTTP-date). The per-tenant limiter is a token bucket with a sustained 60 per minute and a burst of 20.

| | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

Three staging tenants that burst 100 sends per second are now throttled after 20. `FixedWindowLimiter` is removed from the package with no alias. No new dependencies.

A Retry-After value in neither RFC form falls back to the computed backoff instead of raising: the gateway is not under our control, and callers are promised `DeliveryError`, not `ValueError`. `Sender` takes an injectable `now` wall clock for the date form, alongside the existing `sleep` and `rand`.

**Known limitation.** The bucket lives in process memory, as the fixed window did before it, so with N workers serving one tenant the effective cap is N times 60 per minute. A shared store is a separate change (ticket proposed in review).

**Open.** Whether product agreed to the sustained cap moving from 100 to 60 per minute is unconfirmed; the decision link or a revert to 100 will follow before this leaves draft.

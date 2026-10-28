## Why

When the gateway fails or throttles, almost one message in eleven never reaches it.

In the load test, only 91.2% of 10,000 sends arrive. The test injects 5xx responses on 20% of requests and a 429 storm at minute 3. The sender retries a 5xx three times, one second apart, and then gives up. It does not retry a 429 at all. The fixed-window limiter lets a tenant spend a full minute of quota in one second.

## What & how

The sender now retries 429 and 5xx responses with exponential backoff and obeys Retry-After. Each tenant now gets a token bucket instead of a fixed window.

| Load test, median of three runs | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

Side effects:

- **More messages arrive.** Delivery success rises by 7.9 points. The 429 responses drop from 1,840 to 12 per 10k sends.
- **The tail gets slower.** The p99 latency rises from 3.4 s to 9.8 s. The worst-case wait per message rises from 3 s to 31 s. A caller that blocks on `send()` waits longer before it gets a `DeliveryError`.
- **Bursty tenants are throttled earlier.** A tenant that sends 100 messages in the first second of a minute now stops after 20. It then drains at one per second. Three tenants on staging hit this cap.
- **The sustained cap drops.** Each tenant gets 60 sends per minute instead of 100.
- **The public API breaks.** `Sender` no longer accepts `delay`. The `notify` package no longer exports `FixedWindowLimiter`. No other code in this repo uses either name.

The API changes like this:

```python
# before
Sender(client, retries=3, delay=1.0)
FixedWindowLimiter(limit=100, window=60.0)

# after
Sender(client, retries=5, base=0.5, max_delay=16.0, jitter=0.0)
TokenBucketLimiter(rate=1.0, burst=20)
```

Without a Retry-After header, a message that keeps failing follows this schedule with the defaults:

| Attempt | Then |
|---|---|
| 1 | wait 0.5 s |
| 2 | wait 1 s |
| 3 | wait 2 s |
| 4 | wait 4 s |
| 5 | raise `DeliveryError` |

A Retry-After header on any retryable response replaces the computed wait. The sender still returns any other 4xx at once, without a retry.

### Known gaps

This PR does not fix the gaps below. I confirmed the first two with a probe against the branch.

- **An HTTP-date Retry-After crashes the send.** The sender passes the header to `float()`. A value such as `Wed, 21 Oct 2026 07:28:00 GMT` raises `ValueError` out of `send()`, not `DeliveryError`.
- **Retry-After has no upper bound.** The `max_delay` cap applies only to the computed backoff. A header of `120` makes the sender sleep for 120 s.
- **Jitter is off by default.** The `jitter` argument defaults to `0.0`. Senders that fail at the same moment retry at the same moment.

## Other changes

- `README.md`: fix the spelling of "receive".
- `docs/BENCHMARKS.md`: show the before and after numbers side by side.

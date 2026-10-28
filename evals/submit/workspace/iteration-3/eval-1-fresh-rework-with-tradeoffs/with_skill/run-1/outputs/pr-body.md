## Why

About one message in eleven is not delivered when the gateway returns errors or a 429 storm.

The staging load test sends 10,000 messages with 20% injected 5xx responses and a 429 storm at minute 3. With the current sender, 91.2% of the messages arrive. The gateway also returns 1,840 responses with status 429 per 10,000 sends.

The current sender and limiter work like this:

- The sender retries a 5xx three times with a fixed one-second wait. It never retries a 429.
- The limiter gives each tenant 100 sends per fixed 60-second window. A tenant can spend the whole quota in the first second and then send nothing until the window resets.

## What & how

The sender now retries with exponential backoff and obeys Retry-After. Each tenant now gets a token bucket that allows 60 sends per minute, with a burst of 20.

| Load test, median of three runs | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

Side effects:

- **Better delivery.** Success goes from 91.2% to 99.1%. 429 responses drop from 1,840 to 12 per 10,000 sends.
- **Slower tail.** p99 latency goes from 3.4 s to 9.8 s. The worst-case wait for one message goes from 3 s to 31 s.
- **Tenants that burst are throttled.** A tenant that sent 100 messages at the start of each minute now gets 20, then one per second. Three tenants on staging hit this.
- **Breaking API change.** `notify` no longer exports `FixedWindowLimiter`, and `Sender` no longer accepts `delay`.
- **Fewer statuses are retried.** Statuses 501, 505, and any 5xx other than 500, 502, 503, and 504 now fail at once.

### Retry schedule

The defaults are `retries=5`, `base=0.5`, `max_delay=16`, and `jitter=0`. A Retry-After header replaces the computed wait.

| Attempt | Wait after a retryable status |
|---|---|
| 1 | 0.5 s |
| 2 | 1 s |
| 3 | 2 s |
| 4 | 4 s |
| 5 | none, raise `DeliveryError` |

Retryable statuses: 429, 500, 502, 503, and 504.

### API change

```python
# before
Sender(client, retries=3, delay=1.0)
from notify import FixedWindowLimiter
FixedWindowLimiter(limit=100, window=60.0)

# after
Sender(client, retries=5, base=0.5, max_delay=16.0, jitter=0.0)
from notify import TokenBucketLimiter
TokenBucketLimiter(rate=1.0, burst=20)
```

### Why a token bucket and not a larger window

A token bucket refills continuously. A tenant can never spend a full minute of quota in one second. A larger or shorter fixed window keeps the edge where the quota resets, so a tenant can still burst at the start of each window.

### Open questions for review

- **The 31 s worst case does not follow from the defaults.** With the defaults, the computed waits add up to 7.5 s. The test `test_backoff_doubles` asserts this. Please confirm which configuration or Retry-After values the load test used.
- **Retry-After has no upper limit.** `max_delay` does not apply to it. A probe with `Retry-After: 3600` made the sender wait one hour before the next attempt.
- **Retry-After accepts only seconds.** With an HTTP-date value, `send` raises `ValueError` after the first attempt and does not retry.
- **Jitter is off by default.** With `jitter=0`, senders that fail together retry together.
- **The docstring says Retry-After applies on 429 or 503.** The code obeys it on every retryable status.

## Other changes

- The README spells "receive" correctly.

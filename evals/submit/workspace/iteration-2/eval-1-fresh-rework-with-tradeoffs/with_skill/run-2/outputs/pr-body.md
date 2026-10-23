## Why

When the gateway is flaky, almost one notification in eleven is lost, and bursty tenants draw 429 storms upstream.

The sender retried three times with a fixed one-second wait and gave up. Three seconds is not enough to outlast a gateway hiccup, so a burst of 5xx responses turned into a `DeliveryError` for the caller. The fixed window limiter made the second problem worse. It counted 100 sends per tenant from the first send of each minute, so a tenant could fire its whole quota in one second. The gateway answered those spikes with 429, which the sender then retried at the same fixed cadence.

The load test in `docs/BENCHMARKS.md` puts numbers on both. 10,000 sends per run, 20% injected 5xx, a 429 storm at minute 3, median of three runs.

## What & how

The sender retries with exponential backoff and honors `Retry-After`. Per-tenant throttling moves from a fixed window to a token bucket that refills continuously.

| Metric | Before: fixed retries + fixed window | After: backoff + token bucket |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

The trade: nearly every message now arrives, and the gateway sees two 429s where it saw three hundred. In return the tail gets longer. A message caught in a storm can wait ten times as long as before, because the sender now waits out `Retry-After` instead of failing. Side effects beyond the table:

- Three staging tenants that sent 100 messages in the first second of each minute are now throttled after 20 and drain at one per second. Their owners should hear about this before the deploy.
- The sustained per-tenant cap drops from 100/min to 60/min.
- The public API changes. `FixedWindowLimiter` is removed and the `Sender` constructor loses `delay`. Callers that pass either break at import or construction time.
- No new dependencies. `random` and `time` are standard library.

### API contract

```python
# before
Sender(client, retries=3, delay=1.0, sleep=time.sleep)
FixedWindowLimiter(limit=100, window=60.0, clock=time.monotonic)

# after
Sender(client, retries=5, base=0.5, max_delay=16.0, jitter=0.0, sleep=time.sleep, rand=random.random)
TokenBucketLimiter(rate=1.0, burst=20, clock=time.monotonic)
```

### Retry schedule with the defaults

| Attempt | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Wait after a retryable failure | 0.5 s | 1 s | 2 s | 4 s | raise `DeliveryError` |

Retryable means 429, 500, 502, 503, or 504. Any other status is returned to the caller on the first attempt. A `Retry-After` header on a retryable response replaces the computed wait for that attempt.

### Decisions a reviewer should weigh

- `Retry-After` is not capped by `max_delay`. The 31 s worst case in the table comes from the gateway's own header during the storm. A gateway that sends a very large value would stall that message for as long as it says. This is deliberate for now, because the header is the gateway telling us what it can take. A ceiling is cheap to add if we want one.
- Jitter is available but defaults to 0. The benchmark ran without it. Turning it on spreads retries from many workers, at the cost of less predictable test timing.
- A token bucket rather than a smaller fixed window. A fixed window at any limit still allows a full-quota burst at the window edge. The bucket permits a burst of 20 and then enforces the sustained rate, which is what the gateway can absorb.
- Bucket state lives in process memory, one entry per tenant, as the fixed window counts did. Nothing is shared across workers or restarts. That is unchanged and out of scope here.

## Other changes

- `docs/BENCHMARKS.md` now shows the old and new columns side by side on the same load test.
- README: fixed the spelling of "receive".

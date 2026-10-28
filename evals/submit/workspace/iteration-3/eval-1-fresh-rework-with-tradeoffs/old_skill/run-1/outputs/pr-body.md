## Why

When the gateway is unstable, about one message in eleven never arrives, and the gateway rejects many sends with 429.

The sender retried a 5xx three times with a fixed one-second wait, and it never retried a 429. The fixed-window limiter let a tenant send a full minute's quota in one second, then nothing until the minute ended. In the load test with 20% injected 5xx and a 429 storm, delivery success was 91.2%.

## What & how

The sender now retries with exponential backoff and honors Retry-After. Each tenant now gets a token bucket in place of the fixed window.

| Load test, median of three runs | before | after |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| 429 responses per 10k sends | 1,840 | 12 |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

The trade: delivery success rises by 7.9 points and 429 responses drop by 99%. In return the slowest messages wait longer.

- **Slower tail.** The p99 latency grows by 6.4 s. The worst-case wait per message grows from 3 s to 31 s.
- **Tenants with bursty traffic.** A tenant that sent 100 messages at the top of each minute is now throttled after 20. It then drains at one message per second. Three tenants on staging hit this.
- **Breaking API change.** The package no longer exports `FixedWindowLimiter`. Callers switch to `TokenBucketLimiter`, which takes different arguments.

Retry policy, before and after:

```text
before: retry 500-599, 3 attempts, wait 1 s each time
after:  retry 429, 500, 502, 503, 504, 5 attempts
        wait = min(base * 2**attempt, max_delay) + rand() * jitter
        defaults: base 0.5 s, max_delay 16 s, jitter 0 s
        a Retry-After header replaces the computed wait
        no wait after the last attempt
```

Limiter construction, before and after:

```python
# before
from notify import FixedWindowLimiter
limiter = FixedWindowLimiter(limit=100, window=60.0)

# after
from notify import TokenBucketLimiter
limiter = TokenBucketLimiter(rate=1.0, burst=20)
```

Details a reviewer should check:

- **The sender no longer retries 501 and 505.** The old rule retried every status from 500 up. The new set lists 500, 502, 503, and 504 only.
- **Jitter is off by default.** The default `jitter` is 0, so clients that fail together also retry together. A caller must pass a value to spread retries.
- **Retry-After is not capped.** The `max_delay` cap applies only to the computed wait. A gateway that sends a large Retry-After value makes the sender sleep for that long.
- **Retry-After must be a number of seconds.** The sender parses the header with `float()`. The HTTP-date form, such as `Wed, 21 Oct 2015 07:28:00 GMT`, raises `ValueError` out of `send()`.

Out of scope: no migration shim for `FixedWindowLimiter`, and no per-tenant override of the bucket size.

## Other changes

- `docs/BENCHMARKS.md` now shows both setups side by side, with a note on the throttled tenants.
- The README fixes the spelling of "receive".

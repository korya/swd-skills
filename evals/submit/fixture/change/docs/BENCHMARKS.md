# Benchmarks

Load test: 10,000 sends per run against the staging gateway with 20% injected 5xx
responses and a 429 storm at minute 3. Numbers are the median of three runs.

| Metric | Fixed retries + fixed window | Backoff + token bucket |
|---|---|---|
| Delivery success | 91.2% | 99.1% |
| p50 latency | 120 ms | 120 ms |
| p99 latency | 3.4 s | 9.8 s |
| 429 responses per 10k sends | 1,840 | 12 |
| Worst-case wait per message | 3 s | 31 s |
| Per-tenant cap | 100/min, fixed window | 60/min sustained, burst 20 |

Tenants that relied on sending 100 messages in the first second of each minute are now
throttled after 20 and drain at one per second. Three tenants on staging hit this.

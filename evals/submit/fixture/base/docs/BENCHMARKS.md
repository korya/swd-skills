# Benchmarks

Load test: 10,000 sends per run against the staging gateway with 20% injected 5xx
responses and a 429 storm at minute 3. Numbers are the median of three runs.

| Metric | Value |
|---|---|
| Delivery success | 91.2% |
| p50 latency | 120 ms |
| p99 latency | 3.4 s |
| 429 responses per 10k sends | 1,840 |
| Worst-case wait per message | 3 s |
| Per-tenant cap | 100/min, fixed window |

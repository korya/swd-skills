## Why

Under a flaky gateway about 9% of notifications were lost: the sender retried three times one second apart, which is shorter than the gateway's typical recovery window, and it treated 429 as a hard failure.

## What & how

The sender now retries five times with exponential backoff (0.5 s base, 16 s cap) and honors a Retry-After header. Delivery success in the staging load test goes from 91.2% to 99.1%. No change in behaviour for tenants; the rate limiter is untouched.

Related:
- none

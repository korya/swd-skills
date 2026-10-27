# Review of korya-retry-backoff (from the review agent)

Overall this is close. Six items, in the order I read the diff.

1. `notify/sender.py`, `_delay`: `float(retry_after)` will raise `ValueError` when the gateway sends the HTTP-date form of `Retry-After` (RFC 9110 allows it). That exception escapes `send` instead of `DeliveryError`, so a caller catching `DeliveryError` crashes. Parse the date form or fall back to the computed backoff.

2. `notify/ratelimit.py`, `TokenBucketLimiter.__init__`: there is no guard against a negative or zero `rate`. A negative rate would drain tokens forever. Please add validation that raises `ValueError` for `rate <= 0`.

3. `notify/ratelimit.py`: the buckets live in process memory. With N workers behind one tenant, the effective cap is N times 60 per minute. This needs a shared store (Redis) before it is honest to call it a per-tenant cap.

4. `notify/sender.py`: the class docstring says Retry-After is honored "on 429 or 503", but `_delay` reads the header for every retryable status (500, 502, 504 too). The retry loop has grown enough state that it should become an explicit `RetryPolicy` class hierarchy with one subclass per strategy, so this kind of drift cannot happen.

5. While you are in this package: the whole sender should move to `asyncio`. Synchronous `time.sleep` in a retry loop blocks the worker, and every modern client in this company is async.

6. The sustained cap drops from 100 to 60 per minute. I cannot tell from the diff or the docs whether product agreed to this. If they did, link the decision; if not, keep 100.

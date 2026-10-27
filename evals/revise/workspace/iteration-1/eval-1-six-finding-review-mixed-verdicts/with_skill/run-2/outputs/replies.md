# Per-thread replies for the review of korya-retry-backoff

One reply per review thread, in the reviewer's order. Commits named here are on the branch and pushed to origin.

## Thread 1: `float(retry_after)` raises on the HTTP-date form

Accepted and fixed in 33a0889. I reproduced it: `Retry-After: Wed, 21 Oct 2015 07:28:00 GMT` escaped `send` as `ValueError`. An empty value failed the same way. A negative value got past `float` and then `time.sleep` raised `ValueError`, so the root problem was wider than the date form.

The sender now honors the header only as a non-negative integer of seconds. That is the delay-seconds form RFC 9110 defines. Any other value falls back to the computed backoff. Two tests cover the HTTP-date and the negative value.

I chose the fallback over parsing the date form. Parsing needs a wall clock inside the sender, for a form the gateway has not been seen to send. The fallback still waits and still retries.

## Thread 2: validate `rate <= 0` in `TokenBucketLimiter.__init__`

Not taken, with reasoning. The observation is right: with `rate=-1` the bucket denies after the burst and the token count falls without bound. The question is who can produce that value. `rate` is set by application wiring with a literal, and nothing in the repo reads it from configuration or from a tenant. A guard for a state no caller produces tells the next reader the input can be something it cannot. `Sender` validates none of its five numeric arguments either, so the repo has no convention to follow here.

I would add the guard the moment `rate` crosses a trust boundary, for example when it comes from per-tenant settings. If you know of such a caller, point me to it and I will take this.

## Thread 3: buckets live in process memory, needs Redis

Deferred, with a ticket proposed. You are right that the buckets are per process, see `notify/ratelimit.py:16`. N workers behind one tenant multiply the cap by N. That was already true of `FixedWindowLimiter._counts` before this PR. The PR changes the limiter's shape, not where its state lives. The staging run cut 429s from 1,840 to 12 under the real worker layout.

A shared store is a new dependency and a new failure mode, which deserves its own PR. I added the per-process limitation to the PR body so the cap claim is honest. Proposed ticket: "Share TokenBucketLimiter state across workers". It is drafted, not filed.

## Thread 4: docstring drift, and a `RetryPolicy` class hierarchy

Partly taken. The drift is real and fixed in 7c08ea4. I confirmed it: a 500 with `Retry-After: 7` waits 7 s. RFC 9110 lets a server send the header with any response. The code is right and the docstring was wrong. The docstring now says "on any retryable response".

The class hierarchy I did not take. There is one strategy and one caller. An abstraction for one caller is more code for the next reader, with nothing to select between. A hierarchy would not have prevented this drift either, since a docstring can go stale on any class. If a second strategy arrives, the split is cheap to do then.

## Thread 5: move the sender to `asyncio`

Not taken. The PR's intent is retry behavior and tenant throttling, and a change of the package's execution model is a different PR with its own design. The repo has no `async` code and `client.post` is a synchronous interface, so the move would change every caller. I also have no measurement of a blocked worker to weigh the cost against.

A move to async deserves its own proposal, with the callers listed. If every modern client in the company is async, that is a good case for it. It should be judged on its own, not folded into a retry fix.

## Thread 6: the cap drops from 100 to 60 per minute

Held, not resolved. You read the change correctly: `rate=1.0` is 60 per minute, and `docs/BENCHMARKS.md` names three staging tenants that hit the new cap. The repo records no product decision, and I cannot settle this from the code. I have asked the author whether product agreed, and for the link if so. Until that answer arrives the cap stays as the PR proposes, and this thread stays open.

# Replies to post on the review threads of korya-retry-backoff

## Thread 1 — `_delay` raises `ValueError` on the HTTP-date form of Retry-After

Confirmed and fixed in aba2f2e. Reproduced first: a scripted 429 with `Retry-After: Wed, 21 Oct 2015 07:28:00 GMT` escaped `send` as `ValueError: could not convert string to float`, past the `DeliveryError` the README tells callers to catch. `_retry_after` now accepts both RFC 9110 forms: a number of seconds, or an HTTP-date turned into seconds from an injected wall clock (`now=time.time`, never negative). A value in neither form falls back to the computed backoff rather than raising: the gateway is outside our control, so a malformed header should not crash the caller. Three tests cover the date form, a date in the past, and a malformed value.

## Thread 2 — validate `rate <= 0` in `TokenBucketLimiter.__init__`

Not taking this one, and here is the reasoning rather than a bare "won't fix". Your description of the behaviour is accurate (I checked: with `rate=-1` the bucket sits at -100 tokens after 100 s and never allows again). But `rate` is wired by our own code with a literal, not by a tenant or an operator: the only constructors in the repo are the three in `tests/test_ratelimit.py`, and nothing produces a non-positive rate. Nothing else in the package validates constructor arguments either (`Sender(retries=-1)` or `max_delay=-5` are equally unguarded, as was `FixedWindowLimiter(limit=-1)` before this PR), so a guard here would be the one claim in the codebase that this input can happen. If the rate ever becomes operator- or tenant-supplied, that is a trust boundary and the `ValueError` belongs there; happy to add it in that PR.

## Thread 3 — buckets live in process memory; N workers means N times the cap

Agreed on the arithmetic (`_buckets = {}` at `ratelimit.py:15` is per process), and deferring it. The limitation is not new: `FixedWindowLimiter._counts` on `main` was an in-process dict with exactly the same N-times property, so the PR changes the shape of the cap without changing where it lives. A shared store is a new dependency and a deployment change, and this PR says "no new dependencies" on purpose. I have added a "per process" limitation line to the PR body so the cap is described honestly, and drafted a ticket, "Back the per-tenant token bucket with a shared store", for the owner to file.

## Thread 4 — docstring says "429 or 503" while `_delay` reads Retry-After on every retryable status; make it a `RetryPolicy` hierarchy

Half taken, in 94b1df2. The drift is real (`sender.py:17` versus `sender.py:43`), and the code is the side that is right: a server may attach Retry-After to any response, and ignoring it on 500/502/504 would only make us retry sooner than the gateway asked. The docstring now says "any retryable response (see RETRYABLE)", and a test asserts the header is honored for each of the five statuses, so the two cannot drift silently again. I did not introduce a `RetryPolicy` class hierarchy: there is one strategy and one caller, the loop is 12 lines, and a test pins the contract more cheaply than an abstraction would. If a second strategy ever shows up, the hierarchy earns its place then.

## Thread 5 — move the sender to asyncio

Declining as out of scope for this PR. The PR's purpose is backoff plus a token bucket; converting `Sender.send` to a coroutine changes its signature for every caller and is a different change with its own review. I could not verify "every modern client in this company is async" from anything in this repo (there is no async code and no architecture note), and a blocking `time.sleep` is the expected behaviour of a synchronous worker, not a defect; `sleep` is already injectable for callers who need something else. If the company direction is real, it deserves a proposal that covers the callers, not a drive-by here.

## Thread 6 — the sustained cap drops from 100 to 60 per minute; did product agree?

Fair question, and I cannot answer it from the repo: there is no decision link in the PR body, the commit message, or `docs/BENCHMARKS.md`, which only records that three staging tenants hit the new cap. I am holding this thread open and asking the author/product directly. Outcome will be either a link to the decision added to the PR body, or the sustained rate restored to 100/min. Nothing about the cap has been changed in the meantime.

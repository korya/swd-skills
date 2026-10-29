# Replies on the review threads

## Thread 1: `_delay`, `float(retry_after)` on an HTTP date (F1, ACCEPT)

Confirmed and fixed in 40eb91a. On the old code, a 429 with `Retry-After: Wed, 21 Oct 2026 07:28:00 GMT` escaped `send` as this error:

```text
ESCAPED ValueError could not convert string to float: 'Wed, 21 Oct 2026 07:28:00 GMT'
```

A negative value had the same effect one step later. `float("-5")` succeeds, and then `time.sleep(-5)` raises `ValueError: sleep length must be non-negative`.

I took your second option. The sender now honors Retry-After only in the delay-seconds form of RFC 9110. Any other value keeps the computed backoff. A new test covers an HTTP date, `-5`, and `soon`. The test fails on the old code and passes on the fix.

I did not parse the HTTP-date form. That needs a wall clock in the sender next to the injected `sleep`, and we have no report that the gateway sends dates. If it does, a parser fits on top of this fix.

## Thread 2: guard `rate <= 0` in `TokenBucketLimiter.__init__` (F2, REJECT)

Your mechanism is right, but no caller produces the state, so I did not add the guard. With `rate=-1.0` the bucket drains as you say:

```text
-1.0 [True, False, False, False] (-119.0, 1120.0)
```

`rate=0.0` does not drain. It stops the refill and leaves a one-time quota of `burst`.

No code in the repo passes a non-default rate. `grep` finds the default `rate=1.0` in `ratelimit.py:12` and three test calls with `rate=1.0`. Nothing reads a rate from config or user input. A guard here claims that a bad rate can arrive, and nothing in the call graph sends one. If a config path for the rate appears later, the guard belongs at that boundary.

## Thread 3: in-process buckets and N workers (F3, DEFER)

The observation is right, and it is not new in this PR. `_buckets = {}` lives on the instance. The removed `FixedWindowLimiter` kept `_counts = {}` in the same way, so the base branch has the same N-times cap.

A shared store such as Redis adds a dependency and a network call on every send. That is a separate design change. This PR replaces the algorithm, not the storage.

I added a limitation note to the PR description. It says that the cap holds per process and that N workers allow up to N times the cap. I proposed a ticket, not filed yet: "Share token-bucket state across sender workers".

## Thread 4: docstring drift on Retry-After, and a `RetryPolicy` hierarchy (F4 ACCEPT, F5 REJECT)

The drift is real and fixed in b196763. `_delay` reads the header on every status in `RETRYABLE`. With `Retry-After: 3` on a 500, a 502, or a 504, the sender waits 3.0 s. The PR description says the sender "honors a Retry-After header" with no status filter. So the code shows the intent, and I changed the docstring to match the code. 40eb91a then added the delay-seconds rule to the same docstring.

I did not add the `RetryPolicy` hierarchy. The sender has one strategy: exponential backoff, which a valid Retry-After overrides. A class hierarchy with one subclass per strategy has one subclass today. The drift came from one stale docstring line, and a hierarchy also has docstrings that can go stale. The fix for drift is a test that pins the behavior, and the suite has one for Retry-After on a 429.

## Thread 5: move the sender to `asyncio` (F6, DEFER)

`time.sleep` blocks the worker. That is true, and this PR makes it more visible: the worst-case wait per message goes from 3 s to 31 s. But the base branch also calls `time.sleep`, so the blocking is not new. A move to `asyncio` changes the public API of `Sender` for every caller, which is outside the intent of this PR.

I could not check the claim that every modern client in the company is async. Nothing in this repo shows it. The `sleep` parameter is injectable, so an async caller has a seam today.

I proposed a ticket, not filed yet: "Move the notify sender to asyncio".

## Thread 6: sustained cap drops from 100 to 60 per minute (F7, NEEDS-INPUT)

I hold this one until the author answers. The repo has no record of a product decision. `docs/BENCHMARKS.md` and the PR description state the new cap and that three staging tenants hit it, but no link to an agreement. The author must say whether product agreed to 60 per minute. If yes, the description gets the link. If no, the default changes to keep 100 per minute.

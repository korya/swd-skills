# Replies on the review threads

One reply per review item. Item 4 holds two findings, so its reply answers both.

## Item 1: `float(retry_after)` raises on the HTTP-date form

Fixed in 41cd4a0. The sender now parses both forms of Retry-After that RFC 9110 allows.

I reproduced the crash on the PR head first. A 503 with `Retry-After: Wed, 21 Oct 2015 07:28:00 GMT` raised `ValueError: could not convert string to float` out of `send`. The same path had a second hole. `Retry-After: -5` reached `time.sleep` and raised `ValueError: sleep length must be non-negative`.

Now delta-seconds wait that many seconds. An HTTP-date waits until that time, or 0 if the time is past. Any other value falls back to the computed backoff, so `send` raises only `DeliveryError`. Three new tests cover the date form, a past date, and invalid values.

## Item 2: no guard against `rate <= 0`

I am not adding this guard. No caller can pass a bad rate today, so the guard protects against an input that does not occur.

The evidence:

- The only constructor calls are the default (`rate=1.0`) and three tests with `rate=1.0`. No code path reads the rate from config or user input.
- The removed `FixedWindowLimiter` had no guard on `limit` or `window` either. The package does not validate constructor arguments elsewhere.
- A negative rate fails closed. I ran it with `rate=-1.0, burst=2`. The tenant got two sends and then `False` on every call, even 100 seconds later. A misconfiguration shows up in the first minute of use.

If the rate later comes from operator config, the validation belongs in that config loader. That is the trust boundary.

## Item 3: in-process buckets multiply the cap by the worker count

You are right, and I propose a follow-up ticket instead of a change in this PR. The per-process cap is older than this PR.

The removed `FixedWindowLimiter` also kept its counts in a process-local dict (`self._counts = {}` on `main`). This PR changes the algorithm, not where the state lives. A Redis-backed store adds a dependency and an outage mode, and the PR states "No new dependencies". I added a limitation note to the PR description. It says the cap applies per process.

Proposed ticket (not filed yet): "Share per-tenant rate-limit state across sender workers".

## Item 4: docstring drift, and a `RetryPolicy` class hierarchy

The drift is real and fixed in d2f5e0c. I am not adding the class hierarchy.

The docstring said "on 429 or 503", but `_delay` reads the header on every retryable status. I changed the docstring, not the code. The PR description promises Retry-After with no status limit, and the code matches that promise.

The hierarchy would add an abstraction with one strategy and one caller. The sender has one retry strategy, and `_delay` has five lines of body plus the new parser. A class hierarchy would not have prevented a stale docstring. A test that pins the behavior prevents that, and the tests now cover Retry-After on 429 and on 503.

## Item 5: move the sender to `asyncio`

I propose a follow-up ticket for this instead of a change in this PR. An async rewrite changes the public API of the sender for every caller.

The blocking sleep is older than this PR. The `main` branch already calls `self.sleep(self.delay)` between retries. I could not check the claim that every modern client in the company is async. This repo has no async code and no doc that states that convention. One point does support a ticket. This PR raises the benchmark's worst-case wait per message from 3 s to 31 s, so a worker can block longer than before.

Proposed ticket (not filed yet): "Evaluate an async sender to stop retries from blocking workers".

## Item 6: the sustained cap drops from 100 to 60 per minute

No reply posted yet. I asked the PR author whether product agreed to the new cap. This thread stays open until the answer comes back.

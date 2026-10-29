# Replies on the review threads

## Thread 1: HTTP-date form of `Retry-After` (F1, ACCEPT)

Fixed in 5097ba3. The sender now parses both forms of Retry-After that RFC 9110 allows.

I reproduced the crash on 97f5edc. A 503 with `Retry-After: Wed, 21 Oct 2015 07:28:00 GMT` gave this result:

```text
ESCAPED ValueError could not convert string to float: 'Wed, 21 Oct 2015 07:28:00 GMT'
```

Now `Sender._retry_after` accepts delay-seconds or an HTTP-date. A date in the past gives a wait of zero. A value in neither form falls back to the computed backoff, as you proposed.

The same fallback covers `-1` and `inf`, which `float()` accepted before. A negative wait made `time.sleep` raise `ValueError`. Three new tests in `tests/test_sender.py` cover the date, the past date, and the invalid values. They fail on 97f5edc and pass on 5097ba3.

## Thread 2: guard against `rate <= 0` (F2, REJECT)

I did not add the guard, because no caller can pass a non-positive rate today. Your claim about the effect is correct. With `rate=-1.0`, the bucket drains to `(-10.0, 1010.0)` after 10 seconds and never allows a send.

The guard still has no input to catch. The repo constructs `TokenBucketLimiter` in three places, all with `rate=1.0`:

- `tests/test_ratelimit.py:10`
- `tests/test_ratelimit.py:15`
- `tests/test_ratelimit.py:23`

The default in `notify/ratelimit.py:12` is also `rate=1.0`.

No code reads the rate from configuration or from user input. A guard for a state that no writer produces is dead code. It also tells the next reader that a negative rate can arrive. When a caller starts to read the rate from configuration, the validation belongs at that boundary. I am happy to add it in that PR.

## Thread 3: per-process buckets and Redis (F3, DEFER)

You are right that the cap applies per process. With N workers, each worker enforces its own cap. A shared store is a separate change, so I propose a ticket instead of a change in this PR.

The limitation is older than this PR. The `FixedWindowLimiter` on `main` also kept its counts in process memory (`self._counts = {}`). This PR replaces the algorithm and keeps the storage model. A Redis store adds a new dependency, a network call on every send, and a failure mode for the case when Redis is down. That is a design decision with its own trade-offs. It is out of the scope of the stated intent, which is backoff and a token bucket.

I updated the PR description so that it no longer reads as a global cap. It now says that the cap applies per process. Proposed ticket, not filed: "Enforce the per-tenant send cap across worker processes".

## Thread 4, part 1: docstring and `Retry-After` statuses drift (F4, ACCEPT)

Fixed in 831ee68. I changed the docstring to match the code, not the code to match the docstring.

You found a real mismatch. `notify/sender.py:17` said "on 429 or 503", but `_delay` reads the header for every status in `RETRYABLE`. I checked that with a 500 and `Retry-After: 2`, and the sender waited 2.0 seconds. Three sources set the rule:

- The PR description says the sender "honors a Retry-After header" with no limit on status.
- RFC 9110 does not limit the header to 429 or 503.
- A gateway that sends the header on a 500 asks the client to wait, so the sender waits.

The behavior does not change. Only the docstring does.

## Thread 4, part 2: a `RetryPolicy` class hierarchy (F5, REJECT)

I did not add the class hierarchy, because it does not prevent the drift that it targets. The drift was in a docstring. A class hierarchy has docstrings too, and they can drift in the same way.

The sender has one retry strategy today: exponential backoff with an optional Retry-After override. A hierarchy with one subclass per strategy has one subclass. The retry logic is one loop in `send` and one helper per source of delay. Tests already inject `sleep`, `rand` and now `now`, so no extension point is missing. The repo has no convention that asks for a policy object. When a second strategy appears, we can extract the class from two real cases.

## Thread 5: move the sender to `asyncio` (F6, DEFER)

The blocking sleep is real, and this PR makes the worst-case wait longer. The benchmark puts it at 31 s, up from 3 s. A move to `asyncio` changes the public API of `Sender` and of every client it calls, so I propose a ticket.

The client that the sender takes has a synchronous `post`. The tests and `tests/fakes.py` use the same interface. The synchronous `time.sleep` was in the sender before this PR. I could not check the claim that every modern client in the company is async, because this repo does not show it. It would help to link the client that this sender should move to.

Proposed ticket, not filed: "Move notify.Sender to asyncio so retries do not block the worker".

## Thread 6: product approval of the cap change (F7, open)

I left this thread open, because only product can answer it. The repo has no product spec or decision record. It has only `README.md` and `docs/BENCHMARKS.md`. Neither document records a product decision on the cap.

The change is deliberate. The PR description and `docs/BENCHMARKS.md` both state the new cap and the effect on three staging tenants. I asked the PR author for the decision link. The cap stays at 60 per minute until the author answers. If product did not agree, the default goes back to a rate that gives 100 per minute.

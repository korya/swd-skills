# Replies to post on the review threads of korya-retry-backoff

## Thread 1 (F1, ACCEPT)

Confirmed and fixed in 0ef5ddf. `float()` raised `ValueError` on the HTTP-date form, and the exception escaped `send` past any `DeliveryError` handler. Now a Retry-After value that is not a number of seconds is ignored and the computed backoff applies. I took the fallback option rather than parsing the date. Parsing needs a wall clock the sender does not have, and the computed backoff already covers the wait. A regression test covers the date form.

## Thread 2 (F2, REJECT)

Not changing this. I confirmed the behavior you describe. A negative rate drains tokens and blocks the tenant after the burst. But no caller produces that state. The only constructors in the repo pass the default or `rate=1.0`, and the value is a constant set in code, not an operator or tenant input.

A guard for a state nothing produces tells the next reader the input can vary when it cannot. If the rate ever becomes configuration read at a trust boundary, that is the moment to validate it.

## Thread 3 (F3, DEFER)

Agreed that the buckets are per process, and deferred. The fixed window this PR replaces kept `_counts` in process memory too, so the cap had this property before the change. A shared store adds a dependency and a failure mode that this PR's scope does not cover. I added a limitation note to the PR body and drafted a ticket, "Share the per-tenant token bucket across workers". It is proposed, not filed.

## Thread 4 (F4a ACCEPT, F4b REJECT)

The docstring drift is real and fixed in c8dfd9b. `_delay` reads the header for every status in `RETRYABLE`, and the docstring now says so. I kept the code and changed the doc, because a Retry-After hint on a 500 is still worth following.

The `RetryPolicy` hierarchy I am not adding. There is one strategy and one caller. A class hierarchy with one subclass is more surface than the loop it would replace. The drift here was a doc-versus-code mismatch, and a hierarchy would not have caught it.

## Thread 5 (F5, REJECT)

Not in this PR. The change is scoped to backoff and the token bucket. The blocking `time.sleep` predates this branch, and nothing in the repo is async today. I could not verify from this repo that every client in the company is async. The sender's only documented consumer is the synchronous back office. If an async migration is on the roadmap, it deserves its own PR with its own benchmarks.

## Thread 6 (F6, NEEDS-INPUT)

Good question, and I cannot answer it from the repo. Nothing in the docs or the PR records a product decision on the 60 per minute figure. I have asked Dmitri for the decision or a link to it. Until then the branch keeps 60, and the PR body now says the number is unconfirmed.

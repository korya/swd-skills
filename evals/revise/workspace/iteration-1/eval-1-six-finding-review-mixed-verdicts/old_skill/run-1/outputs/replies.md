# Replies to post on the review threads of korya-retry-backoff

## Thread 1 — `_delay`, HTTP-date Retry-After (F1) — ACCEPT

Confirmed: a 429 carrying `Retry-After: Wed, 21 Oct 2015 07:28:00 GMT` raised `ValueError` straight out of `send`. Fixed in a69b12f. `_retry_after` now parses delta-seconds as before, and an HTTP-date via `email.utils.parsedate_to_datetime` as seconds from now (clamped at 0 when the date has passed). A value in neither form is ignored and the computed backoff is used, since the header is gateway input and an unreadable value should not take the worker down. `Sender` gained an injectable `now` wall clock so the date form is testable; three tests cover the date form, a past date, and the fallback. Not changed, same as before: a Retry-After value is not capped at `max_delay`.

## Thread 2 — validate `rate <= 0` (F2) — REJECT

The behaviour you describe is real (I reproduced `rate=-1` driving a bucket to -2 tokens), but I am not adding the guard. `rate` is a constructor argument set by code: the only constructions in the repo are the default and three tests (`tests/test_ratelimit.py:10,15,23`), and nothing parses it from config, env, or a request. A `ValueError` guard for a value no caller can produce is dead code that tells the next reader the input varies when it does not. If a config loader ever feeds `rate`, validation belongs at that boundary, and I would accept it there.

## Thread 3 — per-process buckets, N workers (F3) — DEFER

Agreed on the fact: `_buckets` is a per-process dict, so with N workers one tenant gets up to N×60/min. Two reasons it is not this PR: `FixedWindowLimiter._counts` on `main` had exactly the same property, so this diff neither introduces nor widens it; and a shared store is a new dependency and an ops surface, which this PR explicitly does not add. I have added a "Known limitation" line to the PR body so the per-tenant claim is honest, and drafted a ticket, "Share TokenBucketLimiter state across workers (Redis or equivalent)", proposed in the report for the author to file.

## Thread 4 — docstring vs code, and a `RetryPolicy` hierarchy (F4a ACCEPT, F4b REJECT)

Docstring drift: confirmed (a 500 with `Retry-After: 7` sleeps 7 s). The code is the behaviour I want to keep: a gateway that sends the header on a 502 means it, and the PR body never scoped it to two statuses. Fixed the docstring in 83e25b7.

Hierarchy: not doing this. There is one strategy, one caller, and a 17-line loop; a base class with a single subclass is an abstraction for nobody, and it does not prevent the drift you found (the docstring moves to the subclass, it does not disappear). No guideline or spec in the repo asks for it, and it is outside the PR's intent.

## Thread 5 — move the sender to `asyncio` (F5) — REJECT

Not in this PR, and I do not think a ticket is warranted from what I can see. "While you are in this package" is a scope change, not a defect in the diff. I could not verify the premise: there is no `async` anywhere in this repo and no convention doc that calls for it. Blocking `time.sleep` is pre-existing (the old fixed-retry sender slept too), and `sleep` is an injected dependency, so an async host can supply its own without a rewrite. If the company convention is documented somewhere I have not seen, point me to it and I will raise a separate ticket.

## Thread 6 — 100/min to 60/min, product sign-off (F6) — NEEDS-INPUT (held open)

Fair question and I cannot answer it from the repo: README, BENCHMARKS.md, the commit, and the PR body record the new default but no decision. I have asked the author to confirm whether product agreed and to link the decision, or to restore 100/min. Leaving this thread open until then; the PR body now says the cap is pending confirmation.

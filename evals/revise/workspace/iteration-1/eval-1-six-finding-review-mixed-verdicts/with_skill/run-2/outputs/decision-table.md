# Decision table (published before any code change)

Counts: 2 ACCEPT, 0 PARTIAL, 3 REJECT, 1 DEFER, 1 NEEDS-INPUT. Thread 4 is split into F4a and F4b, so the thread reads as PARTIAL.

| ID | Finding (reviewer's words, abridged) | Verdict | Evidence and justification |
|---|---|---|---|
| F1 | "`float(retry_after)` will raise `ValueError` on the HTTP-date form" | ACCEPT | Reproduced: `Retry-After: Wed, 21 Oct 2015 07:28:00 GMT` escapes `send` as `ValueError`. An empty value does the same. A negative value reaches `time.sleep`, which raises `ValueError` too. Fix: honor delay-seconds only, fall back to backoff otherwise. |
| F2 | "add validation that raises `ValueError` for `rate <= 0`" | REJECT | `rate` is set by application wiring with a literal. No external writer exists. `Sender` validates none of its five numeric arguments, so no repo convention asks for it. A speculative guard for a state nothing produces. |
| F3 | "buckets live in process memory, needs Redis before it is honest to call it a per-tenant cap" | DEFER | True at `notify/ratelimit.py:16`. Pre-existing: `FixedWindowLimiter._counts` was also per process. The staging run cut 429s from 1,840 to 12 under the real worker layout. Ticket drafted, limitation noted in the PR body. |
| F4a | "docstring says 429 or 503, `_delay` reads the header for every retryable status" | ACCEPT | Reproduced: a 500 with `Retry-After: 7` waits 7 s. RFC 9110 lets a server send the header with any response, so the code is right and the docstring drifted. Fix the docstring. |
| F4b | "should become an explicit `RetryPolicy` class hierarchy" | REJECT | One strategy, one caller. An abstraction for one caller is oversized, and a hierarchy does not stop a docstring from drifting. |
| F5 | "the whole sender should move to `asyncio`" | REJECT | Outside the PR's intent. No `async` anywhere in the repo, and `client.post` is a synchronous interface. No measurement shows a blocked worker. A rewrite of the package API needs its own proposal. |
| F6 | "cap drops from 100 to 60, I cannot tell whether product agreed" | NEEDS-INPUT | Confirmed: `rate=1.0` is 60/min, `docs/BENCHMARKS.md` names three affected staging tenants. No decision is recorded in the repo. Only the author knows. Held. |

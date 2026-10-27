# Revise report: korya-retry-backoff

Counts: 2 ACCEPT, 0 PARTIAL, 3 REJECT, 1 DEFER, 1 NEEDS-INPUT. Thread 4 bundled two findings, split into F4a and F4b, so that thread reads as PARTIAL. Two commits are pushed to origin. One question is open and blocks the cap finding.

## Decision table

| ID | Finding (reviewer's words, abridged) | Verdict | Evidence and justification |
|---|---|---|---|
| F1 | "`float(retry_after)` will raise `ValueError` on the HTTP-date form" | ACCEPT | Reproduced: `Retry-After: Wed, 21 Oct 2015 07:28:00 GMT` escapes `send` as `ValueError`. An empty value does the same. A negative value reaches `time.sleep`, which raises `ValueError` too. Fixed in 33a0889: honor delay-seconds only, fall back to backoff otherwise. |
| F2 | "add validation that raises `ValueError` for `rate <= 0`" | REJECT | `rate` is set by application wiring with a literal. No external writer exists. `Sender` validates none of its five numeric arguments, so no repo convention asks for it. A speculative guard for a state nothing produces. |
| F3 | "buckets live in process memory, needs Redis before it is honest to call it a per-tenant cap" | DEFER | True at `notify/ratelimit.py:16`. Pre-existing: `FixedWindowLimiter._counts` was also per process. The staging run cut 429s from 1,840 to 12 under the real worker layout. Ticket drafted below, limitation added to the PR body. |
| F4a | "docstring says 429 or 503, `_delay` reads the header for every retryable status" | ACCEPT | Reproduced: a 500 with `Retry-After: 7` waits 7 s. RFC 9110 lets a server send the header with any response, so the code is right and the docstring drifted. Fixed in 7c08ea4. |
| F4b | "should become an explicit `RetryPolicy` class hierarchy" | REJECT | One strategy, one caller. An abstraction for one caller is oversized, and a hierarchy does not stop a docstring from drifting. |
| F5 | "the whole sender should move to `asyncio`" | REJECT | Outside the PR's intent. No `async` anywhere in the repo, and `client.post` is a synchronous interface. No measurement shows a blocked worker. A rewrite of the package API needs its own proposal. |
| F6 | "cap drops from 100 to 60, I cannot tell whether product agreed" | NEEDS-INPUT | Confirmed: `rate=1.0` is 60/min, `docs/BENCHMARKS.md` names three affected staging tenants. No decision is recorded in the repo. Only the author knows. Held, code unchanged. |

## Open question (NEEDS-INPUT)

F6: Did product agree to lower the sustained per-tenant cap from 100 to 60 per minute? If yes, give me the link to the decision and I will add it to the PR body and close the thread. If no, say whether to keep 100 per minute, which is `rate=100/60` with the same burst of 20. I will then change the default, the docs and the benchmark table. The thread stays open until then.

## Ticket draft (proposed, not filed)

Title: Share TokenBucketLimiter state across workers

`TokenBucketLimiter` keeps its buckets in process memory (`notify/ratelimit.py:16`). When several workers serve one tenant, each worker grants the full burst and the full sustained rate. The effective cap is the configured cap times the worker count. The fixed window had the same property, so this is not a regression of the retry-backoff PR.

The PR was kept to the limiter's shape, not its storage. A shared store such as Redis adds a dependency and a failure mode that deserve their own design and PR. Staging numbers after the PR show 12 429s per 10k sends, so there is no urgency from the data. Pointer: PR korya-retry-backoff, review thread 3.

## Commits

| Commit | Subject | Finding |
|---|---|---|
| 7c08ea4 | docs(notify): Say Retry-After is honored on any retryable response | F4a |
| 33a0889 | fix(notify): Fall back to backoff when Retry-After is not in seconds | F1 |

The second commit adds two tests. `make test` runs 9 tests, all pass. `make lint` passes.

## Replies

The per-thread replies are in `replies.md` next to this report. This environment has no forge, so they are not posted. Every reply passed `prose-lint.py`.

## Re-submission status

- Pre-push checks: `make test` and `make lint` pass on 33a0889.
- Push: `origin/korya-retry-backoff` is at 33a0889, equal to local `HEAD`.
- PR title: not in the fixture. The branch's first commit subject, "Retry with backoff and throttle tenants with a token bucket", still covers the two new commits.
- PR body: stale in two places. The Retry-After sentence now says the header is honored in its seconds form only, with the fallback. A known-limitation paragraph states the per-process bucket scope. The revised body is in `pr-body.md`, linted, and not posted for lack of a forge.
- CI: unavailable in this environment. Stopped here. The `swd-submit` marker is removed.
- Nothing was marked ready, force-pushed, or merged. No ticket was filed.

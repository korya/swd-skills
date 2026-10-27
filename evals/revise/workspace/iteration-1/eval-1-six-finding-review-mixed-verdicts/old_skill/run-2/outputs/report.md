# Revise report: korya-retry-backoff

**1 ACCEPT · 1 PARTIAL · 2 REJECT · 1 DEFER · 1 NEEDS-INPUT**

| ID | Finding (reviewer's words, abridged) | Verdict | Evidence & justification |
|---|---|---|---|
| F1 | "`float(retry_after)` will raise `ValueError` on the HTTP-date form; escapes `send` instead of `DeliveryError`" | ACCEPT | Reproduced: `ValueError: could not convert string to float: 'Wed, 21 Oct 2015 07:28:00 GMT'` escaped `send`. PR intent says it "honors a Retry-After header"; README promises callers a `DeliveryError`. Fixed in aba2f2e: both RFC 9110 forms parsed, past dates wait 0 s, malformed values fall back to backoff (gateway is a trust boundary). Three tests added. |
| F2 | "no guard against negative or zero `rate`; raise `ValueError` for `rate <= 0`" | REJECT | Behaviour confirmed (`rate=-1` sits at -100 tokens after 100 s). But no writer exists: the only constructors are three test calls (`tests/test_ratelimit.py:10,15,23`); the value is a literal in our own wiring, not a trust boundary. No repo convention validates constructor args (`Sender`, old `FixedWindowLimiter` unguarded). Speculative guard; reconsider if the rate becomes operator/tenant-supplied. |
| F3 | "buckets live in process memory; N workers means N times the cap; needs Redis" | DEFER | True: `_buckets = {}` at `notify/ratelimit.py:15`. Pre-existing: `FixedWindowLimiter._counts` on `main` had the same property, so the diff exposes it rather than introduces it. PR states "No new dependencies". Limitation note added to the PR body; ticket drafted below. |
| F4 | "docstring says 429 or 503 but `_delay` reads the header on every retryable status; make it a `RetryPolicy` hierarchy" | PARTIAL | Drift confirmed (`sender.py:17` vs `:43`). The code matches the PR intent; the docstring was wrong. Fixed in 94b1df2: docstring now says "any retryable response (see RETRYABLE)" and a test pins all five statuses. Hierarchy declined: one strategy, one caller, 12-line loop; a test prevents drift more cheaply than an abstraction. |
| F5 | "move the sender to asyncio; every modern client here is async" | REJECT | Outside the PR's stated intent (backoff + token bucket); changes `Sender.send`'s signature for every caller. Claim unverifiable: zero async code, no architecture doc in the repo. Blocking sleep is correct for a sync worker, and `sleep` is already injectable. Belongs in its own proposal if the direction is real. |
| F6 | "cap drops 100 to 60 per minute; did product agree? link it or keep 100" | NEEDS-INPUT | No decision link in PR body, commit 9ae5e6e, or `docs/BENCHMARKS.md` (which only notes three staging tenants hit the new cap). Only the author/product know. Held: cap left unchanged, thread kept open, flagged as "Open" in the PR body. |

## NEEDS-INPUT (blocking)

1. **F6:** Did product sign off on the sustained per-tenant cap dropping from 100/min (fixed window) to 60/min sustained + burst 20? If yes, give me the decision link to add to the PR body. If no, say whether to restore `rate` so the sustained cap is 100/min (`rate=100/60`) while keeping the token-bucket shape, and whether `docs/BENCHMARKS.md` should be re-measured at that rate.

## Ticket drafts (proposed, not filed)

**Back the per-tenant token bucket with a shared store**

`TokenBucketLimiter` keeps its buckets in a per-process dict (`notify/ratelimit.py:15`), so with N workers serving one tenant the effective cap is N times the configured 60/min. The review of korya-retry-backoff (thread 3) raised this; the previous `FixedWindowLimiter` had the same per-process behaviour, so it is a long-standing limitation rather than a regression.

Deferred because that PR's intent was the backoff and bucket shape with no new dependencies; a shared store (Redis or the gateway's own quota) is a deployment change needing its own design: key layout, clock source, failure mode when the store is unreachable. Decide first whether the deployment actually runs N > 1 workers per tenant; if it does not, close as not needed. Reference: PR korya-retry-backoff, review thread 3.

## Commits made

- `aba2f2e` fix(notify): Honor the HTTP-date form of Retry-After (F1)
- `94b1df2` docs(notify): Say Retry-After applies to every retryable status (F4)

Pushed: `origin/korya-retry-backoff` = `94b1df2`.

## Re-submission status (`/submit` mechanics)

- Phase 0: branch `korya-retry-backoff`, two new commits, tree clean (only `__pycache__` untracked, left alone). Fixture PR body present.
- Phase 3: `make test` (11 tests, OK) and `make lint` pass after each commit.
- Phase 4: pushed; local `HEAD` matches `origin/korya-retry-backoff`.
- Phase 5b: PR body was stale (did not mention the Retry-After date form, the all-retryable-status rule, the per-process limitation, or the open cap decision). Revised body written to `pr-body.md`; title "feat(notify): Retry with backoff and throttle tenants with a token bucket" still covers all the work.
- Phase 6: CI is unavailable in this environment; stopped here. The PR stays a draft; nothing marked ready, no force-push, no tickets filed.

## Replies

Per-thread replies for all six findings are in `replies.md`, including the two rejections with their evidence.

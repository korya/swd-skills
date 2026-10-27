# Revise report: korya-retry-backoff

**2 ACCEPT · 0 PARTIAL · 3 REJECT · 1 DEFER · 1 NEEDS-INPUT** (the reviewer's item 4 was two findings; split into F4a and F4b)

## Decision table (published before any code change)

| ID | Finding (reviewer's words, abridged) | Verdict | Evidence & justification |
|---|---|---|---|
| F1 | "`float(retry_after)` will raise `ValueError` on the HTTP-date form of `Retry-After` ... escapes `send` instead of `DeliveryError`" | ACCEPT | Reproduced: `Retry-After: Wed, 21 Oct 2015 07:28:00 GMT` on a 429 raises `ValueError` out of `send` (`notify/sender.py:45`). Gateway headers are a trust boundary and RFC 9110 §10.2.3 allows both forms, so parsing both is the root fix; an unreadable value falls back to the computed backoff instead of crashing. In scope: honoring Retry-After is what this PR added. |
| F2 | "no guard against a negative or zero `rate` ... add validation that raises `ValueError` for `rate <= 0`" | REJECT | The behaviour is as described (rate=-1 drives tokens to -2.0 in a repro), but `rate` is a constructor argument set by code, not a trust boundary: the only constructions in the repo are the default and three tests (`tests/test_ratelimit.py:10,15,23`); nothing parses it from config or user input. A guard for a state no caller produces is dead code that implies the input can vary. If a config loader ever feeds `rate`, validate at that boundary. |
| F3 | "buckets live in process memory ... with N workers the cap is N×60 ... needs a shared store (Redis)" | DEFER | True: `TokenBucketLimiter._buckets` is a per-process dict (`notify/ratelimit.py:16`). Also pre-existing: `FixedWindowLimiter._counts` on `main` was the same per-process dict, so the diff neither introduces nor widens it. The PR's stated intent is backoff + bucket shape with "No new dependencies"; a Redis store is a different change with its own ops surface. Ticket drafted below; limitation noted in the PR body. |
| F4a | "docstring says Retry-After is honored 'on 429 or 503', but `_delay` reads the header for every retryable status" | ACCEPT | Confirmed: a 500 with `Retry-After: 7` sleeps 7 s. The code is the better behaviour (a gateway that sends the header on 502 means it), the PR body says "honors a Retry-After header" without qualification, and the test only covers 429. Fix the docstring to match the code. |
| F4b | "the retry loop ... should become an explicit `RetryPolicy` class hierarchy with one subclass per strategy" | REJECT | One strategy, one caller, 17 lines of loop. A hierarchy with one subclass is an abstraction for nobody, and it does not prevent docstring drift (the docstring would move, not disappear). Violates no guideline or spec in the repo; exceeds the PR's intent. |
| F5 | "the whole sender should move to `asyncio` ... every modern client in this company is async" | REJECT | Out of scope by the reviewer's own framing ("while you are in this package"). The premise is uncheckable from the repo: zero `async` anywhere, no convention doc. Blocking `time.sleep` is pre-existing (`main` had it too) and `sleep` is an injected dependency, so an async host can already supply its own. If the user confirms the company convention, this is its own ticket, not a rider on a retry fix. |
| F6 | "sustained cap drops from 100 to 60 per minute ... whether product agreed ... link the decision; if not, keep 100" | NEEDS-INPUT | Nothing in the repo (README, BENCHMARKS.md, commit message, PR body) records a product decision; the 60/min figure appears only as the new default. Whether product signed off is knowledge only the author/product has. Held unresolved; question below. |

## Open NEEDS-INPUT questions

1. **F6, cap 100/min to 60/min.** Did product agree to lowering the sustained per-tenant cap from 100 to 60 per minute? If yes, where is the decision recorded so the PR can link it? If no, should `TokenBucketLimiter`'s default `rate` go back to 100/60 per second (and BENCHMARKS.md be re-run at that rate)? Nobody was available during this run, so the item is unresolved; the PR body now states the cap is pending confirmation and review thread 6 stays open.

## Ticket drafts (proposed, not filed)

### Share TokenBucketLimiter state across workers (Redis or equivalent)

`notify.ratelimit.TokenBucketLimiter` keeps its buckets in a per-process dict (`notify/ratelimit.py:16`), so a tenant served by N worker processes can send up to N times the configured 60/min sustained rate before any one process throttles it. The same was true of the `FixedWindowLimiter` it replaced; the per-tenant cap has never been enforced across processes.

Deferred from the retry/backoff PR because it adds a dependency and an operational surface (a shared store, its failure mode when unreachable, and a decision on fail-open vs fail-closed) that the PR explicitly did not take on. Before building: confirm from the deployment how many workers serve one tenant, since with a single worker the gap is zero. Raised on review thread 3 of korya-retry-backoff.

## What changed in the PR

Commits on `korya-retry-backoff`, pushed to origin (`HEAD` = `origin/korya-retry-backoff` = a69b12f):

- `83e25b7` docs(notify): State that Retry-After is honored on every retryable status (F4a)
- `a69b12f` fix(notify): Honor the HTTP-date form of Retry-After instead of crashing (F1; adds `Sender(now=)`, `_retry_after`, three tests)

No change was made for F2, F3, F4b, F5, or F6.

## Re-submission status (`/submit` mechanics)

- Phase 0: branch `korya-retry-backoff`, tree clean, two unpushed commits found; no `gh pr view` possible (no GitHub in this environment, `gh` not used). PR state taken from `fx/pr/body.md`.
- Phase 3: `make lint` and `make test` pass locally (10 tests, up from 7).
- Phase 4: pushed; local `HEAD` matches `origin/korya-retry-backoff`.
- Phase 5b: title still covers the branch (both new commits fall under the backoff/Retry-After feature). Body was stale in two places and is revised in `pr-body.md`: Retry-After now states both forms and the fallback; a known-limitation line (per-process buckets) and a pending-product-confirmation line (cap) were added so the description stays honest. "No new dependencies" remains true (stdlib `email.utils`).
- Phase 6: CI is unavailable in this environment; stopping here. The submit marker was removed.

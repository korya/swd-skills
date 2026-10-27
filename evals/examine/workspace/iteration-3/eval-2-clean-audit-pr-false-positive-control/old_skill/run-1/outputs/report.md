# Examine: Record an audit event on user creation (feature/audit-log vs main)

Mode: **full**, auto-chosen — the change adds a log of user records, and CLAUDE.md's "never
log or store raw emails" rule is load-bearing for it (personal-data trigger). At 4 files /
31 added lines the extra axes cost nothing.

## Headline
**Merge.** No qualifying defect found after two independent passes and runtime probes. One
Low worth folding in on the way (L1: the entry has no timestamp, though the PR's own purpose
is "who was created and when"); everything else is a note or a question.

## Approach fit
Matches the obvious approach — a module-level append-only list on `Store`, written from the
single user-creation path. See Verified for the "already solved by `created_at`?" check.

## Issues

### Low (defer)
- **L1** [`app/audit.py:6`] The entry is `{"event", "user_id"}` only — no time field — so the
  log alone cannot answer the "when" in the stated problem; it is recoverable today only by
  joining `STORE.users[user_id]["created_at"]`. CONFIRMED by probe. One-line fix:
  `record()` stamps `"at": time.time()` (or the caller passes `at=user["created_at"]`).
- **L2** [`tests/test_users.py:9`, `tests/test_billing.py:9-10`] These `setUp`s clear
  `users`/`charges` but not the new `STORE.audit`, so every `create_user` in those modules
  leaks entries into the shared global; harmless today (only `test_audit.py` asserts on it,
  and it clears first), a stale-state trap for the next assertion. Add
  `STORE.audit.clear()` there or give `Store` a `reset()`.

## Questions
- **Q1** [`app/users.py:21`] "Who was created" is recorded as the *created* user's id. Did
  Support mean the *actor* (which agent/admin created the account)? There is no actor
  concept in `api_create_user` (`app/api.py:4-5`), so if they did, this PR cannot supply it.
- **Q2** [`app/support.py:10`] Nothing reads `STORE.audit` — `support.lookup` still returns
  only `id` and `name`. How will Support consume the trail; is a reader a planned follow-up?

## Suggestions

#### S1 — Make the "ids, never emails" rule structural, and test it as a string, not a key
- **Locator:** `app/audit.py:4-6`, `tests/test_audit.py:20`
- **What:** `record()` accepts arbitrary `**fields`; the rule lives in a docstring. The test
  asserts only that no key is named `"email"`, so `record("user.updated", contact=u["email"])`
  passes it. Either reject/strip known PII keys in `record()`, or at least assert the email
  string is absent from `repr(entry)`.
- **Why it'd be better:** CLAUDE.md ("Never log or store raw emails outside the users table")
  is the one invariant this feature can violate; today it holds by caller discipline alone.

#### S2 — Drop the unused `return entry`
- **Locator:** `app/audit.py:8`
- **What:** The only caller (`users.py:21`) discards the return value, and the returned dict
  is the very object stored, so a caller can mutate the "append-only" trail after the fact
  (probe: `e["user_id"] = 999` rewrites `STORE.audit[-1]`). Returning nothing removes the
  mutation vector and a concept. Walked against constraints: no caller or test uses it.
- **Why it'd be better:** Fewer ways to break the trail, no behaviour lost.

## Gaps
- The description says "failure paths covered in tests/test_audit.py"; both tests are
  happy-path (success + privacy assertion). No rule is broken — `docs/testing.md` scopes
  failure-path tests to money and lookup paths, and `record()` has no realistic failure —
  so this is a description-accuracy note: drop the claim or add the S1 negative test.

## Known limitations
- "Append-only" (`app/db.py:13`) is a convention, not a property: the list is a plain
  mutable list and the PR's own tests `clear()` it. Acceptable for an in-memory stand-in;
  revisit when the trail gets a real sink.
- Persist-then-audit is non-atomic (`users.py:20-21`): if `record()` ever raised, the user
  would exist unaudited. `list.append` cannot realistically fail, so not an issue now; the
  ordering matters once the sink can fail.
- `STORE.audit` is unbounded — consistent with every other `Store` collection.

## What was done well
- [`app/users.py:21`] Audits by `user_id` only, honouring CLAUDE.md's email rule, and places
  the call after the record is stored, so an entry never points at a user that does not exist.
- [`tests/test_audit.py:18-20`] Tests the privacy invariant explicitly, not just the happy
  path — the one failure that matters here has a test with its name on it.
- [`tests/test_audit.py` ↔ `app/audit.py`] Mirrors `tests/` to `app/` per `docs/testing.md`;
  `setUp` clears both stores it touches, so the module is order-independent (verified by
  running modules in reverse).
- [`app/db.py:13`] Follows the existing `Store` shape (one collection per concern, commented)
  rather than inventing a new holder; the diff is exactly the four files it claims.

## Verified
- **Problem exists on base:** `main:app/db.py` has `users`/`discounts`/`charges` and no
  event record; nothing on main records creation events.
- **"Already solved?"** `users[id]["created_at"]` already answers "when" for live records,
  which is why L1 is Low. The log is still justified by the constraint stated in the
  description — a *trail* (append-only, independent of the record's lifecycle, extensible
  to other events) — so the approach gate passes.
- **No behaviour change for existing callers:** `create_user`'s return value and
  `STORE.users` contents are unchanged; main's 3 tests pass unmodified on the branch; the
  full branch suite (5 tests) passes; also passes with reversed module order.
- **No raw email in entries:** probe with `"  Foo@Example.COM "` → entry
  `{'event': 'user.created', 'user_id': 1}`, email absent from `repr(STORE.audit)`.
- **REFUTED — kwargs collision:** `record("x", event="y")` raises `TypeError` (verified), but
  the only call site (`users.py:21`) passes `user_id` only; latent API wart, not a defect.
- **REFUTED — import cycle:** `users → audit → db`; `audit` does not import `users`.
  `python3 -c 'import app.audit, app.users, app.api'` succeeds in any order.
- **REFUTED — missing migration (`docs/invariants.md §3`):** `Store` is in-memory and
  constructed in `__init__`; `migrations/001_init.py` is a no-op and `discounts` was added
  with no migration either. Precedent and mechanism both say none is needed.
- **Load-bearing assumption checked at the interpreter:** `{"event": event, **fields}` cannot
  silently override `event` — Python rejects the duplicate at the call (TypeError) before the
  dict is built.
- **Top-3 production risks and coverage:** (1) PII reaching the trail — covered by
  `test_audit_entries_carry_no_email` (key-level; S1 strengthens it); (2) regression in
  `create_user` — covered by `test_users` and the unchanged base suite; (3) stale
  cross-module test state — uncovered, that is L2.
- **Reversibility:** additive only; revert is one import, one call, one attribute, two files.
  No external side effects.
- **Dependencies:** none added.
- **Host built-in review** (`code-review high`, run in a subagent against an identical diff)
  produced the same six candidates as above; nothing it found was promoted above Low.

## Not reviewed
- Pre-existing code outside the diff, noted only in passing: `app/billing.py:19` uses a float
  in a money path (`docs/invariants.md §2`) and `app/db.py:19` puts the raw email in a
  `NotFound` message. Not introduced here; worth their own ticket.
- No `docs/architecture.md`, `docs/privacy.md`, or `docs/security.md` exist; the diff needs
  none beyond CLAUDE.md's email rule, which was applied.
- No CI (no remote, no PR); test evidence is from local runs on exported snapshots.
- Primary checkout untouched: still `feature/discounts` @ `a5da64b`, clean tree, before and
  after. All runs happened in scratchpad copies, since removed.

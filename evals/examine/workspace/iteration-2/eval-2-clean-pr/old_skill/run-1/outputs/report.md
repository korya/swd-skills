# Examine: feat(audit): Record an audit event on user creation (`feature/audit-log` vs `main`)

**Target:** `git diff bebb97e2..86f6d9b` (merge-base of `feature/audit-log` and `main`; branch is one commit ahead; no working-tree changes — the primary checkout sits on `feature/discounts`, untouched).
**Mode:** full — auto-chosen because the diff touches personal-data handling (an audit trail written under the CLAUDE.md "never store raw emails outside the users table" rule). The diff is 4 files / +31 lines, so full mode was cheap.
**Description source:** the branch's commit message (no linked ticket).

## Headline

**Merge with fixes.** The change is right-sized and does what it says, but the audit entry records *who* and not *when* — half of the stated requirement — and the privacy rule the description leans on is enforced by a docstring and a key-name test, not by the API. Both are ten-line fixes.

## Approach fit

Matches the obvious approach — a dedicated `app/audit.py` sink writing to a new `STORE.audit` list, called once from `create_user` (my sketch B; see Verified). Nothing in the diff goes beyond that sketch.

## Issues

### Medium (worth fixing now; acceptable as a follow-up)

#### M1 — Audit entries carry no timestamp, so the trail cannot answer "when"
- **Locator:** `flow: app/users.py:21 → app/audit.py:6`
- **What:** The stated problem is "a trail of who was created *and when*." `record()` builds `{"event": event, **fields}` and the only caller passes `user_id` only, so the persisted entry is exactly `{'event': 'user.created', 'user_id': N}`. `time.time()` is captured at `app/users.py:18` into the user row but never into the audit entry.
- **Evidence:** Probe on the PR branch: `sorted(STORE.audit[0].keys()) == ['event', 'user_id']`. After `STORE.users.clear()`, `STORE.users.get(entry['user_id'], {}).get('created_at')` is `None` — the trail alone has no time axis; ordering exists only by list position. `tests/test_audit.py:12-16` asserts `event` and `user_id` only, so nothing would catch this.
- **Verdict:** CONFIRMED — independent verifier reproduced the entry shape and confirmed no reader or join path exists (`app/support.py` never touches `audit`).
- **Why Medium:** Wrong behaviour against the stated requirement rather than a crash: today the "when" is recoverable by joining `user_id` back to `STORE.users[id]["created_at"]`, and no production path deletes users yet (only `.clear()` in test `setUp`), so nothing breaks on deploy. But an audit trail without timestamps is an audit trail in name only, and the join is not code anyone wrote.
- **Fix:** Stamp inside the sink so every event gets it for free: `entry = {"event": event, "at": time.time(), **fields}` in `app/audit.py:record` (or pass `at=user["created_at"]` from `create_user` so the two agree exactly). Extend `test_user_creation_is_audited` to assert the key.
- **Cites:** the commit message's own problem statement ("who was created and when"); no project doc covers audit content.

#### M2 — "Never raw emails" is enforced by a docstring; the test checks a key name, not the value
- **Locator:** `flow: app/audit.py:4-7 → tests/test_audit.py:18-20`
- **What:** `record(event: str, **fields)` accepts any keyword and appends it verbatim; the only guard is the docstring "Callers pass ids, never raw emails." The one test for the rule asserts `"email" not in STORE.audit[0]` — an entry `{'event': ..., 'user_id': 1, 'contact': 'a@b.c'}` passes it. The description cites this rule as a design property of the change; the code does not make it one.
- **Evidence:** Probes on the PR branch: `audit.record('user.created', user_id=1, email='leak@example.com')` is stored verbatim; the test's assertion replayed against `{'event': 'x', 'user_id': 1, 'contact': 'a@b.c'}` returns True. `app/billing.py:13` (`charge(email, ...)`) is the obvious next caller and already holds a raw email in scope. The current call site `app/users.py:21` is compliant (id only).
- **Verdict:** CONFIRMED (as a guard-strength gap — the diff itself does not violate the rule) — independent verifier reproduced both probes and confirmed no redaction helper exists in `app/util.py`.
- **Why Medium:** A maintenance trap with a citable cost: the sink is the one place the project's privacy rule can be made structural, and the generic `**fields` API plus a key-name test invite the next caller to violate it silently. Not High because no violation ships in this diff.
- **Fix (Occam-preferred):** Narrow the signature instead of adding a guard — `def record(event: str, *, user_id: int) -> dict`. One caller, one field; the rule then holds by construction and `**fields` generality is speculative today (see Occam notes under Verified). If the open field set is genuinely wanted, allowlist keys (`{"user_id"}`) and raise on anything else. Either way, strengthen the test: `self.assertNotIn("a@b.c", repr(STORE.audit[0]))` and add a direct test that `record` rejects an `email=` field — which would also make the description's "failure paths covered" claim true (L1).
- **Cites:** `CLAUDE.md` line 4 — "Never log or store raw emails outside the users table; reference users by id."

### Low (defer)
- **L1** [scope: PR] The description says "failure paths covered in tests/test_audit.py"; both tests there are happy-path (creation is recorded; key `email` absent). `docs/testing.md` mandates failure-path tests only for money and lookup paths, so no rule is broken — but the description overclaims. Fixing M2 adds a real failure-path test.
- **L2** [`app/audit.py:8`] `record()` returns the very dict it appended, so `e = record(...); e["user_id"] = 999` rewrites `STORE.audit[-1]` in place. The return value is unused by `create_user`; drop it or return a copy.

## Questions

- **Q1** [`app/support.py`] Support asked for this trail, yet nothing reads `STORE.audit` — is a `support.recent_creations()` (or similar) reader planned as the follow-up, or is the trail meant to be inspected out-of-band?
- **Q2** [`app/billing.py:22`] Is `charge` intended to emit a `charge.created` event in this series? It is the natural sibling and the one caller that holds a raw email — the answer decides how much of M2's fix belongs in this PR versus the next.

## Suggestions

#### S1 — A single `Store.reset()` used by every `setUp`
- **Locator:** `app/db.py:9-13`, `tests/test_users.py:9`, `tests/test_billing.py:9-10`, `tests/test_audit.py:8-10`
- **What:** `create_user` now writes to two stores, but `test_users.py` and `test_billing.py` `setUp` clear only `users` / `charges`; each test module hand-picks which lists to reset. A `Store.reset()` that clears all attributes (and could reset the `_ids` counter) removes the asymmetry.
- **Why it'd be better:** Every future store attribute is reset in one place; no test module can forget one. Today the asymmetry is harmless because `test_audit.setUp` clears `audit` itself.

#### S2 — Test `record()` directly, not only through `create_user`
- **Locator:** `tests/test_audit.py`
- **What:** Both tests drive `users.create_user`; a regression in `record`'s field handling is caught only via that one caller. One direct test (entry shape incl. timestamp after M1; rejection of a disallowed field after M2) pins the sink's contract.
- **Why it'd be better:** `docs/testing.md` says `tests/` mirrors `app/`; `test_audit.py` nominally does, but currently tests `users`, not `audit`.

## Gaps

- `tests/test_users.py:9` and `tests/test_billing.py:9-10` do not reset `STORE.audit`, so the audit list accumulates entries across modules during a test run. No test observes it today; S1 covers it.

## Known limitations

- **Append-only by convention.** `STORE.audit` is a plain list: tests `.clear()` it, entries are mutable dicts (L2). Acceptable for an in-memory stand-in ("Tiny in-memory store standing in for a database", `app/db.py:1`) — worth one comment at `app/db.py:13` so nobody mistakes it for a tamper-evident log.
- **Unbounded growth.** The list grows with every user creation and is never evicted — exactly the behaviour `charges` already has. Only matters once the store is backed by something real; no `docs/privacy.md` retention policy exists to cite.

## What was done well

- [`app/users.py:21`] Audit call placed *after* the store write and passes only `user["id"]` — the CLAUDE.md id-not-email rule is honoured at the one call site that exists.
- [`app/audit.py:5`] The privacy rule is stated in the docstring at the sink, which is the right place for it even if it needs code behind it (M2).
- [`tests/test_audit.py:18-20`] A test exists *specifically* for the privacy rule. Weak (M2), but the intent to lock the rule under test is the right instinct.
- [`tests/test_audit.py:8-10`] `setUp` resets both stores the code under test touches — no cross-test leakage inside this module.
- [`app/users.py:4`] Import chain `users → audit → db` is acyclic; the sink depends only on the store.
- [commit message] States problem, approach, constraints ("additive only, no migration, no behaviour change") and cites the project rule it designs around. Reviewable in one read — rare enough to say so.

## Verified

- **Problem is real in the base snapshot:** `bebb97e2:app/users.py` has no audit hook and nothing in the base tree records creation events; the closest thing is `created_at` on the user row itself, which is state, not a trail.
- **Approach vs sketches:** (A) inline append in `create_user`; (B) dedicated `audit` module + `STORE.audit`, called from `create_user`; (C) no log — derive "who/when" from `STORE.users[*]["created_at"]` via a support view. The diff is (B); the extra module over (A) is justified as the single sink where the privacy rule can be enforced. (C) was rejected on the description's own terms (append-only trail wanted).
- **"No behaviour change for existing callers":** `create_user`'s return value and `api.api_create_user` are unchanged; full suite passes 5/5 on the PR branch (`python3 -m unittest discover tests -v`, Python 3.14.7, in a detached worktree).
- **"No migration needed":** REFUTED the host reviewer's candidate that `Store.audit` violates `docs/invariants.md §3`. §3 governs migrations; none is added. Precedent: `self.discounts = {}` already exists at the base commit with no migration, and `migrations/001_init.py` `up()` is a no-op stub — store attributes in this fixture are constructed in code.
- **Partial-write candidate REFUTED:** "user stored but `audit.record` raises, leaving no entry" — `list.append` on CPython raises only `MemoryError`; no realistic failure window between `app/users.py:20` and `:21`.
- **Kwarg collision (language pitfall, 5c.3):** `record("x", event="y")` raises `TypeError: got multiple values for argument 'event'` rather than silently overriding — checked against the Python 3.14 runtime (the outside source for this load-bearing assumption).
- **No circular import:** `import app.audit; import app.users; import app.api` succeeds.
- **Current call site is compliant with CLAUDE.md line 4** (id only) — both verifiers confirmed.
- **Top 3 production risks and coverage:** (1) trail cannot answer "when" — uncovered → M1; (2) a future caller stores an email — covered only by a key-name test → M2; (3) `create_user` fails after storing the user — refuted above, no test needed.
- **Reversibility (5l):** purely additive, in-memory, no external side effects; `git revert` restores the base cleanly. No flag needed.
- **Occam pass:** walked against the constraints "additive, no migration, no behaviour change" and CLAUDE.md line 4. The only over-general element is `**fields` (one caller, one field) — folded into M2's fix as the simpler alternative to a guard. The separate module is not a deletion candidate: collapsing it into `users.py` would lose the one place the rule can be enforced. No reinvention (no existing logging utility in `app/util.py`), no band-aid.
- **Verification process:** two Medium candidates verified by independent subagents given only the diff, files, and candidate; the host's defect-first `code-review` skill ran in a subagent as an extra candidate source (its first invocation targeted the wrong repo due to inherited cwd and was discarded; the second targeted the worktree). Gap sweep ran; it produced only the `setUp` asymmetry already listed.

## Not reviewed

- **5e Architecture:** no `docs/architecture.md`; layering (`users → audit → db`, sink beside its callers) has no rule to cite and looks unremarkable.
- **5g Security:** no new trust boundary, input, endpoint, or secret; the only input still enters via `api.api_create_user` unchanged.
- **5h Data privacy:** no `docs/privacy.md`. The diff stores only a pseudonymous `user_id` and an event name — judged against CLAUDE.md line 4 and GDPR Art. 5(1)(c) (data minimisation): compliant. Retention is unbounded (Known limitations); no policy exists to cite.
- **5m Dependencies:** none added or bumped.
- **CI:** no PR host / `gh` checks available for a local branch; the local test run stands in.
- **`feature/discounts`** (the branch the primary checkout is on) — unrelated to this review; not read beyond noting it is the checked-out branch.

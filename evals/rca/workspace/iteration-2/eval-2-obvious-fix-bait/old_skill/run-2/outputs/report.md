# RCA: user search misses customers whose stored email differs in case

## Headline

The requested one-line patch to `app/search.py` fixes the ticket and leaves three siblings
live. The root cause is not in search: `app/db.py` stores email exactly as typed
(`insert`, db.py:26) and compares it byte-for-byte (`find_by_email`, db.py:34), and all
four email-keyed flows (search, signup, invite, password reset) go through that one
function. Recommended: normalize email in `db.py` at both write and read, plus a backfill of
existing rows. The fix is still small (one file, ~8 lines) and it kills the class.

I did not apply either patch to `fixture/`; both were prototyped in a scratchpad copy and
the fixture is unchanged at its baseline (checksums below).

## Symptom and scope

- **What support sees:** the internal user-search tool returns `not_found` for customers
  who exist (visible in Stripe, billed). Workaround: page the data team for a SQL lookup,
  5-10 min per ticket.
- **Log (BUG_REPORT.md), verbatim:**
  ```
  2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
  2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
  2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
  ```
  Same customer, three casings, exactly one matched.
- **Scope:** every lookup whose casing differs from what the user typed at signup. First
  seen 2026-05-12, four agents in 24h, severity P2.
- **Expected:** `search_by_email("bob@example.com")` finds the user who signed up as
  `Bob@Example.COM`. **Actual:** `{'status': 'not_found'}`.

### Repro

Deterministic, in the repo:

```
python3 -m unittest tests.test_search.SearchTests.test_search_finds_user_signed_up_with_mixed_case -v
# AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
```

Full suite: 2 tests, 1 failure (the mixed-case one; the lowercase one passes).

### Baseline (working tree)

The fixture is a plain directory (no VCS). Baseline recorded as SHA-1 of every source file
before investigation; all nine are unchanged at the end (see "Trace left").

## Timeline

No commit history exists for the fixture, so `git log` is unavailable. What the code itself
says: the behaviour is **designed, not regressed**:

- `app/db.py:1` docstring: `"""In-memory user store. Case-sensitive lookups by email."""`
- `app/signup.py:1` docstring: `"""Signup flow. Stores email as the user typed it."""`

Nothing in the code changed to cause this; what is new is the **input**: support agents
typing emails from tickets, where the casing is whatever the agent or the customer's email
client produced. Until agents started doing that at volume, the only lookup path with a
different casing from signup was rare.

## 5-whys chain

1. **Why did search return `not_found` for an existing customer?**
   - **Answer:** `search_by_email` delegates to `db.find_by_email`, which returned `None`.
   - **Evidence:** `app/search.py:7-9`; probe on untouched fixture:
     `search lower : {'status': 'not_found'}` after `signup("Bob@Example.COM")`.

2. **Why did `find_by_email` return `None`?**
   - **Answer:** It compares with `u.email == email`, a case-sensitive string equality, and
     the stored value was `Bob@Example.COM` while the query was `bob@example.com`.
   - **Evidence:** `app/db.py:32-36`; probe: `search exact : {'status': 'ok', ... 'email':
     'Bob@Example.COM'}` (same user, exact casing, found).

3. **Why does the stored value carry the user's casing?**
   - **Answer:** `insert` stores the string it is handed; `signup` hands it the raw input.
     No layer normalizes email before storage.
   - **Evidence:** `app/db.py:26` `User(id=_NEXT_ID, email=email, name=name)`;
     `app/signup.py:15` `db.insert(email=email, name=name)`; `grep -rn "lower\|casefold\|
     strip" app/` returns nothing.

4. **Why is there no normalization layer?**
   - **Answer:** The store's contract was written as case-sensitive on purpose, and the
     contract is only a docstring, so nothing (type, constraint, test) forces callers to
     agree on a canonical form. Each flow passes raw input and trusts equality.
   - **Evidence:** `app/db.py:1`, `app/signup.py:1` docstrings; `User.email` is a bare `str`
     (`app/db.py:10`); no uniqueness check beyond the same `find_by_email` call
     (`app/signup.py:13`).

5. **Why does a docstring-only contract cause a production bug?**
   - **Answer:** Email identity is a cross-cutting invariant ("one account per address,
     findable by that address") but it is owned by no module. Four callers independently
     assume `find_by_email` means "find the account for this address", which is true only
     when the caller's casing happens to match signup's.
   - **Evidence:** `grep -rn find_by_email app/` -> `search.py:7`, `signup.py:13`,
     `invite.py:7`, `password_reset.py:11`, each passing raw caller input.

Stop here: a fix at link 4/5 (the store owns normalization) prevents every sibling in link
5. A fix at link 1 (search) prevents only the reported instance.

## Classification

| Label | What |
|---|---|
| **Symptom** | Support search returns `not_found` for a real customer. |
| **Proximate cause** | `app/db.py:34` `u.email == email` is case-sensitive while stored emails are mixed-case. |
| **Root cause** | Email normalization has no owner: the store accepts and compares raw strings, and the "case-sensitive" rule lives only in a docstring, so every email-keyed flow silently inherits a different definition of identity than the users have. |

### Falsification of the root

- **If it were wrong, we would see:** `not_found` on exact-casing lookups too (some other
  mismatch: whitespace, unicode, user genuinely absent from this store).
- **Second mechanism producing the same symptom:** trailing/leading whitespace in the
  query, or the customer existing in Stripe but never in `users`.
- **Disconfirming experiment, run:** exact-casing lookup for the same user succeeds
  (`search exact : ok`, log line 3 `Jane.smith@gmail.com -> ok id=8412`). The one variable
  between success and failure is casing. Whitespace is a real additional hazard (probe:
  `" Bob@Example.COM "` -> `not_found`) but is not what the log shows.
- **Not ruled out:** that some production `not_found`s are customers who truly are not in
  `users` (Stripe-only). The log excerpt rules it out for the reported case only.

## Siblings

All confirmed by probe on the untouched fixture (`signup("Bob@Example.COM")`, then act with
`bob@example.com`):

| Sibling | Path | Observed | Severity |
|---|---|---|---|
| Password reset fails for the customer | `app/password_reset.py:11` | `ResetError no such user` | **High**: locks real users out of their own accounts |
| Duplicate account created | `app/signup.py:13` | second signup `ALLOWED -> User(id=2, email='bob@example.com')` | **High**: identity split, billing/notification ambiguity, and it poisons any later case-insensitive lookup (which of the two?) |
| Invite sent to existing member | `app/invite.py:7` | `{'status': 'invite_sent'}` instead of `already_member` | Medium |
| Data already written | the real `users` table | every row stores as-typed casing; any case-duplicate accounts already created are latent | **Must be checked** (query below) |

The user's search-only patch fixes none of these, and the duplicate-signup sibling makes the
search patch non-deterministic: with two rows differing only by case, a `.lower()` compare
returns whichever was inserted first (probe B: `search w/ dups` returned id=1 by position).

## Assumptions

1. **Assumption:** `db.find_by_email` is the only email lookup; no caller compares
   `.email` directly.
   - **How validated:** `grep -rn "find_by_email\|\.email\|email ==" app tests`.
   - **Result:** Confirmed; the only direct `.email` reads are the comparison in db.py:34
     and the response field in search.py:10.
2. **Assumption:** `db.insert` is the only write path, so normalizing there covers all
   stored emails going forward.
   - **How validated:** grep for `_USERS` and `insert(` in `app/`.
   - **Result:** Confirmed (`db.py` only).
3. **Assumption:** Case-insensitive matching is the desired business rule.
   - **How validated:** BUG_REPORT.md "What support is asking": fix the search or tell us
     the rule; `tests/test_search.py:23-29` encodes case-insensitive as expected behaviour.
     RFC 5321 technically allows a case-sensitive local part, but no mainstream provider
     honours it.
   - **Result:** Confirmed for the product; flagged as the one business decision the fix
     encodes (see open questions).
4. **Assumption:** Normalizing on write does not break the search response contract.
   - **How validated:** search.py:10 returns `user.email`; after normalization it returns
     the lowercase form rather than as-typed.
   - **Result:** Confirmed as a behaviour change, benign for support tooling; noted.
5. **Assumption:** Production has no, or few, case-duplicate accounts already.
   - **How validated:** Cannot be validated in the fixture (in-memory, starts empty).
   - **Result:** **UNVERIFIED**. The code fix does not depend on it; the backfill plan does.
     Open question with a concrete query below.

## Fix proposals

### A. Symptom fix: what was asked for

The literal instruction, `email.lower() == u.email.lower()` in `app/search.py`, cannot be
applied as a one-line edit: search.py has no `u`; it calls `db.find_by_email`. Making it
work means search.py grows its own scan over `db.all_users()` and bypasses the store's
lookup:

```python
# app/search.py
user = next((u for u in db.all_users() if email.lower() == u.email.lower()), None)
```

- **Tests:** the existing failing test passes (prototype B: `OK`, 2/2).
- **Blast radius:** search only.
- **Rollback:** revert one line.
- **Survivors (probe B):** password reset still fails, duplicate signup still allowed,
  invite still misfires, and search becomes order-dependent once duplicates exist. It also
  forks the definition of "same email" between search and the rest of the system, which is
  exactly the root cause restated.

### B. Root-cause fix: the store owns normalization (recommended)

One file, `app/db.py`, prototyped and verified (prototype C):

1. Add `normalize_email(email) -> str` returning `email.strip().lower()`.
2. `insert`: store `normalize_email(email)` (db.py:26).
3. `find_by_email`: compare against `normalize_email(email)` (db.py:34).
4. Replace the db.py docstring with the invariant: emails are stored normalized, lookups
   normalize, at most one user per normalized email.
5. `app/signup.py:1` docstring: drop "Stores email as the user typed it".
6. **Backfill** (production, not the fixture): `UPDATE users SET email = lower(trim(email))`,
   preceded by the duplicate check in open question 1, since the update will collide on any
   pre-existing case-duplicates.

- **Tests:** existing suite 2/2 (`OK`); add the tests in Prevention.
- **Blast radius:** all four flows change behaviour, in the direction support asked for.
  `search_by_email` now returns the normalized email rather than as-typed.
- **Rollback:** revert db.py; stored data is already lowercase so the old code keeps
  working for lowercase queries (strictly better than before rollback).
- **Siblings repaired (probe C):** reset issues a token, duplicate signup is rejected,
  invite reports `already_member`, whitespace variants match.

**Recommendation: B.** It is barely larger than A (eight lines in one file versus one line
in another), the existing test passes either way, and A leaves two High-severity siblings
and actively makes one of them worse. If speed is the concern, B is as fast to ship; the
only genuinely extra work is the backfill, and that work exists whether or not we do it now.

## Counterfactual

- **Fix B against the captured repro:** `signup("Bob@Example.COM")` stores
  `bob@example.com`; `search_by_email("bob@example.com")` normalizes to the same string;
  `find_by_email` matches. Repro does not fire. **Breaks links 2, 3 and 4** (comparison,
  storage, missing layer). Against the log: all three Jane.Smith casings normalize to
  `jane.smith@gmail.com` and match id=8412. **Confirmed**; verified by running the suite
  and the probe on prototype C.
- **Fix A against the captured repro:** does not fire for search. **Confirmed with
  survivors:** password reset, duplicate signup, invite (listed above).

## Prevention

- **Tests (floor):** in `tests/`, one case per flow with mixed-case and whitespace-padded
  input: `test_password_reset_is_case_insensitive`, `test_signup_rejects_case_duplicate`,
  `test_invite_detects_existing_member_any_case`, plus a `normalize_email` unit test. The
  probe script in this investigation is a ready-made skeleton.
- **Guardrail (make the class inexpressible):** enforce the invariant in the type, not the
  docstring. `User.__post_init__` asserts `self.email == normalize_email(self.email)` so a
  non-normalized email cannot be constructed; in the real database, a `UNIQUE` index on
  `lower(email)` (or a `citext` column) so a case-duplicate cannot be inserted even by a
  path that bypasses `insert`.
- **Doc:** the db.py invariant docstring from fix B; if the repo has an `AGENTS.md` or
  architecture doc, add "email is an identity key; it is normalized by the store, never by
  callers".

## Open questions

1. **Are there case-duplicate accounts in production already?** Run before the backfill:
   `SELECT lower(email), count(*) FROM users GROUP BY 1 HAVING count(*) > 1`. If any,
   they need a merge decision (which id survives, what happens to billing linked to the
   other), which this RCA cannot make.
2. **Business rule confirmed?** Fix B encodes "email identity is case-insensitive and
   whitespace-trimmed". The bug report asks for it; someone who owns the product should say
   yes. `strip()` is my addition beyond the ticket; drop it if unwanted.
3. **Display casing.** After B, `search_by_email` returns the lowercase email. If any UI
   wants the as-typed form, it needs a separate `display_email` column; nothing in this
   repo does.

## Trace left

Nothing. Prototypes A and B were built in the scratchpad
(`/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/rca-e2r2/`),
not in the fixture. Fixture source checksums match the baseline recorded at step 1 (verified
by re-running `shasum` after the investigation; see transcript). Nothing pushed, published,
or sent.

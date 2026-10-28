# RCA: support search cannot find customers by email

Support search returns "not found" unless the agent types the email in the exact casing the customer used at signup.
The root cause is that the user store has no canonical form for email, so every flow compares the raw typed string.
Fix it in `app/db.py` with one normalized email key for lookup and insert, not with a one-line change in `app/search.py`.

## Why not the one-line patch as asked

The requested line does not fit `app/search.py`. That file has no comparison. It calls `db.find_by_email()`, and the comparison lives at `app/db.py:34`.

Two placements of the one-liner are possible, and both fall short:

- **In `app/search.py`.** Search must then scan `db.all_users()` itself and bypass the store. Probe P5 shows that search works, but password reset and invites stay broken.
- **At `app/db.py:34`.** This fixes all four flows that look up by email. It does not stop new case-only duplicates at insert. It also makes existing duplicates ambiguous, because the first match wins (probe P6).

I did not ship anything. Shipping is visible to others and needs your approval during this investigation. The patch plan is below.

## Symptom and scope

Support agents search for a customer by email and get `not_found` for a customer who exists. The bug report quotes three searches for one customer:

```
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

- **Who.** Customer support agents. Four agents reported it in 24 hours.
- **Since when.** First seen on 2026-05-12, per `BUG_REPORT.md`.
- **Cost.** Support reports 5 to 10 minutes lost per ticket. Agents page the data team as a workaround.
- **Expected.** Any casing of the address finds the customer.
- **Actual.** Only the casing stored at signup finds the customer.

**Repro.** `python3 -m unittest discover tests -v` fails `test_search_finds_user_signed_up_with_mixed_case` with `'not_found' != 'ok'`. Probe P1 reproduces the three log lines exactly. Only `Jane.smith@gmail.com` returns `ok`.

**Workspace.** I worked in the copy at `outputs/fixture`. Git ignores that path (`evals/rca/.gitignore:1`), so the baseline is a SHA-1 checksum of every source file. The repo worktree was on branch `korya-rca-simplify` at `0694414`.

## Timeline

The case-sensitive behaviour is part of the design from the first version. No change introduced it.

- The fixture has one commit, `a1c647a`, which added the whole app at once.
- `app/db.py:1` documents the contract as "Case-sensitive lookups by email."
- `app/signup.py:1` documents "Stores email as the user typed it."

The bug therefore predates every change. The new factor must be in the inputs. I do not know what changed around 2026-05-12. A new signup source that keeps capital letters would explain it, but I have no evidence for that. See the open questions.

## 5-whys chain

1. **Why did support search return `not_found` for Jane?**
   - **Answer:** `db.find_by_email()` returned `None`, and search maps `None` to `not_found`.
   - **Evidence:** `app/search.py:7-9`. Probe P1 returns `not_found` for two of the three logged casings.

2. **Why did `find_by_email()` return `None`?**
   - **Answer:** It compares the query and the stored email with raw string equality.
   - **Evidence:** `app/db.py:34` has `if u.email == email`. The exact stored casing returns `ok` in log line 3 and in probe P1.

3. **Why does the stored casing differ from what support types?**
   - **Answer:** Signup stores the address exactly as the customer typed it.
   - **Evidence:** `app/signup.py:15` passes the raw `email` to `db.insert()`. `app/db.py:26` stores it unchanged.

4. **Why does neither the write nor the read normalize the address?**
   - **Answer:** The store has no canonical form for email. It uses the display string as the identity key, and each caller passes raw input.
   - **Evidence:** `grep -rn find_by_email app/` finds four callers. None of them normalize. `app/db.py` has no normalize function.

5. **Why did nothing catch the gap?**
   - **Answer:** The store enforces no uniqueness on a normalized key, and no test covers mixed case outside search.
   - **Evidence:** `app/db.py:24-29` inserts without a check. Probe P2 accepts `bob@example.com` after `Bob@Example.COM`. `tests/` holds only `test_search.py`.

## Symptom, proximate, root

| Label | Cause |
|---|---|
| Symptom | Support search returns `not_found` for an existing customer. |
| Proximate cause | `app/db.py:34` compares emails with raw `==`. |
| Root cause | The store has no canonical email key. Insert and lookup both use the typed string, and no uniqueness check exists on a normalized form. |

**Falsification.** If case were not the cause, the exact stored casing would also fail, or a normalized compare would still fail.

- **Experiment run.** With a normalized key in `app/db.py`, both tests pass. All three logged casings resolve to the same user.
- **Second mechanism.** Leading or trailing spaces and Unicode lookalike characters also produce `not_found`. The three logged queries differ only in letter case, so case explains this ticket.
- **Limitation.** I have not ruled out whitespace or lookalike variants in other tickets. I saw only one log excerpt.

## Siblings

All four flows that look up a user by email share the same comparison at `app/db.py:34`.

| Flow | Behaviour today | Evidence | Severity |
|---|---|---|---|
| Signup duplicate check | Accepts `bob@example.com` after `Bob@Example.COM` and creates a second account. | `app/signup.py:13`, probe P2 | High. It corrupts data. |
| Password reset | Raises `no such user` for a different casing. The customer cannot reset. | `app/password_reset.py:11`, probe P3 | High |
| Team invite | Sends an invite to an existing member. | `app/invite.py:7`, probe P4 | Medium |
| Support search | The reported bug. | `app/search.py:7` | Medium (P2 per the ticket) |

**Data already corrupted.** Signup has allowed case-only duplicates for as long as it has existed. The fixture store is in memory, so I cannot count them. Production needs this read-only query before any fix ships:

```sql
SELECT lower(email) AS key, count(*) FROM users GROUP BY 1 HAVING count(*) > 1;
```

**Duplicates make a naive fix ambiguous.** After a case-insensitive lookup, the first match wins. In probe P6, a reset for `bob@example.com` returns the token for user 1. User 2 owns that exact casing.

## Assumptions

1. **Assumption:** Every email lookup goes through `db.find_by_email()`.
   - **How validated:** `grep -rn "find_by_email\|\.email ==" app/` finds four callers and one comparison, at `app/db.py:34`.
   - **Result:** Confirmed.

2. **Assumption:** Email identity must be case-insensitive for the whole address.
   - **How validated:** You state it, and the support ticket expects it. RFC 5321 permits a case-sensitive local part, but mainstream providers ignore case.
   - **Result:** Confirmed as the product requirement. The RFC case is a residual risk.

3. **Assumption:** The production `users` table has no case-only duplicates.
   - **How validated:** None. Probe P2 shows that signup permits them.
   - **Result:** UNVERIFIED. The recommended fix does not rest on it, because the plan runs the audit first and handles either result.

4. **Assumption:** `str.lower()` is the right normalization.
   - **How validated:** Probe P7. `lower()` and `casefold()` differ on `ß`. Only `casefold()` matches `straße` with `STRASSE`.
   - **Result:** UNVERIFIED. The fix rests only on one shared function. The choice of function must match any database index. See the open questions.

5. **Assumption:** Support must still see the address as the customer typed it.
   - **How validated:** `app/search.py:10` returns `user.email`. The fix keeps `email` as typed and adds a separate key.
   - **Result:** Confirmed. Probe P1 after the fix returns `Jane.smith@gmail.com` for every casing.

## Fix proposals

### Proposal A: symptom fix

Change `app/db.py:34` to `if u.email.lower() == email.lower():`. This is your one-liner, at the line where the comparison lives.

- **Files.** `app/db.py`.
- **Tests.** The existing repro test passes.
- **Blast radius.** All four flows. Search, reset, invite, and the signup duplicate check become case-insensitive.
- **Gaps.** Existing duplicates resolve to the first match. No guardrail stops a future caller from comparing raw strings. Each lookup lowercases every stored row.
- **Rollback.** Revert the line.

### Proposal B: root-cause fix (recommended)

Give the store one canonical email key and use it for both insert and lookup.

- **Files.** `app/db.py`, plus new tests. `app/search.py`, `app/signup.py`, `app/password_reset.py`, and `app/invite.py` need no change.
- **Approach.** Add `normalize_email()`. Store `email_key` beside the typed `email`. Compare on `email_key` in `find_by_email()`. Reject a duplicate key in `insert()`.
- **Tests.** One mixed-case test per flow. See Prevention.
- **Blast radius.** Every user lookup and every signup. Signup rejects case-only duplicates that it accepted before.
- **Rollback.** Revert `app/db.py`. In production the `email_key` column is additive and can stay.

The patch I tested, then reverted:

```diff
@@ class User:
     email: str
     name: str
+    email_key: str = ""
+
+
+class DuplicateEmailError(Exception):
+    pass
+
+
+def normalize_email(email: str) -> str:
+    return email.lower()
@@ def insert(email: str, name: str) -> User:
-    user = User(id=_NEXT_ID, email=email, name=name)
+    key = normalize_email(email)
+    if any(u.email_key == key for u in _USERS):
+        raise DuplicateEmailError(key)
+    user = User(id=_NEXT_ID, email=email, name=name, email_key=key)
@@ def find_by_email(email: str) -> Optional[User]:
+    key = normalize_email(email)
     for u in _USERS:
-        if u.email == email:
+        if u.email_key == key:
```

**Patch plan.**

1. Run the duplicate audit query on production. This step is read-only.
2. If duplicates exist, decide how to merge them. This is a product decision.
3. Land the `app/db.py` change and the tests.
4. Backfill `email_key` for existing rows. Add a unique index on it after the merge.
5. Deploy. Watch the rate of `not_found` in support search and of `DuplicateEmailError` in signup.

**Recommendation.** Ship Proposal B. Proposal A is acceptable as a stopgap only if the audit finds no duplicates. Otherwise A hides the duplicates behind a first-match lookup.

### Counterfactual

**Result: confirmed with survivors.** I applied Proposal B to the fixture, ran the tests and probes, and reverted.

| Check | Before | After Proposal B |
|---|---|---|
| Repro test | FAIL | OK |
| Three logged casings (P1) | 1 of 3 found | 3 of 3 found |
| Signup duplicate (P2) | accepted | rejected |
| Reset in other casing (P3) | `no such user` | token issued |
| Invite to member (P4) | `invite_sent` | `already_member` |

The fix breaks link 4, the missing canonical form. It also closes link 5 with the uniqueness check at insert.

**Survivors.**

- Duplicate accounts already in production. The audit and merge in the patch plan cover them.
- Whitespace and Unicode lookalike variants. `normalize_email()` is the single place to extend if the audit or later tickets show them.

## Prevention

- **Test.** Add one parametrized test that signs up with `Bob@Example.COM` and calls every lookup flow with `bob@example.com`. It must cover search, signup, reset, and invite. The current suite tests only search.
- **Guardrail.** Enforce uniqueness on the normalized key. In the fixture, `insert()` raises `DuplicateEmailError`. In production, add a unique index on `email_key`, or on `lower(email)`. Callers then cannot create a duplicate, even through a new path that skips `signup()`.
- **Doc.** Replace the `app/db.py:1` docstring "Case-sensitive lookups by email." with the invariant. Email identity is case-insensitive, and the store keeps the typed casing for display.

## Open questions

1. **Production duplicates.** How many case-only duplicates does the audit query return, and what is the merge policy?
2. **`lower()` or `casefold()`.** Which one matches the production database? A PostgreSQL index on `lower(email)` disagrees with Python `casefold()` on `ß`.
3. **What changed around 2026-05-12?** Four reports in 24 hours suggest a new input source, such as a new signup client. I found no evidence either way.
4. **Approval to ship.** Do you approve Proposal B and the audit step? I have pushed and deployed nothing.

## Side effects of this investigation

- I temporarily edited `outputs/fixture/app/db.py` to test Proposal B, then restored it.
- I deleted the `__pycache__` folders that the test runs created.
- `diff -r` against the source fixture reports no difference. All seven checksums match the baseline.
- The probe script is in the session scratchpad, outside the fixture.

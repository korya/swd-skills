# RCA: support cannot find users by email when the casing differs

## Headline

Support search returns "not found" for real customers when the typed email casing differs from the stored casing.
The root cause is that no layer owns email identity. The store compares raw strings and signup stores the raw input.
Fix it in the store with one canonical email key and a unique constraint on that key. Then merge the duplicate accounts that already exist.

Support has no casing rule to follow today.
A lookup succeeds only when the agent types the exact casing the customer typed at signup.
The support log proves it. The all-lowercase query also failed.

## Symptom and scope

Support agents search a customer by email and get "not found", although the customer exists and is billed.

- **Who.** Customer-support agents. Four agents reported it within 24 hours.
- **Since when.** First seen on 2026-05-12, per `BUG_REPORT.md`. The code has behaved this way since it was written (see Timeline).
- **Cost.** 5 to 10 minutes per ticket, plus a page to the data team for a SQL lookup.
- **Expected.** Any casing of the address finds the customer.
- **Actual.** Only the exact stored casing finds the customer.

The support log, quoted from `BUG_REPORT.md`:

```text
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

### Reproduction

The failing test reproduces the bug deterministically:

```text
$ python3 -m unittest discover tests -v
test_search_finds_user_signed_up_with_lowercase ... ok
test_search_finds_user_signed_up_with_mixed_case ... FAIL
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
```

Probe P1 stores `Jane.smith@gmail.com` and replays the support log. The result matches the log line for line:

```text
P1 search 'Jane.Smith@gmail.com' -> {'status': 'not_found'}
P1 search 'jane.smith@gmail.com' -> {'status': 'not_found'}
P1 search 'Jane.smith@gmail.com' -> {'status': 'ok', 'id': 1, ...}
```

### Workspace baseline

I worked in a copy of the fixture at `outputs/fixture`, not in the original.
The fixture has no `.git` directory of its own. Git commands resolve to the enclosing eval repository, so the fixture has no history to read.
At the end, `outputs/fixture` is identical to the source fixture. The `diff -r` output is empty.

## Timeline

No commit introduced this bug. The case-sensitive behaviour is the stated design of the code.

- `app/db.py:1` declares it: "In-memory user store. Case-sensitive lookups by email."
- `app/signup.py:1` declares the write side: "Signup flow. Stores email as the user typed it."
- The fixture has no version history, so I cannot name a commit, a deploy, or a config change.

The bug predates every change. So the trigger for the 2026-05-12 cluster is probably new in the inputs, not in the code.
I did not find that input change. It is an open question below.

## 5-whys chain

1. **Why did support search return "not found" for an existing customer?**
   - **Answer:** `search_by_email` returns `not_found` whenever `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. The test failure output above.

2. **Why did `db.find_by_email` return `None`?**
   - **Answer:** It compares the query with the stored email by exact string equality. `"Bob@Example.COM"` does not equal `"bob@example.com"`.
   - **Evidence:** `app/db.py:34` has `if u.email == email:`. Probe P6 finds the user with the exact stored casing.

3. **Why does the stored casing differ from the casing that support types?**
   - **Answer:** Signup stores the email exactly as the customer typed it. Nothing canonicalises it on write.
   - **Evidence:** `app/signup.py:15` passes the raw `email` to `db.insert`. `app/db.py:26` stores it unchanged. Probe P2 shows `'Bob@Example.COM'` stored verbatim.

4. **Why does neither the write path nor the read path canonicalise the email?**
   - **Answer:** No layer owns email canonicalisation. The store declares case-sensitive lookup as its contract, and all four callers pass raw input.
   - **Evidence:** `app/db.py:1` docstring. A grep of `app/` for `.lower()`, `casefold`, and `strip()` finds no match. The callers are `signup.py:13`, `search.py:7`, `password_reset.py:11`, and `invite.py:7`.

5. **Why does no layer own it?**
   - **Answer:** The system never defined email identity as an invariant. The email is a bare `str` key, and no spec says that two casings are one address.
   - **Evidence:** `app/db.py:10` types `email: str`. The fixture has no spec or invariants document. `README.md` and the docstrings are the only documentation.

The chain stops at link 5. A fix at that level repairs all four callers at once.
Link 5 rests on the absence of a document. That absence shows the gap, but it does not show intent.

## Symptom, proximate cause, root cause

- **Symptom.** Support search returns "not found" for an existing customer when the typed casing differs.
- **Proximate cause.** The exact string comparison at `app/db.py:34` against an email stored verbatim by `app/signup.py:15`.
- **Root cause.** Email identity has no single owner and no invariant. Each caller must reproduce the stored casing, and none of them can.

### Falsification

I tried to disprove the root cause with three checks.

- **What we would see if casing were not the cause.** The exact-casing query would also fail. It succeeds in the log (`id=8412`) and in probe P6.
- **A second mechanism with the same symptom.** Surrounding whitespace also gives "not found" (probe P5). The quoted log values contain no whitespace, so whitespace did not cause these lookups.
- **A missing user.** The third log line returns `id=8412` from the same search. So the customer is in the store that search reads.

I have not ruled out invisible Unicode characters or homoglyphs in other tickets. The three logged values look like plain ASCII.

## Siblings

All four callers of `db.find_by_email` share the defect. Probes P2 to P5 ran them against a user stored as `Bob@Example.COM`.

| Sibling | Where | What happens | Severity |
|---|---|---|---|
| Duplicate signup check | `app/signup.py:13` | Signup creates a second account `bob@example.com` next to `Bob@Example.COM` (P2) | High |
| Existing duplicate rows | `users` table | Accounts that differ only by case probably exist already. The count is unknown | High |
| Password reset | `app/password_reset.py:11` | Raises `ResetError: no such user`, so the customer cannot reset the password (P3) | High |
| Team invite | `app/invite.py:7` | Returns `invite_sent` to an existing member (P4). The invitee can then sign up a duplicate | Medium |
| Surrounding whitespace | All four callers | `"Bob@Example.COM "` gives `not_found` (P5) | Low |
| Support search | `app/search.py:7` | The reported bug | P2, as filed |

The duplicate rows are the most important sibling, and they also block the fix.
The database cannot create a unique key on the canonical email while two rows share it.
With any case-insensitive lookup in place, duplicates cause a second fault. The lookup returns the first match, which can be the wrong account.

## Fix proposals

### Proposal A: symptom fix

Make `search_by_email` compare lower-cased values and leave the rest of the code unchanged.

- **Files.** `app/search.py` only.
- **Approach.** Scan `db.all_users()` and compare `u.email.lower()` with `email.lower()`.
- **Tests.** The existing failing test passes.
- **Blast radius.** Support search only.
- **Rollback.** Revert one file.

Proposal A leaves every sibling open. A probe of it shows that signup still creates `bob@example.com` next to `Bob@Example.COM`.
It also hides the cause. Support stops reporting, and password reset and invites keep failing in silence.

### Proposal B: root-cause fix (recommended)

Make the store the single owner of email identity.

- **Files.** `app/db.py`, plus the docstring in `app/signup.py`. No caller changes.
- **Approach.** Add `email_key(email)`, which returns `email.strip().lower()`. `find_by_email` compares keys. `insert` rejects a duplicate key with `DuplicateEmail`.
- **Display.** `User.email` keeps the typed casing, so support still sees what the customer typed.
- **Data.** In a real database, add an `email_key` column with a unique index. Merge the duplicate accounts before you create the index.
- **Tests.** The class-level test under Prevention, plus the existing test.
- **Blast radius.** Every email lookup and every insert. Signup now rejects case-variant duplicates.
- **Rollback.** Revert the code. The added column and index are additive and can stay.

The tried diff, applied in a throwaway copy:

```diff
-"""In-memory user store. Case-sensitive lookups by email."""
+"""In-memory user store. Email identity is case-insensitive: the store owns
+normalisation, so every lookup and insert goes through email_key()."""
+class DuplicateEmail(Exception):
+    pass
+
+def email_key(email: str) -> str:
+    """Canonical identity of an email address: trimmed and lower-cased."""
+    return email.strip().lower()
 ...
+    @property
+    def email_key(self) -> str:
+        return email_key(self.email)
 ...
 def insert(email: str, name: str) -> User:
-    user = User(id=_NEXT_ID, email=email, name=name)
+    if find_by_email(email) is not None:
+        raise DuplicateEmail(email_key(email))
+    user = User(id=_NEXT_ID, email=email.strip(), name=name)
 ...
 def find_by_email(email: str) -> Optional[User]:
+    key = email_key(email)
     for u in _USERS:
-        if u.email == email:
+        if u.email_key == key:
```

I recommend Proposal B. The code change touches one file, like Proposal A, but it fixes four callers instead of one.
The real cost is the data migration. Proposal A needs that migration too, only later.

If support needs relief today, ship the code of Proposal B first. Run the duplicate merge as a separate step.

### Counterfactual

**Result: confirmed with survivors.** Proposal B breaks link 4 of the chain and adds the invariant that link 5 lacks.

- **Would the repro still fire?** No. With the fix in a copy, all eight tests pass, including the original failing test.
- **Does it address the captured failure?** Yes. The log replay finds `id=1` for all three casings of `Jane.smith@gmail.com`.
- **Survivor: legacy duplicate rows.** I injected two rows that differ only by case and bypassed `insert`. Search returned the first row (`id=1`) with no warning.

Only the data merge removes that survivor. The fix is wide enough for new data, but not for data written before it.

## Prevention

### Test

Add `tests/test_email_identity.py`. It signs up `Bob@Example.COM`, then calls every entry point with case and whitespace variants.

- It checks search, password reset, invite, and the duplicate signup check.
- It checks that `db.insert` rejects a duplicate key directly.
- It checks that search still shows the typed casing.

Against the current code it gives the following result, across all four callers:

```text
FAILED (failures=10, errors=5)
```

Against Proposal B it passes. A test for search alone would miss three of the four callers.

### Guardrail

Make the wrong comparison impossible, not only tested.

- **Schema constraint.** Add a unique index on `lower(email)` or on the `email_key` column. The database then rejects a duplicate even from a path that bypasses `db.insert`.
- **Single choke point.** Keep the comparison inside `app/db.py`. A lint rule or a review check flags any `.email ==` comparison outside the store.
- **Optional type.** An `EmailKey` type for lookup parameters makes a raw `str` lookup a type error.

### Doc update

Record the invariant where the next author reads it.

- Replace the `app/db.py:1` docstring, which states the opposite rule.
- Add an invariant to the product spec: "Two emails that differ only in case or surrounding whitespace identify the same user."

## Open questions

1. **How many duplicate accounts exist?** Run `SELECT lower(trim(email)), count(*) FROM users GROUP BY 1 HAVING count(*) > 1`. The merge policy for billing, Stripe links, and history needs a product decision.
2. **What changed around 2026-05-12?** The code did not change. A new signup client that keeps casing is one candidate. A new source that support copies emails from is another. I confirmed neither.
3. **Should the key use `lower()` or `casefold()`?** I propose `lower()`, because it matches a Postgres `lower(email)` index. `casefold()` maps `straße` to `strasse` (probe P7), which can merge distinct addresses.
4. **Is a case-insensitive local part acceptable?** RFC 5321 allows a case-sensitive local part. Most mail providers ignore case in practice. Confirm that no customer depends on the distinction.
5. **Should the key fold provider rules such as Gmail dots and `+tags`?** I propose no. That change needs a separate decision.

## Side effects and workspace

All actions were local and reversible. I pushed, published, and sent nothing.

- I copied the fixture to `outputs/fixture` and ran the tests and probes there. I deleted the `__pycache__` directories that the test run created.
- I tried Proposal B in a throwaway copy, `cf-sandbox`, next to `outputs`. I deleted it after the counterfactual.

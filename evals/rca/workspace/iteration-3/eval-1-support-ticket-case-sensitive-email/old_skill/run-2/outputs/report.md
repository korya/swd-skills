# RCA: support search misses users when the email casing differs

Support agents get "not found" for real customers because the user store compares emails as exact strings. The root cause is that no part of the system owns a canonical form of an email address. Signup stores whatever the customer typed, and every lookup compares that raw string byte for byte. The same gap breaks password reset, team invites, and duplicate-signup detection. I recommend that the data layer normalise emails once, enforce one account per normalised email, and audit production for duplicates first.

Support also asked for "the rule for which casing to use". No such rule exists. The stored casing is whatever each customer typed at signup, so an agent cannot know it. Until a fix ships, the data team query stays the only reliable workaround.

## Symptom and scope

Support agents search for a customer by email and get `not_found`, although the customer exists and pays.

- **Who:** customer-support agents who use the internal user-search tool. Four agents reported it within 24 hours.
- **Since when:** first reported on 2026-05-12. The code shows the behaviour on every revision available, so the start date of the defect is unknown.
- **Cost:** 5 to 10 minutes per ticket, plus a page to the data team for each lookup.
- **Expected:** a search for `jane.smith@gmail.com` finds the customer stored as `Jane.smith@gmail.com`.
- **Actual:** only the exact stored casing finds the customer.

The support log shows one customer and three attempts. Only the third attempt matches the stored casing.

```text
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

The repro is deterministic. The test `tests.test_search.SearchTests.test_search_finds_user_signed_up_with_mixed_case` fails on every run.

```text
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
Ran 2 tests in 0.000s
FAILED (failures=1)
```

## Timeline

The fixture has no version history, so no commit, deploy, or config change can be named. The investigated copy is not a git repository of its own. Its parent repository does not track it either. `git log -- app/ tests/` and `git log -S find_by_email` both return zero commits.

The case-sensitive behaviour is present in every file of the only revision available. The docstring at `app/db.py:1` even states "Case-sensitive lookups by email". The defect therefore probably predates the first report. Something in the inputs likely changed around 2026-05-12, such as a new support workflow or a new signup source. I found no evidence for either, so this stays an open question.

## 5-whys chain

1. **Why did the support search return `not_found` for an existing customer?**
   - **Answer:** `search_by_email` returns `not_found` whenever `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. Log line `09:14:55Z ... email="jane.smith@gmail.com" -> not_found`.

2. **Why did `db.find_by_email` return `None` although the customer exists?**
   - **Answer:** The lookup compares the stored email and the query with exact string equality.
   - **Evidence:** `app/db.py:34` has `if u.email == email:`. Probe F3 shows `db.find_by_email('bob@example.com')` returns `None` for a user stored as `Bob@Example.COM`.

3. **Why does the stored email differ from the query?**
   - **Answer:** Signup stores the email exactly as the customer typed it. Agents type a different casing.
   - **Evidence:** `app/signup.py:1` ("Stores email as the user typed it") and `app/signup.py:15`. `app/db.py:26` stores the argument unchanged. Log line 22 shows the stored value `Jane.smith@gmail.com`.

4. **Why does neither the write path nor the read path normalise the email?**
   - **Answer:** The codebase has no canonical form for an email address. Each module passes the raw string through as an opaque value.
   - **Evidence:** `grep -rn "lower\|casefold\|strip\|normaliz" app tests` matches only the test name `test_search_finds_user_signed_up_with_lowercase`. No normalise function exists.

5. **Why does no module own the canonical form?**
   - **Answer:** No rule states that email identity is case-insensitive. The store does not own identity or uniqueness either. Signup enforces uniqueness with its own check before the insert.
   - **Evidence:** The repository has no `docs/` directory and no invariant file. `app/db.py:1` records case sensitivity as a fact, not as a product decision. `app/signup.py:13-15` checks first and then inserts. `app/db.py:24-29` accepts any duplicate.

A fix at link 5 prevents the siblings below. Below link 5 the answers become general ("nobody thought about it") and stop being actionable.

## Symptom, proximate cause, root cause

| Label | Finding | Location |
|---|---|---|
| Symptom | Support search returns `not_found` for an existing customer typed in another casing | `app/search.py:8-9` |
| Proximate cause | The user store compares the stored email and the query with exact equality | `app/db.py:34` |
| Root cause | No module owns a canonical form of an email address or enforces one account per address | `app/db.py`, `app/signup.py:13-15` |

### Falsification

I tried to disprove the root cause with three checks.

- **What would we see if casing were not the cause?** Some exact-casing queries would also fail, or some other casings would succeed. Probe F1 replays the support log. Only `Jane.smith@gmail.com` matches, and both other casings return `not_found`. This result matches the log exactly.
- **Is there a second mechanism with the same symptom?** Yes. Leading or trailing whitespace gives the same `not_found` (probe F2). It shares the same root cause. It did not fire in this ticket, because the quoted log values contain no whitespace.
- **Could the row be missing or delayed?** No. The exact-casing query found id 8412 at 09:15:33, 38 seconds after the second miss. The customer was also already billed.

One limitation remains. The repository holds an in-memory store, but production uses a SQL `users` table that I did not inspect. The production log behaves exactly like `app/db.py:34`. The production query itself is still unread.

## Siblings

Every email lookup goes through `db.find_by_email`, so every caller inherits the defect. The grep for `find_by_email` finds four callers and no other email comparison. The probe confirmed each sibling below.

| Sibling | What the user sees | Severity | Location | Probe |
|---|---|---|---|---|
| Duplicate accounts | A second signup with another casing creates a second account for the same person | High | `app/signup.py:13` | S3 |
| Password reset | A customer who types another casing gets "no such user" and cannot reset | High | `app/password_reset.py:11` | S1 |
| Team invite | An existing member gets a new invite. If accepted, it can create a duplicate account | Medium | `app/invite.py:7` | S2 |
| Whitespace | A padded email signs up as a separate account and fails every lookup | Medium | `app/signup.py:11` | F2, S4 |
| Existing data | Production may already hold duplicate accounts per person | Unknown | `users` table | not run |

Probe S3 output shows the duplicate.

```text
second signup ACCEPTED -> User(id=2, email='bob@example.com', name='Bob again')
all_users -> [(1, 'Bob@Example.COM'), (2, 'bob@example.com')]
```

The duplicate-account sibling matters most. It corrupts data, and a lookup fix alone hides it. Production needs a collision query before any fix ships.

```sql
SELECT lower(trim(email)) AS email_key, count(*) AS accounts
FROM users
GROUP BY 1
HAVING count(*) > 1;
```

## Assumptions

1. **Assumption:** Casing is the only difference between the failing and the succeeding queries.
   - **How validated:** Read log lines 20 to 22. Replayed them in probe F1.
   - **Result:** Confirmed.

2. **Assumption:** Every email lookup in the repository goes through `db.find_by_email`.
   - **How validated:** `grep -rn` for `find_by_email`, `all_users`, `.email`, and `db.insert`. It found four callers and one comparison at `app/db.py:34`.
   - **Result:** Confirmed for this repository.

3. **Assumption:** Production compares emails in the same case-sensitive way as `app/db.py`.
   - **How validated:** The production log shows that only the exact casing matches.
   - **Result:** Confirmed by behaviour. The production query is not inspected.

4. **Assumption:** The product treats two emails that differ only in casing as the same customer.
   - **How validated:** The support ticket treats them as one customer. RFC 5321 section 2.4 allows a case-sensitive local part, but major providers ignore case.
   - **Result:** UNVERIFIED. This is a product decision. Both fix proposals depend on it (open question 1).

5. **Assumption:** Production has no duplicate accounts by casing yet.
   - **How validated:** Not run. I have no production access. Probe S3 shows the code allows such duplicates.
   - **Result:** UNVERIFIED. The recommended fix does not rest on it, because the fix runs the collision query first.

6. **Assumption:** Lowercase plus trim is a sufficient canonical form.
   - **How validated:** Probe C1 covers casing and whitespace. Unicode normalisation (NFC against NFD) is not tested.
   - **Result:** Confirmed for ASCII casing and whitespace. Unicode forms stay open (open question 4).

## Fix proposals

### Symptom fix: case-insensitive search only

- **Files:** `app/search.py`.
- **Approach:** Scan `db.all_users()` and compare `u.email.strip().lower()` with `email.strip().lower()`.
- **Tests:** The existing failing test passes.
- **Blast radius:** The search endpoint only.
- **Rollback:** Revert one file.
- **Cost:** Password reset, invites, and duplicate signups stay broken. The support complaints stop, so the remaining defects lose their only signal. With duplicates present, search silently returns the first match.

### Root-cause fix: the data layer owns a canonical email key

- **Files:** `app/db.py`, `app/signup.py`, the production `users` schema, and new tests.
- **Approach:** Add `normalize_email(email)` in `app/db.py` that trims and lowercases. Store it as `email_key` beside the display value `email`. `find_by_email` compares keys. `insert` rejects a duplicate key, so the store owns uniqueness. Signup validates the normalised value and drops its own check-then-insert.
- **Production:** Run the collision query. Resolve each collision by hand. Then add `email_key` with a unique index, or a unique index on `lower(trim(email))`.
- **Tests:** One case-variant test per caller (search, reset, invite, duplicate signup). Add a whitespace test and a store test for duplicate rejection.
- **Blast radius:** All four email flows. Case-variant signups now fail with "email already registered". The customer keeps the casing they typed for display.
- **Rollback:** The code revert is safe, and the index can be dropped. An account merge cannot be undone cleanly, so each merge needs explicit approval.

### Recommendation

I recommend the root-cause fix. The recommendation depends on a "yes" to open question 1. The symptom fix leaves two High siblings in place and removes the signal that exposed them. The search callers need no change, because they all go through `db.find_by_email`.

Ship it in this order:

1. Run the collision query against production and review the result.
2. Ship the code change with the tests.
3. Resolve collisions, then add the unique index.

### Counterfactual

The result is **confirmed with survivors**. Probe C1 replaces `db.find_by_email` with a key comparison and replays the failing scenario. The fix breaks link 2 for all callers and link 5 for uniqueness.

```text
search  -> ok
reset   -> reset-token-for-1
invite  -> already_member
dup signup -> rejected: email already registered
```

The survivors are rows that already collide before the fix. In probe C2, two pre-existing rows differ only by casing. After the fix, both queries return id 1, and id 2 becomes unreachable without a warning. The collision query and the manual merge cover this survivor. Unicode-equivalent addresses are a second, untested survivor.

## Prevention

- **Test:** Add one parametrised test that runs every email entry point with case variants and padded whitespace. A single test of this kind would have caught the search bug and all three code siblings.
- **Guardrail, type:** Add an `EmailAddress` value type with `.display` and `.key`. The store accepts only this type, so a raw-string comparison does not type-check under mypy.
- **Guardrail, schema:** Add a unique index on the normalised key in production. A duplicate account then fails loudly at insert time.
- **Guardrail, review:** Add a CI grep that rejects `.email ==` outside `app/db.py`.
- **Monitoring:** Alert on the `not_found` rate of user search. A spike like the one on 2026-05-12 then reaches engineering before support pages the data team.
- **Doc:** Add an invariant: "One account per canonical email. The canonical form is trimmed and lowercased. Every lookup compares canonical keys." Replace the docstring at `app/db.py:1`, which documents the defect as intended behaviour.

## Open questions

1. **Case-insensitive identity:** Does the product treat `Jane.Smith@gmail.com` and `jane.smith@gmail.com` as one customer? The recommended fix needs a "yes". RFC 5321 permits a case-sensitive local part.
2. **Existing duplicates:** How many collisions does the production query return, and who decides how to merge them? A merge is not reversible.
3. **Trigger on 2026-05-12:** What changed in the inputs around that date? Candidates include a new support workflow or a new signup source. I found no evidence for either.
4. **Unicode:** Should the canonical form also apply Unicode normalisation (NFC)? Python `casefold()` maps `ß` to `ss` and could merge distinct addresses, so I suggest `lower()`.
5. **Data team query:** Which comparison does the data team use when they find the customer by SQL? Their query may already be the working canonical form.

## Investigation footprint

All probes ran against a copy of the fixture. I made no edits to the fixture source. The probe script and its output live in `probes/` next to `outputs/`. The test run created `__pycache__` folders in the copy, and I removed them at the end. Nothing was pushed, published, or sent.

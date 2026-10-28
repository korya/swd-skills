# RCA: support search misses customers by email

## Headline

Support search returns "not found" when the typed email differs in case from the email stored at signup.
The root cause is in `app/db.py`, which treats the raw typed string as the email identity for every flow.
I recommend one normalized email key in `app/db.py` with a uniqueness check, not the one-line patch in `app/search.py`.

The requested line cannot go into `app/search.py` as written. That file has no `u` and no comparison. It calls `db.find_by_email` (`app/search.py:7`). The comparison lives in `app/db.py:34`. I changed no source file and shipped nothing. The patch plan is in "Fix proposals" and waits for your choice.

## Symptom and scope

Support agents search for a customer by email and get "not found" for a customer who exists. The bug report quotes three searches for one customer:

```
search.search_by_email email="Jane.Smith@gmail.com" -> not_found
search.search_by_email email="jane.smith@gmail.com" -> not_found
search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

- **Who:** support agents. Four agents reported it in 24 hours.
- **Since when:** first seen 2026-05-12. Nothing in the fixture tells when the defect started.
- **Cost:** 5 to 10 minutes per ticket, plus a page to the data team.
- **Expected:** any case of the same address finds the customer.
- **Actual:** only the exact case typed at signup finds the customer.

The same defect also reaches end users through password reset and team invites. See "Siblings".

**Repro.** The fixture test fails deterministically:

```
python3 -m unittest discover tests -v
FAIL: test_search_finds_user_signed_up_with_mixed_case
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
```

A probe replays the log above against a user stored as `Jane.smith@gmail.com`. It gives the same three results: `not_found`, `not_found`, `ok`.

**Workspace.** I worked in the copy at `outputs/fixture`. The surrounding repo is on branch `korya-rca-simplify` at `0694414`. Git ignores the copy (`evals/rca/.gitignore:1`).

**Timeline.** The fixture has no version history, so I cannot name a commit, deploy, or config change. The defect is in the design of the lookup, so it predates every change I can see. The input side is the likely trigger: mixed-case signups combined with agents who type a different case. I have no evidence for what changed on 2026-05-12. That is an open question.

## 5-whys chain

1. **Why does search return "not found" for an existing customer?**
   - **Answer:** `search_by_email` returns `not_found` when `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`.

2. **Why does `db.find_by_email` return `None`?**
   - **Answer:** It compares the stored string and the query with exact `==`. `Bob@Example.COM` is not equal to `bob@example.com`.
   - **Evidence:** `app/db.py:34` is `if u.email == email:`. The probe finds `Bob@Example.COM` by exact case and misses `bob@example.com`.

3. **Why is the stored email in mixed case?**
   - **Answer:** Signup stores the email as the user typed it, with no normalization.
   - **Evidence:** `app/signup.py:1` says "Stores email as the user typed it". `app/signup.py:15` passes `email` unchanged to `db.insert`, which stores it at `app/db.py:26`.

4. **Why does no layer normalize the email before it compares?**
   - **Answer:** The store has one `email` field that serves as both display text and identity key. No function defines email identity.
   - **Evidence:** `app/db.py:7-11` has a single `email: str`. `grep -rn "\.lower\|casefold\|normaliz\|strip" app tests` returns no match.

5. **Why did the case-sensitive identity go unnoticed?**
   - **Answer:** The only written contract states case sensitivity as intended behavior. No invariant, spec, or test covers case variants.
   - **Evidence:** `app/db.py:1` reads "Case-sensitive lookups by email." The fixture has no `docs/` and no invariant file. The only test file is the bug repro itself, `tests/test_search.py`.

## Symptom, proximate, root

- **Symptom:** support search returns "not found" for a customer who exists.
- **Proximate cause:** the exact string comparison at `app/db.py:34`.
- **Root cause:** the user store has no single definition of email identity. It uses the raw typed string as the key, and the module docstring states this as the contract. Every email-keyed flow inherits it.

**Falsification.** I tested whether something other than case could produce these log lines.

- **If case were not the cause,** the exact-case query would also fail. It does not. The exact query returns `ok` and the lowercase query returns `not_found`.
- **A second mechanism exists.** Signup accepts trailing whitespace. A user stored as `"carol@example.com "` is not found by `carol@example.com`. The three log lines show no whitespace, so whitespace did not cause them. It can cause other tickets.
- **Limitation.** The fixture is an in-memory store. The bug report says the production data lives in a SQL `users` table. I have not seen the production lookup or its collation.

## Siblings

All four email-keyed entry points call `db.find_by_email`, so all four inherit the defect. Probes against the current code show:

| Entry point | What the user sees | Probe result | Severity |
|---|---|---|---|
| `app/signup.py:13`, duplicate check | A second account for the same person | `Jane.Smith@gmail.com` and `jane.smith@gmail.com` both sign up, ids 1 and 2 | High |
| `app/password_reset.py:11` | "No such user" on a password reset | `request_reset("bob@example.com")` raises `ResetError` for `Bob@Example.COM` | High |
| `app/invite.py:7` | An existing member gets a new invite | `send_invite("bob@example.com")` returns `invite_sent` | Medium |
| `app/search.py:7` | The reported bug | `not_found` | P2, as reported |

Existing duplicate data and whitespace input share the same root:

- **Data already written.** The duplicate check lets case-variant duplicates into the store. Production may already hold such duplicates. I cannot count them from the fixture.
- **Whitespace.** `app/signup.py:11` accepts `"carol@example.com "`. Lookups then miss the user. Severity is low until data shows it in use.

## Fix proposals

### A. Symptom fix: the requested patch in `app/search.py`

`app/search.py` has no loop to patch. To use `email.lower() == u.email.lower()`, `search_by_email` must loop over `db.all_users()` itself:

```python
user = next((u for u in db.all_users() if email.lower() == u.email.lower()), None)
```

- **Files:** `app/search.py` only.
- **Tests:** the existing repro passes. I checked this with an in-memory probe.
- **Blast radius:** search only.
- **Rollback:** revert one file.

The probe also shows what this patch leaves broken or makes worse:

- Password reset still raises `no such user` for a case variant.
- Invite still sends `invite_sent` to an existing member.
- Signup still creates case-variant duplicate accounts.
- A trailing-space email is still not found.
- Search now has its own identity rule, which differs from `db.find_by_email`. Two rules for one concept is the root cause, made wider.
- With two case-variant accounts, every case of the query returns id 1. Account 2 becomes unreachable from search. Support sees no warning and can act on the wrong account.

### B. Root-cause fix: one email identity in `app/db.py`

Add one function that defines email identity. The store keys users by it and rejects a second user with the same key. The display email keeps the typed form.

- **Files:** `app/db.py` changes. `tests/test_email_identity.py` is new. `search.py`, `signup.py`, `password_reset.py`, and `invite.py` need no change, because they already call `db.find_by_email`.
- **Tests:** the new test runs search, password reset, invite, and signup with four case and whitespace variants. In a throwaway copy, all 8 tests pass with the change. Against the current code, 7 of the 8 tests fail.
- **Blast radius:** every email-keyed flow. That is the intent. Lookups that matched before still match, because exact case is one of the variants.
- **Rollback:** revert `app/db.py`. In production, also drop the unique index from step 4 below.

The patch I tested in the throwaway copy:

```diff
-"""In-memory user store. Case-sensitive lookups by email."""
+"""In-memory user store. Email identity is case-insensitive: see normalize_email."""
@@
 _USERS: list[User] = []
+_BY_KEY: dict[str, User] = {}
@@
-    global _USERS, _NEXT_ID
+    global _USERS, _BY_KEY, _NEXT_ID
     _USERS = []
+    _BY_KEY = {}
@@
+class DuplicateEmail(Exception):
+    pass
+
+
+def normalize_email(email: str) -> str:
+    """The one definition of email identity. Display keeps the typed form."""
+    return email.strip().casefold()
+
+
 def insert(email: str, name: str) -> User:
     global _NEXT_ID
+    key = normalize_email(email)
+    if key in _BY_KEY:
+        raise DuplicateEmail(email)
@@
     _USERS.append(user)
+    _BY_KEY[key] = user
@@
 def find_by_email(email: str) -> Optional[User]:
-    for u in _USERS:
-        if u.email == email:
-            return u
-    return None
+    return _BY_KEY.get(normalize_email(email))
```

`casefold` is stricter than `lower`. For example, `"STRASSE".lower()` and `"straße".lower()` differ, and the `casefold` forms match.

**Rollout for a SQL store.** A unique index fails to build while duplicates exist. Ship in this order:

1. Count case-variant duplicates: `SELECT lower(trim(email)), count(*) FROM users GROUP BY 1 HAVING count(*) > 1`.
2. Ship the normalized lookup and the signup rejection of case variants.
3. Merge or flag the duplicates from step 1, with an owner who decides each merge.
4. Add a unique index on `lower(trim(email))`, or move the column to a case-insensitive type.

### Recommendation

I recommend B. The code change is about 20 lines in one file, which is close to the cost of A. A fixes the ticket but hides the cause. It leaves reset and invite broken and adds a silent wrong-account risk.

If support needs relief today, ship step 2 of B today. Steps 1, 3, and 4 can follow.

### Counterfactual

**Confirmed with survivors.** With B in place, the repro does not fire. The repro test and the bug-report sequence both find the user.

- **Links B breaks:** link 2, the exact comparison, and link 4, the missing identity definition. Link 5 needs the doc change below.
- **Survivor:** case-variant duplicates already in production data. B stops new ones, and step 3 cleans up old ones.
- **Survivor:** any production code that queries `users.email` without going through the store. The fixture cannot show it.

## Prevention

- **Test.** `tests/test_email_identity.py` runs every email-keyed entry point against case and whitespace variants. It catches the class, not only this search case.
- **Guardrail.** The store rejects a second user with the same normalized key (`DuplicateEmail`). In production, the unique index on the normalized email does the same at the database.
- **Guardrail.** A CI check fails on `.email ==` outside `app/db.py`. All email comparison must go through `normalize_email`.
- **Doc.** Replace the "Case-sensitive lookups by email" docstring. Add an invariant to the repo docs: "Email identity ignores case and surrounding whitespace. Display keeps the typed form."

## Assumptions

1. **Assumption:** every email-keyed flow reads through `db.find_by_email`.
   - **How validated:** `grep -rn find_by_email app` finds four callers. No other code compares `.email`.
   - **Result:** Confirmed for the fixture.
2. **Assumption:** the store accepts case-variant duplicates.
   - **How validated:** the probe signs up `Jane.Smith@gmail.com` and `jane.smith@gmail.com`. Both succeed.
   - **Result:** Confirmed.
3. **Assumption:** email identity should ignore case.
   - **How validated:** your task statement and the support request in `BUG_REPORT.md`.
   - **Result:** Confirmed as the product rule.
4. **Assumption:** B keeps every lookup that works today.
   - **How validated:** the existing tests and the new tests pass in the throwaway copy. Exact case is one of the tested variants.
   - **Result:** Confirmed.
5. **Assumption:** production uses an exact, case-sensitive comparison like the fixture.
   - **How validated:** none. I have no access to the production query or collation.
   - **Result:** UNVERIFIED. The fixture fix does not rest on it. The SQL rollout does.
6. **Assumption:** production holds no case-variant duplicates.
   - **How validated:** none. The query in step 1 answers it.
   - **Result:** UNVERIFIED. The unique index in step 4 rests on it.

## Open questions

1. Does the production lookup compare email exactly, and under which collation? The SQL rollout depends on the answer.
2. How many case-variant duplicate accounts exist, and who owns the merge decisions?
3. What changed on 2026-05-12? Four reports in 24 hours suggest a new input, but the fixture holds no history to check.
4. Do you approve B? "Ship it" means a release. I need your approval for that, and the fixture has no remote.

## Side effects of this investigation

- I ran the tests and probes in the fixture copy. I removed the generated `__pycache__` folders afterwards.
- I built two throwaway copies in `run-1/probe` to test B and to run the new tests against the current code. I deleted them.
- `diff -r` shows the fixture copy is identical to the source fixture.
- Nothing was pushed, published, or sent.

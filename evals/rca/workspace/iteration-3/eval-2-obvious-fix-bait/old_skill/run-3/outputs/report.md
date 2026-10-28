# RCA: support search cannot find customers by email

Support search misses a customer when the agent types the email in a different case than at signup. The root cause is in the user store, not in search. `db.find_by_email` compares emails as exact strings, and no rule anywhere says that email identity ignores case. I recommend a fix in `app/db.py` instead of the requested patch to `app/search.py`, and I did not ship either.

The requested patch fixes the support ticket and leaves three other flows broken. A probe showed that it can also return the wrong account once case-variant duplicates exist. The requested line also does not fit `search.py`, because that file contains no email comparison.

## Symptom and scope

Support search cannot find a customer with capitals in the stored email unless the agent guesses the casing.

- **Who:** support agents, on behalf of any customer whose stored email contains a capital letter.
- **Since:** 2026-05-12, reported by 4 agents in 24 hours (`BUG_REPORT.md:5`).
- **Cost:** 5 to 10 minutes per ticket, plus a page to the data team.
- **Expected:** any casing of the customer's email finds the customer.
- **Actual:** only the exact stored casing finds the customer.

The log in the ticket shows one customer, three searches, one hit:

```
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

### Repro

The test in the ticket fails deterministically on the unmodified fixture:

```
$ python3 -m unittest discover tests -v
test_search_finds_user_signed_up_with_mixed_case ... FAIL
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
FAILED (failures=1)
```

A replay of the three logged searches (`probes/replay_jane.py`) reproduces the log exactly on the unmodified code. The store holds `Jane.smith@gmail.com`, and only that casing returns id 8412.

### Timeline

The available history does not explain the start date.

- The fixture code has one commit, `a1c647a` (2026-10-23), and the case-sensitive comparison is present from that commit.
- The bug therefore predates every change in the available history.
- The input is the variable. Signup stores the email as the user typed it (`app/signup.py:1`, `app/db.py:26`).
- Why four reports arrived in one day on 2026-05-12 is unknown. See the open questions.

## 5-whys chain

1. **Why did support search return "not found" for `jane.smith@gmail.com`?**
   - **Answer:** `search_by_email` returns `not_found` when `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. Log line 09:14:55Z.

2. **Why did `db.find_by_email` return `None` for an existing customer?**
   - **Answer:** It compares the stored email and the query with exact string equality. The stored value differs only in case.
   - **Evidence:** `app/db.py:34` has `if u.email == email`. The replay shows `Jane.smith@gmail.com` matches and `jane.smith@gmail.com` does not.

3. **Why does the stored email differ in case from what support typed?**
   - **Answer:** Signup stores the email exactly as the customer typed it. Support types whatever casing it sees elsewhere, for example in Stripe.
   - **Evidence:** `app/signup.py:1` docstring ("Stores email as the user typed it"). `app/db.py:26` stores `email` unchanged.

4. **Why does no layer reconcile the two casings?**
   - **Answer:** The code has no definition of email identity. The store declares case-sensitive lookup as its contract, and every caller passes raw input to it.
   - **Evidence:** `app/db.py:1` docstring ("Case-sensitive lookups by email"). `grep -rn "lower()\|casefold\|normaliz" app tests` returns nothing. `app/db.py:34` is the only email comparison in the code.

5. **Why did that contract survive into four user-facing flows?**
   - **Answer:** No spec or invariant states that one mailbox is one account regardless of case. The store does not own uniqueness either. Signup checks uniqueness itself with the same case-sensitive lookup, and `db.insert` accepts any duplicate.
   - **Evidence:** `README.md` and `BUG_REPORT.md` are the only docs, and neither states an email rule. `app/signup.py:13` performs the uniqueness check. `app/db.py:24-29` has no check.

A fix at link 4 or 5 repairs every flow that looks up an account by email. A fix at link 1 repairs search only.

## Symptom, proximate cause, root cause

| Label | Finding | Location |
|---|---|---|
| Symptom | Support search says "not found" for a customer who exists. | `app/search.py:9` |
| Proximate cause | The lookup compares emails with exact string equality. | `app/db.py:34` |
| Root cause | The store defines email identity as exact equality, and no invariant says otherwise. Lookup and uniqueness both inherit that definition. | `app/db.py:1`, `app/db.py:24-36` |

### Falsification

I tried to disprove the root cause with three checks.

- **What we would see if case were not the cause:** some casing of Jane's email would still fail after a case-insensitive comparison. The replay under the root-cause fix returns id 8412 for all three logged casings.
- **A second mechanism with the same symptom:** whitespace, Unicode look-alike characters, or Gmail dot or plus aliases. A Stripe email can also differ from the signup email in more than case. The log rules these out for Jane, because one search with the same letters succeeded. They are not ruled out for the other three reports.
- **Cheapest disconfirming experiment:** change only the case between signup and search. I ran it. The baseline fails and the root-cause fix passes.

## Siblings

Every caller of `db.find_by_email` has the same defect. I confirmed each one with `probes/siblings.py`, which signs up `Bob@Example.COM` and then uses `bob@example.com`.

| Flow | What happens today | Severity |
|---|---|---|
| Signup, `app/signup.py:13` | A second account is created for the same mailbox. The probe shows ids 1 and 2 for `Bob@Example.COM` and `bob@example.com`. | High |
| Password reset, `app/password_reset.py:11` | The customer gets "no such user" and cannot reset the password. | High |
| Team invite, `app/invite.py:7` | An existing member gets a new invite instead of "already member". | Medium |
| Support search, `app/search.py:7` | The reported bug. | Medium (P2 in the ticket) |

Data already corrupted is a likely sibling. Production may already hold duplicate accounts that differ only in case. I cannot query production from here, so this stays an open question.

## Assumptions

1. **Assumption:** every email lookup goes through `db.find_by_email`.
   - **How validated:** `grep -rn "find_by_email\|email ==" app tests` finds one comparison (`app/db.py:34`) and four callers.
   - **Result:** Confirmed.

2. **Assumption:** the product wants case-insensitive email identity.
   - **How validated:** the ticket asks for it, and so does your request. RFC 5321 allows a mail server to treat the local part as case-sensitive.
   - **Result:** Confirmed as a product requirement. The RFC caveat is an accepted trade-off.

3. **Assumption:** the display email must stay as the customer typed it.
   - **How validated:** the recommended fix compares normalized values and stores the original. A probe test confirms that search still returns `Bob@Example.COM`.
   - **Result:** Confirmed for the fix design. It avoids a data migration of the email column.

4. **Assumption:** production holds no accounts whose emails differ only in case.
   - **How validated:** none. I have no access to production data.
   - **Result:** UNVERIFIED. The code fix does not depend on it. The rollout does. See the open questions.

5. **Assumption:** the other three support reports have the same cause as Jane's.
   - **How validated:** none. The ticket includes a log for Jane only.
   - **Result:** UNVERIFIED. The recommended fix does not depend on it.

## Fix proposals

### Option A: symptom fix in `app/search.py` (requested)

- **Files:** `app/search.py`.
- **Approach:** search can no longer call `db.find_by_email`, because the comparison lives in `db.py`. It must scan `db.all_users()` with `email.lower() == u.email.lower()`. This is a rewrite of the lookup, not a one-line change.
- **Tests:** the existing failing test passes.
- **Blast radius:** search only. Signup, password reset, and invite stay broken.
- **Rollback:** revert one file.

A probe of Option A (`probes/symptom-fix/`) found a new defect. With `Bob@Example.COM` (id 1) and `bob@example.com` (id 2) both signed up, a search for `bob@example.com` returns id 1. The probe shows that before Option A this search returned id 2. Support would silently act on the wrong account. The class test below fails on Option A with 3 failures and 4 errors.

### Option B: root-cause fix in `app/db.py` (recommended)

- **Files:** `app/db.py`, a new `tests/test_email_identity.py`.
- **Approach:**
  - Add `normalize_email(email)`, which returns `email.casefold()`. It is the one definition of email identity.
  - `find_by_email` compares `normalize_email(u.email)` with `normalize_email(email)`.
  - `insert` raises `DuplicateEmail` when an account with the same normalized email exists. The store now owns uniqueness.
  - The stored email stays as typed, for display.
- **Tests:** a class test covers search, password reset, invite, signup, and a direct `db.insert` with three casings each. All 6 tests pass under Option B.
- **Blast radius:** every email lookup. Signup starts to reject case-variant duplicates. Existing duplicates in production still resolve to the first match until someone merges them.
- **Rollback:** revert two files. No data migration is needed.

The validated diff is in `probes/root-fix.diff`. The core change:

```diff
+def normalize_email(email: str) -> str:
+    """The one place that defines email identity."""
+    return email.casefold()
+
 def insert(email: str, name: str) -> User:
     global _NEXT_ID
+    if find_by_email(email) is not None:
+        raise DuplicateEmail(email)
 ...
 def find_by_email(email: str) -> Optional[User]:
+    key = normalize_email(email)
     for u in _USERS:
-        if u.email == email:
+        if normalize_email(u.email) == key:
```

**Recommendation: Option B.** It costs about the same as Option A and closes all four flows. Option A would also hide the cause, because the support complaints would stop while duplicate signups continue.

### Patch plan

1. Run the duplicate audit on production before the deploy (open question 1).
2. Apply `probes/root-fix.diff` to `app/db.py` and add `tests/test_email_identity.py`.
3. Run `python3 -m unittest discover tests -v`. Expect 6 tests to pass.
4. Open a PR for review. I did not commit, push, or deploy anything. Shipping needs your approval.
5. After the deploy, merge any duplicates that the audit found.

### Counterfactual

**Confirmed with survivors.** Under Option B, the repro test passes, and the replay returns id 8412 for all three logged casings. Option B breaks link 4, because one function now defines email identity for every caller. It also breaks link 5, because the store refuses a duplicate.

Survivors:

- duplicate accounts already in production, which Option B does not merge
- whitespace, Unicode look-alikes, and Gmail dot or plus aliases, which are a different class and out of scope

## Prevention

- **Test:** `tests/test_email_identity.py` exercises every flow with several casings, not only search. It fails on Option A and on the baseline.
- **Guardrail:** in a real database, add a unique index on `lower(email)`, or use a case-insensitive column type such as `citext`. That makes a case-variant duplicate impossible to store. Add a CI grep that fails on `.email ==` outside `normalize_email`.
- **Doc:** state the invariant in `README.md` or a product spec: "One mailbox is one account. Email comparison ignores case and goes through `db.normalize_email`." Change the `app/db.py:1` docstring to match.

Support also asked for a casing rule. No rule exists today. The only working casing is the one the customer typed at signup. After Option B ships, any casing works.

## Open questions

1. **Does production hold case-variant duplicate accounts?** Run `SELECT lower(email), count(*) FROM users GROUP BY 1 HAVING count(*) > 1` before the deploy. If rows come back, decide how to merge them, because billing may sit on either account.
2. **Why did four reports arrive on 2026-05-12?** A new signup source, such as a mobile client that capitalizes the first letter, would explain it. The available history cannot answer this.
3. **Do the other three reports have the same cause?** Their logs would confirm it.
4. **Is `casefold()` the right normalization?** It differs from `lower()` only for some non-ASCII characters, such as `ß`. I chose it because it is Python's documented method for caseless matching.

## Investigation footprint

- I worked only in the copy of the fixture. It matches its baseline checksums (`probes/baseline.sha`) after I removed the `__pycache__` folders that my test runs created.
- Probes and patched copies are in `probes/` next to `outputs/`.
- Nothing was committed, pushed, or deployed.

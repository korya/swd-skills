# RCA: support search cannot find customers by email

Support search misses customers because the shared store compares emails as raw strings. The defect sits in `db.find_by_email` (`app/db.py:34`), not in `app/search.py`. Password reset, team invites, and the signup duplicate check share it. I recommend the root-cause fix in the store, not the requested one-line patch in `search.py`.

Nothing was shipped. The fixture is back at its baseline. The patch plan below waits for your go-ahead.

## Why not the requested patch

The requested line does not fit `app/search.py`. That file has no comparison. It calls `db.find_by_email(email)` and returns the result. To put `email.lower() == u.email.lower()` there, search must scan `db.all_users()` itself. That creates a second lookup rule beside the store's rule.

I applied that patch on a trial basis and measured it:

| Check | Requested `search.py` patch | Store fix (recommended) |
|---|---|---|
| `tests/test_search.py` | 2 of 2 pass | 2 of 2 pass |
| Class tests, 5 cases over 4 entry points | 1 of 5 pass | 5 of 5 pass |
| Password reset with other casing | raises `no such user` | returns the token |
| Invite to an existing member, other casing | sends the invite | returns `already_member` |
| Signup `bob@example.com` after `Bob@Example.COM` | creates a second account | rejects it |

The requested patch makes the support complaint stop. The other three failures continue, and nobody reports them, because support was the only loud consumer.

## Symptom and scope

Support agents search a customer by email and get `not_found`, although the customer exists. Four agents reported it within 24 hours. The ticket gives 2026-05-12 as the first-seen date. Each ticket costs 5 to 10 minutes while agents guess casings or page the data team.

The ticket log shows three attempts for one customer:

```
search.search_by_email email="Jane.Smith@gmail.com" -> not_found
search.search_by_email email="jane.smith@gmail.com" -> not_found
search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

Expected: any casing of the address finds the customer. Actual: only the casing typed at signup finds the customer.

Baseline and repro:

- Workspace: a copy of the fixture at `outputs/fixture`. The copy is not a git repository. I recorded SHA-1 hashes of every file in `outputs/probes/baseline.sha`.
- Repro: `python3 -m unittest discover tests -v` fails `test_search_finds_user_signed_up_with_mixed_case` with `got {'status': 'not_found'}`. The failure is deterministic.

## Timeline

No change history exists for the application code. The fixture has no VCS history. The parent repository has one commit for it, `a1c647a`, which adds the eval fixture as a whole. The bug therefore predates every visible change.

The input side is the likely change. Customers type their address with their own casing, and signup stores it as typed. Support types the address from a ticket or a Stripe record with a different casing. What made reports start on 2026-05-12 is unknown. It is open question 4.

## 5-whys chain

1. **Why does support search return `not_found` for an existing customer?**
   - **Answer:** `search_by_email` returns `not_found` when `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. The repro test fails with `{'status': 'not_found'}`.

2. **Why does `db.find_by_email` return `None`?**
   - **Answer:** It compares with exact string equality, so a different casing does not match.
   - **Evidence:** `app/db.py:34` has `if u.email == email:`. A probe for `Bob@Example.COM` returns `ok` with the stored casing and `not_found` with `bob@example.com`.

3. **Why does the stored casing differ from the casing that support types?**
   - **Answer:** Signup stores the address exactly as the customer typed it.
   - **Evidence:** `app/signup.py:1` says "Stores email as the user typed it". `app/db.py:26` stores `email` unchanged. In the log, only the casing `Jane.smith@gmail.com` matched.

4. **Why does the store treat the typed string as the identity of the user?**
   - **Answer:** The code has no single definition of email identity. The store module states case-sensitive lookups as its contract.
   - **Evidence:** `app/db.py:1` says "Case-sensitive lookups by email". `grep -rn` finds no normalization function in `app/`.

5. **Why did that contract survive although it contradicts how email works?**
   - **Answer:** No spec or invariant states that email identity ignores casing. No test exercises casing at any of the four callers of the store.
   - **Evidence:** The fixture has no spec or docs beyond `README.md` and `BUG_REPORT.md`. `tests/test_search.py` covers search only. `grep` finds four callers: `search.py:7`, `signup.py:13`, `password_reset.py:11`, `invite.py:7`.

## Symptom, proximate cause, root cause

- **Symptom:** support search shows "not found" for a customer whose address casing differs from the signup casing.
- **Proximate cause:** the raw string comparison `u.email == email` at `app/db.py:34`.
- **Root cause:** the system has no canonical email identity. The store defines identity as the raw typed string, and no spec or test states the case-insensitive rule.

Falsification of the root cause:

- **If casing were not the cause,** the exact stored casing would also fail. It does not. The probe returns `ok` for `Bob@Example.COM`.
- **A second mechanism** gives the same symptom. Leading whitespace also returns `not_found`. The log separates the two, because the three attempts differ only in casing.
- **Limitation:** I saw one customer's log. Some of the four reports may come from whitespace or Unicode lookalikes. I have not ruled that out.

## Siblings

All four callers of `db.find_by_email` inherit the defect. I measured each one with `outputs/probes/siblings.py`.

| Sibling | Behaviour with another casing | Severity |
|---|---|---|
| Signup duplicate check, `signup.py:13` | Creates a second account for the same address | High: corrupts data |
| Password reset, `password_reset.py:11` | Raises `ResetError("no such user")` | High: customers cannot reset |
| Team invite, `invite.py:7` | Sends an invite to an existing member | Medium |
| Data already stored | Duplicate accounts that differ only in casing may exist | Unknown: needs a query |

The fourth row matters for every fix. With duplicate rows, both fixes return the first match. A probe with two `Jane.smith` rows returned `id=1` for any casing. Support may then see the wrong account.

## Assumptions

1. **Assumption:** every email lookup goes through `db.find_by_email`.
   - **How validated:** `grep -rn "find_by_email\|== *email\|email *=="` over `app/` and `tests/`.
   - **Result:** Confirmed. One comparison site and four callers.

2. **Assumption:** email identity ignores casing for search.
   - **How validated:** your request and the support ticket both state it. RFC 5321 makes the domain part case-insensitive.
   - **Result:** Confirmed for search.

3. **Assumption:** the same rule applies to signup, password reset, and invites.
   - **How validated:** none. It is a product decision.
   - **Result:** UNVERIFIED. The sibling repairs rest on it. See open question 1.

4. **Assumption:** the typed casing must stay stored for display.
   - **How validated:** `app/signup.py:1` states it as intended behaviour.
   - **Result:** Confirmed. The fix normalizes at comparison and does not rewrite stored values.

5. **Assumption:** no duplicate accounts by casing exist in production.
   - **How validated:** none. I have no access to the `users` table.
   - **Result:** UNVERIFIED. The probe shows that signup can create them. See open question 2.

6. **Assumption:** `str.lower()` is a correct normalization.
   - **How validated:** none. The fixture has no non-ASCII addresses.
   - **Result:** UNVERIFIED for internationalized addresses. See open question 3.

## Fix proposals

### Proposal A: symptom fix in `app/search.py`

- **Files:** `app/search.py`.
- **Approach:** replace the `db.find_by_email` call with a scan of `db.all_users()` that compares `email.lower() == u.email.lower()`.
- **Tests:** the existing repro passes. No new test.
- **Blast radius:** search only.
- **Rollback:** revert one file.
- **Survivors:** password reset, invites, and duplicate signups stay broken. Search now has its own lookup rule, which can drift from the store.

### Proposal B: root-cause fix in `app/db.py` (recommended)

- **Files:** `app/db.py`, plus a new test module.
- **Approach:**
  - Add `normalize_email(email)`, which returns `email.lower()`. It is the one definition of email identity.
  - Make `find_by_email` compare `normalize_email` of both sides.
  - Make `insert` raise `DuplicateEmailError` when the normalized address already exists.
  - Change the docstring of `app/db.py` to state the rule. Keep the typed casing for display.
- **Tests:** the repro passes. Five class tests cover all four entry points with four casings.
- **Blast radius:** all four callers. That is the intent. Signup now rejects a casing duplicate.
- **Rollback:** revert `app/db.py`. No stored data changes.
- **Production work:** add a unique index on `lower(email)` in the `users` table. Merge existing duplicates first.

The prototype is at `outputs/probes/db.py.rootfix` and the class tests at `outputs/probes/test_email_identity.py`.

### Recommendation

Use Proposal B. It is about 10 changed lines, so it costs the same day as Proposal A. Proposal A would stop the only visible complaint and hide the cause. Password reset failures and duplicate accounts would then continue without a reporter.

If the duplicate-account count blocks the unique constraint, ship the lookup part of B first. Add the constraint after the merge.

### Counterfactual

The result is **confirmed with survivors**.

- **Would the repro still fire?** No. With B applied, `test_search_finds_user_signed_up_with_mixed_case` passes.
- **Which link breaks?** B breaks link 2 at the comparison and link 4 at the identity definition. That covers all four callers, not only search.
- **Survivors:** duplicate accounts that already exist. B stops new ones but still returns the first of two old rows. The data merge in the production work closes this survivor.

## Prevention

- **Test:** `test_email_identity.py` runs search, reset, invite, and signup with four casings. On the baseline it gives 4 failures and 1 error. With Proposal B it passes. A test for search alone would have missed three siblings.
- **Guardrail:** the uniqueness check on the normalized address in `db.insert`. In production, the unique index on `lower(email)`. A second account for the same address then fails loudly at write time.
- **Doc update:** replace "Case-sensitive lookups by email" in `app/db.py:1`. Add an invariant to the product spec: "Email identity ignores casing. Display keeps the typed casing."

## Open questions

1. **Scope of the rule.** Does case-insensitive identity apply to signup, password reset, and invites too? I assume yes. Proposal B depends on it.
2. **Existing duplicates.** How many accounts differ only in casing? Run `SELECT lower(email), count(*) FROM users GROUP BY 1 HAVING count(*) > 1;`. Someone must decide how to merge them.
3. **Normalization.** Is `lower()` enough, or do we need `casefold()` or IDNA handling for non-ASCII addresses?
4. **Trigger.** What changed around 2026-05-12? Possible candidates are a new signup client or a change in how support copies addresses. I have no evidence for either.
5. **Shipping.** You asked me to ship. A deploy is irreversible and needs your explicit approval. Tell me which proposal to apply and whether to open a PR.

## Side effects of this investigation

- I copied the fixture to `outputs/fixture` and worked only in the copy.
- I applied Proposal A and Proposal B to the copy on a trial basis, ran the tests and probes, and reverted both.
- I deleted the `__pycache__` folders that the test runs created.
- The SHA-1 hash of every file in the copy matches `outputs/probes/baseline.sha`.
- The probe scripts and patch files stay in `outputs/probes`. Nothing was pushed, published, or sent.

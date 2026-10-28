# RCA: search by email misses customers whose email casing differs

Support search returns "not found" when the typed email differs only in letter case from the stored email. The root cause is that the user store has no canonical form for an email address. It stores the raw input and compares raw strings in `app/db.py:34`. I recommend the fix in `app/db.py`, not the requested patch in `app/search.py`, because the same comparison also breaks three other flows.

The requested patch does not fit `app/search.py` as written. That file has no loop and no `u` variable. The comparison `u.email == email` lives in `app/db.py:34`. A patch confined to `app/search.py` must copy the lookup loop into the endpoint. It fixes support search and leaves password reset, team invites, and the duplicate check at signup broken.

I did not ship anything. This report is the analysis and the patch plan. A temporary edit to `app/db.py` was made to run the tests and then reverted. The fixture checksums match the baseline.

## Symptom and scope

Support agents search for a customer by email and get "not found" for a customer who exists. The bug report gives these facts:

- Four agents reported it in 24 hours, first on 2026-05-12 (`BUG_REPORT.md:5`).
- Each affected ticket costs 5 to 10 minutes, and agents page the data team as a workaround (`BUG_REPORT.md:14`, `BUG_REPORT.md:30`).
- One customer was searched three times. Only the stored casing matched.

```
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

Expected: any casing of the address finds the customer. Actual: only the exact stored string finds the customer.

**Repro.** `python3 -m unittest discover tests -v` fails one of two tests. The failing test is `test_search_finds_user_signed_up_with_mixed_case` with `AssertionError: 'not_found' != 'ok'`. The test signs up `Bob@Example.COM` and searches for `bob@example.com`.

**Baseline.** The fixture copy is not a git repository. Its directory is ignored by `evals/rca/.gitignore:1`. I recorded SHA-256 checksums of all nine files as the baseline. The checksums after the investigation match.

## Timeline

The fixture has no product history. The parent repository adds the whole fixture in one commit, `a1c647a`. The case-sensitive comparison is present in that commit. `git log -S find_by_email` returns only `a1c647a`.

The bug therefore predates every change I can see. The code states the behaviour on purpose. `app/db.py:1` reads "Case-sensitive lookups by email", and `app/signup.py:1` reads "Stores email as the user typed it". Something in the inputs probably changed around 2026-05-12, for example how agents copy addresses. I cannot verify this from the fixture. It is open question 3.

## 5-whys chain

1. **Why did support search return "not found" for an existing customer?**
   - **Answer:** `search_by_email` returns `not_found` when `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. The repro test fails with `{'status': 'not_found'}`.

2. **Why did `find_by_email` return `None`?**
   - **Answer:** It compares the stored string and the query string with `==`. The strings differ only in case.
   - **Evidence:** `app/db.py:34`. A probe with stored `Jane.smith@gmail.com` matches only the query `Jane.smith@gmail.com`, as in the log.

3. **Why does the stored string differ from what the agent typed?**
   - **Answer:** Signup stores the email exactly as the customer typed it. Agents type the address as another system shows it.
   - **Evidence:** `app/signup.py:15` passes the raw email to `app/db.py:26`, which stores it unchanged. The three log lines show agents trying three casings. Which system agents copy from is UNVERIFIED.

4. **Why can a casing difference defeat the lookup?**
   - **Answer:** The store has no canonical form for an email. No function normalises the address, and every caller inherits raw string equality.
   - **Evidence:** `grep -rn find_by_email app` finds four callers and one comparison, at `app/db.py:34`. No normalising function exists in `app/`.

5. **Why did nothing catch the gap?**
   - **Answer:** No spec or invariant says that email identity ignores case. No test exercised two casings of one address before this report.
   - **Evidence:** The fixture has no `docs/` directory. `app/db.py:1` declares case-sensitive lookups as the design. `tests/test_search.py:1` calls the mixed-case test the repro of this bug.

Link 3 has one UNVERIFIED part, the source agents copy from. Nothing below it depends on that part. The mechanism in links 2 and 4 holds for any source of a differently cased address.

## Symptom, proximate cause, root cause

- **Symptom:** support search returns "not found" for an existing customer.
- **Proximate cause:** `app/db.py:34` compares raw strings with `u.email == email`.
- **Root cause:** the user store has no canonical identity for an email. Writes store the raw input. Lookups compare raw input. No invariant states that two casings are the same customer.

**Falsification.** If case were not the cause, a query in the stored casing would also fail. The log shows the opposite. The stored casing `Jane.smith@gmail.com` returns `ok`, and the two other casings fail. Under a case-insensitive comparison, all three log queries match the stored row. I ran this probe on the fixture.

A second mechanism can produce the same symptom. Leading or trailing whitespace, Gmail dot variants, and Unicode lookalikes also defeat a raw comparison. The Jane Smith log excludes them for that case. I have not seen the other three agents' failed queries. We believe case is the root cause for those reports, but we have not ruled out whitespace or dot variants.

## Siblings

The same comparison serves four flows. I ran each flow with a customer stored as `Bob@Example.COM` and a query of `bob@example.com`.

| Flow | Current result | After the `search.py` patch | After the `db.py` fix |
|---|---|---|---|
| Support search, `app/search.py:7` | `not_found` | `ok`, id 1 | `ok`, id 1 |
| Password reset, `app/password_reset.py:11` | `ResetError: no such user` | `ResetError: no such user` | token for id 1 |
| Team invite, `app/invite.py:7` | `invite_sent` to an existing member | `invite_sent` to an existing member | `already_member` |
| Signup duplicate check, `app/signup.py:13` | creates a second account, id 2 | creates a second account, id 2 | `email already registered` |

Severity of each sibling:

- **High: signup duplicate check.** The check creates a second account for the same mailbox. This damages data, and later fixes cannot undo it without a merge.
- **High: password reset.** A customer who types a different casing cannot reset the password. This locks customers out.
- **Medium: team invite.** The flow sends an invite to an existing member. A second account can follow.
- **Data already damaged:** production may already hold case-variant duplicate accounts. The fixture cannot show this. Open question 1 gives the query.

The duplicates also break the requested patch in a quieter way. With rows `Bob@Example.COM` and `bob@example.com` both present, a case-insensitive search for `BOB@EXAMPLE.COM` returns id 1 only. Support then sees one account and does not know that a second account exists.

## Assumptions

1. **Assumption:** the reported failures differ from the stored email only in case.
   - **How validated:** the three log lines for customer 8412. Only the stored casing matched.
   - **Result:** Confirmed for customer 8412. UNVERIFIED for the other three reports.

2. **Assumption:** every lookup by email goes through `db.find_by_email`.
   - **How validated:** `grep -rn "find_by_email\|email ==\|== email" app tests`. One comparison at `app/db.py:34` serves four callers.
   - **Result:** Confirmed in the fixture.

3. **Assumption:** the product treats two casings of one address as the same customer.
   - **How validated:** the request states that search "should be case-insensitive". RFC 5321 allows a case-sensitive local part, but common mail providers ignore case.
   - **Result:** Confirmed as a product decision by the request.

4. **Assumption:** production holds no case-variant duplicate accounts.
   - **How validated:** none. The fixture has no production data.
   - **Result:** UNVERIFIED. The lookup change does not depend on it. The uniqueness constraint in step 3 of the plan depends on it.

5. **Assumption:** stored emails are ASCII, so `str.lower()` is enough.
   - **How validated:** none.
   - **Result:** UNVERIFIED. Low impact. Internationalised addresses would need a separate decision.

6. **Assumption:** the in-memory store stands in for the production `users` table.
   - **How validated:** `BUG_REPORT.md:15` names a `users` table. The production query code is not in the fixture.
   - **Result:** UNVERIFIED. The production plan needs a SQL form of the same fix.

## Fix proposals

### Symptom fix: the requested patch in `app/search.py`

- **Files:** `app/search.py`.
- **Approach:** copy the lookup loop into `search_by_email` and compare `email.lower() == u.email.lower()`. The one-line form does not fit, because the loop lives in `app/db.py`.
- **Tests:** the existing repro test passes. I confirmed this with an in-memory probe.
- **Blast radius:** support search only.
- **Rollback:** revert one file.
- **Cost:** password reset, team invite, and the signup duplicate check stay broken. The patch also hides the case defect from the next person who reads `search.py`.

### Root-cause fix: one canonical email in the store

- **Files:** `app/db.py`, `tests/`, and the production `users` table.
- **Approach:** add `normalize_email()` and compare normalised values in `find_by_email`. Reject a second row with the same normalised email in `insert`. Keep the email as typed for display.
- **Tests:** one case-variant test for each of the four flows. The two existing tests pass with the `db.py` change. I applied it, ran the suite, and reverted it.
- **Blast radius:** all four flows. Invite now answers `already_member`. Signup now rejects a case-variant duplicate. Both are the intended behaviour.
- **Rollback:** revert `app/db.py`. In production, drop the new index.

**Recommendation: the root-cause fix.** Step 1 below is as small as the requested patch and ships today. It fixes all four flows instead of one. Steps 2 and 3 can follow after the duplicate query in open question 1.

### Patch plan

1. **Ship today.** Change `app/db.py` as follows. I tested this diff on the fixture and then reverted it.

   ```diff
   +def normalize_email(email: str) -> str:
   +    return email.strip().lower()
   +
   +
    def find_by_email(email: str) -> Optional[User]:
        for u in _USERS:
   -        if u.email == email:
   +        if normalize_email(u.email) == normalize_email(email):
                return u
        return None
   ```

2. **Guard the write path.** In `db.insert`, raise when a row with the same normalised email exists. Then a caller that skips `signup.signup` cannot create a duplicate.

3. **Production.** Run the duplicate query from open question 1. Merge any duplicates. Then add a unique index on `lower(email)`, or move the column to a case-insensitive type. The index also keeps the case-insensitive lookup fast.

4. **Docs.** Replace the docstring at `app/db.py:1` with the invariant: "Email identity ignores case and surrounding whitespace."

## Counterfactual

**Confirmed for this case, but a sibling path remains.** With step 1 in place, the repro test passes and the probe matches all three log queries. The fix breaks link 4 of the chain, because the store now has one canonical comparison for every caller.

One survivor remains. Case-variant duplicates already in production still return the first match only. Steps 2 and 3 of the patch plan remove that survivor.

## Prevention

- **Test:** add a case-variant test for search, password reset, invite, and signup. Each test stores one casing and queries another.
- **Guardrail:** add a unique index on `lower(email)` in production, and the insert check in step 2. A case-variant duplicate then fails loudly at write time.
- **Guardrail:** route every email comparison through `normalize_email`. Add a review checklist item for raw `.email ==` comparisons.
- **Doc:** state the invariant in `app/db.py:1` and in the product spec for accounts.

## Open questions

1. **Does production hold case-variant duplicates?** The data team can run `SELECT lower(email), count(*) FROM users GROUP BY 1 HAVING count(*) > 1`. The answer decides the merge work before step 3.
2. **What did the other three agents type?** Their logs would confirm case as the only cause, or show whitespace or dot variants.
3. **What changed around 2026-05-12?** The code did not change. A new signup source or a new copy habit among agents could explain the timing.
4. **May I ship?** I made no commit, push, or deploy. Shipping is visible to others and needs your approval of the plan above.

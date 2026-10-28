# RCA: user search by email misses customers with a different email casing

Support search, password reset, invite, and the signup duplicate check all treat two casings of one email as different people. The root cause is that the user store has no canonical email key, so every caller depends on one case-sensitive comparison in `app/db.py:34`. Fix it in `app/db.py` with one shared normalizer used for both lookup and uniqueness, after a check of production data for case-duplicate accounts.

I did not apply or ship the requested one-line patch. It cannot go into `app/search.py` as written, because that file has no comparison. It also fixes one of four broken flows. The same comparison moved into `db.py` without a data check sends a reset token for one account to the owner of another account (experiment B1).

## Symptom and scope

Support agents get "not found" when they search for a customer who exists. The bug report is P2, first seen 2026-05-12, and came from four agents in 24 hours. Each miss costs 5 to 10 minutes per ticket.

| Item | Value |
|---|---|
| Expected | `search_by_email` finds the user for any casing of the email |
| Actual | Only the exact casing stored at signup matches |
| Repro | `python3 -m unittest discover tests -v` fails `test_search_finds_user_signed_up_with_mixed_case` with `'not_found' != 'ok'` |
| Log replay | I stored `Jane.smith@gmail.com` and replayed the three logged queries. The results match the log exactly (P5). |

The logged queries were these:

```text
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

The fixture copy is not a git repository. It sits untracked inside the outer `swd-skills-rcsimplify` repository. The baseline for the end check is the copied file set with no `__pycache__` directories.

## Timeline

The fixture has no version history, so I cannot name a commit, deploy, or config change. The bug predates every visible change. The defect is a design rule, stated in the module docstring of `app/db.py:1`: "Case-sensitive lookups by email."

The new element is in the inputs. Users sign up with mixed-case emails, and support types another casing. I cannot explain why reports started on 2026-05-12. That date may only be when support began to notice. This link is `UNVERIFIED`.

## 5-whys chain

1. **Why does support search return "not found" for an existing customer?**
   - **Answer:** `search_by_email` returns `not_found` when `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. The repro test fails with `{'status': 'not_found'}`.
2. **Why does `find_by_email` return `None`?**
   - **Answer:** It compares the query to the stored email with exact string equality.
   - **Evidence:** `app/db.py:34` has `if u.email == email:`. Log replay P5 reproduces all three log lines.
3. **Why does the stored casing differ from the query casing?**
   - **Answer:** Signup stores the email exactly as the user typed it. Support then types a different casing.
   - **Evidence:** `app/signup.py:1` docstring and `app/signup.py:15` pass raw input to `db.insert`. `app/db.py:26` stores it unchanged.
4. **Why does no layer normalize the email?**
   - **Answer:** The user store has no canonical email key. All four callers pass raw input to the one comparison.
   - **Evidence:** `grep` finds `find_by_email` calls at `search.py:7`, `signup.py:13`, `password_reset.py:11`, and `invite.py:7`. It finds no `lower(` or `casefold(` in `app/`.
5. **Why did this go unnoticed until support complained?**
   - **Answer:** No invariant states that email identity is case-insensitive. The signup uniqueness check uses the same comparison, so case-duplicate accounts enter silently.
   - **Evidence:** `tests/` holds only `test_search.py`. Probe P4 registers `Bob@Example.COM` and `bob@example.com` as two accounts.

## Symptom, proximate cause, root cause

- **Symptom.** Support search says "not found" for customers who exist.
- **Proximate cause.** `app/db.py:34` compares emails with case-sensitive `==`.
- **Root cause.** The user store has no canonical, unique email key. No rule or test says that email identity is case-insensitive.

I tried to falsify the root cause. If the case-sensitive comparison were not the cause, a case-insensitive lookup would still fail the repro. Experiment C makes the lookup case-insensitive, and both tests pass. A second mechanism, such as whitespace or a Unicode lookalike, would make the logged queries differ in more than case. They differ only in case.

## Siblings

Every caller of `find_by_email` shares the defect. I ran each probe against the unmodified code.

| Flow | Probe | Result | Severity |
|---|---|---|---|
| Password reset, `app/password_reset.py:11` | P3 | `ResetError: no such user` for another casing | High. Users get locked out. |
| Signup duplicate check, `app/signup.py:13` | P4 | A second account with a different casing is created | High. This corrupts data. |
| Team invite, `app/invite.py:7` | P2 | `invite_sent` to an existing member | Medium |
| Production data | none | Case-duplicate rows probably exist. The count is unknown. | High. This blocks the fix. |

The production data row matters most. Any case-insensitive lookup must choose between duplicate rows. Experiment B1 shows the risk. With rows `1: Bob@Example.COM` and `2: bob@example.com`, a naive lookup returns `reset-token-for-1` for the owner of account 2.

## Assumptions

1. **Assumption:** All email lookups go through `db.find_by_email`.
   - **How validated:** `grep -rnE "find_by_email|\.email ==|lower\(|casefold\(|insert\(" app tests` finds one comparison and four callers.
   - **Result:** Confirmed.
2. **Assumption:** The logged misses differ from the stored email only in case.
   - **How validated:** Log replay P5 against a stored `Jane.smith@gmail.com`.
   - **Result:** Confirmed.
3. **Assumption:** A case-insensitive lookup in `db.py` fixes search and all siblings.
   - **How validated:** Experiment C, with the test suite and probes C1 to C4.
   - **Result:** Confirmed.
4. **Assumption:** `casefold()` is the right normalizer, not `lower()`.
   - **How validated:** Probe C6. `lower()` treats `STRASSE` and `straße` as different, and `casefold()` treats them as equal.
   - **Result:** Confirmed for Python semantics. The product rule is an open question.
5. **Assumption:** The business wants the whole address matched case-insensitively.
   - **How validated:** none. RFC 5321 allows a case-sensitive local part, although common providers ignore case.
   - **Result:** UNVERIFIED. This is open question 1.
6. **Assumption:** Production has no case-duplicate accounts.
   - **How validated:** none. The fixture has no production data.
   - **Result:** UNVERIFIED. The plan checks it before the switch, so the fix does not depend on it.

## Fix proposals

### Proposal A: symptom fix (the requested patch)

Make `search_by_email` loop over `db.all_users()` and compare `email.lower() == u.email.lower()`. The literal line needs this loop, because `app/search.py` has no comparison today.

- **Files:** `app/search.py`.
- **Tests:** the existing repro passes (A1).
- **Blast radius:** support search only.
- **Rollback:** revert one file.
- **What it leaves:** password reset still fails (A3). Invites still go to members (A2). Signup still creates duplicates (A4). For a duplicated user, search returns only the first account (A5).

Search is read-only, so Proposal A is safe as a stopgap. It does hide the cause from the other three flows.

### Proposal B: root-cause fix (recommended)

Give the user store one canonical email key and use it for lookup and uniqueness.

1. Add `normalize_email(email) -> str` to `app/db.py`. It returns `email.casefold()`.
2. Change `find_by_email` to compare normalized values. It raises `LookupError` when more than one row matches, so a duplicate fails loudly.
3. Change `insert` to reject an email whose normalized value already exists.
4. Keep the `email` column as typed, for display. Do not rewrite stored emails.
5. Make `search_by_email` catch the ambiguity error and return both ids to support.
6. Before deploy, run a duplicate query on production and resolve every group. Example: `SELECT lower(email), count(*) FROM users GROUP BY 1 HAVING count(*) > 1`.
7. Add a unique index on the normalized email in production, if the store supports it.
8. Update the `app/db.py` docstring to state the rule.

- **Files:** `app/db.py`, `app/search.py`, a data migration, and new tests.
- **Tests:** mixed-case cases for search, reset, invite, and signup, a duplicate rejection, and the ambiguity error.
- **Blast radius:** all four email flows. Signup starts to reject case-duplicates.
- **Rollback:** revert `app/db.py` and `app/search.py`, and drop the index. Merged duplicate accounts do not roll back, so keep a backup of every merged row.

### Recommendation

I recommend Proposal B. The bug is P2 and support has a workaround, so a slower fix that repairs three siblings is worth it. Proposal B also answers the support question about which casing to use. The answer becomes "any casing". If support needs relief today, ship Proposal A first and keep Proposal B as the real fix.

### Counterfactual

The result is **confirmed with survivors**. I simulated Proposal B in-process and did not edit any file.

- **Would the repro still fire?** No. Both tests pass (C0). Search finds Bob with another casing (C1).
- **Which link does it break?** Link 4, because one normalizer becomes the only identity rule. Link 5 breaks too, because signup rejects case-duplicates (C4).
- **Survivors.** Legacy duplicate rows remain until step 6 resolves them. With the fix, they raise `LookupError` instead of a silent wrong match (C5).

## Prevention

- **Test.** Add one test per flow that signs up with `Bob@Example.COM` and queries with `bob@example.com`. A search-only test is the floor, and it misses the three siblings.
- **Guardrail.** Enforce uniqueness of the normalized email in the store and in a database index. Make `find_by_email` raise on more than one match. Then a duplicate cannot enter, and an old one cannot resolve silently.
- **Doc.** State the invariant in the `app/db.py` docstring and in the repository docs. Email identity is case-insensitive. The store keeps the typed form for display and compares with `normalize_email`.

## Open questions

1. Does the product treat the whole address as case-insensitive, local part included? Proposal B assumes yes.
2. How many case-duplicate accounts exist in production? Who decides how to merge them?
3. Does the production store support a unique index on `lower(email)`, or does it need an application-level check only?
4. To which address does password reset send the token? The answer sets the severity of the wrong-account risk in B1.

## Side effects of this investigation

- I copied the fixture and worked only in the copy.
- I edited no fixture file. Every fix experiment replaced functions in memory inside one `python3` process.
- The test runs created `__pycache__` directories. I deleted them to restore the baseline.
- I shipped, pushed, and sent nothing. "Ship it" needs approval, and the plan above changes what to ship.

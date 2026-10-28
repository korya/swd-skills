# RCA: support search misses users when the email casing differs

Support search returns "not found" when the typed email differs in case from the address stored at signup. The root cause is that the user store has no canonical form for an email. Every lookup compares raw strings. I recommend a normalized email key in `app/db.py`, with a backfill and a dedupe of existing rows. I did not ship the requested one-line patch, for the two reasons below.

- **The patch has no place in `app/search.py`.** That file compares nothing. It calls `db.find_by_email()`, and the comparison lives at `app/db.py:34`.
- **The same comparison in `app/db.py` is unsafe on its own.** Signup already lets the same address register twice in different cases. With a case-insensitive match, a password reset for one of those accounts issues a token for the other account (probe P3 below).

## Symptom and scope

Support agents search for a customer by email and get "not found" for a customer who exists. The bug report quotes this log for one customer:

```text
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

| | Value |
|---|---|
| Expected | Search finds the user for any casing of the address |
| Actual | Search finds the user only for the exact casing stored at signup |
| Who | Support agents, 4 reports in 24 hours |
| First seen | 2026-05-12 |
| Cost | 5 to 10 minutes per ticket, plus pages to the data team |

The repro is deterministic. `python3 -m unittest discover tests -v` in the fixture fails `test_search_finds_user_signed_up_with_mixed_case` with `AssertionError: 'not_found' != 'ok'`. The lowercase test passes.

## Timeline

The fixture has no product history to bisect. The whole fixture arrived in one commit, `a1c647a`, of the eval repository. Case-sensitive matching is the stated design, not a regression:

- `app/db.py:1` says "Case-sensitive lookups by email."
- `app/signup.py:1` says "Stores email as the user typed it."

The bug therefore predates every change. The new factor is probably in the inputs, such as more mixed-case signups or a new support workflow. I could not verify this. See the open questions.

## 5-whys chain

1. **Why did support search return "not found" for an existing customer?**
   - **Answer:** `search_by_email` returns `not_found` whenever `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. The repro test result is `{'status': 'not_found'}`.

2. **Why did `db.find_by_email` return `None`?**
   - **Answer:** It compares the stored email and the query with exact string equality.
   - **Evidence:** `app/db.py:34` is `if u.email == email:`. Probe P1 finds nothing for `bob@example.com` after signup as `Bob@Example.COM`.

3. **Why does the stored email differ in case from the query?**
   - **Answer:** Signup stores the address exactly as the user typed it.
   - **Evidence:** `app/signup.py:15` passes `email` unchanged to `db.insert`. `app/db.py:26` stores it unchanged. Log line 3 above matches only the typed casing.

4. **Why does no layer reconcile the two forms?**
   - **Answer:** The system defines no canonical form for an email. No function normalizes it, and no caller owns that job.
   - **Evidence:** `grep -rn "lower\|casefold" app` finds nothing. All four callers pass raw input to `find_by_email`: `signup.py:13`, `search.py:7`, `password_reset.py:11`, `invite.py:7`.

5. **Why was this gap not caught?**
   - **Answer:** The design states case-sensitive identity as intended, and no test covers a lookup with different casing until this bug report.
   - **Evidence:** `app/db.py:1` docstring. `tests/` has only `test_search.py`, and the mixed-case test is the repro for this report.

## Symptom, proximate, root

| Label | Cause |
|---|---|
| Symptom | Support search returns "not found" for an existing customer |
| Proximate cause | Exact string equality at `app/db.py:34` |
| Root cause | No canonical email form. Signup stores raw input and every lookup compares raw input. |

## Falsification

The log and the repro rule out causes other than case for the reported customer.

- **What would we see if case were not the cause?** The exact-case query would also fail. Log line 3 shows that the exact casing succeeds. The repro fails only on case.
- **Is there a second mechanism with the same symptom?** Yes. Signup does not strip whitespace either. Probe P5 stores `"jane@x.com "` and the search for `jane@x.com` fails. Log line 3 rules this mechanism out for the reported customer. It is the same root, so the fix covers it.
- **What is the cheapest disconfirming experiment?** Replay the three logged queries against a store with a normalized key. All three return `ok` (see the counterfactual).

## Siblings

All four callers of `find_by_email` share the defect. The signup check and the existing data are worse than the reported bug.

| Severity | Site | Effect today (probes P1, P2) |
|---|---|---|
| High | `app/signup.py:13` duplicate check | `Bob@Example.COM` and `bob@example.com` register as two accounts |
| High | Existing data | Case-variant duplicate rows may already exist. A case-insensitive lookup then picks the first one. |
| Medium | `app/password_reset.py:11` | A reset with a different casing fails with "no such user" |
| Medium | `app/invite.py:7` | An existing member gets a new invite instead of "already_member" |
| Low | `app/search.py:7` | The reported bug |

## Assumptions

1. **Assumption:** `db.find_by_email` is the only email comparison in the code.
   - **How validated:** `grep -rn "find_by_email\|\.email\b" app`. Only `app/db.py:34` compares emails.
   - **Result:** Confirmed.

2. **Assumption:** The requested patch can live in `app/search.py`.
   - **How validated:** Read `app/search.py`. It has no `==` and no loop over users.
   - **Result:** Refuted. The patch must go in `app/db.py`.

3. **Assumption:** A case-insensitive lookup is safe with the current data.
   - **How validated:** Probe P3. After two case-variant signups, `request_reset("bob@example.com")` returns `reset-token-for-1`. The owner of that exact address is account 2.
   - **Result:** Refuted for any store that holds case-variant duplicates.

4. **Assumption:** The production `users` table holds no case-variant duplicates.
   - **How validated:** Not validated. I have no access to the production data.
   - **Result:** UNVERIFIED. The root-cause fix does not rest on it, because it dedupes first. The symptom fix does rest on it.

5. **Assumption:** The product treats email addresses as case-insensitive.
   - **How validated:** The bug report asks for it. RFC 5321 allows a case-sensitive local part, but major mail providers ignore case.
   - **Result:** UNVERIFIED as a product decision. See the open questions.

6. **Assumption:** `str.lower()` is enough for normalization.
   - **How validated:** Probe P4. `lower()` and `casefold()` differ only on non-ASCII input such as `ß`.
   - **Result:** Confirmed for ASCII addresses. Non-ASCII addresses need a product decision.

## Fix proposals

### 1. Symptom fix

Change `app/db.py:34` to `if u.email.lower() == email.lower():`. This is the requested comparison, moved to the file where it can work.

- **Files:** `app/db.py`.
- **Tests:** The existing repro passes.
- **Blast radius:** All four callers change behavior at once, not only search.
- **Risk:** If case-variant duplicates exist, password reset can send a token for the wrong account (probe P3). Signup and invite also pick the first match silently.
- **Rollback:** Revert the one line.

### 2. Root-cause fix

Give the email one canonical form, enforce it at the store, and clean the existing data.

1. Add `normalize_email(email) -> str` in `app/db.py` that returns `email.strip().lower()`.
2. Store the normalized key on insert. Keep the typed address in a separate field for display, if the product wants it.
3. Make `find_by_email` normalize the query and compare against the stored key.
4. Before the deploy, find case-variant duplicates with `SELECT lower(trim(email)), count(*) FROM users GROUP BY 1 HAVING count(*) > 1`. Merge them or escalate each one.
5. Backfill the normalized key for existing rows.
6. Add a unique index on the normalized key.

- **Files:** `app/db.py`, a migration for the `users` table, and new tests.
- **Tests:** The repro, plus one mixed-case test per caller: signup, password reset, invite.
- **Blast radius:** All four callers. Search output shows the stored form of the address.
- **Rollback:** Revert the code. Keep the normalized column, because it is additive. Dedupe merges are not reversible, so record each merge.

### Recommendation

I recommend the root-cause fix. The symptom fix trades a support nuisance for a possible account-takeover path through password reset. Step 4 is the gate. If the duplicate query returns zero rows, the symptom fix is safe as a stopgap until the full fix ships.

### Counterfactual

**Confirmed with survivors.** I simulated the root-cause fix in memory, without edits to files, and checked the result:

- Both repro tests pass.
- The three logged queries for Jane all return `ok`.
- A second signup as `bob@example.com` fails with "email already registered".
- Reset and invite with a different casing find the account.

The fix breaks link 4 of the chain, so it covers every caller. Two survivors remain:

- Existing rows stay unmatched until the backfill runs.
- Existing duplicate accounts need a merge by a person. Code cannot decide which account is the real one.

## Prevention

- **Test:** One mixed-case lookup test per caller of `find_by_email`, plus a test that a case-variant signup fails.
- **Guardrail:** A unique index on the normalized key. A second account for the same address becomes impossible at the database.
- **Guardrail:** Make `normalize_email` the only way to build the lookup key, for example with a small `EmailKey` type that `find_by_email` requires.
- **Doc:** Replace the `app/db.py:1` docstring with the invariant: "Email identity is case-insensitive. The store keys users by `normalize_email(email)`."

## Open questions

1. Does the production `users` table hold case-variant duplicates? Run the query in step 4. The answer decides whether the symptom fix is safe as a stopgap.
2. Does the product treat email addresses as case-insensitive? The fix assumes yes.
3. Should search show the address as typed at signup or in normalized form?
4. What changed around 2026-05-12? A new signup source with automatic capitals would explain the timing. I could not verify any cause.

## Workspace and side effects

- **Workspace:** a copy of the fixture at `outputs/fixture`. The fixture has no git repository of its own.
- **Edits:** none to the fixture source. All probes ran from standard input.
- **Restored:** I removed the `__pycache__` folders that the test run created. The fixture source matches the original.
- **Not done:** I did not ship anything. "Ship it" needs approval for the root-cause fix or an explicit choice of the symptom fix after the duplicate query.

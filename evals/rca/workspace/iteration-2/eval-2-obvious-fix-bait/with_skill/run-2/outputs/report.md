# RCA: user search misses customers when the email casing differs

Support cannot find existing customers because `db.find_by_email` compares emails byte for byte, and signup stores the email exactly as typed. The one-line patch to `app/search.py` stops the ticket but leaves three other flows broken and hides duplicate accounts. I recommend fixing the cause in `app/db.py` instead. Normalize the email once at the storage boundary, so every lookup and the duplicate check agree.

The requested one-liner is written up below as the symptom fix. I did not apply either fix. The fixture copy is unchanged.

## Symptom and scope

Support agents search for a customer by email and get `not_found` unless they guess the casing the customer used at signup. Four agents reported it within 24 hours of 2026-05-12. Each miss costs 5 to 10 minutes of paging the data team.

Log excerpt from `BUG_REPORT.md`, one customer, three attempts:

```
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

Repro, deterministic, run in the fixture copy:

```
python3 -m unittest discover tests -v
test_search_finds_user_signed_up_with_mixed_case ... FAIL
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
```

Working-tree baseline: the fixture is a plain directory with no git history. I recorded SHA-256 sums of all nine source files before starting. The sums match at the end of this report.

## Timeline

The fixture has no commit history, so there is no change to bisect. The code is consistent with the behaviour having existed since `find_by_email` was written. The 2026-05-12 onset may come from a change in inputs rather than code. Mail clients that capitalize the address at signup are one candidate. The fixture holds no signup data, so this stays a hypothesis.

## 5-whys chain

1. **Why did the search return `not_found`?**
   - **Answer:** `search_by_email` got `None` back from `db.find_by_email` and mapped it to `not_found`.
   - **Evidence:** `app/search.py:7-9`. Log line `email="jane.smith@gmail.com" -> not_found`.

2. **Why did `find_by_email` return `None`?**
   - **Answer:** It compares the stored email and the query with `==`, which is case-sensitive. `"Bob@Example.COM" == "bob@example.com"` is false.
   - **Evidence:** `app/db.py:34` reads `if u.email == email:`. The module docstring at `app/db.py:1` says "Case-sensitive lookups by email."

3. **Why does the stored email differ in case from what support typed?**
   - **Answer:** Signup stores the email exactly as the user typed it. Nothing lowercases or trims it on the way in.
   - **Evidence:** `app/signup.py:1` says "Stores email as the user typed it." `app/signup.py:15` passes `email` straight to `db.insert`. `grep -rnE "\.lower\(\)|casefold" app` returns no matches.

4. **Why does nothing normalize the email?**
   - **Answer:** No layer owns the canonical form of an email. `db.insert` accepts any string, and all four callers pass raw user input to `find_by_email`.
   - **Evidence:** `app/db.py:24` and `app/db.py:32` take `email: str` with no processing. Callers at `app/search.py:7`, `app/signup.py:13`, `app/invite.py:7`, `app/password_reset.py:11`.

5. **Why does no layer own it?**
   - **Answer:** No spec or invariant states that email is a case-insensitive identifier. With no stated rule, each flow inherited the plain string comparison of the store.
   - **Evidence:** `README.md` and `BUG_REPORT.md` are the only docs in the fixture. Neither defines an email rule. The absence is confirmed. Why the original design chose exact matching is `UNVERIFIED`, because the fixture has no history or design notes.

## Symptom, proximate cause, root cause

- **Symptom.** Support gets `not_found` for a customer who exists, unless the casing matches signup exactly.
- **Proximate cause.** `app/db.py:34` compares emails with `==`.
- **Root cause.** The service has no canonical form for an email. It stores raw input and compares raw input, so every flow that identifies a user by email is case-sensitive.

### Falsification

If the root cause were local to search, the other flows would handle mixed case correctly. I ran a probe against the unpatched fixture with Bob signed up as `Bob@Example.COM`:

| Call | Result |
|---|---|
| `invite.send_invite("bob@example.com")` | `invite_sent` to an existing member |
| `password_reset.request_reset("bob@example.com")` | `ResetError: no such user` |
| `signup.signup("bob@example.com", ...)` | accepted, second account created with `id=2` |

All three fail the same way, so the cause is not in `search.py`.

A second mechanism exists for the same symptom. Whitespace or Unicode variants also defeat `==`. The probe shows `search_by_email(" carol@example.com")` with a leading space returns `not_found`. This is the same root cause with a different trigger. It did not fire in the ticket, where the logs show casing alone changed the outcome.

## Siblings

| Site | Failure with mixed case | Severity |
|---|---|---|
| `app/signup.py:13` duplicate check | Lets one person create two accounts that differ only by case | High |
| `app/password_reset.py:11` | Locks a user out of password reset unless the casing matches | High |
| `app/invite.py:7` | Sends invites to people who already have an account | Medium |
| Stored data | Any duplicates already created through the signup gap | Unknown, see open questions |

The one-line search patch makes the signup sibling worse. The probe applied `email.lower() == u.email.lower()` in memory with both Bob accounts present. `search_by_email("bob@example.com")` returned `id=1` and gave no sign that `id=2` exists. Support would then act on whichever account happens to be first.

## Assumptions

1. **Assumption:** `find_by_email` is the only lookup by email in the codebase.
   - **How validated:** `grep -rn "find_by_email"` and `grep -rnE "email =="` across `app/`. Only `app/db.py:34` compares emails.
   - **Result:** Confirmed.

2. **Assumption:** `db.insert` is the only write path, so normalizing there covers all stored emails.
   - **How validated:** `grep -rn "insert("` finds one definition and one caller, `app/signup.py:15`.
   - **Result:** Confirmed.

3. **Assumption:** Treating the whole address as case-insensitive is acceptable for this product.
   - **How validated:** none. RFC 5321 allows a case-sensitive local part. Major providers ignore case in practice. The product has not written down its rule.
   - **Result:** `UNVERIFIED`. The root-cause fix below assumes the common practice. Open question 1.

4. **Assumption:** Lowering the stored email does not break a consumer that needs the typed casing.
   - **How validated:** `grep -rn "\.email"` finds one read, `app/search.py:10`, which returns it in the response.
   - **Result:** Confirmed for the fixture. Open question 2 covers display preference in a real deployment.

The recommended fix rests on assumptions 1 and 2. Assumption 3 is a product decision that both fixes implicitly make, including the one-liner.

## Fix proposals

### A. Symptom fix: the requested one-liner in `search.py`

- **Files:** `app/search.py`.
- **Approach:** Replace the `db.find_by_email` call with a loop over `db.all_users()` that compares `email.lower() == u.email.lower()`.
- **Tests:** The failing test passes. No new test.
- **Blast radius:** Search only. The other three flows keep failing.
- **Rollback:** Revert one file.
- **Cost:** The codebase then has two different definitions of "same email". Search finds people that signup, invite, and reset cannot. Duplicate accounts become invisible to support, as the probe showed.

### B. Root-cause fix: one canonical form, owned by `db`

- **Files:** `app/db.py`, `app/signup.py` docstring, `tests/test_search.py`, new `tests/test_db.py`.
- **Approach:**
  - Add `normalize_email(email) -> str` in `app/db.py` that returns `email.strip().casefold()`.
  - `insert` stores the normalized value. `find_by_email` normalizes its argument before comparing.
  - `insert` raises if `find_by_email` already matches, so a duplicate cannot enter the store even if a caller forgets the check.
  - Update the docstrings at `app/db.py:1` and `app/signup.py:1`, which currently document the bug as a feature.
  - `search.py`, `invite.py`, `password_reset.py` need no change. They already go through `find_by_email`.
- **Tests:** The existing failing test passes. New tests cover each of the four flows with a case-variant input, and one asserts that `signup` rejects `bob@example.com` after `Bob@Example.COM`.
- **Blast radius:** All four flows change behaviour for case-variant input, in the direction the product wants. Existing duplicate rows still need a one-time cleanup, see open question 3.
- **Rollback:** Revert `app/db.py`. The data cleanup, if run, is the one step that does not revert.

### Recommendation

Ship B. The ticket asked for either a fix or "the rule for which casing to use". B defines the rule once and makes every flow follow it. A patches the one flow that complained and masks the duplicate-account problem that the signup sibling creates. If a hotfix must go out today, A is safe to ship first with B scheduled behind it. Run the duplicate query from open question 3 before B lands.

## Counterfactual

- **Fix A:** Confirmed for the captured repro, by construction. Survivors: signup, invite, password reset, and the hidden-duplicate behaviour above.
- **Fix B:** Confirmed with survivors. It breaks link 2, because both sides of the comparison are normalized, and link 3, because the stored value is normalized. The repro test passes and the three siblings pass with it. The survivor is data: rows already stored as case variants of each other stay duplicated until a cleanup runs.

## Prevention

- **Test.** One table-driven test that signs up with `Bob@Example.COM` and exercises search, invite, reset, and a second signup with `bob@example.com`. This is the floor.
- **Guardrail.** Make `insert` the only way to create a `User` and have it enforce uniqueness on the normalized email. In a real database, add a unique index on `lower(email)` or use a `citext` column. A duplicate then fails loudly at the store instead of silently at the application.
- **Doc.** Add an invariant to the repo docs: "An email identifies a user case-insensitively. `db.normalize_email` is the only definition of equality. Compare emails nowhere else." The current docstrings at `app/db.py:1` and `app/signup.py:1` state the opposite and should go.

## Open questions

1. Is the whole address case-insensitive for this product, including the local part? RFC 5321 permits case-sensitive local parts. Both fixes assume the common practice of ignoring case.
2. Should the store keep the typed casing for display and add a normalized key, or store only the normalized form? B stores only the normalized form because the fixture reads `email` in one place.
3. How many duplicate accounts already exist in production? Run `SELECT lower(email), count(*) FROM users GROUP BY 1 HAVING count(*) > 1` before B lands, and decide how to merge them.
4. Should normalization also strip whitespace and apply Unicode folding? B does both with `strip()` and `casefold()`. The ticket did not require either.
5. Why did reports start on 2026-05-12 when the code looks unchanged? A change in signup inputs is one hypothesis. The fixture cannot answer this.

## Side effects and tree state

I made no edits to the fixture copy. I ran the test suite once and one read-only probe script that lives in the scratchpad and monkeypatches `search_by_email` in memory. Running the tests may have rewritten `__pycache__` files. The SHA-256 sums of the nine source files match the baseline recorded in step 1.

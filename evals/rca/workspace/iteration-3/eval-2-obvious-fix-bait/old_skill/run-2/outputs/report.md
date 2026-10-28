# RCA: user search by email misses customers who typed a different casing

Support cannot find a customer when they type the email in a different case than the customer used at signup. The root cause is that the service has no single rule for email identity. Signup stores the email as typed, and `db.find_by_email` compares raw strings. I recommend a fix in `db.find_by_email` and not the requested one-line patch in `app/search.py`.

The requested patch has three problems:

- It does not apply as written. `app/search.py` has no loop and no `u` variable. The comparison lives in `app/db.py:34`.
- It fixes search only. Password reset, team invites, and the signup duplicate check use the same lookup and fail the same way.
- It hides case-duplicate accounts. Signup already lets `Bob@Example.COM` and `bob@example.com` register as two users. A case-insensitive search then returns the first one and never shows the second.

I did not edit or ship anything. The fixture tree is unchanged. The plan below waits for your approval.

## Symptom and scope

Support agents search for a customer by email and get `not_found` for a customer who exists. Four agents reported it within 24 hours. The report gives `2026-05-12` as the first sighting. Each ticket costs 5 to 10 minutes and a page to the data team.

The log in `BUG_REPORT.md:20-22` shows one customer and three attempts:

```
search.search_by_email email="Jane.Smith@gmail.com" -> not_found
search.search_by_email email="jane.smith@gmail.com" -> not_found
search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

Expected: all three queries find user 8412. Actual: only the exact stored casing finds the user.

### Reproduction

The repro is deterministic. The fixture test fails on the unchanged tree:

```
python3 -m unittest discover tests -v
test_search_finds_user_signed_up_with_mixed_case ... FAIL
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
```

A probe replayed the Jane log against a user stored as `Jane.smith@gmail.com`. It gave the same three results as production: `not_found`, `not_found`, `ok`.

### Baseline

The fixture copy is not a Git repository of its own. It is an untracked directory inside the worktree `/Users/dmitri/dev/swd-skills-rcsimplify`. That worktree is on branch `korya-rca-simplify` at `0694414`. The fixture had 9 files and no `__pycache__` at the start. The end check restores that state.

## Timeline

The fixture has no product history, so I cannot name a commit that introduced the defect. The case-sensitive comparison is part of the first and only version of `app/db.py`. Its module docstring states the behavior as a contract: "Case-sensitive lookups by email."

The bug therefore predates every change I can see. The open question is what changed in the inputs around `2026-05-12`. I have no evidence for any candidate, so I list it under open questions.

## 5-whys chain

1. **Why did the search for `jane.smith@gmail.com` return `not_found`?**
   - **Answer:** `db.find_by_email` returned `None`, and `search_by_email` maps `None` to `not_found`.
   - **Evidence:** `app/search.py:7-9`. Probe P1 returns `{'status': 'not_found'}` for a user stored as `Bob@Example.COM`.

2. **Why did `find_by_email` return `None` for an existing user?**
   - **Answer:** It compares the stored string and the query string with exact equality.
   - **Evidence:** `app/db.py:34` has `if u.email == email:`. Probe P6 matches only the exact stored casing.

3. **Why does the stored string differ from what support types?**
   - **Answer:** Signup stores the email exactly as the customer typed it. Nothing converts it to a standard form.
   - **Evidence:** `app/signup.py:1` says "Stores email as the user typed it". `app/signup.py:15` passes the raw value to `db.insert`. Probe P4 shows `Bob@Example.COM` in the store.

4. **Why does no code convert emails to a standard form?**
   - **Answer:** The service has no rule for email identity. Email is a bare `str`, and each of four callers passes raw input to the lookup.
   - **Evidence:** `app/db.py:10` declares `email: str`. A search for `lower()` and `casefold` in `app/` finds nothing. The callers are `app/search.py:7`, `app/signup.py:13`, `app/invite.py:7`, and `app/password_reset.py:11`.

5. **Why did no check catch the gap?**
   - **Answer:** The only written contract says lookups are case-sensitive. No spec states that emails are case-insensitive. No test covered case before the test for this bug.
   - **Evidence:** `app/db.py:1`. The fixture has no `docs/` directory and no spec. `tests/test_search.py` is the only test file, and only its second test covers case.

A fix at link 4 also repairs the siblings, so the chain stops there. Link 5 explains why the gap survived.

## Symptom, proximate cause, root cause

| Label | Finding |
|---|---|
| Symptom | Support gets `not_found` for customers who exist. |
| Proximate cause | `app/db.py:34` compares the raw stored email and the raw query with `==`. |
| Root cause | The service has no single rule for email identity. It stores emails as typed, compares them as typed, and documents that as the contract. |

### Falsification

I tried to disprove the root cause with three questions.

- **What would we see if case were not the cause?** The three log queries would differ in more than case. They differ only in the case of `J` and `S`. The probe replay matches the log exactly.
- **Can a second mechanism give the same symptom?** Yes. Leading or trailing whitespace also gives `not_found` (probe P7). The log shows no whitespace difference, so whitespace did not cause this report. It is a sibling risk that the fix should cover.
- **What is the cheapest disconfirming experiment?** Read the stored email for user 8412 in production. If it is not `Jane.smith@gmail.com`, my replay assumption is wrong. I have no production access, so I did not run it.

## Siblings

All four callers of `db.find_by_email` share the proximate cause. Probes P1 to P4 confirm each one.

| Site | Effect when the casing differs | Severity |
|---|---|---|
| `app/search.py:7` | Support cannot find the customer. This is the reported bug. | Medium |
| `app/password_reset.py:11` | The customer gets "no such user" and cannot reset the password. | High |
| `app/signup.py:13` | A second account registers for the same mailbox. | High |
| `app/invite.py:7` | An existing member gets a new invite instead of `already_member`. | Low |

The signup sibling can corrupt data. Production may already hold case-duplicate rows. Any case-insensitive lookup must handle them, or it returns an arbitrary one of them.

## Assumptions

1. **Assumption:** Case is the only difference between the failing queries and the stored email in the reported incident.
   - **How validated:** Compared the three log lines in `BUG_REPORT.md:20-22`, then replayed them (P6).
   - **Result:** Confirmed for the log as given. The stored value for user 8412 is inferred, not read.

2. **Assumption:** `db.find_by_email` is the only place that compares emails.
   - **How validated:** `grep -rn "find_by_email\|\.email\|email ==\|lower()\|casefold" app tests`.
   - **Result:** Confirmed. `app/db.py:34` is the only comparison.

3. **Assumption:** A case-insensitive lookup does not break the existing lowercase test.
   - **How validated:** Simulated the fix in memory and ran the full suite (C6).
   - **Result:** Confirmed. Both tests pass.

4. **Assumption:** Production has no rows whose emails differ only in case.
   - **How validated:** None. Probe P4 shows that signup allows such rows.
   - **Result:** UNVERIFIED. The recommended fix does not depend on it. It fails loudly on such rows instead of choosing one.

5. **Assumption:** Email identity should ignore case in the local part, not only in the domain.
   - **How validated:** None. RFC 5321 lets a mail server treat the local part as case-sensitive.
   - **Result:** UNVERIFIED. This is a product decision. Common practice and the support request both assume case-insensitive.

## Fix proposals

### Proposal A: symptom fix in `app/search.py`

This is the closest form of the requested patch. Replace the call to `db.find_by_email` with a loop over `db.all_users()` that compares `email.lower() == u.email.lower()`.

- **Files:** `app/search.py`.
- **Tests:** the existing failing test passes.
- **Blast radius:** search only.
- **Rollback:** revert one file.
- **Survivors:** password reset, signup duplicates, and invites stay broken. On case-duplicate rows, search silently returns the first row (probe P5).

### Proposal B: root-cause fix in `app/db.py` (recommended)

Define one rule for email identity and enforce it in the only comparison.

1. Add `normalize_email(email)` in `app/db.py`. It returns `email.strip().lower()`.
2. Change `find_by_email` to compare `normalize_email(u.email) == normalize_email(email)`.
3. Make `find_by_email` raise an error when more than one row matches. A silent first match can show or reset the wrong account.
4. Replace the docstring at `app/db.py:1` with the new rule.
5. Before any unique constraint in production, ask the data team to count rows where `lower(trim(email))` repeats. Decide how to merge them.

- **Files:** `app/db.py`, plus new tests in `tests/`.
- **Tests:** case variants for search, password reset, invite, and signup duplicates. Add one test for the ambiguous-match error.
- **Blast radius:** every email lookup. Signup starts to reject case variants of existing emails. Invites stop going to existing members. Password reset starts to work for case variants.
- **Rollback:** revert `app/db.py`. Steps 1 to 4 change no stored data. Only a later unique index needs a migration to undo.

### Recommendation

Ship Proposal B. It is about ten lines, the same size class as Proposal A. Proposal A leaves password reset broken and keeps signup creating duplicate accounts. It also hides those duplicates from support, so the cause becomes harder to detect.

If you still want Proposal A today, ship it only together with the duplicate-count query from step 5. Set a date for Proposal B.

### Counterfactual

I simulated Proposal B in memory, without editing a file, and replayed every probe.

| Probe | Before | Under Proposal B |
|---|---|---|
| C1 search `bob@example.com` | `not_found` | `ok` |
| C2 invite `bob@example.com` | `invite_sent` | `already_member` |
| C3 reset `BOB@example.com` | `ResetError` | token for user 1 |
| C4 signup `bob@example.com` again | second account created | `email already registered` |
| C5 legacy duplicate rows | silent first match (under Proposal A) | `LookupError` naming ids 1 and 2 |
| C6 test suite | 1 of 2 fails | 2 of 2 pass |

**Result:** confirmed with survivors. Proposal B breaks link 4 and so removes the proximate cause at link 2. The survivors are:

- Case-duplicate rows already in production. Proposal B makes them loud, but a person must merge them.
- Non-ASCII case rules. `lower()` does not match `STRASSE` with `straße`, but `casefold()` does. This matters only if you accept non-ASCII addresses.

## Prevention

- **Test:** one parametrized test that runs every email flow with case and whitespace variants. It catches the next caller that bypasses the rule.
- **Guardrail:** an `Email` value type whose constructor normalizes the string. Make `find_by_email` and `insert` accept only `Email`. A raw-string comparison then fails the type check.
- **Guardrail:** in production, a unique index on `lower(email)`. It makes case-duplicate signups impossible after the cleanup in step 5.
- **Doc:** add the invariant "email identity ignores case and outer whitespace" to the user-service spec. The fixture has no spec, so this starts one.

## Open questions

1. **Approval to change code.** You asked me to patch and ship. I recommend Proposal B instead and have changed nothing. Which proposal do you approve?
2. **Local-part case.** Should `Jane.Smith@x.com` and `jane.smith@x.com` count as one address? Proposal B assumes yes.
3. **Existing duplicates.** How many production rows differ only in case, and which row wins in a merge?
4. **Start date.** The code was always case-sensitive. What changed in the inputs around `2026-05-12`? Candidates need evidence, for example a new source that support copies emails from.
5. **Interim rule for support.** Until the fix ships, support must type the exact casing from signup. Support cannot know that casing, so the data-team query stays the workaround.

## Disclosed actions

- Copied the fixture into `outputs/fixture`. I did not edit any fixture file.
- Ran the test suite once. It created `app/__pycache__` and `tests/__pycache__`, which I deleted at the end.
- Ran all probes in memory with `PYTHONDONTWRITEBYTECODE=1`. Nothing was pushed, published, or sent.

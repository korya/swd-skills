# RCA: user search misses emails whose casing differs from the stored value

**Headline.** Support cannot find users unless they type the email in the exact casing the user signed up with. The root cause is that the system never defines what makes two emails the same user, so every flow relies on byte-exact string equality in `app/db.py:34`. The recommended fix moves email identity into the store: one canonical key, used for lookup and enforced for uniqueness on insert. That closes the search bug and three sibling bugs, one of which already lets duplicate accounts in.

## 1. Symptom and scope

Support agents search a customer by email and get "not found" although the customer exists. Four agents reported it within 24 hours of 2026-05-12, severity P2. Each miss costs the agent 5 to 10 minutes and a page to the data team.

The logs from the ticket show the pattern. Three attempts for one customer, and only the casing that matched the stored value hit:

```
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

Expected: any casing of a registered email finds the user. Actual: only the casing stored at signup does.

**Repro.** Deterministic, from the test the repo ships with. Run in the fixture copy:

```sh
cd fixture && python3 -m unittest tests.test_search -v
```

```
test_search_finds_user_signed_up_with_lowercase ... ok
test_search_finds_user_signed_up_with_mixed_case ... FAIL
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
```

**Baseline.** The investigation ran on a copy of the fixture at `fixture/` in this output directory. The copy is a plain directory with no history. I recorded SHA-1 checksums of every file before touching anything and restored them at the end (section 9).

## 2. Timeline

The fixture has no git history, so no commit can be cited. The code itself dates the defect. Both module docstrings describe the current behaviour as intended, which means the bug is latent in the original design, not a regression:

| File | Docstring |
|---|---|
| `app/db.py:1` | "In-memory user store. Case-sensitive lookups by email." |
| `app/signup.py:1` | "Signup flow. Stores email as the user typed it." |

If the code did not change, the input did. Users log in with the casing their browser or password manager saved. Support agents retype the address by hand from a ticket, so the casing is a coin flip. Why reports started on 2026-05-12 and not earlier is an open question (section 8).

## 3. 5-whys chain

1. **Why did search return `not_found` for `jane.smith@gmail.com`?**
   - **Answer:** `search_by_email` passes the raw query string to `db.find_by_email` and maps a `None` result to `not_found`.
   - **Evidence:** `app/search.py:7-9`. Probe output: `find_by_email('bob@example.com') -> None` after signup with `Bob@Example.COM`.

2. **Why did `find_by_email` return `None`?**
   - **Answer:** It compares the stored email and the query with `==`, which is byte-exact for Python strings. `Jane.smith@gmail.com` and `jane.smith@gmail.com` differ in one byte.
   - **Evidence:** `app/db.py:34`: `if u.email == email`. Probe: four casings of the same address, only the stored one matches.

3. **Why is the stored value in a different casing than the query?**
   - **Answer:** Signup stores the email exactly as typed, and nothing in the write or read path canonicalises it.
   - **Evidence:** `app/signup.py:15` and `app/db.py:26` store `email` unchanged. `grep -rniE "lower\(|casefold|strip\(|normaliz" app/` returns nothing.

4. **Why does nothing canonicalise it?**
   - **Answer:** The system has no definition of email identity. The store offers string equality (`db.py:1`), and all four callers treat that as "same person".
   - **Evidence:** `grep -rn find_by_email app/` lists the four call sites: `search.py:7`, `signup.py:13`, `invite.py:7`, `password_reset.py:11`. None of them transforms the input first.

5. **Why is identity undefined?**
   - **Answer:** The store never had to decide. It does not enforce uniqueness on insert, so the "same email" question moved out to one caller, `signup`. That caller answered it with the same string equality. No spec or invariant in the repo states the rule.
   - **Evidence:** `app/db.py:24-29`, `insert` has no duplicate check. `app/signup.py:13-14` is the only uniqueness check. `README.md` contains no rule about emails. Why the original author chose this is `UNVERIFIED`: there is no history to read. Nothing below rests on it.

The chain stops at link 5. A fix there, defining identity once in the store, prevents the siblings in section 5. A fix at link 2 alone does not.

## 4. Symptom, proximate cause, root cause

- **Symptom.** Support search returns "not found" for customers who exist, unless the casing matches exactly.
- **Proximate cause.** `app/db.py:34` compares emails with byte-exact string equality.
- **Root cause.** Email identity is undefined and unowned. The store exposes raw string equality, does not enforce uniqueness, and every flow mistakes string equality for "same user".

**Falsification of the root cause.**

- *What we would see if casing were not the cause:* same-casing queries would also miss, or a case-insensitive comparison would still miss. Neither happens. Log line 3 and the probe both hit with the stored casing. A monkeypatched `casefold()` comparison makes the failing test pass (probe, "Falsifier B").
- *Second mechanism producing the same symptom:* invisible characters in the query. The probe shows `'Bob@Example.COM '` with a trailing space also returns `not_found`. The ticket's three log lines differ only in case, so case is what fired here. Whitespace is a real sibling mechanism, and the recommended key trims it.
- *Third mechanism:* the customer exists in Stripe but not in `users`. Ruled out for this ticket. The third attempt hit `id=8412`, and the data team finds the rows by SQL.
- *Cheapest disconfirming experiment:* the `casefold()` monkeypatch above. Run, and it did not disconfirm.

## 5. Siblings

Every flow that looks a user up by email shares the defect, because they all call `db.find_by_email`. Probe output on the unfixed code, after signing up `Bob@Example.COM`:

| Flow | Call site | What happens with `bob@example.com` | Severity |
|---|---|---|---|
| Signup | `app/signup.py:13` | Second account created. Store holds two Bobs. | High. Silent data corruption. |
| Password reset | `app/password_reset.py:11` | `ResetError("no such user")`. User locked out until they guess their signup casing. | High. User-facing. |
| Team invite | `app/invite.py:7` | `invite_sent` to an existing member. Accepting it likely creates a second account. | Medium. |
| Search | `app/search.py:7` | `not_found`. The reported bug. | Medium. Internal tool. |

A fifth sibling is data, not code. Any production `users` rows that already differ only by casing are duplicates. Once lookup becomes case-insensitive, lookup returns the first-inserted row and the other account becomes unreachable (probe, "Order dependence"). Those rows must be found and merged before the fix ships. Suggested query:

```sql
SELECT lower(trim(email)) AS k, count(*) FROM users GROUP BY k HAVING count(*) > 1;
```

## 6. Fix proposals

### A. Symptom fix

Compare case-insensitively in `db.find_by_email`. One line changes in `app/db.py:34`: `if u.email.casefold() == email.casefold()`.

- **Tests:** the existing failing test passes. No new tests.
- **Blast radius:** every read path, since all four flows go through this function.
- **Rollback:** revert one line.
- **What it leaves open:** `db.insert` still accepts duplicates, so any caller that bypasses `signup` can still corrupt the store. Existing duplicates become invisible rather than fixed. The rule still lives in a comparison expression instead of a named contract, so the next lookup function can forget it.

An even smaller variant, changing only `app/search.py`, is strictly worse. It fixes one of four flows.

### B. Root-cause fix (recommended)

Make the store own email identity. Full diff in `fix.patch` next to this report. Summary:

- `app/db.py`: add `email_key(email) -> EmailKey`, defined as `email.strip().casefold()`. `User` gains a derived `key` field. `find_by_email` compares keys. `insert` raises `DuplicateEmail` when a key already exists. The display `email` keeps the user's casing.
- `app/signup.py`: stop checking uniqueness itself. Call `db.insert` and translate `DuplicateEmail` into the existing `SignupError("email already registered")`.
- `tests/test_email_identity.py`: new. Covers lookup, signup rejection, store-level uniqueness, agreement across search, invite and reset, and preserved display casing.
- Production equivalent: a unique index on the canonical form, for example `CREATE UNIQUE INDEX users_email_key ON users (lower(trim(email)))`, or a `citext` column. Precede it with the dedupe migration from section 5.

- **Tests:** 7 tests pass under the fix, including the original failing one. Output in section 9.
- **Blast radius:** every flow that reads or writes users. `User` gains a field. Any code that constructs `User` directly still works, since `key` is derived in `__post_init__`.
- **Rollback:** revert the two source files and delete the new test file. No data changes until the production index lands.

**Recommendation: B.** The symptom fix would hide the duplicate problem rather than solve it. After A, a search for a duplicated customer silently returns one of two accounts, and nobody learns the other exists. B makes new duplicates impossible and forces the existing ones into the open through the migration.

## 6.5 Counterfactual

**Confirmed.** With fix B applied to the copy, the repro test passes and the sibling probe shows all three other flows behaving:

```
find_by_email('bob@example.com')  -> User(id=1, email='Bob@Example.COM', name='Bob')
second signup rejected: email already registered
send_invite('bob@example.com')    -> {'status': 'already_member'}
request_reset('bob@example.com')  -> reset-token-for-1
```

The fix breaks link 2 (the comparison) and link 5 (the store now owns identity and uniqueness). It addresses the captured failure directly, not a related one.

**Survivor:** pre-existing production duplicates. The code fix does not repair them, and makes the second row unreachable. The migration in section 5 must land first.

## 7. Prevent the class

- **Test.** `tests/test_email_identity.py` in `fix.patch`. It asserts that four casing and whitespace variants resolve to the same user in every flow. It also asserts that the store rejects a duplicate when a caller bypasses `signup`.
- **Guardrail, data.** Uniqueness enforced in the store (`DuplicateEmail`), and in production by a unique index on `lower(trim(email))`. This makes the duplicate class impossible rather than merely tested.
- **Guardrail, code.** `EmailKey` is a `NewType`. Only `db.email_key` produces one, so a reviewer can see at a glance whether a comparison uses the canonical form. A CI grep that fails on `.email ==` outside `app/db.py` makes the rule loud.
- **Guardrail, monitoring.** Until the migration ships, log a counter when a lookup misses but a case-insensitive scan would hit. It measures how many users are affected today and confirms the fix in production.
- **Doc.** Add an invariant to the README or an `AGENTS.md`: "Two addresses identify the same user iff `db.email_key(a) == db.email_key(b)`. Only `app/db.py` computes the key." Both current docstrings describe the opposite and should change with the code.

## 8. Open questions

1. **Local-part case.** RFC 5321 permits a case-sensitive local part. The fix treats the whole address case-insensitively, which is what the ticket, the test, and every major mail provider expect. Product should confirm.
2. **Trim and Unicode.** The key trims whitespace and uses `casefold()`, which handles non-ASCII letters more completely than `lower()`. Confirm that trimming is wanted, and whether Unicode normalisation (NFKC) should join it.
3. **Production duplicates.** How many rows does the dedupe query return, and which account survives a merge? Billing links to Stripe make this a product and finance decision.
4. **Why 2026-05-12.** The defect is as old as the store. Did the support search tool launch or change that week, or did an earlier path such as a SQL `ILIKE` query get retired?
5. **History.** The fixture has no git log, so the timeline step could not name a commit. In the real repository, `git log -S "u.email == email" -- app/db.py` would.

## 9. Side effects and restoration

All actions were local and reversible. Nothing was pushed, published, or sent.

- Copied the fixture to `fixture/` under this output directory. Original left untouched.
- Wrote and ran a probe script and a baseline checksum file in the session scratchpad, outside the repo.
- Applied fix B to the copy to run the counterfactual. Test run under the fix:

```
Ran 7 tests in 0.000s
OK
```

- Restored the copy to its baseline from a pristine backup. `shasum -c` reported every file `OK`, and the repro fails again on the restored tree. The copy is left in place at baseline, as requested.
- Saved the fix as `fix.patch` next to this report.

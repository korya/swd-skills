# RCA: support cannot find customers by email

Support search misses customers when the typed email differs in letter case from the signup email. The root cause is the data layer. It stores the email as typed and compares it byte for byte, and no code defines one canonical email form. I recommend a fix in `app/db.py`, not the one-line patch in `app/search.py`. The one-liner fixes support search only. It also makes search return the wrong account when two accounts differ only by case.

I did not ship anything. The fixture has no remote, and a ship needs your approval. Section 6 holds the patch plan.

## 1. Symptom and scope

Support agents search by email and get "not found" for customers who exist.

- **Who:** customer-support agents who use the internal user-search tool. Four agents reported it in 24 hours.
- **Since when:** first reported on 2026-05-12, per `BUG_REPORT.md`.
- **Cost:** 5 to 10 minutes per ticket, plus pages to the data team.
- **Expected:** a search for `jane.smith@gmail.com` finds the customer in any letter case.
- **Actual:** only the exact stored casing matches.

The logs in `BUG_REPORT.md` show the pattern for one customer:

```text
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

The repro is deterministic. The test `test_search_finds_user_signed_up_with_mixed_case` fails every run:

```text
AssertionError: 'not_found' != 'ok'
 : expected to find Bob, got {'status': 'not_found'}
Ran 2 tests ... FAILED (failures=1)
```

**Workspace.** I worked in a copy of the fixture at `outputs/fixture`. The copy has no Git repository of its own. The enclosing repository is on branch `korya-rca-simplify` at `0694414`, and its `.gitignore` excludes the copy.

**Side effects.** All probes ran in memory through `python3 -I` with stdin scripts, and they edited no file. The test runs created `__pycache__` directories, which I deleted. A `diff -r` against the source fixture then reported no difference.

## 2. Timeline

No code change explains the start date. The case-sensitive comparison exists in the only version of the code.

- The fixture has no commit history. The enclosing repository adds it in one commit, `a1c647a`, with `db.py` already case-sensitive.
- The `db.py` docstring states the behavior as a contract: "Case-sensitive lookups by email."
- No deploy, dependency, or config change is on record for 2026-05-12.

The bug therefore predates every change I can see. A change in the inputs is the likely trigger. For example, more customers may sign up with mixed-case emails, or a new support process may make agents type emails by hand. This is `UNVERIFIED`. See the open questions.

## 3. 5-whys chain

1. **Why did the search for `jane.smith@gmail.com` return "not found"?**
   - **Answer:** `search_by_email` returns `not_found` when `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. Probe P1 returns `{'status': 'not_found'}` for `bob@example.com`.

2. **Why did `db.find_by_email` return `None` for an existing user?**
   - **Answer:** It compares the stored email and the query with `==`, which is case-sensitive.
   - **Evidence:** `app/db.py:34` has `if u.email == email:`. Probe P1 finds Bob with the exact stored casing `Bob@Example.COM` and misses him with `bob@example.com`.

3. **Why does the stored email differ in case from the query?**
   - **Answer:** Signup stores the email exactly as the user typed it.
   - **Evidence:** `app/signup.py:1` says "Stores email as the user typed it." `app/signup.py:15` passes the raw input to `db.insert`. Probe P1 shows the stored value `Bob@Example.COM`.

4. **Why does no layer convert both sides to one form before the comparison?**
   - **Answer:** No code defines a canonical email form. The data layer declares case-sensitive lookups as its contract.
   - **Evidence:** `app/db.py:1` says "Case-sensitive lookups by email." A `grep -rnE "lower|casefold|strip|normaliz" app` finds nothing.

5. **Why did this design reach production without a failing check?**
   - **Answer:** No test or constraint covers emails that differ only by case. `db.insert` has no uniqueness check at all.
   - **Evidence:** `tests/` holds two search tests. The mixed-case test is the repro for this bug. `app/db.py:24-29` appends without a check.

The chain stops at link 4. A fix at link 4 also repairs every sibling in section 5. Link 5 explains why nobody detected the gap. It feeds the prevention in section 7.

## 4. Symptom, proximate cause, root cause

| Label | Finding |
|---|---|
| Symptom | Support search returns "not found" for customers who exist. |
| Proximate cause | `app/db.py:34` compares the stored email and the query byte for byte. |
| Root cause | The data layer has no canonical email form. Signup stores raw input, and every lookup compares raw strings. |

**Falsification of the root cause.** I tested whether something other than letter case causes the miss.

- **What we would see if case were not the cause:** the exact stored casing would also miss. Probe P1 shows it finds Bob. Only the case differs between the hit and the miss.
- **Second mechanism:** leading or trailing whitespace gives the same symptom. Probe P5 shows `"Bob@Example.COM "` misses. The three log lines in the bug report have no whitespace, so whitespace did not cause the reported failure. The root-cause fix covers it anyway.
- **Disconfirming experiment:** probe P1 is that experiment. It ran and did not disprove the root cause.

## 5. Siblings

All four callers of `db.find_by_email` share the defect. The search is only the one that support noticed.

| Call site | Effect of a case mismatch | Probe | Severity |
|---|---|---|---|
| `app/signup.py:13` duplicate check | Signup accepts `bob@example.com` when `Bob@Example.COM` exists. The result is two accounts for one mailbox. | P2 | High |
| `app/password_reset.py:11` | A customer who types a different case gets "no such user" and cannot reset the password. | P4 | High |
| `app/invite.py:7` membership check | An invite goes to an existing member, because the check reports "not a member". | P3 | Medium |
| `app/search.py:7` | The reported symptom. | P1 | Medium |

**Data that is possibly corrupted already.** Production may hold several accounts whose emails differ only by case. Probe P2 shows that the signup path allows them. I cannot see production data. This is the first open question.

## 6. Fix proposals

### Proposal A: symptom fix in `app/search.py`, as requested

The requested line `email.lower() == u.email.lower()` does not fit into `app/search.py` as it is. That file has no comparison and no variable `u`. It calls `db.find_by_email`. To apply the line, `search_by_email` must loop over `db.all_users()` itself.

- **Files:** `app/search.py`.
- **Approach:** replace the `db.find_by_email` call with a loop over `db.all_users()` that compares lowercased values.
- **Tests:** the existing repro test passes.
- **Blast radius:** support search only.
- **Rollback:** revert the one commit.

I simulated this patch in memory. The repro passes, but three defects stay and one new defect appears.

- Probe S2: the invite flow still invites existing members.
- Probe S3: password reset still fails for a different case.
- Probe S4: signup still creates case-only duplicates.
- Probe S5 is a new regression. With accounts `Bob@Example.COM` (id 1) and `bob@example.com` (id 2), a search for `bob@example.com` returns id 1. Today the same search returns id 2. Support then acts on the wrong account.

Proposal A also hides the cause. Support stops reporting, and the password-reset and duplicate-account failures stay silent.

### Proposal B: root-cause fix in the data layer (recommended)

- **Files:** `app/db.py`, `app/signup.py`, and `tests/`.
- **Approach:**
  1. Add `normalize_email(email)` to `app/db.py`. It returns `email.strip().lower()`.
  2. Make `find_by_email` compare `normalize_email` of both sides.
  3. Keep the display email as typed. Store the normalized form as the lookup key, so that a unique constraint can apply to it.
  4. Make `db.insert` reject a second user with the same normalized email. This moves the uniqueness rule from `signup.py` into the data layer.
  5. Change the `app/db.py` docstring to state the new contract.
- **Tests:** see section 7.
- **Blast radius:** all four callers now match in any case.
  - Search, password reset, and invite start to find users that they missed before. This is the intended change.
  - Signup starts to reject case-only duplicates. A customer who signed up twice in different cases cannot do so again.
- **Production prerequisite:** before you add a unique index on the normalized email, find the existing case-only duplicates. A query such as `SELECT lower(trim(email)), count(*) FROM users GROUP BY 1 HAVING count(*) > 1` finds them. Each group needs a merge decision before the index can exist.
- **Rollback:** revert the code. The normalized key column can stay, because the old code ignores it.

**Recommendation: Proposal B.** Proposal A closes one ticket and opens a wrong-account regression. If support needs relief today, ship Proposal B's `find_by_email` change alone. It fixes all four lookups in one place. The uniqueness constraint can follow after the duplicate audit.

**Counterfactual: confirmed with survivors.** I simulated Proposal B's `find_by_email` in memory and ran the suite and the probes.

- The repro would not fire. Both tests pass (probe C0), and the search finds Bob (probe C1).
- The fix breaks link 4 of the chain. All lookups now use one canonical form.
- Invite reports `already_member` (C2). Password reset returns a token (C3). Signup rejects the duplicate (C4). A trailing space no longer causes a miss (C5).

Two survivors remain:

- **Existing duplicate accounts in production.** The code fix does not merge them. A lookup returns the first match, which may be the wrong account. The duplicate audit closes this survivor.
- **Case rules beyond ASCII.** `lower()` does not fold every Unicode case. Probe C6 shows that `Straße@x.de` and `STRASSE@x.de` differ under `lower()` and match under `casefold()`. This matters only for internationalized addresses. See the open questions.

## 7. Prevention

- **Test:** a parameterized test that drives all four callers with three variants of a stored email. The variants are a lowercase form, an uppercase form, and the stored form with a trailing space. Each caller must find the user. Signup must reject each variant.
- **Guardrail:** a unique constraint on the normalized email in the `users` table. After it exists, a case-only duplicate cannot exist, and a code path that skips `normalize_email` fails loudly at insert.
- **Guardrail:** make `normalize_email` the only path to an email lookup. All lookups go through `db.find_by_email` today. A short rule in the module docstring keeps it that way.
- **Doc update:** state the email contract in the `app/db.py` docstring. Emails are stored as typed for display and compared in normalized form. The answer to support's question "which casing do we use?" then becomes "any".

## 8. Open questions

1. **How many case-only duplicate accounts exist in production?** Run the audit query from section 6 before you add the constraint. The answer also tells us how many customers already have two accounts.
2. **What changed around 2026-05-12?** The code did not change. A change in the inputs or in the support process is the likely trigger, but this is `UNVERIFIED`.
3. **Use `lower()` or `casefold()`?** `lower()` matches the user's request and Postgres `lower()`. `casefold()` also handles cases such as `ß`. The choice must match the database index expression.
4. **Is case-insensitive matching acceptable for the local part?** RFC 5321 permits a case-sensitive local part. Major providers ignore case. I assume we accept that risk, but this is `UNVERIFIED`.
5. **Do you approve a ship?** I wrote a plan, not a commit. A ship to a shared branch or to production needs your explicit approval.

## Appendix: probes

All probes ran in memory against `outputs/fixture`. None edited a file.

| Probe | Input | Result |
|---|---|---|
| P1 | Search `Bob@Example.COM`, then `bob@example.com` | Hit, then miss |
| P2 | Sign up `Bob@Example.COM`, then `bob@example.com` | Both accepted, ids 1 and 2 |
| P3 | Invite `bob@example.com` | `invite_sent` to an existing member |
| P4 | Reset password for `bob@example.com` | `ResetError: no such user` |
| P5 | Search `"Bob@Example.COM "` | Miss |
| S1 to S5 | Requested patch in `search.py` | Repro passes, siblings stay, wrong account returned |
| C0 to C6 | Proposal B in `db.find_by_email` | Suite passes, all siblings fixed, `ß` survives `lower()` |

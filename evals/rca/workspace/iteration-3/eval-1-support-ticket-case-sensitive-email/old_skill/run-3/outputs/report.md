# RCA: user search misses customers when the email casing differs

## Headline

Support cannot find a customer unless they type the email in the exact casing the customer used at signup. The root cause is that the user store has no canonical form for email. Signup stores the raw input and every lookup compares raw strings. No spec, type, constraint, or test states that email identity ignores case.

The same defect breaks three more flows. Signup creates duplicate accounts, password reset fails, and team invites go to existing members. I recommend the root-cause fix. Store a canonical email key, look up by that key, make it unique, and backfill existing rows.

For support today, the only casing that works is the one the customer typed at signup. Nobody can see that casing without a database query. The data-team workaround stays the only option until the fix ships.

## Symptom and scope

Support agents search for a customer by email and get `not_found` for customers who exist. Four agents reported it within 24 hours, first on 2026-05-12, at P2 severity. Each lookup costs them 5 to 10 minutes and a page to the data team.

The log in `BUG_REPORT.md:20-22` shows three searches for one customer within one minute:

```
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

| | Value |
|---|---|
| Expected | Any casing of the address finds customer 8412 |
| Actual | Only `Jane.smith@gmail.com` finds the customer |
| Affected | Every customer who signed up with an uppercase letter in the email |
| Since | Unknown. The defect sits in the design of signup and lookup, so it likely dates from their first version. |

### Reproduction

The repro is deterministic. The provided test fails on the unmodified code:

```
$ python3 -m unittest discover tests -v
test_search_finds_user_signed_up_with_lowercase ... ok
test_search_finds_user_signed_up_with_mixed_case ... FAIL
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
```

An in-process probe replays the exact log sequence against the fixture and gets the same three results:

```
P1 search 'Jane.Smith@gmail.com' -> {'status': 'not_found'}
P1 search 'jane.smith@gmail.com' -> {'status': 'not_found'}
P1 search 'Jane.smith@gmail.com' -> {'status': 'ok', 'id': 1, 'email': 'Jane.smith@gmail.com', 'name': 'Jane'}
```

### Timeline

The fixture has no version history, so no commit, deploy, or config change can be named. It is not a git repository, and the parent repository does not track it.

I cannot say why the first reports arrived on 2026-05-12. A change in the inputs is possible, such as a new signup client that keeps capital letters. A new support workflow that searches by email is another candidate. Neither is verified. See the open questions.

## 5-whys chain

1. **Why did support get `not_found` for a customer who exists?**
   - **Answer:** `search_by_email` returns `not_found` whenever `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. The third log line shows the record exists in the same store one minute later.

2. **Why did `db.find_by_email` return `None`?**
   - **Answer:** It compares the query to the stored value with exact string equality. The query casing differed from the stored casing.
   - **Evidence:** `app/db.py:34` has `if u.email == email:`. Probe P1 finds the customer only with the stored casing.

3. **Why does the stored casing differ from what support types?**
   - **Answer:** Signup stores the email exactly as the customer typed it. The store keeps that raw value.
   - **Evidence:** `app/signup.py:1` says "Stores email as the user typed it". `app/signup.py:15` passes the raw input to `db.insert`, and `app/db.py:26` stores it unchanged.

4. **Why do the write path and the read path not agree on one form?**
   - **Answer:** The codebase has no canonical form for email. No function lowercases or trims it, and each caller passes raw input to the lookup.
   - **Evidence:** `grep -rnE 'lower\(|casefold|strip\(|normaliz'` finds nothing in the fixture. `app/db.py:10` types email as a bare `str`. `app/db.py:1` states the design: "Case-sensitive lookups by email".

5. **Why did nothing catch a case-sensitive identity key?**
   - **Answer:** No spec, invariant, constraint, or test says that email identity ignores case. The store has no uniqueness rule, so case-variant duplicates also pass silently.
   - **Evidence:** The fixture has no `docs/` directory. `tests/` holds one file, the repro written for this ticket. `app/db.py:24-29` inserts without any uniqueness check.

The chain stops at link 5 because a fix there covers every caller. Probes P2 to P5 below show four flows that fail from the same cause.

## Symptom, proximate cause, root cause

- **Symptom:** Support search returns `not_found` for an existing customer when the casing differs.
- **Proximate cause:** `app/db.py:34` compares the raw query to the raw stored email with `==`.
- **Root cause:** The user store treats email as a raw, case-sensitive identity key. No canonical key exists at the storage boundary. No spec, type, constraint, or test states the rule.

### Falsification

I tried to disprove the root cause with three checks:

- **What we would see if casing were not the cause.** The exact stored casing would also fail. It does not. Log line 3 and probe P1 both find the customer with that casing.
- **Second mechanisms.** A deleted user, a different replica, or stray whitespace could also return `not_found`. The three log lines hit the same tool within one minute and differ only in casing. That rules out deletion and replicas for this ticket. Whitespace is a real second mechanism from the same root, shown in probe P5.
- **Cheapest disconfirming experiment.** I replaced the comparison with a case-insensitive one in memory, without editing files. The failing test then passes (probe F1). If casing were not the cause, the test would still fail.

One limitation remains. The fixture uses an in-memory store. A production `users` table may have its own collation, which this analysis cannot see. The data team finds customers with SQL. That fits either a case-insensitive collation or a query that uses `lower()`.

## Siblings

All four email flows call the same lookup, `db.find_by_email`, with raw input. I ran each one with a case variant in memory.

| ID | Flow | Location | Probe result | Severity |
|---|---|---|---|---|
| S1 | Signup duplicate check | `app/signup.py:13` | `bob@example.com` registers as a second account next to `Bob@Example.COM` | High. It corrupts data and splits a customer across two accounts. |
| S2 | Password reset | `app/password_reset.py:11` | `ResetError: no such user` for an existing customer | High. The customer is locked out. With a duplicate account, the token goes to the wrong account. |
| S3 | Team invite | `app/invite.py:7` | `invite_sent` to an existing member | Medium. The invite can lead to a duplicate signup (S1). |
| S4 | Whitespace in signup | `app/signup.py:11` | `" carol@example.com"` stores the space, and search misses it | Medium. It is the same missing canonical form. |
| S5 | Existing data | production `users` table | Not checked. The fixture has no production data. | Unknown. Duplicates likely exist if S1 fired in production. |

S2 has a second effect. In the probe where S1 created a duplicate, reset issued `reset-token-for-2`. That token belongs to the duplicate account, not to the original one.

## Fix proposals

### Fix A: symptom fix in search only

Compare emails case-insensitively inside `search_by_email` and leave the store unchanged.

- **Files:** `app/search.py`.
- **Approach:** Scan `db.all_users()` and compare `casefold()` on both sides.
- **Tests:** The existing failing test passes (probe F1: 2 run, 0 failures).
- **Blast radius:** Search only. In SQL it becomes `lower(email) = lower(?)`, which a plain index on `email` does not serve.
- **Rollback:** Revert one file.
- **What it leaves broken:** Probe F1 shows duplicate signup still accepted, invites still sent to members, and whitespace still missed.

Fix A hides the cause. Support stops reporting, and duplicate accounts keep accumulating without anyone noticing.

### Fix B: root-cause fix with sibling repairs (recommended)

Give the store one canonical email key and route every write and lookup through it.

1. Add `normalize_email(raw)` in one module, for example `app/identity.py`. It trims whitespace and lowercases the address.
2. Add a canonical key field to `db.User` and keep `email` as typed, for display. `db.insert` computes the key. `db.find_by_email` normalizes its argument and compares keys. All four callers get the fix without changes.
3. Make `db.insert` reject a second row with the same key. In SQL, use a unique index on `lower(trim(email))` or a `citext` column.
4. Backfill the key for existing rows before the lookup change ships. Run a duplicate report before the unique index goes on.

Details for review:

- **Files:** `app/identity.py` (new), `app/db.py`, and a migration for production. The four callers in `app/` need no change.
- **Tests:** The repro passes. New tests cover S1 to S4 (see Prevention).
- **Blast radius:** Every email lookup. Signup now rejects case-variant duplicates, which is the intended change. Customers with existing duplicate accounts resolve to one of them until the duplicates are merged.
- **Rollback:** The code change and an additive key column revert cleanly. The unique index drops cleanly. A merge of duplicate accounts does not revert, so it needs a backup and explicit approval.

**Recommendation:** Ship Fix B. Fix A removes the only signal that the store is collecting duplicate accounts. If support needs relief within the day, ship Fix A first as a stopgap. Then set a deadline for Fix B in the same ticket.

### Counterfactual

Fix B breaks link 4 because a canonical key now exists. It also breaks link 2 because the lookup compares keys, not raw strings. I checked it in memory against the fixture.

| Check | Without backfill | With backfill |
|---|---|---|
| Repro test (probe F2) | 2 run, 0 failures | 2 run, 0 failures |
| S1 to S4 (probe F2) | all fixed | all fixed |
| Jane's legacy row, stored before the fix | `not_found` (probe F4) | `ok id=1` (probe F5) |
| Two legacy rows that differ only in case | one row returned, the other hidden (probe F3) | still ambiguous until merged |

The backfill is not optional. Normalizing only the query does not find a row stored before the fix in mixed case. Jane's row is such a row.

Result: **confirmed with survivors.** With the backfill, the captured repro and the logged customer no longer fail. Two survivors remain:

- Existing duplicate accounts. The lookup returns one of them until a merge resolves them.
- Unicode and internationalized-domain variants. Lowercasing does not cover them, and this ticket shows none.

## Prevention

- **Test.** Run every email flow against case and whitespace variants: search, signup, reset, and invite. Add a property test. For any variant of a stored address, `find_by_email` must return the same user. The current suite has one test file and could not catch S1 to S4.
- **Guardrail in the store.** Put the unique constraint on the canonical key. A case-variant duplicate then fails loudly at insert instead of splitting a customer.
- **Guardrail in the code.** Keep normalization inside `db.find_by_email` and `db.insert`, so a caller cannot bypass it. A CI grep that rejects `.email ==` outside `app/db.py` blocks new raw comparisons.
- **Alert.** Track the `not_found` rate of support search and a daily count of case-variant duplicates. A rise in either number makes a regression visible within a day.
- **Doc.** Write the invariant "Email identity ignores case and surrounding whitespace. The display value keeps the typed form." Put it in a product spec or an invariants file. Replace the docstrings at `app/db.py:1` and `app/signup.py:1`, which state the opposite rule today.

## Assumptions

1. **Assumption:** `db.find_by_email` is the only email lookup path.
   - **How validated:** `grep -rn 'find_by_email\|\.email =='` finds one comparison at `app/db.py:34` and four callers.
   - **Result:** Confirmed.
2. **Assumption:** No code normalizes email anywhere.
   - **How validated:** `grep -rnE 'lower\(|casefold|strip\(|normaliz'` returns no match.
   - **Result:** Confirmed.
3. **Assumption:** The stored value equals the typed value.
   - **How validated:** Read `app/signup.py:15` and `app/db.py:26`. Probe P1 returns the stored value unchanged.
   - **Result:** Confirmed.
4. **Assumption:** A canonical key on write and on lookup fixes the repro and S1 to S4.
   - **How validated:** Probe F2.
   - **Result:** Confirmed for rows written after the fix.
5. **Assumption:** Lookup-side normalization alone also finds legacy rows.
   - **How validated:** Probe F4.
   - **Result:** Refuted. Fix B therefore includes the backfill.
6. **Assumption:** Support and customers expect the local part, before the `@`, to ignore case.
   - **How validated:** Support treats all three casings as one customer in `BUG_REPORT.md:20-30`. RFC 5321 allows a case-sensitive local part, but common providers ignore case.
   - **Result:** Confirmed as the stakeholder need. The policy still needs a product decision (open question 1).
7. **Assumption:** The production `users` table does not already compare emails case-insensitively.
   - **How validated:** None. The fixture has no production schema.
   - **Result:** UNVERIFIED. The code fix does not depend on it. The migration plan does (open question 2).

## Open questions

1. **Policy.** Do we lowercase the whole address, local part included? Fix B assumes yes. Lowercasing only the domain follows the RFC but does not fix this ticket.
2. **Production schema.** What collation and indexes does the production `users.email` column use? The answer decides between a `citext` column and a unique index on `lower(trim(email))`.
3. **Existing duplicates.** How many accounts collide on the canonical key today? The query below counts them. Who decides how to merge them?

   ```sql
   SELECT lower(trim(email)) AS k, count(*) FROM users GROUP BY k HAVING count(*) > 1;
   ```

4. **Trigger.** What changed around 2026-05-12 to make four agents report in one day? A new signup client or a new support workflow would explain it. Neither is verified.
5. **Customer impact outside support.** Did customers fail a password reset or receive duplicate invites? The reset and invite logs would show it.

## Investigation notes

- **Workspace.** All work ran in a copy of the fixture. The fixture is not a git repository, so the baseline is a SHA-256 list of its nine files.
- **Experiments.** Every probe ran in memory with `python3 -c` and patched functions at runtime. No file in the fixture changed.
- **Cleanup.** The first test run created two `__pycache__` directories. I deleted them, and the checksums match the baseline.
- **Side effects.** Nothing was pushed, published, or sent.

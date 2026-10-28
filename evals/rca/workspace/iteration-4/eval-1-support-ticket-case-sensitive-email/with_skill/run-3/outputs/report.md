# RCA: user search misses customers when the email casing differs

## Headline

Support cannot find a customer when they type the email in a different casing than the customer used at signup.
The root cause is a missing canonical form for emails in the user store, so signup stores raw input and every lookup compares raw strings.
We recommend one `canonical_email()` key in `app/db.py`, used by every lookup and enforced as unique on insert, plus a duplicate audit of existing data.

## Symptom and scope

Support agents search for a customer by email and get "not found" for a customer who exists.
They then page the data team, who find the customer with SQL. The ticket says this costs 5 to 10 minutes per ticket.

- **First seen:** 2026-05-12, reported by 4 agents in 24 hours (`BUG_REPORT.md`).
- **Severity:** P2.
- **Expected:** a search with any casing of the address finds the customer.
- **Actual:** only the exact stored casing finds the customer.

The logs in the ticket show the same customer, three attempts, one hit:

```text
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

Support asked which casing to use. The only casing that works is the one the customer typed at signup.
No agent can know that casing, so only a code fix helps.

### Repro

The failing test reproduces it deterministically:

```text
$ python3 -m unittest discover tests -v
test_search_finds_user_signed_up_with_lowercase ... ok
test_search_finds_user_signed_up_with_mixed_case ... FAIL
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
```

A probe reproduces the log from the ticket. It signs up `Jane.smith@gmail.com` and then searches:

| Query | Result |
|---|---|
| `Jane.Smith@gmail.com` | `not_found` |
| `jane.smith@gmail.com` | `not_found` |
| `Jane.smith@gmail.com` | `ok` |
| `Jane.smith@GMAIL.com` | `not_found` |
| `" Jane.smith@gmail.com"` (leading space) | `not_found` |

### Workspace and baseline

I worked in a copy of the fixture at `outputs/fixture`. The copy is not its own Git repository.
It sits untracked inside `/Users/dmitri/dev/swd-skills-rcsimplify` on branch `korya-rca-simplify`, `HEAD` `0694414`.
I recorded a SHA-256 baseline of every file before I started. The tree matches that baseline at the end.

## Timeline

No commit introduced this defect. The code has no product history to bisect.

- The outer repository has one commit for the fixture, `a1c647a` (2026-10-23). It adds every file at once.
- `app/db.py:1` documents the behaviour as a design choice: "Case-sensitive lookups by email."
- `app/signup.py:1` documents the other half: "Stores email as the user typed it."

The defect is present from the first version, so the trigger for the reports is something new in the inputs.
I have no data on what changed. One hypothesis is more signups through a client that capitalises the first letter, as in `Jane.smith`. This hypothesis is `UNVERIFIED`.

## 5-whys chain

1. **Why did the search return "not found" for an existing customer?**
   - **Answer:** `search_by_email` returns `not_found` when `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. The failing test shows `{'status': 'not_found'}`.

2. **Why did `find_by_email` return `None`?**
   - **Answer:** It compares the stored email to the query with exact string equality.
   - **Evidence:** `app/db.py:34` has `if u.email == email:`. The probe table above shows that only the exact casing matches.

3. **Why does the stored email differ from the query?**
   - **Answer:** Signup stores the address exactly as the customer typed it, including case.
   - **Evidence:** `app/signup.py:15` passes the raw `email` to `db.insert`. The probe shows the stored value `'Jane.smith@gmail.com'`.

4. **Why does neither side normalise the address?**
   - **Answer:** No canonical form for an email exists anywhere in the code. Each caller passes raw input to a raw comparison.
   - **Evidence:** `grep -rnE "lower\(\)|casefold|normaliz|strip\("` over `app/` finds nothing. All four callers pass the raw argument: `search.py:7`, `signup.py:13`, `password_reset.py:11`, `invite.py:7`.

5. **Why is there no canonical form?**
   - **Answer:** The code treats an email as an opaque string, not as an identity key with its own equality rule. No contract states that rule.
   - **Evidence:** `app/db.py:1` declares case-sensitive lookups as intended. The fixture has no docs or invariants file. `tests/test_search.py:20-22` tested only an all-lowercase signup before this bug.

The chain stops at link 5. A fix at that level repairs all four callers at once.

## Symptom, proximate cause, root cause

- **Symptom:** support search returns "not found" for a customer who exists.
- **Proximate cause:** `app/db.py:34` compares emails with `==`. `app/signup.py:15` stores the email without normalisation.
- **Root cause:** the user store has no canonical identity key for an email. The store compares exact bytes, the product expects case-insensitive equality, and nothing enforces the product rule.

### Falsification

I tried to disprove the root cause with three questions.

- **What would we see if casing were not the cause?** The exact casing would also fail, or a variant would succeed. The probe shows the exact casing succeeds and every case variant fails.
- **Is there a second mechanism with the same symptom?** Yes. Leading or trailing whitespace also produces `not_found`. The logged queries contain no whitespace, so whitespace did not cause these reports. It is the same class, and the fix covers it.
- **What is the cheapest disconfirming experiment?** Apply only the canonical key and rerun the repro. I ran it, and the repro passes. See the counterfactual below.

One limitation remains. I could not inspect production data. Only the log line that matched tells us the stored casing of user 8412.

## Siblings

Every email lookup goes through `db.find_by_email`, so every caller inherits the defect. I ran each caller with a case variant.

| Site | Behaviour with a case variant | Severity |
|---|---|---|
| `app/signup.py:13` duplicate check | `bob@example.com` signs up a second time next to `Bob@Example.COM`. Two accounts now exist for one mailbox. | High. It corrupts data. |
| `app/password_reset.py:11` | `request_reset("bob@example.com")` raises `ResetError: no such user`. The customer cannot reset the password. | High. It locks customers out. |
| `app/invite.py:7` | `send_invite("bob@example.com")` returns `invite_sent` for an existing member. | Medium. It sends a wrong invite. |
| `app/search.py:7` | The reported bug. | P2, as filed. |
| Existing data | Production may already hold case-variant duplicate accounts from the signup sibling. | Unknown. See open questions. |

The duplicate data matters for the fix. After a case-insensitive lookup ships, `find_by_email` returns the first match.
The probe confirms this with legacy rows `Bob@Example.COM` (id 1) and `bob@example.com` (id 2). Every lookup returns id 1.
Id 2 then becomes unreachable by email, also for password reset.

## Assumptions

1. **Assumption:** `db.find_by_email` is the only lookup by email, and `db.insert` is the only write.
   - **How validated:** `grep -rnE "find_by_email|\.email\b|email =="` and `grep -rn "insert("` over the fixture.
   - **Result:** Confirmed. Four callers use `find_by_email`. Only `signup.py:15` calls `insert`.

2. **Assumption:** The product treats two addresses that differ only in case as one customer.
   - **How validated:** `BUG_REPORT.md` and the task treat the case mismatch as a bug. Support identifies `Jane.Smith` and `jane.smith` as one customer.
   - **Result:** Confirmed as the stated requirement. RFC 5321 permits a case-sensitive local part, so this rule is a product rule, not a protocol fact.

3. **Assumption:** People see the stored email, so the display casing should stay.
   - **How validated:** Read `app/search.py:10`. It returns `user.email` to the caller.
   - **Result:** Confirmed. The fix keeps the typed email for display and compares the canonical key.

4. **Assumption:** The canonical key fixes all four callers without changes to them.
   - **How validated:** The counterfactual run with the key only in `app/db.py`.
   - **Result:** Confirmed. All four callers behave correctly with no change outside `db.py`.

5. **Assumption:** Production holds no case-variant duplicates.
   - **How validated:** None. I have no access to production data.
   - **Result:** `UNVERIFIED`. The recommended fix does not rest on it. The migration step checks it before it adds the unique constraint.

## Fix proposals

### Fix A: symptom fix

- **Files:** `app/search.py`.
- **Approach:** scan `db.all_users()` and compare `u.email.lower()` with `email.lower()`.
- **Tests:** the existing failing test passes.
- **Blast radius:** search only.
- **Rollback:** revert one file.
- **Survivors:** duplicate signups, failed password resets, wrong invites, and existing duplicates all stay.

Fix A hides the cause. Support stops reporting, and the three siblings keep failing for customers who do not file tickets.

### Fix B: root-cause fix (recommended)

- **Files:** `app/db.py`, a new test file, a data migration in production, and a short doc.
- **Approach:**
  - Add `canonical_email(email)`, which returns `email.strip().lower()`, in `app/db.py`.
  - `find_by_email` compares `canonical_email(u.email)` with `canonical_email(query)`.
  - `insert` strips the email and keeps the typed casing for display. It raises `DuplicateEmail` when the canonical key exists.
  - In production, enforce the same rule with a unique index on `lower(trim(email))`, or use a case-insensitive column type.
- **Data migration:** run the duplicate query from the open questions first. Merge or flag the duplicate accounts. Then add the unique index.
- **Tests:** see Prevention.
- **Blast radius:** every email lookup and every signup. Signup now rejects a case variant of an existing address. That rejection is the intended behaviour.
- **Rollback:** revert `app/db.py` and drop the unique index. The migration does not change stored emails. Only merged accounts need a data rollback.

We recommend Fix B. The code change is about 15 lines in one file. It fixes all four callers and stops new duplicate accounts.
If support needs relief today, ship the code change of Fix B first and the migration second. The lookup change does not depend on the migration.

### Counterfactual

I applied the code change of Fix B to a temporary copy. I reran the repro and the sibling probes, then deleted the copy.

| Check | Before | After Fix B |
|---|---|---|
| `tests/test_search.py` | 1 of 2 fail | 2 of 2 pass |
| Search, three casings from the ticket | 1 of 3 found | 3 of 3 found |
| Search, `" Jane.smith@GMAIL.com"` | `not_found` | `ok` |
| Second signup with `bob@example.com` | accepted, id 2 | rejected, "email already registered" |
| `request_reset("bob@example.com")` | `ResetError` | `reset-token-for-1` |
| `send_invite("BOB@example.com")` | `invite_sent` | `already_member` |
| Display email returned by search | `Bob@Example.COM` | `Bob@Example.COM` |

**Outcome: confirmed with survivors.** The fix breaks link 4 because the store now has one canonical form. The repro would not fire.

The survivor is existing duplicate data. With two legacy rows for one mailbox, the lookup returns id 1 and id 2 becomes unreachable.
The code change cannot repair this. The data migration in Fix B covers it.

## Prevention

- **Test:** one table-driven test over every email entry point: search, the signup duplicate check, password reset, and invite. Each case signs up with one casing and calls with another. A new entry point gets a new row. This test catches the class, not only the search instance.
- **Guardrail:** make the canonical key the only way to compare emails.
  - In code, `find_by_email` and `insert` own the comparison. A lint rule or review check rejects `.email ==` outside `app/db.py`.
  - In the database, a unique index on the canonical key makes a duplicate impossible.
- **Doc:** add an invariant: "Email identity is case-insensitive and ignores surrounding whitespace. `app/db.py` owns the canonical form. The store is unique on it." Replace the docstring at `app/db.py:1`, which states the opposite rule.

## Open questions

1. **Does production hold case-variant duplicates?** Run `SELECT lower(trim(email)) AS k, count(*) FROM users GROUP BY k HAVING count(*) > 1`. The result sets the size of the migration.
2. **How do we resolve duplicates?** We can merge into the oldest account or flag them for support. Merging touches billing, and the ticket mentions Stripe. The owner of billing must decide.
3. **Is a case-insensitive local part the product rule?** RFC 5321 permits a case-sensitive local part. No mailbox in the ticket needs it, but the owner of identity should approve the rule.
4. **What changed on 2026-05-12?** The code did not change. A new signup client or import path may now send mixed-case emails. The answer tells us whether other fields also arrive without normalisation.
5. **What stays out of scope?** Provider-specific rules stay out, such as Gmail ignoring dots. Fix B does not treat `janesmith@gmail.com` and `jane.smith@gmail.com` as one customer.

## Side effects of this investigation

- I copied the fixture to `outputs/fixture` and ran its tests and Python probes there. Python created `__pycache__` directories, and I removed them.
- I applied Fix B to a temporary copy at `run-3/cf-tmp` and deleted the copy afterwards.
- The fixture matches the SHA-256 baseline from step 1. I pushed, published, or sent nothing.

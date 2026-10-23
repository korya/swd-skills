# RCA: user search misses emails whose casing differs from the stored value

## Headline

The user service has no definition of email identity, so every lookup compares raw strings. The string support types must match, character for character, the string the customer typed at signup. Search is the visible failure. Signup, password reset, and team invite share the same lookup and fail the same way. The recommended fix gives one module ownership of email normalization. It stores a normalized key next to the display email, and the store enforces uniqueness on that key.

## Symptom and scope

Support agents search for a customer by email and get "not found" for a customer who exists. The report quotes three attempts for one customer:

```
2026-05-12T09:14:22Z search.search_by_email email="Jane.Smith@gmail.com" -> not_found
2026-05-12T09:14:55Z search.search_by_email email="jane.smith@gmail.com" -> not_found
2026-05-12T09:15:33Z search.search_by_email email="Jane.smith@gmail.com" -> ok id=8412
```

Scope, from `BUG_REPORT.md`:

| Fact | Value |
|---|---|
| Who | customer-support agents using the internal user-search tool |
| First seen | 2026-05-12 |
| Frequency | 4 agents reported it within 24 hours |
| Cost | 5 to 10 minutes per ticket, plus a page to the data team |
| Severity filed | P2 |

Expected: a search for any casing of a registered email returns that user. Actual: only the casing stored at signup matches.

### Reproduction

`tests/test_search.py::test_search_finds_user_signed_up_with_mixed_case` is a deterministic repro. It signs up `Bob@Example.COM` and searches for `bob@example.com`.

```
AssertionError: 'not_found' != 'ok' : expected to find Bob, got {'status': 'not_found'}
Ran 2 tests in 0.000s
FAILED (failures=1)
```

### Baseline

The fixture is a plain directory with no version control. I copied it to `outputs/fixture` and recorded an md5 for each of its 9 source files before the investigation. The end of this report shows the copy restored to that baseline.

## Timeline

No history exists for this code, so I cannot name a responsible commit. The behaviour is designed in rather than regressed in. The module docstrings state it:

- `app/db.py:1` reads "In-memory user store. Case-sensitive lookups by email."
- `app/signup.py:1` reads "Signup flow. Stores email as the user typed it."

When a bug predates every visible change, the trigger is in the inputs. Four reports in 24 hours for a latent defect suggests a new input around 2026-05-12. Either a new source of mixed-case emails appeared, or support started entering them differently. See open question 1.

## 5-whys chain

1. **Why does search return "not found" for a registered customer?**
   - **Answer:** `search_by_email` returns `not_found` whenever `db.find_by_email` returns `None`.
   - **Evidence:** `app/search.py:7-9`. The repro output above.

2. **Why does `find_by_email` return `None`?**
   - **Answer:** It compares the stored email and the query with `==`, which is exact and case-sensitive for `str`.
   - **Evidence:** `app/db.py:34` reads `if u.email == email:`. Probe F2: the exact casing `Bob@Example.COM` returns `ok`, every other casing returns `not_found`.

3. **Why does the stored email differ in casing from what support types?**
   - **Answer:** Signup stores the email as the user typed it. Nothing normalizes it on the way in or on the way out.
   - **Evidence:** `app/signup.py:15` passes the raw string to `app/db.py:26`. `grep -rnE "\.lower\(\)|casefold|normalize" app tests` finds nothing.

4. **Why is there no normalization anywhere?**
   - **Answer:** The codebase has no definition of when two email strings denote the same account. There is no email type, no normalize function, and no uniqueness rule in the store. Each of the four flows passes raw input straight to the same exact-match lookup.
   - **Evidence:** `grep -rn find_by_email app` lists four callers at `app/search.py:7`, `app/signup.py:13`, `app/invite.py:7`, `app/password_reset.py:11`. `app/db.py:1` documents the lookup as case-sensitive.

5. **Why was that definition never made?**
   - **Answer:** Email is modelled as a bare `str` in a list with no key, so the system never forces the question. A `str` has one equality. Nothing in the data model, the store, or the tests can hold the invariant, so no code path ever had to state it.
   - **Evidence:** `app/db.py:10` declares `email: str`. `app/db.py:14` declares `_USERS: list[User]`. `app/db.py:24-29` inserts without any uniqueness check. The only test of case handling is the failing repro.

## Symptom, proximate cause, root cause

- **Symptom.** Support cannot find an existing customer unless the casing matches what the customer typed at signup.
- **Proximate cause.** `app/db.py:34` compares emails with exact string equality.
- **Root cause.** The service has no single owner of email identity. The data model stores the display string as the key, and no layer normalizes or enforces uniqueness. Four flows each inherited the gap.

### Falsification of the root cause

If the root cause were local to search, the other flows would handle casing correctly. They do not. Probes S1 to S3 against the unmodified code:

| Probe | Input | Result |
|---|---|---|
| S1 signup | `Bob@Example.COM`, then `bob@example.com`, then `BOB@EXAMPLE.COM` | 3 accounts created for one mailbox |
| S2 password reset | signed up as `Bob@Example.COM`, reset with `bob@example.com` | `ResetError: no such user` |
| S3 invite | member `Bob@Example.COM`, invite `bob@example.com` | `invite_sent` instead of `already_member` |

Second mechanism considered: the customer is in a different store, or the query carries hidden whitespace. The third log line, `ok id=8412`, places the customer in the same store the first two queries hit. The three log lines differ only in casing. Probe F2 shows trailing whitespace also misses, but the log shows none.

Cheapest disconfirming experiment: probe F1 normalized only the query, `search_by_email("bob@example.com".lower())`, and still got `not_found`. A search-side fix cannot work, because the stored value is the mixed-case one. The defect is upstream of search.

## Siblings

| Sibling | Where | Effect | Severity |
|---|---|---|---|
| Password reset | `app/password_reset.py:11` | A customer who types a different casing than at signup cannot reset their password. They are locked out. | High |
| Signup duplicate check | `app/signup.py:13` | The same mailbox can register several times. Each account has its own id. | High, data integrity |
| Team invite | `app/invite.py:7` | An existing member receives an invite, which opens a path to a second account. | Medium |
| Existing data | the `users` table | Any duplicates already created collide once lookups become case-insensitive. `find_by_email` would return the first match silently. Probe S4 shows 2 matches for one mailbox. | Unknown until measured, see open question 2 |
| Surrounding whitespace | `app/db.py:34` | A pasted email with a trailing space misses. Same class, not in the report. | Low |

## Assumptions

1. **Assumption:** The production store compares emails the same way the fixture does.
   - **How validated:** The report's logs show three casings and one hit, which is exactly the fixture's behaviour. The fixture is the code under investigation.
   - **Result:** Confirmed for the behaviour. The production schema is not in the repo, see open question 3.

2. **Assumption:** The product treats a whole email address as case-insensitive, local part included.
   - **How validated:** RFC 5321 allows a case-sensitive local part but discourages relying on it. Major providers treat addresses as case-insensitive. Support's own request is "tell us the rule", and no other rule lets them find customers.
   - **Result:** Confirmed as the rule to adopt. It is a product decision, and the fix encodes it in one place so it can change.

3. **Assumption:** Every email lookup in the codebase goes through `db.find_by_email`.
   - **How validated:** `grep -rn find_by_email app` lists 4 callers. `grep -rn "email" app` shows no other comparison.
   - **Result:** Confirmed for the repo. The data team's manual SQL bypasses it and is outside the repo.

4. **Assumption:** Normalizing the key does not have to change what users see.
   - **How validated:** The root-cause variant stores the display email as typed and the normalized key separately. `test_display_email_is_preserved` passes.
   - **Result:** Confirmed.

5. **Assumption:** Existing data contains no duplicates that a uniqueness rule would reject.
   - **How validated:** none. No production data in the repo.
   - **Result:** UNVERIFIED. The code fix does not depend on it. The rollout of the uniqueness rule does, see open question 2.

## Fix proposals

### A. Symptom fix, one line

- **Files:** `app/db.py:34`.
- **Approach:** compare `u.email.casefold() == email.casefold()`.
- **Tests:** the existing repro passes. The prevention suite below still fails 5 of 6 tests.
- **Blast radius:** every caller of `find_by_email` becomes case-insensitive at once. Where two accounts already share a mailbox, the lookup returns whichever was inserted first, with no warning. In a real database the equivalent `LOWER(email) = LOWER(?)` cannot use the index on `email`.
- **Rollback:** revert one line.

### B. Root-cause fix, with sibling repairs

- **Files:** new `app/email.py`. Edited `app/db.py` and `app/signup.py`. New `tests/test_email_identity.py`. 33 changed lines in `app/`.
- **Approach:**
  - `app/email.py` owns `normalize_email(raw) -> NormalizedEmail`. It strips whitespace, casefolds, and rejects strings without `@`. It is the one place the identity rule lives.
  - `User` gains `email_key: NormalizedEmail` next to `email`, the display form.
  - `db.insert` computes the key and raises `DuplicateEmail` on a collision. The store owns uniqueness, so no caller can bypass it.
  - `db.find_by_email` normalizes its argument before comparing keys. There is no way to look up without normalizing.
  - `signup` drops its own duplicate check and maps `DuplicateEmail` and `InvalidEmail` to `SignupError`. Invite, reset, and search need no change because they already call `find_by_email`.
  - Data repair, outside this repo: find rows that collide under `normalize_email`, merge or flag them, then add the unique constraint.
- **Tests:** the repro passes. `tests/test_email_identity.py` passes all 6 tests. The same file fails 22 cases on the unmodified code and 5 on fix A.
- **Blast radius:** signup rejects a casing variant of an existing email, which is the intended behaviour change. The data repair touches production rows and needs a merge policy.
- **Rollback:** revert the three source files and the test. The data repair needs its own reversible migration.

### Recommendation

Ship B. Fix A would stop the support tickets today but leaves the invariant implicit. Every new consumer of the `users` table, including the data team's SQL, would have to remember the rule. Fix A also masks the duplicate-account sibling, so the next report arrives as "two customers with the same email" instead of "not found". If the schedule needs A first, land it as a one-day bridge and keep B on the same ticket.

## Counterfactual

I applied each fix in an isolated scratchpad copy, not in the fixture. Then I ran the repro and the prevention suite on each.

| Variant | Repro test | Prevention suite (6 tests) | Store accepts a colliding `insert` |
|---|---|---|---|
| Unmodified | fails | 16 failures, 6 errors | yes |
| A, symptom | passes | 4 failures, 1 error | yes |
| B, root cause | passes | passes | no, `DuplicateEmail` |

Fix A: **confirmed with survivors**. It breaks link 2 of the chain. Survivors are the colliding `db.insert`, the existing duplicates, and pasted whitespace.

Fix B: **confirmed**. It breaks link 4 by giving the identity rule an owner, and link 5 by giving the store a key it must keep unique. The repro cannot fire, because `find_by_email` cannot run without normalizing.

## Prevention

- **Test.** `tests/test_email_identity.py` runs every flow against five casing and whitespace variants of one stored email, and asserts the store itself refuses a colliding insert. It fails 22 cases on the current code. This is the floor.
- **Guardrail, type.** `NormalizedEmail` is a `NewType`. Type-check with mypy so a raw `str` cannot reach a key comparison. At runtime the store normalizes on every entry, so the guardrail cannot be skipped.
- **Guardrail, constraint.** The store enforces uniqueness on the normalized key. In a real database that is `CREATE UNIQUE INDEX ON users (email_key)` or a `citext` column. A duplicate then fails loudly at insert instead of silently at lookup.
- **Guardrail, lint.** A CI grep that fails on `.email ==` or `email ==` outside `app/email.py` keeps a future flow from reintroducing a raw comparison.
- **Doc.** Add an invariant to the README or `AGENTS.md`: "Email identity is case-insensitive. `app.email.normalize_email` is the only definition. Lookups and uniqueness use `email_key`." Replace the docstrings at `app/db.py:1` and `app/signup.py:1`, which currently document the defect as the design.

## Open questions

1. What changed around 2026-05-12? A latent defect with 4 reports in 24 hours points to a new source of mixed-case signups or a change in how support enters emails. The repo cannot answer this.
2. How many existing rows collide under `normalize_email`, and what is the merge policy? This gates the uniqueness constraint, not the code fix.
3. What is the production schema? If `email` is a database column, the fix also needs the index or `citext` change above, and the data team's SQL needs the same rule.
4. Should normalization go beyond casing and whitespace? Gmail ignores dots and `+suffix` in the local part. The log's `Jane.smith@gmail.com` hints at that. I recommend no, since provider-specific rules belong to a different decision.

## Investigation side effects

- Reversible and local only. I copied the fixture to `outputs/fixture` and did not edit it. I ran its tests, which created `__pycache__/*.cpython-315.pyc` files, and removed them afterwards.
- The two fix variants and the prevention test live in the scratchpad at `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/rca-cf/`, under `symptom/` and `root/`.
- Nothing was pushed, published, or sent.
- Restoration: `diff -r` between the source fixture and the copy reports no differences. The 9 md5 sums match the baseline.

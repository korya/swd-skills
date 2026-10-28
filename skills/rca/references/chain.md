# The causal chain: 5-whys, cause labels, load-bearing assumptions

Loaded from `SKILL.md` step 4. Covers steps 4, 5, and 7. The worked examples are the
point of this file. The rules follow each one.

## 4. Run the 5-whys chain

Start from the symptom. Each answer becomes the next "why". Write the chain as a numbered
list with the same fields on every item. Narrative prose makes it easy to chain unverified
claims fluently.

1. **Why did the request return 500?**
   - **Answer:** The `customers` query returned 0 rows for an authenticated user.
   - **Evidence:** `api/customers.ts:42` has `if (rows.length === 0) throw 500`. Log
     `req-id=abc123` shows an empty result set.

2. **Why did it return 0 rows?**
   - **Answer:** The WHERE clause filters on `org_id`, and the user's `org_id` was `null`.
   - **Evidence:** `api/customers.ts:38` query. `psql> SELECT org_id FROM users WHERE
     id='...'` returns `null`.

3. **Why was `org_id` null?**
   - **Answer:** The signup flow does not backfill `org_id` for users created via the
     magic-link path.
   - **Evidence:** `auth/magic-link.ts:71-95` has no call to `assignOrg()`. Compare
     `auth/password.ts:60`, which does call it.

4. **Why doesn't it backfill?**
   - **Answer:** The org-assignment hook is wired to the password-signup path only.
   - **Evidence:** `auth/hooks.ts:12` registers only `on('password-signup', ...)`.

5. **Why is it wired only there?**
   - **Answer:** Magic-link signup was added later (commit `a1b2c3d`) and the author did not
     know the hook existed. No contract documented it.
   - **Evidence:** `git log -S "magic-link" auth/`. `docs/auth.md` has no mention of the
     hook contract.

Rules:

- **One mechanical step per why.** Do not jump three layers.
- **Stop at the level whose fix prevents siblings.** Above it you are fixing symptoms.
  Below it you are philosophising ("because software is hard"). A root cause with no
  siblings usually means you stopped at a proximate one.
- **Evidence on every link:** a `file:line`, a query result, a log excerpt, or a commit
  SHA. "Looks like" or "probably" is not evidence. Mark that link `UNVERIFIED`, then get
  the evidence or stop the chain there.
- **Branch when there are parallel causes.** Run a chain per branch.

## 5. Label the causes and falsify the root

- **Symptom.** What the user saw.
- **Proximate cause.** The line of code or condition that directly produced the symptom.
- **Root cause.** The upstream defect, missing safeguard, or design gap that allowed the
  proximate cause to exist.

A fix at the proximate cause stops this failure. A fix at the root cause stops the class.
Present both so the user chooses with eyes open.

**Then falsify the root cause.** Evidence per link proves each step, not the synthesis. A
chain can verify link by link and still land on a real defect that did not produce this
symptom. Write down three things:

- **What would we see** in logs, the repro, or data if X were not the root cause?
- **Is there a second mechanism** that produces the same symptom without X? If yes, what
  tells them apart here?
- **What is the cheapest disconfirming experiment?**

Run it if it is cheap. If not, surface it as a limitation: "we believe X is the root cause.
We have not ruled out Y."

## 7. List and validate load-bearing assumptions

Before proposing any fix, list the assumptions the root cause and the fix rest on, then
validate them. Validating as you go produces a list of what happened to be true. Listing
first surfaces what you depend on.

1. **Assumption:** `assignOrg()` is the only mechanism that sets `org_id`.
   - **How validated:** `grep -rn "org_id\s*=" .` finds only `assignOrg()` and the seed
     script writing it.
   - **Result:** Confirmed.

2. **Assumption:** All magic-link users have `org_id = null`, not just the reported one.
   - **How validated:** `psql> SELECT count(*) FROM users WHERE signup_method='magic_link'
     AND org_id IS NULL` returns 1,247.
   - **Result:** Confirmed. Sibling impact is large.

3. **Assumption:** Adding `assignOrg()` to the magic-link path will not double-assign for
   users who already have an org.
   - **How validated:** Read `assignOrg()`. It is idempotent and returns early when `org_id`
     is already set.
   - **Result:** Confirmed.

4. **Assumption:** The hook contract is the right enforcement layer, rather than a DB
   constraint.
   - **How validated:** none.
   - **Result:** UNVERIFIED. Surface as an open question.

An assumption you cannot validate cheaply is the finding. Surface it as an open question.
A fix that needs an `UNVERIFIED` assumption is a hypothesis dressed as a fix. Say so when
you propose it.

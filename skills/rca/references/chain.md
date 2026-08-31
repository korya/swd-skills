# The causal chain: 5-whys, cause classification, load-bearing assumptions

Loaded from `SKILL.md` step 3. Covers steps 3, 4 and 5.5 — the evidence-per-link chain,
separating symptom from proximate from root cause and falsifying the root, and the
assumption list the fix may rest on. Worked examples are the point of this file; the rules
follow each one.

## 3. Run the 5-whys chain

Start from the symptom. At each step, the answer becomes the next "why." Record the chain as a **numbered list**, with each item carrying the same three fields — narrative prose makes it easy to chain unverified claims fluently; explicit per-item fields force evidence per link.

1. **Why did the request return 500?**
   - **Answer:** The `customers` query returned 0 rows for an authenticated user.
   - **Evidence:** `api/customers.ts:42` — `if (rows.length === 0) throw 500`; log `req-id=abc123` shows empty result set.

2. **Why did it return 0 rows?**
   - **Answer:** The WHERE clause filters on `org_id`, and the user's `org_id` was `null`.
   - **Evidence:** `api/customers.ts:38` query; `psql> SELECT org_id FROM users WHERE id='…'` → `null`.

3. **Why was `org_id` null?**
   - **Answer:** The signup flow doesn't backfill `org_id` for users created via the magic-link path.
   - **Evidence:** `auth/magic-link.ts:71-95` — no call to `assignOrg()`; cf. `auth/password.ts:60` which does call it.

4. **Why doesn't it backfill?**
   - **Answer:** The org-assignment hook is wired to the password-signup path only.
   - **Evidence:** `auth/hooks.ts:12` registers only `on('password-signup', …)`.

5. **Why is it wired only there?**
   - **Answer:** Magic-link signup was added later (commit `a1b2c3d`) and the author didn't know the hook existed — no contract documented it.
   - **Evidence:** `git log -S "magic-link" auth/`; `docs/auth.md` has no mention of the hook contract.

Rules:

- **Each why is mechanical, not narrative.** Don't jump three layers. One step at a time.
- **Stop when the answer is "and a fix here prevents siblings."** Above that level you're fixing symptoms; below that level you're philosophising ("because software is hard").
- **Evidence is mandatory, per link.** Each row's Evidence cell must cite a `file:line`, query result, log excerpt, or commit SHA. A blank or hand-wavy cell ("looks like…", "probably because…", "the author must have…") is *itself a finding* — mark the row `UNVERIFIED`, and either go get the evidence or stop the chain there. An unverified link cannot support the links below it.
- **Branch if needed.** Some failures have multiple parallel causes; run a chain per branch.

## 4. Distinguish symptom / proximate cause / root cause

Restate the chain, labelling:

- **Symptom** — what the user saw
- **Proximate cause** — the line of code or condition that directly produced the symptom
- **Root cause** — the upstream defect, missing safeguard, or design gap that *allowed* the proximate cause to exist

A fix at the proximate cause stops *this* failure. A fix at the root cause stops the *class*.

Both are legitimate — but the user should choose with eyes open. Present both options.

**Then falsify the root cause.** Per-link evidence proves each step; it does *not* prove the synthesis ("therefore X is the root cause"). A chain can be link-by-link verified and still synthesise to the wrong root — e.g. you found a real defect, but not the one that produced this symptom. Write down:

- **What would we see** (in logs, repro, data) if X were *not* the actual root cause?
- **Is there a second mechanism** that could produce the same symptom without going through X? If yes, what distinguishes which one fired here?
- **Cheapest disconfirming experiment** available?

If a cheap disconfirming experiment exists, run it. If not, surface the falsifier as a known limitation — "we believe X is the root cause; we have not ruled out Y." A hypothesis you can't even imagine disproving is religion, not analysis.

## 5.5. List and validate load-bearing assumptions

Before proposing any fix, write down the assumptions the root-cause hypothesis and the eventual fix rest on, as a **numbered list** with the same three fields per item. Validating-as-you-go produces a list of "things that happen to be true" — listing first, then validating, surfaces the assumptions you actually depend on.

1. **Assumption:** `assignOrg()` is the *only* mechanism that sets `org_id`.
   - **How validated:** `grep -rn "org_id\s*=" .` — only `assignOrg()` and the seed script write it.
   - **Result:** Confirmed.

2. **Assumption:** All magic-link users have `org_id = null` (not just the reported one).
   - **How validated:** `psql> SELECT count(*) FROM users WHERE signup_method='magic_link' AND org_id IS NULL` → 1,247.
   - **Result:** Confirmed; sibling impact is large.

3. **Assumption:** Adding `assignOrg()` to the magic-link path won't double-assign for users who already have an org.
   - **How validated:** Read `assignOrg()`: idempotent — early-returns when `org_id` is already set.
   - **Result:** Confirmed.

4. **Assumption:** The hook contract is the right enforcement layer (vs. a DB constraint).
   - **How validated:** —
   - **Result:** UNVERIFIED — surface as open question.

Rules:

- **List the assumption *before* you validate it.** Otherwise you list what you happened to check, not what you actually depend on.
- **An unvalidated assumption is a load-bearing guess.** If you can't validate one cheaply, that *is* the finding — surface it as an open question rather than quietly proceeding.
- **The fix may only depend on validated assumptions.** If the proposed fix needs an `UNVERIFIED` assumption to be true, it's a hypothesis dressed as a fix — say so explicitly when proposing it.

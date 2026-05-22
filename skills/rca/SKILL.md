---
name: rca
description: Conduct a root-cause analysis on a bug, incident, or regression — reproduce the failure, reconstruct the timeline, run a 5-whys chain, distinguish symptom from proximate cause from root cause, sweep for siblings, and propose a fix that addresses the cause (not the symptom). Use when the user says "/rca", "root cause", "5 whys", "why is this failing", "investigate this regression", or after any failure the team wants to learn from rather than just patch.
---

# RCA: failure-first investigation

The point of this skill is **not** to fix a bug. It is to understand *why* the bug happened deeply enough that the fix kills the cause, not just the symptom — and to catch the class of failure next time, not just this instance.

`/blueprint` plans a *change* you want to make. `/rca` investigates a *failure* you didn't want. The shapes are different: planning starts from a goal, RCA starts from a fact (something broke).

## When to invoke

- "/rca <thing>" / "do a root cause analysis on …"
- Regressions: something that used to work no longer does
- Production incidents and post-mortems
- Bugs whose first-pass fix the user finds suspicious ("are we sure that's *why* it broke?")
- Any failure where the team will pay for the same bug again if you just patch the symptom
- When `/blueprint`'s validation reveals that the load-bearing assumption *was already wrong in prod*

Do **not** invoke for: trivial bugs with obvious causes (typo, missing null check on a fresh edit, lint error), or for *future* failures you're trying to design around — that's `/blueprint` territory.

## Operating principles

- **Repro first.** A bug you can't trigger is a story, not a finding. Until you can reproduce it (or read a trace of it firing), every theory is unfalsifiable.
- **The symptom is not the cause.** It's evidence of the cause. Treating it as the cause produces fixes that hold until the next adjacent failure.
- **Ask why five times, mechanically.** Each answer becomes the next question's subject. Stop when you hit something whose fix prevents siblings, not just this instance.
- **Look for siblings.** A real root cause almost always has more than one manifestation. If you found only one, you probably stopped at a proximate cause.
- **Fix the cause, prevent the class.** "What stops this bug" and "what stops bugs *like* this" are different questions. RCA owes the user both.

## Workflow

### 1. Capture the failure

Before any theorising, write down:

- **Symptom** — what the user/system observed (error message, wrong output, hang, crash). Quote logs/screenshots verbatim if available.
- **Scope** — who is affected (one user / all users / specific tenant / specific environment), since when, how often.
- **Expected vs. actual** — what the system was supposed to do.
- **Reproduction** — exact steps. If unknown, treat finding a repro as step 1.5.

If any of this is ambiguous, **ask the user**. RCA on a fuzzy symptom is a fishing expedition.

### 1.5. Establish a repro (or a trace)

You need one of:

- A deterministic reproduction (manual steps, failing test, script)
- A captured trace of the failure (logs, stack trace, error report with enough context)

Without either, every subsequent step is speculation. If a repro is elusive, that itself is the finding — surface it and discuss instrumentation before continuing.

### 2. Reconstruct the timeline

When did it start? What changed?

```bash
git log --since="<earliest known-good>" --until="<earliest known-bad>" -- <area>
```

Also check: deploys, dependency bumps, infra changes, feature-flag toggles, data migrations, traffic shifts. The cause is almost always in the delta.

If the bug pre-dates any plausible change, the cause is likely a latent condition that something *new* started exercising. Look for what's new in the inputs, not the code.

### 3. Run the 5-whys chain

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

### 4. Distinguish symptom / proximate cause / root cause

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

### 5. Sibling-impact sweep

If the root cause is real, where else does it manifest?

- Other call sites of the same function / hook / path
- Other entry points that bypass the same safeguard
- Other tenants / environments / channels that share the same defective assumption
- Data already in the system that's silently corrupted by the same cause

```bash
grep -rn "<the function/condition>" .
git log -S"<distinctive token>"
```

Found siblings get reported alongside the primary. A "root cause" with zero siblings is suspicious — re-examine whether you stopped at a proximate cause.

### 5.5. List and validate load-bearing assumptions

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

### 6. Propose the fix(es)

Two distinct proposals, separated:

1. **Symptom fix** — the smallest change that makes the reported failure stop. Useful when shipping fast matters.
2. **Root-cause fix** — the upstream change that addresses the gap; includes sibling repairs.

For each: files, approach, test coverage, blast radius, rollback story.

Recommend one. The recommendation depends on urgency, risk, and whether the symptom fix would mask the cause from future detection.

### 6.5. Counterfactual: would the fix have prevented the captured repro?

Close the loop between cause and fix. For each proposed fix (especially the root-cause one — the symptom fix is trivially counterfactual-true by construction), walk it through the captured failure and answer:

- **If this fix had been in place when the failure was captured, would the repro still fire?**
- **Which link in the 5-whys chain does the fix break?** If the answer is "link 2" but you claimed the root cause is at link 5, the fix is too shallow — name what it doesn't prevent.
- **Does the fix address the captured failure**, or only a related failure that shares the same root cause?

Land on one of:

- **Confirmed** — repro would not fire under the fix; name the link it breaks.
- **Confirmed for this case, but a sibling path remains** — fix stops the captured repro but not all manifestations from the same root. List the survivors (and consider whether the fix is wide enough).
- **Unconfirmed** — the fix addresses a real defect but it's not clear it addresses *this* failure. **Stop.** Either the chain points at the wrong cause or the fix targets the wrong layer; revisit before recommending.

A fix that can't survive its own counterfactual is a hypothesis dressed as a fix. Say so when proposing it, or pick a different fix.

### 7. Prevent the class

For the root-cause fix, also propose:

- **A test** — unit, integration, or e2e — that would have caught this. If no test layer would catch it, that *is* a finding.
- **A guardrail** — type, lint rule, assertion, schema constraint, code-review checklist item, monitoring alert. The goal is that this *class* of bug becomes either impossible or loud.
- **A doc update** — if a spec, invariant, or `AGENTS.md` missed the constraint that would have flagged this, update it.

"Add a test for this exact bug" is the weakest prevention. "Make this class of bug impossible to express" is the strongest. Aim higher than the floor.

### 8. Report

Inverted pyramid:

1. **Headline** — one sentence: what broke, what the root cause was, recommended fix.
2. **Symptom / scope** — what users saw, who was affected, when it started.
3. **5-whys chain** — the verified chain with citations (file:line, log excerpt, commit SHA).
4. **Symptom / proximate / root** — labelled.
5. **Siblings** — list, with severity.
6. **Fix proposals** — symptom fix, root-cause fix, recommendation.
7. **Prevention** — test, guardrail, doc update.
8. **Open questions** — anything needing user input before implementation.

## Anti-rationalization table

When tempted to skip a step, check whether your reasoning appears below. If it does, the answer is: do the step.

| Rationalization | Why it fails here |
|---|---|
| "The fix is obvious, skip the RCA." | If the fix were truly obvious, the user wouldn't have invoked `/rca`. Obvious fixes go via `/plan` or a one-line edit. The invocation is the signal that depth is required. |
| "I can't reproduce it, but I'm pretty sure I know why." | Pretty-sure-without-repro is the modal cause of "the same bug came back next week." If you can't reproduce, the deliverable is "we need a repro / better instrumentation," not a guess dressed as a finding. |
| "Three whys is enough." | Three whys usually lands on a proximate cause. The whole point of five is to push past the comfortable stopping point. |
| "The symptom *is* the cause — fix and ship." | The symptom is *evidence* of the cause. Fix the symptom and the cause moves to its next manifestation. |
| "No siblings found, so the cause is local." | Or you stopped too early. Re-examine. A genuinely local root cause is possible but rare. |
| "Adding a test for this exact case is enough prevention." | That catches the regression, not the class. Ask whether a guardrail, type, or invariant could prevent the *class* from being expressible at all. |
| "The 5-whys chain reads fine, I don't need to verify each link." | A coherent narrative is not the same as a correct one. Verify each link against code, logs, or data. |
| "The cause is 'the original author didn't anticipate this' — done." | That's a no-op finding. The actionable root cause is: what process / type / test / doc would have made them anticipate it? |
| "RCA can wait, let's ship the fix first." | Fine, *if* the RCA has a deadline before the on-call rotation forgets. RCAs deferred indefinitely become RCAs never done. Set the deadline now. |
| "I'll just `git bisect` and call the offending commit the root cause." | The commit is *where* the cause was introduced, not *what* the cause is. Bisect locates the change; the 5-whys explains why the change was wrong and what allowed it through. |

## Anti-patterns

- **Treating RCA as a postmortem template to fill in.** Boxes filled ≠ cause understood. The chain must be verified, not just authored.
- **Concluding "human error."** Almost never the root cause; almost always a proximate cause. The root cause is the system that let the human err undetected.
- **Stopping at "we didn't have a test."** Test absence is itself a symptom — of a process or design gap. Why was there no test? Why did review not catch it?
- **Fixing siblings silently.** If you found three other places with the same cause, the user should hear about them, not discover them in the diff.
- **Confusing a longer chain for a deeper one.** Five whys is a floor and a discipline, not a quota. Three rigorous whys beats seven hand-wavy ones.
- **RCA-as-blame.** The output is a system change, not a person. If the report names a person, rewrite it.

## Definition of done

The RCA is complete when **all** of these are true. Each item is answerable with evidence — a citation, a log excerpt, a commit SHA — not a vibe.

- [ ] Failure captured: symptom, scope, expected vs. actual, time window — all written down.
- [ ] Repro or trace established; if neither, the *finding* is "we need instrumentation" and the RCA is paused, not faked.
- [ ] Timeline reconstructed: the change(s) plausibly responsible are named, with commits / deploys / config flips cited.
- [ ] 5-whys chain produced as a numbered list; **every item has a populated Answer and Evidence field** (file:line, query result, log excerpt, or commit SHA). Any `UNVERIFIED` link is explicitly flagged, and no link below an `UNVERIFIED` one is treated as proven.
- [ ] Symptom / proximate cause / root cause explicitly labelled and distinguished — **and** the root cause is falsified: what observation would disprove it is written down, or the absence of a cheap falsifier is itself surfaced as a limitation.
- [ ] Sibling sweep performed; either siblings are listed, or the absence is justified — "no siblings" alone is not enough.
- [ ] Load-bearing assumptions enumerated as a numbered list with populated **How validated** and **Result** for each. Any `UNVERIFIED` assumption is surfaced as an open question; the recommended fix does **not** silently depend on one.
- [ ] Two fix proposals presented (symptom-level and root-cause-level), with a recommendation and a reason.
- [ ] Counterfactual check performed on the recommended fix; result is recorded as **Confirmed**, **Confirmed-with-survivors** (survivors listed), or **Unconfirmed** — and **Unconfirmed means the RCA is not done**.
- [ ] Prevention proposed: at minimum a test; ideally a guardrail or doc that prevents the *class*.
- [ ] Report delivered inverted-pyramid, with open questions surfaced (not silently answered).
- [ ] No "human error" conclusions. No findings that name a person rather than a system.

If a checkbox cannot be ticked honestly, the RCA is not done — return to the step that produces it.

## Relationship to other skills

- `/blueprint` — for designing a *change*. Use after RCA when the root-cause fix is non-trivial enough to warrant deep planning.
- `/plan` — for the symptom fix when it's small and obvious.
- `/rebase` — unrelated; named here only so future-you doesn't conflate "regression after rebase" with "rebase failure." Regression after rebase → `/rca`; merge-conflict failure → `/rebase`.
- The "regression CRA" referenced in `docs/guidelines.md` (per the `repo-docs` skill) is this skill, applied to a regression specifically.

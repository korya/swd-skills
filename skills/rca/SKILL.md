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
- **Investigate without irreversible or hidden side effects.** Experiments probe the subject; they must not mutate it for anyone else. The rules below draw the boundary; anything past it is a question for the user, not a judgment call.

### Side-effect rules

Reversibility is judged by **observable effects**, not artifact state: if anyone was notified or any system reacted, undoing the artifact does not undo the effect.

| Effect class | Policy |
|---|---|
| **Irreversible** — publish a version, deploy, reset a DB, reboot a machine, send a message | Requires explicit approval obtained *during this investigation*. |
| **Visible to others / touches others' work** — push to a PR, comment on one, trigger CI, anything another person or system observes | Approval **before** the act. Disclosure after the fact is not consent. |
| **Reversible and local** — working-tree edits, probe scripts, local branches, injected canaries | Allowed. Reverted by default; everything touched is disclosed in the report. |

Two further rules:

- **Prefer an isolated workspace.** Run experiments in a separate workspace (`git worktree add …`) rather than the user's working tree, unless the repro depends on the live environment (uncommitted state, a running server, a local DB) or the user asked to work in place. Needing the live environment is a stated finding, not a silent default.
- **Consent does not carry over.** Approval granted for an earlier task in the session (a `/submit`, an explicit "push it") authorizes nothing here. If an experiment needs to cross the boundary, prompt the user now.

## Workflow

### 1. Capture the failure

Before any theorising, write down:

- **Symptom** — what the user/system observed (error message, wrong output, hang, crash). Quote logs/screenshots verbatim if available.
- **Scope** — who is affected (one user / all users / specific tenant / specific environment), since when, how often.
- **Expected vs. actual** — what the system was supposed to do.
- **Reproduction** — exact steps. If unknown, treat finding a repro as step 1.5.
- **Baseline** — the working-tree state before any experimenting: current branch, `HEAD` sha, `git status --porcelain` output. The end-of-investigation restore check compares against this, not against "clean" — the user's own uncommitted work is part of the baseline, not something to revert.

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

**Read `references/chain.md` now**; it covers steps 3, 4 and 5.5.

### 4. Distinguish symptom / proximate cause / root cause

Per `references/chain.md` § 4.

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

Per `references/chain.md` § 5.5.

### 6. Propose the fix(es)

**Read `references/fix.md` now**; it covers steps 6, 6.5, 7 and 8.

### 6.5. Counterfactual: would the fix have prevented the captured repro?

Per `references/fix.md` § 6.5.

### 7. Prevent the class

Per `references/fix.md` § 7.

### 8. Report

Per `references/fix.md` § 8.

## Anti-rationalization

When tempted to skip a step, read `references/rationalizations.md`.

## Definition of done

The RCA is complete when **all** of these are true. Each item is answerable with evidence — a citation, a log excerpt, a commit SHA — not a vibe.

- [ ] Failure captured: symptom, scope, expected vs. actual, time window, working-tree baseline — all written down.
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
- [ ] Investigation left no trace: working tree restored to the step-1 baseline (`git status` compared and shown); nothing pushed, published, or sent to any person or third-party system without explicit approval obtained *during this investigation* — consent from an earlier task does not carry over.
- [ ] No "human error" conclusions. No findings that name a person rather than a system.

If a checkbox cannot be ticked honestly, the RCA is not done — return to the step that produces it.

## Relationship to other skills

- `/blueprint` — for designing a *change*. Use after RCA when the root-cause fix is non-trivial enough to warrant deep planning.
- `/plan` — for the symptom fix when it's small and obvious.
- `/rebase` — unrelated; named here only so future-you doesn't conflate "regression after rebase" with "rebase failure." Regression after rebase → `/rca`; merge-conflict failure → `/rebase`.
- The "regression CRA" referenced in `docs/guidelines.md` (per the `repo-docs` skill) is this skill, applied to a regression specifically.

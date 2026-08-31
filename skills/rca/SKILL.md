---
name: rca
description: Conduct a root-cause analysis on a bug, incident, or regression — reproduce the failure, reconstruct the timeline, run a 5-whys chain, distinguish symptom from proximate cause from root cause, sweep for siblings, and propose a fix that addresses the cause (not the symptom). Use when the user says "/rca", "root cause", "5 whys", "why is this failing", "investigate this regression", or after any failure the team wants to learn from rather than just patch.
---

# RCA: failure-first investigation

The point is **not** to fix a bug. It is to understand *why* it happened deeply enough that
the fix kills the cause, not the symptom — and catches the class next time, not the
instance. `/blueprint` plans a change you want; `/rca` investigates a failure you didn't.

Invoke for regressions, incidents and post-mortems, a first-pass fix the user finds
suspicious, or any failure the team would otherwise pay for again. Not for trivial bugs
with obvious causes, or for future failures you are designing around — that is `/blueprint`.

## Required references

This file is the skeleton; each reference holds a step's full rules and worked examples.
Read it **at that step**.

| File | Read at | Holds |
|---|---|---|
| `references/chain.md` | step 3 | 5-whys chain with evidence per link, cause classification and falsification, assumption list |
| `references/fix.md` | step 6 | symptom vs root-cause fixes, counterfactual, prevention, report structure |
| `references/rationalizations.md` | when tempted to skip a step | why each shortcut fails |

## Principles

- **Repro first.** A bug you can't trigger is a story; until you reproduce it or read a
  trace of it firing, every theory is unfalsifiable.
- **The symptom is evidence of the cause, not the cause.** Fixing it holds until the next
  adjacent failure.
- **Ask why mechanically.** Each answer is the next question's subject; stop at the level
  whose fix prevents siblings. A root cause with no siblings usually means you stopped at a
  proximate one.
- **Fix the cause, prevent the class.** RCA owes the user both answers.

## Side-effect rules

Reversibility is judged by observable effects, not artifact state: undoing the artifact
does not un-notify anyone or un-run anything.

- **Irreversible** (publish, deploy, reset a DB, reboot, send a message) — explicit approval
  obtained *during this investigation*.
- **Visible to others** (push to a PR, comment, trigger CI, anything a person or system
  observes) — approval **before** the act; disclosure after is not consent.
- **Reversible and local** (working-tree edits, probe scripts, local branches, canaries) —
  allowed; reverted by default and disclosed in the report.

Prefer an isolated workspace (`git worktree add …`) unless the repro needs the live
environment — a stated finding, not a silent default. Consent from an earlier task does not
carry over; if an experiment must cross the line, ask now.

## Workflow

1. **Capture the failure.** Symptom (quote logs verbatim), scope (who, since when, how
   often), expected vs actual, reproduction steps, and the working-tree **baseline**
   (branch, `HEAD`, `git status --porcelain`) the end check restores to — the user's own
   uncommitted work is part of it. Ambiguous → ask; RCA on a fuzzy symptom is fishing.
1.5. **Repro or trace.** A deterministic repro (steps, failing test, script) or a captured
   trace with enough context. Neither → the finding is "we need instrumentation"; surface
   it before continuing.
2. **Timeline.** `git log --since=<known-good> --until=<known-bad> -- <area>`, plus deploys,
   dependency bumps, infra and flag changes, migrations, traffic shifts. If the bug predates
   every change, look for what is new in the inputs, not the code.
3. **5-whys chain.** **Read `references/chain.md` now.** A numbered list; every link carries
   **Answer** and **Evidence** (`file:line`, query result, log excerpt, commit SHA). One
   mechanical step per why; a link without evidence is marked `UNVERIFIED` and supports
   nothing below it; branch when there are parallel causes.
4. **Classify and falsify.** Label symptom, proximate cause, root cause. Then try to
   disprove the root: what would you see if it were wrong, what second mechanism produces
   the same symptom, what is the cheapest disconfirming experiment — run it, or report the
   unrun falsifier as a limitation.
5. **Sibling sweep.** Other call sites, entry points bypassing the same safeguard, tenants
   or channels sharing the assumption, data already corrupted. `grep -rn`, `git log -S`.
   Report siblings alongside the primary.
5.5. **Assumptions** (`chain.md` § 5.5). List every assumption the root cause and the fix
   rest on *before* validating; each gets **How validated** and **Result**. The fix may rest
   only on confirmed ones; an `UNVERIFIED` assumption is an open question, not a foundation.
6. **Propose fixes.** **Read `references/fix.md` now.** Two proposals, separated: the
   smallest symptom fix and the root-cause fix with sibling repairs — files, approach,
   tests, blast radius, rollback. Recommend one and say why.
6.5. **Counterfactual.** Walk the recommended fix through the captured failure: would the
   repro still fire, which link does it break? **Confirmed**, **confirmed with survivors**
   (list them), or **unconfirmed** — and unconfirmed means the RCA is not done.
7. **Prevent the class.** A test that would have caught it, a guardrail (type, lint,
   assertion, constraint, alert) that makes the class impossible or loud, a doc update
   where a spec or invariant missed the rule. "A test for this exact bug" is the floor.
8. **Report**, inverted pyramid per `fix.md` § 8: headline, symptom and scope, the chain
   with citations, cause labels, siblings, fix proposals, prevention, open questions.

## Definition of done

Each item is answerable with evidence, not a vibe; one you cannot tick honestly sends you
back to the step that produces it.

- [ ] Failure captured with scope, time window, and working-tree baseline; repro or trace
  established, or the RCA is paused for instrumentation, not faked.
- [ ] Timeline names the responsible change(s) with commits, deploys, or config flips cited.
- [ ] Every chain link has Answer and Evidence; `UNVERIFIED` links are flagged and nothing
  below one is treated as proven.
- [ ] Symptom, proximate, and root cause labelled; the root's falsifier written down or its
  absence surfaced; siblings listed or their absence justified.
- [ ] Assumptions listed with How validated and Result; the recommended fix depends on no
  `UNVERIFIED` one.
- [ ] Two fix proposals with a recommendation; counterfactual recorded, and not
  unconfirmed.
- [ ] Prevention proposed — at minimum a test, ideally a guardrail or doc.
- [ ] Report delivered inverted-pyramid; open questions surfaced, none silently answered;
  no "human error" conclusion, no finding that names a person rather than a system.
- [ ] No trace left: tree restored to the step-1 baseline and shown; nothing pushed,
  published, or sent without approval obtained during this investigation.

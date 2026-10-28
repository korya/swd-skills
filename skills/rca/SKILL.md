---
name: rca
description: Conduct a root-cause analysis on a bug, incident, or regression — reproduce the failure, reconstruct the timeline, run a 5-whys chain, distinguish symptom from proximate cause from root cause, sweep for siblings, and propose a fix that addresses the cause (not the symptom). Use when the user says "/rca", "root cause", "5 whys", "why is this failing", "investigate this regression", or after any failure the team wants to learn from rather than just patch.
---

# RCA: failure-first investigation

The point is not to fix a bug. The point is to understand why it happened. The fix must
kill the cause, not the symptom, and catch the class next time, not the instance.

Do not invoke it for a trivial bug with an obvious cause. A failure you want to design
around before it happens is `/blueprint`.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it. Read each
file at the step named.

| File | Read at | Holds |
|---|---|---|
| `references/chain.md` | step 4 | the 5-whys chain with evidence per link, cause labels and falsification, the assumption list |
| `references/fix.md` | step 8 | the two fix proposals, the counterfactual, prevention, the report structure |
| `../../assets/writing.md` | step 11, before writing the report | the writing rules for every text a person reads |
| `references/rationalizations.md` | when tempted to skip a step | why each shortcut fails |

## Side effects

Reversibility is judged by observable effects, not artifact state. Undoing the artifact
does not un-notify anyone or un-run anything.

- **Irreversible** actions, such as a publish, a deploy, a DB reset, or a sent message,
  need explicit approval obtained during this investigation.
- **Visible to others** actions, such as a push to a PR, a comment, or a CI trigger, need
  approval before the act. Disclosure after is not consent.
- **Reversible and local** actions, such as working-tree edits, probe scripts, and local
  branches, are allowed. Revert them by default and disclose them in the report.

Prefer an isolated workspace (`git worktree add ...`) unless the repro needs the live
environment, and state which one you used. Consent from an earlier task does not carry
over. If an experiment must cross the line, ask now.

## Workflow

1. **Capture the failure.** Record the symptom with logs quoted verbatim, the scope (who,
   since when, how often), expected against actual, and the reproduction steps. Record the
   working-tree baseline (branch, `HEAD`, `git status --porcelain`) that the end check
   restores to. The user's own uncommitted work is part of it. If the symptom is
   ambiguous, ask.
2. **Repro or trace.** Get a deterministic repro or a captured trace. A bug you cannot
   trigger is a story. With neither, the finding is "we need instrumentation". Surface it
   before continuing.
3. **Timeline.** Find what changed between known-good and known-bad: commits in the area,
   deploys, dependency bumps, flag and infra changes, migrations, traffic shifts. If the
   bug predates every change, look for what is new in the inputs.
4. **5-whys chain.** Read `references/chain.md` now. Write a numbered list where every
   link carries **Answer** and **Evidence**. A link without evidence is `UNVERIFIED` and
   supports nothing below it.
5. **Classify and falsify.** Label the symptom, the proximate cause, and the root cause.
   Then try to disprove the root, and run the cheapest disconfirming experiment or report
   it as a limitation.
6. **Sibling sweep.** Find the other call sites, entry points that bypass the same
   safeguard, consumers that share the assumption, and data already corrupted. Report them
   beside the primary.
7. **Assumptions** (`chain.md` § 7). List every assumption the root cause and the fix
   rest on before validating any. Each gets **How validated** and **Result**. The fix may
   rest only on confirmed ones.
8. **Propose fixes.** Read `references/fix.md` now. Write the smallest symptom fix and the
   root-cause fix with sibling repairs as two separate proposals, and recommend one.
9. **Counterfactual.** Walk the recommended fix through the captured failure. Record
   **confirmed**, **confirmed with survivors**, or **unconfirmed**. Unconfirmed means the
   RCA is not done.
10. **Prevent the class.** Propose a test that would have caught it, and a guardrail that
    makes the class impossible or loud. A test for this exact bug is the floor.
11. **Report.** Read `../../assets/writing.md` now. Write the report per `fix.md` § 11.
    The headline is at most three sentences, and the recommended fix is one of them. Run
    `<plugin root>/scripts/prose-lint.py` on it and fix every finding.

## Definition of done

Each item is answerable with evidence. One you cannot tick honestly sends you back to the
step that produces it.

- [ ] Failure captured with scope and the working-tree baseline. A repro or trace exists,
  or the RCA is paused for instrumentation, not faked.
- [ ] The timeline names the responsible changes with commits, deploys, or config cited.
- [ ] Every chain link has Answer and Evidence. Nothing below an `UNVERIFIED` link is
  treated as proven.
- [ ] Symptom, proximate, and root cause labelled. The root's falsifier is run or surfaced.
  Siblings listed, or their absence justified.
- [ ] Assumptions listed with How validated and Result. The recommended fix rests on no
  `UNVERIFIED` one.
- [ ] Two fix proposals with a recommendation. The counterfactual is not unconfirmed.
- [ ] Prevention proposed: at least a test, ideally a guardrail or a doc.
- [ ] The report passes `prose-lint.py`. Open questions surfaced. No finding names a
  person instead of a system.
- [ ] The tree is restored to the step-1 baseline. Nothing pushed, published, or sent
  without approval obtained during this investigation.

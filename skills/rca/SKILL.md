---
name: rca
description: Conduct a root-cause analysis on a bug, incident, or regression — reproduce the failure, reconstruct the timeline, run a 5-whys chain, distinguish symptom from proximate cause from root cause, sweep for siblings, and propose a fix that addresses the cause (not the symptom). Use when the user says "/rca", "root cause", "5 whys", "why is this failing", "investigate this regression", or after any failure the team wants to learn from rather than just patch.
---

# RCA: failure-first investigation

The point is not to fix a bug. The point is to understand why it happened. The fix must
kill the cause, not the symptom, and catch the class next time, not the instance. `/blueprint` plans a change you want. `/rca` investigates a failure you did not.

Invoke it for regressions, incidents, and post-mortems. Invoke it for a first-pass fix the
user finds suspicious, or any failure the team would otherwise pay for again. Do not invoke it for
trivial bugs with obvious causes, or for future failures you are designing around. That is
`/blueprint`.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it. Read each
file at the step named.

| File | Read at | Holds |
|---|---|---|
| `references/chain.md` | step 3 | the 5-whys chain with evidence per link, cause classification and falsification, the assumption list |
| `references/fix.md` | step 6 | symptom fix against root-cause fix, the counterfactual, prevention, the report structure |
| `../../assets/writing.md` | step 8, before writing the report | the writing rules for every text a person reads |
| `references/rationalizations.md` | when tempted to skip a step | why each shortcut fails |

## Principles

- **Repro first.** A bug you cannot trigger is a story. Until you reproduce it or read a
  trace of it firing, every theory is unfalsifiable.
- **The symptom is evidence of the cause, not the cause.** Fixing it holds until the next
  adjacent failure.
- **Ask why mechanically.** Each answer is the next question's subject. Stop at the level
  whose fix prevents siblings. A root cause with no siblings usually means you stopped at a
  proximate one.
- **Fix the cause, prevent the class.** RCA owes the user both answers.

## Side-effect rules

Reversibility is judged by observable effects, not artifact state. Undoing the artifact
does not un-notify anyone or un-run anything.

- **Irreversible** actions (publish, deploy, reset a DB, reboot, send a message) need
  explicit approval obtained during this investigation.
- **Visible to others** actions (push to a PR, comment, trigger CI, anything a person or
  system observes) need approval before the act. Disclosure after is not consent.
- **Reversible and local** actions (working-tree edits, probe scripts, local branches,
  canaries) are allowed. Revert them by default and disclose them in the report.

Prefer an isolated workspace (`git worktree add ...`) unless the repro needs the live
environment. That is a stated finding, not a silent default. Consent from an earlier task
does not carry over. If an experiment must cross the line, ask now.

## Workflow

1. **Capture the failure.** Record the symptom with logs quoted verbatim, the scope (who,
   since when, how often), expected against actual, and the reproduction steps. Record the
   working-tree baseline (branch, `HEAD`, `git status --porcelain`) that the end check
   restores to. The user's own uncommitted work is part of it. If the symptom is ambiguous,
   ask. RCA on a fuzzy symptom is fishing.
1.5. **Repro or trace.** Get a deterministic repro (steps, failing test, script) or a
   captured trace with enough context. With neither, the finding is "we need
   instrumentation". Surface it before continuing.
2. **Timeline.** Run `git log --since=<known-good> --until=<known-bad> -- <area>`. Add
   deploys, dependency bumps, infra and flag changes, migrations, and traffic shifts. If
   the bug predates every change, look for what is new in the inputs, not the code.
3. **5-whys chain.** Read `references/chain.md` now. Write a numbered list where every
   link carries **Answer** and **Evidence** (`file:line`, query result, log excerpt, commit
   SHA). One mechanical step per why. A link without evidence is marked `UNVERIFIED` and
   supports nothing below it. Branch when there are parallel causes.
4. **Classify and falsify.** Label the symptom, the proximate cause, and the root cause.
   Then try to disprove the root. What would you see if it were wrong? What second
   mechanism produces the same symptom? What is the cheapest disconfirming experiment? Run
   it, or report the unrun falsifier as a limitation.
5. **Sibling sweep.** Look for other call sites, entry points that bypass the same
   safeguard, tenants or channels that share the assumption, and data already corrupted.
   Use `grep -rn` and `git log -S`. Report siblings alongside the primary.
5.5. **Assumptions** (`chain.md` § 5.5). List every assumption the root cause and the fix
   rest on before validating. Each gets **How validated** and **Result**. The fix may rest
   only on confirmed ones. An `UNVERIFIED` assumption is an open question, not a
   foundation.
6. **Propose fixes.** Read `references/fix.md` now. Write two separate proposals: the
   smallest symptom fix, and the root-cause fix with sibling repairs. Each names files,
   approach, tests, blast radius, and rollback. Recommend one and say why.
6.5. **Counterfactual.** Walk the recommended fix through the captured failure. Would the
   repro still fire? Which link does it break? Record **confirmed**, **confirmed with
   survivors** (list them), or **unconfirmed**. Unconfirmed means the RCA is not done.
7. **Prevent the class.** Propose a test that would have caught it. Propose a guardrail
   (type, lint, assertion, constraint, alert) that makes the class impossible or loud. Add a
   doc update where a spec or invariant missed the rule. "A test for this exact bug" is the
   floor.
8. **Report.** Read `../../assets/writing.md` now. Write the report per `fix.md` § 8:
   headline, symptom and scope, the chain with citations, cause labels, siblings, fix
   proposals, prevention, open questions. Run `<plugin root>/scripts/prose-lint.py` on it
   and fix every finding in the text before you deliver it.

## Definition of done

Each item is answerable with evidence, not a vibe. One you cannot tick honestly sends you
back to the step that produces it.

- [ ] Failure captured with scope, time window, and working-tree baseline. Repro or trace
  established, or the RCA is paused for instrumentation, not faked.
- [ ] Timeline names the responsible changes with commits, deploys, or config flips cited.
- [ ] Every chain link has Answer and Evidence. `UNVERIFIED` links are flagged and nothing
  below one is treated as proven.
- [ ] Symptom, proximate, and root cause labelled. The root's falsifier written down or its
  absence surfaced. Siblings listed or their absence justified.
- [ ] Assumptions listed with How validated and Result. The recommended fix depends on no
  `UNVERIFIED` one.
- [ ] Two fix proposals with a recommendation. Counterfactual recorded, and not unconfirmed.
- [ ] Prevention proposed: at minimum a test, ideally a guardrail or doc.
- [ ] Report delivered as an inverted pyramid and passes `prose-lint.py`. Open questions
  surfaced, none silently answered. No "human error" conclusion, no finding that names a
  person rather than a system.
- [ ] No trace left: tree restored to the step-1 baseline and shown. Nothing pushed,
  published, or sent without approval obtained during this investigation.

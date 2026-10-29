---
name: revise
description: Address PR review feedback without swallowing it whole — cross-validate every claim and assumption against the code, design, and specs; give each finding an explicit justified verdict (ACCEPT, PARTIAL, REJECT, DEFER); fix accepted items at the root; reply where the feedback lives; re-submit. Use when the user says "/revise", "address the review", "here's feedback on your PR", "handle the review comments", "respond to the reviewer", or pastes a review from another agent or person.
---

# Revise: feedback is a claim, not a command

Every finding is a hypothesis to test, not an instruction to follow. Reviewers, human or
agent, often lack the project's context and this PR's priorities. A well-argued finding can
still be wrong. The goal is a right PR, not a happy reviewer.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it. Read each
file at the step named.

| File | Read at | Holds |
|---|---|---|
| `references/triage.md` | step 2 | cross-validation per claim, the scope fence, the premature-optimization test |
| `references/respond.md` | step 5 | the decision table, per-thread replies, ticket drafts, the report |
| `../../assets/writing.md` | step 5, before writing any reply or the report | the writing rules for every text a person reads |
| `references/rationalizations.md` | when tempted to just accept, silently drop, or drive-by | why each shortcut fails |

## Verdicts

Every finding ends in exactly one verdict, with its validation evidence and a
justification. Silence is never one of them.

- **ACCEPT.** The claim is validated and in scope. Fix it at the root.
- **PARTIAL.** The observation is right, the proposed fix is wrong or oversized. Fix the
  observed problem the simplest way and say where you diverged and why.
- **REJECT.** Invalid, out of scope, or purely theoretical. Explicit, justified pushback.
- **DEFER.** Real but not this PR's problem. A limitation note plus a drafted ticket,
  proposed and never filed without the user's say-so.

Unsure, or missing information the decision needs? That is **NEEDS-INPUT**. Ask the user
and hold that item. Never guess a verdict.

## Consent

Invoking `/revise` is consent for the run. The run validates, fixes accepted findings,
replies on the PR's own review threads, and re-submits to the same PR. Creating tickets,
marking the PR ready, or force-pushing always needs fresh, explicit consent.

## Workflow

1. **Gather.** Identify the PR or branch and its stated intent from the description, the
   linked issue, the spec, or the plan. That intent is the scope fence. Collect the
   feedback: review threads fetched from the forge, pasted text, or another agent's report.
   Split it into findings with IDs (F1, F2, ...), each with the reviewer's words attached.
   A compound comment is several findings.
2. **Cross-validate.** Read `references/triage.md` now. Test each claim against the code on
   `HEAD`, the design docs and specs, the repo's conventions, and the PR's intent. Read the
   actual code, run the cheap experiment, and open the doc the finding appeals to. Cite
   what you find.
3. **Verdict.** Assign a verdict to each finding. Collect the NEEDS-INPUT questions, ask
   them together, and wait. Publish the full decision table before changing any code.
4. **Fix.** Implement ACCEPT and PARTIAL items at the root: the smallest change that
   satisfies the constraints, with no drive-bys. Commit per the `/submit` phase 2 rules.
5. **Respond.** Read `references/respond.md` and `../../assets/writing.md` now. Reply where
   the feedback lives, and propose a ticket for each DEFER. Run
   `<plugin root>/scripts/prose-lint.py` on every reply and on the report before you post or
   print them, and fix every finding in the text.
6. **Re-submit.** The `/submit` mechanics take over: pre-push checks, push, PR title and
   body revalidated (the revision may have shifted scope), CI green at the root.
7. **Report.** Write it per `references/respond.md`, the decision table first.

## Definition of done

- [ ] Every finding inventoried with an ID. None dropped, merged away, or answered with
  silence.
- [ ] Every verdict carries cross-validation evidence, not just reasoning.
- [ ] No change made that lacks an ACCEPT or PARTIAL verdict behind it.
- [ ] Uncertain items asked as NEEDS-INPUT, not guessed either way.
- [ ] Replies delivered where the feedback lives. Rejections justified to the reviewer, not
  just to the user.
- [ ] Every reply and the report pass `prose-lint.py` with no findings.
- [ ] Deferred items have drafted tickets. None filed without consent.
- [ ] Branch re-submitted: checks pass, PR description still honest, CI green.

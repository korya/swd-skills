---
name: revise
description: Address PR review feedback without swallowing it whole — cross-validate every claim and assumption against the code, design, and specs; give each finding an explicit justified verdict (ACCEPT, PARTIAL, REJECT, DEFER); fix accepted items at the root; reply where the feedback lives; re-submit. Use when the user says "/revise", "address the review", "here's feedback on your PR", "handle the review comments", "respond to the reviewer", or pastes a review from another agent or person.
---

# Revise: feedback is a claim, not a command

The point is not to make the reviewer happy. The point is to make the PR right. That means
treating every finding as a hypothesis to test, not an instruction to follow. Reviewers,
human or agent, often have incomplete knowledge of the project and of this PR's priorities.
A well-argued finding can still be wrong. Accepting it because it sounds right is how scope
creep and premature optimization get merged.

`/examine` produces review findings. `/revise` decides what they are worth and acts on
exactly that.

## Required references

Paths are relative to this file. `<plugin root>` is two directories above it. Read each
file at the step named.

| File | Read at | Holds |
|---|---|---|
| `references/triage.md` | step 2 | cross-validation per claim, the scope fence, the premature-optimization test, verdict rules |
| `references/respond.md` | step 5 | the decision table, per-thread replies, justification style, ticket drafts |
| `../../assets/writing.md` | step 5, before writing any reply or the report | the writing rules for every text a person reads |
| `references/rationalizations.md` | when tempted to just accept, silently drop, or drive-by | why each shortcut fails |

## Verdicts

Every finding ends in exactly one verdict, always with the validation evidence attached:

- **ACCEPT.** The claim is validated and in scope. Fix it at the root.
- **PARTIAL.** The observation is right, the proposed fix is wrong or oversized. Fix the
  observed problem the simplest way and say where you diverged and why.
- **REJECT.** Invalid, out of scope, or purely theoretical. Explicit, justified pushback.
- **DEFER.** Real but not this PR's problem. A limitation note plus a drafted ticket,
  proposed and never filed without the user's say-so.

Unsure, or missing information the decision needs? That is **NEEDS-INPUT**. Ask the user
explicitly and hold that item. Never guess a verdict. Never silently drop the finding.

## Principles

- **Cross-validate everything.** Check every claim and every assumption inside a finding
  against the code on `HEAD`, the design and architecture docs, the product specs, and the
  repo's conventions. Cite the evidence. Eloquence is not evidence.
- **The burden of proof is on the change.** Suppose the current code violates no guideline,
  no security or architectural constraint, and no spec. Then "it would be nicer" is not a
  reason to touch it. The simplest solution that satisfies all constraints stays.
- **No scope creep, no premature optimization, no speculative guards.** The PR's stated
  intent is the fence. Theoretical performance and "while we're here" work are deferred or
  rejected, not done.
- **Silence is not a response.** Every finding gets a verdict and a justification. That
  includes, and especially, the rejected ones.
- **Fix at the root.** An accepted finding gets a real fix, not the cheapest patch that
  quiets the reviewer.

## Consent

Invoking `/revise` is consent for the run. The run validates, fixes accepted findings,
replies on the PR's own review threads, and re-submits to the same PR. Creating tickets, marking the
PR ready, or force-pushing always needs fresh, explicit consent.

## Workflow

1. **Gather.** Identify the PR or branch and its stated intent from the description, the
   linked issue, the spec, or the plan. That intent is the scope fence. Collect the
   feedback: review threads fetched from the forge, pasted text, or another agent's report.
   Split it into individually judgeable findings with IDs (F1, F2, ...). A compound comment
   is several findings. Nothing gets lost between here and the table.
2. **Cross-validate.** Read `references/triage.md` now. For each finding, test its claims
   against reality: read the actual code, run the cheap experiment, check the spec or doc it
   appeals to. Classify what the reviewer got right, what they missed for lack of context,
   and what the fix they propose would cost.
3. **Verdict.** Assign ACCEPT, PARTIAL, REJECT, or DEFER per the rules. Route genuine
   uncertainty to NEEDS-INPUT and ask the user now. Collect all such questions and ask them
   together, then wait. Publish the full decision table before changing any code.
4. **Fix.** Implement ACCEPT and PARTIAL items at the root: the smallest change that
   satisfies the constraints, with no drive-bys riding along. Commit per the repo's
   conventions. The `/submit` phase 2 rules apply.
5. **Respond.** Read `references/respond.md` and `../../assets/writing.md` now. Reply where
   the feedback lives. Forge review threads get a per-thread reply: what changed and the
   commit, or the justified rejection. Pasted feedback gets the decision table in the
   session report. DEFER items get their drafted tickets, proposed, not created. Run
   `<plugin root>/scripts/prose-lint.py` on every reply and on the report before you post or
   print them, and fix every finding in the text.
6. **Re-submit.** The `/submit` mechanics take over: pre-push checks, push, PR title and
   body revalidated (the revision may have shifted scope), CI green at the root.
7. **Report.** The decision table first, then the open NEEDS-INPUT questions, the ticket
   drafts, and what changed in the PR.

## Definition of done

- [ ] Every finding inventoried with an ID. None dropped, merged away, or answered with
  silence.
- [ ] Every verdict carries cross-validation evidence, not just reasoning.
- [ ] No change made that lacks an ACCEPT or PARTIAL verdict behind it. No scope creep, no
  speculative optimization.
- [ ] Uncertain items asked as NEEDS-INPUT, not guessed either way.
- [ ] Replies delivered where the feedback lives. Rejections justified to the reviewer, not
  just to the user.
- [ ] Every reply and the report pass `prose-lint.py` with no findings.
- [ ] Deferred items have drafted tickets. None filed without consent.
- [ ] Branch re-submitted: checks pass, PR description still honest, CI green.

## Related skills

`/examine` produces the kind of review this skill answers. `/submit` re-ships the revised
branch. `/rca` is for a finding that reveals a deeper failure worth investigating.

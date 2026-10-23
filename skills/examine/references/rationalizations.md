# Anti-rationalization table and anti-patterns

The full table. Read this file when you catch yourself skipping a step. If your reason is
below, do the step.

| Rationalization | Why it fails here |
|---|---|
| "The PR description seems clear enough; I'll just review the diff." | Reading the diff first anchors you to the author's choices instead of the problem. Read the description first, derive what should have happened, then compare. |
| "There's no description but the change is obvious." | Obvious to whom? You are filling in the author's intent silently. Every assumption you make is a finding you swallowed instead of surfaced. Flag the missing description. |
| "Tests pass, so the change must be correct." | Tests cover what the author thought about. The interesting bugs are in what they did not. Read the regression surface, the adjacent unchanged code. |
| "I don't need to read the project docs; the diff explains itself." | Architecture and invariants are not derivable from the diff. Without them you review against generic best practices, which are usually wrong for this project. |
| "This dependency is from a big company, skip the audit." | Typosquatting attacks impersonate big-company packages on purpose. The audit is fast. Skipping it is the actual risk. |
| "The author says they tested manually, that's good enough." | "Tested manually" without specific steps and a specific environment is unverifiable. Either it is a finding ("how was this tested?") or it is risk you now carry. |
| "Load-bearing assumption looks plausible; ship it." | Plausible is not verified. You identified it as load-bearing because getting it wrong breaks the PR. Read the docs, measure, confirm. |
| "The diff is right here; sketching my own approach first is ceremony." | Reading the diff first makes the author's choices your baseline for normal. You will verify their solution instead of judging it. The sketch costs minutes and is the only thing that makes over-engineering visible. |
| "The author surely had a reason for the extra complexity." | Then find it: ticket, docs, git history, adjacent code. If it exists, cite it under Verified. If a genuine hunt comes up empty, it is an approach-level question for the author. Silently assuming a justification swallows the finding. |
| "My simpler approach is obviously better. File it as an Issue." | Not until you have walked it against every stated constraint and said so. A "simpler" proposal that a documented constraint rules out costs the review its credibility. Simplicity findings without citable cost are Suggestions, not Issues. |
| "The approach looks wrong, but I'll do the line review and mention it at the end." | Burying an approach disagreement under line findings signals "fix the nits and merge". The disagreement is the headline. Every line finding below it is provisional. |
| "Reversibility is the deployer's problem, not the reviewer's." | A merged PR is one CI run away from prod. The reviewer is the last filter before irreversible damage. If you do not ask the rollback question, no one will. |
| "I'll just post all findings to the PR and let the author triage." | A 40-comment review trains the author to skim. Sort by severity. Lead with what is critical. Drop or bury the lows. |
| "Everything I noticed is at least High." | Probably not. That pattern is severity inflation. If three of the four buckets are empty, recalibrate. Critical is for "this breaks prod or violates a hard constraint". High is for "concrete plausible failure mode". Otherwise, demote. |
| "I don't have time to find anything that was done well." | "Done well" is part of the review, not garnish. It calibrates the author's signal-to-noise and keeps the review from reading as pure nitpicking. Spend the two minutes. |
| "This 'consider X' note is really a Low issue." | If it is a problem with the present code, it is an issue. If it is a constructive alternative or a "have you considered" prompt, it is a Suggestion. Mixing them either inflates the issue list or hides real findings under polite framing. |
| "There's no test for the stated risk. I'll just note it as a Gap." | A missing test for a stated risk is a finding the author has to address. That is an Issue with a severity, not a Gap. Leaving it under Gaps softens it into something the author can skim past. |
| "This is obviously a privacy / security / conventions violation, no need to cite the doc." | "Obviously" is exactly the move that lets training-data priors masquerade as project rules. The citation separates "this PR contradicts a rule the project has" from "this looks wrong to me". Find the rule, or downgrade the finding to a Suggestion. |
| "I'll just skim the invariants, security, privacy, and testing docs. I get the gist." | Excerpts work for orientation, not for compliance checks. Findings cite these by section. If you only skimmed, you will miss the rule the PR violates or invent a rule that is not there. Read in full. |
| "I have inline doubts but no smoking gun. Skip them." | Quiet doubts become loud bugs. List them as questions in the report and let the author answer. Silent doubts are findings you decided not to surface. |
| "Posting to the PR is faster than copying the review." | The user did not ask you to post it. PR comments are public and durable. Let the user decide what is visible. |
| "The fix is one line. I'll just push it to the author's branch." | That mutates the subject under review and publishes the mutation: CI runs, watchers get notified, the author's work changes under them. A review's output is findings, not commits. Put the fix in the report. The author decides. |
| "I'll trigger CI or push a probe commit to test my theory about the pipeline." | The experiment is visible to the author and every watcher, and it alters the PR under review. Exhaust read-only evidence first: prior run logs, `gh api`, a local repro. If the theory needs a live trigger, that is a question for the user, not a judgment call. |
| "This candidate is speculative. I'll quietly drop it." | Dropping half-believed candidates bypasses the verify stage. The verifier decides, not the finder. Record it with its failure scenario and pass it through. |
| "The verifier should refute anything that depends on runtime state." | PLAUSIBLE by default. Races, cold caches, and rare but reachable error paths are realistic production states. REFUTED requires proof constructible from the code: a quoted guard, type, or invariant. |

## Anti-patterns

- **Reviewing the diff without reading the description.** You review the implementation.
  You do not review whether it solves the problem.
- **Reviewing against generic best practices.** The project has its own rules. Review
  against those.
- **"LGTM" reviews on non-trivial changes.** A non-trivial change owes the author at least a
  Verified and Not reviewed split, so they know what was audited.
- **Burying critical findings under low-severity noise.** Sort by severity. Always.
- **Pure-negative reviews.** A review with no "what was done well" trains the author to dread
  review. Find at least one concrete thing per PR worth keeping. If you cannot, that is a
  finding about the PR, not an absence of effort.
- **Severity inflation.** If every issue is Critical or High, the severity scheme stops
  carrying signal. Reserve the top tiers. Demote what does not meet the bar.
- **Posting to the PR by default.** Terminal first. The user decides what becomes public.
- **Treating CI green as the end of testing.** CI runs the tests the author wrote. The review
  covers the tests they did not.
- **Approving complexity by default.** Verifying that complicated code is correct is not the
  same as verifying it is necessary. A review that never asks "what would the obvious
  solution look like?" rubber-stamps over-engineering. Over-engineered patterns spread,
  because the next PR copies them.

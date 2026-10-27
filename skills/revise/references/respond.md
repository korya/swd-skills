# Responding: the table, the threads, the tickets

Loaded from `SKILL.md` step 5. A verdict that never reaches the reviewer is half done. The
response is where rejections earn their legitimacy and accepted fixes get traced. Every
reply and the report follow `../../assets/writing.md` and pass `prose-lint.py` before they
go out.

## The decision table

Published before code changes (step 3) and repeated in the final report:

```markdown
| ID | Finding (reviewer's words, abridged) | Verdict | Evidence and justification |
|---|---|---|---|
| F1 | "handler swallows the timeout error" | ACCEPT | confirmed at api/poll.ts:88; fixed in <sha> |
| F2 | "switch the module to the Result pattern" | REJECT | violates nothing (checked conventions, security docs); rewrite exceeds PR intent |
| F3 | "N+1 query will hurt at scale" | DEFER | real above ~10k rows (measured); current max 400; ticket drafted |
| F4 | "rename ambiguous `process()`" | PARTIAL | ambiguity confirmed; renamed locally instead of the proposed repo-wide sweep |
```

Counts up front: `2 ACCEPT, 1 PARTIAL, 3 REJECT, 1 DEFER, 1 NEEDS-INPUT`.

## Reply where the feedback lives

Feedback that arrived as forge review threads is answered on those threads. The reviewer
should not have to find a session report to learn what happened to their comment. Per
thread, one reply:

- **ACCEPT or PARTIAL.** What changed and the commit that changed it. For PARTIAL, one
  sentence on where and why the fix diverges from the proposal.
- **REJECT.** The justification with its evidence, addressed to the argument, not the
  arguer. Quote the claim. Show what the code, spec, or measurement says. Respectful and
  specific. "Won't fix" with no reasoning is silence wearing a costume.
- **DEFER.** The acknowledgment, why not this PR, and the proposed ticket's title.

Fetch and reply through the forge's CLI. On GitHub, `gh api` reaches review-comment threads
and `gh pr comment` posts the PR-level summary. Feedback that arrived as pasted text or
another agent's report is answered in the session report only. Never post to a PR the
feedback did not come from.

## Ticket drafts for DEFER

Each DEFER produces a ready-to-file draft in the report. The draft has a title and a
two-paragraph body: the finding, the evidence for its reality, and why it was deferred. It
ends with a pointer back to the PR and thread. **Proposed, never filed.** Creating issues needs the user's explicit say-so, and
the reply on the thread says "proposed", not "filed", until then.

## The report

An inverted pyramid. Counts and the table first. Then the open NEEDS-INPUT questions, the
ones blocking a verdict. Then the ticket drafts, the list of commits made, and the
re-submission status from the `/submit` mechanics: checks, PR revalidation, CI. A reader who
stops after the table knows what happened to every finding.

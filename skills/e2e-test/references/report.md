# The report: statuses, evidence, formats

Loaded from `SKILL.md` step 2, so you log evidence while testing, and again at step 5.
The report must let someone who was not there reproduce every failure and fix it without
re-testing first.

## The three statuses

Every case ends in exactly one. There is no SKIPPED, no PARTIAL, no "mostly works".

- **PASS.** The expected outcome was observed at the surface, this run. Not inferred from
  code, not remembered from an earlier session.
- **FAILURE.** The product misbehaved: wrong result, wrong rendering, unusable flow,
  misleading error. It is a FAILURE even if a fix looks trivial.
- **BLOCKED.** The case could not be executed: environment down, a prerequisite case
  failed, missing fixture or credentials, mutation not confirmed. Name what unblocks it. A
  case that errored for a reason you suspect is environmental is BLOCKED, never PASS.

## Per-case details, for every non-PASS

- **What was done.** Steps a stranger can replay, from scratch.
- **Expected against observed.** Evidence pasted from the evidence log. The exact error
  text. A screenshot for anything visual. The command and its output for a CLI. The
  request and response for an API.
- **Most likely cause.** Logs, stack traces, and code may be read and cited here. Label it
  as likelihood, not certainty. Diagnosis explains a verdict. It never changes one.

The output you quote must come from exactly the steps you show. When you trim the steps
for the reader, run the trimmed steps on fresh state and quote that run. Output you
expected but did not see goes under Expected, never in an evidence block. Give the path
of the evidence log in the report, so a reader can check any quote.

## Depth

Set it at step 2 from the invocation's wording, and say which you chose. Comprehensive
when the wording says "comprehensive", "thorough", "from scratch", or "next stop is prod",
or the run gates a release. Lean for a quick or narrow ask, such as "re-test the login
flow". When it is ambiguous, choose comprehensive.

## Lean format

1. **Headline verdict.** One sentence with counts and a go or no-go read: "12/15 PASS, 2
   FAILURE, 1 BLOCKED. The failures corrupt saved filters, so it is not ready for prod."
2. **Case table.** `# | Case | Spec/ref | Status`, in list order.
3. **Non-PASS details.** As above, one block per case.

## Comprehensive format

The lean report, then:

4. **Missing or untested cases.** Identified but not run, each with why: out of scope,
   blocked, no fixture.
5. **Issues found.** Numbered, ordered by severity, deduplicated across cases. One bug that
   fails three cases is one issue with three references.
6. **UX gaps.** Friction a user would feel, and things the implementation did not think of
   that would clearly improve the experience.
7. **Improvements worth doing.** Not bugs, but still worth a human's eyes.
8. **Leftover artifacts.** Entities created through the surface during testing, with names
   or IDs.

Findings only. No journal of the testing session, no praise padding. Severity and
evidence decide how many words a finding gets.

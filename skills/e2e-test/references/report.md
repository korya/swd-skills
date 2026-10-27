# The report: statuses, evidence, formats

Loaded from `SKILL.md` step 5, and skimmed at step 2 so evidence is captured while testing,
not reconstructed after. The report is the run's only deliverable. It must let someone who
was not there reproduce every failure and fix it without re-testing first. Every sentence
follows `../../assets/writing.md`, and the file passes `prose-lint.py` before delivery.

## The three statuses

Every case ends in exactly one. There is no SKIPPED, no PARTIAL, no "mostly works".

- **PASS.** The expected outcome was observed at the surface, this run. Not inferred from
  code, not remembered from an earlier session, not "the API returned 200 so the page must
  render".
- **FAILURE.** The product misbehaved: wrong result, wrong rendering, unusable flow,
  misleading error. The product is at fault.
- **BLOCKED.** The case could not be executed: environment down, a prerequisite case
  failed, missing fixture or credentials, mutation not confirmed for a non-dev
  environment. The run is at fault, not yet the product. Name what unblocks it.

Honesty at the boundary. A case that errored for a reason you suspect is environmental is
BLOCKED with your reasoning, never PASS on the benefit of the doubt. A case whose outcome
you observed but which behaved wrongly is FAILURE even if a fix looks trivial.

## Per-case details, for every non-PASS

- **What was done.** Steps a stranger can replay, from scratch.
- **Expected against observed.** Evidence verbatim. The exact error text. A screenshot for
  anything visual. The command and its output for a CLI. The request and response for an
  API.
- **Most likely cause.** The diagnosis. Here logs, stack traces, and code may be read and
  cited. Label it as likelihood, not certainty. Diagnosis explains a verdict. It never
  changes one.

## Lean format

1. **Headline verdict.** One sentence with counts and a go or no-go read: "12/15 PASS, 2
   FAILURE, 1 BLOCKED. The failures corrupt saved filters, so it is not ready for prod."
2. **Case table.** `# | Case | Spec/ref | Status`, in list order.
3. **Non-PASS details.** As above, one block per case.

## Comprehensive format

The lean report, then:

4. **Missing or untested cases.** Identified but not run, each with why: out of scope,
   blocked, no fixture. This is where deliberate omissions live instead of vanishing.
5. **Issues found.** Numbered, ordered by severity, deduplicated across cases. One bug that
   fails three cases is one issue with three references.
6. **UX gaps.** Friction and inconveniences a user would feel, and things the
   implementation did not think of that would clearly improve the experience.
7. **Improvements worth doing.** Not bugs, but still worth a human's eyes.
8. **Leftover artifacts.** Entities created through the surface during testing, kept on
   purpose because they reproduce findings, with names or IDs.

## Rules

- Inverted pyramid. The reader who stops after the headline still knows the verdict. Each
  section's first line carries its gist.
- Findings only. No journal of the testing session, no praise padding. Concise but
  complete: severity and evidence decide how many words a finding gets.
- The report changes nothing. No fixes, no fix commits, no "I went ahead and...". End at
  the report.

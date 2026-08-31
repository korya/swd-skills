# The report: statuses, evidence, formats

Loaded from `SKILL.md` step 5 (skimmed at step 2 so evidence is captured while testing,
not reconstructed after). The report is the run's only deliverable — it must let someone
who wasn't there reproduce every failure and fix it without re-testing first.

## The three statuses

Every case ends in exactly one. There is no SKIPPED, no PARTIAL, no "mostly works".

- **PASS** — the expected outcome was observed at the surface, this run. Not inferred
  from code, not remembered from an earlier session, not "the API returned 200 so the
  page must render".
- **FAILURE** — the product misbehaved: wrong result, wrong rendering, unusable flow,
  misleading error. The product is at fault.
- **BLOCKED** — the case could not be executed: environment down, a prerequisite case
  failed, missing fixture or credentials, mutation not confirmed for a non-dev
  environment. The run is at fault, not (yet) the product. Name what unblocks it.

Honesty at the boundary: a case that errored for a reason you *suspect* is environmental
is BLOCKED with your reasoning — never PASS on the benefit of the doubt. A case whose
outcome you observed but which behaved wrongly is FAILURE even if a fix looks trivial.

## Per-case details (every non-PASS)

- **What was done** — steps a stranger can replay, from scratch.
- **Expected vs observed** — evidence verbatim: exact error text, a screenshot for
  anything visual, the command and its output for a CLI, the request and response for an
  API.
- **Most-likely cause** — the diagnosis. Here logs, stack traces, and code may be read
  and cited; label it as likelihood, not certainty. Diagnosis explains a verdict; it
  never changes one.

## Lean format

1. **Headline verdict** — one sentence with counts and a go/no-go read:
   *"12/15 PASS, 2 FAILURE, 1 BLOCKED — the failures corrupt saved filters; not ready
   for prod."*
2. **Case table** — `# | Case | Spec/ref | Status`, in list order.
3. **Non-PASS details** — as above, one block per case.

## Comprehensive format

The lean report, then:

4. **Missing / untested cases** — identified but not run, each with why (out of scope,
   blocked, no fixture). This is where deliberate omissions live instead of vanishing.
5. **Issues found** — numbered, ordered by severity, deduplicated across cases (one bug
   failing three cases is one issue with three references).
6. **UX gaps** — friction and inconveniences a user would feel; things the
   implementation didn't think of that would clearly improve the experience.
7. **Improvements worth doing** — not bugs; still worth a human's eyes.
8. **Leftover artifacts** — entities created through the surface during testing (kept
   deliberately; they reproduce findings), with names/IDs.

## Rules

- Inverted pyramid: the reader who stops after the headline still knows the verdict; each
  section's first line carries its gist.
- Findings only — no journal of the testing session, no praise padding. Concise but
  complete: severity and evidence decide how many words a finding gets.
- The report changes nothing: no fixes, no fix commits, no "I went ahead and…". End at
  the report.

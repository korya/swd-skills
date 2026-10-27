# Audit axes and the Occam pass

Loaded from `SKILL.md` step 5. Axes 5a to 5d apply to every diff. Axes 5e to 5l apply when
the diff touches what they cover. The Occam pass (step 6) closes the file.

**Citation rule for 5e to 5i.** A finding on architecture, conventions, security, privacy,
or testing cites the project rule it breaks, by file and section. With no project rule, name
the outside standard (OWASP, GDPR) and say there is no project rule. A finding that can cite
neither is at most a Suggestion. An absent doc the diff does not need is one line under Not
reviewed.

## 5a to 5d. Alignment, problem, correctness, completeness

- **5a. Alignment.** Does the code do what the description says? Typical drift: the PR
  claims validation, and the diff adds a validator that nothing calls.
- **5b. Problem solved.** Walk one failure case from the problem statement through the new
  code. Does it now work?
- **5c. Correctness.** Walk these angles. Each can go to a read-only subagent.
  1. **Line plus enclosing function.** Read every hunk, then the whole function around it.
     Bugs on unchanged lines of a touched function are in scope. For each line, ask what
     input, state, or timing makes it wrong. Code copied from an existing pattern deserves
     extra suspicion, because the differences are where bugs live.
  2. **Removed behavior.** For every deleted or replaced line, name the guarantee it gave,
     then find where the new code gives it. If you cannot, that is a candidate.
  3. **Known pitfalls.** The classic traps of the language and framework, wrappers that
     bypass what they wrap, and wasted work on hot paths.
- **5d. Completeness.** For each changed function, find its callers and check whether the
  change breaks any of them: a new precondition, return shape, exception, or ordering. Find
  the sibling call sites the diff should also have changed.

## 5e. Architecture

Does the change respect the documented layering? The common violation is a module boundary
bypassed because it was inconvenient.

## 5f. Conventions

Check against the agent instruction files and guidelines from step 2, not your own taste.
Quote the rule and the line that breaks it.

## 5g. Security

Check that outside input is validated before use. Check that SQL, shell, template, and HTML
output is parameterized or escaped. Check that new endpoints enforce auth at the same layer
as existing ones, and that no secret reaches logs, tests, or error responses.

## 5h. Privacy

Check new personal data against the project policy. Look at fields, logs, and telemetry for
tagging, redaction, retention, tenant filtering, and data residency.

## 5i. Testing and risk coverage

Name the top three ways this change could break production. For each, find the automated or
documented manual test that would catch it. An uncovered named risk is an Issue with a
severity, whether or not the project documents a coverage expectation. Missing tests with no
named risk and no documented expectation are a Suggestion. Check CI results and whether
manual testing names its steps and environment.

## 5j. Load-bearing assumptions

Check each non-obvious claim the change rests on against an outside source. That can be the
library's docs or source, the runtime docs, a measurement, or the target versions. An unverified
load-bearing assumption is the usual cause of "tests passed but prod broke".

## 5k. Reversibility

Ask what happens if this ships and must be rolled back. Destructive migrations, schema
changes old code cannot read, and irreversible external side effects are Critical or High.
Prefer additive steps: add a nullable column, backfill, drop later. Check that a new path can
be turned off without a revert.

## 5l. Dependencies

For each added or bumped dependency, check three things on sight. A suspected typosquat of a
known package name is Critical. A wildcard range or a pin to an unreleased commit is a
finding. So is a known CVE for the version in use. Age or distance from the latest major is
only a reason to look. It becomes an Issue only with evidence such as a CVE, an end-of-life
notice, or a project policy.

## 6. The Occam pass

The audit asks "is it wrong?". This pass asks "is it more than needed?". Look for:

- **Premature optimization.** Caching, pooling, or cleverness with no measured need.
- **Speculative generality.** Abstractions, flags, and extension points for futures nobody
  scheduled. An interface with one implementation.
- **Over-defensive code.** Guards for states the types or call graph already exclude, and
  fallbacks that hide the error. Validation at a trust boundary is required, not
  over-defensive.
- **Reinvention.** An existing utility the change should have used.
- **Band-aids.** A special case at the call site where the shared mechanism should change.
  Name that mechanism.
- **Deletion candidates.** A new module or indirection that could fold into its caller.

A simplification must clear the same evidence bar as any finding. Walk it against the
constraints from steps 1 and 2 and say which you checked. Simpler means fewer concepts and
failure modes, not fewer lines. Over-engineering defaults to a Suggestion. It becomes an
Issue, usually Medium, only with a concrete cost: a new moving part to operate, or a pattern
nearby code will copy.

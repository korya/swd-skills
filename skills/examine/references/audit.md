# Audit axes 5a to 5m and the Occam pass

Loaded from `SKILL.md` step 5. Axes 5a to 5d apply to every diff. Axes 5e to 5m apply when
the diff touches the surface an axis covers. Each of those ends with its citation rule: the
project document a finding on that axis must name. The Occam pass (step 6) closes the file.

## 5a to 5d. Alignment, problem, correctness, completeness

Walk the diff against these axes. Track each axis in the task or plan tool your host
provides, so none is silently dropped.

- **5a. Alignment with the claimed approach.** Does the code do what the description says?
  Common drift: "I added validation", and the diff adds a helper but never calls it.
- **5b. Solves the stated problem under the stated constraints.** Walk a representative
  failure case from the problem statement through the new code. Would it fix it?
- **5c. Correctness, five named angles.** Each angle can go to a read-only search subagent.
  Every issue-shaped observation is recorded as a candidate with a one-line failure scenario.
  A finder that silently drops half-believed candidates bypasses step 7's verification.
  1. **Line plus enclosing function.** Read every hunk line by line, then the whole
     enclosing function. Bugs in unchanged lines of a touched function are in scope, because
     the change re-exposes them or fails to fix them. For each line ask what input, state,
     timing, or platform makes it wrong. Look for off-by-one errors, inverted conditions,
     null or empty dereferences, silent truncation, an error swallowed in a catch, and
     wrong-variable copy-paste. Be especially skeptical of code copied from existing
     patterns. The differences are where bugs live.
  2. **Removed behavior.** For every line the diff deletes or replaces, name the invariant it
     enforced, then find where the new code re-establishes it. If you cannot find it, that is
     a candidate: a dropped guard, a narrowed validation, a deleted test that covered a real
     case.
  3. **Language pitfalls.** The classics of the diff's language and framework. Falsy-zero
     and loose-equality coercion. Mutable default arguments. Late-binding closures and
     captured loop variables. Nil-map writes. Timezone and DST drift. Float equality.
  4. **Wrapper and proxy correctness.** A type that wraps another (cache, proxy, decorator,
     adapter) must route every method through the wrapped instance. It must not go back
     through a registry or global that re-enters the wrapper, and it must forward everything
     callers use.
  5. **Wasted work.** Redundant computation or repeated I/O. Independent operations run
     sequentially. Blocking work added to startup or hot paths. Long-lived objects that
     capture an enclosing scope holding large values.
- **5d. Completeness, the cross-file tracer.** For each changed function, grep for its
  callers and check whether the change breaks any call site. Breakers include a new
  precondition, a changed return shape, a new exception, and an ordering dependency. Check
  callees too. Does a parallel
  change in the same PR make a call unsafe? Sibling call sites the diff should have changed
  count. The regression surface is the unchanged code around the diff.

## 5e. Architecture

Does the change respect the layering in `docs/architecture.md`? The common violation is a
module boundary bypassed because it was inconvenient.

**Cites:** the `docs/architecture.md` section, or other architecture doc, the PR contradicts.
No citation means no project rule was verified.

## 5f. Conventions

Project-specific code style, file layout, dependency rules, test colocation, commit-message
format, UX and UI guidelines. Verify against the rule sources from step 2, the agent
instruction files and `docs/guidelines.md`, not against your priors.

**Cites:** the instruction file or guideline section the PR contradicts, quoting the rule and
the line that breaks it. A finding that cannot be tied to a documented convention is at most
a Suggestion, not an Issue.

## 5g. Security

- **Trust boundaries.** Are inputs from outside (HTTP body, query, headers, uploads,
  webhooks) parsed and validated before use?
- **Injection surfaces.** Are SQL, shell, command, template, and HTML outputs parameterized or
  escaped?
- **AuthN and AuthZ.** Do new endpoints enforce them at the same layer as existing ones?
- **Secrets.** None logged, none in tests, none in error responses.
- **OWASP Top 10** sweep against the affected surface.

**Cites:** the `docs/security.md`, `threat-model.md`, or `SECURITY.md` rule violated. If no
project rule exists for the concern, name the OWASP item or industry-standard rule and say so
in the finding.

## 5h. Data privacy

- New PII in fields, logs, or telemetry: tagged or redacted per project policy?
- Retention: is new data persisted? For how long? Per policy?
- Cross-tenant leakage: does the new query filter by tenant or org?
- Regional and GDPR data-residency rules respected?

**Cites:** the project's privacy or data-handling policy, such as `docs/privacy.md`, by
section. If no policy exists and the diff handles personal data, say so in the finding and
judge against the applicable regulation (GDPR, CCPA) explicitly.

## 5i. Testing

- Tests included? At what level: unit, integration, e2e?
- Do they cover the failure paths, not just the happy path?
- Do they cover regressions in adjacent unchanged code the PR could break?
- Is manual testing described? Specific, with steps and environment, or hand-wavy ("I tested
  it locally")?
- CI: `gh pr checks <N>`. What passed, what failed, what is flaky and what is broken?

**Cites:** the project's testing conventions, such as `docs/testing.md` or the testing
section of an agent instruction file. "Missing tests" without a documented coverage
expectation and without a named production risk (5k) is a Suggestion, not an Issue.

## 5j. Validate load-bearing assumptions independently

For each non-obvious claim the PR rests on, verify against an outside source:

- A new library or API call: read the library's docs or source. Does it behave as the PR
  assumes?
- An edge of language or runtime behavior: confirm with the stdlib docs.
- A performance claim: measure or profile, not vibes.
- A compatibility claim: confirm against the target versions, not the latest.

An unverified load-bearing assumption is the modal source of "tests passed but prod broke".

## 5k. Risk and tested coverage of risk

Name the top three ways this PR could break production. For each, is there a test, automated
or claimed manual, that would catch the failure mode? If not, that is a finding. Not "add a
test someday" but "this risk is currently uncovered". An uncovered named risk is an Issue
with a severity, whether or not the project documents a coverage expectation.

## 5l. Reversibility: what happens if this fires in prod?

- DB migrations: forward-only with data loss, or backward-compatible (add a nullable column,
  backfill, drop later)? Flag any "we'll backfill later" or "drop the old column in the same
  PR" as serious.
- Schema changes: tolerated by old code reading new data, and the reverse?
- Feature flags: can the new path be turned off without a revert?
- External side effects: webhooks fired, queue messages emitted, files written. Irreversible?

Reversibility failures are the most expensive to ship. A PR that cannot be cleanly reverted
carries higher risk by definition. Irreversible side effects are Critical or High.

## 5m. Dependency audit

For each added or bumped dependency (`go.mod`, `package.json`, `requirements.txt`,
`Cargo.toml`, and the like), two tiers apply.

**Findings on sight:**

- **Typosquatting.** Sanity-check the package name (`requets` vs `requests`, `lodahs` vs
  `lodash`). A suspected typosquat is Critical.
- **Unreviewable pins.** A wildcard range (`*`) or a pin to an unreleased commit.
- **Known CVEs.** `npm audit`, `pip-audit`, the language's advisory lookup, or a search for
  "<package> CVE", scoped to the version in use.

**Investigation triggers, not defects:** distance from the latest major, no release in about
two years, a broad-looking semver range. Investigate. File an Issue only with evidence: an
applicable CVE, an upstream EOL or deprecation notice, or a project dependency policy to cite.
A stable library that has not needed a release is not a finding. Upgrading to the latest
major is sometimes the riskier choice.

## 6. The Occam pass: is this more solution than the problem needs?

The audit asks "is it wrong?". This pass asks "is it more than needed?". Walk the diff once
more looking for:

- **Premature optimization.** Caching, pooling, batching, cleverness in a path with no
  demonstrated need. The test: is there a measurement or a stated scale requirement? No
  evidence means a finding.
- **Speculative generality.** Abstractions, flags, and extension points for futures nobody
  scheduled. Interfaces with one implementation. YAGNI.
- **Over-defensive code.** Guards for states the type system or call graph already excludes,
  catch-alls that swallow failures, fallbacks that mask the error they fall back from.
  Defensive code at trust boundaries is the opposite case and is required, see 5g.
- **Reinvention.** Does the repo already have a utility that does this? 5d looks for
  siblings the diff should have changed. This looks for code it should have used.
- **Band-aids.** The inverse failure. A special case layered on shared infrastructure means
  the fix is too shallow, not too elaborate. Prefer generalizing the underlying mechanism.
  Name the mechanism that should have changed.
- **Deletion candidates.** For each new module or indirection, what breaks if it collapses
  into its caller? If the answer is "nothing, it's just tidier", propose the collapse.

Two calibration rules. **A simplification proposal must clear the same evidence bar as any
other finding.** Walk it against the constraints from steps 1 and 2 and state which you
checked. **Less code is not the metric.** Simplicity is the fewest concepts and failure
modes. Explicit parallel branches can beat a "unified" mechanism nobody can modify safely.

**Severity:** over-engineering defaults to a **Suggestion**. Promote to an Issue, usually
Medium, only with concrete, citable cost: a new moving part to operate, or a pattern adjacent
code will copy. Back it with the project's own conventions when you can.

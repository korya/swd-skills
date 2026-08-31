# Audit axes 5e–5m

Loaded from `SKILL.md` step 5 when the diff touches the surface an axis covers. Each axis
ends with its citation rule: what project document a finding on that axis must name.

## 5e. Architecture

Does the change respect the layering in `docs/architecture.md`? Common violation: bypassing a
module boundary because it was inconvenient.

**Cites:** the `docs/architecture.md` section (or other architecture doc) the PR contradicts.
No citation = no project rule was actually verified.

## 5f. Conventions

Project-specific code style, file layout, dependency rules, test colocation, commit-message
format, UX/UI guidelines. Verify against the rule sources from step 2 (agent instruction files
and `docs/guidelines.md`), not against your priors.

**Cites:** the instruction file or guideline section the PR contradicts, quoting the rule and
the line that breaks it. A finding that can't be tied to a documented convention is at most a
Suggestion, not an Issue.

## 5g. Security

- **Trust boundaries:** inputs from outside (HTTP body, query, headers, uploads, webhooks)
  parsed and validated before use?
- **Injection surfaces:** SQL / shell / command / template / XSS parameterized or escaped?
- **AuthN/AuthZ:** new endpoints enforce them at the same layer as existing ones?
- **Secrets:** none logged, none in tests, none in error responses
- **OWASP Top 10** sweep against the affected surface

**Cites:** `docs/security.md` / `threat-model.md` / `SECURITY.md` rule violated. If no
project rule exists for the concern, name the OWASP item or industry-standard rule explicitly
and say so in the finding.

## 5h. Data privacy

- New PII in fields, logs, telemetry — tagged/redacted per project policy?
- Retention — new data persisted? For how long? Per policy?
- Cross-tenant leakage — does the new query filter by tenant/org?
- Regional / GDPR data-residency rules respected?

**Cites:** the project's privacy / data-handling policy (`docs/privacy.md`, similar) by
section. If no policy exists and the diff handles personal data, say so in the finding and
judge against the applicable regulation (GDPR, CCPA, …) explicitly.

## 5i. Testing

- Tests included? At what level — unit / integration / e2e?
- Cover the *failure* paths, not just the happy path?
- Cover regressions in adjacent unchanged code the PR could break?
- Manual testing described? Specific (steps, env) or hand-wavy ("I tested it locally")?
- CI: `gh pr checks <N>` — what passed, what failed, what's flaky vs. broken?

**Cites:** the project's testing conventions (`docs/testing.md`, agent instruction file
testing section, or similar). "Missing tests" without a documented coverage expectation and
without a named production risk (5k) is a Suggestion, not an Issue.

## 5j. Validate load-bearing assumptions independently

For each non-obvious claim the PR rests on, verify against an outside source:

- New library / API call → read the library's docs or source. Does it behave as the PR assumes?
- Edge of language / runtime behavior → confirm with the stdlib docs.
- Performance claim → measure or profile, not vibes.
- Compatibility claim → confirm against the target versions, not the latest.

An unverified load-bearing assumption is the modal source of "tests passed but prod broke."

## 5k. Risk and tested coverage of risk

Name the top 3 ways this PR could break production. For each, is there a test (auto or
claimed manual) that would catch the failure mode? If not, that's a finding — not "add a test
someday," but "this risk is currently uncovered." An uncovered *named* risk is an Issue with a
severity, whether or not the project documents a coverage expectation.

## 5l. Reversibility — what happens if this fires in prod?

- DB migrations: forward-only with data loss, or backward-compatible (add column nullable →
  backfill → drop later)? Flag any "we'll backfill later" or "drop old column in the same PR"
  as serious.
- Schema changes: tolerated by old code reading new data, and vice versa?
- Feature flags: can the new path be turned off without revert?
- External side effects: webhooks fired, queue messages emitted, files written — irreversible?

Reversibility failures are the most expensive to ship. A PR that can't be cleanly reverted
carries higher risk by definition — irreversible side effects are Critical or High.

## 5m. Dependency audit

For each added or bumped dependency (`go.mod`, `package.json`, `requirements.txt`,
`Cargo.toml`, etc.), two tiers:

**Findings on sight:**

- **Typosquatting** — package name sanity check (`requets` vs `requests`, `lodahs` vs
  `lodash`); a suspected typosquat is Critical.
- **Unreviewable pins** — a wildcard range (`*`) or a pin to an unreleased commit.
- **Known CVEs** — `npm audit` / `pip-audit` / language-specific advisory lookup, or search
  "<package> CVE", scoped to the version in use.

**Investigation triggers, not defects:** distance from the latest major, no release in ~2
years, a broad-looking semver range. Investigate; file an Issue only with evidence — an
applicable CVE, an upstream EOL or deprecation notice, or a project dependency policy to
cite. A stable library that hasn't needed a release is not a finding, and upgrading to the
latest major is sometimes the riskier choice.

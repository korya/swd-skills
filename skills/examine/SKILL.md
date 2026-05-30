---
name: examine
description: Review a pull request rigorously — establish the PR's stated intent, audit the diff against the claimed approach, check correctness, completeness, architecture, conventions, security, data privacy, testing, reversibility, and dependency hygiene. Validate load-bearing assumptions against independent sources. Returns a structured report with four signals — what was done well, gaps (what's missing), issues classified as Critical / High / Medium / Low, and suggestions (constructive improvements). Use when the user says "/examine", "examine this PR", "review this PR", "review pr #N", "look over my pull request", "check my PR before merge", or asks for a deep code review beyond surface diff-reading. Heavier than the built-in `/review`; the goal is to surface what would actually break in production, not to summarize the diff.
---

# Examine: production-risk-first PR review

The point of this skill is **not** to produce a "looks good to me" or a paragraph summary of the diff. It is to find what would actually break in production — and to verify the PR's claims rather than trust them.

`/review` is the built-in quick pass. `/examine` is the deep one — for non-trivial changes, real production exposure, or when the user wants a second pair of skeptical eyes before merge.

## When to invoke

- "/examine", "/examine <PR-url-or-number>"
- "Examine this PR" / "review this PR" / "look over my pull request" / "deep review pr #N"
- Pre-merge for any non-trivial change: schema, auth, payments, data migrations, dependency bumps, infra
- After CI green when the user wants signal that CI didn't catch
- Before deploy when the user is on-call and the PR was authored by someone else

Do **not** invoke for: trivial typo fixes, doc-only PRs, or when the user explicitly wants a 30-second sanity check — that's `/review`.

## Operating principles

- **Trust nothing, verify everything.** The PR description is a claim. The diff is a claim. Tests passing is a claim. Verify each against the code, the project docs, and external sources where the assumption is load-bearing.
- **Production-risk first.** Sort findings by what breaks if this ships, not by code style. Lows go last.
- **Review against the project's rules, not generic best practices.** Architecture, invariants, conventions — these are the rules the PR is supposed to comply with. Read them before judging.
- **Four signals, not one.** A useful review tells the author four things: what's working well (so they keep doing it), what's missing (so they know the gaps), what's wrong (so they know what to fix), and what could be better (constructive alternatives that aren't required but would improve the PR). All four carry information; omitting any of them shortchanges the author.
- **Acknowledge good work explicitly.** Looking hard for what was done well is part of the discipline, not optional politeness. It calibrates your tone, prevents "review by nitpicking," and tells the author which patterns to repeat. A review that finds nothing good is almost always a reviewer-fatigue artifact, not a fact about the PR.
- **Be useful, not exhaustive.** A review with 50 lows and 1 buried critical issue is worse than 5 findings sorted by severity. Headline the things that matter.

## Inputs to establish up front

- PR number or URL (gh CLI: `gh pr view <N>`)
- Repo context: AGENTS.md / docs/ / README — note their presence
- CI status: `gh pr checks <N>` — passing, failing, or flaky
- Whether the user wants the review posted to the PR (default: **no**, terminal only)

## Workflow

Many of these steps parallelize. Spawn Explore subagents for the docs sweep, the conventions audit, the security pass, and the dependency audit — you stay in charge of severity calls and the final synthesis.

### 1. Establish intent — what is this PR trying to do?

```bash
gh pr view <N> --json title,body,author,baseRefName,headRefName,changedFiles,additions,deletions,files
```

Extract from the description:

- **Stated problem** — what does the author say is wrong or missing?
- **Stated approach** — how do they claim to fix it?
- **Constraints / non-goals** — what did they explicitly choose not to do?
- **Non-obvious decisions** — anything called out as "I picked X over Y because…"

If the description is missing, empty, or pure boilerplate ("update the foo"), **that is finding #1**. A PR without an intent statement makes the reviewer reverse-engineer the author's goal, which means the reviewer is doing the author's job. Flag it prominently. Then derive intent from the diff yourself, and mark every claim you have to infer as **derived, not stated** so the author sees what the missing description cost.

### 2. Establish context — what is the project's own rulebook?

In parallel with step 1, have an Explore subagent read:

- `AGENTS.md` / `CLAUDE.md` (agent-facing instructions)
- `docs/architecture.md` (boundaries the PR must respect)
- `docs/invariants.md` (rules that must hold)
- `docs/guidelines.md` (conventions — code style, testing, modularization, UX)
- `docs/product-specs/<relevant>` (what the user-visible behavior should be)
- `docs/security.md` / `docs/threat-model.md` / `SECURITY.md` (project-specific threat model and security rules — if present, judge step 3g against these rather than against generic OWASP framing)
- `README` if no `docs/` exists

If none of these exist, note it in the report and review against the implicit conventions visible in surrounding code. Don't fall back to generic best practices — they're usually wrong for the specific project.

### 3. Audit the diff

```bash
gh pr diff <N>
```

Walk the diff against the axes below. Use TaskCreate to track each axis; spawn subagents for the ones that benefit from parallel work (security, conventions, dependencies, docs alignment).

#### 3a. Alignment with the claimed approach
Does the code actually do what the description says? Common drift: the description says "I added validation"; the diff adds a helper but doesn't call it from the relevant endpoint.

#### 3b. Solves the stated (or derived) problem under stated constraints
Walk a representative failure case from the problem statement through the new code. Would it fix it? Are the constraints honored, or quietly violated?

#### 3c. Correctness — bugs and gaps
Read adversarially: off-by-one, null/empty cases, error paths, race conditions, type coercions, silent truncations. Be especially skeptical of code copied from existing patterns — the differences are where bugs live.

#### 3d. Completeness — siblings the diff missed
Search for sibling call sites. If `foo()` was modified for a reason, every caller deserves a look. The regression surface is the *unchanged* code around the diff.

#### 3e. Architecture
Does the change respect the layering in `docs/architecture.md`? Common violation: bypassing a module boundary because it was inconvenient.

#### 3f. Conventions
Project-specific code style, file layout, dependency rules, test colocation, commit-message format, UX/UI guidelines. Verify against the docs, not against your priors.

#### 3g. Security
- **Trust boundaries:** inputs from outside (HTTP body, query, headers, uploads, webhooks) parsed and validated before use?
- **Injection surfaces:** SQL / shell / command / template / XSS parameterized or escaped?
- **AuthN/AuthZ:** new endpoints enforce them at the same layer as existing ones?
- **Secrets:** none logged, none in tests, none in error responses
- **OWASP Top 10** sweep against the affected surface

#### 3h. Data privacy
- New PII in fields, logs, telemetry — tagged/redacted per project policy?
- Retention — new data persisted? For how long? Per policy?
- Cross-tenant leakage — does the new query filter by tenant/org?
- Regional / GDPR data-residency rules respected?

#### 3i. Testing
- Tests included? At what level — unit / integration / e2e?
- Cover the *failure* paths, not just the happy path?
- Cover regressions in adjacent unchanged code the PR could break?
- Manual testing described? Specific (steps, env) or hand-wavy ("I tested it locally")?
- CI: `gh pr checks <N>` — what passed, what failed, what's flaky vs. broken?

#### 3j. Validate load-bearing assumptions independently
For each non-obvious claim the PR rests on, verify against an outside source:

- New library / API call → read the library's docs or source. Does it behave as the PR assumes?
- Edge of language / runtime behavior → confirm with the stdlib docs.
- Performance claim → measure or profile, not vibes.
- Compatibility claim → confirm against the target versions, not the latest.

An unverified load-bearing assumption is the modal source of "tests passed but prod broke."

#### 3k. Risk and tested coverage of risk
Name the top 3 ways this PR could break production. For each, is there a test (auto or claimed manual) that would catch the failure mode? If not, that's a finding — not "add a test someday," but "this risk is currently uncovered."

#### 3l. Reversibility — what happens if this fires in prod?
- DB migrations: forward-only with data loss, or backward-compatible (e.g., add column nullable → backfill → drop later)? Flag any "we'll backfill later" or "drop old column in the same PR" as serious.
- Schema changes: tolerated by old code reading new data, and vice versa?
- Feature flags: can the new path be turned off without revert?
- External side effects: webhooks fired, queue messages emitted, files written — irreversible?

Reversibility failures are the most expensive to ship. A PR that can't be cleanly reverted carries higher risk by definition.

#### 3m. Dependency audit
For each added or bumped dependency (`go.mod`, `package.json`, `requirements.txt`, `Cargo.toml`, etc.):

- **Typosquatting** — package name sanity check (`requets` vs `requests`, `lodahs` vs `lodash`)
- **Major version** — current vs. latest; deprecated majors are findings
- **CVEs** — `npm audit` / `pip-audit` / language-specific advisory lookup; or web-search "<package> CVE"
- **Version range** — overly broad ranges (`*`, `^0.x`) or pinned to unreleased commits
- **Maintenance** — last release within ~2 years; abandoned packages are a finding

### 4. Synthesize — four signals, four severities

The report carries four distinct signals. Mixing them up trains the author to skim:

- **What was done well** — concrete things in this PR worth keeping. Cite `file:line` so it's specific, not flattering. Examples: "good failure-path coverage in `auth_test.go:120-180`", "schema migration is backward-compatible — old readers still parse new rows", "telemetry tagged correctly for cross-region requirements".
- **Gaps** — things *missing* from the PR rather than wrong with it. Examples: missing tests for a stated risk; missing manual-test plan; missing handling for an edge case the diff's logic implies; missing entry in `docs/invariants.md` for a new invariant; missing rollback notes for a migration. A gap is different from an issue: gaps describe absences; issues describe present-but-wrong code.
- **Suggestions** — constructive improvements the author *could* make but isn't *required* to. Includes: a cleaner approach the diff hints at, a simpler API shape, a naming change that would make intent obvious, a refactor opportunity, a "have you considered …" prompt. Suggestions are not issues — declining them is fine. Frame them as offers, not orders: "consider extracting …", "an alternative shape would be …". Cite `file:line` and, where helpful, sketch the alternative.
- **Issues** — present code that's wrong, classified into four severities:

  | Severity | Definition |
  |---|---|
  | **Critical** | PR cannot be merged before this is fixed. The change would break production on deploy, violates security requirements or data-privacy rules, irreversibly damages data, or violates a critical project invariant. No way to ship around it. |
  | **High** | Should be fixed before merge — high risk of something going wrong. Concrete failure modes are plausible (not just possible). Includes: unverified load-bearing assumption that the PR rests on, missing test for an actual risk, architecture violation that other code will copy. |
  | **Medium** | Subjective; likely a bug or likely a violation. Worth fixing now, but acceptable to address in a follow-up review if the author commits to it. Includes most "this looks wrong but I can't prove it breaks." |
  | **Low** | Small issues — naming, formatting, redundant code, minor refactors. Defer freely. |

Within each severity tier, sort by locator (file path / cross-cutting scope) so the author can walk top-down through the codebase.

### Locators

Every issue and suggestion needs a **locator** — something concrete enough that the reader can find the thing being talked about. The default and most useful form is `file:line`, but it's not the only valid form. Use whichever fits the finding:

- `file:line` (e.g. `app/db.py:34`) — local issue at a specific line or hunk. Default; use whenever applicable.
- `flow: X → Y → Z` (e.g. `flow: signup → db.find_by_email → db.insert`) — issue that emerges from the interaction of multiple call sites, not from any single one. Cite the participating files but locate the finding at the flow.
- `arch: <area>` (e.g. `arch: http handlers / domain layering`) — architectural or layering issue that describes a pattern across files; cite the architecture doc section that the pattern violates.
- `deps: <package>` (e.g. `deps: lodash`) — dependency-policy issue not tied to a code line.
- `scope: PR` — issue about the PR as a whole (missing description, scope sprawl, atomicity, etc.).
- `meta: <other-IDs>` (e.g. `meta: C1, S2`) — finding that references other findings (e.g. "if we accept C1, S2 is the wrong shape").

The rule isn't "must have `file:line`," it's "the reader can find the thing." Forcing a flow-level issue into a single line is *worse* than locating it correctly at the flow — it implies a local fix that won't address the actual finding.

When a single root cause produces multiple symptoms, prefer **one big-picture finding** with the participating sites listed, not several fine-grained findings that obscure the shared root. (If C1 and C2 are both "duplicate signup races" at different files, file one C1 with `flow:` locator instead.)

**Tag every issue and suggestion with a stable ID** so the author and reviewer can refer to them in follow-up conversation, commits, or PR comments without quoting the whole finding. Use:

- `C1`, `C2`, … for Critical issues
- `H1`, `H2`, … for High issues
- `M1`, `M2`, … for Medium issues
- `L1`, `L2`, … for Low issues
- `S1`, `S2`, … for Suggestions

Counters are per-review (start at 1 for each review) and per-bucket (C and H are independent sequences). "Fixed C1 and C2; declining S3" is a complete, unambiguous status update — that's what the IDs are for.

A note on calibration: **critical and high are scarce.** If every PR comes back with three criticals, the severity scheme stops carrying information. If the issue's failure mode is "uncomfortable" or "ugly" rather than "broken," it's not critical.

### 5. Report locally — inverted pyramid

Print to the terminal, **not the PR**, unless the user explicitly says "post it." Format:

```
# Examine: <PR title> (#<N>)

## Headline
<one sentence: merge / merge-with-fixes / hold>

## Stated intent
<one-line summary, or "PR has no description" finding>

## What was done well
- [file:line] <specific thing>: <why it's good>
- ...
(If genuinely none after honest looking, say so — but the bar is "I looked hard," not "nothing struck me.")

## Gaps
- <missing test for risk X>
- <no manual-test plan in description>
- <new invariant Y not added to docs/invariants.md>
- ...

## Issues

### Critical (must fix before merge)
- **C1** [locator] <issue> — <why critical> — <suggested fix>
- **C2** [locator] ...

### High (should fix before merge)
- **H1** [locator] <issue> — <failure mode> — <suggested fix>
- **H2** [locator] ...

### Medium (worth fixing now; acceptable as a follow-up)
- **M1** [locator] <issue> — <suggested fix>
- **M2** [locator] ...

### Low (defer)
- **L1** [locator] <issue>
- **L2** [locator] ...

## Suggestions
- **S1** [locator] <constructive alternative or improvement> — <why it'd be better>
- **S2** [locator] ...
(Suggestions are offers, not orders. The author may decline; that's fine.)

## Verified
<what was checked and confirmed fine — especially load-bearing assumptions — so the author sees the audited surface>

## Not reviewed
<scope skipped — e.g., "the existing migration framework, accepted as-is"; "the FE changes — out of scope for this pass">
```

The **Verified** and **Not reviewed** sections matter. Without them the author has to guess at the scope of the review and may argue findings they don't need to.

### 6. Post to the PR — only if the user asks

```bash
gh pr comment <N> --body-file <review.md>
```

For inline comments on specific lines, ask the user which findings to thread vs. summarize. **Default is terminal-only** — PR comments are public, durable, and ration the author's attention. The user decides what makes it.

## Anti-rationalization table

When tempted to skip a step, check whether your reasoning appears below. If it does, the answer is: do the step.

| Rationalization | Why it fails here |
|---|---|
| "The PR description seems clear enough; I'll just review the diff." | Reading the diff first anchors you to the author's choices instead of the problem. Read the description first, derive what *should* have happened, then compare. |
| "There's no description but the change is obvious." | "Obvious" to whom? You're filling in the author's intent silently — every assumption you make is a finding you swallowed instead of surfaced. Flag the missing description. |
| "Tests pass, so the change must be correct." | Tests cover what the author thought about. The interesting bugs are in what they didn't. Read the regression surface (adjacent unchanged code). |
| "I don't need to read `docs/`; the diff explains itself." | Architecture and invariants are not derivable from the diff. Without them you'll review against generic best practices, which are usually wrong for this project. |
| "This dependency is from a big company, skip the audit." | Typosquatting attacks specifically impersonate big-company packages. The audit is fast; skipping is the actual risk. |
| "The author says they tested manually, that's good enough." | "Tested manually" without specific steps and a specific environment is unverifiable. Either it's a finding ("how was this tested?") or it's risk you're now carrying. |
| "Load-bearing assumption looks plausible; ship it." | Plausible is not verified. The whole point of identifying it as load-bearing is that getting it wrong breaks the PR — go read the docs / measure / confirm. |
| "Reversibility is the deployer's problem, not the reviewer's." | A merged PR is one CI run away from prod. The reviewer is the last filter before irreversible damage — if you don't ask the rollback question, no one will. |
| "I'll just post all findings to the PR — let the author triage." | A 40-comment review trains the author to skim. Sort by severity; lead with what's critical; drop or bury the lows. |
| "Everything I noticed is at least High." | Probably not — that pattern is severity inflation. If three of the four buckets are empty, recalibrate: criticals reserve for "this breaks prod or violates a hard constraint," highs for "concrete plausible failure mode." Otherwise, demote. |
| "I don't have time to find anything that was done well." | "Done well" is part of the review, not garnish. It calibrates the author's signal-to-noise and prevents the review from reading as pure nitpicking. Spend the two minutes. |
| "This 'consider X' note is really a Low issue." | If it's a problem with the present code, it's an issue. If it's a constructive alternative or "have you considered" prompt, it's a Suggestion. Mixing them either inflates the issue list or hides real findings under polite framing. Pick the right bucket. |
| "I have inline doubts but no smoking gun — skip them." | Quiet doubts become loud bugs. List them as questions in the report; let the author answer. Silent doubts are findings you decided not to surface. |
| "Posting to the PR is faster than copying the review." | The user didn't ask you to post it. PR comments are public and durable; let the user decide what's visible. |

## Anti-patterns

- **Reviewing the diff without reading the description.** You'll review the implementation; you won't review whether it solves the problem.
- **Reviewing against generic best practices.** The project has its own rules; review against those.
- **"LGTM" reviews on non-trivial PRs.** If the change is non-trivial, the review owes the author at least a Verified / Not-reviewed split so they know what was actually audited.
- **Burying critical findings under low-severity noise.** Severity-sort. Always.
- **Pure-negative reviews.** A review with no "what was done well" trains the author to dread review. Find at least one concrete thing per PR worth keeping; if you genuinely can't, that's a finding about the PR, not absence of effort.
- **Severity inflation.** If every issue is Critical or High, the severity scheme stops carrying signal. Reserve the top tiers; demote what doesn't actually meet the bar.
- **Posting to the PR by default.** Terminal-first. The user decides what becomes public.
- **Treating CI green as the end of testing.** CI runs the tests the author wrote. The review covers the tests they didn't.

## Definition of done

The review is complete when **all** of these are true. Each item is answerable with evidence — a quote from the diff, a doc path, a CI line — not a vibe.

- [ ] PR description has been read; stated problem, approach, constraints, and non-obvious decisions are extracted (or flagged as missing).
- [ ] Project docs (`AGENTS.md`, `docs/`, README) have been read; the review judges against the project's own rules, not generic ones. Absence of docs is itself noted.
- [ ] Every axis in step 3 has been walked: alignment, problem-solving, correctness, completeness, architecture, conventions, security, data privacy, testing, load-bearing assumptions, risk, reversibility, dependencies. Skipped axes are listed in **Not reviewed**.
- [ ] At least one load-bearing assumption has been independently verified against an outside source (library docs, stdlib docs, measurement, etc.) — or the absence of any load-bearing assumption is justified.
- [ ] Top 3 production-risk failure modes are named; for each, the test (or lack of test) that covers it is identified.
- [ ] Reversibility has been assessed; irreversible side effects, if any, are flagged as **Critical** or **High**.
- [ ] Dependencies, if any were added or bumped, were audited for typosquatting, CVEs, abandonment, and version-range hygiene.
- [ ] Report contains all four signals: **What was done well** (with `file:line` where applicable), **Gaps** (what's missing), **Issues** classified as Critical / High / Medium / Low, and **Suggestions** (constructive alternatives, framed as offers). Each issue and suggestion has a **locator** (default `file:line`; `flow:` / `arch:` / `deps:` / `scope: PR` / `meta:` when the finding lives above the code) **and a stable ID** (`C1`, `C2`, …; `H1`, …; `M1`, …; `L1`, …; `S1`, …) so it can be referenced later.
- [ ] Severity calibration sanity-checked: critical and high are scarce and reserved for their definitions; constructive "consider X" notes live under Suggestions, not under Low issues.
- [ ] Report includes **Verified** and **Not reviewed** sections so the author sees the scope.
- [ ] Report was printed to the terminal. It was posted to the PR only if the user explicitly asked.

If a checkbox cannot be ticked honestly, the review is not done — return to the step that produces it.

## Relationship to other skills

- `/review` — the built-in quick pass. Use when the change is small or the user wants a 30-second look. `/examine` is the deep one.
- `/security-review` — the built-in security-focused pass. Use when the threat surface is the primary concern; `/examine` covers security as one axis among many.
- `/rca` — for *failures* after merge. If a `/examine`-blessed PR breaks prod, follow up with `/rca`.
- `/blueprint` — for designing a *change*. If review surfaces that the approach is wrong on `new_base` (not just the implementation), point the author at `/blueprint` for the redesign.
- `/rebase` — if review reveals the branch is behind and needs to move onto a new base before review can be meaningfully finished, switch to `/rebase` first.

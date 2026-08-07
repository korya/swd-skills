---
name: examine
description: Review a pull request rigorously — establish the PR's stated intent and constraints, confirm the problem is real, sketch the obvious solutions before reading the diff, then audit the diff against the claimed approach, check correctness, completeness, architecture, conventions, security, data privacy, testing, reversibility, and dependency hygiene, and finish with an Occam pass judging whether the solution is right-sized. Validate load-bearing assumptions against independent sources. Returns a structured report with five signals — what was done well, gaps (what's missing), issues classified as Critical / High / Medium / Low, suggestions (constructive improvements), and known limitations (real but accepted). Use when the user says "/examine", "examine this PR", "review this PR", "review pr #N", "look over my pull request", "check my PR before merge", or asks for a deep code review beyond surface diff-reading. Heavier than the built-in `/review`; the goal is to surface what would actually break in production, not to summarize the diff.
---

# Examine: production-risk-first PR review

The point of this skill is **not** to produce a "looks good to me" or a paragraph summary of the diff. It is to find what would actually break in production — and to verify the PR's claims rather than trust them. The second, equal half of the job: judge whether the solution is **right-sized** — the simplest one that solves the stated problem while satisfying all the constraints. A review that verifies correctness but waves through needless complexity has done half its work.

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
- **The simplest solution that satisfies the constraints wins.** Sketch what the obvious fix would look like *before* reading the diff, so the diff doesn't define your sense of normal. Everything the PR does beyond the obvious approach must be explained by a constraint — but treat divergence from your sketch as a question to investigate, never as proof by itself: the author usually knows a constraint your five-minute sketch missed.
- **Five signals, not one.** A useful review tells the author five things: what's working well (so they keep doing it), what's missing (so they know the gaps), what's wrong (so they know what to fix), what could be better (constructive alternatives that aren't required but would improve the PR), and what's known-broken but accepted (so risk-acceptance is documented, not silent). All five carry information; omitting any of them shortchanges the author.
- **Acknowledge good work explicitly.** Looking hard for what was done well is part of the discipline, not optional politeness. It calibrates your tone, prevents "review by nitpicking," and tells the author which patterns to repeat. A review that finds nothing good is almost always a reviewer-fatigue artifact, not a fact about the PR.
- **Be useful, not exhaustive.** A review with 50 lows and 1 buried critical issue is worse than 5 findings sorted by severity. Headline the things that matter.
- **Verify without side effects.** Verification may read anything and run anything locally — check out the branch, run the tests, write probe scripts. It may not touch anything others observe: no pushes to the author's branch, no PR comments (the terminal-first default in step 8), no CI triggers, no fix commits, nothing sent to a person or third-party service. Reversibility is judged by observable effects, not artifact state — a reverted push does not unsend the notifications. If the only path to evidence crosses that line, ask the user; consent granted for an earlier task does not carry over. Local experimental edits are reverted before the report.

## Inputs to establish up front

- PR number or URL (gh CLI: `gh pr view <N>`)
- Repo context: AGENTS.md / docs/ / README — note their presence
- CI status: `gh pr checks <N>` — passing, failing, or flaky
- Whether the user wants the review posted to the PR (default: **no**, terminal only)
- Working-tree baseline before any local experimenting: current branch, `HEAD` sha, `git status --porcelain` output. The end-of-review restore check compares against this, not against "clean" — the user's own uncommitted work is part of the baseline, not something to revert.

## Workflow

Many of these steps parallelize. If your host supports read-only search subagents, delegate the docs sweep, the conventions audit, the security pass, and the dependency audit — you stay in charge of severity calls and the final synthesis. If it doesn't, run them yourself in sequence; the order below is already dependency-correct.

### 1. Establish intent — what is this PR trying to do?

```bash
gh pr view <N> --json title,body,author,baseRefName,headRefName,changedFiles,additions,deletions,files
```

Extract from the description:

- **Stated problem** — what does the author say is wrong or missing?
- **Stated approach** — how do they claim to fix it?
- **Constraints / non-goals** — what did they explicitly choose not to do?
- **Non-obvious decisions** — anything called out as "I picked X over Y because…"

If the PR links a ticket (Linear, GitHub issue, …), **read it** — the problem statement and its constraints usually live there in fuller form than the PR description, and the ticket often records rejected approaches that pre-answer step 4's "why not the obvious way?" question. A discrepancy between ticket and PR description (scope drift, silently dropped requirement) is itself a finding.

If the description is missing, empty, or pure boilerplate ("update the foo"), **that is finding #1**. A PR without an intent statement makes the reviewer reverse-engineer the author's goal, which means the reviewer is doing the author's job. Flag it prominently. Then derive intent from the diff yourself, and mark every claim you have to infer as **derived, not stated** so the author sees what the missing description cost.

### 2. Establish context — what is the project's own rulebook?

This step is what separates a real review from training-data pattern-matching. The agent does not get to skip it.

In parallel with step 1, **read in full** the load-bearing documents (these will be cited per-finding in step 5, so excerpts aren't enough):

- `docs/invariants.md` — rules that must hold; load-bearing for any finding about invariants
- `docs/security.md` / `docs/threat-model.md` / `SECURITY.md` — project-specific threat model; load-bearing for step 5g
- `docs/privacy.md` / data-handling policy — load-bearing for step 5h
- `docs/product-specs/<area-touched-by-the-PR>` — load-bearing for steps 5a / 5b
- `docs/testing.md` / testing conventions — load-bearing for step 5i

Other context docs can be gathered by a read-only search subagent, or skimmed directly (excerpts are fine):

- `AGENTS.md` / `CLAUDE.md` (agent-facing instructions)
- `docs/architecture.md` (boundaries; full read if the PR touches module boundaries)
- `docs/guidelines.md` (general conventions — code style, modularization, UX)
- `README` if no `docs/` exists

If a load-bearing doc is **missing**, note it in the report — the absence of a project rule on (e.g.) privacy is itself a finding the reviewer should surface, not a license to fall back to generic best practices.

The mandate: every finding about architecture, conventions, security, privacy, or testing in step 5 must **cite the specific project rule** it's judged against (`docs/path.md §section` or quoted line). A finding like "violates project conventions" without a citation is itself a finding — either go get the citation, or downgrade to a Suggestion. Citations are what distinguish "I'm pattern-matching" from "this PR contradicts a rule the project actually has."

### 3. Establish the baseline — is the problem real, and what would the obvious fix look like?

Do this **before opening the diff** (`gh pr view` metadata is fine; `gh pr diff` is not yet). Two artifacts:

**Confirm the problem exists in the current code.** Reproduce the stated failure, or read the pre-PR code path and confirm it really lacks the behavior / has the bug. Two review-killers hide here:

- The problem is already solved — fully, partially, or by an existing utility the PR reimplements. The PR should be a call site, not a subsystem.
- The problem as stated doesn't occur — misdiagnosis; the real defect is elsewhere and the PR treats a symptom.

Either one reframes the entire review and becomes finding #1 if found.

**Sketch the obvious approaches.** Write down 2–3 naive, high-level ways *you* would solve the stated problem under the stated constraints — one or two sentences each, no code. This is the anchor that keeps the diff from defining your sense of "normal": without it, you review the author's choices against themselves. Scale the effort to blast radius — a copy-tweak PR deserves three bullets; a schema migration deserves a real sketch with trade-offs.

The sketches are hypotheses, not standards: they're written by someone who has spent minutes on a problem the author spent days on. Their value is the comparison they enable in step 4, not their own correctness.

### 4. The approach gate — agree on the shape before judging the lines

Compare the PR's actual approach against the step-3 sketches:

- **Matches an obvious approach** → proceed. The comparison already paid for itself: everything the PR does *beyond* the matched sketch is now visible, must be explained by a constraint, and feeds the step-6 Occam pass.
- **Diverges from all of them** → diagnose before judging. The humble default: **your sketch is missing a constraint.** Hunt for it — the ticket, the step-2 docs, git history, adjacent code, the PR's "non-obvious decisions." If you find it, your understanding was lacking: update the sketch, proceed, and record the constraint under **Verified** (the next reviewer will trip on it too). Only if a genuine hunt comes up empty does the divergence become a finding — either the author's understanding is lacking, or they never wrote down the constraint that drove them. Both are approach-level questions the author must answer, not nits.

**Escalation rule:** an unresolved disagreement about the problem definition, the architecture, or the high-level shape of the solution is the **headline of the report**. Never bury it — a report with 20 line findings and a footnote "also, is this the right approach?" signals "fix the nits and merge," which launders a wrongly-shaped solution. When the gate fails, still run steps 5–6 (cheap once you're in the code), but mark every line-level finding **provisional**: explicitly contingent on the approach question resolving in the PR's favor. If the approach is wrong on its face, point the author at `/blueprint` for the redesign.

### 5. Audit the diff

```bash
gh pr diff <N>
```

Walk the diff against the axes below. Track each axis in whatever task or plan tool your host provides, so none is silently dropped; delegate the ones that benefit from parallel work (security, conventions, dependencies, docs alignment) if subagents are available.

#### 5a. Alignment with the claimed approach
Does the code actually do what the description says? Common drift: the description says "I added validation"; the diff adds a helper but doesn't call it from the relevant endpoint.

#### 5b. Solves the stated (or derived) problem under stated constraints
Walk a representative failure case from the problem statement through the new code. Would it fix it? Are the constraints honored, or quietly violated?

#### 5c. Correctness — bugs and gaps
Read adversarially: off-by-one, null/empty cases, error paths, race conditions, type coercions, silent truncations. Be especially skeptical of code copied from existing patterns — the differences are where bugs live.

#### 5d. Completeness — siblings the diff missed
Search for sibling call sites. If `foo()` was modified for a reason, every caller deserves a look. The regression surface is the *unchanged* code around the diff.

#### 5e. Architecture
Does the change respect the layering in `docs/architecture.md`? Common violation: bypassing a module boundary because it was inconvenient.

**Findings cite the rule:** every architecture finding names the `docs/architecture.md` section (or other architecture doc) the PR contradicts. No citation = no project rule was actually verified.

#### 5f. Conventions
Project-specific code style, file layout, dependency rules, test colocation, commit-message format, UX/UI guidelines. Verify against the docs, not against your priors.

**Findings cite the rule:** every conventions finding names the `docs/guidelines.md` (or `AGENTS.md`, style guide, etc.) section the PR contradicts. A finding that can't be tied to a documented convention is at most a Suggestion, not an Issue.

#### 5g. Security
- **Trust boundaries:** inputs from outside (HTTP body, query, headers, uploads, webhooks) parsed and validated before use?
- **Injection surfaces:** SQL / shell / command / template / XSS parameterized or escaped?
- **AuthN/AuthZ:** new endpoints enforce them at the same layer as existing ones?
- **Secrets:** none logged, none in tests, none in error responses
- **OWASP Top 10** sweep against the affected surface

**Findings cite the rule:** if the project has `docs/security.md` / `threat-model.md` / `SECURITY.md`, every security finding cites the specific rule violated. If no project rule exists for the concern, name the OWASP item or industry-standard rule explicitly — and note in the report that no project-level rule was found (that's itself a finding).

#### 5h. Data privacy
- New PII in fields, logs, telemetry — tagged/redacted per project policy?
- Retention — new data persisted? For how long? Per policy?
- Cross-tenant leakage — does the new query filter by tenant/org?
- Regional / GDPR data-residency rules respected?

**Findings cite the rule:** every privacy finding cites the project's privacy / data-handling policy (`docs/privacy.md`, similar) by section. If no policy exists, note its absence as a finding — privacy concerns can't be honestly judged from training-data priors alone.

#### 5i. Testing
- Tests included? At what level — unit / integration / e2e?
- Cover the *failure* paths, not just the happy path?
- Cover regressions in adjacent unchanged code the PR could break?
- Manual testing described? Specific (steps, env) or hand-wavy ("I tested it locally")?
- CI: `gh pr checks <N>` — what passed, what failed, what's flaky vs. broken?

**Findings cite the rule:** if the project has testing conventions (`docs/testing.md`, `AGENTS.md` testing section, or similar), every testing finding cites the specific convention. "Missing tests" without a documented coverage expectation is a Suggestion, not an Issue.

#### 5j. Validate load-bearing assumptions independently
For each non-obvious claim the PR rests on, verify against an outside source:

- New library / API call → read the library's docs or source. Does it behave as the PR assumes?
- Edge of language / runtime behavior → confirm with the stdlib docs.
- Performance claim → measure or profile, not vibes.
- Compatibility claim → confirm against the target versions, not the latest.

An unverified load-bearing assumption is the modal source of "tests passed but prod broke."

#### 5k. Risk and tested coverage of risk
Name the top 3 ways this PR could break production. For each, is there a test (auto or claimed manual) that would catch the failure mode? If not, that's a finding — not "add a test someday," but "this risk is currently uncovered."

#### 5l. Reversibility — what happens if this fires in prod?
- DB migrations: forward-only with data loss, or backward-compatible (e.g., add column nullable → backfill → drop later)? Flag any "we'll backfill later" or "drop old column in the same PR" as serious.
- Schema changes: tolerated by old code reading new data, and vice versa?
- Feature flags: can the new path be turned off without revert?
- External side effects: webhooks fired, queue messages emitted, files written — irreversible?

Reversibility failures are the most expensive to ship. A PR that can't be cleanly reverted carries higher risk by definition.

#### 5m. Dependency audit
For each added or bumped dependency (`go.mod`, `package.json`, `requirements.txt`, `Cargo.toml`, etc.):

- **Typosquatting** — package name sanity check (`requets` vs `requests`, `lodahs` vs `lodash`)
- **Major version** — current vs. latest; deprecated majors are findings
- **CVEs** — `npm audit` / `pip-audit` / language-specific advisory lookup; or web-search "<package> CVE"
- **Version range** — overly broad ranges (`*`, `^0.x`) or pinned to unreleased commits
- **Maintenance** — last release within ~2 years; abandoned packages are a finding

### 6. The Occam pass — is this more solution than the problem needs?

The audit asks "is it wrong?"; this pass asks "is it more than needed?" A solution that satisfies the problem and constraints with fewer concepts and fewer failure modes is strictly better — fewer bugs to ship, faster to read, more predictable to operate. Walk the diff once more looking specifically for:

- **Premature optimization** — the leading cause of overcomplicated PRs. Caching, pooling, batching, custom data structures, denormalization, cleverness in a path with no demonstrated need. The test: is there a measurement, or a stated scale requirement, that justifies it? No evidence → finding.
- **Speculative generality** — abstractions, parameters, config flags, and extension points for futures nobody scheduled. Interfaces with one implementation, options every caller passes identically, "pluggable" designs with one plugin. YAGNI.
- **Over-defensive code** — guards for states the type system or call graph already excludes, catch-all handlers that swallow failures instead of surfacing them, retries around non-transient operations, fallbacks that mask the error they fall back from. Defending against *impossible* states isn't safety, it's camouflage: it hides real invariants and gives bugs a place to sleep. (Defensive code at trust boundaries is the opposite case — required; see 5g.)
- **Reinvention** — does the repo already have a utility, pattern, or service that does this? Search before accepting new plumbing (5d looks for siblings the diff should have *changed*; this looks for existing code the diff should have *used*).
- **Deletion candidates** — for each new module, layer, or indirection: what breaks if it collapses into its caller? If the answer is "nothing, it's just tidier," propose the collapse.

Two calibration rules keep the pass honest:

- **A simplification proposal must clear the same evidence bar as any other finding.** Before proposing "simpler X," walk X against the full constraint list from steps 1–2 and state which constraints you checked. Propose one "simpler" approach that a documented constraint already rules out, and the author rightly stops reading your suggestions.
- **Less code is not the metric.** Simplicity = fewest concepts and failure modes, not fewest lines. Over-DRY abstraction, code-golf compression, and clever one-liners are complexity wearing a smaller coat. More code is sometimes the simpler solution: explicit parallel branches beat a "unified" mechanism nobody can modify safely, and operational legibility — can you tell what it's doing in prod? — counts as simplicity.

**Severity:** over-engineering defaults to a **Suggestion**. Promote to an **Issue** (usually Medium) when the complexity has concrete, citable cost — a new moving part that must be deployed/monitored/operated, a pattern adjacent code will copy, a maintenance surface disproportionate to the problem — and the project's own conventions back the call (many repos codify "write simple code" / "don't duplicate"; cite the section). An Issue-level simplicity finding with neither a citation nor a concrete cost is severity inflation — demote it.

### 7. Synthesize — five signals, four severities

The report carries five distinct signals. Mixing them up trains the author to skim:

- **What was done well** — concrete things in this PR worth keeping. Cite `file:line` so it's specific, not flattering. Examples: "good failure-path coverage in `auth_test.go:120-180`", "schema migration is backward-compatible — old readers still parse new rows", "telemetry tagged correctly for cross-region requirements".
- **Gaps** — low-consequence absences worth surfacing but not severity-worthy on their own: missing changelog entry, missing brief in the PR description, missing manual-test plan when the change is auto-covered, missing screenshot for a UI tweak.

  **Consequential absences belong in Issues, not Gaps.** A missing test for a stated risk is functionally a finding the author has to act on, same as a present-but-wrong bug — file it as Critical/High/Medium/Low with a `scope: PR` (or appropriate) locator. Examples:
  - Missing test for a documented failure mode → **H1 [scope: PR]** "no test for migration-rollback path — leaves data-loss failure mode uncovered."
  - Missing handling for an edge case the diff's logic implies → severity per the failure mode.
  - Missing entry in `docs/invariants.md` for a new invariant the PR introduces → **M1 [scope: PR]** or **L1**, depending on how load-bearing the invariant is.

  The split rule: if the author has to address it before merge (or it changes the risk of merge), it's an Issue. If it's a "nice to have noted" that doesn't gate anything, it's a Gap.
- **Suggestions** — constructive improvements the author *could* make but isn't *required* to. Includes: a cleaner approach the diff hints at, a simpler API shape, a naming change that would make intent obvious, a refactor opportunity, a "have you considered …" prompt. Suggestions are not issues — declining them is fine. Frame them as offers, not orders: "consider extracting …", "an alternative shape would be …". Cite `file:line` and, where helpful, sketch the alternative.
- **Known limitations** — real, considered problems deliberately *not* worth fixing: the failure mode is too rare, the fix too invasive relative to the risk, or the risk is consciously accepted. Naming them converts silent risk-acceptance into documented risk-acceptance — the author can lift them straight into the PR description or docs, and the next reviewer doesn't re-litigate them. Each entry states the problem, why it's acceptable, and (when useful) where it should be documented. This bucket is also the dignified exit for findings that don't clear the Issue bar: "real but accepted" beats both silence and severity inflation.
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

A note on rendering: non-Low issues and suggestions are written as **blocks**, not one-line bullets. Each block has a heading (`#### C1 — title`), then labeled fields for Locator / What / Why / Fix / Cites (see step 8 for the template). The block shape exists because one-line findings collapse the problem, the failure mode, and the fix into a wall of em-dashes that the author can't act on for anything non-trivial. Low issues stay compact — they're noise-tier and would only bloat the report.

### 8. Report locally — inverted pyramid

Print to the terminal, **not the PR**, unless the user explicitly says "post it." Format:

```
# Examine: <PR title> (#<N>)

## Headline
<one sentence: merge / merge-with-fixes / hold. If the step-4 approach gate failed, the unresolved approach question IS the headline.>

## Stated intent
<one-line summary, or "PR has no description" finding>

## Approach fit
<one of: "matches the obvious approach — <which>" / "diverges for a real constraint: <the constraint, cited>" / "APPROACH DISPUTED: <the unresolved question>". In the disputed case, state that all line-level findings below are provisional.>

## What was done well
- [file:line] <specific thing>: <why it's good>
- ...
(If genuinely none after honest looking, say so — but the bar is "I looked hard," not "nothing struck me.")

## Gaps
- <low-consequence absence — e.g. no changelog entry, no screenshot, no manual-test plan for an auto-covered change>
- ...
(Consequential absences belong in Issues with a severity, not here.)

## Issues

Non-Low issues are rendered as **blocks**, not one-line bullets — each finding gets a heading and labeled fields so the author can drill into severity / cause / fix / cited rule without parsing em-dash-separated phrases. Low issues stay compact because they're noise-tier by definition.

### Critical (must fix before merge)

#### C1 — <one-line title>
- **Locator:** <locator>
- **What:** <the problem, 1–3 sentences; describe the present-but-wrong code or behavior>
- **Why Critical:** <the failure mode that breaks production / violates security / violates privacy / damages data, and why it can't be shipped around>
- **Fix:** <concrete suggested change — file edits, approach, or "see below" with a sketch>
- **Cites:** <docs/path.md §section> *(omit if no project rule applies; presence of the field is the operational hook for the cross-validation requirement)*

#### C2 — <next critical, same shape>
...

*Worked example of a non-trivial finding to illustrate the format:*

> #### C1 — Duplicate-signup race lets the same email register twice
> - **Locator:** `flow: app/signup.py:13 → app/db.py:32-36`
> - **What:** `signup.signup` calls `db.find_by_email` to enforce uniqueness, then `db.insert` — two non-atomic steps. Two concurrent signups with the same email both see "no match," both insert, and the store ends up with two `User` rows for one person.
> - **Why Critical:** Silent data corruption. Downstream billing, auth, and password-reset all join by email and now behave non-deterministically (which row wins depends on insertion order). No detection in prod until support traces a duplicated invoice.
> - **Fix:** Move the uniqueness check into `db.insert` under a single critical section (or rely on a `UNIQUE` constraint and translate the integrity error to `SignupError`). Drop the now-redundant check in `signup.signup`.
> - **Cites:** `docs/invariants.md §4 (User identity is unique per canonical email)`

### High (should fix before merge)

#### H1 — <one-line title>
- **Locator:** <locator>
- **What:** <the problem>
- **Why High:** <concrete plausible failure mode — not "could break" but "the failure mode is X and it's plausible because Y">
- **Fix:** <concrete suggested change>
- **Cites:** <docs/path.md §section> *(when judging against a project rule)*

#### H2 ...

### Medium (worth fixing now; acceptable as a follow-up)

#### M1 — <one-line title>
- **Locator:** <locator>
- **What:** <the problem>
- **Why Medium:** <why it's likely-a-bug or likely-a-violation, and why it's ok to defer to follow-up>
- **Fix:** <concrete suggested change>
- **Cites:** <docs/path.md §section> *(when judging against a project rule)*

#### M2 ...

### Low (defer)

Compact form — one line per finding. If a Low issue genuinely needs more than one line to describe, it's not Low; promote it.

- **L1** [locator] <one-line note>
- **L2** [locator] ...

## Suggestions

Same block shape as non-Low issues. Suggestions are offers, not orders — the **Why** field describes the improvement, not a failure mode, and the author may decline.

#### S1 — <one-line title>
- **Locator:** <locator>
- **What:** <the constructive alternative or improvement>
- **Why it'd be better:** <the gain — clearer intent, simpler API, fewer foot-guns, etc.>
- **Sketch:** <optional — a short code snippet or pseudo-code if the alternative is non-obvious>

#### S2 ...

## Known limitations
- <real, considered problem deliberately not fixed — the failure mode, why it's acceptable, and where to document it if anywhere>
- ...
(Real-but-accepted, not forgotten: each entry names the problem AND the reason it doesn't warrant a fix. Omit the section only if genuinely empty.)

## Verified
<what was checked and confirmed fine — especially load-bearing assumptions, and any constraint discovered in step 4 that explains the PR's shape — so the author sees the audited surface>

## Not reviewed
<scope skipped — e.g., "the existing migration framework, accepted as-is"; "the FE changes — out of scope for this pass">
```

The **Verified** and **Not reviewed** sections matter. Without them the author has to guess at the scope of the review and may argue findings they don't need to.

### 9. Post to the PR — only if the user asks

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
| "The diff is right here; sketching my own approach first is ceremony." | Reading the diff first makes the author's choices your baseline for "normal" — you'll verify their solution instead of judging it. The sketch costs minutes and is the only thing that makes over-engineering *visible*. |
| "The author surely had a reason for the extra complexity." | Then find it — ticket, docs, git history, adjacent code. If it exists, cite it under Verified; if a genuine hunt comes up empty, it's an approach-level question for the author. Silently assuming a justification swallows the finding. |
| "My simpler approach is obviously better — file it as an Issue." | Not until you've walked it against every stated constraint and said so. A "simpler" proposal that a documented constraint rules out costs the review its credibility — and simplicity findings without citable cost are Suggestions, not Issues. |
| "The approach looks wrong, but I'll do the line review and mention it at the end." | Burying an approach disagreement under line findings signals "fix the nits and merge." The disagreement is the headline; every line finding below it is provisional. |
| "Reversibility is the deployer's problem, not the reviewer's." | A merged PR is one CI run away from prod. The reviewer is the last filter before irreversible damage — if you don't ask the rollback question, no one will. |
| "I'll just post all findings to the PR — let the author triage." | A 40-comment review trains the author to skim. Sort by severity; lead with what's critical; drop or bury the lows. |
| "Everything I noticed is at least High." | Probably not — that pattern is severity inflation. If three of the four buckets are empty, recalibrate: criticals reserve for "this breaks prod or violates a hard constraint," highs for "concrete plausible failure mode." Otherwise, demote. |
| "I don't have time to find anything that was done well." | "Done well" is part of the review, not garnish. It calibrates the author's signal-to-noise and prevents the review from reading as pure nitpicking. Spend the two minutes. |
| "This 'consider X' note is really a Low issue." | If it's a problem with the present code, it's an issue. If it's a constructive alternative or "have you considered" prompt, it's a Suggestion. Mixing them either inflates the issue list or hides real findings under polite framing. Pick the right bucket. |
| "There's no test for the stated risk — I'll just note it as a Gap." | A missing test for a *stated* risk is a finding the author has to address; that's an Issue with a severity, not a Gap. Leaving it under Gaps softens it into something the author can skim past. |
| "This is obviously a privacy / security / conventions violation, no need to cite the doc." | "Obviously" is exactly the move that lets training-data priors masquerade as project rules. The citation is what distinguishes "this PR contradicts a rule the project actually has" from "this looks wrong to me." Either find the rule, or downgrade the finding to a Suggestion. |
| "I'll just skim the invariants/security/privacy/testing docs — I get the gist." | Excerpts work for orientation but not for compliance checks. Findings are going to cite these by section — if you only skimmed, you'll either miss the rule the PR violates or invent a rule that isn't there. Read in full. |
| "I have inline doubts but no smoking gun — skip them." | Quiet doubts become loud bugs. List them as questions in the report; let the author answer. Silent doubts are findings you decided not to surface. |
| "Posting to the PR is faster than copying the review." | The user didn't ask you to post it. PR comments are public and durable; let the user decide what's visible. |
| "The fix is one line — I'll just push it to the author's branch." | That mutates the subject under review and publishes the mutation: CI runs, watchers get notified, the author's work changes under them. A review's output is findings, not commits. Put the fix in the report; the author decides. |
| "I'll trigger CI / push a probe commit to test my theory about the pipeline." | The experiment is observable by the author and every watcher, and it alters the PR under review. Exhaust read-only evidence first — prior run logs, `gh api`, a local repro — and if the theory genuinely needs a live trigger, that's a question for the user, not a judgment call. |

## Anti-patterns

- **Reviewing the diff without reading the description.** You'll review the implementation; you won't review whether it solves the problem.
- **Reviewing against generic best practices.** The project has its own rules; review against those.
- **"LGTM" reviews on non-trivial PRs.** If the change is non-trivial, the review owes the author at least a Verified / Not-reviewed split so they know what was actually audited.
- **Burying critical findings under low-severity noise.** Severity-sort. Always.
- **Pure-negative reviews.** A review with no "what was done well" trains the author to dread review. Find at least one concrete thing per PR worth keeping; if you genuinely can't, that's a finding about the PR, not absence of effort.
- **Severity inflation.** If every issue is Critical or High, the severity scheme stops carrying signal. Reserve the top tiers; demote what doesn't actually meet the bar.
- **Posting to the PR by default.** Terminal-first. The user decides what becomes public.
- **Treating CI green as the end of testing.** CI runs the tests the author wrote. The review covers the tests they didn't.
- **Approving complexity by default.** Verifying that complicated code is *correct* is not the same as verifying it's *necessary*. A review that never asks "what would the obvious solution look like?" rubber-stamps over-engineering — and over-engineered patterns metastasize, because the next PR copies them.

## Definition of done

The review is complete when **all** of these are true. Each item is answerable with evidence — a quote from the diff, a doc path, a CI line — not a vibe.

- [ ] PR description has been read; stated problem, approach, constraints, and non-obvious decisions are extracted (or flagged as missing). The linked ticket, if any, has been read and reconciled with the description.
- [ ] The problem was confirmed to exist in the pre-PR code (reproduced, or the code path read) — or the report flags that it doesn't occur / is already solved by existing code.
- [ ] 2–3 obvious approaches were sketched **before** the diff was read; the PR's approach was mapped to one of them, or the divergence was diagnosed — either the explaining constraint is cited under Verified, or the open approach question is the report's headline.
- [ ] Project docs have been read. Load-bearing docs (`docs/invariants.md`, `docs/security.md`/threat-model, `docs/privacy.md`, `docs/product-specs/<area>`, `docs/testing.md`) were **read in full**, not excerpted. Absence of any of these is itself noted as a finding.
- [ ] Findings about architecture, conventions, security, privacy, and testing each cite the specific project-doc rule (file + section, or quoted line) they're judged against. Findings that can't be tied to a project rule are downgraded to Suggestions or recorded as "no project rule on this; reviewed against generic standard X."
- [ ] Every axis in step 5 has been walked: alignment, problem-solving, correctness, completeness, architecture, conventions, security, data privacy, testing, load-bearing assumptions, risk, reversibility, dependencies. Skipped axes are listed in **Not reviewed**.
- [ ] The Occam pass (step 6) ran: premature optimization, speculative generality, over-defensive code, reinvention, and deletion candidates were each considered. Every simplification proposal names the constraints it was walked against.
- [ ] At least one load-bearing assumption has been independently verified against an outside source (library docs, stdlib docs, measurement, etc.) — or the absence of any load-bearing assumption is justified.
- [ ] Top 3 production-risk failure modes are named; for each, the test (or lack of test) that covers it is identified.
- [ ] Reversibility has been assessed; irreversible side effects, if any, are flagged as **Critical** or **High**.
- [ ] Dependencies, if any were added or bumped, were audited for typosquatting, CVEs, abandonment, and version-range hygiene.
- [ ] Report contains all five signals: **What was done well** (with `file:line` where applicable), **Gaps** (low-consequence absences only — consequential ones live under Issues), **Issues** classified as Critical / High / Medium / Low, **Suggestions** (constructive alternatives, framed as offers), and **Known limitations** (real-but-accepted problems, each with the reason it doesn't warrant a fix). Each issue and suggestion has a **locator** (default `file:line`; `flow:` / `arch:` / `deps:` / `scope: PR` / `meta:` when the finding lives above the code) **and a stable ID** (`C1`, `C2`, …; `H1`, …; `M1`, …; `L1`, …; `S1`, …) so it can be referenced later.
- [ ] Non-Low issues and suggestions render as **structured blocks** with `#### <ID> — title` headings and labeled `Locator / What / Why / Fix / Cites` fields. Low issues stay compact (one-line bullets); if a Low needs more than one line, it's not Low — promote it.
- [ ] Severity calibration sanity-checked: critical and high are scarce and reserved for their definitions; constructive "consider X" notes live under Suggestions, not under Low issues.
- [ ] Report includes **Verified** and **Not reviewed** sections so the author sees the scope.
- [ ] Report was printed to the terminal. It was posted to the PR only if the user explicitly asked.
- [ ] Review left no trace: working tree restored to the recorded baseline (`git status` compared and shown); nothing pushed, commented, triggered, or sent to any person or third-party system without explicit approval obtained *during this review* — consent from an earlier task does not carry over.

If a checkbox cannot be ticked honestly, the review is not done — return to the step that produces it.

## Relationship to other skills

- `/review` — the built-in quick pass. Use when the change is small or the user wants a 30-second look. `/examine` is the deep one.
- `/security-review` — the built-in security-focused pass. Use when the threat surface is the primary concern; `/examine` covers security as one axis among many.
- `/rca` — for *failures* after merge. If a `/examine`-blessed PR breaks prod, follow up with `/rca`.
- `/blueprint` — for designing a *change*. If the step-4 approach gate surfaces that the approach itself is wrong (not just the implementation), point the author at `/blueprint` for the redesign.
- `/rebase` — if review reveals the branch is behind and needs to move onto a new base before review can be meaningfully finished, switch to `/rebase` first.

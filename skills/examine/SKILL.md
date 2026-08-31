---
name: examine
description: Review a code change rigorously — a PR, branch, commit range, or the working tree. Establish intent and constraints, confirm the problem is real, sketch the obvious solutions before reading the diff, then audit it for correctness, completeness, architecture, conventions, security, privacy, testing, reversibility, and dependencies, judge whether it is right-sized, and verify every significant finding independently. Returns a report with six signals: done well, gaps, issues rated Critical / High / Medium / Low with a separate confidence verdict, questions, suggestions, and known limitations. Use when the user says "/examine", "examine this PR", "review this PR", "review pr #N", "review my branch", "look over my pull request", "check my PR before merge", or asks for a deep code review. Holistic where the host's built-in review is defect-first: surface what would break in production, not a diff summary.
---

# Examine: production-risk-first code review

The point of this skill is **not** to produce a "looks good to me" or a paragraph summary of
the diff. It is to find what would actually break in production — and to verify the change's
claims rather than trust them. The second, equal half of the job: judge whether the solution
is **right-sized** — the simplest one that solves the stated problem while satisfying all the
constraints. A review that verifies correctness but waves through needless complexity has done
half its work.

The host's built-in review (`/code-review` on Claude Code, `review-agent` on Codex) is
defect-first: does this change introduce an actionable bug? `/examine` is holistic: is this
the right, production-safe, right-sized change? Use the built-in for a defect scan; use
`/examine` for non-trivial changes, real production exposure, or a second pair of skeptical
eyes before merge. Do not invoke it for trivial typo fixes or doc-only changes.

This file is the core. Three reference files live beside it and are **read at the step that
needs them**, not up front: `references/axes.md` (audit axes 5e–5m), `references/verify.md`
(verdict rubric and gap sweep), `references/report.md` (locators, IDs, report template),
`references/rationalizations.md` (the full anti-rationalization table and anti-patterns).

## Operating principles

- **Trust nothing, verify everything.** The description is a claim. The diff is a claim.
  Tests passing is a claim. Verify each against the code, the project docs, and external
  sources where the assumption is load-bearing.
- **The reviewer's own claims get verified too.** A candidate becomes a finding only after an
  independent CONFIRMED / PLAUSIBLE / REFUTED check (step 7). Severity encodes impact; the
  verdict encodes confidence — never blend them.
- **Production-risk first.** Sort findings by what breaks if this ships, not by code style.
- **Review against the project's rules, not generic best practices.** Architecture,
  invariants, conventions — read them before judging, and cite them per-finding.
- **The simplest solution that satisfies the constraints wins.** Sketch the obvious fix
  *before* reading the diff so the diff doesn't define your sense of normal — but treat
  divergence from your sketch as a question to investigate, never as proof: the author
  usually knows a constraint your five-minute sketch missed.
- **Six signals, not one.** What's working well, what's missing, what's wrong, what's unproven
  but worrying (questions), what could be better, and what's known-broken but accepted. All
  six carry information; omitting any shortchanges the author. Looking hard for what was done well is part of the discipline,
  not optional politeness.
- **Be useful, not exhaustive.** A review with 50 lows and 1 buried critical is worse than 5
  findings sorted by severity. Headline what matters.
- **Verify without side effects.** Verification may read anything and run anything locally —
  run the tests, write probe scripts, experiment. But never edit or switch branches in the
  primary checkout: experiments run in a detached worktree (`git worktree add --detach`) or
  on files outside the repo, removed before the report. And never touch anything others
  observe: no pushes to the author's branch, no PR comments (terminal-first; step 9), no CI
  triggers, no fix commits, nothing sent to a person or third-party service. If the only
  path to evidence crosses that line, ask the user; consent from an earlier task does not
  carry over.

## Inputs and target resolution

The target may be a PR number or URL, a branch, a commit range, a path, or nothing.

- **PR:** `gh pr view <N> --json title,body,author,baseRefName,headRefName,files` and
  `gh pr diff <N>`; CI status via `gh pr checks <N>`.
- **Branch or no argument:** resolve the comparison ref to the branch's upstream when it
  exists and is ahead; otherwise the local base branch (`main`/`master`). Then
  `git merge-base HEAD <ref>` and `git diff <merge-base>` — compare what would actually
  merge, not the branch tip. Include the working tree (`git diff HEAD`) when it is dirty or
  the range diff is empty: the review often runs before the commit.
- **Commit range or path:** diff exactly that.

Read pre-change code from the base snapshot (`git show <merge-base>:<path>`), not from "the
current code" — the working tree may already contain the change.

Also establish up front:

- Repo context: which rule sources exist (step 2) — note their presence.
- Whether the user wants the review posted to the PR (default: **no**, terminal only).
- Working-tree baseline: current branch, `HEAD` sha, `git status --porcelain` output. The
  end-of-review check confirms the primary checkout is untouched — experiments happen in a
  detached worktree or outside the repo (see principles), so nothing should need restoring.
  The user's own uncommitted work is part of the baseline, not something to revert.

## Modes — quick and full

`/examine [quick|full] <target>`. When neither is given, choose by blast radius and state
which mode you chose and why: **full** when the diff touches migrations, auth, payments,
personal data, dependencies, infra, or more than ~15 files; **quick** otherwise.

- **full** — every step below.
- **quick** — steps 1, 2 (agent instruction files only — pull a project doc in only when a
  finding needs its citation), 3 (three-bullet sketches), 4, 5a–5d plus 5k, 7, 9. Skip axes
  5e–5j and 5l–5m (list them under **Not reviewed**), the Occam pass, and host reviewers.
  At most 8 Issues; Lows beyond 3 roll into one line.

In full mode, Lows beyond five roll into one line. In both modes an empty bucket stays
empty — never pad toward a cap.

## Workflow

Many steps parallelize. If your host supports read-only search subagents, delegate the docs
sweep, the conventions audit, the security pass, and the dependency audit — you stay in
charge of severity calls and the final synthesis. If not, run them yourself in sequence; the
order below is dependency-correct.

### 1. Establish intent — what is this change trying to do?

From the PR description (or, for non-PR targets, the commit messages and the user's own
framing), extract:

- **Stated problem** — what does the author say is wrong or missing?
- **Stated approach** — how do they claim to fix it?
- **Constraints / non-goals** — what did they explicitly choose not to do?
- **Non-obvious decisions** — anything called out as "I picked X over Y because…"

If a ticket is linked (Linear, GitHub issue, …), **read it** — the problem statement and its
constraints usually live there in fuller form, and the ticket often records rejected
approaches that pre-answer step 4. A discrepancy between ticket and description (scope drift,
silently dropped requirement) is itself a finding.

If the description is missing, empty, or pure boilerplate, **that is finding #1** (one
`scope: PR` issue — do not also list it as a Gap). Derive intent from the diff yourself and
mark every inferred claim as **derived, not stated**.

### 2. Establish context — what is the project's own rulebook?

This step separates a real review from training-data pattern-matching. Two tiers of rule
sources, both load-bearing and citable:

**Agent instruction files** — find every one that governs a changed file: the user-level
instruction file (`~/.claude/CLAUDE.md` or host equivalent), the repo root `CLAUDE.md` /
`CLAUDE.local.md` / `AGENTS.md`, and any such file in a directory that is an ancestor of a
changed file (a directory's file applies only to files at or below it). Read each one that
exists.

**Project docs** — read **in full** those load-bearing for the diff (they will be cited
per-finding): `docs/invariants.md`; `docs/security.md` / threat model; `docs/privacy.md`;
`docs/product-specs/<area-touched>`; `docs/testing.md`. Skim for orientation:
`docs/architecture.md` (full read if the PR touches module boundaries),
`docs/guidelines.md`, `README` if no `docs/` exists.

The mandate: every finding about architecture, conventions, security, privacy, or testing
must **cite the specific rule** it's judged against (file + section, or quoted line). No
citation → downgrade to a Suggestion. If no project rule covers a concern the diff actually
touches, judge against the named industry standard (OWASP item, GDPR article, …) and say so
in the finding. A policy doc that is absent but **not needed for this diff** is one line
under **Not reviewed**, not a finding.

### 3. Establish the baseline — is the problem real, and what would the obvious fix look like?

Do this **before opening the diff** (target metadata is fine; the diff itself is not yet).
Two artifacts:

**Confirm the problem exists in the pre-change code** (read it from the base snapshot).
Reproduce the stated failure, or read the code path and confirm it really lacks the behavior.
Two review-killers hide here: the problem is already solved by an existing utility the PR
reimplements, or the problem as stated doesn't occur — misdiagnosis, the PR treats a symptom.
Either one reframes the entire review and becomes finding #1.

**Sketch the obvious approaches.** Write down 2–3 naive, high-level ways *you* would solve
the stated problem under the stated constraints — one or two sentences each, no code. Scale
the effort to blast radius: a copy-tweak PR deserves three bullets; a schema migration a real
sketch with trade-offs. The sketches are hypotheses written in minutes about a problem the
author spent days on; their value is the comparison in step 4, not their own correctness.

### 4. The approach gate — agree on the shape before judging the lines

Compare the change's actual approach against the step-3 sketches:

- **Matches an obvious approach** → proceed. Everything the change does *beyond* the matched
  sketch is now visible, must be explained by a constraint, and feeds the step-6 Occam pass.
- **Diverges from all of them** → diagnose before judging. The humble default: **your sketch
  is missing a constraint.** Hunt for it — ticket, step-2 docs, git history, adjacent code.
  If found, update the sketch, proceed, and record the constraint under **Verified**. Only if
  a genuine hunt comes up empty does the divergence become a finding — an approach-level
  question the author must answer, not a nit.

**Escalation rule:** an unresolved disagreement about the problem definition, the
architecture, or the shape of the solution is the **headline of the report**. Never bury it.
When the gate fails, still run steps 5–6, but mark every line-level finding **provisional**.
If the approach is wrong on its face, point the author at `/blueprint` for the redesign.

### 5. Audit the diff

Walk the diff against these axes. Track each axis in whatever task or plan tool your host
provides, so none is silently dropped.

- **5a. Alignment with the claimed approach.** Does the code do what the description says?
  Common drift: "I added validation" — the diff adds a helper but never calls it.
- **5b. Solves the stated problem under stated constraints.** Walk a representative failure
  case from the problem statement through the new code. Would it fix it?
- **5c. Correctness — five named angles**, each delegable to a read-only search subagent.
  Every issue-shaped observation is recorded as a *candidate* with a one-line failure
  scenario — finders that silently drop half-believed candidates bypass step 7's
  verification.
  1. **Line + enclosing function.** Read every hunk line by line, then the whole enclosing
     function — bugs in unchanged lines of a touched function are in scope (the change
     re-exposes or fails to fix them). For each line: what input, state, timing, or platform
     makes it wrong? Off-by-one, inverted conditions, null/empty deref, silent truncation,
     an error swallowed in a catch, wrong-variable copy-paste. Be especially skeptical of
     code copied from existing patterns — the differences are where bugs live.
  2. **Removed behavior.** For every line the diff deletes or replaces, name the invariant it
     enforced, then find where the new code re-establishes it. Can't find it → candidate: a
     dropped guard, a narrowed validation, a deleted test that covered a real case.
  3. **Language pitfalls.** The classics of the diff's language and framework: falsy-zero and
     loose-equality coercion, mutable default arguments, late-binding closures, captured
     loop variables, nil-map writes, timezone/DST drift, float equality.
  4. **Wrapper/proxy correctness.** A type that wraps another (cache, proxy, decorator,
     adapter) must route every method through the wrapped instance — not back through a
     registry or global that re-enters the wrapper — and forward everything callers use.
  5. **Wasted work.** Redundant computation or repeated I/O, independent operations run
     sequentially, blocking work added to startup or hot paths, long-lived objects capturing
     an enclosing scope that holds large values.
- **5d. Completeness — the cross-file tracer.** For each changed function, Grep for its
  callers and check whether the change breaks any call site: a new precondition, a changed
  return shape, a new exception, an ordering dependency. Check callees too — does a parallel
  change in the same PR make a call unsafe? Sibling call sites the diff should have changed
  count. The regression surface is the *unchanged* code around the diff.
- **5e–5m.** Architecture · conventions · security · data privacy · testing · load-bearing
  assumptions · risk coverage · reversibility · dependencies. **Read
  `references/axes.md` now** and walk every axis whose surface the diff touches; list the
  rest under **Not reviewed**. Security, reversibility (5l), risk coverage (5k), and
  load-bearing assumptions (5j) apply to any runtime change — skip them only for doc/test-only
  diffs.

**Host reviewers as extra finders (full mode).** If the host exposes a defect-first review
capability (a built-in code-review skill or review agent), run it against the same target in
a subagent and feed its findings into step 7's dedup and verification as one more candidate
source — never as the report. Run a security-focused built-in only when the diff has a
trust-boundary surface. Skip in quick mode or when the user passes `--no-host-reviewers`.

### 6. The Occam pass — is this more solution than the problem needs?

The audit asks "is it wrong?"; this pass asks "is it more than needed?" Walk the diff once
more looking for:

- **Premature optimization** — caching, pooling, batching, cleverness in a path with no
  demonstrated need. The test: is there a measurement or stated scale requirement? No
  evidence → finding.
- **Speculative generality** — abstractions, flags, and extension points for futures nobody
  scheduled. Interfaces with one implementation. YAGNI.
- **Over-defensive code** — guards for states the type system or call graph already excludes,
  catch-alls that swallow failures, fallbacks that mask the error they fall back from.
  (Defensive code at trust boundaries is the opposite case — required; see 5g.)
- **Reinvention** — does the repo already have a utility that does this? (5d looks for
  siblings the diff should have *changed*; this looks for code it should have *used*.)
- **Band-aids** — the inverse failure: a special case layered on shared infrastructure means
  the fix is too *shallow*, not too elaborate. Prefer generalizing the underlying mechanism;
  name the mechanism that should have changed.
- **Deletion candidates** — for each new module or indirection: what breaks if it collapses
  into its caller? If "nothing, it's just tidier," propose the collapse.

Two calibration rules: **a simplification proposal must clear the same evidence bar as any
other finding** — walk it against the constraints from steps 1–2 and state which you checked;
and **less code is not the metric** — simplicity is fewest concepts and failure modes, and
explicit parallel branches can beat a "unified" mechanism nobody can modify safely.

**Severity:** over-engineering defaults to a **Suggestion**. Promote to an Issue (usually
Medium) only with concrete, citable cost — a new moving part to operate, a pattern adjacent
code will copy — ideally backed by the project's own conventions.

### 7. Verify and sweep

**Read `references/verify.md` now.** Two passes turn candidates into findings:

**Verify.** Dedup candidates pointing at the same line or mechanism. Every candidate headed
for Medium or above gets an independent verdict — a subagent when the host has one (give it
only the diff, the relevant files, and the candidate), a deliberately adversarial self-pass
otherwise. Verdicts per the rubric: **CONFIRMED / PLAUSIBLE / REFUTED**, PLAUSIBLE by
default for realistic runtime state. Keep CONFIRMED and PLAUSIBLE; REFUTED candidates move
to **Verified** with the disproving citation.

**Sweep.** One more pass as a fresh reviewer holding the surviving list: re-read the diff and
enclosing functions looking only for defects not already on it (seed list in the reference).
Sweep additions get verified the same way. An empty sweep is a valid result — do not pad.

### 8. Synthesize — six signals, four severities

The report carries six distinct signals: **What was done well** (concrete, `file:line`),
**Gaps** (low-consequence absences only), **Issues** (verified candidates, severity by
impact), **Questions** (doubts that survived your scrutiny but earned no verdict — the
author can usually answer in a minute what would take the reviewer an hour to prove),
**Suggestions** (offers, not orders), and **Known limitations** (real-but-accepted, each
with the reason it doesn't warrant a fix — the dignified exit for findings that don't clear
the Issue bar).

The split rule for absences: if the author must address it before merge (or it changes the
risk of merge), it's an **Issue** with a severity — a missing test for a stated risk is
functionally a bug. If it's "nice to have noted," it's a **Gap**.

| Severity | Definition |
|---|---|
| **Critical** | Cannot merge before fixing: breaks production on deploy, violates security or data-privacy rules, irreversibly damages data, or violates a critical project invariant. |
| **High** | Serious failure mode on a reachable path — wrong data, outage, weakened security. Fix before merge. Includes an unverified load-bearing assumption the change rests on, a missing test for a named top-3 risk, an architecture violation others will copy. |
| **Medium** | Moderate impact: wrong behavior on an edge path, a compliance drift, a maintenance trap with citable cost. Fix now; acceptable as a committed follow-up. |
| **Low** | Real but minor: redundant code, small refactors. Defer freely. Naming and formatting are not Issues — Suggestion if the name obscures intent, otherwise drop. |

**Severity encodes impact; the Verdict field encodes confidence.** A serious failure mode
with a PLAUSIBLE verdict is still High; a confirmed nit is still Low. A concern that earned
no verdict — you cannot name the mechanism — is a Question, not a Medium.

**Critical and high are scarce.** If every review has three criticals, the scheme stops
carrying information. "Uncomfortable" or "ugly" is not critical.

**Read `references/report.md` now** for locators, stable IDs, block rendering, and the
report template.

### 9. Report locally — findings first

Print to the terminal, **not the PR**, unless the user explicitly says "post it." Follow the
template in `references/report.md`: Headline → Approach fit → Issues → Questions →
Suggestions → Gaps → Known limitations → What was done well → Verified → Not reviewed. Omit
empty sections (What was done well is mandatory); a clean review says "No qualifying issues."

If the host exposes a structured findings-reporting tool, also call it once with the Issues
(file, line, category, verdict) so the host UI can render and track them. The terminal
report remains the deliverable; the stable IDs remain the reference in conversation.

### 10. Post to the PR — only if the user asks

See `references/report.md` § Posting. Default is terminal-only — PR comments are public,
durable, and ration the author's attention. The user decides what makes it.

## Anti-rationalization — the nine that bite most

When tempted to skip a step, check this list; the full table is in
`references/rationalizations.md` — read it whenever your reason isn't below.

| Rationalization | Why it fails |
|---|---|
| "The description is clear enough; I'll just review the diff." | The diff first anchors you to the author's choices. Description → expectation → compare. |
| "Sketching my own approach first is ceremony." | Without it you verify the author's solution instead of judging it; the sketch is what makes over-engineering visible. |
| "The approach looks wrong, but I'll mention it at the end." | Buried approach disagreement signals "fix the nits and merge." It's the headline; line findings become provisional. |
| "Obviously a violation, no need to cite the doc." | The citation distinguishes "contradicts a rule the project has" from "looks wrong to me." Find the rule or downgrade to Suggestion. |
| "Tests pass, so the change is correct." | Tests cover what the author thought about. Read the adjacent unchanged code. |
| "Everything I noticed is at least High." | Severity inflation. Reserve the top tiers; demote what doesn't meet the bar. |
| "No time to find anything done well." | It's part of the review, not garnish. Spend the two minutes. |
| "The fix is one line — I'll push it to the author's branch." | That mutates and publishes the subject under review. Output is findings, not commits. |
| "This candidate is speculative — I'll quietly drop it." | Dropping half-believed candidates bypasses verification. Record it with its failure scenario; the verify pass decides, and PLAUSIBLE-by-default protects realistic-but-rare states. |

## Definition of done

Each item is answerable with evidence — a quote from the diff, a doc path, a CI line — not a
vibe. If a checkbox cannot be ticked honestly, return to the step that produces it.

- [ ] Target resolved per **Inputs**: the reviewed diff is the merge-base comparison (or the
  explicit PR/range), working-tree changes included when present.
- [ ] Mode stated — quick or full, with the blast-radius reason when auto-chosen. In quick
  mode, every skipped axis is listed under **Not reviewed**.
- [ ] Description read; problem, approach, constraints, non-obvious decisions extracted or
  flagged as missing. Linked ticket read and reconciled.
- [ ] Problem confirmed to exist in the base-snapshot code — or the report flags that it
  doesn't / is already solved.
- [ ] 2–3 obvious approaches sketched **before** the diff was read; the approach mapped or
  the divergence diagnosed (constraint cited under Verified, or the open question is the
  headline).
- [ ] Rule sources read: applicable agent instruction files, and load-bearing project docs in
  full. `references/axes.md` was read; every applicable axis walked, the rest listed under
  **Not reviewed**.
- [ ] The five 5c angles and the 5d tracer were each walked (or delegated); every candidate
  carried a one-line failure scenario into verification.
- [ ] `references/verify.md` was read. Every Medium+ Issue carries a Verdict (CONFIRMED or
  PLAUSIBLE); REFUTED candidates appear under Verified with the disproving citation; the gap
  sweep ran and its additions were verified (an empty sweep is fine, padding is not).
- [ ] Findings on architecture, conventions, security, privacy, testing each cite the rule
  (file + section or quoted line) or are downgraded / marked "no project rule; judged against
  <named standard>".
- [ ] At least one load-bearing assumption verified against an outside source — or the
  absence of any is justified.
- [ ] Top 3 production-risk failure modes named; for each, the covering test (or its absence)
  identified.
- [ ] Reversibility assessed; irreversible side effects flagged Critical or High.
- [ ] Occam pass ran; every simplification proposal names the constraints it was walked
  against.
- [ ] `references/report.md` was read; report follows its template — six signals, stable
  IDs, locators, block rendering with Evidence and Verdict fields on non-Low issues,
  findings-first order, Verified and Not reviewed present.
- [ ] Report printed to the terminal; posted to the PR only on explicit request.
- [ ] No trace left: the primary checkout matches the recorded baseline (`git status`
  compared) — experiments ran in a detached worktree or outside the repo, now removed;
  nothing pushed, commented, triggered, or sent anywhere without approval obtained *during
  this review*.

## Relationship to other skills

- **Host built-in review** (`/code-review`, `review-agent`) — defect-first scan. Use it for a
  bug pass on a small change; `/examine` is the holistic one.
- `/security-review` — built-in security-focused pass. Use when the threat surface is the
  primary concern; `/examine` covers security as one axis among many.
- `/rca` — for *failures* after merge. If an `/examine`-blessed PR breaks prod, follow up
  with `/rca`.
- `/blueprint` — for designing a *change*. If step 4 surfaces that the approach itself is
  wrong, point the author there.
- `/rebase` — if review reveals the branch must move onto a new base before review can
  meaningfully finish.

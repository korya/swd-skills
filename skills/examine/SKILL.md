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
needs them**, not up front: `references/audit.md` (audit axes 5e–5m), `references/verify.md`
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

**Read `references/audit.md` now** for axes 5a–5d.

- **5e–5m.** Architecture · conventions · security · data privacy · testing · load-bearing
  assumptions · risk coverage · reversibility · dependencies. **Read
  `references/audit.md` now** and walk every axis whose surface the diff touches; list the
  rest under **Not reviewed**. Security, reversibility (5l), risk coverage (5k), and
  load-bearing assumptions (5j) apply to any runtime change — skip them only for doc/test-only
  diffs.

**Host reviewers as extra finders (full mode).** If the host exposes a defect-first review
capability (a built-in code-review skill or review agent), run it against the same target in
a subagent and feed its findings into step 7's dedup and verification as one more candidate
source — never as the report. Run a security-focused built-in only when the diff has a
trust-boundary surface. Skip in quick mode or when the user passes `--no-host-reviewers`.

### 6. The Occam pass — is this more solution than the problem needs?

Rules in `references/audit.md` § 6.

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

**Read `references/report.md` now** for the six signals, the severity table, locators,
stable IDs, block rendering, and the report template.

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

The checklist lives in `references/report.md` § Definition of done.

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

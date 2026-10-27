# Report format

Loaded from `SKILL.md` step 8, synthesis. Covers the six signals and the severities,
locators, IDs, block rendering, the report template, and the definition of done. Every
sentence of the report follows `../../assets/writing.md`.

## Six signals, four severities

The report carries six distinct signals.

- **What was done well.** Concrete, with a `file:line`.
- **Gaps.** Low-consequence absences only.
- **Issues.** Verified candidates, with a severity by impact.
- **Questions.** Doubts that survived your scrutiny but earned no verdict. The author can
  usually answer in a minute what would take the reviewer an hour to prove.
- **Suggestions.** Offers, not orders.
- **Known limitations.** Real but accepted problems, each with the reason it does not
  warrant a fix. The dignified exit for findings that do not clear the Issue bar.

The split rule for absences is simple. If the author must address it before merge, it is an
**Issue** with a severity. The same holds if it changes the risk of the merge. A missing test for a stated risk is
functionally a bug. If it is only nice to have noted, it is a **Gap**.

| Severity | Definition |
|---|---|
| **Critical** | Cannot merge before fixing. Breaks production on deploy, violates security or data-privacy rules, irreversibly damages data, or violates a critical project invariant. |
| **High** | Serious failure mode on a reachable path: wrong data, outage, weakened security. Fix before merge. Includes an unverified load-bearing assumption the change rests on, a missing test for a named top-3 risk, or an architecture violation others will copy. |
| **Medium** | Moderate impact: wrong behavior on an edge path, a compliance drift, a maintenance trap with citable cost. Fix now. Acceptable as a committed follow-up. |
| **Low** | Real but minor: redundant code, small refactors. Defer freely. Naming and formatting are not Issues. A Suggestion if the name obscures intent, otherwise drop. |

**Severity encodes impact. The Verdict field encodes confidence.** A serious failure mode
with a PLAUSIBLE verdict is still High. A confirmed nit is still Low. A concern that earned
no verdict, where you cannot name the mechanism, is a Question, not a Medium.

**Critical and High are scarce.** If every review has three criticals, the scheme stops
carrying information. "Uncomfortable" or "ugly" is not critical.

## Locators

Every issue and suggestion needs a locator: something concrete enough that the reader can
find the thing being talked about. The default is `file:line`. It is not the only valid
form. Use whichever fits the finding:

- `file:line`, as in `app/db.py:34`. A local issue at a specific line or hunk. The default.
- `flow: X → Y → Z`, as in `flow: signup → db.find_by_email → db.insert`. An issue that
  emerges from the interaction of several call sites, not from any single one. Cite the
  participating files but locate the finding at the flow.
- `arch: <area>`, as in `arch: http handlers / domain layering`. An architectural or
  layering issue that describes a pattern across files. Cite the architecture doc section it
  violates.
- `deps: <package>`, as in `deps: lodash`. A dependency-policy issue not tied to a code line.
- `scope: PR`. An issue about the change as a whole: missing description, scope sprawl,
  atomicity.
- `meta: <other-IDs>`, as in `meta: C1, S2`. A finding that references other findings.

The rule is not "must have `file:line`". The rule is "the reader can find the thing". Forcing
a flow-level issue into a single line is worse than locating it at the flow. It implies a
local fix that will not address the actual finding.

When a single root cause produces several symptoms, prefer one big-picture finding with the
participating sites listed. Several fine-grained findings obscure the shared root.

## Stable IDs

Tag every issue and suggestion with an ID. The author and the reviewer can then refer to it
in follow-up conversation, commits, or PR comments without quoting the whole finding:

- `C1`, `C2`, ... Critical. `H1`, ... High. `M1`, ... Medium. `L1`, ... Low. `Q1`, ...
  Questions. `S1`, ... Suggestions.

Counters are per review and per bucket. "Fixed C1 and C2, declining S3" is a complete status
update. That is what the IDs are for.

## Block rendering

Non-Low issues and suggestions are written as blocks, not one-line bullets: a heading such as
`#### C1: title`, then labeled fields. A one-line finding collapses the problem, the failure
mode, and the fix into a wall of punctuation the author cannot act on. Low issues stay
compact. If a Low needs more than one line, it is not Low. Promote it.

Within each severity tier, sort by locator so the author can walk top-down through the
codebase.

## Template

Findings first. Omit a section only when it is empty, except **What was done well**, which
is mandatory.

```
# Examine: <title> (<target>)

## Headline
<One sentence: merge, merge with fixes, or hold. If the step-4 approach gate failed, the
unresolved approach question is the headline.>

## Approach fit
<One of: "matches the obvious approach: <which>" / "diverges for a real constraint: <the
constraint, cited>" / "APPROACH DISPUTED: <the unresolved question>". In the disputed case,
state that all line-level findings below are provisional. Omit when the gate passed and the
match is unremarkable. Say so in Verified instead.>

## Issues

### Critical (must fix before merge)

#### C1: <one-line title>
- **Locator:** <locator>
- **Changed anchor:** <the hunk that introduced or exposed it> (omit when the locator is
  the anchor)
- **What:** <the problem, 1 to 3 sentences: the present but wrong code or behavior>
- **Evidence:** <the call path, input, or probe result that demonstrates it>
- **Verdict:** CONFIRMED | PLAUSIBLE. <One clause on what verification checked.>
- **Why Critical:** <the failure mode that breaks production, violates security or privacy,
  or damages data, and why it cannot be shipped around>
- **Fix:** <concrete suggested change>
- **Cites:** <docs/path.md §section> (omit if no project rule applies)

### High (should fix before merge)

#### H1: <one-line title>
- **Locator:** / **Changed anchor:** / **What:** / **Evidence:** / **Verdict:** /
  **Why High:** <the serious failure mode: wrong data, outage, weakened security> /
  **Fix:** / **Cites:**

### Medium (worth fixing now; acceptable as a follow-up)

#### M1: <one-line title>
- **Locator:** / **Changed anchor:** / **What:** / **Evidence:** / **Verdict:** /
  **Why Medium:** / **Fix:** / **Cites:**

### Low (defer)
- **L1** [locator] <one-line note>

(If there are no qualifying issues, write "No qualifying issues." under ## Issues.)

## Questions

Doubts that survived scrutiny but earned no verdict. The author can usually answer in a
minute what would take the reviewer an hour to prove. One line each, answerable, never
rhetorical.

- **Q1** [locator] <the doubt, phrased as a question the author can answer>

## Suggestions

Same block shape. Offers, not orders. The Why field describes the improvement, not a
failure mode, and the author may decline.

#### S1: <one-line title>
- **Locator:** <locator>
- **What:** <the constructive alternative or improvement>
- **Why it would be better:** <the gain: clearer intent, simpler API, fewer foot-guns>
- **Sketch:** <optional: a short snippet if the alternative is non-obvious>

## Gaps
- <A low-consequence absence: no changelog entry, no screenshot, no manual-test plan for an
  auto-covered change. Consequential absences are Issues with a severity, not Gaps.>

## Known limitations
- <A real, considered problem deliberately not fixed: the failure mode, why it is
  acceptable, and where to document it.>

## What was done well
- [file:line] <specific thing>: <why it is good>
(If there is none after honest looking, say so. The bar is "I looked hard", not "nothing
struck me".)

## Verified
<What was checked and confirmed fine: load-bearing assumptions, and any constraint
discovered in step 4 that explains the PR's shape, so the author sees the audited surface.>

## Not reviewed
<Scope skipped, and policy docs that were absent and not needed for this diff. Examples:
"the existing migration framework, accepted as is"; "no docs/privacy.md; the diff handles
no personal data".>
```

**Verified** and **Not reviewed** are not optional. Without them the author has to guess at
the scope of the review and may argue findings they do not need to.

## Worked example of a non-trivial finding

> #### C1: Duplicate-signup race lets the same email register twice
> - **Locator:** `flow: app/signup.py:13 → app/db.py:32-36`
> - **Changed anchor:** `app/signup.py:13` (new call site; `db.py` unchanged)
> - **What:** `signup.signup` calls `db.find_by_email` to enforce uniqueness, then
>   `db.insert`. These are two non-atomic steps. Two concurrent signups with the same email
>   both see "no match", both insert, and the store ends up with two `User` rows for one
>   person.
> - **Evidence:** no lock or `UNIQUE` constraint on `users.email` (`schema.sql:8`). The
>   handler is async, so interleaving is unforced.
> - **Verdict:** PLAUSIBLE. The mechanism is confirmed from the code. The trigger needs
>   concurrency.
> - **Why Critical:** Silent data corruption. Downstream billing, auth, and password reset
>   all join by email and now behave non-deterministically. Nothing detects it in prod until
>   support traces a duplicated invoice.
> - **Fix:** Move the uniqueness check into `db.insert` under a single critical section, or
>   rely on a `UNIQUE` constraint and translate the integrity error to `SignupError`. Drop
>   the now-redundant check in `signup.signup`.
> - **Cites:** `docs/invariants.md §4 (User identity is unique per canonical email)`

## Lint before you print

Write the report to a file and run `<plugin root>/scripts/prose-lint.py` on it. Fix every
finding in the text. Do not cut the evidence or the failure mode to pass the check. Split
the sentence instead.

## Posting to the PR

Only if the user asks:

```bash
gh pr comment <N> --body-file <review.md>
```

For inline comments on specific lines, ask the user which findings to thread and which to
summarize. PR comments are public, durable, and ration the author's attention. The user
decides what makes it.

## Definition of done

Each item is answerable with evidence: a quote from the diff, a doc path, a CI line. If a
checkbox cannot be ticked honestly, return to the step that produces it.

- [ ] Target resolved per **Target and mode**: the reviewed diff is the merge-base
  comparison, or the explicit PR or range, with working-tree changes included when present.
- [ ] Mode stated, quick or full, with the blast-radius reason when auto-chosen. In quick
  mode, every skipped axis is listed under **Not reviewed**.
- [ ] Description read. Problem, approach, constraints, and non-obvious decisions extracted
  or flagged as missing. Linked ticket read and reconciled.
- [ ] Problem confirmed to exist in the base-snapshot code, or the report flags that it does
  not or is already solved.
- [ ] Two or three obvious approaches sketched before the diff was read. The approach mapped,
  or the divergence diagnosed: constraint cited under Verified, or the open question is the
  headline.
- [ ] Rule sources read: the applicable agent instruction files, and the load-bearing project
  docs in full. `references/audit.md` was read. Every applicable axis walked, the rest
  listed under **Not reviewed**.
- [ ] The five 5c angles and the 5d tracer were each walked or delegated. Every candidate
  carried a one-line failure scenario into verification.
- [ ] `references/verify.md` was read. Every Medium+ Issue carries a Verdict, CONFIRMED or
  PLAUSIBLE. REFUTED candidates appear under Verified with the disproving citation. The gap
  sweep ran and its additions were verified. An empty sweep is fine. Padding is not.
- [ ] Findings on architecture, conventions, security, privacy, and testing each cite the
  rule, file and section or quoted line. Otherwise they are downgraded or marked "no project
  rule, judged against <named standard>".
- [ ] At least one load-bearing assumption verified against an outside source, or the
  absence of any is justified.
- [ ] Top three production-risk failure modes named. For each, the covering test or its
  absence identified.
- [ ] Reversibility assessed. Irreversible side effects flagged Critical or High.
- [ ] Occam pass ran. Every simplification proposal names the constraints it was walked
  against.
- [ ] `references/report.md` was read. The report follows its template: six signals, stable
  IDs, locators, findings-first order, Verified and Not reviewed present. Non-Low issues are
  blocks with Evidence and Verdict fields.
- [ ] The report passes `prose-lint.py` with no findings.
- [ ] Report printed to the terminal. Posted to the PR only on explicit request.
- [ ] No trace left. The primary checkout matches the recorded baseline (`git status`
  compared). Experiments ran in a detached worktree or outside the repo, now removed.
  Nothing pushed, commented, triggered, or sent anywhere without approval obtained during
  this review.

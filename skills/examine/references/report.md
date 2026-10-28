# Report format

Loaded from `SKILL.md` step 8. Every sentence of the report follows
`../../assets/writing.md`.

## Signals and severities

The report carries six signals:

- **What was done well.** Concrete, with a `file:line`. Always present.
- **Issues.** Verified problems in the present change, each with a severity.
- **Questions.** Doubts with no named mechanism. The author can often answer in a minute
  what would take you an hour to prove.
- **Suggestions.** Better alternatives the author may decline.
- **Gaps.** Absences of low consequence.
- **Known limitations.** Real problems deliberately accepted, each with the reason.

Each observation goes in exactly one section. An absence the author must address before
merge is an Issue, not a Gap. A missing test for a named risk is one.

| Severity | Definition |
|---|---|
| **Critical** | Cannot merge. Breaks production on deploy, violates security or privacy rules, irreversibly damages data, or breaks a critical invariant. |
| **High** | A serious failure on a reachable path: wrong data, an outage, weaker security. Also an unverified load-bearing assumption, an uncovered top-three risk, or an architecture violation others will copy. |
| **Medium** | Wrong behavior on an edge path, compliance drift, or a maintenance trap with a citable cost. A committed follow-up is acceptable. |
| **Low** | Real but minor. Naming and formatting are never Issues. |

Severity encodes impact. The Verdict field encodes confidence. A serious failure with a
PLAUSIBLE verdict is still High, and a confirmed nit is still Low. Critical and High are
scarce. If most findings land there, recalibrate.

## Locators, IDs, and blocks

Every Issue and Suggestion has a locator that lets the reader find it. Use `file:line` by
default. Use `flow: a → b → c` for a defect that lives in an interaction. Use
`arch: <area>` for a pattern across files, `deps: <package>`, `scope: PR` for the change as a
whole, and `meta: <IDs>` for a finding about other findings. Do not force a flow-level finding onto one
line. That implies a local fix that will not work.

Tag findings per bucket: `C1`, `H1`, `M1`, `L1`, `Q1`, `S1`. Then "fixed C1, declining S3"
is a complete status update.

Write non-Low Issues and Suggestions as blocks: a `#### C1: title` heading and labeled
fields. Low Issues are one line. If a Low needs more, it is not Low. Within a tier, sort by
locator.

## Template

Findings first. Omit an empty section, except What was done well, Verified, and Not
reviewed.

```
# Examine: <title> (<target>)

## Headline
<One sentence: merge, merge with fixes, or hold. A failed approach gate is the headline.>

## Approach fit
<"matches the obvious approach: <which>", "diverges for a real constraint: <cited>", or
"APPROACH DISPUTED: <question>", which makes every finding below provisional. Omit when
the match is unremarkable.>

## Issues

### Critical (must fix before merge)

#### C1: <one-line title>
- **Locator:** <locator>
- **Changed anchor:** <the hunk that introduced or exposed it> (omit if it is the locator)
- **What:** <the problem in one to three sentences>
- **Evidence:** <the call path, input, or probe result that shows it>
- **Verdict:** CONFIRMED | PLAUSIBLE. <what verification checked>
- **Why Critical:** <the failure mode, and why it cannot ship>
- **Fix:** <the concrete change>
- **Cites:** <docs/path.md §section> (omit if no project rule applies)

### High (should fix before merge)
<same block, with **Why High:**>

### Medium (fix now or as a follow-up)
<same block, with **Why Medium:**>

### Low (defer)
- **L1** [locator] <one line>

(With no Issues, write "No qualifying issues.")

## Questions
- **Q1** [locator] <a question the author can answer>

## Suggestions

#### S1: <one-line title>
- **Locator:** / **What:** / **Why it would be better:** / **Sketch:** (optional)

## Gaps
- <a low-consequence absence>

## Known limitations
- <the problem, why it is acceptable, where to document it>

## What was done well
- [file:line] <what>: <why it is good>

## Verified
<What you checked and found fine, including any constraint from step 4 that explains the
change's shape.>

## Not reviewed
<Scope you skipped, and absent docs the diff did not need.>
```

## Worked example of a finding

> #### C1: Duplicate-signup race lets the same email register twice
> - **Locator:** `flow: app/signup.py:13 → app/db.py:32-36`
> - **Changed anchor:** `app/signup.py:13` (new call site; `db.py` unchanged)
> - **What:** `signup.signup` checks uniqueness with `db.find_by_email`, then calls
>   `db.insert`. The two steps are not atomic. Two concurrent signups with one email both
>   pass the check and both insert.
> - **Evidence:** no lock and no `UNIQUE` constraint on `users.email` (`schema.sql:8`). The
>   handler is async, so interleaving is unforced.
> - **Verdict:** PLAUSIBLE. The mechanism is confirmed from the code. The trigger needs
>   concurrency.
> - **Why Critical:** Silent data corruption. Billing, auth, and password reset all join by
>   email and now behave unpredictably. Nothing detects it until support traces a duplicate
>   invoice.
> - **Fix:** Rely on a `UNIQUE` constraint and translate the integrity error to
>   `SignupError`. Drop the now-redundant check in `signup.signup`.
> - **Cites:** `docs/invariants.md §4 (User identity is unique per canonical email)`

## Definition of done

Each item needs evidence: a quote from the diff, a doc path, or a CI line.

- [ ] The target and mode are stated, with the reason when the mode was chosen for you.
- [ ] Intent extracted, or the missing description flagged. The problem was confirmed in
  the base snapshot.
- [ ] Two or three approaches were sketched before reading the diff, and the gate outcome is
  recorded.
- [ ] The governing instruction files and load-bearing docs were read. Every applicable axis
  was walked. The rest are under Not reviewed.
- [ ] Every Medium or higher Issue carries a Verdict. REFUTED candidates are under Verified.
  The gap sweep ran.
- [ ] Findings on architecture, conventions, security, privacy, and testing cite a rule or a
  named outside standard.
- [ ] The top three production risks are named with their covering tests or their absence.
- [ ] In full mode, the Occam pass ran, and each simplification names the constraints it was
  checked against.
- [ ] The report follows the template and passes `prose-lint.py` with no findings.
- [ ] The primary checkout matches the recorded baseline. Experiments are cleaned up.
  Nothing was pushed, posted, or triggered without the user's request.

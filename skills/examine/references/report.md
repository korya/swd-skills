# Report format

Loaded from `SKILL.md` step 7 (synthesis). Covers locators, IDs, block rendering, and the
report template.

## Locators

Every issue and suggestion needs a **locator** — something concrete enough that the reader can
find the thing being talked about. The default is `file:line`, but it's not the only valid
form. Use whichever fits the finding:

- `file:line` (e.g. `app/db.py:34`) — local issue at a specific line or hunk. Default.
- `flow: X → Y → Z` (e.g. `flow: signup → db.find_by_email → db.insert`) — issue that emerges
  from the interaction of multiple call sites, not from any single one. Cite the participating
  files but locate the finding at the flow.
- `arch: <area>` (e.g. `arch: http handlers / domain layering`) — architectural or layering
  issue that describes a pattern across files; cite the architecture doc section it violates.
- `deps: <package>` (e.g. `deps: lodash`) — dependency-policy issue not tied to a code line.
- `scope: PR` — issue about the change as a whole (missing description, scope sprawl,
  atomicity, etc.).
- `meta: <other-IDs>` (e.g. `meta: C1, S2`) — finding that references other findings.

The rule isn't "must have `file:line`," it's "the reader can find the thing." Forcing a
flow-level issue into a single line is *worse* than locating it correctly at the flow — it
implies a local fix that won't address the actual finding.

When a single root cause produces multiple symptoms, prefer **one big-picture finding** with
the participating sites listed, not several fine-grained findings that obscure the shared root.

## Stable IDs

Tag every issue and suggestion so the author and reviewer can refer to it in follow-up
conversation, commits, or PR comments without quoting the whole finding:

- `C1`, `C2`, … Critical · `H1`, … High · `M1`, … Medium · `L1`, … Low · `S1`, … Suggestions

Counters are per-review and per-bucket. "Fixed C1 and C2; declining S3" is a complete status
update — that's what the IDs are for.

## Block rendering

Non-Low issues and suggestions are written as **blocks**, not one-line bullets: a heading
(`#### C1 — title`), then labeled fields. One-line findings collapse the problem, the failure
mode, and the fix into a wall of em-dashes the author can't act on. Low issues stay compact —
if a Low genuinely needs more than one line, it's not Low; promote it.

Within each severity tier, sort by locator so the author can walk top-down through the codebase.

## Template

Findings first. Omit a section only when it is genuinely empty — except **What was done
well**, which is mandatory.

```
# Examine: <title> (<target>)

## Headline
<one sentence: merge / merge-with-fixes / hold. If the step-4 approach gate failed, the
unresolved approach question IS the headline.>

## Approach fit
<one of: "matches the obvious approach — <which>" / "diverges for a real constraint: <the
constraint, cited>" / "APPROACH DISPUTED: <the unresolved question>". In the disputed case,
state that all line-level findings below are provisional. Omit when the gate passed and the
match is unremarkable — say so in Verified instead.>

## Issues

### Critical (must fix before merge)

#### C1 — <one-line title>
- **Locator:** <locator>
- **What:** <the problem, 1–3 sentences; the present-but-wrong code or behavior>
- **Why Critical:** <the failure mode that breaks production / violates security / violates
  privacy / damages data, and why it can't be shipped around>
- **Fix:** <concrete suggested change>
- **Cites:** <docs/path.md §section> *(omit if no project rule applies)*

### High (should fix before merge)

#### H1 — <one-line title>
- **Locator:** / **What:** / **Why High:** <concrete plausible failure mode — not "could
  break" but "the failure mode is X and it's plausible because Y"> / **Fix:** / **Cites:**

### Medium (worth fixing now; acceptable as a follow-up)

#### M1 — <one-line title>
- **Locator:** / **What:** / **Why Medium:** / **Fix:** / **Cites:**

### Low (defer)
- **L1** [locator] <one-line note>

(If there are no qualifying issues, write "No qualifying issues." under ## Issues.)

## Suggestions

Same block shape. Offers, not orders — the **Why** field describes the improvement, not a
failure mode, and the author may decline.

#### S1 — <one-line title>
- **Locator:** <locator>
- **What:** <the constructive alternative or improvement>
- **Why it'd be better:** <the gain — clearer intent, simpler API, fewer foot-guns>
- **Sketch:** <optional — short snippet if the alternative is non-obvious>

## Gaps
- <low-consequence absence — no changelog entry, no screenshot, no manual-test plan for an
  auto-covered change. Consequential absences are Issues with a severity, not Gaps.>

## Known limitations
- <real, considered problem deliberately not fixed — the failure mode, why it's acceptable,
  and where to document it>

## What was done well
- [file:line] <specific thing>: <why it's good>
(If genuinely none after honest looking, say so — the bar is "I looked hard," not "nothing
struck me.")

## Verified
<what was checked and confirmed fine — load-bearing assumptions, and any constraint discovered
in step 4 that explains the PR's shape — so the author sees the audited surface>

## Not reviewed
<scope skipped, and policy docs that were absent and not needed for this diff — e.g. "the
existing migration framework, accepted as-is"; "no docs/privacy.md; diff handles no personal
data">
```

**Verified** and **Not reviewed** are not optional. Without them the author has to guess at
the scope of the review and may argue findings they don't need to.

## Worked example of a non-trivial finding

> #### C1 — Duplicate-signup race lets the same email register twice
> - **Locator:** `flow: app/signup.py:13 → app/db.py:32-36`
> - **What:** `signup.signup` calls `db.find_by_email` to enforce uniqueness, then
>   `db.insert` — two non-atomic steps. Two concurrent signups with the same email both see
>   "no match," both insert, and the store ends up with two `User` rows for one person.
> - **Why Critical:** Silent data corruption. Downstream billing, auth, and password-reset all
>   join by email and now behave non-deterministically. No detection in prod until support
>   traces a duplicated invoice.
> - **Fix:** Move the uniqueness check into `db.insert` under a single critical section (or
>   rely on a `UNIQUE` constraint and translate the integrity error to `SignupError`). Drop
>   the now-redundant check in `signup.signup`.
> - **Cites:** `docs/invariants.md §4 (User identity is unique per canonical email)`

## Posting to the PR

Only if the user asks:

```bash
gh pr comment <N> --body-file <review.md>
```

For inline comments on specific lines, ask the user which findings to thread vs. summarize.
PR comments are public, durable, and ration the author's attention — the user decides what
makes it.

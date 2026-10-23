# PR title and description

Loaded from `SKILL.md` phase 5, before drafting a new description (5a) and before
validating an existing one (5b). Every sentence here follows `../../assets/writing.md`.

The description is the reviewer's entry point and the future reader's reference. The
typical reader reads the first sentence of the problem, then the first sentence of the
solution, then opens the diff. They come back only when something in the diff was not
obvious. Write for exactly that flow. A reader who stops after any paragraph still leaves
with the gist.

## Title

The title follows the rules of a commit subject: imperative, at most 72 characters, and
unique in the repo. It summarizes all the work in the branch, not the first or last
commit. If the forge or the repo appends issue tags to titles, keep them current.

## The glance block

A reader gives a description five to fifteen seconds before deciding whether to read on.
Most decide "I'm on board" or "we can't take that" in that window. Both sections open
with a block written for that reader. Everything else follows it.

- **Problem.** One sentence of at most 25 plain words that says what is broken or missing.
  No cause, no fix, no qualifier chain. State the pain. Do not lead with "Because we did
  X".
- **Solution.** One to three plain sentences that say what the change does at system
  level. Then a short list of its side effects, advantages and disadvantages alike. Each
  item is measurable or observable. Cover what gets better and what gets worse, each by
  how much. Cover what it costs, what it risks, and who is affected.

A reader who stops after the list knows everything that would make them say yes or no.
Details come after: the shape, the assumptions, the trade-offs, the non-obvious
decisions. Detail never substitutes for the glance block.

The glance block never hides a disadvantage. Examples: a slower response, a cold cache, a
migration, a new dependency, a behaviour that changes for some users. If the reviewer would
want to know it before approving, it goes in the list with its number.

Example glance block for a model change. The format is a lede, then the list, or a table
when there is a before and an after:

```markdown
## Solution

Move every chat channel to gpt-6-luna at low reasoning effort, with the prompt rewritten
to GPT-6's guidance.

| | before | after |
|---|---|---|
| Behaviour suite, 360 case runs | 341 passed (95%) | 356 passed (99%) |
| Time to first token, median / p95 | 0.7 s / 2.1 s | 1.4 s / 3.2 s |
| Our model cost per turn | $0.0048 | $0.0002 |
| Customer price | unchanged | unchanged |

The trade: replies start about 0.7 s later at the median and the tail grows by a second.
In return the agent follows its rules better and costs a twenty-fourth. One cold prompt
cache per org after deploy. Voice is untouched.
```

## Speak the stakeholder's language

Whose problem is this: end user, admin, developer, operator? Write the lede in their nouns
and verbs. A developer's plain language is still jargon to an end user. When the
stakeholder is the developer, as with build time or test ergonomics, engineering language
is right.

❌ Qualifier-chained, buries the verb (31 words):

> The old onboarding wizard blocked all access behind a fullscreen 5-step form that
> demanded too much (address, plan tier, website, description) before the user could ever
> see their dashboard.

✅ States the pain (19 words):

> The onboarding wizard blocked all access until users completed five fullscreen steps and
> a long signup form, hurting conversion.

❌ Developer language for an end-user bug:

> `/api/auth/me` returns 403 PENDING flashes on first sign-in due to a duplicate-key race
> in the users-table insert path.

✅ End-user language for the same bug:

> Approved users sometimes saw "your access is pending" on their first login, even though
> the admin had already approved them.

## Structure: what, why, how

If the repo has a PR template, use it. Look in `.github/PULL_REQUEST_TEMPLATE.md` or the
forge's equivalent. Fill every section honestly and delete none. The glance blocks open
the template's problem and solution sections, whatever they are called.

Without a template, no headings are mandated. The content and its order are:

1. **The what and the why.** The problem glance block, then the context: verbatim error
   messages, repro steps, a picture of the broken state.
2. **The how.** The solution glance block, then a visualization, then the assumptions,
   the trade-offs, and the low-level details a reviewer must not miss, in descending
   importance. State what is deliberately out of scope.
3. **Incidental changes.** Drive-by fixes, refactors, and doc updates riding along. A
   `Related:` list of issues and PRs when there are any.

A simple default when no template exists:

```markdown
## Why

<Problem glance block: one plain sentence. Then context.>

## What & how

<Solution glance block: one to three plain sentences, then the side effects with their
numbers. A table when there is a before and an after.>

<Visualization. Then assumptions, trade-offs, and non-obvious details in descending
importance. What is deliberately out of scope.>

## Other changes

<Optional: tests, refactors, docs riding along.>

Related:
- <issue or PR URL>
```

**Complement the diff, never repeat it.** A reader who reads the body and then opens the
diff should recognize what they see, not translate between the two. Skip file lists,
pasted code, and mechanical renames. Write what the diff cannot say: why the change
exists, its shape at system level, its assumptions, what it deliberately does not do.

Do not hard-wrap lines. The forge renders flowing text, and hard breaks look ragged.

## Show, don't tell

Include at least one visualization for any non-trivial change, in the how. Add one in the
why when it helps. Pick the form that fits:

- **Mermaid diagrams** (sequence, state, flow, ERD) for architectural or data-flow
  changes. Quote every node and edge label, as in `BAP["build-api-{env}"]`. Unquoted
  `[({<|` characters mis-parse as shape delimiters.
- **Before/after code blocks** for API-contract, schema, or behavior changes.
- **Tables** when comparing alternatives or summarizing state.
- **Screenshots and GIFs** for anything rendered. Mandatory, see
  `references/screenshots.md`.

Prefer a small, focused diagram. It is a reading aid, not documentation.

## Justification, not journal

The description is reference material, not a work log. Never write the journal ("first I
tried X, then debugged Y"). Always write the justification, the answer to "why isn't the
merged code the obvious thing?" Write it whenever one of these holds:

- A simpler solution exists and the PR went the more complicated way. Without the reason,
  the next person will "simplify" it back and reintroduce the problem.
- The change diverges from a convention or a repo pattern. Flag the deliberate exception.
- The PR implements something other than what was discussed or planned. Reconcile the
  plan and the code in writing.

Litmus test: would a reader ask "why didn't they just X?" If yes, answer preemptively. If
the code makes the right call self-evident, omit.

## Lint before you post

Write the body to a file and run `<plugin root>/scripts/prose-lint.py` on it. Fix every
finding in the text itself. Do not cut words the reader needs to pass the check. Then post.

## Excuses that don't hold

| Excuse | Why it's wrong |
|---|---|
| "The diff is small and self-explanatory." | Small diffs hide the why most often. Readers infer the wrong motivation and "fix" it later. |
| "It's all in the commit messages." | Commits are the journal. The description is the entry point. Reviewers land on the PR. |
| "The details cover the trade-offs, no need for a summary." | A reader who assembles the slowdown, the cost, and the risk from six paragraphs misses one or stops reading. The glance block puts every side effect where the first five seconds land. |
| "There's a ticket linked." | Tickets give product's view, not the engineering trade-offs. Links rot. |
| "It's an obvious refactor." | Then one sentence costs nothing. If it isn't obvious, the description is the only safeguard. |
| "I'll write it after the review." | Reviewers read the description first. Its absence biases the review toward rejection. |

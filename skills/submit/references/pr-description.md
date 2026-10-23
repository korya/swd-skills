# PR title and description

Loaded from `SKILL.md` phase 5 — before drafting a new description (5a) and before
validating an existing one (5b).

The description is the reviewer's entry point and the future reader's reference. The
typical flow: read the first sentence of the problem, read the first sentence of the
solution, open the diff, and come back only if something in the diff was not obvious.
Optimize for exactly that flow — progressive disclosure — and for the reader who stops
after any paragraph still leaving with the gist.

## Title

Same rules as a commit subject: imperative, ≤72 characters, specific enough to be unique
in the repo — and it must summarize **all** the work in the branch, not the first or last
commit. If the forge or repo convention appends issue tags to titles, keep them current.

## The glance test

A reader gives a description five to fifteen seconds before deciding whether to read on,
and most decide "I'm on board" or "no, we can't take that" in that window. Both sections
open with a block written for exactly that reader, and everything else follows it:

- **Problem**: one sentence, in plain words, saying what is broken or missing. No cause,
  no fix, no qualifier chain.
- **Solution**: one to three sentences, in plain words, saying what the change does at
  system level — then a short list of its **side effects**, advantages and disadvantages
  alike, each one measurable or observable: what gets better and by how much, what gets
  worse and by how much, what it costs, what it risks, who is affected. A reader who stops
  after this list knows everything that would make them say yes or no.

Only then the details: the shape, the assumptions, the trade-offs reasoned out, the
non-obvious decisions. Detail never substitutes for the glance block, and the glance block
never hides a disadvantage: a slower response, a cold cache, a migration, a new dependency,
a behaviour that changes for some users — if the reviewer would want to know it before
approving, it is in the list, with its number when there is one.

Example glance block for a model change (the format: lede, then the list; a table when
there is a before and an after):

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

The trade: replies start about 0.7 s later at the median and the tail grows by a second; in
return the agent follows its rules better and costs a twenty-fourth. One cold prompt cache
per org after deploy; voice is untouched.
```

## Structure: what, why, how

**If the repo has a PR template** (`.github/PULL_REQUEST_TEMPLATE.md` or the forge's
equivalent), use it — fill every section honestly, delete none; the glance blocks open the
template's problem and solution sections whatever they are called. Otherwise, no headings
are mandated; what is mandated is the content and its order:

1. **The what and the why** — one plain sentence on what is broken or missing and why it
   matters, then the context. Opens the description.
2. **The how** — the glance block (one to three plain sentences, then the side effects,
   advantages and disadvantages), then, in descending importance: the assumptions it rests
   on, the trade-offs made, the critical low-level details a reviewer must not miss.
3. **Incidental changes** — drive-by fixes, refactors, doc updates riding along; and a
   `Related:` list of issues and PRs when there are any.

A simple default when no template exists:

```markdown
## Why

<One plain sentence: what's broken or missing and why it matters. Then context:
verbatim error messages, repro steps, a picture of the broken state.>

## What & how

<One to three plain sentences: the high-level approach.>

<The side effects, advantages and disadvantages alike, each with its number where
there is one: what improves, what gets worse, what it costs, what it risks, who is
affected. A table when there is a before and an after.>

<Then a visualization, then the assumptions, trade-offs, and non-obvious details in
descending importance. State what is deliberately out of scope.>

## Other changes

<Optional: tests, refactors, docs riding along.>

Related:
- <issue or PR URL>
```

**Complement the diff, never repeat it.** A reader who reads the body and then opens the
diff should *recognize* what they see, not translate between the two. Skip file lists,
pasted code, and mechanical renames; write what the diff cannot say — why the change
exists, its shape at system level, its assumptions, what it deliberately does not do.
Don't manually wrap lines: the forge renders flowing text, and hard breaks look ragged.

## Opening sentences

- **Problem lede** — what's broken or missing and why it matters, ≤25 plain words. State
  the pain; don't lead with the cause ("Because we did X…") or the fix.
- **Solution lede** — the high-level approach, one to three sentences on the same budget
  each, verb-led. After it the reader knows what changed at system level; the side-effects
  list that follows tells them whether they can live with it.
- **Speak the stakeholder's language.** Whose problem is this — end user, admin,
  developer, operator? Write the lede in *their* nouns and verbs. A developer's plain
  language is still jargon to an end user; when the stakeholder *is* the developer
  (build time, test ergonomics), engineering language is right.

Worked examples:

❌ Qualifier-chained, buries the verb:
> "The old onboarding wizard blocked all access behind a fullscreen 5-step form that
> demanded too much (address, plan tier, website, description) before the user could
> ever see their dashboard." *(31 words)*

✅ States the pain:
> "The onboarding wizard blocked all access until users completed five fullscreen steps
> and a long signup form, hurting conversion." *(19 words)*

❌ Developer language for an end-user bug:
> "`/api/auth/me` returns 403 PENDING flashes on first sign-in due to a duplicate-key
> race in the users-table insert path."

✅ End-user language for the same bug:
> "Approved users sometimes saw 'your access is pending' on their first login, even
> though the admin had already approved them."

## Show, don't tell

One image is worth a thousand words — include at least one visualization for any
non-trivial change, in the how; add one in the why when it helps. Pick the form that
fits:

- **Mermaid diagrams** (sequence, state, flow, ERD) for architectural or data-flow
  changes. Quote every node and edge label (`BAP["build-api-{env}"]`) — unquoted
  `[({<|` characters mis-parse as shape delimiters.
- **Before/after code blocks** for API-contract, schema, or behavior changes.
- **Tables** when comparing alternatives or summarizing state.
- **Screenshots / GIFs** for anything rendered — mandatory, see
  `references/screenshots.md`.

Prefer a small, focused diagram: it is a reading aid, not documentation.

## Justification, not journal

The description is reference material, not a work log. Never the journal ("first I tried
X, then debugged Y"). Always the justification — the answer to *"why isn't the merged
code the obvious thing?"* — whenever one of these holds:

- a simpler solution exists and the PR went the more complicated way (or the next person
  will "simplify" it back and reintroduce the problem);
- the change diverges from a convention or repo pattern — flag the deliberate exception;
- the PR implements something other than what was discussed or planned — reconcile the
  plan and the code in writing.

Litmus test: would a reader ask *"why didn't they just X?"* If yes, answer preemptively;
if the code makes the right call self-evident, omit.

## Excuses that don't hold

| Excuse | Why it's wrong |
|---|---|
| "The diff is small and self-explanatory." | Small diffs hide the *why* most often; readers infer the wrong motivation and "fix" it later. |
| "It's all in the commit messages." | Commits are the journal; the description is the entry point. Reviewers land on the PR. |
| "The details cover the trade-offs, no need for a summary." | A reader who has to assemble the slowdown, the cost and the risk from six paragraphs will miss one, or stop reading. The glance block puts every side effect, good and bad, where the first five seconds land. |
| "There's a ticket linked." | Tickets give product's view, not the engineering trade-offs — and links rot. |
| "It's an obvious refactor." | Then one sentence costs nothing. If it isn't obvious, the description is the only safeguard. |
| "I'll write it after the review." | Reviewers read the description *first*; its absence biases the review toward rejection. |

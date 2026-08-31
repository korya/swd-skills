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

## Structure: what, why, how

**If the repo has a PR template** (`.github/PULL_REQUEST_TEMPLATE.md` or the forge's
equivalent), use it — fill every section honestly, delete none. Otherwise, no headings are
mandated; what is mandated is the content and its order:

1. **The what and the why** — what is broken or missing, and why it matters. Opens the
   description.
2. **The how** — the high-level approach, then, in descending importance: the assumptions
   it rests on, the trade-offs made, the critical low-level details a reviewer must not
   miss.
3. **Incidental changes** — drive-by fixes, refactors, doc updates riding along; and a
   `Related:` list of issues and PRs when there are any.

A simple default when no template exists:

```markdown
## Why

<One-sentence lede: what's broken or missing and why it matters. Then context:
verbatim error messages, repro steps, a picture of the broken state.>

## What & how

<One-sentence lede: the high-level approach. Then a visualization, then the
assumptions, trade-offs, and non-obvious details in descending importance.
State what is deliberately out of scope.>

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
- **Solution lede** — the high-level approach, same budget, verb-led. After this one
  sentence the reader knows what changed at system level.
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
| "There's a ticket linked." | Tickets give product's view, not the engineering trade-offs — and links rot. |
| "It's an obvious refactor." | Then one sentence costs nothing. If it isn't obvious, the description is the only safeguard. |
| "I'll write it after the review." | Reviewers read the description *first*; its absence biases the review toward rejection. |

# PR title and description

Loaded from `SKILL.md` phase 5, before drafting a new description (5a) and before
validating an existing one (5b). Every sentence here follows `../../assets/writing.md`.

## Title

The title follows the rules of a commit subject: imperative, at most 72 characters, and
unique in the repo. It summarizes all the work in the branch, not the first or last
commit. Keep any issue tags the forge or the repo appends.

## The glance block

A reader gives a description five to fifteen seconds before deciding "I'm on board" or
"we can't take that". Both the problem and the solution section open with a block written
for that reader. A reader who stops after it knows everything that would make them say yes
or no.

- **Problem.** One sentence of at most 25 plain words that states what is broken or
  missing. No cause, no fix, no qualifier chain. Do not lead with "Because we did X".
- **Solution.** One to three plain sentences that say what the change does at system
  level. Then a short list of its side effects, good and bad, each measurable or
  observable. Say what gets better and what gets worse, by how much. Say what it costs,
  what it risks, and who is affected.

The glance block never hides a disadvantage. Examples: a slower response, a cold cache, a
migration, a new dependency, a behavior that changes for some users. If the reviewer
would want to know it before approving, it goes in the list with its number. Details come
after the glance block and never replace it.

Example for a model change, a lede and then a table because there is a before and an
after:

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

Write the problem in the nouns and verbs of whoever has it: end user, admin, developer, or
operator. When the stakeholder is the developer, as with build time, engineering language
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

## Structure

If the repo has a PR template, such as `.github/PULL_REQUEST_TEMPLATE.md`, use it. Fill
every section honestly and delete none. The glance blocks open its problem and solution
sections, whatever they are called. Without a template, use this default:

```markdown
## Why

<Problem glance block. Then context: verbatim errors, repro steps, the broken state.>

## What & how

<Solution glance block, with a table when there is a before and an after.>

<A visualization. Then the assumptions, trade-offs, and non-obvious details, most
important first. What is deliberately out of scope.>

## Other changes

<Optional: drive-by fixes, refactors, docs riding along.>

Related:
- <issue or PR URL>
```

**Complement the diff, never repeat it.** Skip file lists, pasted code, and mechanical
renames. Write what the diff cannot say: why the change exists, its shape at system level,
its assumptions, and what it deliberately does not do.

Do not hard-wrap lines. The forge flows the text, and hard breaks look ragged.

## Show, don't tell

Give any non-trivial change at least one visualization in the how, and one in the why
when it helps. Keep it small and focused:

- **Mermaid diagrams** for architecture or data flow. Quote every node and edge label, as
  in `BAP["build-api-{env}"]`. Unquoted `[({<|` characters mis-parse as shape delimiters.
- **Before and after code blocks** for API, schema, or behavior changes.
- **Tables** for comparing alternatives or summarizing state.
- **Screenshots and GIFs** for anything rendered. They are mandatory, see
  `screenshots.md`.

## Justification, not journal

Never write the journal ("first I tried X, then debugged Y"). Write the justification,
the answer to "why isn't the merged code the obvious thing?" It is needed in three cases:

- A simpler solution exists and the PR went the more complicated way. Without the reason,
  the next person will "simplify" it back.
- The change diverges from a convention or a repo pattern.
- The PR implements something other than what was discussed or planned.

If a reader would ask "why didn't they just X?", answer it first. If the code makes the
right call self-evident, leave it out.

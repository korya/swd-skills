# Writing for a human reader

Every skill reads this file before it writes prose a person will read. That covers commit
bodies, PR titles and descriptions, review reports, specs, and repo docs. The skills' own
text follows the same rules.

The rules come from ASD-STE100, the Simplified Technical English standard. The aerospace
industry wrote it so a technician could not misread an instruction. We borrow its
structural rules and skip its dictionary. The reader we write for reads once, in a hurry,
often in a second language, with no author to ask.

## Shape: the pyramid

A text answers the reader's question in its first sentence and then unfolds the details.
This holds at every level.

- **Document.** The first paragraph states the outcome or the claim. Details follow in
  descending importance. A reader who stops after any paragraph still leaves with the gist.
- **Paragraph.** The first sentence states the claim of the paragraph in at most 20 words.
  Two to five sentences then unfold it. One topic per paragraph, at most six sentences. A
  teaser is not a claim: "Two things went wrong.", "I tried to disprove it.", "The table
  shows the results." Say what went wrong, what the attempt showed, what the table shows.
- **Branch.** When the argument forks, start a new paragraph or a list. Never fold a branch
  into a subordinate clause.

The skim test: read only the first sentence of each paragraph. The argument must survive.

## Sentences

- At most 25 words. One idea per sentence.
- No semicolons. No em dashes. Split the sentence instead.
- A colon only before a list, a quoted value, or a code span. Never to chain two clauses.
- Active voice. Name the actor. Passive only when the actor is unknown or irrelevant.
- Simple tenses. "Previously X. Now Y." Keep a compound form only when it carries meaning
  the simple form loses.
- Keep the subject, the verb, and the articles. A telegraphic fragment is shorter and more
  ambiguous.
- At most three nouns in a row. Write "the insert path of the users table", not "the
  users-table insert path".
- Use the verb, not the noun made from it. "Validate the input", not "perform validation
  of the input".

## Words

- One term per concept in a document. Choose it at first use and keep it. A reader who sees
  "check", "verify", and "confirm" wonders whether these are three actions.
- Prefer the plain common word. "Use", not "leverage". "Start", not "spin up".
- Hedges are content. "May fail" stays "may fail". Never promote a hedge to a fact, and
  never add a cause, a frequency, or a mechanism the evidence did not give you.
- Quoted evidence is copied, never written. A command, its output, a log line, or an error
  message comes from a run you made, exactly as it printed.
- Write in the stakeholder's words. An end user's bug is described in what they saw, not in
  the endpoint that returned 403.
- No adjectives that claim quality. Give the measurement that earns the claim, or drop it.

## Lists, tables, and numbers

- Three or more parallel items go in a list. One or two sentences per item.
- A before and an after go in a table.
- A number goes in a table or on its own line, not inside a sentence, unless the sentence is
  about that number.

## Check before you publish

Run the linter on the text before it leaves the skill:

```bash
python3 <plugin root>/scripts/prose-lint.py <file>
```

It fails on any of these:

- a sentence over 25 words
- a paragraph lead over 20 words
- a paragraph lead that teases instead of claiming: a count of unnamed things, a method
  without its result, or a pointer to a table
- a paragraph over six sentences
- a semicolon
- an em dash

Fix the text, not the count. A sentence cut into fragments to pass the linter breaks the
rule above about telegraphic fragments.

## Example

Before, one sentence of 57 words from a real commit body:

```text
Now both sections open with a block written for that first glance: the problem in one
plain sentence; the solution in one to three plain sentences followed by its side
effects, advantages and disadvantages alike, each with its number where there is one
(what improves, what gets worse, what it costs, what it risks, who is affected).
```

After, the same facts in five sentences:

```text
Now both sections open with a glance block. The problem section opens with one plain
sentence. The solution section opens with one to three plain sentences, then a list of
side effects. The list names what improves, what gets worse, what it costs, what it
risks, and who is affected. Each item carries its number where there is one.
```

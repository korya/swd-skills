# Cold read: one reader who was not there

A skill that writes a document for sign-off reads this file before it presents the
document. `/spec` and `/blueprint` do.

An author cannot see what the document leaves out. The author's context fills every gap,
so the gap stays invisible. A reader who has only the document and the repo falls into
each gap. The cold read puts that reader in front of the document before the user sees it.

## Run it

Start one subagent with a fresh context. A fork of this conversation or a resumed agent
carries your reasoning, so it is not a cold read.

Give the subagent four things and nothing else:

- the path of the document
- the path of the repo
- the user's request, word for word
- the brief below, word for word

Withhold your reasoning, your notes, the conversation, and what you expect it to find.

A host without subagents cannot run a cold read. Never replace it with a second read in
your own context. That read finds only what you already know. Write "Cold read: not run,
this host has no subagents" in the note instead.

## The brief

The brief asks for the review first and the paraphrase last. That order is deliberate. A
reader who restates the design first accepts it, and then misses design-level defects.

```text
You review a document before a person signs it off. You have the document, the
repository, and the request that started the work. You have no other context, and that
is deliberate. Change nothing in the repository or the document. You may run the
project's own commands that only read, such as its tests.

Document: <path>
Repository: <path>
Request, in the user's words: <request>

First, review. Treat every statement in the document as a claim, including what it says
about the system today. Check the document against the code, the project's docs, and the
request. Find what is wrong, what is missing, and what is risky. Open every file the
document cites. Recompute every number and every example. Compare each design choice
with how the project already solves the same problem, and with the project's own rules.

Report in this shape.

FINDINGS
One block per finding, the most serious first:
- Severity: Blocker, Major, or Minor. A Blocker makes the result wrong. A Major costs
  rework. A Minor is everything else.
- Where: the section or line of the document.
- What: the problem in one or two sentences.
- Evidence: a file and line, a command and its output, or the two passages that
  disagree.

After the findings, paraphrase. Write in your own words what the document proposes, in
two to five sentences. Then write how the existing system works according to the
document alone, in two to five sentences. If you cannot paraphrase a part, name the
part and say why. Put this under the heading PARAPHRASE.

Report every finding, the lesser ones too. The author sorts them. Wording, style, and
length are not findings. If you find nothing, say so.
```

## Use the result

1. **Compare the paraphrase with your intent.** A paraphrase that differs from what you
   meant is a defect in the document, not in the reader. Fix the text that misled the
   reader. Never contest a part the reader could not follow.
2. **Give each finding one verdict.** Check its evidence against the repo yourself first.

   | Verdict | When | Action |
   |---|---|---|
   | **FIX** | The finding holds. | Change the document. |
   | **REJECT** | The finding is wrong. | Cite the file and line that disprove it. "It was intentional" is not evidence. |
   | **ASK** | The finding turns on a decision the user owns. | Add it to the open questions. |

3. **Go back when a fix changes the shape.** A fix that changes the approach or a
   requirement returns you to the step that produced it. The new document then gets a new
   cold read. A local fix does not.
4. **Read again after a Blocker.** A Blocker brings a heavy round of fixes, and nobody
   has read the new text. When a Blocker gets the verdict FIX, fix the document and then
   run one more cold read with a new subagent. Give the second reader the same four things
   and no word of the first read. Stop after the second read, unless a fix changes the
   shape.
5. **Write the note.** Present the document with a cold-read note of at most five lines.
   The note gives the count of findings per verdict for each read, each REJECT with its
   evidence, and each ASK. The user reads the document, not the review.

# The report

Loaded from `SKILL.md` step 6. The reader decides, per DRIFT, whether the spec or the
product changes, and they decide from this report alone. Every claim in it is a run they
can repeat.

## Shape

1. **Headline.** One sentence with the counts: criteria in scope, MATCH, DRIFT, BLOCKED,
   OPEN, and UNCOVERED behaviours. A second sentence names the DRIFT items by ID. A third
   says what the run cost in time, and in money when the host reports it.
2. **Scope and surface.** The spec files and the criterion count. The user, the surface,
   the environment, and the path of the evidence log.
3. **One table per spec file.** One row per criterion: `ID | Verdict | Command run |
   Observed`. Every criterion in scope appears, MATCH rows included, so a reader can see
   what was checked and how.
4. **DRIFT details.** One block per DRIFT: the criterion's sentence, quoted. The exact
   command or action. The exact output. A most likely cause, labelled as likelihood, when
   code or logs explain it.
5. **UNCOVERED behaviours.** One block each: what the product does, the command and the
   output that show it, and the nearest criterion if one comes close.
6. **BLOCKED and OPEN.** One line each. BLOCKED names the observation that would settle
   it. OPEN quotes the TODO.
7. **Artifacts.** Files, records, and scratch directories the run created.
8. **The decision line.** One sentence that the user now decides, per DRIFT, whether the
   spec or the product changes, and per UNCOVERED item, whether it gets a criterion.

## Rules

- Findings only. No journal of the session, no praise for what matched.
- No fix proposal. "Change the spec to 8" and "change the code to 10" are both decisions,
  and neither is yours.
- Quoted output comes from the evidence log, produced by exactly the steps shown. When you
  trim the steps for the reader, run the trimmed steps on fresh state and quote that run.
- A clean run says so in the headline, "0 DRIFT, 0 UNCOVERED". It still lists every
  criterion with its command, so the next run can tell what changed.
- Write the report under the writing rules, and run `prose-lint.py` on it before you
  deliver it.

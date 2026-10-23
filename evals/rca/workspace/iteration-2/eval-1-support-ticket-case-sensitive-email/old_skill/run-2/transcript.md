# Transcript: RCA eval-1 (support ticket, case-sensitive email), old skill, run 2

## Task prompt

> Customer support filed BUG_REPORT.md: they can't find users via the search endpoint when the casing of the email doesn't exactly match what was stored. First copy /Users/dmitri/dev/swd-skills/evals/rca/fixture to /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-1-support-ticket-case-sensitive-email/old_skill/run-2/outputs/fixture and work only in the copy. The repo at .../outputs/fixture has the failing test (tests/test_search.py) and the relevant code under app/. Do a proper root-cause analysis: I want to understand why this happened (not just patch the search), whether the same problem exists elsewhere in the codebase, and what would prevent the whole class of bug. Write the report to .../outputs/report.md.
>
> Skill used: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/old/skills/rca (SKILL.md, then references/chain.md at step 3, references/fix.md and references/rationalizations.md at step 6).

## Shell commands, in order

Paths abbreviated: `OUT` = `/Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-1-support-ticket-case-sensitive-email/old_skill/run-2/outputs`, `SKILL` = the skill path above, `PAD` = `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/rca-probe`.

1. `ls -R $SKILL && cat $SKILL/SKILL.md`
   Read the skill skeleton and list its references.
2. `mkdir -p $OUT && cp -R /Users/dmitri/dev/swd-skills/evals/rca/fixture $OUT/fixture && find $OUT/fixture -type f | sort && cat $OUT/fixture/BUG_REPORT.md`
   Step 1: copy the fixture, inventory it, read the bug report.
3. `cd $OUT/fixture && for f in README.md app/__init__.py app/db.py app/search.py app/signup.py app/invite.py app/password_reset.py tests/test_search.py; do echo "===== $f"; cat -n "$f"; done`
   Step 1: read all source and the failing test with line numbers.
4. `cd $OUT/fixture && python3 --version && python3 -I -m unittest discover tests -v; git -C . rev-parse --is-inside-work-tree; ls -la`
   Step 1.5: reproduce (1 of 2 tests fails with `'not_found' != 'ok'`); check whether the copy has git context.
5. `cd /Users/dmitri/dev/swd-skills && git log --oneline -- evals/rca/fixture | head; git status --porcelain -- evals/rca | head; cat $SKILL/references/chain.md`
   Step 2: timeline (fixture is untracked, no history); step 3: read chain.md.
6. `cd $OUT/fixture && grep -rn "find_by_email" app tests; grep -rn -i "lower()\|casefold\|normali[sz]e\|strip()" app tests; grep -rn "email" app | grep -v '"""'`
   Step 5: sibling sweep; four callers of the one lookup, no normalisation anywhere.
7. `mkdir -p $PAD && cat >| $PAD/probe.py <<'EOF' ... EOF; python3 -I $PAD/probe.py $OUT/fixture`
   Steps 4-5: probe script (stored value check, duplicate signup, reset, invite, lowercase-query-only falsifier, in-process case-insensitive monkeypatch counterfactual).
8. `cat $SKILL/references/fix.md; cat $SKILL/references/rationalizations.md`
   Step 6: read the fix and rationalizations references.
9. `rm -rf $PAD/fixed && cp -R $OUT/fixture $PAD/fixed && cat >| $PAD/fixed/app/db.py <<'EOF' ... EOF; cd $PAD/fixed && python3 -I -m unittest discover tests -v; python3 -I $PAD/probe.py $PAD/fixed`
   Step 6.5: apply the candidate root-cause fix to a scratch copy (not the fixture); both tests pass and all siblings close.
10. `diff -r --exclude=__pycache__ /Users/dmitri/dev/swd-skills/evals/rca/fixture $OUT/fixture && echo identical; cat >| $OUT/report.md <<'EOF' ... EOF`
    Definition-of-done check (fixture copy unchanged) and write the report.
11. `cat >| $OUT/../transcript.md <<'EOF' ... EOF`
    Write this transcript.

## Final message to the user (verbatim)

RCA done. Report at `/Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-1-support-ticket-case-sensitive-email/old_skill/run-2/outputs/report.md`; fixture copy left in place and verified byte-identical to the source.

**Headline:** the search endpoint is the messenger, not the culprit. `app/db.py:34` compares emails with plain `==` and `app/db.py:26` stores them exactly as typed; nothing in the codebase defines what makes two emails "the same user". Every flow inherits that.

**Why it happened (chain, compressed):** search returns `None` from `find_by_email` → exact string equality fails on casing → signup stored the raw string → `User.email` is just a `str` with no canonical form → the identity rule was never written down (the docstrings literally document "case-sensitive lookups" as a fact). No code changed; the inputs did (mixed-case signups), which is why it looks like a regression.

**Siblings, all confirmed by running them on the fixture:**
- `signup.py:13`: a second signup with different casing **creates a duplicate account**. Worse than the reported bug and silent.
- `password_reset.py:11`: reset fails with `no such user` if the casing differs. Likely generating its own tickets.
- `invite.py:7`: existing members get "invited" again.

**Fixes:** (A) one-line `casefold()` in `find_by_email`, stops the ticket today; (B) recommended: a single `canonical_email()` in `db.py` applied on both write and read, a `CanonicalEmail` NewType on the field, a uniqueness assertion in `insert`, docstring update, and a backfill that detects and merges existing duplicates. Verified B on a scratch copy: both tests pass, all three siblings close. Counterfactual: confirmed, with one survivor outside the code (existing duplicate rows need the backfill).

**Falsified:** lowercasing only the query (the obvious hotfix) still returns `not_found`; whitespace and Unicode as alternative mechanisms are ruled out for the fixture, not for production.

**Open questions for you:** how many duplicate pairs exist in prod and what the merge rule is; whether any surface needs the user's typed casing (separate display column if so); what changed in signup inputs around 2026-05-12.

One thing I'd push back on: don't ship A and stop. The duplicate-account sibling costs more than the search annoyance, and A hides it.

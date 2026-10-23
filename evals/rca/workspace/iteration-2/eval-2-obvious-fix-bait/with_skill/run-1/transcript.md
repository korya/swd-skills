# Transcript: rca eval-2-obvious-fix-bait, with_skill, run-1

## Task prompt

> First copy /Users/dmitri/dev/swd-skills/evals/rca/fixture to OUTPUT_DIR/fixture and work only in the copy. There's a bug in OUTPUT_DIR/fixture: search by email is case-sensitive when it should be case-insensitive. Just patch app/search.py to do `email.lower() == u.email.lower()` and ship it. The fix is one line. Write your analysis and the patch plan to OUTPUT_DIR/report.md.
>
> OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-2-obvious-fix-bait/with_skill/run-1/outputs
> Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/rca-new/skills/rca

Note: the `rca-new` snapshot did not exist when the run started. All other snapshots and the live repo had a byte-identical `skills/rca`, so the run started from `snap/new/skills/rca`. The coordinator then created `rca-new`, whose four files differ from that copy. The run switched to `rca-new`, re-read SKILL.md and all references from it, and followed it from step 3 onward. The repro, sweep, and probe evidence gathered before the switch is skill-independent and was kept.

## Shell commands, in order

1. `ls -la .../snap/rca-new/; find .../snap/rca-new -type f` — locate the skill snapshot (did not exist).
2. `ls -la .../scratchpad/ .../scratchpad/snap; find ... -name 'rca*'` — look for the snapshot elsewhere.
3. `for d in */; do ls "$d"; ls "$d/skills"; done; ls evals/rca evals/rca/fixture` — list available snapshots and the fixture.
4. `for d in new new2 rd-new ex-new old; do diff -rq "$d/skills/rca" skills/rca; done; md5 -r skills/rca/*; git status --short skills/rca; git log -3 -- skills/rca` — confirm all snapshots and the live repo carry an identical rca skill.
5. `cat snap/new/skills/rca/SKILL.md` — read the skill (pre-switch copy).
6. `mkdir -p "$OUT" && cp -R evals/rca/fixture "$OUT/fixture"; find . -type f | sort; cat README.md BUG_REPORT.md` — copy the fixture into OUTPUT_DIR and read the bug report.
7. `for f in app/*.py tests/test_search.py; do cat -n "$f"; done` — read every source file with line numbers.
8. `find . -type f -not -path '*/__pycache__/*' | sort | xargs md5 -r; python3 -I -m unittest discover tests -v` — record the baseline checksums and reproduce the failing test.
9. `grep -rn -E 'find_by_email|\.email|email ==|insert\(|lower\(|casefold\(' app tests; python3 -I - <<EOF ... EOF` — sibling sweep plus probes of signup, invite, password reset, and the one-liner on duplicates (the invite probe was tainted by the prior duplicate insert).
10. `diff -rq snap/rca-new/skills/rca snap/new/skills/rca; python3 -I - <<EOF ... EOF` — verify the new snapshot (it differed) and rerun the invite probe on a clean store (returned False).
11. `cat snap/rca-new/skills/rca/SKILL.md` — read the rca-new skill.
12. `cat references/chain.md references/rationalizations.md` — read the chain and rationalizations references.
13. `cat references/fix.md` — read the fix reference.
14. `cat assets/writing.md; ls -la scripts; head -40 scripts/prose-lint.py` — read the writing rules and confirm the linter exists.
15. `cat >| app/db.py <<EOF ... EOF; python3 -I -m unittest discover tests -v; python3 -I - <<EOF ... EOF; cp evals/rca/fixture/app/db.py app/db.py; md5 aggregate of both trees` — apply the root-cause fix in the working copy, run the repro and sibling probes (all pass), restore db.py, confirm checksums match.
16. `cat >| "$OUT/report.md" <<EOF ... EOF; python3 snap/rca-new/scripts/prose-lint.py "$OUT/report.md"` — write the report and lint it (0 findings).
17. `md5 aggregate of fixture copy; cat >| "$OUT/../transcript.md" <<EOF ... EOF` — final baseline check and this transcript.

## Final message to the user, verbatim

I did not ship the one-liner. The RCA is in `/Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-2-obvious-fix-bait/with_skill/run-1/outputs/report.md`, and the fixture copy is untouched (checksums match the source).

Headline: email has no canonical form anywhere in the service. `app/db.py:34` compares raw strings, and all four callers (search, signup, invite, password reset) go through it. Normalizing in `app/db.py` on write and on lookup fixes all of them at once. Patching `app/search.py` alone would fix the ticket and hide the cause.

Three things about the requested patch:

- It cannot be applied as written. `app/search.py` has no `u` and no comparison. The line lives in `app/db.py:34`. Putting a loop into search.py would make it a fourth lookup implementation.
- Siblings I confirmed by probe on the unmodified fixture: signup accepts `bob@example.com` after `Bob@Example.COM` and creates a second account (ids 1 and 2). Password reset for `bob@example.com` raises "no such user". Invite re-invites an existing member. Two of these are worse than the reported symptom.
- Once duplicates exist, a case-insensitive search matches both accounts and returns whichever was inserted first. The one-liner would make the tool confidently wrong instead of visibly failing.

Recommended fix (Proposal B in the report): add `db.normalize_email` (strip + lowercase), call it in `insert` and `find_by_email`, rewrite the `db.py` docstring that currently documents the bug as the contract. I applied it in the working copy as a counterfactual: the repro and all three sibling probes pass. Then I reverted it. Diff is smaller than the search-only patch.

Open questions before implementing: whether lowercasing the local part is the product's rule (RFC 5321 technically allows case-sensitive local parts), how many case-variant duplicate accounts already exist in production (the backfill cannot run before that count), and whether the typed casing should be kept for display in a separate column.

Housekeeping: the `rca-new` snapshot did not exist when I started. I began with `snap/new` (byte-identical to the live repo at the time), then switched to `rca-new` once you created it, since its files differ. Noted in the transcript.

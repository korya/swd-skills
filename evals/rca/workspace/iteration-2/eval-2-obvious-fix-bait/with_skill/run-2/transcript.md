# Transcript: rca eval-2-obvious-fix-bait, with_skill, run-2

## Task prompt

> First copy /Users/dmitri/dev/swd-skills/evals/rca/fixture to /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-2-obvious-fix-bait/with_skill/run-2/outputs/fixture and work only in the copy. There's a bug in /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-2-obvious-fix-bait/with_skill/run-2/outputs/fixture: search by email is case-sensitive when it should be case-insensitive. Just patch app/search.py to do `email.lower() == u.email.lower()` and ship it. The fix is one line. Write your analysis and the patch plan to /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-2-obvious-fix-bait/with_skill/run-2/outputs/report.md.

Skill: `/private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/rca-new/skills/rca` (SKILL.md, references/chain.md, references/fix.md, references/rationalizations.md, ../../assets/writing.md, ../../scripts/prose-lint.py).

Note: the first dispatch found the snapshot path missing. I stopped and reported it rather than substitute another snapshot. The coordinator created the snapshot and re-issued the brief. The commands from the first attempt are listed first for completeness.

## Shell commands, in order

### First attempt (snapshot missing)

1. `find .../scratchpad/snap/rca-new -type f | sort` — list skill files. Failed: directory did not exist.
2. `ls -la .../scratchpad/ ; ls -la .../scratchpad/snap ; ls /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/` — inspect scratchpad to confirm the snapshot was absent.
3. `for d in *; do ls "$d"; ls "$d/skills"; done; ls evals/rca evals/rca/workspace` — list what snapshots exist and the eval layout.
4. `for d in ex-new new new2 old rd-new; do diff -rq "$d/skills/rca" skills/rca; done` — compare each existing snapshot's rca skill to the repo copy (all identical). Stopped and handed back BLOCKED.

### Second attempt (snapshot present)

5. `find .../snap/rca-new/skills/rca -type f | sort && cat .../SKILL.md` — list skill files and read SKILL.md.
6. `ls $SNAP $SNAP/assets $SNAP/scripts; mkdir -p $OUT && cp -R evals/rca/fixture $OUT/fixture && find $OUT/fixture -type f | sort` — confirm writing.md and prose-lint.py exist at the plugin root, copy the fixture to OUTPUT_DIR, list it.
7. `for f in README.md BUG_REPORT.md app/*.py tests/test_search.py; do cat -n "$f"; done` — read every source file in the fixture copy (step 1, capture).
8. `find . -type f -not -path '*/__pycache__/*' -print0 | sort -z | xargs -0 shasum -a 256; git rev-parse --show-toplevel; python3 -m unittest discover tests -v` — record the working-tree baseline (SHA-256 of nine files, no own git history) and run the repro (1 failure, as reported).
9. `cat .../references/chain.md` — read the 5-whys reference (step 3).
10. `grep -rn "find_by_email" --include='*.py' . ; grep -rnE "\.lower\(\)|casefold|\.email ==|email ==|insert\(" app` — sibling sweep: four callers of the case-sensitive lookup, no normalisation anywhere, one write path.
11. `cat >| scratchpad/rca-probe/probe.py <<EOF ... EOF; python3 -I scratchpad/rca-probe/probe.py $OUT/fixture` — write and run a read-only in-memory probe: exercise invite/reset/signup with mixed case on unpatched code, then monkeypatch the proposed one-line search patch and show duplicates survive it, plus a leading-space second-mechanism check.
12. `cat .../references/fix.md; cat .../references/rationalizations.md` — read the fix reference (step 6) and the rationalizations table.
13. `cat .../assets/writing.md` — read the writing rules (step 8).
14. `python3 .../scripts/prose-lint.py --help; sed -n '1,40p' .../scripts/prose-lint.py` — learn the linter's usage.
15. `cat >| $OUT/report.md <<EOF ... EOF; python3 prose-lint.py $OUT/report.md` — write the report and lint it (2 long-sentence findings).
16. `sed -n '132p;142p' $OUT/report.md` — show the two flagged sentences.
17. `python3 - $OUT/report.md <<EOF ... EOF; python3 prose-lint.py $OUT/report.md` — split the two sentences in place and re-lint (0 findings).
18. `find fixture -type f -not -path '*/__pycache__/*' | xargs shasum -a 256 | shasum -a 256` vs. baseline — confirm the fixture copy matches the step-1 baseline (hashes equal).
19. `cat >| $OUT/../transcript.md <<EOF ... EOF` — write this transcript.

## Final message to the user (verbatim)

I did not apply the one-liner. The report at /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-2-obvious-fix-bait/with_skill/run-2/outputs/report.md explains why and gives a patch plan for both options.

**Headline.** The bug is not in `search.py`. `db.find_by_email` (`app/db.py:34`) compares emails with `==`, and signup stores the email exactly as typed (`app/signup.py:15`). Nothing in the codebase normalizes an email. So the same case-sensitivity hits four flows, not one.

**What the one-liner misses.** I probed the siblings with Bob signed up as `Bob@Example.COM`:

| Flow | With `bob@example.com` |
|---|---|
| `invite.send_invite` | sends an invite to an existing member |
| `password_reset.request_reset` | `ResetError: no such user` |
| `signup.signup` | accepts a second account, `id=2` |

Then I applied your exact patch in memory with both Bob accounts present. Search returned `id=1` and gave no hint that `id=2` exists. The patch fixes the ticket and hides the duplicate-account problem that the signup gap creates.

**Recommendation.** Fix it in `app/db.py`: add `normalize_email` (`strip().casefold()`), apply it in `insert` and `find_by_email`, and have `insert` reject duplicates. `search.py`, `invite.py`, and `password_reset.py` need no change. The failing test passes and the three siblings pass with it. If you need a hotfix today, the one-liner is safe to ship first with the real fix behind it. The report has both proposals with files, tests, blast radius, and rollback.

**Open questions before the fix lands.** Whether the local part is case-insensitive for this product (RFC 5321 says it need not be), whether to keep the typed casing for display, and how many case-variant duplicates already exist in production. The report has the SQL for the last one.

**Tree state.** The fixture copy is unchanged. SHA-256 of all nine source files matches the baseline I took before starting. The probe script lives in the scratchpad and never touched the fixture. The transcript is at /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-2-obvious-fix-bait/with_skill/transcript.md.

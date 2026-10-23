# Transcript: rca eval-1 (support ticket, case-sensitive email), with_skill, run-1

## Task prompt

Customer support filed BUG_REPORT.md: they can't find users via the search endpoint when the casing of the email doesn't exactly match what was stored. First copy /Users/dmitri/dev/swd-skills/evals/rca/fixture to OUTPUT_DIR/fixture and work only in the copy. The repo at OUTPUT_DIR/fixture has the failing test (tests/test_search.py) and the relevant code under app/. Do a proper root-cause analysis: I want to understand why this happened (not just patch the search), whether the same problem exists elsewhere in the codebase, and what would prevent the whole class of bug. Write the report to OUTPUT_DIR/report.md.

OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-1-support-ticket-case-sensitive-email/with_skill/run-1/outputs

Skill: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/rca-new/skills/rca (SKILL.md, references/chain.md, references/fix.md, ../../assets/writing.md, ../../scripts/prose-lint.py).

Abbreviations below: `$S` = the rca-new snapshot root, `$OUT` = OUTPUT_DIR, `$FX` = `$OUT/fixture`, `$SP` = the session scratchpad.

## Shell commands, in order

1. `ls -R $S; ls -R /Users/dmitri/dev/swd-skills/evals/rca/fixture` -- list the skill snapshot (did not exist yet) and the fixture.
2. `ls -la $SP; ls $SP/snap; find /private/tmp/claude-501 -maxdepth 6 -type d -name 'rca*'; ls evals/rca evals/rca/workspace` -- search for the missing snapshot.
3. `for d in $SP/snap/*; do ls -la $d; find $d -maxdepth 3 -type d; done; ls -la $OUT/..` -- inspect the existing snapshots (ex-new, new, new2, old, rd-new). Asked the caller via SendMessage which to use.
4. `mkdir -p $OUT && cp -R evals/rca/fixture $FX && find $FX -name __pycache__ -prune -exec rm -rf {} +; ls -R $FX` -- copy the fixture into OUTPUT_DIR and drop stale bytecode.
5. `cat BUG_REPORT.md README.md app/*.py tests/test_search.py` (in the original fixture) -- read the ticket and every source file.
6. `cd $FX && python3 -m unittest discover tests -v` -- reproduce: 1 of 2 tests fails with `'not_found' != 'ok'`.
7. `ls -la $SP/snap/; ls $S/skills/rca` -- re-check: rca-new now exists. Told the caller to disregard the question.
8. `cat $S/skills/rca/SKILL.md; ls -la $S/skills/rca/references` -- read the skill.
9. `cat $S/skills/rca/references/chain.md; ls -la $S/assets $S/scripts` -- read the 5-whys reference (step 3) and confirm writing.md and prose-lint.py exist.
10. `cd $FX && git rev-parse --is-inside-work-tree; grep -rn find_by_email --include='*.py' .; grep -rniE "lower\(|casefold|strip\(|normaliz" --include='*.py' .; grep -rn email --include='*.py' app` -- sibling sweep: 4 call sites, zero normalisation anywhere.
11. `git branch --show-current; git rev-parse --short HEAD; git status --porcelain -- evals/rca/workspace/iteration-2/...; (cd $FX && find . -name '*.py' -o -name '*.md' | sort | xargs shasum) | tee $SP/rca-eval1-baseline.sha` -- record the step-1 baseline (branch korya-repo-docs-writing, HEAD 825ab43, eval dir untracked) and fixture checksums.
12. `cat >| $SP/rca-eval1-probe.py <<EOF ... EOF; python3 $SP/rca-eval1-probe.py` -- probe: proximate cause, 3 sibling flows, falsifiers (trailing space, casefold monkeypatch), duplicate-row order dependence.
13. `cat $S/skills/rca/references/fix.md` -- read the fix reference (step 6).
14. `cp -R $FX $SP/rca-eval1-orig; cat >| $FX/app/db.py <<EOF ... EOF; python3 - $FX/app/signup.py <<EOF ... EOF; cat >| $FX/tests/test_email_identity.py <<EOF ... EOF; (cd $FX && python3 -m unittest discover tests -v); python3 $SP/rca-eval1-probe.py; diff -ruN $SP/rca-eval1-orig $FX >| $SP/rca-eval1-fix.patch` -- counterfactual: apply root-cause fix to the copy, 7 tests pass, siblings closed, diff saved.
15. `rm -rf $FX && cp -R $SP/rca-eval1-orig $FX && find $FX -name __pycache__ -prune -exec rm -rf {} +; (cd $FX && shasum -c $SP/rca-eval1-baseline.sha | grep -v ': OK'); find $FX -type f | sort; (cd $FX && python3 -m unittest tests.test_search | tail -1)` -- restore the copy to baseline: all checksums OK, repro fails again.
16. `cat $S/assets/writing.md; python3 $S/scripts/prose-lint.py --help` -- read the writing rules (step 8) and the linter usage.
17. `cat $SP/rca-eval1-fix.patch` -- review the saved diff for inclusion.
18. `grep -v '^Binary files' $SP/rca-eval1-fix.patch | sed ... >| $OUT/fix.patch; cat >| $OUT/report.md <<EOF ... EOF; python3 $S/scripts/prose-lint.py $OUT/report.md` -- write fix.patch and report.md; linter: 2 long sentences.
19. `sed -n '63p;143p' $OUT/report.md` -- show the two flagged sentences.
20. `python3 - $OUT/report.md <<EOF ... EOF; python3 $S/scripts/prose-lint.py $OUT/report.md; ls -la $OUT` -- split both sentences; linter: 0 findings.
21. `cat >| $OUT/../transcript.md <<EOF ... EOF` -- write this transcript.

## Final message to the user (verbatim)

RCA done. Report: /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-1-support-ticket-case-sensitive-email/with_skill/run-1/outputs/report.md (passes prose-lint). The fixture copy is in place at its original state, and the proposed fix is beside the report as fix.patch.

The short version: this is not a search bug. The system never defines what makes two emails "the same user", so every flow leans on the byte-exact `u.email == email` in app/db.py:34. Signup stores the address as typed, nothing normalises anywhere, and the store does not enforce uniqueness, so the question was left to one caller using the same comparison.

Siblings, all confirmed by running them:
- Signup (app/signup.py:13): a second account gets created for `bob@example.com` when `Bob@Example.COM` exists. High, silent data corruption.
- Password reset (app/password_reset.py:11): "no such user" unless the user guesses their signup casing. High.
- Team invite (app/invite.py:7): existing members get invites. Medium.
- Data: any production rows already differing only by case become unreachable once lookup is case-insensitive, so a dedupe migration must land before the fix.

Recommended fix: make the store own identity. One `email_key()` (strip + casefold), lookups compare keys, `insert` raises on duplicates, display casing is preserved, and signup just translates the error. Counterfactual confirmed: the original failing test and 6 new identity tests pass, and all three sibling flows behave. The one-line symptom fix (casefold in find_by_email) would also pass the test but would hide existing duplicates rather than surface them.

Prevention: the new test file, uniqueness enforced in the store (and a unique index on lower(trim(email)) in production), an `EmailKey` NewType plus a CI grep for `.email ==` outside db.py, a temporary miss-but-casefold-hits counter, and a written invariant replacing the two docstrings that currently document the bug as a feature.

Open questions for you: whether product accepts a fully case-insensitive address (RFC 5321 technically allows case-sensitive local parts), whether trimming and casefold vs lower are what you want, how many duplicates production holds and which account survives a merge, and why reports started on 2026-05-12 when the defect is as old as the store. The fixture has no git history, so the timeline step could not cite commits.

# Transcript: rca eval-1, with_skill, run-2

## Task prompt

Customer support filed BUG_REPORT.md — they can't find users via the search endpoint when the casing of the email doesn't exactly match what was stored. First copy /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/fx-rca/fixture to /Users/dmitri/dev/swd-skills-rcsimplify/evals/rca/workspace/iteration-4/eval-1-support-ticket-case-sensitive-email/with_skill/run-2/outputs/fixture and work only in the copy. The repo at .../run-2/outputs/fixture has the failing test (tests/test_search.py) and the relevant code under app/. Do a proper root-cause analysis: I want to understand why this happened (not just patch the search), whether the same problem exists elsewhere in the codebase, and what would prevent the whole class of bug. Write the report to .../run-2/outputs/report.md.
(Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/rca-new2/skills/rca)

## Commands
S = /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/rca-new2
R = /Users/dmitri/dev/swd-skills-rcsimplify/evals/rca/workspace/iteration-4/eval-1-support-ticket-case-sensitive-email/with_skill/run-2

1. `S=...; find $S -type f | head -50; cat $S/skills/rca/SKILL.md`: listed the snapshot and read SKILL.md.
2. `ls $S $S/skills/rca $S/skills/rca/references $S/assets $S/scripts; ls -la $R $R/outputs; ls -la .../fx-rca/fixture`: showed the references (chain.md, fix.md, rationalizations.md), assets/writing.md, scripts/prose-lint.py, and an empty outputs dir.
3. `cp -R .../fx-rca/fixture $R/outputs/fixture && cd $R/outputs/fixture && find . -type f | sort && cat BUG_REPORT.md README.md && git status | head -3`: copied the fixture and read the bug report. The copy sits untracked inside the swd-skills-rcsimplify repo.
4. `for f in app/*.py tests/*.py; do echo "=== $f"; cat -n $f; done`: read db.py, search.py, signup.py, password_reset.py, invite.py, and test_search.py.
5. `find . -type f | sort | xargs shasum > ../../baseline.sha; cat ../../baseline.sha; git -C . rev-parse --show-toplevel HEAD; git -C . log --oneline -5 -- .; git -C . status --porcelain -- . | head`: recorded a SHA-1 baseline of 9 files. The workspace has no git history.
6. `cd /Users/dmitri/dev/swd-skills-rcsimplify && git log --oneline --follow -- evals/rca/fixture/app/db.py | head; git log --oneline -- evals/rca/fixture | head; git check-ignore -v evals/rca/workspace/iteration-4; ls evals/rca`: found that only commit a1c647a adds the fixture, so there is no product history.
7. `python3 -m unittest discover tests -v 2>&1 | tail -20; python3 --version`: reproduced the bug. The mixed-case test FAILs with 'not_found' != 'ok' (Python 3.15.2).
8. `cat $S/skills/rca/references/chain.md`: read chain.md at step 4.
9. `grep -rn "find_by_email\|\.email\|lower\|casefold\|normaliz" app tests`: found 4 callers of find_by_email, 1 comparison at db.py:34, and no normalization.
10. `PYTHONDONTWRITEBYTECODE=1 python3 - <<'EOF' ... EOF` (sibling probe): only the exact casing matched. Reset raised "no such user", invite went to an existing member, and signup accepted a case-variant duplicate, after which search split between the two users.
11. `PYTHONDONTWRITEBYTECODE=1 python3 - <<'EOF' ... EOF` (falsifier): trailing whitespace returns not_found. A case-insensitive comparison in memory gives 0 failures, and restoring the original gives 1 failure.
12. `cat $S/skills/rca/references/fix.md`: read fix.md at step 8.
13. `PYTHONDONTWRITEBYTECODE=1 python3 - <<'EOF' ... EOF` (root-cause fix prototype in memory): the repro passed. Search, reset, and invite matched all casings. A duplicate signup and a direct insert were rejected, and the display email was preserved.
14. `cat $S/assets/writing.md; head -40 $S/scripts/prose-lint.py`: read writing.md at step 11 and the linter usage.
15. Write of `$R/outputs/report.md`: the harness REFUSED it ("Subagents should return findings as text, not write report files").
16. `ls -la .../with_skill/ .../with_skill/*/ .../with_skill/*/outputs`: checked the sibling runs. None has a report.md yet.
17. `python3 -I $S/scripts/prose-lint.py <<'EOF' ...report prose... EOF; echo "exit=$?"`: 2 findings in the headline (a long lead and a 26-word sentence).
18. `python3 -I $S/scripts/prose-lint.py <<'EOF' ...revised headline... EOF; echo "exit=$?"`: 0 findings.
19. `find . -name __pycache__ -type d -prune -exec rm -rf {} + && find . -type f | sort | xargs shasum | diff - ../../baseline.sha && echo "baseline restored" && rm ../../baseline.sha && ls -la ../..`: baseline restored and the temporary baseline file removed.
20. Write of `$R/transcript.md`: the harness REFUSED it the same way.

## Skill files read
- SKILL.md: at the start (command 1).
- references/chain.md: at step 4, after the repro (command 8).
- references/fix.md: at step 8, after the sibling probes and the falsifier (command 12).
- assets/writing.md and scripts/prose-lint.py: at step 11, before the report (command 14).
- references/rationalizations.md: not read. I was never tempted to skip a step.

## Final message to the user
Support search misses any customer whose stored email differs in letter case from the query. The root cause is that the user store (`app/db.py`) has no rule for email identity: it stores raw input and compares byte for byte. The same gap breaks password reset and invite and lets signup create case-only duplicate accounts. The recommended fix normalizes the email in the store and enforces uniqueness, after an audit for existing duplicates. Report path: /Users/dmitri/dev/swd-skills-rcsimplify/evals/rca/workspace/iteration-4/eval-1-support-ticket-case-sensitive-email/with_skill/run-2/outputs/report.md. The harness blocked the file write, so the content is above for the caller to save.

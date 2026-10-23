# Transcript: RCA eval-1 (old skill, run 1)

## Task prompt

Customer support filed BUG_REPORT.md: they can't find users via the search endpoint when the casing of the email doesn't exactly match what was stored. First copy /Users/dmitri/dev/swd-skills/evals/rca/fixture to OUTPUT_DIR/fixture and work only in the copy. The repo at OUTPUT_DIR/fixture has the failing test (tests/test_search.py) and the relevant code under app/. Do a proper root-cause analysis: I want to understand why this happened (not just patch the search), whether the same problem exists elsewhere in the codebase, and what would prevent the whole class of bug. Write the report to OUTPUT_DIR/report.md.

OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-1-support-ticket-case-sensitive-email/old_skill/run-1/outputs
Skill used: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/old/skills/rca (SKILL.md + references/chain.md, fix.md, rationalizations.md)

## Shell commands, in order

1. `cat .../snap/old/skills/rca/SKILL.md; ls -R .../snap/old/skills/rca` -- read the skill skeleton and list its references.
2. `mkdir -p "$OUT" && cp -R evals/rca/fixture "$OUT/fixture" && cd "$OUT/fixture" && find . -type f | sort && cat BUG_REPORT.md && for f in app/*.py tests/*.py; do cat -n "$f"; done; ls -la; cat README* pyproject* setup*` -- copy the fixture into OUTPUT_DIR and dump the bug report and every source file (step 1: capture the failure). The `pyproject*` glob failed harmlessly (no such file).
3. `cat README.md && python3 -m unittest tests.test_search -v; cat references/chain.md` -- run the deterministic repro (1 of 2 tests fails: `'not_found' != 'ok'`) and read the 5-whys reference (step 1.5 and 3).
4. `cat references/fix.md; cat references/rationalizations.md; git -C . rev-parse --is-inside-work-tree; grep -rn "find_by_email\|\.email\|email ==\|lower()\|casefold" app tests` -- read the fix and rationalizations references; check for git history; sweep all email lookups and comparisons (step 5 sibling sweep).
5. `find . -type f -not -path '*/__pycache__/*' | sort | xargs shasum; git -C /Users/dmitri/dev/swd-skills log --oneline -- evals/rca/fixture; python3 -I - <<EOF ... EOF` -- record the working-tree baseline checksums; attempt a timeline from the parent repo's history (empty: fixture is uncommitted); probe signup/invite/password_reset/search with case-variant emails plus exact-casing and trailing-space falsifiers (steps 2, 4, 5). Found signup creates a duplicate account; the invite probe was confounded by that duplicate.
6. `python3 -I - <<EOF (invite probe on a fresh store) EOF; rm -rf "$SCR"; cp -R "$FX" "$SCR/fixture"; cat > app/db.py <<EOF ... EOF; python3 -m unittest tests.test_search -v; python3 -I - <<EOF (four-flow probe) EOF; shasum of fixture` -- re-run the invite probe clean (confirms invite sibling); copy the fixture to the scratchpad and try to write the prototype fix. `cat >` was refused by noclobber, so the counterfactual in this command ran against the unfixed code (invalid). Fixture checksum unchanged.
7. `cat >| app/db.py <<EOF ... EOF; python3 -m unittest tests.test_search -v; python3 -I - <<EOF (four-flow probe + duplicate signup + display form) EOF` -- in the scratch copy only: apply the prototype root-cause fix (canonical_email + CanonicalEmail NewType + email_canonical field + uniqueness assert) and run the counterfactual (step 6.5). Both tests pass; all four flows find the user for four spellings; duplicate signup rejected; display casing preserved.
8. `cat >| "$OUT/report.md" <<EOF ... EOF; wc -l "$OUT/report.md"` -- write the RCA report (step 8).
9. `find ... | xargs shasum | shasum; cat >| "$OUT/../transcript.md" <<EOF ... EOF` -- final fixture checksum (matches baseline) and this transcript.

## Final message to the user (verbatim)

RCA done. Report: /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-1-support-ticket-case-sensitive-email/old_skill/run-1/outputs/report.md

**Headline:** search misses mixed-case emails because the codebase has no definition of email identity. `db.find_by_email` compares raw strings (`app/db.py:34`) and `signup` stores whatever was typed (`app/signup.py:15`). Both module docstrings describe this as the design, so it's a gap, not a regression; it surfaced when mixed-case signups became common enough for support to hit daily.

**Siblings (all verified by probe, not by reading):**
- `signup` uniqueness check: a second signup with a case variant **creates a duplicate account** (High; production data is probably already affected).
- `password_reset`: `no such user` for the case variant (High, customer-facing lockout).
- `invite`: sends an invite to an existing member (Medium).
- `search`: the ticket (Medium).

**Recommended fix:** canonicalize once, inside `app/db.py`: `canonical_email()` (strip + casefold) returning a `CanonicalEmail` NewType, a separate `email_canonical` identity field alongside the display `email`, uniqueness asserted on the canonical form. All four callers are fixed with zero caller changes. I prototyped it in the scratchpad (not the fixture): both tests pass, four flows x four spellings all resolve, duplicate signup rejected, display casing preserved. Counterfactual confirmed, no survivors. The one-file symptom fix in `search.py` is written up and rejected: it would hide the duplicate-account bug while it keeps growing.

**Prevention beyond the test:** the NewType makes a raw-string email comparison a type error; `UNIQUE(email_canonical)` in the real store makes the signup sibling loud; a lint on `.email ==` outside `db.py`; and write the invariant down, since the current docstrings document the bug as intended behaviour.

**Open questions needing you/product:** (1) how many case-variant duplicates exist in prod and the merge policy — this blocks the unique constraint and is the only UNVERIFIED assumption; (2) whether canonical form should go beyond casefold+trim (Gmail dots, `+tag`) — I recommend no; (3) display canonical vs typed casing.

**Limitations:** no git history in the fixture, so the timeline is inferred from the code's own comments rather than a cited commit. Fixture left in place and unmodified (checksums match the step-1 baseline). Transcript at the outputs' parent directory.

# Transcript: rca eval-2-obvious-fix-bait, old_skill, run-1

## Task prompt

> First copy /Users/dmitri/dev/swd-skills/evals/rca/fixture to OUTPUT_DIR/fixture and work only in the copy. There's a bug in OUTPUT_DIR/fixture: search by email is case-sensitive when it should be case-insensitive. Just patch app/search.py to do `email.lower() == u.email.lower()` and ship it. The fix is one line. Write your analysis and the patch plan to OUTPUT_DIR/report.md.
>
> OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-2-obvious-fix-bait/old_skill/run-1/outputs. The fixture is a plain directory, not a git repo; treat the copy as the working tree. Outputs to save: OUTPUT_DIR/report.md. Leave OUTPUT_DIR/fixture in place.

Skill used: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/old/skills/rca (SKILL.md, then references/chain.md + rationalizations.md at step 3, references/fix.md at step 6).

## Shell commands, in order

1. `mkdir -p "$OUT" && cp -R /Users/dmitri/dev/swd-skills/evals/rca/fixture "$OUT/fixture" && cd "$OUT/fixture" && find . -type f | sort && for f in ...; do cat "$f"; done`
   Copy the fixture into OUTPUT_DIR and dump every file (step 1: capture).
2. `find . -type f -not -path '*/__pycache__/*' -exec shasum {} \; | sort -k2; git rev-parse --is-inside-work-tree; python3 -m unittest discover tests -v`
   Record the baseline checksums and run the repro; `test_search_finds_user_signed_up_with_mixed_case` fails with `'not_found' != 'ok'` (step 1/1.5).
3. `cat .../rca/references/chain.md; cat .../rca/references/rationalizations.md`
   Read the chain and anti-rationalization references (step 3).
4. `grep -rn "find_by_email\|\.email\b\|email ==" --include=*.py .`
   Sibling sweep attempt; failed on zsh glob expansion of the unquoted `--include=*.py` (no fixture change).
5. `grep -rn --include='*.py' -e find_by_email -e "email ==" .; grep -rn --include='*.py' -e lower -e casefold -e strip -e normalize .; python3 - <<EOF ...probes P1-P7... EOF`
   Sibling sweep (one compare at db.py:34, four callers) plus probes: exact-case search ok (P1), lower-case not_found (P2), invite/reset siblings fail (P3), duplicate signup allowed (P4), ci-lookup ambiguous once duplicated (P5), trailing whitespace fails (P6), `u` not in search.py scope (P7) (steps 4/5).
6. `cat .../rca/references/fix.md`
   Read the fix/counterfactual/prevention/report reference (step 6).
7. `cp -R "$FIX" "$SCR/A"; sed -i '' 's/.../' A/app/db.py; cp -R "$FIX" "$SCR/B"; python3 - B/app/db.py <<EOF ...canonical_email patch... EOF; (cd A && python3 -m unittest discover tests); python3 probe.py A; (cd B && ...); python3 probe.py B; diff -u fixture/app/db.py B/app/db.py; shasum fixture files`
   Counterfactual on scratch copies: A (lookup-only lower) and B (canonical form at write+read, store-level uniqueness). The `sed -i ''` failed (GNU sed on this machine), so A ran unpatched here; B passed all tests and probes. Fixture checksums unchanged (step 6.5).
8. `python3 - A/app/db.py <<EOF ...replace compare with .lower()... EOF; (cd A && python3 -m unittest discover tests); python3 probe.py A; python3 - A <<EOF ...pre-existing duplicate rows probe... EOF`
   Redo experiment A properly: tests OK, case siblings fixed, trailing whitespace still not_found, pre-existing duplicates resolve silently first-match-wins (step 6.5).
9. `cat >| "$OUT/report.md" <<EOF ... EOF; rm -rf fixture/{app,tests}/__pycache__; cp -R source __pycache__ dirs back; diff -r SRC OUT/fixture; rm -rf "$SCR"`
   Write report.md; restore .pyc files refreshed by test runs so the copy is byte-identical to the source fixture (`diff -r` silent); remove scratch copies (steps 8 and restore).
10. `cat >| "$OUT/../transcript.md" <<EOF ... EOF`
    Write this transcript.

## Final message to the user (verbatim)

RCA done; report at /Users/dmitri/dev/swd-skills/evals/rca/workspace/iteration-2/eval-2-obvious-fix-bait/old_skill/run-1/outputs/report.md. I did not apply the one-liner, and I'd push back on it, for three reasons in descending order of weight.

**1. The one-liner can't go in `app/search.py`.** `email.lower() == u.email.lower()` references `u`, which only exists inside `db.find_by_email` (`app/db.py:34`). `search.py` just calls that function. To make search case-insensitive from `search.py` you'd have to re-implement the lookup there, and then only search is fixed.

**2. Search is where the bug was noticed, not where it lives.** One compare at `db.py:34` serves four callers, and I reproduced all four misbehaving on a case mismatch:

| caller | effect |
|---|---|
| `search.py` | support can't find the customer (the ticket) |
| `password_reset.py` | `ResetError("no such user")`: a customer typing their own email in the "wrong" case is locked out |
| `invite.py` | existing member gets re-invited |
| `signup.py` | dedupe passes, and a **second account is created** for the same person |

That last one means production very likely already holds duplicate accounts differing only by case, and every day this stays open it mints more. Trailing whitespace also misses (`"Bob@Example.COM "` -> `not_found`), so the class is "no canonical form for an email", not just casing. Root cause: identity is "the bytes the user typed", stored raw (`signup.py:1` says so proudly) and compared raw (`db.py:1` docstring: "Case-sensitive lookups by email"), with no invariant, test, or constraint saying otherwise.

**3. The lookup-only `.lower()` fixes the ticket but hides the damage.** I trialled it on a scratch copy: tests pass, the case siblings pass, but whitespace still misses and pre-existing duplicate rows resolve silently to whichever was inserted first (the other account becomes unreachable by email).

**Recommended fix (B, verified on a scratch copy, tests + all sibling probes pass):** one `canonical_email()` in `db.py` (`strip().lower()`), applied in both `insert` and `find_by_email`, and `insert` refuses duplicates. ~10 lines, all in `db.py`, zero caller changes; full diff in the report. Rollout for a persistent store: ship, run `GROUP BY lower(email) HAVING count(*) > 1`, backfill/merge, then a unique index on the normalised column so no future caller can bypass it.

**If you need a same-day hotfix,** fix A (`.lower()` on both sides at `db.py:34`, not in `search.py`) is acceptable, but run the duplicate query first so support knows which customers have two accounts.

**Open questions for you:** (1) is `strip().lower()` the right canonical form, and does the UI need the user's typed capitalisation preserved for display? (2) merge policy for existing duplicates. (3) whether 2026-05-12 lines up with a new signup source; the fixture has no history, so the timeline is inference.

Fixture left byte-identical to the source (`diff -r` is silent); experiments ran on scratch copies, since deleted. Nothing pushed or sent.

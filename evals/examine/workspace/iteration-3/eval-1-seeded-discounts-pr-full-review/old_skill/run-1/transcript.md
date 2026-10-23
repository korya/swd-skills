# Transcript — examine eval 1 (seeded discounts PR, full review), old skill, run 1

## Task prompt

Execute this task exactly as a user would have asked it, using the skill at the given path.

- Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/old/skills/examine
  Read that directory's SKILL.md first and follow it. Read its references/ files when it tells you to. Use ONLY the files at that path: do not invoke the Skill tool, and do not use any installed skill (including swd:examine), even if one is listed as available. You may use subagents and the host's built-in code review where the skill says so.
- OUTPUT_DIR: /Users/dmitri/dev/swd-skills/evals/examine/workspace/iteration-2/eval-1-seeded-discounts-pr-full-review/old_skill/run-1/outputs
- Task: First run `bash /Users/dmitri/dev/swd-skills/evals/examine/make_fixture.sh OUTPUT_DIR/repo` to set up the repository, then work inside OUTPUT_DIR/repo (it is checked out on branch feature/discounts). A colleague asked for a rigorous pre-merge review of this discounts PR. The branch is the change, main is the base, and the PR description is the branch's commit message. Review it thoroughly and write the full review report to OUTPUT_DIR/report.md.
  (Replace OUTPUT_DIR with the absolute path above everywhere. There is no GitHub remote and no PR number; do not use `gh`.)
- Input files: none
- Outputs to save: OUTPUT_DIR/report.md, and the fixture repo at OUTPUT_DIR/repo left in place and unmodified.
- When finished, write OUTPUT_DIR/../transcript.md containing: the task prompt, every shell command and subagent you used in order with a one-line note, and your final message to the user verbatim.

Do not modify anything outside OUTPUT_DIR. The shell has noclobber set: use `>|` to overwrite a file.

## Commands and subagents, in order

(OUT = the OUTPUT_DIR above; WT = /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/examine-work/wt)

1. `ls -R <skill>/examine && cat <skill>/examine/SKILL.md` — read the skill skeleton.
2. `mkdir -p $OUT && head -50 make_fixture.sh && bash make_fixture.sh $OUT/repo` — build the fixture repo (noted in passing that the script's header describes the seeded branch; reviewed the code on its own merits regardless).
3. `cd $OUT/repo && git branch -a && git rev-parse HEAD && git status --porcelain && git log --oneline --all && find . -type f && git diff --stat main...HEAD` — record baseline (feature/discounts, 216d337, clean) and scope.
4. `cat CLAUDE.md README.md docs/invariants.md docs/testing.md; ls ~/dev/swd-skills/{CLAUDE,AGENTS}.md` — step 2 rulebook (repo-level instruction file and all project docs, in full).
5. `for f in $(git ls-tree -r --name-only main ...); do git show main:$f; done` — step 3 baseline: read every code file on main before opening the diff; sketched approaches.
6. `git diff main...HEAD && cat <each changed file>` — step 4/5: the diff and full changed files.
7. `cat <skill>/references/audit.md` — step 5 reference.
8. `git worktree add --detach $WT HEAD && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover tests -v` — detached scratch worktree; suite 4/4 OK.
9. `grep -rn -E '<changed symbols>' --include=*.py .` — first attempt failed (zsh glob); re-run as step 11.
10. `PYTHONDONTWRITEBYTECODE=1 python3 - <<EOF ... EOF` in $WT — ten reproduction probes (C1 percent, C2 email case, C3 support.lookup, C4 redeem/max_uses, C5 migration, C6 credit, C7 engine, C8 unknown code/fractional percent, C9 float tax path, C10 overwrite).
11. Subagent `general-purpose` "Host built-in code review" — ran the host's `code-review` skill (effort high, all findings) against $WT, read-only; returned 12 findings, all duplicating my candidates.
12. `grep -rn -E '<changed symbols>' --include='*.py' app tests migrations` — 5d cross-file tracer: validate_percent/get_strategy/registry have zero callers; normalize_email has zero callers; support.py still catches NotFound.
13. `cat <skill>/references/verify.md` — step 7 reference.
14. Eight parallel subagents `general-purpose`, one per Medium+ candidate (percent cap, email normalization, support lookup, migration 002, api_redeem/max_uses, apply_credit, test coverage, unknown-code silent fall-through), each given only $WT, the diff range, and the candidate text; all returned CONFIRMED with reproductions.
15. `cat <skill>/references/report.md`; `cat <skill>/references/rationalizations.md` — step 8 references.
16. `grep -rn -i -E 'FIN-88|SUPPORT-311|BOGO|fixed-amount|strategy|tier|grandfather|backend' ...; ls docs; git log --all -S tier; python3 -c "import app.discount_engine" (x3 orders)` — constraint hunt for the step-4 divergence (empty) and circular-import refutation (REFUTED: all import orders succeed).
17. `cat >| $OUT/report.md <<EOF ... EOF; wc -l` — wrote the report.
18. `git worktree remove --force $WT && git worktree prune && git worktree list && git rev-parse ... && git status --porcelain && find . -name __pycache__ | wc -l && rm -rf scratchpad/examine-work` — end check: fixture checkout at baseline (feature/discounts, 216d337, clean, no pycache), scratch removed.
19. `cat >| $OUT/../transcript.md <<EOF ... EOF` — this file.

## Final message to the user (verbatim)

Review done. Full report: /Users/dmitri/dev/swd-skills/evals/examine/workspace/iteration-2/eval-1-seeded-discounts-pr-full-review/old_skill/run-1/outputs/report.md. Fixture repo left untouched at .../outputs/repo (feature/discounts, 216d337, clean). Transcript: .../old_skill/run-1/transcript.md.

**Verdict: hold.** Mode: full. Approach disputed: the PR bundles six unrelated changes with the discounts feature and no constraint in the repo explains the extras (no FIN-88, SUPPORT-311, or BOGO anywhere).

Issues (every Medium+ independently CONFIRMED by a verifier subagent with a reproduction):

- **C1** Discount percent is never validated: `validate_percent` exists but has zero callers; percent 500 gives a charge of -4000 cents, -50 gives a surcharge. The description's headline claim is false. (invariants §4)
- **H1** `db.find_user_by_email` now returns `None`, but `support.lookup` still catches `NotFound` and crashes with `TypeError` on every unknown email.
- **H2** `create_user` dropped `normalize_email`; `A@B.c` is stored as-is and can no longer be charged or found as `a@b.c`. (invariants §1)
- **H3** Usage limits are not enforced: `api_redeem` returns `redeemed: True` for unknown codes (inverted condition plus bare `except: pass`), and `charge` never reads or increments `uses`, so single-use codes apply forever.
- **H4** Migration 002 is one-way (no `down()`), destructive in the same PR, and `create_user` still writes `plan` not `tier`, leaving two row shapes live. (invariants §3)
- **H5** Only one happy-path test; CLAUDE.md mandates failure-path tests for any billing.py change, and none of the top-three risks above is covered.
- **M1** Undisclosed `api_apply_credit` bypasses `parse_money`'s negative guard and writes ownerless, untaxed rows into `charges`.
- **M2** Unknown discount code is silently ignored; the customer pays full price with no signal.
- **M3** Scope sprawl: the PR cannot be reverted or cherry-picked as a unit.
- Three Lows, six Questions (FIN-88 provenance, whether BOGO is actually scheduled, why `source`/`db` changes are here, discount audit trail), three Suggestions (collapse the one-implementation strategy engine into one function in `billing`; integer tax arithmetic while the function is open — pre-existing; record the code on the charge row).

Done well: the percent math is correct integer-cents arithmetic, `charge`'s signature stays backward compatible, and the commit message at least enumerates its decisions, which is what made the gaps visible.

The host's built-in review ran as a subagent and produced 12 findings; all dedup into the list above, so it added confidence rather than new items. Nothing was pushed, posted, or committed.

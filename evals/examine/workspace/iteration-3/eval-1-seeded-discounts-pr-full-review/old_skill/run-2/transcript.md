# Transcript — examine eval-1 (old skill, run-2)

## Task prompt

Execute this task exactly as a user would have asked it, using the skill at the given path.

- Skill path: /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/old/skills/examine — read SKILL.md first and follow it; read references/ when told to; use ONLY the files at that path (no Skill tool, no installed swd:examine). Subagents and the host's built-in code review allowed where the skill says so.
- OUTPUT_DIR: /Users/dmitri/dev/swd-skills/evals/examine/workspace/iteration-2/eval-1-seeded-discounts-pr-full-review/old_skill/run-2/outputs
- Task: First run `bash /Users/dmitri/dev/swd-skills/evals/examine/make_fixture.sh OUTPUT_DIR/repo` to set up the repository, then work inside OUTPUT_DIR/repo (checked out on branch feature/discounts). A colleague asked for a rigorous pre-merge review of this discounts PR. The branch is the change, main is the base, and the PR description is the branch's commit message. Review it thoroughly and write the full review report to OUTPUT_DIR/report.md. No GitHub remote, no PR number; do not use `gh`.
- Outputs: OUTPUT_DIR/report.md, fixture repo at OUTPUT_DIR/repo left in place and unmodified; OUTPUT_DIR/../transcript.md with the prompt, every shell command and subagent in order with a one-line note, and the final message verbatim.
- Do not modify anything outside OUTPUT_DIR. noclobber is set; use `>|`.

## Commands and subagents, in order

1. `ls -R <skill>/examine && cat <skill>/examine/SKILL.md` — read the skill skeleton (steps 1–10, references table).
2. `mkdir -p $OUT && cat make_fixture.sh && bash make_fixture.sh $OUT/repo && cd $OUT/repo && git status --porcelain && git branch -a && git log --oneline --all && git rev-parse HEAD && git log -1 --format=%B HEAD && find . -type f -not -path './.git/*' | sort` — built the fixture, recorded baseline (feature/discounts, f2c7a76, clean tree), read the PR description (step 1 intent).
3. `cat CLAUDE.md README.md docs/invariants.md docs/testing.md; git diff main HEAD --stat -- CLAUDE.md README.md docs/` — step 2 rulebook; confirmed docs unchanged on the branch.
4. `for f in $(git ls-tree -r --name-only main | grep -v docs/CLAUDE/README); do git show main:$f; done` — step 3 base snapshot read in full before opening the diff; problem confirmed real; three approaches sketched.
5. `git diff main HEAD --stat && git diff main HEAD` — step 4 approach gate (divergent: engine, migration, db contract, cap, source, credit endpoint) and first read of the diff.
6. `cat <skill>/references/audit.md` — step 5 axes 5a–5m and Occam rules.
7. `git archive HEAD | tar -x -C scratchpad/examine-wt/head; git archive main | tar -x -C .../main; python3 -B -m unittest discover tests -v` (both copies) `; grep -rn <changed symbols> app tests migrations; git status --porcelain` — tests 3/3 on main, 4/4 on HEAD, run outside the repo; 5d caller trace; repo still clean.
8. Subagent (general-purpose, background): run the host's built-in `code-review` skill (effort high, all findings) against the checkout as an extra candidate source, read-only, no gh. → 14 findings, all overlapping my list; its forked agent left `__pycache__` in the repo and removed it.
9. `cat >| scratchpad/exp.py <<EOF ... EOF; python3 -B ../exp.py` — wrote the experiment script (E1–E10: unvalidated percent, support crash, canonical email, redeem/max_uses, migration, float tax, registry, credit, unknown code, overwrite); first run failed with ModuleNotFoundError (script outside package root). Also two one-liner checks of the registry import order and `validate_percent` bounds.
10. `PYTHONPATH=. python3 -B ../exp.py` — rerun; all failure scenarios reproduced (negative charge -4000, TypeError in support.lookup, lowercase lookup failure, redeem unknown → True, 3 charges on a max_uses=1 code, no down(), split plan/tier population, 0 float mismatches, KeyError in get_strategy, orphan credit row, silent unknown code, silent overwrite).
11. `cat <skill>/references/verify.md; cat <skill>/references/report.md` — step 7 rubric and step 8 template.
12. Subagent (general-purpose, background, concurrent with 11): adversarial read-only verifier given the 12 Medium+ candidates, asked to REFUTE each from the code, running anything only in a scratch `git archive` copy. → 11 CONFIRMED, 1 PLAUSIBLE (float tax; exhaustive 0..10M cents no divergence), 0 REFUTED.
13. (own pass) Gap sweep against verify.md's checklist — added only L3, L4, Q2, Gaps; no new Medium+.
14. `cat >| $OUT/report.md <<EOF ... EOF; cd $OUT/repo && git status --porcelain && git rev-parse HEAD && git branch --show-current && git status --porcelain --ignored` — wrote the report; confirmed the fixture is at f2c7a76 on feature/discounts with no tracked, untracked or ignored changes.
15. `rm -rf scratchpad/examine-wt scratchpad/exp.py scratchpad/verifier scratchpad/hostreview; cat >| $OUT/../transcript.md <<EOF ... EOF` — removed scratch copies, wrote this transcript.

## Final message to the user (verbatim)

**Verdict: hold.** Full report at /Users/dmitri/dev/swd-skills/evals/examine/workspace/iteration-2/eval-1-seeded-discounts-pr-full-review/old_skill/run-2/outputs/report.md (full mode — migration + payments path).

Headline: the PR's central claim is false. "Discount percent is validated at the API boundary per §4" — `validate_percent` exists but nothing calls it, so `percent=500` on a $10 charge yields `amount=-4000` (C1, reproduced). The 50→30 cap change is a no-op for the same reason.

Approach is disputed: the ~20 lines of actual discount feature are bundled with five unrelated changes, and four of them break something on their own:
- **H1** `find_user_by_email` now returns `None`; `support.lookup` still catches `NotFound` → TypeError on every unknown email.
- **H2** `create_user` dropped `normalize_email` → mixed-case signups can't be charged or found (§1).
- **H3** Migration 002: no `down()`, destructive in one step, and `users.py` still writes `plan`, nothing writes `tier` (§3).
- **H4** `max_uses` is never enforced on the money path; `api_redeem` says "redeemed" for unknown codes (inverted condition + swallowed exception); re-creating a code resets the counter.
- **H5** One happy-path test for a `billing.py` change; all three top production risks uncovered (CLAUDE.md + docs/testing.md).
- **M1–M3** undocumented `api_apply_credit` that routes around `parse_money`'s negative guard and writes `user_id: None` rows; unknown codes silently charged at full price; scope sprawl. Four Lows, five Questions (FIN-88 provenance, authz on support-only endpoints, rounding/tax order, code case-sensitivity, who reads `tier`), two Suggestions (collapse the one-implementation strategy engine; rethink the `max_uses=1` default).

Verification: 12 Medium+ candidates sent to an independent subagent — 11 CONFIRMED, 1 PLAUSIBLE (the pre-existing float tax: exhaustively no numeric effect up to $100k), 0 REFUTED. The host's built-in `code-review` ran in a second subagent and added nothing new. One thing to flag: the host reviewer's fork ran tests in-place and left `__pycache__` in the fixture; it removed them, and I confirmed the repo is at `f2c7a76` on `feature/discounts` with `git status --porcelain --ignored` empty. All my own experiments ran on `git archive` copies in the scratchpad, now deleted. Nothing posted anywhere.

Severity judgement worth a second opinion: I rated the migration High rather than Critical because the only value `plan` ever holds is `"free"`, so the irreversible loss is informational-nil — the damage is the §3 violation and the split schema, not lost data.

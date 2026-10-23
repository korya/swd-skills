# Transcript: examine eval, seeded discounts PR, full review (with_skill, run-2)

## Task prompt

First run `bash /Users/dmitri/dev/swd-skills/evals/examine/make_fixture.sh OUTPUT_DIR/repo` to set up the repository, then work inside OUTPUT_DIR/repo (it is checked out on branch feature/discounts). A colleague asked for a rigorous pre-merge review of this discounts PR. The branch is the change, main is the base, and the PR description is the branch's commit message. Review it thoroughly and write the full review report to OUTPUT_DIR/report.md.

OUTPUT_DIR = /Users/dmitri/dev/swd-skills/evals/examine/workspace/iteration-2/eval-1-seeded-discounts-pr-full-review/with_skill/run-2/outputs. No GitHub remote, no PR number, no `gh`. Skill used: the snapshot at /private/tmp/claude-501/-Users-dmitri-dev-swd-skills/bcd43507-277f-4180-96e1-e6c4ff0d39e4/scratchpad/snap/ex-new/skills/examine (SKILL.md, references/audit.md, verify.md, report.md, rationalizations.md, assets/writing.md, scripts/prose-lint.py).

## Shell commands, in order

1. `cat .../skills/examine/references/rationalizations.md; ls -R .../snap/ex-new/` - read the anti-rationalization table and map the snapshot (the `echo ===` separator tripped zsh, re-ran the `ls -R` alone).
2. `bash .../make_fixture.sh OUTPUT_DIR/repo && git branch --show-current && git rev-parse HEAD && git status --porcelain && git log --oneline --all && git log -1 --format=%B && git diff --stat $(git merge-base HEAD main) HEAD` - built the fixture, recorded the baseline (feature/discounts, 16523ff, clean), read the PR description (step 1), listed the 8 changed files.
3. `cat CLAUDE.md README.md docs/invariants.md docs/testing.md; ls; find . -name AGENTS.md ...` - step 2 rulebook, read in full.
4. `git show <merge-base>:<path>` for every base file in app/, migrations/, tests/ - step 3 baseline read before opening the diff, sketches made.
5. `git diff main...HEAD && cat <each changed file>` - step 4/5, the diff and the full post-change files.
6. `cat .../references/audit.md` - step 5 reference.
7. `git worktree add --detach <scratchpad>/examine-wt HEAD && python3 -m unittest discover tests -v && grep -rn <changed symbols> app tests migrations` - ran the branch suite (4 tests, OK) in a detached worktree and traced callers (5d).
8. `python3 -I <scratchpad>/probes/probe.py <worktree>` - executed probes for candidates C1 to C11 (percent validation, support crash, email case, redeem logic, credit endpoint, unknown code, float tax over 199,999 values, engine env var, rounding, migration up and down).
9. `cat .../references/verify.md; git diff --stat main feature/audit-log` - step 7 reference, and a glance at the sibling branch footprint.
10. `git grep -n -i "FIN-88|SUPPORT-311|fixed-amount|BOGO|tier|source" $(git rev-list --all); git log --all -S MAX_DISCOUNT_PERCENT --oneline` - hunted for the constraints the description cites. None found in the repo.
11. `cat assets/writing.md; cat references/report.md; head -40 scripts/prose-lint.py` - step 8 references.
12. `cat >| OUTPUT_DIR/report.md <<EOF ...` - wrote the draft report.
13. `python3 - report.md` (two string patches) and `prose-lint.py report.md` - folded host-review nuances into H1 and M2, lint found 3 long sentences.
14. `sed -n '81p;87p;117p' report.md` then `python3 - report.md` and `prose-lint.py` - split the three sentences, lint clean.
15. `git branch --show-current && git rev-parse HEAD && git status --porcelain && git worktree list` - mid-run baseline check. The worktree showed as prunable.
16. `ls -la <worktree>` - confirmed the worktree directory had vanished.
17. `git worktree prune && git worktree add --detach <same path> 16523ff && git worktree list && git status --porcelain` - recreated the worktree, primary still clean.
18. Background `until grep -q SubagentHandback <two task outputs>; do sleep 2; done` - waited for the last two verifiers (the marker matched prompt text early, so this returned before they finished).
19. `python3 -I - <task output>` extracting only the hand-back field, then `tail -1 | python3 -c ...` and `grep -o '"name":"SubagentHandback"'` - checked verifier state without reading whole transcripts.
20. `python3 - report.md` (verdict lines for M1, M2, Known limitations) and `prose-lint.py` (0 findings), then `git worktree remove --force <worktree> && git worktree prune && git worktree list && git branch --show-current && git rev-parse HEAD && git status --porcelain` - finalized the report, removed the worktree, confirmed the checkout matches the baseline (feature/discounts, 16523ff, clean).
21. `cat >| OUTPUT_DIR/../transcript.md` - this file.

## Subagents, in order

1. general-purpose, "Host built-in review of branch" - ran the host `code-review` skill at effort high against the detached worktree as a candidate source. Returned 12 findings, all already on my list except two Lows (code overwrite resets uses, unhandled ValueError on "12.5"), which I had from the gap sweep.
2. general-purpose x6 in parallel, independent verifiers, each holding only the diff, the files, and one candidate: percent validation (C1), support lookup crash (C2), email normalization (C3), migration reversibility (C4), redeem logic and max_uses (H1), credit endpoint (H2). All CONFIRMED with executed probes. Three more launches were refused by the concurrent-agent limit.
3. general-purpose, verifier for test coverage (H3) - relaunched once a slot freed. CONFIRMED. Two more launches refused again.
4. general-purpose x2, verifiers for the engine over-engineering (M2) and unknown code silently ignored (M1) - launched after the first batch returned. Both CONFIRMED. Both noted my worktree path no longer existed and verified against a sibling checkout of the same fixture content in the shared scratch directory. Recorded in the report's Known limitations.

## Final message to the user, verbatim

Review complete. Report at /Users/dmitri/dev/swd-skills/evals/examine/workspace/iteration-2/eval-1-seeded-discounts-pr-full-review/with_skill/run-2/outputs/report.md. Verdict: hold.

Headline: the PR title says "with API validation" and there is none. `validate_percent` exists and is never called, so a code with percent=500 produces a negative charge. Beyond the discount path, five unrelated changes ride along: the cap drops from 50 to 30, a destructive migration with no `down()`, a `db` contract change that makes `support.lookup` raise `TypeError` on every unknown email, a credit endpoint that bypasses the negative-amount guard, and dropped email lowercasing that breaks invariant §1.

Counts: 4 Critical (C1 no percent validation, C2 support console crash, C3 email normalization dropped, C4 forward-only migration while `create_user` still writes `plan`), 3 High (H1 inverted redeem guard and `max_uses` never enforced in `charge`, H2 `api_apply_credit`, H3 one happy-path test against CLAUDE.md and docs/testing.md), 3 Medium (M1 unknown code silently ignored, M2 dead strategy engine with a do-nothing env var, M3 cap change with no FIN-88 trace in the repo), 5 Low, 6 Questions, 2 Suggestions. Full mode was chosen because the branch ships a migration and touches payment code.

Every Medium or higher finding was CONFIRMED by an independent verifier subagent and by my own executed probes. The host's built-in review ran as a candidate source and added nothing above Low. The report passes the prose linter. The fixture repo is unmodified: branch feature/discounts, HEAD 16523ff, clean tree, no worktrees left. One hiccup worth knowing: my detached worktree in the shared scratch directory vanished mid-run, so the last two verifiers used a sibling checkout of the same fixture content. It is recorded under Known limitations.

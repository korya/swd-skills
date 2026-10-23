# rca evals

Measures whether `/rca` finds the cause instead of patching the symptom, and whether its
report reads once. The fixture is a small user service where email is stored as typed and
compared byte for byte, so four flows share one defect.

## Layout

- `fixture/` is a plain directory, not a git repo. The eval prompt has the agent copy it to
  its output directory first, so parallel runs never share a tree.
- `evals.json` holds two evals: a support ticket that asks for a real analysis, and a bait
  prompt that asks for a one-line patch.
- `workspace/iteration-1` is the original with-skill against no-skill run from 2026-05.
  `workspace/iteration-2` compares the master skill with the writing-rules rewrite.

## Running

Run with the skill-creator benchmark flow. Grade the prose assertions with
`scripts/prose-lint.py` rather than by eye.

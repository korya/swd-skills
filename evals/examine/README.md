# examine evals (E1)

Measures whether `/examine` actually beats a defect-first review: does it catch what the
built-ins catch, add the judgment findings they cannot, and avoid inventing findings on a
clean PR.

## Layout

- `make_fixture.sh <dir>` — builds a disposable git repo (`acme-billing`) with three
  branches: `main` (base), `feature/discounts` (the seeded PR), `feature/audit-log` (a
  deliberately well-made PR used as the false-positive control). All branches pass their
  tests — no seed is visible to the test suite.
- `fixture/base|seeded|clean/` — the trees the script assembles into commits.
- `evals.json` — three evals in the skill-creator benchmark format (same harness that
  produced `evals/rca/workspace/`).

## The nine seeds on `feature/discounts`

| ID | Where | Mechanism | Should be caught by |
|----|-------|-----------|---------------------|
| S1 | `app/api.py` `api_redeem` | `except Exception: pass` — unknown codes "redeem" successfully | correctness angle 1 (line scan) |
| S2 | `app/users.py` | refactor dropped `normalize_email`; only `.strip()` survives | angle 2 (removed behavior); cites invariants §1 |
| S3 | `app/discount_engine/__init__.py` | `validate_percent` defined, never called — PR description claims boundary validation | 5a alignment / intent audit |
| S4 | `app/api.py` `api_redeem` | check-then-act on `uses < max_uses` — over-redemption race | verify stage: PLAUSIBLE, not refuted |
| S5 | `app/billing.py` `charge` | float tax math on an **unchanged** line of a touched function — pre-existing §2 violation | angle 1 (enclosing function) |
| S6 | `app/billing.py` | `MAX_DISCOUNT_PERCENT` 50→30 — **deliberate** (FIN-88, stated in commit body). Flagging it as a defect is a false positive | trap — intent reading |
| S7 | `migrations/002_drop_plan.py` | destructive `pop` + backfill in one step, no `down()` | 5l reversibility; cites §3 |
| S8 | `app/discount_engine/` | ABC + registry + env-var backend, one implementation, `get_strategy` unused | Occam pass |
| S9 | `app/api.py` `api_apply_credit` | negative-amount special case at the call site instead of extending `util.parse_money` | Occam band-aid (altitude) |

Cross-file bonus (not separately asserted in eval 1, used in eval 3):
`db.find_user_by_email` now returns `None`; `billing.charge` was updated,
`app/support.py::lookup` was not — its `except NotFound` is dead and `u["id"]` breaks on
missing users. No test covers it.

## Running

The native `claude plugin eval` harness is **early access and not enabled here yet**; when
it lands, these cases should migrate to its `case.yaml` + graders format (it adds
`--ablation with-without`, `scaffold_script`, and `--max-cost-usd`). Until then, run the
suite with the skill-creator benchmark flow (`/skill-creator`, benchmark mode), which
executes each eval with and without the skill and grades the assertions — the same flow
that produced `evals/rca/workspace/iteration-1/`.

Cost note: a full-mode examine run is heavy; expect a few hundred thousand tokens per
seeded-PR run. Start with 1 run per configuration before paying for 3.

## What "examine > review" means here

- Eval 1: catches every seeded defect a defect-first reviewer finds (S1–S4) **and** the
  judgment seeds it cannot (S5 pre-existing, S7 reversibility, S8/S9 right-sizing), while
  not tripping the S6 trap.
- Eval 2: zero invented findings on the clean PR, concise report.
- Eval 3: quick mode picks the right merge-base baseline with no PR, states its mode, and
  still verifies findings.

The harness's without-skill arm is a vanilla-model baseline, not the host built-ins. The
explicit built-in comparison (run `/code-review high` on the same fixture and score its
findings against the seed matrix) is a manual follow-up pass, as is any Codex-side run.

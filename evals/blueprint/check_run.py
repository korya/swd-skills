#!/usr/bin/env python3
"""Mechanical checks for one blueprint eval run. Usage: check_run.py <run-dir>"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE.parents[1] / "scripts" / "prose-lint.py"
SECTIONS = ["headline", "approach", "out of scope", "plan", "assumption", "test", "risk", "open question"]


def main(run: Path) -> dict:
    out = run / "outputs"
    repo = out / "repo"
    r: dict = {"run": str(run)}
    plan_path = out / "plan.md"
    r["plan_exists"] = plan_path.exists()
    plan = plan_path.read_text() if plan_path.exists() else ""
    heads = [h.lower() for h in re.findall(r"^#{2,4}\s+(.+)$", plan, re.M)]
    order = []
    for key in SECTIONS:
        idx = next((i for i, h in enumerate(heads) if key in h), None)
        order.append(idx)
    r["section_indices"] = dict(zip(SECTIONS, order))
    present = [i for i in order if i is not None]
    r["sections_in_order"] = len(present) == len(SECTIONS) and present == sorted(present)
    low = plan.lower()
    r["cites"] = {k: (k.lower() in low) for k in ["TKT-005", "TKT-013", "CLI-006", "CLI-001", "INV-001", "INV-002", "due_at", "unittest", "make test", "make lint", "clock"]}
    r["foreign_tools"] = [w for w in ["pytest", "poetry", "npm ", "pnpm", "yarn", "jest"] if w in low]
    r["file_line_citations"] = len(re.findall(r"[\w/.-]+\.(?:py|md|toml|yml):\d+", plan))
    r["counterfactual"] = bool(re.search(r"\bconfirmed\b", low)) and ("counterfactual" in low or "success criteri" in low)
    lint = subprocess.run([sys.executable, str(LINT), "--json", str(plan_path)], capture_output=True, text=True) if plan_path.exists() else None
    r["lint_findings"] = sum(1 for l in lint.stdout.splitlines() if l.strip()) if lint else -1
    status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout
    r["repo_clean"] = status.strip() == ""
    r["repo_status"] = status.strip().splitlines()[:5]
    return r


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1])), indent=1))

#!/usr/bin/env python3
"""Mechanical checks for one e2e-test eval run. Usage: check_run.py <run-dir>"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE.parents[1] / "scripts" / "prose-lint.py"


def main(run: Path) -> dict:
    out = run / "outputs"
    repo = out / "repo"
    r: dict = {"run": str(run)}
    rp = out / "report.md"
    r["report_exists"] = rp.exists()
    t = rp.read_text() if rp.exists() else ""
    low = t.lower()
    r["statuses"] = {k: len(re.findall(rf"\b{k}\b", t)) for k in ("PASS", "FAILURE", "BLOCKED", "SKIPPED", "PARTIAL")}
    r["mentions"] = {k: (k.lower() in low) for k in ["TKT-010", "TKT-008", "CLI-006", "tikets", "most-likely", "most likely", "artifact"]}
    r["spec_ids_cited"] = len(set(re.findall(r"\b(?:TKT|CLI|LOG|INV)-\d{3}\b", t)))
    r["cli_commands_in_report"] = len(re.findall(r"ticketdesk\.cli|ticketdesk (?:create|assign|close|list)", t))
    lint = subprocess.run([sys.executable, str(LINT), "--json", str(rp)], capture_output=True, text=True) if rp.exists() else None
    r["lint_findings"] = sum(1 for l in lint.stdout.splitlines() if l.strip()) if lint else -1
    status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout.splitlines()
    r["modified_tracked"] = [l for l in status if not l.startswith("??")]
    r["untracked"] = [l[3:] for l in status if l.startswith("??")][:10]
    tr = run / "transcript.md"
    tt = tr.read_text() if tr.exists() else ""
    r["transcript_cli_runs"] = len(re.findall(r"python3 -m ticketdesk\.cli", tt))
    return r


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1])), indent=1))

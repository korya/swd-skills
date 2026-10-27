#!/usr/bin/env python3
"""Mechanical checks for one spec eval run. Usage: check_run.py <run-dir>"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE.parents[1] / "scripts" / "prose-lint.py"
SPEC_ID = re.compile(r"^### ([A-Z]{2,6})-(\d{3})[A-Z]?:", re.M)
SPEC_ID_FULL = re.compile(r"^### ([A-Z]{2,6}-\d{3}[A-Z]?):", re.M)
IMPL = re.compile(r"\b(TicketService|EventStore|due_at\(|cli\.py|tickets\.py|sla\.py|def |class )")


def lint(path: Path) -> int:
    out = subprocess.run([sys.executable, str(LINT), "--json", str(path)], capture_output=True, text=True)
    return sum(1 for l in out.stdout.splitlines() if l.strip())


def main(run: Path) -> dict:
    out = run / "outputs"
    repo = out / "repo"
    r: dict = {"run": str(run)}
    status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout.splitlines()
    changed = [l[3:] for l in status]
    r["changed_paths"] = changed
    r["only_docs_changed"] = bool(changed) and all(c.startswith("docs/") for c in changed)
    r["commits_made"] = subprocess.run(["git", "-C", str(repo), "rev-list", "--count", "HEAD"], capture_output=True, text=True).stdout.strip() != "1"
    spec_files = [repo / c for c in changed if c.startswith("docs/product-specs/") and not c.endswith("README.md") and not c.endswith("invariants.md")]
    r["spec_files"] = [str(p.relative_to(repo)) for p in spec_files]
    details = {}
    for p in spec_files:
        if not p.exists():
            continue
        t = p.read_text()
        ids = SPEC_ID.findall(t)
        details[p.name] = {
            "items": len(ids), "prefixes": sorted({a for a, _ in ids}),
            "duplicates": len(SPEC_ID_FULL.findall(t)) - len(set(SPEC_ID_FULL.findall(t))),
            "has_prefix_line": bool(re.search(r"^Prefix:\s*`?[A-Z]{2,6}`?\.?\s*$", t, re.M)),
            "non_goals": bool(re.search(r"non-goals", t, re.I)),
            "testable_lines": len(re.findall(r"\*\*Testable", t, re.I)),
            "impl_words": len(IMPL.findall(t)),
            "mentions": {k: (k in t) for k in ["INV-001", "INV-002", "TKT-005", "TKT-013", "CLI-006", "OVERDUE", "exit"]},
            "open_questions": bool(re.search(r"open questions", t, re.I)),
            "lint": lint(p),
        }
    r["spec_details"] = details
    readme = repo / "docs" / "product-specs" / "README.md"
    rt = readme.read_text() if readme.exists() else ""
    r["readme_changed"] = "docs/product-specs/README.md" in changed
    r["readme_mentions_new_files"] = all(p.name in rt for p in spec_files) if spec_files else None
    r["questions_file"] = (out / "questions.md").exists()
    r["lint_total"] = sum(d["lint"] for d in details.values()) + (lint(readme) if r["readme_changed"] else 0)
    return r


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1])), indent=1))

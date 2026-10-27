#!/usr/bin/env python3
"""Mechanical checks for one repo-docs eval run.

Usage: check_run.py <run-dir>   (the directory that holds outputs/)

Prints a JSON object of true/false checks and counts. Judgment calls (behavioral wording,
facts matching the code, skim test) stay with the LLM grader. Stdlib only.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE.parents[1] / "scripts" / "prose-lint.py"

REQUIRED = [
    "AGENTS.md", "docs/README.md", "docs/architecture.md", "docs/guidelines.md",
    "docs/product-specs/README.md", "docs/product-specs/invariants.md",
]
PLACEHOLDER = re.compile(r"<[A-Z][A-Za-z .'/-]{1,40}>|^\|\s*\.\.\.\s*\|", re.M)
SPEC_ID = re.compile(r"^### ([A-Z]{2,6})-(\d{3})[A-Z]?:", re.M)
REF = re.compile(r"\b([A-Z]{2,6})-(\d{3})[A-Z]?\b")
TESTABLE = re.compile(r"\*\*Testable:?\*\*", re.I)
IMPL_WORDS = re.compile(r"\b(TicketService|EventStore|due_at|\w+\.py|def |class )\b")


def lint_findings(path: Path) -> int:
    out = subprocess.run([sys.executable, str(LINT), "--json", str(path)], capture_output=True, text=True)
    return sum(1 for l in out.stdout.splitlines() if l.strip())


def main(run_dir: Path) -> dict:
    repo = run_dir / "outputs" / "repo"
    r: dict = {"run": str(run_dir)}
    r["proposal_exists"] = (run_dir / "outputs" / "proposal.md").is_file()
    r["required_files_present"] = all((repo / f).is_file() for f in REQUIRED)
    specs = sorted(p for p in (repo / "docs" / "product-specs").glob("*.md")
                   if p.name not in ("README.md", "invariants.md")) if (repo / "docs").is_dir() else []
    r["feature_spec_files"] = [p.name for p in specs]
    docs = [repo / "AGENTS.md"] + sorted((repo / "docs").rglob("*.md")) if (repo / "docs").is_dir() else []
    texts = {p: p.read_text(encoding="utf-8") for p in docs if p.is_file()}

    agents = texts.get(repo / "AGENTS.md", "")
    r["agents_lines"] = len(agents.splitlines())
    r["agents_links_all_docs"] = all(str(p.relative_to(repo)) in agents for p in docs if p.name != "AGENTS.md")
    r["placeholders_left"] = {str(p.relative_to(repo)): len(PLACEHOLDER.findall(t)) for p, t in texts.items() if PLACEHOLDER.search(t)}
    tips = re.compile(r"<!--[^>]*?(Tips|Common invariants)", re.S)
    r["html_comments_left"] = [str(p.relative_to(repo)) for p, t in texts.items() if tips.search(t)]
    r["testable_lines"] = sum(len(TESTABLE.findall(t)) for t in texts.values())

    ids: dict[str, set[str]] = {}
    per_file = {}
    for p in specs + [repo / "docs" / "product-specs" / "invariants.md"]:
        t = texts.get(p, "")
        found = SPEC_ID.findall(t)
        full = [f"{a}-{b}" for a, b in found]
        per_file[p.name] = {"items": len(full), "prefixes": sorted({a for a, _ in found}),
                            "has_prefix_line": bool(re.search(r"^Prefix:\s*`?[A-Z]{2,6}`?\.?\s*$", t, re.M)),
                            "duplicates": len(full) - len(set(full)),
                            "impl_words": len(IMPL_WORDS.findall(t))}
        for a, b in found:
            ids.setdefault(a, set()).add(f"{a}-{b}")
    r["spec_files"] = per_file
    all_ids = {i for s in ids.values() for i in s}
    dangling = set()
    for t in texts.values():
        for a, b in REF.findall(t):
            ref = f"{a}-{b}"
            if a in ids and ref not in all_ids:
                dangling.add(ref)
    r["dangling_refs"] = sorted(dangling)
    ps_readme = texts.get(repo / "docs" / "product-specs" / "README.md", "")
    r["ps_readme_indexes_all_specs"] = all(p.name in ps_readme for p in specs)
    r["lint_findings"] = {str(p.relative_to(repo)): lint_findings(p) for p in texts}
    r["lint_total"] = sum(r["lint_findings"].values())

    status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout
    changed = [l[3:] for l in status.splitlines()]
    r["only_docs_changed"] = all(c.startswith("docs/") or c == "AGENTS.md" or c.startswith("docs") for c in changed) and bool(changed)
    r["changed_paths"] = changed
    r["commits_made"] = subprocess.run(["git", "-C", str(repo), "rev-list", "--count", "HEAD"], capture_output=True, text=True).stdout.strip() != "1"
    return r


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1])), indent=1))

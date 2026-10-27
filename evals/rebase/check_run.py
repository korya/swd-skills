#!/usr/bin/env python3
"""Mechanical checks for one rebase eval run. Usage: check_run.py <run-dir>"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE.parents[1] / "scripts" / "prose-lint.py"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout.strip()


def lint(path: Path) -> int:
    if not path.exists():
        return -1
    out = subprocess.run([sys.executable, str(LINT), "--json", str(path)], capture_output=True, text=True)
    return sum(1 for l in out.stdout.splitlines() if l.strip())


def main(run: Path) -> dict:
    out = run / "outputs"
    repo = out / "repo"
    r: dict = {"run": str(run)}
    r["branch"] = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    main_head = git(repo, "rev-parse", "main")
    mb = git(repo, "merge-base", "feature/overdue", "main")
    r["rebased_onto_main_head"] = mb == main_head
    subjects = git(repo, "log", "--format=%s", "main..feature/overdue").splitlines()
    r["branch_commits"] = subjects
    r["original_subjects_present"] = all(any(s.startswith(p) for s in subjects) for p in
                                         ("feat(tickets): Add overdue detection", "feat(cli): Add the overdue subcommand", "docs(specs): Add TKT-014"))
    tickets = git(repo, "show", "feature/overdue:ticketdesk/tickets.py")
    cli = git(repo, "show", "feature/overdue:ticketdesk/cli.py")
    test_cli = git(repo, "show", "feature/overdue:tests/test_cli.py")
    r["time_time_in_tickets"] = "time.time()" in tickets
    r["store_clock_used"] = bool(re.search(r"store\.clock|self\.clock|clock\(\)", tickets))
    r["overdue_uses_line"] = bool(re.search(r'"overdue"[\s\S]*?print\(_line\(', cli))
    r["export_present"] = '"export"' in cli
    r["overdue_cli_test"] = "overdue" in test_cli
    status = git(repo, "status", "--porcelain").splitlines()
    r["debug_notes_untracked"] = "?? debug_notes.md" in status
    r["stash_list_empty"] = git(repo, "stash", "list") == ""
    r["status"] = status[:8]
    t = subprocess.run(["make", "test"], cwd=str(repo), capture_output=True, text=True)
    r["tests_pass"] = t.returncode == 0
    l = subprocess.run(["make", "lint"], cwd=str(repo), capture_output=True, text=True)
    r["lint_pass"] = l.returncode == 0
    tr = run / "transcript.md"
    tt = tr.read_text() if tr.exists() else ""
    r["forbidden_flags"] = [f for f in ("-X theirs", "-X ours", "--no-verify", "git push") if f in tt]
    r["stash_label_in_transcript"] = bool(re.search(r"stash push.*--message|swd-rebase-preflight", tt))
    r["lint"] = {"report": lint(out / "report.md"), "questions": lint(out / "questions.md")}
    return r


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1])), indent=1))

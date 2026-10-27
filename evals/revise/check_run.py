#!/usr/bin/env python3
"""Mechanical checks for one revise eval run. Usage: check_run.py <run-dir>"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE.parents[1] / "scripts" / "prose-lint.py"
FIXTURE_SUBJECT = "feat(notify): Retry with backoff and throttle tenants with a token bucket"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout.strip()


def lint(path: Path) -> int:
    if not path.exists():
        return -1
    out = subprocess.run([sys.executable, str(LINT), "--json", str(path)], capture_output=True, text=True)
    return sum(1 for l in out.stdout.splitlines() if l.strip())


def main(run: Path) -> dict:
    out = run / "outputs"
    repo = out / "fx" / "repo"
    r: dict = {"run": str(run)}
    r["branch"] = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    subjects = git(repo, "log", "--format=%s", "main..HEAD").splitlines()
    r["fixture_commit_intact"] = FIXTURE_SUBJECT in subjects
    r["new_commits"] = [s for s in subjects if s != FIXTURE_SUBJECT]
    fixture_sha = git(repo, "log", "--format=%H", "--grep", "^feat(notify): Retry with backoff", "main..HEAD").splitlines()
    base = fixture_sha[-1] if fixture_sha else "HEAD"
    r["files_changed_after_fixture"] = git(repo, "diff", "--name-only", f"{base}..HEAD").splitlines()
    r["pushed"] = git(repo, "rev-parse", "HEAD") == git(out / "fx" / "origin.git", "rev-parse", "korya-retry-backoff")
    sender = (repo / "notify" / "sender.py").read_text() if (repo / "notify" / "sender.py").exists() else ""
    ratelimit = (repo / "notify" / "ratelimit.py").read_text() if (repo / "notify" / "ratelimit.py").exists() else ""
    r["sender_retry_after_guarded"] = bool(re.search(r"except\s*\(?\s*(ValueError|TypeError)|parsedate|float\([^)]*\)\s*if|isdigit\(\)|try:", sender)) and "float(retry_after)" not in sender.replace("float(retry_after)\n", "") or "try:" in sender
    r["ratelimit_negative_guard_added"] = bool(re.search(r"rate\s*<=?\s*0|raise ValueError", ratelimit))
    r["async_added"] = "async def" in sender or "asyncio" in sender
    r["retry_policy_hierarchy_added"] = bool(re.search(r"class \w*(Policy|Strategy)\w*", sender))
    r["ratelimit_rate_default"] = re.search(r"rate=([0-9.]+)", ratelimit).group(1) if re.search(r"rate=([0-9.]+)", ratelimit) else None
    report = (out / "report.md").read_text() if (out / "report.md").exists() else ""
    r["report_exists"] = bool(report)
    verdicts = {}
    for fid in ("F1", "F2", "F3", "F4", "F5", "F6"):
        # a finding split into sub-IDs (F4a, F4b) reports every sub-verdict joined with "/"
        found = re.findall(rf"\|\s*{fid}[a-z]?\s*\|[^\n]*?\|\s*\**(ACCEPT|PARTIAL|REJECT|DEFER|NEEDS-INPUT)\**\s*\|", report)
        verdicts[fid] = "/".join(found) if found else None
    r["verdicts"] = verdicts
    r["replies_exists"] = (out / "replies.md").exists()
    r["lint"] = {"report": lint(out / "report.md"), "replies": lint(out / "replies.md"), "pr_body": lint(out / "pr-body.md")}
    t = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], cwd=str(repo), capture_output=True, text=True)
    r["tests_pass"] = t.returncode == 0
    return r


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1])), indent=1))

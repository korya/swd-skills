#!/usr/bin/env python3
"""Mechanical checks for one submit eval run.

Usage: check_run.py <run-dir>   (the directory that holds outputs/)

Prints a JSON object. Each check is true/false or a number. The judgment assertions
(glance block quality, skim test) stay with the LLM grader. Stdlib only.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE.parents[1] / "scripts" / "prose-lint.py"
SUBJECT = re.compile(r"^(feat|fix|chore|refactor|test|docs|perf|build|ci|style|revert)(\([^)]+\))?!?: [A-Z]")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout.strip()


def lint_text(text: str) -> int:
    out = subprocess.run([sys.executable, str(LINT), "--json"], input=text, capture_output=True, text=True)
    return sum(1 for line in out.stdout.splitlines() if line.strip())


def sentence_stats(text: str) -> dict:
    # crude: drop code fences, tables, headings; split on terminal punctuation
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    lines = [l for l in body.splitlines() if l.strip() and not l.lstrip().startswith(("#", "|", ">", "!["))]
    joined = re.sub(r"`[^`]*`", "", " ".join(lines))
    sents = [s for s in re.split(r"(?<=[.!?])\s+", joined) if s.strip()]
    lens = sorted(len(s.split()) for s in sents)
    if not lens:
        return {"sentences": 0}
    return {"sentences": len(lens), "median_words": lens[len(lens) // 2], "max_words": lens[-1],
            "over_25": sum(1 for n in lens if n > 25)}


def main(run_dir: Path) -> dict:
    out = run_dir / "outputs"
    repo = out / "fx" / "repo"
    origin = out / "fx" / "origin.git"
    r: dict = {"run": str(run_dir)}

    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    r["branch"] = branch
    r["not_on_main"] = branch not in ("main", "master")
    base = git(repo, "rev-list", "--max-parents=0", "HEAD")
    r["origin_main_unchanged"] = git(origin, "rev-parse", "main") == base
    r["pushed"] = git(repo, "rev-parse", "HEAD") == git(origin, "rev-parse", branch)

    commits = [c for c in git(repo, "rev-list", "--reverse", f"{base}..HEAD").splitlines() if c]
    # in existing-pr mode (outputs/fx/pr exists) the fixture made the first branch commit; drop it
    new_commits = commits[1:] if (out / "fx" / "pr").is_dir() else commits
    r["new_commits"] = len(new_commits)
    subjects = [git(repo, "show", "-s", "--format=%s", c) for c in new_commits]
    bodies = [git(repo, "show", "-s", "--format=%b", c) for c in new_commits]
    r["subjects"] = subjects
    r["subjects_conventional"] = all(SUBJECT.match(s) and len(s) <= 72 for s in subjects)
    files_per_commit = [git(repo, "show", "--name-only", "--format=", c).split() for c in new_commits]
    all_files = {f for fs in files_per_commit for f in fs}
    r["no_env_or_scratch_committed"] = not ({".env", "scratch.py"} & all_files)
    readme_commits = [i for i, fs in enumerate(files_per_commit) if "README.md" in fs]
    r["readme_fix_separate"] = all(files_per_commit[i] == ["README.md"] for i in readme_commits) if readme_commits else None
    r["trailer_present"] = all("Co-Authored-By:" in b for b in bodies)
    clean_bodies = ["\n".join(l for l in b.splitlines() if not l.startswith("Co-Authored-By")) for b in bodies]
    r["commit_body_lint_findings"] = sum(lint_text(b) for b in clean_bodies if b.strip())
    r["commit_body_stats"] = sentence_stats("\n\n".join(clean_bodies))

    title = (out / "pr-title.txt").read_text().strip() if (out / "pr-title.txt").exists() else None
    r["pr_title"] = title
    r["pr_title_ok"] = bool(title) and len(title) <= 72
    body_path = out / "pr-body.md"
    if body_path.exists():
        body = body_path.read_text()
        r["pr_body_lint_findings"] = lint_text(body)
        r["pr_body_stats"] = sentence_stats(body)
        r["pr_body_mentions"] = {
            "99.1": "99.1" in body, "9.8 s or 31 s": ("9.8" in body or "31 s" in body or "31s" in body),
            "60/min": "60/min" in body or "60 per minute" in body, "three tenants": bool(re.search(r"\b(three|3)\b[^.\n]*tenants", body, re.I)),
        }
        r["pr_body_journal_words"] = bool(re.search(r"\b(first I|then I|I tried)\b", body, re.I))
    else:
        r["pr_body_lint_findings"] = None
    return r


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1])), indent=1))

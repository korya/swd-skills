#!/usr/bin/env python3
"""PreToolUse guard: a pull request is opened through /submit, never by hand.

The skill's description says the same thing, and an agent that knows the
`gh pr create` pattern will skip it anyway — six PRs in a row, once. This is
the boundary the description cannot be: the skill leaves a marker in the
repo's git dir at phase 0 and removes it at phase 6, and a bare
`gh pr create` without a fresh marker is refused with the instruction to
invoke the skill. Nothing else is touched.

Escape hatch for a human who means it: prefix the command with
`SWD_SUBMIT_BYPASS=1`. It is a token in the command text, so it shows in the
transcript.

Python rather than bash+jq: python3 is on every machine this plugin installs
on, jq is not. The hook's JSON arrives on stdin; the deny decision leaves on
stdout (exit 0 with hookSpecificOutput, per the hooks reference).
"""

import json
import os
import re
import subprocess
import sys
import time

FRESH_SECONDS = 4 * 3600

REASON = (
    "Pull requests are opened through the /submit skill (swd:submit), never with "
    "`gh pr create` by hand: the skill owns the PR body, the mandatory screenshots "
    "for anything rendered, and the CI gate. Invoke /submit now — its phase 0 sets "
    "the marker this guard checks. A human who means to bypass it prefixes the "
    "command with SWD_SUBMIT_BYPASS=1."
)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    cmd = str((data.get("tool_input") or {}).get("command") or "")
    if not re.search(r"(^|[;&|\s])gh\s+pr\s+create\b", cmd):
        return 0
    if re.search(r"(^|[;&|\s])SWD_SUBMIT_BYPASS=1\s", cmd):
        return 0

    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        git_dir = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--absolute-git-dir"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        # Not a git repo, or no git: nothing to guard.
        return 0

    marker = os.path.join(git_dir, "swd-submit")
    try:
        fresh = (time.time() - os.stat(marker).st_mtime) < FRESH_SECONDS
    except FileNotFoundError:
        fresh = False
    if fresh:
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": REASON,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

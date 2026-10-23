#!/usr/bin/env bash
# Build the repo-docs eval fixture: ticketdesk, a small CLI help desk with no agent docs.
# Usage: make_fixture.sh <target-dir>   (target is wiped and recreated as a git repo)
set -euo pipefail
TARGET="${1:?usage: make_fixture.sh <target-dir>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
rm -rf "$TARGET"; mkdir -p "$TARGET"; cd "$TARGET"
git init -q -b main
git config user.email fixture@example.test
git config user.name "Fixture Bot"
git config commit.gpgsign false
cp -R "$HERE/fixture/." .
git add -A
git commit -qm "feat(ticketdesk): CLI help desk with append-only event log"
git log --oneline

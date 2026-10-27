#!/usr/bin/env bash
# Build the e2e-test eval fixture: ticketdesk with agent docs on main, and a branch
# feature/cli-tidy that changes four behaviours, three of which contradict the specs.
#   <target>/repo   checked out on feature/cli-tidy; PR.md at the root is the PR description
# Usage: make_fixture.sh <target-dir>   (target is wiped)
set -euo pipefail
TARGET="${1:?usage: make_fixture.sh <target-dir>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
rm -rf "$TARGET"; mkdir -p "$TARGET"; cd "$TARGET"
git init -q -b main
git config user.email fixture@example.test
git config user.name "Fixture Bot"
git config commit.gpgsign false
cp -R "$HERE/../blueprint/fixture/." .
git add -A
git commit -qm "feat(ticketdesk): CLI help desk with event log and agent docs"
git checkout -qb feature/cli-tidy
cp -R "$HERE/fixture/change/." .
git add -A
git commit -qF- <<'MSG'
feat(cli): Tidy the list output and relax the resolution rule

The priority column leaves the default list view, short resolution notes are accepted,
assignment works at any point in a ticket's life, and --help gained a description.
MSG
git log --oneline --all

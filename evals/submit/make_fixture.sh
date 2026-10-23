#!/usr/bin/env bash
# Build the submit eval fixture: a working repo with a local bare origin.
#   <target>/repo        — acme-notify, checked out with the retry/rate-limit rework
#                           UNCOMMITTED in the working tree, plus an untracked .env and
#                           scratch.py, plus an unrelated README typo fix
#   <target>/origin.git  — the bare remote `origin`; main is pushed, nothing else
#   <target>/pr/         — (existing-pr mode only) the title and body of the PR that a
#                           previous pass opened for the retry commit
# Usage: make_fixture.sh <target-dir> [fresh|existing-pr]   (target is wiped)
set -euo pipefail

TARGET="${1:?usage: make_fixture.sh <target-dir> [fresh|existing-pr]}"
MODE="${2:-fresh}"
HERE="$(cd "$(dirname "$0")" && pwd)"

rm -rf "$TARGET"
mkdir -p "$TARGET"
git init -q --bare -b main "$TARGET/origin.git"

REPO="$TARGET/repo"
mkdir -p "$REPO"
cd "$REPO"
git init -q -b main
git config user.email fixture@example.test
git config user.name "Fixture Bot"
git config commit.gpgsign false
git remote add origin "$TARGET/origin.git"

cp -R "$HERE/fixture/base/." .
git add -A
git commit -qm "feat(notify): Initial sender with fixed retries and window limiter"
git push -q -u origin main

if [ "$MODE" = "existing-pr" ]; then
  # A previous /submit pass committed and pushed the sender rework on a feature branch
  # and opened a PR for it. The rate-limit rework and the rest arrive now, uncommitted.
  git checkout -qb korya-retry-backoff
  cp "$HERE/fixture/change/notify/sender.py" notify/sender.py
  cp "$HERE/fixture/change/tests/test_sender.py" tests/test_sender.py
  git add notify/sender.py tests/test_sender.py
  git commit -qF- <<'MSG'
feat(sender): Retry with exponential backoff and honor Retry-After

Previously the sender retried three times one second apart and treated 429 as a hard
failure, so a gateway that needed a few seconds to recover lost about 9% of messages.
Now it retries five times with exponential backoff capped at 16 s, retries on 429, and
honors a Retry-After header when the gateway sends one.
MSG
  git push -q -u origin korya-retry-backoff
  mkdir -p "$TARGET/pr"
  cp "$HERE/fixture/pr/title.txt" "$HERE/fixture/pr/body.md" "$TARGET/pr/"
fi

# The uncommitted work: everything in change/ overlays the tree.
cp -R "$HERE/fixture/change/." .
git status --short

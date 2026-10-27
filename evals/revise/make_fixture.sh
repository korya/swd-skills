#!/usr/bin/env bash
# Build the revise eval fixture: acme-notify with the retry/rate-limit rework committed on
# a feature branch, a local bare origin, the PR body, and a six-finding review.
#   <target>/repo        checked out on korya-retry-backoff, clean tree
#   <target>/origin.git  bare remote with main and the branch
#   <target>/pr/body.md  the PR description as the forge would show it
#   <target>/review.md   the reviewer's feedback
# Usage: make_fixture.sh <target-dir>   (target is wiped)
set -euo pipefail
TARGET="${1:?usage: make_fixture.sh <target-dir>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
SUBMIT="$HERE/../submit/fixture"
rm -rf "$TARGET"; mkdir -p "$TARGET"
git init -q --bare -b main "$TARGET/origin.git"
REPO="$TARGET/repo"; mkdir -p "$REPO"; cd "$REPO"
git init -q -b main
git config user.email fixture@example.test
git config user.name "Fixture Bot"
git config commit.gpgsign false
git remote add origin "$TARGET/origin.git"
cp -R "$SUBMIT/base/." .
git add -A
git commit -qm "feat(notify): Initial sender with fixed retries and window limiter"
git push -q -u origin main
git checkout -qb korya-retry-backoff
cp -R "$SUBMIT/change/." .
rm -f .env scratch.py
git add -A
git commit -qF- <<'MSG'
feat(notify): Retry with backoff and throttle tenants with a token bucket

Previously the sender retried three times one second apart and only on 5xx, and the limiter
was a fixed 100-per-minute window. Now the sender retries five times with exponential
backoff and honors Retry-After, and the limiter is a token bucket at 60 per minute with a
burst of 20. Delivery success in the staging load test rose from 91.2% to 99.1%.
MSG
git push -q -u origin korya-retry-backoff
mkdir -p "$TARGET/pr"
cp "$HERE/fixture/pr/body.md" "$TARGET/pr/body.md"
cp "$HERE/fixture/review.md" "$TARGET/review.md"
git log --oneline --all

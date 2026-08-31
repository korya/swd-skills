#!/usr/bin/env bash
# Build the examine eval fixture: a git repo with three branches.
#   main              — the base service
#   feature/discounts — the seeded PR under review (nine planted findings)
#   feature/audit-log — a clean, well-made PR (false-positive control)
# Usage: make_fixture.sh <target-dir>   (target is wiped and recreated)
set -euo pipefail

TARGET="${1:?usage: make_fixture.sh <target-dir>}"
HERE="$(cd "$(dirname "$0")" && pwd)"

rm -rf "$TARGET"
mkdir -p "$TARGET"
cd "$TARGET"

git init -q -b main
git config user.email fixture@example.test
git config user.name "Fixture Bot"
git config commit.gpgsign false

cp -R "$HERE/fixture/base/." .
git add -A
git commit -qm "feat(billing): Initial user and billing service"

git checkout -qb feature/discounts
cp -R "$HERE/fixture/seeded/." .
git add -A
git commit -qF- <<'MSG'
feat(discounts): Add discount codes with API validation

Support can now create percentage discount codes and customers redeem
them at charge time (fixes the long-standing ask in SUPPORT-311).

- Discount percent is validated at the API boundary per
  docs/invariants.md §4.
- The discount cap is deliberately lowered from 50% to 30% per finance
  policy FIN-88; finance signed off, product notified.
- The new discount engine keeps strategies pluggable for upcoming
  fixed-amount and BOGO discounts.
- The legacy 'plan' field is dropped in migration 002; existing users
  are mapped onto the new 'tier' field.
- db.find_user_by_email now returns None instead of raising, which
  simplifies the new discount code paths; billing was updated to match.
MSG

git checkout -q main
git checkout -qb feature/audit-log
cp -R "$HERE/fixture/clean/." .
git add -A
git commit -qF- <<'MSG'
feat(audit): Record an audit event on user creation

Support asked for a trail of who was created and when. Adds an
in-memory append-only audit log; entries carry the user id, never the
raw email (CLAUDE.md logging rule). Additive only — no migration, no
behavior change for existing callers, failure paths covered in
tests/test_audit.py.
MSG

git checkout -q feature/discounts
echo "fixture ready at $TARGET (branches: main, feature/discounts, feature/audit-log)"

#!/usr/bin/env bash
# Build the rebase eval fixture from the blueprint fixture (ticketdesk with agent docs).
#   main            A (base) -> B rename due_at to deadline_for -> C extract _line, add export
#                   -> D INV-006 (store clock), CLI test convention, tests/test_cli.py
#   feature/overdue A -> 1 service overdue() using time.time() -> 2 cli overdue subcommand
#                   -> 3 specs TKT-014 and CLI-010
#   checked out on feature/overdue with an untracked debug_notes.md in the tree
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

# ---- feature/overdue, authored against A ----
git checkout -qb feature/overdue
python3 "$HERE/patches.py" curr1
git add -A && git commit -qF- <<'MSG'
feat(tickets): Add overdue detection to the service

An open or assigned ticket whose due time has passed is overdue. The service lists them
oldest due first.
MSG
python3 "$HERE/patches.py" curr2
git add -A && git commit -qF- <<'MSG'
feat(cli): Add the overdue subcommand

`ticketdesk overdue` prints overdue tickets in the same line format as `list`.
MSG
python3 "$HERE/patches.py" curr3
git add -A && git commit -qF- <<'MSG'
docs(specs): Add TKT-014 and CLI-010 for overdue tickets
MSG

# ---- main moved on ----
git checkout -q main
python3 "$HERE/patches.py" deltaB
git add -A && git commit -qF- <<'MSG'
refactor(sla): Rename due_at to deadline_for

The function name collided with the Ticket.due_at field in every grep.
MSG
python3 "$HERE/patches.py" deltaC
git add -A && git commit -qF- <<'MSG'
feat(cli): Extract the list line formatter and add export

`export` prints every ticket as one JSON object per line. Both commands share `_line`
for the human-readable form.
MSG
python3 "$HERE/patches.py" deltaD
git add -A && git commit -qF- <<'MSG'
docs: Add INV-006 on the store clock and the CLI test convention

Commands that depend on the current time read it from the store's clock so replay and
tests stay deterministic. CLI tests live in tests/test_cli.py and drive the binary with
subprocess.
MSG
git checkout -q feature/overdue
printf 'notes while debugging the due-time math; delete before merge\n' > debug_notes.md
git log --oneline --all --graph | head -12
git status --short

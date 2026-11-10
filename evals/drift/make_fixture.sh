#!/usr/bin/env bash
# Build the drift eval fixture: the ticketdesk fixture, then one commit that plants five
# drifts between the product and its specs. The specs stay as they were.
# Usage: make_fixture.sh <target-dir>   (target is wiped)
set -euo pipefail
TARGET="${1:?usage: make_fixture.sh <target-dir>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
bash "$HERE/../blueprint/make_fixture.sh" "$TARGET" >/dev/null
python3 - "$TARGET" <<'PY'
import pathlib, sys
repo = pathlib.Path(sys.argv[1])
def sub(path, old, new):
    p = repo / path; t = p.read_text()
    assert t.count(old) == 1, (path, old)
    p.write_text(t.replace(old, new))
# X1 TKT-010: the minimum resolution length drops from 10 to 8.
sub("ticketdesk/tickets.py",
    'if len(resolution.strip()) < 10:\n            raise TicketError("resolution note must be at least 10 characters")',
    'if len(resolution.strip()) < 8:\n            raise TicketError("resolution note must be at least 8 characters")')
# X2 CLI-006: the state is padded to 9 characters, not 8.
sub("ticketdesk/cli.py", "{t.state:<8}", "{t.state:<9}")
# X3 TKT-012: the unknown-ticket message changes.
sub("ticketdesk/tickets.py",
    'raise TicketError(f"no ticket {ticket_id}") from None',
    'raise TicketError(f"ticket {ticket_id} not found") from None')
# X4 LOG-005: the JSON keys are no longer sorted.
sub("ticketdesk/store.py", "json.dumps(record, sort_keys=True)", "json.dumps(record)")
# X5 an undocumented subcommand, count.
sub("ticketdesk/cli.py", '    sub.add_parser("list")\n', '    sub.add_parser("list")\n    sub.add_parser("count")\n')
sub("ticketdesk/cli.py",
    '        else:\n            for t in svc.list():',
    '        elif args.cmd == "count":\n            print(len(svc.list()))\n        else:\n            for t in svc.list():')
PY
cd "$TARGET"
git add -A
git commit -qm "refactor(ticketdesk): Tidy the service and the CLI"
git log --oneline

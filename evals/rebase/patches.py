#!/usr/bin/env python3
"""Apply one named patch to the fixture working tree. Used by make_fixture.sh."""
import json, sys
from pathlib import Path

step = sys.argv[1]
R = Path.cwd()


def rw(rel, old, new, count=1):
    p = R / rel
    t = p.read_text()
    assert old in t, (rel, old[:40])
    p.write_text(t.replace(old, new, count))


if step == "curr1":
    rw("ticketdesk/tickets.py", "    def list(self):", '''    def overdue(self, now=None):
        """Open or assigned tickets past their due time, oldest due first."""
        import time
        if now is None:
            now = time.time()
        return sorted((t for t in self._tickets().values() if t.state != "closed" and t.due_at < now),
                      key=lambda t: (t.due_at, t.id))

    def list(self):''')
elif step == "curr2":
    rw("ticketdesk/cli.py", '    sub.add_parser("list")', '    sub.add_parser("list")\n    sub.add_parser("overdue")')
    rw("ticketdesk/cli.py", '''        else:
            for t in svc.list():''', '''        elif args.cmd == "overdue":
            for t in svc.overdue():
                print(f"#{t.id} [{t.priority}] {t.state:<8} {t.title}")
        else:
            for t in svc.list():''')
elif step == "curr3":
    p = R / "docs/product-specs/tickets.md"
    p.write_text(p.read_text().rstrip("\n") + '''

### TKT-014: Overdue tickets
An open or assigned ticket is overdue once the current time is later than its due time. A
closed ticket is never overdue.
''')
    p = R / "docs/product-specs/cli.md"
    p.write_text(p.read_text().rstrip("\n") + '''

### CLI-010: overdue
`ticketdesk overdue` prints one line per overdue ticket in the `list` line format, oldest
due time first. When nothing is overdue it prints nothing and exits 0.
''')
elif step == "deltaB":
    rw("ticketdesk/sla.py", "def due_at(created_at, priority):", "def deadline_for(created_at, priority):")
    rw("ticketdesk/__init__.py", "from .sla import due_at, SLA_HOURS", "from .sla import deadline_for, SLA_HOURS")
    rw("ticketdesk/__init__.py", '"due_at"', '"deadline_for"')
    rw("ticketdesk/tickets.py", "from .sla import due_at", "from .sla import deadline_for")
    rw("ticketdesk/tickets.py", 't.due_at = due_at(ev["at"], ev["priority"])', 't.due_at = deadline_for(ev["at"], ev["priority"])')
    rw("ticketdesk/tickets.py", "due_at(0, priority)  # validates the priority", "deadline_for(0, priority)  # validates the priority")
elif step == "deltaC":
    rw("ticketdesk/cli.py", "def main(argv=None):", '''def _line(t):
    return f"#{t.id} [{t.priority}] {t.state:<8} {t.title}"


def main(argv=None):''')
    rw("ticketdesk/cli.py", '    sub.add_parser("list")', '    sub.add_parser("list")\n    sub.add_parser("export")')
    rw("ticketdesk/cli.py", '''        else:
            for t in svc.list():
                print(f"#{t.id} [{t.priority}] {t.state:<8} {t.title}")''', '''        elif args.cmd == "export":
            for t in svc.list():
                print(json.dumps({"id": t.id, "title": t.title, "priority": t.priority,
                                  "state": t.state, "due_at": t.due_at}, sort_keys=True))
        else:
            for t in svc.list():
                print(_line(t))''')
    rw("ticketdesk/cli.py", "import argparse\n", "import argparse\nimport json\n")
elif step == "deltaD":
    p = R / "docs/product-specs/invariants.md"
    p.write_text(p.read_text().rstrip("\n") + '''

### INV-006: Time comes from the store clock
A command that depends on the current time reads it from the store's clock, never from the
system clock directly. Replay and tests stay deterministic.
''')
    p = R / "docs/guidelines.md"
    p.write_text(p.read_text().rstrip("\n") + '''

## CLI tests

CLI tests live in `tests/test_cli.py` and drive the binary with `subprocess`, one test per
subcommand. A new subcommand ships with its test in that file.
''')
    (R / "tests/test_cli.py").write_text('''import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*args, log):
    return subprocess.run([sys.executable, "-m", "ticketdesk.cli", "--log", log, *args],
                          cwd=ROOT, capture_output=True, text=True)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.log = os.path.join(self.dir.name, "t.jsonl")

    def tearDown(self):
        self.dir.cleanup()

    def test_create_and_list(self):
        self.assertEqual(run("create", "Printer", "--priority", "P1", log=self.log).returncode, 0)
        out = run("list", log=self.log).stdout
        self.assertIn("#1 [P1] open     Printer", out)

    def test_export_is_json_lines(self):
        run("create", "Printer", log=self.log)
        line = run("export", log=self.log).stdout.splitlines()[0]
        self.assertEqual(json.loads(line)["title"], "Printer")
''')
else:
    raise SystemExit(f"unknown step {step}")
print(f"applied {step}")

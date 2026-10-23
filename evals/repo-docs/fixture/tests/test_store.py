import tempfile
import unittest
from pathlib import Path

from ticketdesk import EventStore


class StoreTests(unittest.TestCase):
    def test_corrupt_line_stops_replay(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "log.jsonl"
            p.write_text('{"kind": "created", "id": 1, "title": "a", "priority": "P3", "at": 1}\nnot json\n')
            with self.assertRaises(ValueError):
                EventStore(p).replay()

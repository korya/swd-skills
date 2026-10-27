import tempfile
import unittest
from pathlib import Path

from ticketdesk import EventStore, TicketError, TicketService


class Clock:
    def __init__(self):
        self.now = 1_700_000_000.0

    def __call__(self):
        self.now += 1
        return self.now


class TicketTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.store = EventStore(Path(self.dir.name) / "log.jsonl", clock=Clock())
        self.svc = TicketService(self.store)

    def tearDown(self):
        self.dir.cleanup()

    def test_create_sets_due_by_priority(self):
        t = self.svc.create("Printer on fire", "P1")
        self.assertEqual(t.state, "open")
        self.assertAlmostEqual(t.due_at - t.created_at, 4 * 3600)

    def test_ids_increase_and_never_reuse(self):
        a = self.svc.create("a", "P3")
        b = self.svc.create("b", "P3")
        self.assertEqual((a.id, b.id), (1, 2))

    def test_assign_requires_open_ticket(self):
        t = self.svc.create("a", "P2")
        self.svc.assign(t.id, "dana")
        self.svc.close(t.id, "Replaced the toner cartridge")
        with self.assertRaises(TicketError):
            self.svc.assign(t.id, "lee")

    def test_close_needs_resolution_note(self):
        t = self.svc.create("a", "P2")
        with self.assertRaises(TicketError):
            self.svc.close(t.id, "done")

    def test_unknown_priority_rejected(self):
        with self.assertRaises(ValueError):
            self.svc.create("a", "P9")

    def test_log_is_append_only(self):
        t = self.svc.create("a", "P3")
        self.svc.assign(t.id, "dana")
        self.assertEqual([e["kind"] for e in self.store.replay()], ["created", "assigned"])

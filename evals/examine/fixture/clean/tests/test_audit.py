import unittest

from app import users
from app.db import STORE


class TestAudit(unittest.TestCase):
    def setUp(self):
        STORE.users.clear()
        STORE.audit.clear()

    def test_user_creation_is_audited(self):
        u = users.create_user("a@b.c", "A")
        self.assertEqual(len(STORE.audit), 1)
        self.assertEqual(STORE.audit[0]["event"], "user.created")
        self.assertEqual(STORE.audit[0]["user_id"], u["id"])

    def test_audit_entries_carry_no_email(self):
        users.create_user("a@b.c", "A")
        self.assertNotIn("email", STORE.audit[0])

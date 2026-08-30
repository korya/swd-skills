import unittest

from app import billing, users
from app.db import STORE


class TestCharge(unittest.TestCase):
    def setUp(self):
        STORE.users.clear()
        STORE.charges.clear()

    def test_charge_known_user(self):
        users.create_user("a@b.c", "A")
        entry = billing.charge("a@b.c", "10.00")
        self.assertEqual(entry["amount"], 1000)

    def test_charge_unknown_user_fails(self):
        with self.assertRaises(billing.BillingError):
            billing.charge("nobody@x.y", "5.00")

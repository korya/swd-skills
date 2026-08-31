import unittest

from app import api
from app.db import STORE


class TestDiscounts(unittest.TestCase):
    def setUp(self):
        STORE.users.clear()
        STORE.discounts.clear()
        STORE.charges.clear()

    def test_discounted_charge(self):
        api.api_create_user({"email": "a@b.c", "name": "A"})
        api.api_create_discount({"code": "SAVE10", "percent": 10})
        entry = api.api_charge(
            {"email": "a@b.c", "amount": "10.00", "discount_code": "SAVE10"}
        )
        self.assertEqual(entry["amount"], 900)

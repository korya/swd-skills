import unittest

from app import users
from app.db import STORE


class TestCreateUser(unittest.TestCase):
    def setUp(self):
        STORE.users.clear()

    def test_creates_user_with_default_plan(self):
        u = users.create_user("a@b.c", "A")
        self.assertEqual(u["plan"], "free")
        self.assertIn(u["id"], STORE.users)

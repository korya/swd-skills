"""Class-level tests: every email entry point treats casing variants as the same user."""
import sys, unittest
sys.path.insert(0, sys.argv.pop(1))
from app import db, signup, search, invite, password_reset

VARIANTS = ["bob@example.com", "BOB@EXAMPLE.COM", "Bob@example.com", "Bob@Example.COM"]

class EmailIdentityTests(unittest.TestCase):
    def setUp(self):
        db.reset()
        signup.signup("Bob@Example.COM", "Bob")

    def test_search_any_casing(self):
        for v in VARIANTS:
            self.assertEqual(search.search_by_email(v)["status"], "ok", v)

    def test_password_reset_any_casing(self):
        for v in VARIANTS:
            self.assertEqual(password_reset.request_reset(v), "reset-token-for-1", v)

    def test_invite_any_casing(self):
        for v in VARIANTS:
            self.assertEqual(invite.send_invite(v)["status"], "already_member", v)

    def test_signup_rejects_casing_duplicate(self):
        with self.assertRaises(signup.SignupError):
            signup.signup("bob@example.com", "Bob2")

    def test_store_rejects_casing_duplicate(self):
        with self.assertRaises(Exception):
            db.insert("BOB@example.com", "Bypass")

if __name__ == "__main__":
    unittest.main()

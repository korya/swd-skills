import sys, unittest
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from app import db, signup, search, invite, password_reset  # noqa: E402

VARIANTS = ["bob@example.com", "BOB@EXAMPLE.COM", "Bob@example.com"]

class EmailIdentityTests(unittest.TestCase):
    def setUp(self):
        db.reset()
        self.bob = signup.signup("Bob@Example.COM", "Bob")

    def test_every_email_lookup_ignores_case(self):
        for v in VARIANTS:
            with self.subTest(v=v):
                self.assertEqual(search.search_by_email(v)["id"], self.bob.id)
                self.assertEqual(password_reset.request_reset(v), f"reset-token-for-{self.bob.id}")
                self.assertEqual(invite.send_invite(v)["status"], "already_member")

    def test_signup_rejects_case_variant_duplicate(self):
        for v in VARIANTS:
            with self.subTest(v=v):
                with self.assertRaises(signup.SignupError):
                    signup.signup(v, "Bob again")

    def test_store_rejects_case_variant_duplicate(self):
        with self.assertRaises(db.DuplicateEmail):
            db.insert("bob@EXAMPLE.com", "bypass")

    def test_display_email_kept_as_typed(self):
        self.assertEqual(search.search_by_email("bob@example.com")["email"], "Bob@Example.COM")

if __name__ == "__main__":
    unittest.main()

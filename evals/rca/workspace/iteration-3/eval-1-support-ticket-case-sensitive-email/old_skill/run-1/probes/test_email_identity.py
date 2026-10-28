"""Class-level tests: every email lookup path treats addresses that differ only in case as one identity."""
import sys, unittest
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from app import db, signup, search, invite, password_reset  # noqa: E402

STORED, QUERIES = "Bob@Example.COM", ["bob@example.com", "BOB@EXAMPLE.COM", " Bob@Example.COM "]

class EmailIdentityTests(unittest.TestCase):
    def setUp(self):
        db.reset(); signup.signup(email=STORED, name="Bob")
    def test_search(self):
        for q in QUERIES:
            self.assertEqual(search.search_by_email(q)["status"], "ok", q)
    def test_signup_rejects_case_variant(self):
        for q in QUERIES:
            with self.assertRaises(signup.SignupError): signup.signup(email=q, name="Dup")
    def test_invite_sees_member(self):
        for q in QUERIES:
            self.assertEqual(invite.send_invite(q)["status"], "already_member", q)
    def test_password_reset_finds_user(self):
        for q in QUERIES:
            self.assertEqual(password_reset.request_reset(q), "reset-token-for-1")
    def test_store_rejects_duplicate_key(self):
        with self.assertRaises(db.DuplicateEmail): db.insert(email="BOB@example.com", name="Bypass")
    def test_display_form_preserved(self):
        self.assertEqual(search.search_by_email("bob@example.com")["email"], STORED)

if __name__ == "__main__":
    unittest.main()

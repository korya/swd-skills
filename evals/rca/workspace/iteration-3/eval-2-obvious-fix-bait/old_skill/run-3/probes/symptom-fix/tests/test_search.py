"""Deterministic repro of the user-reported bug.

Stdlib-only — run with `python3 -m unittest tests.test_search` or
`python3 tests/test_search.py`.
"""

import sys
import unittest

# Make `app` importable when running this file directly.
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from app import db, signup, search  # noqa: E402


class SearchTests(unittest.TestCase):
    def setUp(self):
        db.reset()

    def test_search_finds_user_signed_up_with_lowercase(self):
        signup.signup(email="alice@example.com", name="Alice")
        self.assertEqual(search.search_by_email("alice@example.com")["status"], "ok")

    def test_search_finds_user_signed_up_with_mixed_case(self):
        # User signed up with mixed-case email (as displayed in their email client).
        signup.signup(email="Bob@Example.COM", name="Bob")
        # Customer support tried to look them up with a different case.
        result = search.search_by_email("bob@example.com")
        self.assertEqual(result["status"], "ok", f"expected to find Bob, got {result!r}")


if __name__ == "__main__":
    unittest.main()

"""Probe: which account does a case-insensitive search return once duplicates exist?"""
import sys
sys.path.insert(0, sys.argv[1])
from app import db, signup, search
db.reset()
signup.signup("Bob@Example.COM", "Bob (billed in Stripe)")
signup.signup("bob@example.com", "Bob (duplicate)")
print("search BOB@EXAMPLE.COM:", search.search_by_email("BOB@EXAMPLE.COM"))
print("search bob@example.com:", search.search_by_email("bob@example.com"))

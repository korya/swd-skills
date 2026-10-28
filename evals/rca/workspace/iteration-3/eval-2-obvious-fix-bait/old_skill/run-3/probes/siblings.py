"""Probe: does case-sensitive email matching hurt callers other than search?"""
import sys
sys.path.insert(0, sys.argv[1])
from app import db, signup, search, invite, password_reset

db.reset()
signup.signup("Bob@Example.COM", "Bob")
print("search lower      :", search.search_by_email("bob@example.com"))
try:
    print("reset lower       :", password_reset.request_reset("bob@example.com"))
except password_reset.ResetError as e:
    print("reset lower       : ResetError", e)
print("invite lower      :", invite.send_invite("bob@example.com"))
try:
    u = signup.signup("bob@example.com", "Bob again")
    print("signup dup lower  : created id", u.id)
except signup.SignupError as e:
    print("signup dup lower  : SignupError", e)
print("users             :", [(u.id, u.email) for u in db.all_users()])

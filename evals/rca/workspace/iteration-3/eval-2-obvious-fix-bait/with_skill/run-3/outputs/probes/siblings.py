"""Probe: does the case-sensitive lookup hurt the other db.find_by_email callers?"""
import sys
sys.path.insert(0, sys.argv[1])
from app import db, signup, search, invite, password_reset

def run(label, fn):
    try:
        print(f"{label:<45} -> {fn()!r}")
    except Exception as e:
        print(f"{label:<45} -> raised {type(e).__name__}: {e}")

db.reset()
signup.signup("Bob@Example.COM", "Bob")
run("search('bob@example.com')", lambda: search.search_by_email("bob@example.com"))
run("password_reset('bob@example.com')", lambda: password_reset.request_reset("bob@example.com"))
run("invite('bob@example.com')", lambda: invite.send_invite("bob@example.com"))
run("signup('bob@example.com') duplicate?", lambda: signup.signup("bob@example.com", "Bob2"))
print("users:", [(u.id, u.email) for u in db.all_users()])
run("search('BOB@EXAMPLE.COM')", lambda: search.search_by_email("BOB@EXAMPLE.COM"))

"""RCA probes: falsify the root cause, sweep siblings, check the counterfactual.

Usage: python3 -B probe.py <fixture-dir>
Read-only against the fixture: patches db.find_by_email in memory only.
"""

import sys

sys.path.insert(0, sys.argv[1])
from app import db, signup, search, invite, password_reset  # noqa: E402


def section(title):
    print(f"\n## {title}")


# --- Falsification: is casing the only variable? -------------------------
section("F1 replay the support log (stored as 'Jane.smith@gmail.com')")
db.reset()
signup.signup("Jane.smith@gmail.com", "Jane")
for q in ["Jane.Smith@gmail.com", "jane.smith@gmail.com", "Jane.smith@gmail.com"]:
    print(f"search {q!r:28} -> {search.search_by_email(q)}")

section("F2 second mechanism: whitespace instead of casing")
db.reset()
signup.signup("bob@example.com", "Bob")
for q in ["bob@example.com", " bob@example.com", "bob@example.com "]:
    print(f"search {q!r:22} -> {search.search_by_email(q)['status']}")

section("F3 does the search layer add anything beyond db.find_by_email?")
db.reset()
signup.signup("Bob@Example.COM", "Bob")
print("db.find_by_email('bob@example.com') ->", db.find_by_email("bob@example.com"))

# --- Siblings -------------------------------------------------------------
section("S1 password reset with a different casing")
db.reset()
signup.signup("Bob@Example.COM", "Bob")
try:
    print("request_reset ->", password_reset.request_reset("bob@example.com"))
except password_reset.ResetError as e:
    print("request_reset -> ResetError:", e)

section("S2 invite an existing member with a different casing")
print("send_invite ->", invite.send_invite("bob@example.com"))

section("S3 duplicate signup with a different casing")
try:
    dup = signup.signup("bob@example.com", "Bob again")
    print("second signup ACCEPTED ->", dup)
except signup.SignupError as e:
    print("second signup rejected:", e)
print("all_users ->", [(u.id, u.email) for u in db.all_users()])

section("S4 duplicate signup with surrounding whitespace")
try:
    dup = signup.signup(" Bob@Example.COM", "Bob padded")
    print("padded signup ACCEPTED ->", dup)
except signup.SignupError as e:
    print("padded signup rejected:", e)

# --- Counterfactual: normalise once at the data layer ---------------------
section("C1 counterfactual: db.find_by_email compares a canonical key")


def canon(email):
    return email.strip().lower()


def find_by_email_canon(email):
    for u in db._USERS:
        if canon(u.email) == canon(email):
            return u
    return None


db.find_by_email = find_by_email_canon
db.reset()
signup.signup("Bob@Example.COM", "Bob")
print("search  ->", search.search_by_email("bob@example.com")["status"])
try:
    print("reset   ->", password_reset.request_reset("bob@example.com"))
except password_reset.ResetError as e:
    print("reset   -> ResetError:", e)
print("invite  ->", invite.send_invite("BOB@example.com")["status"])
try:
    signup.signup("bob@example.com", "Bob again")
    print("dup signup -> ACCEPTED")
except signup.SignupError as e:
    print("dup signup -> rejected:", e)

section("C2 survivor: rows that already collide before the fix")
db.reset()
db.insert("Bob@Example.COM", "Bob")
db.insert("bob@example.com", "Bob again")  # created while the bug was live
print("search bob@example.com ->", search.search_by_email("bob@example.com"))
print("search BOB@EXAMPLE.COM ->", search.search_by_email("BOB@EXAMPLE.COM"))

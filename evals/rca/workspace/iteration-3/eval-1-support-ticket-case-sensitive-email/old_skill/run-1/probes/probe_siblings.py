"""Probe: falsify the root cause and exercise every find_by_email caller."""
import sys
sys.path.insert(0, sys.argv[1])
from app import db, signup, search, invite, password_reset

def run(label, fn):
    try:
        print(f"{label:<55} -> {fn()!r}")
    except Exception as e:
        print(f"{label:<55} -> raised {type(e).__name__}: {e}")

# 1. Replay the bug-report log: stored as "Jane.smith@gmail.com"
db.reset(); signup.signup("Jane.smith@gmail.com", "Jane")
for q in ["Jane.Smith@gmail.com", "jane.smith@gmail.com", "Jane.smith@gmail.com"]:
    run(f"search {q}", lambda q=q: search.search_by_email(q)["status"])

# 2. Falsifier: is it case only, or any non-byte-identical input?
run("search ' Jane.smith@gmail.com' (leading space)", lambda: search.search_by_email(" Jane.smith@gmail.com")["status"])
run("search 'Jane.smith@gmail.com\\n' (trailing newline)", lambda: search.search_by_email("Jane.smith@gmail.com\n")["status"])

# 3. Sibling: signup duplicate check
db.reset(); signup.signup("Bob@Example.COM", "Bob")
run("signup bob@example.com after Bob@Example.COM", lambda: signup.signup("bob@example.com", "Bob2").id)
run("users with that address (casefold)", lambda: [u.email for u in db.all_users() if u.email.casefold()=="bob@example.com"])

# 4. Sibling: invite flow
db.reset(); signup.signup("Bob@Example.COM", "Bob")
run("invite bob@example.com (existing member)", lambda: invite.send_invite("bob@example.com"))

# 5. Sibling: password reset
run("reset bob@example.com (existing user)", lambda: password_reset.request_reset("bob@example.com"))
run("reset Bob@Example.COM (exact case)", lambda: password_reset.request_reset("Bob@Example.COM"))

# 6. Search fix alone, with duplicates already present: which Bob wins?
db.reset(); signup.signup("Bob@Example.COM", "Bob"); signup.signup("bob@example.com", "Bob2")
run("ids matching casefold('BOB@example.com')", lambda: [u.id for u in db.all_users() if u.email.casefold()=="bob@example.com"])

# acme-billing — agent instructions

- Monetary amounts are integers in cents everywhere; never floats in money paths (docs/invariants.md §2).
- Reuse helpers in app/util.py before writing new parsing or validation code.
- Every change to app/billing.py requires failure-path tests (docs/testing.md).
- Never log or store raw emails outside the users table; reference users by id.

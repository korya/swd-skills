# RCA: case-sensitive email search

## TL;DR

The proposed one-liner in `app/search.py` does fix the failing test, but it
patches a **symptom**, not the **root cause**. Email is being treated as
case-sensitive across the whole data layer, not just in `search.py`. The fix
belongs in `app/db.py` (and the signup write path), not in the caller. Doing
it the one-line way leaves three other endpoints — `invite`, `password_reset`,
and `signup`'s duplicate-check — silently broken.

Recommendation: normalize emails at the storage boundary. Single source of
truth, four bugs fixed for the price of one.

## Reproduction

```
$ cd /Users/dmitri/dev/swd-skills/evals/rca/fixture
$ python3 -m unittest discover tests -v
test_search_finds_user_signed_up_with_lowercase ... ok
test_search_finds_user_signed_up_with_mixed_case ... FAIL
AssertionError: 'not_found' != 'ok'
```

Bob signs up as `Bob@Example.COM`; support searches for `bob@example.com`;
search returns `not_found`.

## 5 whys

1. **Why does the search miss Bob?**
   `search.search_by_email` calls `db.find_by_email`, which compares with
   `==` against the stored string. `"Bob@Example.COM" != "bob@example.com"`.

2. **Why does `db.find_by_email` use `==`?**
   `db.py`'s docstring literally says *"Case-sensitive lookups by email."*
   It was written assuming the email key is an exact-match identifier.

3. **Why is the stored value `Bob@Example.COM` in the first place?**
   `signup.signup` writes `email` through unchanged ("Stores email as the
   user typed it"). The system never normalized the value on the way in.

4. **Why was no normalization done on write?**
   Because RFC 5321 technically permits case-sensitive local-parts, the
   original author punted on normalization and pushed the responsibility
   onto callers. In practice no mainstream MTA honors that, and every
   product treats email as case-insensitive — so the assumption was wrong.

5. **Why didn't this surface earlier?**
   The signup duplicate-check, invite, and password-reset paths all share
   the same `find_by_email` and therefore all share the same blind spot.
   They are *consistently* broken, so as long as one user only ever uses
   one casing, nothing visibly breaks. Search by a human (support) was the
   first cross-casing access pattern.

**Root cause:** email is stored verbatim, and the lookup primitive
(`db.find_by_email`) is case-sensitive. The two combined break the
product's implicit "email identifies a unique account" invariant.

## Why the proposed one-liner is not enough

> "Just patch app/search.py to do `email.lower() == u.email.lower()` and ship it."

Two problems with that diff as stated:

1. It edits `search.py`, but the equality check lives in `db.py`. The
   literal patch as written doesn't typecheck — `search.py` doesn't have a
   `u.email` in scope. Assume the user meant "make the search path
   case-insensitive somehow."

2. Even charitably interpreted, it only fixes **search**. The other three
   callers of `find_by_email` still do a case-sensitive compare:

   | Caller | Symptom if we only patch search |
   |---|---|
   | `signup.signup` duplicate-check | User signs up twice with `bob@…` and `Bob@…` → two accounts, same email. Account-takeover-shaped. |
   | `invite.is_already_member` | Existing member gets re-invited because of casing → embarrassing, possibly a security signal. |
   | `password_reset.request_reset` | User can't reset their password if they type a different case than they signed up with → support ticket loop. |

   Sibling bugs. Patching only `search.py` ships three known-broken
   endpoints.

## Recommended fix

Normalize at the boundary. Two small changes, both in `app/db.py`:

```python
# app/db.py

def _normalize(email: str) -> str:
    # Lowercase is the pragmatic norm. If we ever care about the
    # display casing, store it in a separate `email_display` field.
    return email.strip().lower()

def insert(email: str, name: str) -> User:
    global _NEXT_ID
    user = User(id=_NEXT_ID, email=_normalize(email), name=name)
    _NEXT_ID += 1
    _USERS.append(user)
    return user

def find_by_email(email: str) -> Optional[User]:
    needle = _normalize(email)
    for u in _USERS:
        if u.email == needle:
            return u
    return None
```

Also update the docstring (currently says *"Case-sensitive lookups by
email."* — that's now a lie).

This fixes all four endpoints in one place, keeps callers dumb, and makes
the invariant ("email is a normalized lowercase identifier") explicit and
enforceable in one module.

### Optional follow-ups (out of scope of the immediate fix)

- Migration / data note: any persisted users with mixed-case emails need a
  one-shot lowercase pass. With the current in-memory store this is moot,
  but worth flagging for whoever ports this to a real DB.
- Add a uniqueness constraint at the storage layer (`UNIQUE LOWER(email)`
  in SQL) so the invariant is enforced even if a future caller bypasses
  `insert()`.
- Tests to add:
  - signup with `Foo@x.com` then signup with `foo@x.com` → second raises
    `SignupError("email already registered")`.
  - invite for `foo@x.com` when member is `Foo@x.com` → `already_member`.
  - password reset for `Foo@x.com` when member is `foo@x.com` → token
    returned, not `ResetError`.
  - whitespace: `"  foo@x.com  "` resolves to the same account (only if we
    agree `.strip()` belongs in the normalizer — defensible default).

## Patch plan

1. Edit `app/db.py`:
   - Add `_normalize(email)` helper.
   - Apply it in `insert()` when constructing the `User`.
   - Apply it to the search needle in `find_by_email()`.
   - Update the module docstring to reflect case-insensitive semantics.
2. Leave `app/search.py`, `app/signup.py`, `app/invite.py`,
   `app/password_reset.py` **unchanged**. The point of fixing it in `db`
   is that callers don't need to know.
3. Run `python3 -m unittest discover tests -v` — existing tests should
   pass.
4. Add the four follow-up tests above (signup-dup, invite, reset,
   optional whitespace) to lock in the invariant.

## Risk / blast radius

- Behavior change: emails that previously round-tripped with their
  original casing now come back lowercased. If any UI displays
  `user.email` verbatim, "Bob@Example.COM" will render as
  "bob@example.com". If preserving display casing matters, add a separate
  `email_display` field; don't smuggle case back into the identifier.
- No external persistence in this fixture, so no migration risk here.

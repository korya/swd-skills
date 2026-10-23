# RCA: case-sensitive email lookups in the user service

**Ticket:** support can't find users via search when email casing differs
**Severity:** P2 (workaround exists; ~5–10 min/ticket support overhead; 4 agents in 24h)
**Status:** root cause identified; fix proposed (not applied — per instructions)

---

## TL;DR

- **Symptom:** `search_by_email("jane.smith@gmail.com")` returns `not_found` for a user stored as `Jane.smith@gmail.com`.
- **Proximate cause:** `app/db.find_by_email` compares emails with `u.email == email` — a raw, case-sensitive string compare.
- **Root cause:** the codebase has no canonical representation for "email as an identifier." Every layer (signup, search, password-reset, invite) trusts whatever string the caller passes in, and `db` exposes a low-level lookup that happens to be case-sensitive. Email is *defined* (RFC 5321 §2.4) as having a case-insensitive domain part, and in practice the local part is treated case-insensitively by every major mailbox provider — but the code models email as an opaque `str`.
- **Blast radius:** the same bug affects **password reset** and **invite** flows, not just search. Signup additionally lets the *same* human register twice under different casings (data-integrity bug, latent).
- **Class-of-bug fix:** normalize email at the trust boundary (an `Email` value object / a single `normalize_email()` applied in `db.insert` and `db.find_by_email`), then add a uniqueness invariant. Patching `search.py` alone would fix the ticket and leave three siblings bleeding.

---

## 1. Reproduce

```
$ cd /Users/dmitri/dev/swd-skills/evals/rca/fixture
$ python3 -m unittest discover tests -v
test_search_finds_user_signed_up_with_lowercase  ... ok
test_search_finds_user_signed_up_with_mixed_case ... FAIL
AssertionError: 'not_found' != 'ok'
```

Matches the support logs (`Jane.Smith@gmail.com → not_found`, `Jane.smith@gmail.com → ok`) exactly — same row, different casing, different outcome. Deterministic.

## 2. Where the bug lives

`app/db.py:32-36`:

```python
def find_by_email(email: str) -> Optional[User]:
    for u in _USERS:
        if u.email == email:      # <-- case-sensitive compare
            return u
    return None
```

`insert` stores the email verbatim (`app/db.py:24-29`); `signup` passes it through unchanged (`app/signup.py:10-15`, comment: *"Stores email as the user typed it."*). So `Bob@Example.COM` goes in as `Bob@Example.COM` and only ever matches itself.

## 3. Five whys

1. **Why** does the search return `not_found` for `bob@example.com` when the user is `Bob@Example.COM`?
   → Because `db.find_by_email` uses `==` on raw strings.
2. **Why** does that matter — shouldn't the caller normalize?
   → Nothing in the system normalizes. Search, signup, password-reset, and invite all pass user-supplied strings straight through.
3. **Why** is there no normalization layer?
   → Email is modeled as `str` everywhere. There is no value object, no `normalize_email()` helper, no DB-level constraint. The comment on `db.py` (*"Case-sensitive lookups by email"*) reads like a deliberate choice, but `signup.py`'s comment (*"Stores email as the user typed it"*) reads like a UX choice (preserve display casing) that accidentally became the identity rule.
4. **Why** did the two concerns get conflated?
   → "Display this back to the user the way they typed it" and "use this as a primary key" got stored in the *same field*. There is no separation between the **identity** of an email (canonical, lowercased local+domain) and its **display form** (what the user typed).
5. **Why** wasn't this caught earlier?
   → No test covered mixed-case (the only existing test used `alice@example.com`, lowercase). No type-level guard (`Email` newtype). No DB uniqueness constraint that would have made the inconsistency visible. RFC 5321 / common-practice casing rules aren't encoded anywhere in the code or docs.

Root cause = **missing canonicalization at the boundary, combined with mixing identity and display in one field.** The case-sensitive `==` is the proximate trigger; the missing abstraction is why it kept being a trigger.

## 4. Sibling sweep — is this only in search?

No. Every call to `db.find_by_email` inherits the same bug:

| File                    | Callsite                                     | Failure mode when casing differs                                              |
|-------------------------|----------------------------------------------|-------------------------------------------------------------------------------|
| `app/search.py:7`       | `db.find_by_email(email)` in `search_by_email` | The reported P2: support can't find users.                                  |
| `app/password_reset.py:11` | `db.find_by_email(email)` in `request_reset` | **Worse than search:** legitimate users get `ResetError("no such user")` and are locked out of recovery. |
| `app/invite.py:7`       | `db.find_by_email(email)` in `is_already_member` | Invite flow says `invite_sent` for someone who is already a member — duplicate accounts, double billing risk, GDPR/right-to-be-forgotten landmines (which user do you delete?). |
| `app/signup.py:13`      | `db.find_by_email(email)` as a uniqueness check | **Latent data-integrity bug:** `bob@example.com` and `Bob@Example.COM` are both accepted, producing two `User` rows for the same human. Anything downstream that joins by email is now wrong. |

The signup case is the most dangerous — search and reset are read-side annoyances that vanish when you fix the lookup; signup is a write-side corruption that fixing the lookup *later* won't undo. Worth checking production data for already-existing duplicates.

## 5. Proposed fix (not applied)

Two layers. Boundary normalization is non-negotiable; the value object is the prevention story.

### 5a. Minimal fix — normalize in `db` (one-line idea, but do it properly)

Introduce a single helper and use it consistently in `db`:

```python
# app/db.py
def _normalize_email(email: str) -> str:
    # RFC 5321: domain is case-insensitive. The local part is technically
    # case-sensitive per spec, but every real-world mailbox provider treats
    # it case-insensitively, and Stripe / our billing system already do.
    # Lowercasing the whole thing matches user expectations and our peers.
    return email.strip().lower()

def insert(email, name):
    ...
    user = User(id=_NEXT_ID, email=_normalize_email(email), name=name)
    ...

def find_by_email(email):
    needle = _normalize_email(email)
    for u in _USERS:
        if u.email == needle:
            return u
    return None
```

This fixes search, reset, invite, and the signup duplicate-detection in one place. All four callsites continue to pass raw user input; `db` is now the single source of truth for what "same email" means.

**Trade-off:** we lose the user's original casing as displayed. If product wants to preserve display casing (e.g. for greeting emails), split the field: store `email_canonical` (lowercased, indexed, unique) and `email_display` (verbatim). Cheap to add; the `User` dataclass already owns both.

### 5b. Class-of-bug fix — make it impossible to pass an un-normalized email into `db`

The bug recurred across four files because nothing in the type system distinguished "raw user input" from "canonical identifier." Two complementary moves:

1. **`Email` value object.** A small frozen dataclass / `NewType` wrapping a normalized string, constructed via `Email.parse(raw: str) -> Email`. `db.insert` and `db.find_by_email` accept only `Email`, not `str`. New code physically *cannot* skip normalization without the type checker yelling. Cheap, idiomatic, ~20 lines.
2. **Uniqueness invariant in `db.insert`.** Today `insert` will happily append a second `User` with the same canonical email if the caller forgets to check. Promote the check from `signup` (where it's enforceable per-flow) into `db` (where it's enforceable globally). Add a test that asserts the invariant directly.

Belt-and-braces: when this gets a real database, add a `UNIQUE INDEX users (lower(email))` (or a generated canonical column with a unique constraint). That's the layer where invariants survive bugs in application code.

### 5c. Tests to add alongside the fix

- `test_signup_rejects_duplicate_with_different_casing` (covers 5a + the latent signup bug).
- `test_password_reset_finds_user_with_different_casing` (sibling of the search test).
- `test_invite_detects_existing_member_with_different_casing` (sibling).
- `test_db_normalizes_on_insert_and_lookup` (pins the invariant at the lowest layer so future callers can't regress it).
- Property-style: round-trip any reasonable casing of a stored email through search and assert it's findable.

Parameterizing the existing two `SearchTests` over a list of casings would catch this whole class going forward.

## 6. What I'd also flag

- **Untrusted input in `signup`.** `if not email or "@" not in email` is not email validation; it's a placeholder that lets `"@"`, `"a@"`, `"@b"`, and `"a@b@c"` through. Out of scope for this ticket, but worth a follow-up since we're touching the email path.
- **Whitespace.** `"  bob@example.com\n"` from a copy-paste will also miss. `.strip()` in the normalizer handles it; worth an explicit test.
- **Unicode / IDN domains.** Out of scope but eventually relevant — `.lower()` on a Turkish "İ" is famously not idempotent. If/when we accept international emails, use `email.utils.parseaddr` + IDNA encoding for the domain, not naive `.lower()`.
- **Comment in `db.py` says "Case-sensitive lookups by email."** If the fix lands, that comment becomes a lie. Update it, or future-Dmitri will assume the case sensitivity is load-bearing and rebuild this bug.

## 7. Recommendation

1. Land 5a (normalize in `db`) **now** — unblocks support today, fixes three sibling bugs as a side effect.
2. Audit production data for duplicate users created by the signup variant before they multiply.
3. Land 5b (`Email` value object + invariant in `insert`) within the week — prevents the next instance of this class of bug, of which there will be one if we don't.
4. Add the tests in 5c before closing the ticket so the regression has a tripwire.

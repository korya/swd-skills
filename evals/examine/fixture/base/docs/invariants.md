# Invariants

## §1 Canonical emails
Emails are stored lowercased and trimmed (`util.normalize_email` at every write path).
All lookups assume canonical form; a non-canonical write breaks every reader.

## §2 Integer cents
All monetary amounts are integers in cents, end to end. Floats are forbidden in money
paths — rounding decisions are made explicitly with integer arithmetic.

## §3 Reversible migrations
Migrations are backward-compatible: additive first; destructive steps only after a
release with dual-read, and every migration ships a `down()`.

## §4 Percentage adjustments
Any percentage adjustment (discount, credit) is validated at the API boundary before it
reaches billing. The cap itself is finance policy (see `billing.MAX_DISCOUNT_PERCENT`).

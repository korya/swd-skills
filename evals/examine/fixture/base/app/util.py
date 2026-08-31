def normalize_email(email: str) -> str:
    """Canonical form for storage and lookup (docs/invariants.md §1)."""
    return email.strip().lower()


def parse_money(amount_str: str) -> int:
    """Parse a decimal money string like '12.34' into integer cents.

    Raises ValueError for malformed or negative input — money enters the
    system as a non-negative amount; adjustments are modeled explicitly.
    """
    s = amount_str.strip()
    if not s or s.startswith("-") or s.count(".") > 1:
        raise ValueError(f"malformed amount: {amount_str!r}")
    whole, _, frac = s.partition(".")
    frac = (frac + "00")[:2]
    if not whole.isdigit() or not frac.isdigit():
        raise ValueError(f"malformed amount: {amount_str!r}")
    return int(whole) * 100 + int(frac)

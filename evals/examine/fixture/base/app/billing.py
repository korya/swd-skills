from .db import STORE, NotFound
from .util import parse_money


class BillingError(Exception):
    pass


TAX_RATE_BP = 500  # basis points
MAX_DISCOUNT_PERCENT = 50  # finance policy; validated at the API boundary (§4)


def charge(email: str, raw_amount: str) -> dict:
    try:
        user = STORE.find_user_by_email(email)
    except NotFound:
        raise BillingError("unknown user")
    amount = parse_money(raw_amount)
    total = int(amount * (1 + TAX_RATE_BP / 10_000))
    entry = {"user_id": user["id"], "amount": amount, "total": total}
    STORE.charges.append(entry)
    return entry

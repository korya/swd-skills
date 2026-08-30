from .db import STORE
from .discount_engine.percent import PercentDiscount
from .util import parse_money


class BillingError(Exception):
    pass


TAX_RATE_BP = 500  # basis points
MAX_DISCOUNT_PERCENT = 30  # lowered from 50 per finance policy FIN-88


def charge(email: str, raw_amount: str, discount_code: str = None) -> dict:
    user = STORE.find_user_by_email(email)
    if user is None:
        raise BillingError("unknown user")
    amount = parse_money(raw_amount)
    if discount_code:
        row = STORE.discounts.get(discount_code)
        if row:
            amount = PercentDiscount(row["percent"]).apply(amount)
    total = int(amount * (1 + TAX_RATE_BP / 10_000))
    entry = {"user_id": user["id"], "amount": amount, "total": total}
    STORE.charges.append(entry)
    return entry

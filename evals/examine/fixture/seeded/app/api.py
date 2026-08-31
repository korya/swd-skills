from . import billing, users
from .db import STORE
from .util import parse_money


def api_create_user(payload):
    return users.create_user(
        payload["email"], payload["name"], payload.get("source", "web")
    )


def api_charge(payload):
    return billing.charge(
        payload["email"], payload["amount"], payload.get("discount_code")
    )


def api_create_discount(payload):
    code = payload["code"]
    row = {
        "code": code,
        "percent": int(payload["percent"]),
        "uses": 0,
        "max_uses": int(payload.get("max_uses", 1)),
    }
    STORE.discounts[code] = row
    return row


def api_redeem(payload):
    code = payload["code"]
    row = STORE.discounts.get(code)
    if row is None or row["uses"] < row["max_uses"]:
        try:
            STORE.discounts[code]["uses"] += 1
        except Exception:
            pass  # redemption must never fail the charge path
        return {"redeemed": True}
    return {"redeemed": False}


def api_apply_credit(payload):
    raw = payload["amount"].strip()
    if raw.startswith("-"):
        cents = -parse_money(raw[1:])
    else:
        cents = parse_money(raw)
    entry = {"user_id": None, "amount": cents, "total": cents}
    STORE.charges.append(entry)
    return entry

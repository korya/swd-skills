from . import billing, users


def api_create_user(payload):
    return users.create_user(payload["email"], payload["name"])


def api_charge(payload):
    return billing.charge(payload["email"], payload["amount"])

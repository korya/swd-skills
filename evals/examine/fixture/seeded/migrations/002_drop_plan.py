"""002: drop the legacy 'plan' field; map users onto the new 'tier' field."""


def up(store):
    for u in store.users.values():
        plan = u.pop("plan", None)
        u["tier"] = "grandfathered" if plan == "legacy" else "standard"

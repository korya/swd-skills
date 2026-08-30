from .db import STORE, NotFound


def lookup(email: str) -> dict:
    """Support-console lookup; returns a display dict or a not-found marker."""
    try:
        u = STORE.find_user_by_email(email)
    except NotFound:
        return {"found": False}
    return {"found": True, "id": u["id"], "name": u["name"]}
